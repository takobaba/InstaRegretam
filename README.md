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
git clone https://github.com/takobaba/InstaRegretam.git
cd InstaRegretam

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

## Example Output

```
🔄 Unliking posts:   0%|▋                | 85/18403 [ETA: 45:41:47]
16:26:51 [INFO] your_username [200] POST https://i.instagram.com/api/v1/media/xxxxx/unlike/
  ✓ 86/18403 — @some_user — reel/abc123/
🔄 Unliking posts:   0%|▋                | 86/18403 [ETA: 41:37:27]
16:26:59 [INFO] your_username [200] POST https://i.instagram.com/api/v1/media/xxxxx/unlike/
  ✓ 87/18403 — @another_user — reel/def456/
🔄 Unliking posts:   0%|▊                | 87/18403 [ETA: 41:04:58]
16:27:06 [INFO] your_username [200] POST https://i.instagram.com/api/v1/media/xxxxx/unlike/
  ✓ 88/18403 — @cool_account — p/ghi789/
```

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
| 🐢 Safe | 30-120s | 60/hr | 400/day | ~50 days |
| 🚀 Moderate | 10-30s | 120/hr | 1000/day | ~19 days |
| ⚡ Fast | 3-8s | 200/hr | 2000/day | ~10 days |
| 💀 Aggressive | 2-5s | 500/hr | 5000/day | ~4 days |
| 🔥 YOLO | 1-3s (library only) | No cap | 18000/day | ~1 day |

Higher speeds increase risk of temporary action blocks (24-48h cooldown, not a ban).

## Authentication

The login flow uses a two-library approach:

1. **[ensta](https://github.com/diezo/Ensta)** handles the initial authentication, including 2FA (TOTP). It establishes a session with Instagram and returns a session ID.
2. **[instagrapi](https://github.com/subzeroid/instagrapi)** receives that session ID and performs the actual unlike operations via Instagram's mobile private API.

### Session Persistence

After the first successful login, the session is saved to `accounts/<username>_session.json`. On subsequent runs, the script reloads the saved session instead of logging in fresh. This is important because:

- Instagram treats fresh logins from automation as suspicious
- Reusing a session looks like a normal phone that stays logged in
- Avoids unnecessary 2FA prompts on every run

If the saved session expires, the script automatically falls back to a fresh login via ensta and saves the new session.

### Manual Session Setup

If the automatic login fails (Instagram sometimes blocks programmatic logins), you can provide your session cookie manually:

1. Log into Instagram in your browser (Chrome/Firefox)
2. Open DevTools (`F12` or `Cmd+Option+I`)
3. Go to **Application** or **Storage** → **Cookies** → `https://www.instagram.com`
4. Find the cookie named `sessionid` and copy its value
5. Run this from the project directory:

```bash
python3 -c "
from instagrapi import Client
cl = Client()
cl.login_by_sessionid('YOUR_SESSION_ID_HERE')
cl.dump_settings('accounts/<your_username>_session.json')
print(f'Saved session for: {cl.account_info().username}')
"
```

The script will pick up this session on the next run. You only need to do this once — the session stays valid for weeks/months as long as you don't log out.

### 2FA Support

If your account has two-factor authentication enabled (recommended), add your TOTP secret key when setting up your account in the script. This is the same key your authenticator app uses — the script generates the 2FA code automatically so you don't need to enter it manually each time.

### Credentials Storage

- Username, password, and TOTP key are stored locally in `accounts/<username>.json`
- Session data is stored in `accounts/<username>_session.json`
- The `accounts/` directory is gitignored — nothing is ever uploaded
- Credentials are only used to establish a session with Instagram

## How It Avoids Bans

Following [instagrapi best practices](https://subzeroid.github.io/instagrapi/usage-guide/best-practices.html):

- **Session persistence** — reuses saved sessions instead of logging in fresh each run
- **Built-in library delay** — `delay_range` set on the instagrapi client as a safety net
- **Randomized delays** — jittered sleep between actions to mimic human behavior
- **Hourly/daily caps** — prevent velocity spikes
- **Specific error handling** — catches `ClientThrottledError`, `PleaseWaitFewMinutes`, and `FeedbackRequired` directly
- **Immediate exit on block** — does not retry rate-limited requests (retrying extends the block)
- **Exponential backoff** — on transient errors only
- **Residential IP** — designed to run from your home network, not a datacenter

### What happens if you get blocked?

The script detects action blocks immediately, logs the event, saves your progress, and exits. Your account is **not banned** — it's a temporary restriction (24-48h). When you run again after the cooldown, it resumes exactly where it left off.

### Instagram rate limit hierarchy

1. **`PleaseWaitFewMinutes`** — soft limit, clears in 5-30 min. Script exits immediately.
2. **`FeedbackRequired`** — harder block, lasts 6-48 hours. Script exits immediately.
3. **`ClientThrottledError`** (HTTP 429) — IP-level throttle. Script exits immediately.

⚠️ Three soft limits in one hour can escalate to a `FeedbackRequired` block. That's why the script exits on the first detection rather than retrying.

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
