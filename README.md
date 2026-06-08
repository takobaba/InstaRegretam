# 📱 InstaRegretam

> Mass unlike your Instagram posts safely. Supports the latest Instagram data export format, auto-excludes people you follow, and includes anti-ban protections.

[![Python Version](https://img.shields.io/badge/python-3.14%2B-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

## How It Works

1. Export your Instagram data (JSON format)
2. Run the script — it reads your liked posts and unlikes them via Instagram's private API
3. Posts from people you follow are automatically excluded
4. Built-in rate limiting prevents bans

## Quick Start

### 1. Export Your Instagram Data

- Instagram → Settings → **Account Center** → **Your Information and Permissions** → **Download your Information**
- Select your Instagram account → **"Some of your information"**
- ✅ Check **"Likes"** (under Your Instagram Activity)
- ✅ Check **"Followers and Following"** (under Connections) — needed for auto-exclude
- Select **JSON** format, **All time** date range
- Submit and wait for the email (usually 15 min, can take up to 48h)

You'll need:
- `liked_posts.json` — found in `your_instagram_activity/likes/`
- `following.json` — found in `connections/followers_and_following/`

### 2. Setup

```bash
git clone https://github.com/takobaba/InstaRegretam.git
cd InstaRegretam
pip install -e .  # requires Python 3.14+

# Copy your export files
cp /path/to/liked_posts.json .
cp /path/to/following.json .    # optional, for auto-exclude
```

### 3. Run

```bash
python3 instaregretam.py
```

### 4. First Run

1. **Add your account** (option 1) — enter your username and password
2. **Import following list** (option 4 → 4) — auto-excludes everyone you follow
3. **Pick a speed mode** (option 7)
4. **Start unliking** (option 3)

## Features

- **Works with 2FA** — supports TOTP authenticator apps
- **Auto-exclude following** — import your `following.json` to skip people you follow
- **Manual exclude list** — add/remove specific users
- **Speed presets** — Safe, Moderate, Fast, Aggressive, YOLO
- **Anti-ban protections** — configurable delays, hourly/daily caps, random breaks, exponential backoff, auto-stop on block detection
- **Progress tracking** — atomic saves after each unlike, safe to Ctrl+C, resumes where you left off
- **Both export formats** — handles old (`string_list_data`) and new (`label_values`) Instagram data exports

## Speed Modes

| Mode | Delay | Hourly | Daily | Best For |
|------|-------|--------|-------|----------|
| � Direct | 1-3s (library only) | No cap | 18000/day | Old/established accounts |
| �️ Safe | 3-8s | 200/hr | 2000/day | Newer accounts |

**Direct** makes API calls as fast as the library allows — no added delay. Use this if your account is old and well-established. **Safe** adds delays between requests to reduce the chance of blocks on newer accounts.

## Authentication

> ⚠️ **Note:** Automatic login via ensta is currently broken. Use the [Manual Session Setup](#manual-session-setup) method below for now.

Sessions are saved to `accounts/<username>_session.json` and reused across runs. If a session expires, the script automatically does a fresh login.

### Manual Session Setup

If automatic login fails, you can provide your session cookie manually:

1. Log into Instagram in your browser
2. DevTools → **Application** → **Cookies** → `https://www.instagram.com`
3. Copy the `sessionid` cookie value
4. Run:

```bash
python3 -c "
from instagrapi import Client
cl = Client()
cl.login_by_sessionid('YOUR_SESSION_ID_HERE')
cl.dump_settings('accounts/<your_username>_session.json')
print(f'Saved session for: {cl.account_info().username}')
"
```

### Credentials Storage

- Stored locally in `accounts/` (gitignored)
- Only used to establish a session with Instagram
- Nothing is ever uploaded

## What Happens If You Get Blocked?

The script detects action blocks immediately, saves progress, and exits. Your account is **not banned** — it's a temporary restriction (24-48h). Run again after the cooldown and it resumes where it left off.

⚠️ The script exits on the first rate limit signal rather than retrying — retrying extends the block.

## ⚠️ Disclaimer

This tool uses Instagram's private API which is against their Terms of Service. Use at your own risk.

## License

MIT
