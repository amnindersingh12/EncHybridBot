"""
__main__.py – Bot startup
"""
import asyncio
import logging
from pyrogram import Client
from bot.config import (
    APP_ID, API_HASH, BOT_TOKEN, WORKERS,
    LOCK_ON_STARTUP, ALWAYS_DEPLOY_LATEST,
)
from bot.handlers.handlers import register
from bot.db.database import set_lock

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
log = logging.getLogger("encbot")


async def main():
    if ALWAYS_DEPLOY_LATEST:
        import subprocess
        log.info("Pulling latest from upstream...")
        subprocess.run(["git", "pull"], check=False)

    app = Client(
        "encbot",
        api_id=APP_ID,
        api_hash=API_HASH,
        bot_token=BOT_TOKEN,
        workers=WORKERS,
    )

    register(app)

    async with app:
        if LOCK_ON_STARTUP:
            await set_lock(True)
            log.info("Encoding locked on startup.")

        me = await app.get_me()
        log.info(f"Bot started: @{me.username} ({me.id})")
        await asyncio.Event().wait()   # run forever


if __name__ == "__main__":
    # Python 3.10+ removed implicit event loop creation in get_event_loop().
    # Pyrogram 2.x calls get_event_loop() during import/sync bootstrap,
    # so we must set a loop on MainThread BEFORE asyncio.run().
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(main())
    finally:
        loop.close()
