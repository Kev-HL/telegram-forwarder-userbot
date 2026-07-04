"""Telegram Forwarder Userbot"""

# Standard imports
import asyncio
import logging
import os
import random
import sys
from datetime import datetime, timezone
from logging.handlers import RotatingFileHandler

# Third-party imports
from dotenv import load_dotenv
from telethon import TelegramClient, events

# Local imports
from tfu.comms import check_comms, CommsError
from tfu.config import load_config, ConfigError
from tfu.handlers import handle_new_message, handle_admin_command
from tfu.paths import DATA_DIR, SESSION_BASENAME

# Set up logging
log_dir = DATA_DIR / "logs"
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

# Heartbeat settings for monitoring
HEARTBEAT_INTERVAL = 300  # 5 min
STARTED_AT = datetime.now(timezone.utc)
PROCESSED_MESSAGES = 0
PROCESSED_COMMANDS = 0
FORWARDED_MESSAGES = 0

# Load environment variables from .env file
load_dotenv()

# Fetch credentials
API_ID = os.getenv("TG_API_ID")
API_HASH = os.getenv("TG_API_HASH")

# Safety check for missing credentials
if not API_ID or not API_HASH:
    logger.error("Critical Error: TG_API_ID or TG_API_HASH missing in .env file.")
    sys.exit(1)


async def heartbeat():
    while True:
        now = datetime.now(timezone.utc)
        uptime = now - STARTED_AT
        uptime_s = int(uptime.total_seconds())
        h, rem = divmod(uptime_s, 3600)
        m, s = divmod(rem, 60)

        logger.info(
            "heartbeat | uptime=%02d:%02d:%02d | processed_messages=%d"
            " | processed_commands=%d | forwarded_messages=%d",
            h,
            m,
            s,
            PROCESSED_MESSAGES,
            PROCESSED_COMMANDS,
            FORWARDED_MESSAGES,
        )
        await asyncio.sleep(HEARTBEAT_INTERVAL)


async def run():
    heartbeat_task = None
    client = None
    try:
        # Load config
        config = load_config()
        logger.info("Configuration loaded successfully.")

        # Initialize Telethon Userbot Client
        # First call creates a persistent 'userbot.session' file in your root folder
        client = TelegramClient(str(SESSION_BASENAME), int(API_ID), API_HASH)

        # Register Listener for incoming messages
        @client.on(events.NewMessage(incoming=True))
        async def router(event):
            global PROCESSED_MESSAGES
            global PROCESSED_COMMANDS
            global FORWARDED_MESSAGES

            admin_id = config["admin_user"]["id"]
            source_ids = {s["id"] for s in config["feed_sources"]}
            PROCESSED_MESSAGES += 1

            # Admin command handler
            if event.sender_id == admin_id:
                await handle_admin_command(event, client, config)
                PROCESSED_COMMANDS += 1
                return

            # Feed message handler
            if event.chat_id in source_ids:
                await handle_new_message(event, config)
                FORWARDED_MESSAGES += 1
                return

        # Start client session loop, sync cache and wait for events
        logger.info("Initializing Telegram Client...")
        await client.start()
        logger.info("Syncing dialogs and populating local cache...")
        await client.get_dialogs()
        logger.info("Checking communication with admin and target...")
        await check_comms(client, config)
        logger.info("Starting heartbeat task...")
        heartbeat_task = asyncio.create_task(heartbeat())
        logger.info("Telegram Forwarder Userbot is running!")
        await client.run_until_disconnected()
    finally:
        # Cancel heartbeat
        if heartbeat_task is not None:
            heartbeat_task.cancel()
            try:
                await heartbeat_task
            except asyncio.CancelledError:
                pass

        # Ensure client disconnects cleanly
        if client is not None:
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
            sys.exit(1)

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
