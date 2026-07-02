"""Telegram Forwarder Userbot"""

# Standard imports
import asyncio
import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

# Third-party imports
from dotenv import load_dotenv
from telethon import TelegramClient, events

# Local imports
from comms import check_comms, CommsError
from config import load_config, ConfigError
from handlers import handle_new_message, handle_admin_command, HandlerError

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


# Load environment variables from .env file
load_dotenv()

# Fetch credentials
API_ID = os.getenv("TG_API_ID")
API_HASH = os.getenv("TG_API_HASH")

# Safety check for missing credentials
if not API_ID or not API_HASH:
    logger.error("Critical Error: TG_API_ID or TG_API_HASH missing in .env file.")
    sys.exit(1)


async def main():
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


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Application stopped by user.")
    except ConfigError as e:
        logger.error(f"Application stopped. Configuration error: {e}")
        sys.exit(1)
    except CommsError as e:
        logger.error(f"Application stopped. Communication error: {e}")
        sys.exit(1)
    except HandlerError as e:
        logger.error(f"Application stopped. Handler error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Application stopped. Unexpected error: {e}", exc_info=True)
        sys.exit(1)
