"""Communication module for Telegram Forwarder Userbot"""

# Standard imports
import logging

# Third-party imports
from telethon import TelegramClient

# Set up logging
logger = logging.getLogger(__name__)


class CommsError(Exception):
    """Custom exception for communication errors."""

    pass


async def check_comms(client: TelegramClient, config: dict) -> None:
    try:
        admin_id = config.get("admin_user", {}).get("id")
        admin_entity = await client.get_entity(admin_id)
        # Update config with updated name for easier logging
        config["admin_user"]["name"] = getattr(
            admin_entity, "username", getattr(admin_entity, "first_name", "Unknown")
        )
        target_id = config.get("forward_target", {}).get("id")
        target_entity = await client.get_entity(target_id)
        # Update config with updated name for easier logging
        config["forward_target"]["name"] = getattr(
            target_entity, "title", getattr(target_entity, "first_name", "Unknown")
        )
    except Exception as e:
        logger.error(f"Admin or target is unreachable. Error: {e}")
        raise CommsError(f"Admin or target is unreachable. Error: {e}")


async def get_entity_id(client: TelegramClient, username: str) -> int:
    """Helper async function to fetch the internal Telegram ID."""
    try:
        entity = await client.get_entity(username)
        return entity.id
    except Exception as e:
        logger.error(f"Error fetching user ID: {e}")
        raise CommsError(f"Error fetching user ID: {e}")
