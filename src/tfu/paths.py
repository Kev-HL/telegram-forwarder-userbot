"""Shared runtime paths module for Telegram Forwarder Userbot"""

# Standard imports
from pathlib import Path

# Root path of the repository
ROOT_PATH = Path(__file__).resolve().parent.parent.parent

# Env file path
ENV_PATH = ROOT_PATH / ".env"

# Runtime data directory (logs, session, config)
DATA_DIR = ROOT_PATH / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

# Telethon session base path -> creates "userbot.session"
SESSION_BASENAME = DATA_DIR / "userbot"

# Runtime config.json path
CONFIG_PATH = DATA_DIR / "config.json"
