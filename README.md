# Telegram Forwarder Userbot

![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)
![Telegram](https://img.shields.io/badge/Telegram-0088CC?logo=telegram&logoColor=white)
![Telethon 1.44](https://img.shields.io/badge/telethon-1.44-purple.svg)
![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)


Asynchronous Telegram application built with Telethon to automatically filter and route messages from multiple sources to a single destination. 

With customizable content filter and configurable from chat.

> **WARNING:** Be careful not to break [Telegram's API ToS](https://core.telegram.org/api/terms) or Telegram can ban your account. It is recommended to use a dev account to protect your personal account.

---

## Workflow


```text
┌──────────────────────────────────────────┐
│ 1) setup.py (one-time)                   │
│ - Aks for API keys                       │
│ - Create/update .env file                │
│ - Ask for admin and forward target info  │
│ - Resolve admin and forward target IDs   │
│ - Create/update config.json file         │
└──────────────┬───────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────────┐
│ 2) main.py (long-running)                    │
│ - Load .env + config.json                    │
│ - Start Telethon client                      │
│ - Validate comms (admin + target reachable)  │
│ - Wait for event (NewMessage)                │
└──────────────┬───────────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────────┐
│ 3) Incoming Telegram NewMessage event        │
└──────────────┬───────────────────────────────┘
               │
               ▼
┌────────────────────────┐  No   ┌─────────────────────────┐
│ From admin ID?         │──────▶│ From monitored source?  │
└──────────────┬─────────┘       └───────────┬─────────────┘
               │ Yes                         │ Yes
               ▼                             ▼
┌────────────────────────┐       ┌──────────────────────────────────┐
│ handle_admin_command   │       │ handle_new_message               │
│ - /filter list/add/rm  │       │ - scan text for keywords         │
│ - /source list/add/rm  │       │ - if match -> forward to target  │
│ - /target set/show     │       └──────────────────────────────────┘
│ - persist to config    │
└────────────────────────┘

(main.py continues running until disconnected/stopped)
```


---

## Tech stack

**Telethon** - Asyncio Python library to collect data using Telegram's API

---

## How to Run

### 1) Clone and set up environment

```bash
git clone https://github.com/Kev-HL/telegram-forwarder-userbot.git # or SSH if you like
cd telegram-forwarder-userbot
make venv
source .venv/bin/activate
make setup
```

> If you use `make setup-dev` locally, that works too.

---

### 2) Configure credentials and initial entities (one-time)

```bash
python3 setup.py
```
And follow CLI instructions.

This will:
- create/update `.env` with `TG_API_ID` and `TG_API_HASH`
- create/update `config.json`
- resolve and store:
  - `admin_user` (ID + username)
  - `forward_target` (ID + name)

---

### 3) Start the bot

```bash
python3 main.py
```

Bot behavior:
- listens to incoming messages
- accepts admin commands from configured admin user
- checks monitored source chats
- forwards only messages that match configured keywords

---

### 4) Runtime admin commands (from Telegram chat)

To be used in any chat where bot and admin are present, including direct conversation:

- `/filter list` — View active keywords
- `/filter add <word>` — Add keyword
- `/filter rm <word>` — Remove keyword
- `/source list` — Show tracked sources
- `/source add <identifier>` — Add source
- `/source rm <identifier|ID>` — Remove source
- `/target show` — Show current forward target
- `/target set <identifier>` — Change forward target

With identifier being: @name or link (t.me/name).

Only works with UserNames, Public Channels or Super Groups.
Private channels or private/legacy groups are not supported.

Use `me` as identifier on target to forward to your *Saved Messages*.
Numerical IDs should only be used for source removal (if by name does not work).

---

### 5) Oracle Cloud Deployment [OPTIONAL]

This is just an example, you can run the script locally or with other cloud services.  

High-level flow:
1. Create [Oracle Cloud](https://www.oracle.com/cloud/free/) VM
   - Free Tier VM (Ubuntu latest LTS is easiest)
   - Create/select a VCN + public subnet and ensure the instance has a public IPv4
   - Configure SSH key pair
2. SSH into VM
3. Install `git`, `python3` (>=3.12, <3.13), `python3-pip`, `python3-venv`, `make`
4. Clone repo and `cd` into it
5. Run `make venv`, **activate** the virtual environment, then run `make setup`
6. Run `python3 setup.py` once
7. Run `python3 main.py` (or use systemd for 24/7 mode)

> Note: Tested with Python 3.12.3, hence the strict version pin.

---

### 6) Run 24/7 via systemd  [OPTIONAL]

A `tg-bot.service` file is provided and assumes common Ubuntu defaults.  
Before using it, verify/update: `User`, `Group`, `WorkingDirectory`, `ExecStart`.

Then on the VM:

```bash
sudo cp tg-bot.service /etc/systemd/system/tg-bot.service
sudo systemctl daemon-reload
sudo systemctl enable tg-bot
sudo systemctl start tg-bot
sudo systemctl status tg-bot
journalctl -u tg-bot -f
```

systemd will start `main.py` on boot and restart it if the process exits unexpectedly.

---

## References

[Telethon: Repository](https://codeberg.org/Lonami/Telethon)  
[Telegram's API ToS](https://core.telegram.org/api/terms)  

---

## Contact

For questions reach out via GitHub (Kev-HL).
