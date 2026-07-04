"""Storage module for Telegram Forwarder Userbot"""

# Standard imports
import json
import logging

# Local imports
from tfu.paths import CONFIG_PATH

# Set up logging
logger = logging.getLogger(__name__)


class ConfigError(Exception):
    """Custom exception for configuration errors."""

    pass


def load_config() -> dict:
    """Loads the application configuration state from config.json.

    Args:
        None

    Returns:
        dict: The configuration state loaded from config.json.

    Raises:
        FileNotFoundError: If config.json is missing.
        json.JSONDecodeError: If config.json contains invalid JSON.
    """
    if not CONFIG_PATH.exists():
        logger.error("Critical Error: config.json is missing.")
        raise FileNotFoundError("Critical Error: config.json is missing.")

    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as file:
            config = json.load(file)
        _validate_config(config)  # Validate the config structure
        return config
    except json.JSONDecodeError as e:
        logger.error(f"Invalid config.json syntax: {e}")
        raise
    except ConfigError as e:
        logger.error(f"Configuration validation error: {e}")
        raise


def _validate_config(config: dict) -> None:
    """
    Validates the structure and content of the configuration dictionary.

    Args:
        config (dict): The configuration state to validate.

    Returns:
        None

    Raises:
        ConfigError: If the configuration is invalid or missing required fields.
    """
    required_keys = ["feed_sources", "forward_target", "admin_user", "keywords"]
    for key in required_keys:
        if key not in config:
            logger.error(f"Invalid config: Missing '{key}' in config.json.")
            raise ConfigError(f"Missing '{key}' in config.json.")

    if not isinstance(config["feed_sources"], list):
        logger.error("Invalid config: 'feed_sources' must be a list (can be empty).")
        raise ConfigError("'feed_sources' must be a list (can be empty).")

    if not isinstance(config["forward_target"], dict):
        logger.error("Invalid config: 'forward_target' must be a dictionary.")
        raise ConfigError("'forward_target' must be a dictionary.")

    if not config["forward_target"].get("id"):
        logger.error("Invalid config: 'forward_target' ID must exist")
        raise ConfigError("'forward_target' ID must exist.")

    if not isinstance(config["admin_user"], dict):
        logger.error("Invalid config: 'admin_user' must be a dictionary.")
        raise ConfigError("'admin_user' must be a dictionary.")

    if not config["admin_user"].get("id"):
        logger.error("Invalid config: 'admin_user' ID must exist")
        raise ConfigError("'admin_user' ID must exist.")

    if not isinstance(config["keywords"], list):
        logger.error("Invalid config: 'keywords' must be a list (can be empty).")
        raise ConfigError("'keywords' must be a list (can be empty).")


def save_config(config: dict) -> None:
    """
    Safely saves the active runtime configuration back to config.json.

    Args:
        config (dict): The configuration state to be saved.

    Returns:
        None

    Raises:
        Exception: If there is an error while writing to config.json.
    """
    try:
        _validate_config(config)  # Validate the config structure before saving
        with open(CONFIG_PATH, "w", encoding="utf-8") as file:
            json.dump(config, file, indent=2, ensure_ascii=False)
        logger.info("config.json successfully saved to disk.")
    except Exception as e:
        logger.error(f"Failed to save config.json to disk: {e}")
        raise
