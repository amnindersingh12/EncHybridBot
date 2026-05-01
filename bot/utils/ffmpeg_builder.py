"""
ffmpeg_builder.py  –  Build ffmpeg encode commands for AV1 / HEVC265 / HEVC264
Supports: 10-bit depth, dual audio, subtitle passthrough, custom CRF/preset.
"""
from __future__ import annotations
import re
from dataclasses import dataclass, field
from typing import Optional


CODECS = {
    "av1":      "libsvtav1",
    "hevc265":  "libx265",
    "hevc264":  "libx264",
}

PRESET_MAP = {
    "av1":     ["1","2","3","4","5","6","7","8","9","10","11","12","13"],
    "hevc265": ["ultrafast","superfast","veryfast","faster","fast","medium","slow","slower","veryslow","placebo"],
    "hevc264": ["ultrafast","superfast","veryfast","faster","fast","medium","slow","slower","veryslow","placebo"],
}

DEFAULT_CRF = {"av1": 30, "hevc265": 24, "hevc264": 22}
DEFAULT_PRESET = {"av1": "8", "hevc265": "ultrafast", "hevc264": "ultrafast"}


@dataclass
class EncodeProfile:
    codec: str = "hevc265"           # av1 | hevc265 | hevc264
    crf: Optional[int] = None
    preset: Optional[str] = None
    bit_depth: int = 10              # 8 or 10
    audio_tracks: list[int] = field(default_factory=list)   # source stream indices
    sub_tracks: list[int]   = field(default_factory=list)
    dual_audio: bool = True
    audio_lang_1: str = "jpn"
    audio_lang_2: str = "eng"
    custom_vf: str = ""              # extra -vf filters
    extra_args: str = ""             # appended verbatim


def _pixel_fmt(bit_depth: int, codec: str) -> str:
    if bit_depth == 10:
        return "yuv420p10le"
    return "yuv420p"


def _audio_args(profile: EncodeProfile, src_audio_count: int) -> list[str]:
    """
    Build audio mapping args.
    No audio: skip audio entirely.
    Dual-audio: keep both tracks as AAC 192k.
    Single: keep first track only.
    """
    if src_audio_count == 0:
        return ["-an"]

    args = []
    if profile.dual_audio and src_audio_count >= 2:
        # map both tracks
        args += ["-map", "0:a:0", "-map", "0:a:1"]
        args += ["-c:a:0", "aac", "-b:a:0", "192k",
                 "-metadata:s:a:0", f"language={profile.audio_lang_1}",
                 "-c:a:1", "aac", "-b:a:1", "192k",
                 "-metadata:s:a:1", f"language={profile.audio_lang_2}"]
    else:
        args += ["-map", "0:a:0"]
        args += ["-c:a:0", "aac", "-b:a:0", "192k"]
    return args


def build_command(
    input_path: str,
    output_path: str,
    profile: EncodeProfile,
    src_audio_count: int = 2,
    src_sub_count: int = 0,
    thumbnail_path: str = "",
) -> list[str]:
    """Return full ffmpeg argv list (no 'ffmpeg' prefix)."""

    lib   = CODECS.get(profile.codec, "libx265")
    crf   = profile.crf   if profile.crf   is not None else DEFAULT_CRF.get(profile.codec, 24)
    pset  = profile.preset if profile.preset else DEFAULT_PRESET.get(profile.codec, "ultrafast")
    pix   = _pixel_fmt(profile.bit_depth, profile.codec)

    # Validate preset: if a numeric AV1 preset leaked into x264/x265, reset it
    valid_presets = PRESET_MAP.get(profile.codec, [])
    if valid_presets and pset not in valid_presets:
        pset = DEFAULT_PRESET.get(profile.codec, "ultrafast")

    cmd: list[str] = ["-hide_banner", "-loglevel", "warning", "-stats", "-threads", "2"]
    cmd += ["-i", input_path]

    # ── Video ──
    cmd += ["-map", "0:v:0"]
    vf = f"scale=trunc(iw/2)*2:trunc(ih/2)*2"
    if profile.custom_vf:
        vf += f",{profile.custom_vf}"
    cmd += ["-vf", vf]
    cmd += ["-c:v", lib, "-crf", str(crf), "-preset", pset, "-pix_fmt", pix]

    # codec-specific params
    if profile.codec == "hevc265":
        x265_params = "pools=2:frame-threads=2:lookahead-slices=2:no-sao=1:bframes=3:aq-mode=1:rc-lookahead=10:ctu=32"
        cmd += ["-x265-params", x265_params]
    elif profile.codec == "hevc264":
        cmd += ["-profile:v", "high10" if profile.bit_depth == 10 else "high"]
        cmd += ["-level", "5.1", "-tune", "film"]
    elif profile.codec == "av1":
        cmd += ["-svtav1-params", "film-grain=8:film-grain-denoise=1"]

    # ── Audio ──
    cmd += _audio_args(profile, src_audio_count)

    # ── Subtitles ──
    if src_sub_count > 0:
        cmd += ["-map", "0:s?", "-c:s", "copy"]
    else:
        cmd += ["-sn"]

    # ── Container ──
    cmd += ["-movflags", "+faststart"]

    # ── Extra / mux args ──
    if profile.extra_args:
        cmd += profile.extra_args.split()

    cmd += ["-y", output_path]
    return cmd


def preset_for_codec(codec: str) -> list[str]:
    return PRESET_MAP.get(codec, [])


def codec_display_name(codec: str) -> str:
    return {"av1": "AV1 10-bit", "hevc265": "HEVC x265 10-bit", "hevc264": "HEVC x264 10-bit"}.get(codec, codec)
