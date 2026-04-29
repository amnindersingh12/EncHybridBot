"""
database.py – MongoDB async layer (Motor)
Stores per-user settings, encoding queue, global config.
"""
from __future__ import annotations
import motor.motor_asyncio
from bot.config import DATABASE_URL, DBNAME

_client = None
_db = None


async def get_db():
    global _client, _db
    if _db is None:
        _client = motor.motor_asyncio.AsyncIOMotorClient(DATABASE_URL)
        _db = _client[DBNAME]
    return _db


# ─── User settings ────────────────────────────────────────────────────────────

async def get_user_settings(user_id: int) -> dict:
    db = await get_db()
    doc = await db.users.find_one({"_id": user_id})
    if doc is None:
        return {}
    return doc


async def update_user_settings(user_id: int, data: dict):
    db = await get_db()
    await db.users.update_one({"_id": user_id}, {"$set": data}, upsert=True)


async def get_user_field(user_id: int, field: str, default=None):
    doc = await get_user_settings(user_id)
    return doc.get(field, default)


async def set_user_field(user_id: int, field: str, value):
    await update_user_settings(user_id, {field: value})


# ─── Convenience wrappers ─────────────────────────────────────────────────────

async def get_thumbnail(user_id: int) -> str | None:
    return await get_user_field(user_id, "thumbnail")

async def set_thumbnail(user_id: int, file_id: str):
    await set_user_field(user_id, "thumbnail", file_id)

async def del_thumbnail(user_id: int):
    db = await get_db()
    await db.users.update_one({"_id": user_id}, {"$unset": {"thumbnail": ""}})


async def get_codec(user_id: int) -> str:
    from bot.config import DEFAULT_CODEC
    return await get_user_field(user_id, "codec", DEFAULT_CODEC)

async def set_codec(user_id: int, codec: str):
    await set_user_field(user_id, "codec", codec)


async def get_crf(user_id: int) -> int:
    from bot.config import DEFAULT_CRF
    return await get_user_field(user_id, "crf", DEFAULT_CRF)

async def set_crf(user_id: int, crf: int):
    await set_user_field(user_id, "crf", crf)


async def get_preset(user_id: int) -> str:
    from bot.config import DEFAULT_PRESET
    return await get_user_field(user_id, "preset", DEFAULT_PRESET)

async def set_preset(user_id: int, preset: str):
    await set_user_field(user_id, "preset", preset)


async def get_prefix(user_id: int) -> str:
    return await get_user_field(user_id, "prefix", "")

async def set_prefix(user_id: int, value: str):
    await set_user_field(user_id, "prefix", value)


async def get_suffix(user_id: int) -> str:
    return await get_user_field(user_id, "suffix", "")

async def set_suffix(user_id: int, value: str):
    await set_user_field(user_id, "suffix", value)


async def get_rename_rule(user_id: int) -> str:
    return await get_user_field(user_id, "rename_rule", "")

async def set_rename_rule(user_id: int, rule: str):
    await set_user_field(user_id, "rename_rule", rule)


async def get_dual_audio(user_id: int) -> bool:
    from bot.config import DUAL_AUDIO
    return await get_user_field(user_id, "dual_audio", DUAL_AUDIO)

async def set_dual_audio(user_id: int, val: bool):
    await set_user_field(user_id, "dual_audio", val)


async def get_bit_depth(user_id: int) -> int:
    return await get_user_field(user_id, "bit_depth", 10)

async def set_bit_depth(user_id: int, val: int):
    await set_user_field(user_id, "bit_depth", val)


# ─── Queue ────────────────────────────────────────────────────────────────────

async def add_to_queue(task: dict):
    db = await get_db()
    await db.queue.insert_one(task)

async def pop_next_task() -> dict | None:
    db = await get_db()
    return await db.queue.find_one_and_delete({}, sort=[("_id", 1)])

async def queue_size() -> int:
    db = await get_db()
    return await db.queue.count_documents({})

async def clear_queue():
    db = await get_db()
    await db.queue.delete_many({})


# ─── Global lock ──────────────────────────────────────────────────────────────

async def is_locked() -> bool:
    db = await get_db()
    doc = await db.global_state.find_one({"_id": "state"})
    return bool(doc and doc.get("locked"))

async def set_lock(val: bool):
    db = await get_db()
    await db.global_state.update_one({"_id": "state"}, {"$set": {"locked": val}}, upsert=True)
