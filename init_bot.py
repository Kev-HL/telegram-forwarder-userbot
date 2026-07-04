"""Telegram Forwarder Userbot setup script."""

# Standard imports
import logging
import sys
from datetime import datetime
from pathlib import Path

# Third-party imports
from dotenv import dotenv_values, set_key
from inputimeout import inputimeout, TimeoutOccurred
from telethon import TelegramClient

# Local imports
from comms import get_entity_id, CommsError
from config import load_config, save_config
from paths import CONFIG_PATH, DATA_DIR, ENV_PATH, SESSION_BASENAME

# Set up logging
log_dir = DATA_DIR / "logs"
log_dir.mkdir(exist_ok=True)
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
log_file = log_dir / f"userbot_setup_{timestamp}.log"
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)
logger.info(f"Logging to: {log_file}")
logging.getLogger("telethon").setLevel(logging.WARNING)


def main():
    # Initial message
    logger.info("Starting setup for Telegram Forwarder Userbot.")

    # ========== API Credentials Setup ==========
    logger.info("Starting API credentials setup.")
    # Create .env file if it doesn't exist
    if not ENV_PATH.is_file():
        logger.info(".env file not found. Creating a new one.")
        ENV_PATH.touch()
    else:
        logger.info(".env file already exists. Checking contents...")

    # Initialize API values
    TG_API_ID = None
    TG_API_HASH = None

    # Load .env values, and prompt to overwrite if API keys already exist
    env_vars = dotenv_values(ENV_PATH)
    if "TG_API_ID" in env_vars and "TG_API_HASH" in env_vars:
        TG_API_ID = env_vars["TG_API_ID"]
        TG_API_HASH = env_vars["TG_API_HASH"]
        logger.info("API credentials found in existing .env")
        credentials_exist = True
        credentials_overwrite = None
        while credentials_overwrite not in ["y", "yes", "n", "no"]:
            try:
                credentials_overwrite = inputimeout(
                    prompt="Do you want to overwrite the existing API keys? (y/n): ",
                    timeout=60,
                ).lower()
            except TimeoutOccurred:
                logger.info("Timeout occurred during input. Exiting setup.")
                sys.exit(0)
            if credentials_overwrite not in ["y", "yes", "n", "no"]:
                logger.info("Invalid input. Please enter 'y' or 'n'.")
        credentials_overwrite = credentials_overwrite in ["y", "yes"]
    else:
        logger.info("No API credentials found in .env. Proceeding to create new ones.")
        credentials_exist = False
        credentials_overwrite = True  # To bound value

    # Prompt for new API credentials if needed (dont exist or user wants to overwrite)
    if not credentials_exist or (credentials_exist and credentials_overwrite):
        try:
            TG_API_ID = inputimeout(prompt="Enter new TG_API_ID: ", timeout=60).strip()
            TG_API_HASH = inputimeout(
                prompt="Enter new TG_API_HASH: ", timeout=60
            ).strip()
        except TimeoutOccurred:
            logger.info("Timeout occurred during input. Exiting setup.")
            sys.exit(0)
        set_key(ENV_PATH, "TG_API_ID", TG_API_ID)
        set_key(ENV_PATH, "TG_API_HASH", TG_API_HASH)
        logger.info("API credentials updated successfully.")

    # ========== config.json Setup ==========
    # Load existing config.json if it exists
    if CONFIG_PATH.is_file():
        logger.info("config.json found. Loading existing configuration.")
        config = load_config()
    else:
        logger.info("config.json not found. Creating a new configuration.")
        config = {
            "feed_sources": [],
            "forward_target": {},
            "admin_user": {},
            "keywords": [],
        }

    # Initialize TelegramClient for fetching IDs
    try:
        client = TelegramClient(str(SESSION_BASENAME), int(TG_API_ID), TG_API_HASH)
    except Exception as e:
        logger.error(f"Failed to initialize TelegramClient: {e}")
        sys.exit(1)

    logger.info("Starting admin user and forward target setup")

    # Update admin user if it exists, or prompt for new one
    admin_user = config.get("admin_user", {})
    if admin_user.get("id", None) is not None:
        logger.info(f"Admin user ID found in config.json: {admin_user['id']}")
        admin_overwrite = None
        while admin_overwrite not in ["y", "yes", "n", "no"]:
            try:
                admin_overwrite = inputimeout(
                    prompt="Do you want to overwrite the existing admin user? (y/n): ",
                    timeout=60,
                ).lower()
            except TimeoutOccurred:
                logger.info("Timeout occurred during input. Exiting setup.")
                sys.exit(0)
            if admin_overwrite not in ["y", "yes", "n", "no"]:
                logger.info("Invalid input. Please enter 'y' or 'n'.")
        admin_overwrite = admin_overwrite in ["y", "yes"]
    else:
        logger.info("No admin user ID found. Proceeding to create a new one.")
        admin_overwrite = True  # To bound value
    if admin_overwrite:
        # Prompt for new admin username
        try:
            admin_username = inputimeout(
                prompt="Enter new admin username (@name): ", timeout=60
            ).strip()
        except TimeoutOccurred:
            logger.info("Timeout occurred during input. Exiting setup.")
            sys.exit(0)
        # Fetch ID
        try:
            logger.info(f"Fetching Telegram ID for admin username: {admin_username}")
            with client:
                # Execute the async function synchronously using the client's loop
                admin_id = client.loop.run_until_complete(
                    get_entity_id(client, admin_username)
                )
                logger.info(f"Fetched admin ID: {admin_id}")
        except CommsError as e:
            logger.error(f"Failed to fetch admin user ID: {e}")
            sys.exit(1)
        config["admin_user"] = {"id": admin_id, "username": admin_username}

    # Update forward target if it exists, or prompt for new one
    forward_target = config.get("forward_target", {})
    if forward_target.get("id", None) is not None:
        logger.info(f"Forward target ID found in config.json: {forward_target['id']}")
        target_overwrite = None
        while target_overwrite not in ["y", "yes", "n", "no"]:
            try:
                target_overwrite = inputimeout(
                    prompt="Do you want to overwrite the forward target? (y/n): ",
                    timeout=60,
                ).lower()
            except TimeoutOccurred:
                logger.info("Timeout occurred during input. Exiting setup.")
                sys.exit(0)
            if target_overwrite not in ["y", "yes", "n", "no"]:
                logger.info("Invalid input. Please enter 'y' or 'n'.")
        target_overwrite = target_overwrite in ["y", "yes"]
    else:
        logger.info("No forward target ID found. Proceeding to create a new one.")
        target_overwrite = True  # To bound value

    if target_overwrite:
        # Prompt for new forward target username
        try:
            target_name = inputimeout(
                prompt="Enter new forward target @name or t.me/link: ", timeout=60
            ).strip()
        except TimeoutOccurred:
            logger.info("Timeout occurred during input. Exiting setup.")
            sys.exit(0)
        # Fetch ID
        try:
            logger.info(f"Fetching Telegram ID for forward target: {target_name}")
            with client:
                # Execute the async function synchronously using the client's loop
                target_id = client.loop.run_until_complete(
                    get_entity_id(client, target_name)
                )
                logger.info(f"Fetched forward target ID: {target_id}")
        except CommsError as e:
            logger.error(f"Failed to fetch forward target user ID: {e}")
            sys.exit(1)
        config["forward_target"] = {"id": target_id, "username": target_name}

    # Validate and save updated config.json
    logger.info("Validating and saving updated configuration to config.json.")
    save_config(config)
    logger.info("Configuration saved successfully to config.json.")
    logger.info("Setup completed successfully. You can now run the userbot.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Setup interrupted by user.")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Setup failed with unexpected error: {e}", exc_info=True)
        sys.exit(1)
