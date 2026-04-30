"""
handlers.py – Pyrogram command & message handlers
"""
from __future__ import annotations
import asyncio
import os
from pathlib import Path

from pyrogram import Client, filters
from pyrogram.enums import ParseMode
from pyrogram.types import (
    Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
)

from bot.config import (
    OWNER, TEMP_USERS, MAX_QUEUE, LOCK_ON_STARTUP,
    SAMPLE_DURATION, SCREENSHOT_COUNT,
)
from bot.encoder import (
    run_encode_pipeline, generate_sample, generate_screenshots,
    download_file, probe, get_duration, DOWNLOAD_DIR, ENCODE_DIR,
)
from bot.utils.ffmpeg_builder import CODECS, preset_for_codec, codec_display_name
from bot.db.database import (
    get_codec, set_codec, get_crf, set_crf,
    get_preset, set_preset,
    get_prefix, set_prefix,
    get_suffix, set_suffix,
    get_rename_rule, set_rename_rule,
    get_thumbnail, set_thumbnail, del_thumbnail,
    get_dual_audio, set_dual_audio,
    get_bit_depth, set_bit_depth,
    queue_size, is_locked, set_lock, clear_queue,
    get_user_settings,
)

# In-memory encode semaphore (1 at a time per config, or more via WORKERS)
_encode_sem = asyncio.Semaphore(1)

# ─── Auth helpers ─────────────────────────────────────────────────────────────

def is_authorized(user_id: int) -> bool:
    return user_id == OWNER or user_id in TEMP_USERS


def owner_only(func):
    async def wrapper(client, message, *args, **kwargs):
        if message.from_user.id != OWNER:
            return await message.reply("⛔ Owner only.")
        return await func(client, message, *args, **kwargs)
    wrapper.__name__ = func.__name__
    return wrapper


# ─── /start ──────────────────────────────────────────────────────────────────

async def cmd_start(client: Client, message: Message):
    await message.reply(
        "👋 <b>EncHybrid Bot</b>\n\n"
        "Send me a video and I'll encode it to <b>AV1 / HEVC x265 / HEVC x264</b> "
        "(10-bit, dual audio).\n\n"
        "Use /help to see all commands.",
        parse_mode=ParseMode.HTML,
    )


# ─── /help ───────────────────────────────────────────────────────────────────

HELP_TEXT = """
<b>EncHybrid Bot — Commands</b>

<b>Encoding</b>
/encode — encode replied/forwarded video
/sample — generate sample clip
/screenshots — generate screenshots
/queue — view queue status
/cancel — cancel current job

<b>Codec / Quality</b>
/setcodec — choose AV1 / HEVC265 / HEVC264
/setcrf [n] — set CRF (default 24)
/setpreset — choose encode preset
/setbitdepth [8|10] — set bit depth

<b>Audio</b>
/dualaudio [on|off] — toggle dual audio
/setlang1 [lang] — set primary audio lang (e.g. jpn)
/setlang2 [lang] — set secondary audio lang (e.g. eng)

<b>Rename / Caption</b>
/setprefix [text] — auto-prefix for output filenames
/setsuffix [text] — auto-suffix for output filenames
/setrename [pattern|replacement] — regex autorename
/clearrename — remove rename rule

<b>Thumbnail</b>
/setthumb — set custom thumbnail (reply to image)
/delthumb — delete custom thumbnail
/viewthumb — preview current thumbnail

<b>Settings</b>
/mysettings — view all your current settings
/reset — reset all settings to default

<b>Admin</b>
/lock — lock encoding
/unlock — unlock encoding
/clearqueue — clear all queued tasks
/broadcast [text] — broadcast message (owner)
/stats — bot stats
"""


async def cmd_help(client: Client, message: Message):
    await message.reply(HELP_TEXT, parse_mode=ParseMode.HTML)


# ─── Video handler ───────────────────────────────────────────────────────────

async def handle_video(client: Client, message: Message):
    user_id = message.from_user.id
    if not is_authorized(user_id):
        return await message.reply("⛔ Not authorized.")
    if await is_locked():
        return await message.reply("🔒 Encoding is locked.")
    qs = await queue_size()
    if qs >= MAX_QUEUE:
        return await message.reply(f"⏳ Queue full ({qs}/{MAX_QUEUE}). Try later.")

    status_msg = await message.reply("⏳ <b>Queued...</b>", parse_mode=ParseMode.HTML)

    async with _encode_sem:
        await run_encode_pipeline(client, message, status_msg, user_id)


# ─── /encode ─────────────────────────────────────────────────────────────────

async def cmd_encode(client: Client, message: Message):
    if message.reply_to_message and (
        message.reply_to_message.video or message.reply_to_message.document
    ):
        await handle_video(client, message.reply_to_message)
    else:
        await message.reply("↩️ Reply to a video/document to encode it.")


# ─── /sample ─────────────────────────────────────────────────────────────────

async def cmd_sample(client: Client, message: Message):
    target = message.reply_to_message
    if not target or not (target.video or target.document):
        return await message.reply("↩️ Reply to a video.")
    user_id = message.from_user.id
    if not is_authorized(user_id):
        return await message.reply("⛔ Not authorized.")
    status = await message.reply("📥 Downloading for sample...")
    path = await download_file(client, target, status)
    if not path:
        return await status.edit("❌ Download failed.")
    await status.edit(f"✂️ Generating {SAMPLE_DURATION}s sample...")
    sample = await generate_sample(path, duration=SAMPLE_DURATION)
    if sample:
        await client.send_video(message.chat.id, sample, caption="🎬 Sample video")
        os.remove(sample)
    else:
        await status.edit("❌ Sample generation failed.")
    os.remove(path)
    await status.delete()


# ─── /screenshots ─────────────────────────────────────────────────────────────

async def cmd_screenshots(client: Client, message: Message):
    target = message.reply_to_message
    if not target or not (target.video or target.document):
        return await message.reply("↩️ Reply to a video.")
    user_id = message.from_user.id
    if not is_authorized(user_id):
        return await message.reply("⛔ Not authorized.")
    status = await message.reply("📥 Downloading for screenshots...")
    path = await download_file(client, target, status)
    if not path:
        return await status.edit("❌ Download failed.")
    info = probe(path)
    dur = get_duration(info)
    await status.edit(f"📸 Capturing {SCREENSHOT_COUNT} screenshots...")
    shots = await generate_screenshots(path, count=SCREENSHOT_COUNT, duration=dur)
    if shots:
        media_group = []
        from pyrogram.types import InputMediaPhoto
        for s in shots:
            media_group.append(InputMediaPhoto(s))
        await client.send_media_group(message.chat.id, media_group)
        for s in shots:
            os.remove(s)
    else:
        await status.edit("❌ Screenshots failed.")
    os.remove(path)
    await status.delete()


# ─── /setcodec ───────────────────────────────────────────────────────────────

async def cmd_setcodec(client: Client, message: Message):
    current = await get_codec(message.from_user.id)
    buttons = [
        [InlineKeyboardButton(f"{'✅ ' if current=='av1' else ''}AV1 10-bit", callback_data="codec|av1")],
        [InlineKeyboardButton(f"{'✅ ' if current=='hevc265' else ''}HEVC x265 10-bit", callback_data="codec|hevc265")],
        [InlineKeyboardButton(f"{'✅ ' if current=='hevc264' else ''}HEVC x264 10-bit", callback_data="codec|hevc264")],
    ]
    await message.reply("🎛 Choose encode codec:", reply_markup=InlineKeyboardMarkup(buttons))


async def cb_codec(client: Client, query: CallbackQuery):
    _, codec = query.data.split("|")
    await set_codec(query.from_user.id, codec)
    await query.answer(f"✅ Codec set to {codec_display_name(codec)}")
    await query.message.edit_text(f"✅ Codec: <b>{codec_display_name(codec)}</b>", parse_mode=ParseMode.HTML)


# ─── /setcrf ─────────────────────────────────────────────────────────────────

async def cmd_setcrf(client: Client, message: Message):
    parts = message.text.split()
    if len(parts) < 2 or not parts[1].isdigit():
        cur = await get_crf(message.from_user.id)
        return await message.reply(f"Current CRF: <b>{cur}</b>\nUsage: /setcrf 24", parse_mode=ParseMode.HTML)
    crf = int(parts[1])
    if not 0 <= crf <= 63:
        return await message.reply("CRF must be 0–63.")
    await set_crf(message.from_user.id, crf)
    await message.reply(f"✅ CRF set to <b>{crf}</b>", parse_mode=ParseMode.HTML)


# ─── /setpreset ──────────────────────────────────────────────────────────────

async def cmd_setpreset(client: Client, message: Message):
    user_id = message.from_user.id
    codec = await get_codec(user_id)
    presets = preset_for_codec(codec)
    current = await get_preset(user_id)
    buttons = [
        [InlineKeyboardButton(f"{'✅ ' if p==current else ''}{p}", callback_data=f"preset|{p}")]
        for p in presets
    ]
    await message.reply(f"🎛 Choose preset for <b>{codec_display_name(codec)}</b>:",
                        reply_markup=InlineKeyboardMarkup(buttons), parse_mode=ParseMode.HTML)


async def cb_preset(client: Client, query: CallbackQuery):
    _, preset = query.data.split("|")
    await set_preset(query.from_user.id, preset)
    await query.answer(f"✅ Preset: {preset}")
    await query.message.edit_text(f"✅ Preset: <b>{preset}</b>", parse_mode=ParseMode.HTML)


# ─── /setbitdepth ─────────────────────────────────────────────────────────────

async def cmd_setbitdepth(client: Client, message: Message):
    parts = message.text.split()
    if len(parts) < 2 or parts[1] not in ("8", "10"):
        cur = await get_bit_depth(message.from_user.id)
        return await message.reply(f"Current bit depth: <b>{cur}</b>\nUsage: /setbitdepth 8|10",
                                   parse_mode=ParseMode.HTML)
    await set_bit_depth(message.from_user.id, int(parts[1]))
    await message.reply(f"✅ Bit depth: <b>{parts[1]}</b>", parse_mode=ParseMode.HTML)


# ─── /dualaudio ───────────────────────────────────────────────────────────────

async def cmd_dualaudio(client: Client, message: Message):
    parts = message.text.split()
    user_id = message.from_user.id
    if len(parts) < 2:
        cur = await get_dual_audio(user_id)
        return await message.reply(f"Dual audio: <b>{'on' if cur else 'off'}</b>\nUsage: /dualaudio on|off",
                                   parse_mode=ParseMode.HTML)
    val = parts[1].lower() == "on"
    await set_dual_audio(user_id, val)
    await message.reply(f"✅ Dual audio: <b>{'on' if val else 'off'}</b>", parse_mode=ParseMode.HTML)


# ─── /setprefix / /setsuffix ─────────────────────────────────────────────────

async def cmd_setprefix(client: Client, message: Message):
    parts = message.text.split(None, 1)
    user_id = message.from_user.id
    if len(parts) < 2:
        cur = await get_prefix(user_id)
        return await message.reply(f"Current prefix: <code>{cur or '(none)'}</code>\nUsage: /setprefix [text]",
                                   parse_mode=ParseMode.HTML)
    await set_prefix(user_id, parts[1].strip())
    await message.reply(f"✅ Prefix: <code>{parts[1].strip()}</code>", parse_mode=ParseMode.HTML)


async def cmd_setsuffix(client: Client, message: Message):
    parts = message.text.split(None, 1)
    user_id = message.from_user.id
    if len(parts) < 2:
        cur = await get_suffix(user_id)
        return await message.reply(f"Current suffix: <code>{cur or '(none)'}</code>\nUsage: /setsuffix [text]",
                                   parse_mode=ParseMode.HTML)
    await set_suffix(user_id, parts[1].strip())
    await message.reply(f"✅ Suffix: <code>{parts[1].strip()}</code>", parse_mode=ParseMode.HTML)


# ─── /setrename / /clearrename ───────────────────────────────────────────────

async def cmd_setrename(client: Client, message: Message):
    parts = message.text.split(None, 1)
    user_id = message.from_user.id
    if len(parts) < 2 or "|" not in parts[1]:
        cur = await get_rename_rule(user_id)
        return await message.reply(
            f"Current rule: <code>{cur or '(none)'}</code>\n"
            "Usage: /setrename pattern|replacement\n"
            "Example: /setrename \\[BD\\]|[Blu-ray]",
            parse_mode=ParseMode.HTML)
    await set_rename_rule(user_id, parts[1].strip())
    await message.reply(f"✅ Rename rule set: <code>{parts[1].strip()}</code>", parse_mode=ParseMode.HTML)


async def cmd_clearrename(client: Client, message: Message):
    await set_rename_rule(message.from_user.id, "")
    await message.reply("✅ Rename rule cleared.")


# ─── /setthumb / /delthumb / /viewthumb ──────────────────────────────────────

async def cmd_setthumb(client: Client, message: Message):
    target = message.reply_to_message
    if not target or not target.photo:
        return await message.reply("↩️ Reply to an image to set as thumbnail.")
    file_id = target.photo.file_id
    await set_thumbnail(message.from_user.id, file_id)
    await message.reply("✅ Custom thumbnail saved.")


async def cmd_delthumb(client: Client, message: Message):
    await del_thumbnail(message.from_user.id)
    await message.reply("✅ Thumbnail deleted.")


async def cmd_viewthumb(client: Client, message: Message):
    fid = await get_thumbnail(message.from_user.id)
    if not fid:
        return await message.reply("No custom thumbnail set.")
    await client.send_photo(message.chat.id, fid, caption="🖼 Your current thumbnail")


# ─── /mysettings ─────────────────────────────────────────────────────────────

async def cmd_mysettings(client: Client, message: Message):
    uid = message.from_user.id
    codec = await get_codec(uid)
    crf = await get_crf(uid)
    preset = await get_preset(uid)
    prefix = await get_prefix(uid)
    suffix = await get_suffix(uid)
    rule = await get_rename_rule(uid)
    dual = await get_dual_audio(uid)
    depth = await get_bit_depth(uid)
    has_thumb = bool(await get_thumbnail(uid))

    text = (
        f"<b>⚙️ Your Settings</b>\n\n"
        f"🎛 Codec: <code>{codec_display_name(codec)}</code>\n"
        f"📊 CRF: <code>{crf}</code>\n"
        f"⚡ Preset: <code>{preset}</code>\n"
        f"🔢 Bit Depth: <code>{depth}</code>\n"
        f"🎵 Dual Audio: <code>{'on' if dual else 'off'}</code>\n"
        f"📝 Prefix: <code>{prefix or '(none)'}</code>\n"
        f"📝 Suffix: <code>{suffix or '(none)'}</code>\n"
        f"🔄 Rename Rule: <code>{rule or '(none)'}</code>\n"
        f"🖼 Custom Thumb: <code>{'yes' if has_thumb else 'no'}</code>"
    )
    await message.reply(text, parse_mode=ParseMode.HTML)


# ─── /reset ──────────────────────────────────────────────────────────────────

async def cmd_reset(client: Client, message: Message):
    from bot.db.database import get_db
    db = await get_db()
    await db.users.delete_one({"_id": message.from_user.id})
    await message.reply("✅ Settings reset to defaults.")


# ─── /queue ──────────────────────────────────────────────────────────────────

async def cmd_queue(client: Client, message: Message):
    qs = await queue_size()
    locked = await is_locked()
    await message.reply(
        f"📋 Queue: <b>{qs}</b> tasks\n🔒 Locked: <b>{'yes' if locked else 'no'}</b>",
        parse_mode=ParseMode.HTML)


# ─── /lock / /unlock ─────────────────────────────────────────────────────────

@owner_only
async def cmd_lock(client: Client, message: Message):
    await set_lock(True)
    await message.reply("🔒 Encoding locked.")


@owner_only
async def cmd_unlock(client: Client, message: Message):
    await set_lock(False)
    await message.reply("🔓 Encoding unlocked.")


@owner_only
async def cmd_clearqueue(client: Client, message: Message):
    await clear_queue()
    await message.reply("✅ Queue cleared.")


# ─── /stats ───────────────────────────────────────────────────────────────────

async def cmd_stats(client: Client, message: Message):
    qs = await queue_size()
    import psutil, platform
    cpu = psutil.cpu_percent()
    ram = psutil.virtual_memory()
    disk = psutil.disk_usage("/tmp")
    await message.reply(
        f"<b>📊 Bot Stats</b>\n\n"
        f"🖥 CPU: <code>{cpu}%</code>\n"
        f"💾 RAM: <code>{ram.used//1e6:.0f} / {ram.total//1e6:.0f} MB</code>\n"
        f"💿 Disk (/tmp): <code>{disk.used//1e9:.1f} / {disk.total//1e9:.1f} GB</code>\n"
        f"📋 Queue: <code>{qs}</code>",
        parse_mode=ParseMode.HTML)


# ─── /broadcast ──────────────────────────────────────────────────────────────

@owner_only
async def cmd_broadcast(client: Client, message: Message):
    parts = message.text.split(None, 1)
    if len(parts) < 2:
        return await message.reply("Usage: /broadcast [message]")
    from bot.db.database import get_db
    db = await get_db()
    text = parts[1]
    count = 0
    async for user in db.users.find({}, {"_id": 1}):
        try:
            await client.send_message(user["_id"], text)
            count += 1
            await asyncio.sleep(0.1)
        except Exception:
            pass
    await message.reply(f"✅ Broadcast sent to {count} users.")


# ─── Register all handlers ────────────────────────────────────────────────────

def register(app: Client):
    app.on_message(filters.command("start"))(cmd_start)
    app.on_message(filters.command("help"))(cmd_help)
    app.on_message(filters.command("encode"))(cmd_encode)
    app.on_message(filters.command("sample"))(cmd_sample)
    app.on_message(filters.command("screenshots"))(cmd_screenshots)
    app.on_message(filters.command("setcodec"))(cmd_setcodec)
    app.on_message(filters.command("setcrf"))(cmd_setcrf)
    app.on_message(filters.command("setpreset"))(cmd_setpreset)
    app.on_message(filters.command("setbitdepth"))(cmd_setbitdepth)
    app.on_message(filters.command("dualaudio"))(cmd_dualaudio)
    app.on_message(filters.command("setprefix"))(cmd_setprefix)
    app.on_message(filters.command("setsuffix"))(cmd_setsuffix)
    app.on_message(filters.command("setrename"))(cmd_setrename)
    app.on_message(filters.command("clearrename"))(cmd_clearrename)
    app.on_message(filters.command("setthumb"))(cmd_setthumb)
    app.on_message(filters.command("delthumb"))(cmd_delthumb)
    app.on_message(filters.command("viewthumb"))(cmd_viewthumb)
    app.on_message(filters.command("mysettings"))(cmd_mysettings)
    app.on_message(filters.command("reset"))(cmd_reset)
    app.on_message(filters.command("queue"))(cmd_queue)
    app.on_message(filters.command("lock"))(cmd_lock)
    app.on_message(filters.command("unlock"))(cmd_unlock)
    app.on_message(filters.command("clearqueue"))(cmd_clearqueue)
    app.on_message(filters.command("stats"))(cmd_stats)
    app.on_message(filters.command("broadcast"))(cmd_broadcast)

    # Video/document auto-handler
    app.on_message(filters.private & (filters.video | filters.document))(handle_video)

    # Callbacks
    app.on_callback_query(filters.regex(r"^codec\|"))(cb_codec)
    app.on_callback_query(filters.regex(r"^preset\|"))(cb_preset)
