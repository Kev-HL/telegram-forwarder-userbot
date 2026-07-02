"""Telegram Forwarder Userbot"""

# Standard imports
import asyncio
import logging
import os
import random
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

# Third-party imports
from dotenv import load_dotenv
from telethon import TelegramClient, events

# Local imports
from comms import check_comms, CommsError
from config import load_config, ConfigError
from handlers import handle_new_message, handle_admin_command

# Set up logging
log_dir = Path("./logs")
log_dir.mkdir(exist_ok=True)
log_file = log_dir / "userbot.log"
size_handler = RotatingFileHandler(
    filename=log_file,
    maxBytes=10 * 1024 * 1024,  # 10 MB
    backupCount=5,
    encoding="utf-8",
)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        size_handler,
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)
logger.info(f"Logging to: {log_file}")
logging.getLogger("telethon").setLevel(logging.WARNING)

# Backoff settings for retrying on transient errors
MAX_BACKOFF = 900  # 15 minutes
BASE_BACKOFF = 30
MAX_JITTER = 3

# Load environment variables from .env file
load_dotenv()

# Fetch credentials
API_ID = os.getenv("TG_API_ID")
API_HASH = os.getenv("TG_API_HASH")

# Safety check for missing credentials
if not API_ID or not API_HASH:
    logger.error("Critical Error: TG_API_ID or TG_API_HASH missing in .env file.")
    sys.exit(1)


async def run():
    try:
        # Load config
        config = load_config()
        logger.info("Configuration loaded successfully.")

        # Initialize Telethon Userbot Client
        # First call creates a persistent 'userbot.session' file in your root folder
        client = TelegramClient("userbot", int(API_ID), API_HASH)

        # Register Listener for incoming messages
        @client.on(events.NewMessage(incoming=True))
        async def router(event):
            admin_id = config["admin_user"]["id"]
            source_ids = {s["id"] for s in config["feed_sources"]}

            # Admin command handler
            if event.sender_id == admin_id:
                await handle_admin_command(event, client, config)
                return

            # Feed message handler
            if event.chat_id in source_ids:
                await handle_new_message(event, config)
                return

        # Start client session loop, sync cache and wait for events
        logger.info("Initializing Telegram Client...")
        await client.start()
        logger.info("Syncing dialogs and populating local cache...")
        await client.get_dialogs()
        logger.info("Checking communication with admin and target...")
        await check_comms(client, config)
        logger.info("Telegram Forwarder Userbot is running!")
        await client.run_until_disconnected()
    finally:
        # Ensure client disconnects cleanly
        try:
            await client.disconnect()
        except Exception as e:
            logger.warning(f"Error during client disconnect: {e}")


async def supervisor():
    delay = BASE_BACKOFF

    while True:
        try:
            await run()
            # Disconnected cleanly: restart with small delay
            logger.warning("Client disconnected. Restarting soon...")
            await asyncio.sleep(3)
            delay = BASE_BACKOFF

        except ConfigError as e:
            # Likely not transient (invalid or corrupt config)
            logger.error(f"Fatal config error: {e}")
            raise

        except CommsError as e:
            # Admin or target unreachable, could be transient (network issues)
            jitter = random.uniform(0, MAX_JITTER)
            sleep_for = min(delay + jitter, MAX_BACKOFF)
            logger.error(f"Comms failure. Retrying in {sleep_for:.1f}s: {e}")
            await asyncio.sleep(sleep_for)
            delay = min(delay * 2, MAX_BACKOFF)

        except Exception as e:
            # Unexpected error, could be transient
            jitter = random.uniform(0, MAX_JITTER)
            sleep_for = min(delay + jitter, MAX_BACKOFF)
            logger.exception(f"Unexpected failure. Retrying in {sleep_for:.1f}s: {e}")
            await asyncio.sleep(sleep_for)
            delay = min(delay * 2, MAX_BACKOFF)


if __name__ == "__main__":
    try:
        asyncio.run(supervisor())
    except KeyboardInterrupt:
        logger.info("Application stopped by user.")
