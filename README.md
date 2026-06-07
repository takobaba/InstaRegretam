# 📱 InstaMassUnliker

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
- Select your Instagram account
- Click **"Some of your information"**
- ✅ Make sure to check **"Likes"** (under Your Instagram Activity)
- ✅ Check **"Followers and Following"** (under Connections) — needed for auto-exclude
- Select **JSON** format, **All time** date range
- Submit request and wait for the email (usually 15 min, can take up to 48h)
- Download and extract the ZIP

You'll need:
- `liked_posts.json` — found in `your_instagram_activity/likes/`
- `following.json` — found in `connections/followers_and_following/`

### 2. Setup

```bash
# Clone and enter directory
git clone https://github.com/takobaba/InstaRegrettam.git
cd InstaRegrettam

# Install dependencies (requires Python 3.14+)
pip install -r requirements.txt

# Copy your export files
cp /path/to/liked_posts.json .
cp /path/to/following.json .    # optional, for auto-exclude
```

### 3. Run

```bash
python3 instaregretam.py
```

### 4. First Run

1. **Add your account** (option 1) — enter your username and password (stored locally)
2. **Import following list** (option 4 → 4) — auto-excludes everyone you follow
3. **Pick a speed mode** (option 7)
4. **Start unliking** (option 3)

The script uses [ensta](https://github.com/diezo/Ensta) to authenticate and obtain a session, then passes that session to [instagrapi](https://github.com/subzeroid/instagrapi) to perform the unlike operations. Your credentials are stored locally in the `accounts/` directory and are only used to establish a session with Instagram.

## Features

- **Works with 2FA** — supports TOTP authenticator apps
- **Auto-exclude following** — import your `following.json` to protect likes from people you follow
- **Manual exclude list** — add/remove specific users
- **Speed presets** — Safe, Moderate, Fast, Aggressive
- **Anti-ban protections:**
  - Configurable delays between actions
  - Hourly and daily rate limits
  - Random breaks to mimic human behavior
  - Exponential backoff on errors
  - Auto-stop on action block detection
- **Progress tracking** — saves after each unlike, resume anytime
- **New export format support** — handles both old (`string_list_data`) and new (`label_values`) Instagram data exports

## Speed Modes

| Mode | Delay | Hourly Rate | Daily Rate | Est. Time (18k posts) |
|------|-------|-------------|------------|-----------------------|
| 🐢 Safe | 30-120s | 50/hr | 400/day | ~50 days |
| 🚀 Moderate | 10-30s | 100/hr | 1000/day | ~19 days |
| ⚡ Fast | 3-8s | 200/hr | 2000/day | ~10 days |
| 💀 Aggressive | 2-5s | 500/hr | 5000/day | ~4 days |

Higher speeds increase risk of temporary action blocks (24-48h cooldown, not a ban).

## How It Avoids Bans

- Uses Instagram's mobile private API (same as the app)
- Randomized delays between actions
- Hourly/daily caps prevent velocity spikes
- Detects rate-limit responses and stops immediately
- Exponential cooldown on consecutive errors

**Worst case:** Temporary action block (24-48h). The script detects this and exits with a warning. Your progress is saved.

## Requirements

- Python 3.14+
- Instagram account
- Your Instagram data export (`liked_posts.json`)

## Tech Stack

- **[ensta](https://github.com/diezo/Ensta)** — handles authentication (including 2FA) and session management
- **[instagrapi](https://github.com/subzeroid/instagrapi)** — performs the actual unlike operations via Instagram's mobile API

## ⚠️ Disclaimer

This tool uses Instagram's private API which is against their Terms of Service. Use at your own risk. The worst that can happen is a temporary action block — not a permanent ban. We are not responsible for any consequences.

## License

MIT
