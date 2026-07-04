"""Handlers module for Telegram Forwarder Userbot"""

# Standard imports
import logging
import re

# Third party imports
from telethon import events, TelegramClient
from telethon.utils import get_peer_id, get_display_name
from telethon.tl.functions.channels import JoinChannelRequest, LeaveChannelRequest

# Local imports
from config import save_config

# Set up logging
logger = logging.getLogger(__name__)


async def handle_new_message(event: events.NewMessage.Event, config: dict) -> None:
    """
    Processes incoming feed messages from source chats or channels, scans for keywords,
    and routes matching posts to your target destination chat or channel.
    """
    # Skip empty messages
    if not event.message or not event.message.message:
        return

    message_text = event.message.message
    logger.debug(f"Scanning incoming message from source ID {event.chat_id}")

    # Extract filter keywords from config.json
    keywords = config.get("keywords", [])
    if not keywords:
        return  # No active filters set, skip routing

    # Compile a fast, case-insensitive regex pattern matching any keyword
    # Escaping prevents symbols in keywords from breaking regex
    pattern = re.compile("|".join(map(re.escape, keywords)), re.IGNORECASE)

    # Search logic execution
    if pattern.search(message_text.lower()):
        target_id = config.get("forward_target", {}).get("id", "me")
        target_name = config.get("forward_target", {}).get("name", "Saved Messages")
        logger.info(
            f"Match found! Forwarding message {event.id} to "
            f"'{target_name}' with ID {target_id}"
        )

        try:
            # Forward the exact original message container
            await event.message.forward_to(target_id)
        except Exception as e:
            logger.error(
                f"Failed to forward message from event id {event.id} and "
                f"chat id {event.chat_id}. Error: {e}"
            )


async def handle_admin_command(
    event: events.NewMessage.Event, client: TelegramClient, config: dict
) -> None:
    """
    Interceptors terminal control commands originating strictly from your admin account
    ID to dynamically adjust config.
    """
    # Skip empty messages
    if not event.message or not event.message.message:
        return

    # Extract the command text and remove leading/trailing whitespace
    text = event.message.message.strip()

    try:
        # Define strict interactive structural commands matching regex configurations
        # Command styles: "/filter add Adidas" or "/channel add @deals_hub"
        if text.startswith("/help"):
            help_menu = (
                "**Telegram Forwarder Userbot - How to use**\n\n"
                "- `/filter list` — View active keywords\n"
                "- `/filter add <word>` — Add keyword\n"
                "- `/filter rm <word>` — Remove keyword\n\n"
                "- `/source list` — Show tracked sources\n"
                "- `/source add <identifier>` — Add source\n"
                "- `/source rm <identifier|ID>` — Remove source\n"
                "- `/target show` — Show current forward target\n"
                "- `/target set <identifier>` — Change forward target\n"
                "- `beep` — Answers `boop`\n\n"
                "With identifier: @name or link (t.me/name).\n"
                "Numerical IDs should only be used for source removal.\n"
                "Only works with @usernames, Public Channels or Super Groups.\n"
                "Private channels and private/legacy groups are not supported.\n"
                "Use 'me' as identifier on target to forward to your Saved Messages."
            )
            await event.respond(help_menu)
            return

        # Handle Filter Management Command Chain
        if text.startswith("/filter"):
            parts = text.split(" ", 2)
            if len(parts) < 2:
                await event.respond("Usage: `/filter [list|add|rm] <keyword>`")
                return

            action = parts[1].lower()

            if action == "list":
                current_filters = (
                    ",\n".join([f"`{k}`" for k in config["keywords"]]) or "None"
                )
                await event.respond(f"Active Keywords:\n{current_filters}")
                return

            if len(parts) < 3:
                await event.respond("Please provide a keyword value.")
                return

            keyword = parts[2].strip().lower()

            if action == "add":
                if keyword not in config["keywords"]:
                    config["keywords"].append(keyword)
                    save_config(config)
                    await event.respond(f"Added filter keyword: `{keyword}`")
                else:
                    await event.respond(f"Keyword `{keyword}` is already present.")

            elif action == "rm":
                if keyword in config["keywords"]:
                    config["keywords"].remove(keyword)
                    save_config(config)
                    await event.respond(f"Removed filter keyword: `{keyword}`")
                else:
                    await event.respond(f"Keyword `{keyword}` not found in list.")
            return

        # Handle Feed Sources Management Command Chain
        if text.startswith("/source"):
            parts = text.split(" ", 2)
            if len(parts) < 2:
                await event.respond("Usage: `/source [list|add|rm] <identifier>`")
                return

            action = parts[1].lower()

            if action == "list":
                sources_list = [
                    f"`{c['name']}` (ID: `{c['id']}`)" for c in config["feed_sources"]
                ]
                formatted_list = ",\n".join(sources_list) or "None"
                await event.respond(f"Monitored Sources:\n{formatted_list}")
                return

            if len(parts) < 3:
                await event.respond("Please provide a source link, username or ID.")
                return

            target = parts[2].strip()

            # Check in case user has provided a numeric ID
            # And if rm, bypass the network to remove directly from config.json
            if bool(re.match(r"^-?[0-9]+$", target)):
                target = int(target)
                if action == "rm":
                    try:
                        target_entity = await client.get_entity(target)
                        await client(LeaveChannelRequest(target_entity))
                    except Exception as e:
                        logger.debug(f"Failed to fetch source {target}: {e}")
                    current_source_ids = [c["id"] for c in config["feed_sources"]]
                    if target in current_source_ids:
                        config["feed_sources"] = [
                            c for c in config["feed_sources"] if c["id"] != target
                        ]
                        save_config(config)
                        await event.respond(
                            f"Stopped monitoring source with ID: `{target}`"
                        )
                    else:
                        await event.respond(
                            f"Source with ID `{target}` not found in tracking config."
                        )
                    return

            target_entity = await client.get_entity(target)
            target_id = get_peer_id(target_entity)
            target_name = get_display_name(target_entity)

            current_source_ids = [c["id"] for c in config["feed_sources"]]

            if action == "add":
                if target_id not in current_source_ids:
                    try:
                        await client(JoinChannelRequest(target_entity))
                    except Exception as e:
                        logger.debug(f"Failed to join source {target_name}: {e}")
                    config["feed_sources"].append(
                        {"id": target_id, "name": target_name}
                    )
                    save_config(config)
                    await event.respond(f"Monitoring added for source: `{target_name}`")
                else:
                    await event.respond(
                        f"Source `{target_name}` is already actively monitored."
                    )

            elif action == "rm":
                if target_id in current_source_ids:
                    try:
                        await client(LeaveChannelRequest(target_entity))
                    except Exception as e:
                        logger.debug(f"Failed to leave source {target_name}: {e}")
                    config["feed_sources"] = [
                        c for c in config["feed_sources"] if c["id"] != target_id
                    ]
                    save_config(config)
                    await event.respond(f"Stopped monitoring source: `{target_name}`")
                else:
                    await event.respond(
                        f"Source `{target_name}` not found in tracking configuration."
                    )
            return

        # Handle Forward Target Management Command Chain
        if text.startswith("/target"):
            parts = text.split(" ", 2)
            if len(parts) < 2:
                await event.respond("Usage: `/target [show|set] <identifier>`")
                return

            action = parts[1].lower()

            if action == "show":
                target_name = config.get("forward_target", {}).get("name", "")
                target_id = config.get("forward_target", {}).get("id", None)
                await event.respond(f"Forward Target:\n`{target_name}` (`{target_id}`)")
                return

            if len(parts) < 3:
                await event.respond("Please provide a @name or t.me link.")
                return

            target = parts[2].strip()

            target_entity = await client.get_entity(target)
            target_id = get_peer_id(target_entity)
            target_name = get_display_name(target_entity)

            if action == "set":
                config["forward_target"] = {"id": target_id, "name": target_name}
                save_config(config)
                await event.respond(f"Forward target set to: `{target_name}`")
            return
        if text == "Beep":
            await event.respond("Boop")
            return
        
        if text:
            await event.respond(
                "Unrecognized command. Use `/help` to see available commands."
            )

    except Exception as e:
        logger.error(f"Error processing admin command: {e}")
        try:
            await event.respond(f"Error processing command: {e}")
        except Exception as inner_e:
            logger.error(f"Completely unable to connect through: {inner_e}")
