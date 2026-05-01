"""
encoder.py – core encode worker
Download → probe → encode → rename → upload → cleanup
"""
from __future__ import annotations
import asyncio
import os
import time
import json
import math
import subprocess
import traceback
from pathlib import Path

from pyrogram import Client
from pyrogram.enums import ParseMode
from pyrogram.types import Message

from bot.config import (
    ALLOW_ACTION, LOG_CHANNEL, LOGS_IN_CHANNEL,
    AUTO_PREFIX, AUTO_SUFFIX, CAP_DECO, RELEASER,
    DUMP_LEECH, DUMP_CHANNEL, UPLOAD_AS_VIDEO,
    UPLOAD_VIDEO_AS_SPOILER, FILENAME_AS_CAPTION,
    SAMPLE_DURATION, SAMPLE_START, SCREENSHOT_COUNT,
)
from bot.utils.ffmpeg_builder import build_command, EncodeProfile, codec_display_name
from bot.utils.rename import apply_rename_rules, build_caption, sanitize_filename
from bot.db.database import (
    get_thumbnail, get_codec, get_crf, get_preset,
    get_prefix, get_suffix, get_rename_rule,
    get_dual_audio, get_bit_depth,
)

DOWNLOAD_DIR = Path("/tmp/encbot/downloads")
ENCODE_DIR   = Path("/tmp/encbot/encodes")
THUMB_DIR    = Path("/tmp/encbot/thumbs")

for d in (DOWNLOAD_DIR, ENCODE_DIR, THUMB_DIR):
    d.mkdir(parents=True, exist_ok=True)


# ─── Progress helper ──────────────────────────────────────────────────────────

def _hms(seconds: float) -> str:
    seconds = int(seconds)
    h, m, s = seconds // 3600, (seconds % 3600) // 60, seconds % 60
    return f"{h:02d}:{m:02d}:{s:02d}"


def _progress_bar(pct: float, width: int = 12) -> str:
    filled = int(width * pct / 100)
    return "█" * filled + "░" * (width - filled)


async def _edit_safe(msg: Message, text: str):
    try:
        await msg.edit_text(text, parse_mode=ParseMode.HTML)
    except Exception:
        pass


# ─── ffprobe helpers ─────────────────────────────────────────────────────────

def probe(path: str) -> dict:
    cmd = [
        "ffprobe", "-v", "quiet", "-print_format", "json",
        "-show_streams", "-show_format", str(path)
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return json.loads(result.stdout) if result.returncode == 0 else {}


def get_duration(info: dict) -> float:
    try:
        return float(info["format"]["duration"])
    except Exception:
        return 0.0


def count_streams(info: dict, codec_type: str) -> int:
    return sum(1 for s in info.get("streams", []) if s.get("codec_type") == codec_type)


# ─── Thumbnail ────────────────────────────────────────────────────────────────

async def extract_thumbnail(video_path: str, at: float = 5.0) -> str:
    out = str(THUMB_DIR / f"{Path(video_path).stem}_thumb.jpg")
    cmd = ["ffmpeg", "-ss", str(at), "-i", video_path,
           "-frames:v", "1", "-q:v", "2", "-y", out]
    proc = await asyncio.create_subprocess_exec(*cmd,
        stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.DEVNULL)
    await proc.wait()
    return out if os.path.exists(out) else ""


async def resolve_thumbnail(user_id: int, video_path: str) -> str:
    """Return path to thumbnail: user's custom → auto-extract → empty."""
    user_thumb = await get_thumbnail(user_id)
    if user_thumb:
        return user_thumb   # Telegram file_id, used directly in upload
    return await extract_thumbnail(video_path)


# ─── Sample video ─────────────────────────────────────────────────────────────

async def generate_sample(video_path: str, start: int = SAMPLE_START,
                           duration: int = SAMPLE_DURATION) -> str:
    out = str(ENCODE_DIR / f"{Path(video_path).stem}_sample.mkv")
    cmd = [
        "ffmpeg", "-ss", str(start), "-i", video_path,
        "-t", str(duration), "-c", "copy", "-y", out
    ]
    proc = await asyncio.create_subprocess_exec(*cmd,
        stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.DEVNULL)
    await proc.wait()
    return out if os.path.exists(out) else ""


# ─── Screenshots ──────────────────────────────────────────────────────────────

async def generate_screenshots(video_path: str, count: int = SCREENSHOT_COUNT,
                                duration: float = 0) -> list[str]:
    if duration <= 0:
        info = probe(video_path)
        duration = get_duration(info)
    paths = []
    step = duration / (count + 1)
    for i in range(1, count + 1):
        ts = step * i
        out = str(THUMB_DIR / f"{Path(video_path).stem}_ss_{i:02d}.jpg")
        cmd = ["ffmpeg", "-ss", str(ts), "-i", video_path,
               "-frames:v", "1", "-q:v", "2", "-y", out]
        proc = await asyncio.create_subprocess_exec(*cmd,
            stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.DEVNULL)
        await proc.wait()
        if os.path.exists(out):
            paths.append(out)
    return paths


# ─── Download ────────────────────────────────────────────────────────────────

async def download_file(client: Client, message: Message,
                         status_msg: Message) -> str | None:
    start = time.time()
    last_edit = [0.0]

    async def progress(current, total):
        now = time.time()
        if now - last_edit[0] < 3:
            return
        last_edit[0] = now
        pct = current * 100 / total if total else 0
        speed = current / max(now - start, 1)
        eta = (total - current) / max(speed, 1)
        bar = _progress_bar(pct)
        await _edit_safe(status_msg,
            f"<b>📥 Downloading...</b>\n"
            f"<code>[{bar}] {pct:.1f}%</code>\n"
            f"{current/1e6:.1f} MB / {total/1e6:.1f} MB\n"
            f"⚡ {speed/1e6:.2f} MB/s  ⏱ ETA {_hms(eta)}")

    path = await client.download_media(message, file_name=str(DOWNLOAD_DIR) + "/",
                                        progress=progress)
    return path


# ─── Encode ──────────────────────────────────────────────────────────────────

async def encode_video(input_path: str, output_path: str,
                        profile: EncodeProfile, duration: float,
                        status_msg: Message) -> bool:
    cmd = ["ffmpeg"] + build_command(input_path, output_path, profile,
        src_audio_count=2)
    start = time.time()

    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    last_edit = [0.0]
    buf = b""

    while True:
        chunk = await proc.stderr.read(512)
        if not chunk:
            break
        buf += chunk
        lines = buf.split(b"\r")
        buf = lines[-1]
        for line in lines[:-1]:
            text = line.decode(errors="ignore")
            # parse time= field
            if "time=" in text:
                m = __import__("re").search(r"time=(\d+):(\d+):(\d+\.\d+)", text)
                if m:
                    h, mn, s = int(m.group(1)), int(m.group(2)), float(m.group(3))
                    elapsed_enc = h * 3600 + mn * 60 + s
                    pct = min(elapsed_enc / max(duration, 1) * 100, 100)
                    now = time.time()
                    if now - last_edit[0] >= 4:
                        last_edit[0] = now
                        speed_m = __import__("re").search(r"speed=\s*([\d.]+)x", text)
                        spd = speed_m.group(1) if speed_m else "?"
                        bar = _progress_bar(pct)
                        codec_name = codec_display_name(profile.codec)
                        asyncio.ensure_future(_edit_safe(status_msg,
                            f"<b>⚙️ Encoding [{codec_name}]</b>\n"
                            f"<code>[{bar}] {pct:.1f}%</code>\n"
                            f"⏱ {_hms(elapsed_enc)} / {_hms(duration)}\n"
                            f"🚀 Speed: {spd}x"))

    await proc.wait()
    return proc.returncode == 0


# ─── Upload ──────────────────────────────────────────────────────────────────

async def upload_video(client: Client, chat_id: int,
                        file_path: str, thumb_path: str | None,
                        caption: str, status_msg: Message,
                        as_video: bool = True,
                        spoiler: bool = False):
    start = time.time()
    last_edit = [0.0]
    file_size = os.path.getsize(file_path)

    async def progress(current, total):
        now = time.time()
        if now - last_edit[0] < 3:
            return
        last_edit[0] = now
        pct = current * 100 / total if total else 0
        speed = current / max(now - start, 1)
        eta = (total - current) / max(speed, 1)
        bar = _progress_bar(pct)
        asyncio.ensure_future(_edit_safe(status_msg,
            f"<b>📤 Uploading...</b>\n"
            f"<code>[{bar}] {pct:.1f}%</code>\n"
            f"{current/1e6:.1f} MB / {total/1e6:.1f} MB\n"
            f"⚡ {speed/1e6:.2f} MB/s  ⏱ ETA {_hms(eta)}"))

    # get video dimensions for proper metadata
    info = probe(file_path)
    width = height = 0
    for stream in info.get("streams", []):
        if stream.get("codec_type") == "video":
            width  = stream.get("width", 0)
            height = stream.get("height", 0)
            break
    duration_s = int(get_duration(info))

    kwargs = dict(
        chat_id=chat_id,
        caption=caption,
        thumb=thumb_path,
        parse_mode=ParseMode.HTML,
        progress=progress,
        has_spoiler=spoiler,
    )

    if as_video:
        await client.send_video(
            video=file_path,
            width=width, height=height,
            duration=duration_s,
            supports_streaming=True,
            **kwargs,
        )
    else:
        await client.send_document(document=file_path, **kwargs)


# ─── Main encode pipeline ────────────────────────────────────────────────────

async def run_encode_pipeline(
    client: Client,
    message: Message,
    status_msg: Message,
    user_id: int,
):
    input_path = None
    output_path = None
    try:
        # 1. Fetch user prefs
        codec      = await get_codec(user_id)
        crf        = await get_crf(user_id)
        preset     = await get_preset(user_id)
        prefix     = await get_prefix(user_id) or AUTO_PREFIX
        suffix     = await get_suffix(user_id) or AUTO_SUFFIX
        rename_rule = await get_rename_rule(user_id)
        dual_audio = await get_dual_audio(user_id)
        bit_depth  = await get_bit_depth(user_id)

        # 2. Download
        await _edit_safe(status_msg, "<b>📥 Starting download...</b>")
        input_path = await download_file(client, message, status_msg)
        if not input_path:
            await _edit_safe(status_msg, "❌ Download failed.")
            return

        # 3. Probe
        info         = probe(input_path)
        duration     = get_duration(info)
        audio_count  = count_streams(info, "audio")
        sub_count    = count_streams(info, "subtitle")

        # 4. Build output path
        orig_name    = os.path.basename(input_path)
        codec_tag    = f"[{codec_display_name(codec)}]"
        new_name     = apply_rename_rules(
            orig_name, prefix=prefix, suffix=suffix,
            custom_rename=rename_rule, releaser=RELEASER,
            codec_tag=codec_tag,
        )
        new_name     = sanitize_filename(new_name)
        new_base     = os.path.splitext(new_name)[0]
        new_name     = new_base + ".mkv"
        output_path  = os.path.join(str(ENCODE_DIR), new_name)

        # 5. Build profile
        profile = EncodeProfile(
            codec=codec, crf=crf, preset=preset,
            bit_depth=bit_depth, dual_audio=dual_audio,
        )

        # 6. Encode
        await _edit_safe(status_msg, f"<b>⚙️ Starting encode [{codec_display_name(codec)}]...</b>")
        if ALLOW_ACTION:
            await client.send_chat_action(message.chat.id, "record_video")

        success = await encode_video(input_path, output_path, profile, duration, status_msg)
        if not success or not os.path.exists(output_path):
            await _edit_safe(status_msg, "❌ Encoding failed.")
            return

        # 7. Thumbnail
        thumb = await resolve_thumbnail(user_id, output_path)
        # If it's a file_id (from DB) use it; if it's a path verify it exists
        thumb_arg = thumb if (thumb and (thumb.startswith("/") and os.path.exists(thumb))) \
                    else (thumb if thumb and not thumb.startswith("/") else None)

        # 8. Caption
        cap_lines = [
            f"🎬 Codec: <code>{codec_display_name(codec)}</code>",
            f"🎵 Audio: {'Dual' if dual_audio and audio_count>=2 else 'Single'} | {bit_depth}-bit",
            f"📦 Size: {os.path.getsize(output_path)/1e6:.1f} MB",
        ]
        caption = build_caption(new_name, deco=CAP_DECO, extra_lines=cap_lines)

        # 9. Upload to requester
        await _edit_safe(status_msg, "<b>📤 Uploading...</b>")
        await upload_video(
            client, message.chat.id, output_path, thumb_arg,
            caption, status_msg,
            as_video=UPLOAD_AS_VIDEO,
            spoiler=UPLOAD_VIDEO_AS_SPOILER,
        )

        # 10. Dump to dump channel
        if DUMP_LEECH and DUMP_CHANNEL:
            await upload_video(
                client, DUMP_CHANNEL, output_path, thumb_arg,
                caption, status_msg,
                as_video=UPLOAD_AS_VIDEO,
            )

        await _edit_safe(status_msg, "✅ <b>Done!</b>")

    except Exception as e:
        err = traceback.format_exc()
        log.error(f"Error in encode pipeline: {err}")
        await _edit_safe(status_msg, f"❌ Error: <code>{e}</code>")
        if LOG_CHANNEL and LOGS_IN_CHANNEL:
            await client.send_message(LOG_CHANNEL,
                f"#ERROR\n<pre>{err[:3000]}</pre>", parse_mode=ParseMode.HTML)
    finally:
        for p in [input_path, output_path]:
            if p and os.path.exists(p):
                try:
                    os.remove(p)
                except Exception:
                    pass
