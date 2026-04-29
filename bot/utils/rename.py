"""
rename.py – filename transformation utilities
"""
from __future__ import annotations
import re
import os


def apply_rename_rules(
    filename: str,
    prefix: str = "",
    suffix: str = "",
    custom_rename: str = "",   # "pattern|replacement"
    releaser: str = "",
    codec_tag: str = "",       # e.g. "[x265 10bit]"
) -> str:
    """
    Transform filename:
    1. Strip extension
    2. Apply regex custom_rename   (pattern|replacement)
    3. Prepend prefix
    4. Append suffix
    5. Append releaser tag
    6. Append codec tag
    7. Re-attach extension
    """
    base, ext = os.path.splitext(filename)

    # 2. custom regex rename
    if custom_rename and "|" in custom_rename:
        pat, rep = custom_rename.split("|", 1)
        try:
            base = re.sub(pat, rep, base)
        except re.error:
            pass

    # 3-6
    if prefix:
        base = prefix + base
    if suffix:
        base = base + suffix
    if releaser:
        base = f"{base} [{releaser}]"
    if codec_tag:
        base = f"{base} {codec_tag}"

    return base + ext


def build_caption(
    filename: str,
    deco: str = "",
    extra_lines: list[str] | None = None,
) -> str:
    """Build Telegram caption from filename + optional decorator + extra info lines."""
    parts = []
    if deco:
        parts.append(deco)
    parts.append(f"<b>{filename}</b>")
    if extra_lines:
        parts.extend(extra_lines)
    return "\n".join(parts)


def sanitize_filename(name: str) -> str:
    """Remove/replace characters unsafe for filenames."""
    name = re.sub(r'[\\/*?:"<>|]', "_", name)
    name = re.sub(r'\s+', " ", name).strip()
    return name
