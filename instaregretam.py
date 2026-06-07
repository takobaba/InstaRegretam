#!/usr/bin/env python3
"""Instagram Mass Unliker — Erase your digital footprint."""

import os
import sys
import json
import time
import random
import logging
import platform
import subprocess
import signal
import atexit
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List, Set
from getpass import getpass
from logging.handlers import RotatingFileHandler

from dotenv import load_dotenv
from tqdm import tqdm
from colorama import init as colorama_init, Fore, Style

load_dotenv()
colorama_init()

# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Default configuration
CONFIG = {
    "delay": {"min": 30, "max": 120},
    "break": {"min": 600, "max": 1800, "probability": 0.05},
    "accounts": {},
    "excluded_users": [],
    "hourly_limit": 60,
    "daily_limit": 400,
    "log_level": "INFO",
    "max_retries": 3,
    "retry_delay": 60,
    "auto_update": True,
    "python_min_version": "3.14.0"
}


class InstagramUnliker:
    def __init__(self):
        """Initialize the Instagram Unliker application."""
        logging.info("Starting Instagram Unliker application...")

        self.config_file = "config.json"
        self.accounts_dir = Path("accounts")
        self.logs_dir = Path("logs")
        self.running = True
        self.excluded_users: Set[str] = set()

        self._create_required_directories()
        self._setup_signal_handlers()
        self.setup_logging()
        self.check_and_create_config()
        self._load_excluded_users()

    def _load_excluded_users(self):
        """Load excluded users from config."""
        self.excluded_users = set(CONFIG.get('excluded_users', []))
        logging.info(f"Loaded {len(self.excluded_users)} excluded users")

    def _setup_signal_handlers(self):
        """Set up handlers for graceful shutdown."""
        signal.signal(signal.SIGINT, self._handle_shutdown)
        signal.signal(signal.SIGTERM, self._handle_shutdown)

    def _handle_shutdown(self, signum, frame):
        """Handle shutdown signals gracefully."""
        print(f"\n{Fore.YELLOW}[!] Received shutdown signal. Cleaning up...{Style.RESET_ALL}")
        self.running = False
        time.sleep(1)
        sys.exit(0)

    def setup_logging(self):
        """Configure logging with rotation and cleanup."""
        self.logs_dir.mkdir(exist_ok=True)

        log_file = self.logs_dir / "unliker.log"
        file_handler = RotatingFileHandler(
            log_file, maxBytes=5*1024*1024, backupCount=5, encoding='utf-8'
        )
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s [%(levelname)s] [%(filename)s:%(lineno)d] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        ))

        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(logging.Formatter(
            '%(asctime)s [%(levelname)s] %(message)s', datefmt='%H:%M:%S'
        ))

        root_logger = logging.getLogger()
        root_logger.setLevel(logging.INFO)
        logging.getLogger('instagrapi').setLevel(logging.WARNING)
        root_logger.handlers.clear()
        root_logger.addHandler(file_handler)
        root_logger.addHandler(console_handler)

        atexit.register(self._cleanup_logs)
        logging.info("Logging system initialized")

    def _cleanup_logs(self):
        """Cleanup function that runs on program exit."""
        try:
            logging.info("Performing final cleanup...")
            self.save_config()
            for handler in logging.getLogger().handlers:
                handler.close()
        except Exception as e:
            print(f"Error during cleanup: {e}")

    def _create_required_directories(self):
        """Create necessary directories if they don't exist."""
        try:
            self.accounts_dir.mkdir(exist_ok=True)
            self.logs_dir.mkdir(exist_ok=True)
            logging.info("Required directories created successfully")
        except Exception as e:
            logging.error(f"Failed to create directories: {e}")
            print("Please ensure you have write permissions in the current directory")

    def check_python_version(self) -> bool:
        """Verify Python version meets requirements."""
        version = sys.version_info
        if version.major < 3 or (version.major == 3 and version.minor < 14):
            print(f"{Fore.RED}[✗] Error: Python 3.14 or higher required (current: {version.major}.{version.minor}){Style.RESET_ALL}")
            return False
        print(f"{Fore.GREEN}[✓] Python version check passed ({version.major}.{version.minor}){Style.RESET_ALL}")
        return True

    def check_and_create_config(self):
        """Create or load configuration file."""
        if not os.path.exists(self.config_file):
            with open(self.config_file, 'w') as f:
                json.dump(CONFIG, f, indent=4)
            print(f"{Fore.GREEN}[✓] Created default configuration file{Style.RESET_ALL}")
        else:
            try:
                with open(self.config_file, 'r') as f:
                    loaded_config = json.load(f)
                    for key, value in loaded_config.items():
                        if key in CONFIG:
                            CONFIG[key] = value
                print(f"{Fore.GREEN}[✓] Loaded existing configuration{Style.RESET_ALL}")
            except json.JSONDecodeError:
                print(f"{Fore.RED}[✗] Error: Corrupted configuration file{Style.RESET_ALL}")
                backup_file = f"{self.config_file}.bak"
                os.rename(self.config_file, backup_file)
                print(f"{Fore.YELLOW}[!] Backed up corrupted config to {backup_file}{Style.RESET_ALL}")
                self.check_and_create_config()

    def add_account(self):
        """Add an Instagram account."""
        print(f"\n{Fore.CYAN}➕ Add Instagram Account{Style.RESET_ALL}")
        print("-" * 40)

        username = input(f"{Style.BRIGHT}Username: {Style.RESET_ALL}").strip()
        password = input(f"{Style.BRIGHT}Password: {Style.RESET_ALL}").strip()

        if not username or not password:
            print(f"{Fore.RED}Username and password are required{Style.RESET_ALL}")
            return

        self.accounts_dir.mkdir(exist_ok=True)
        account_file = self.accounts_dir / f"{username}.json"

        if account_file.exists():
            override = input(f"{Fore.YELLOW}Account exists. Replace? (y/N): {Style.RESET_ALL}").lower()
            if override != 'y':
                return

        account_data = {
            "username": username,
            "password": password,
            "last_run": None,
            "total_unliked": 0,
            "last_error": None,
            "created_at": datetime.now().isoformat()
        }

        try:
            with open(account_file, 'w') as f:
                json.dump(account_data, f, indent=4)

            CONFIG['accounts'][username] = {"enabled": True, "delay_multiplier": 1.0}
            self.save_config()
            print(f"{Fore.GREEN}✨ Account @{username} added successfully!{Style.RESET_ALL}")
        except Exception as e:
            print(f"{Fore.RED}Could not save account: {e}{Style.RESET_ALL}")

    def remove_account(self):
        """Remove an Instagram account."""
        accounts = self.list_accounts()
        if not accounts:
            print(f"{Fore.YELLOW}[!] No accounts configured{Style.RESET_ALL}")
            return

        print(f"\n{Fore.BLUE}[×] Remove Account{Style.RESET_ALL}")
        print("-" * 30)
        for i, acc in enumerate(accounts, 1):
            print(f"{i}. {acc}")

        try:
            choice = input(f"\n{Style.BRIGHT}Select account to remove (0 to cancel): {Style.RESET_ALL}")
            if not choice.isdigit() or int(choice) == 0:
                return

            idx = int(choice)
            if idx < 1 or idx > len(accounts):
                print(f"{Fore.RED}[✗] Invalid selection{Style.RESET_ALL}")
                return

            username = accounts[idx - 1]
            confirm = input(f"{Fore.YELLOW}[!] Are you sure you want to remove {username}? (y/N): {Style.RESET_ALL}").lower()
            if confirm != 'y':
                return

            account_file = self.accounts_dir / f"{username}.json"
            if account_file.exists():
                account_file.unlink()
            if username in CONFIG['accounts']:
                del CONFIG['accounts'][username]
                self.save_config()

            print(f"{Fore.GREEN}[✓] Account {username} removed successfully{Style.RESET_ALL}")
        except Exception as e:
            print(f"{Fore.RED}[✗] Error: {e}{Style.RESET_ALL}")

    def manage_excluded_users(self):
        """Manage excluded users list."""
        while True:
            print(f"\n{Fore.CYAN}🚫 Manage Excluded Users{Style.RESET_ALL}")
            print("=" * 50)

            if self.excluded_users:
                print(f"\n{Fore.YELLOW}Currently Excluded ({len(self.excluded_users)} users):{Style.RESET_ALL}")
                for i, user in enumerate(sorted(self.excluded_users), 1):
                    if i <= 20:
                        print(f"  {i}. @{user}")
                if len(self.excluded_users) > 20:
                    print(f"  ... and {len(self.excluded_users) - 20} more")
            else:
                print(f"\n{Fore.YELLOW}No users excluded yet{Style.RESET_ALL}")

            print(f"\n{Fore.CYAN}Options:{Style.RESET_ALL}")
            print("  1. Add user to exclude list")
            print("  2. Remove user from exclude list")
            print("  3. Clear all excluded users")
            print("  4. 🔄 Auto-import from your Following list")
            print("  0. Back to main menu")

            choice = input(f"\n{Style.BRIGHT}Select option: {Style.RESET_ALL}").strip()

            if choice == "1":
                username = input(f"{Style.BRIGHT}Enter username to exclude: {Style.RESET_ALL}").strip().lower()
                if username:
                    self.excluded_users.add(username)
                    CONFIG['excluded_users'] = list(self.excluded_users)
                    self.save_config()
                    print(f"{Fore.GREEN}✓ Added @{username} to exclude list{Style.RESET_ALL}")
            elif choice == "2":
                if not self.excluded_users:
                    print(f"{Fore.YELLOW}No users to remove{Style.RESET_ALL}")
                    continue
                username = input(f"{Style.BRIGHT}Enter username to remove: {Style.RESET_ALL}").strip().lower()
                if username in self.excluded_users:
                    self.excluded_users.remove(username)
                    CONFIG['excluded_users'] = list(self.excluded_users)
                    self.save_config()
                    print(f"{Fore.GREEN}✓ Removed @{username} from exclude list{Style.RESET_ALL}")
                else:
                    print(f"{Fore.YELLOW}User not found in exclude list{Style.RESET_ALL}")
            elif choice == "3":
                if self.excluded_users:
                    confirm = input(f"{Fore.YELLOW}Clear all excluded users? (y/N): {Style.RESET_ALL}").lower()
                    if confirm == 'y':
                        self.excluded_users.clear()
                        CONFIG['excluded_users'] = []
                        self.save_config()
                        print(f"{Fore.GREEN}✓ Cleared all excluded users{Style.RESET_ALL}")
            elif choice == "4":
                self._import_following_list()
            elif choice == "0":
                break
            else:
                print(f"{Fore.RED}Invalid option{Style.RESET_ALL}")
                time.sleep(1)

    def _import_following_list(self):
        """Import following list from Instagram data export file."""
        possible_paths = [
            'following.json',
            'followers_and_following/following.json',
            'connections/followers_and_following/following.json',
        ]

        following_file = None
        for path in possible_paths:
            if os.path.exists(path):
                following_file = path
                break

        if not following_file:
            print(f"{Fore.YELLOW}Could not find following.json automatically.{Style.RESET_ALL}")
            print("Expected locations:")
            for p in possible_paths:
                print(f"  • {p}")
            custom = input(f"\n{Style.BRIGHT}Enter path to following.json (or 0 to cancel): {Style.RESET_ALL}").strip()
            if custom == '0' or not custom:
                return
            if not os.path.exists(custom):
                print(f"{Fore.RED}[✗] File not found: {custom}{Style.RESET_ALL}")
                return
            following_file = custom

        try:
            with open(following_file, 'r') as f:
                data = json.load(f)

            following_usernames = set()
            if isinstance(data, list):
                entries = data
            elif isinstance(data, dict):
                entries = data.get('relationships_following', data.get('following', []))
            else:
                entries = []

            for entry in entries:
                username = entry.get('title', '').lower()
                if not username:
                    try:
                        username = entry['string_list_data'][0]['value'].lower()
                    except KeyError, IndexError, TypeError:
                        continue
                if username:
                    following_usernames.add(username)

            if not following_usernames:
                print(f"{Fore.YELLOW}No usernames found in {following_file}{Style.RESET_ALL}")
                return

            new_count = len(following_usernames - self.excluded_users)
            self.excluded_users.update(following_usernames)
            CONFIG['excluded_users'] = list(self.excluded_users)
            self.save_config()

            print(f"\n{Fore.GREEN}✓ Imported {len(following_usernames)} users from {following_file}{Style.RESET_ALL}")
            print(f"{Fore.GREEN}  ({new_count} new, {len(self.excluded_users)} total excluded){Style.RESET_ALL}")

        except json.JSONDecodeError:
            print(f"{Fore.RED}[✗] Invalid JSON in {following_file}{Style.RESET_ALL}")
        except Exception as e:
            print(f"{Fore.RED}[✗] Error: {e}{Style.RESET_ALL}")

    def list_accounts(self) -> List[str]:
        """List all configured accounts."""
        accounts = []
        env_user = os.getenv('INSTAGRAM_USERNAME')
        if env_user:
            accounts.append(env_user)
        if self.accounts_dir.exists():
            for f in self.accounts_dir.glob("*.json"):
                if f.stem not in accounts:
                    accounts.append(f.stem)
        return accounts

    def save_config(self):
        """Save current configuration."""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(CONFIG, f, indent=4)
        except Exception as e:
            print(f"{Fore.RED}[✗] Failed to save configuration: {e}{Style.RESET_ALL}")

    def unlike_posts(self, username: str):
        """Unlike posts using JSON file with exclude list support."""
        progress_bar = None

        # Load credentials: .env first, then accounts/ JSON fallback
        env_user = os.getenv('INSTAGRAM_USERNAME')
        env_pass = os.getenv('INSTAGRAM_PASSWORD')
        env_totp = os.getenv('INSTAGRAM_TOTP_KEY')

        if env_user and env_pass and env_user == username:
            account_data = {
                'username': env_user,
                'password': env_pass,
                'totp_token': env_totp,
                'total_unliked': 0,
            }
            account_file = None
        else:
            account_file = self.accounts_dir / f"{username}.json"
            if not account_file.exists():
                print(f"\n{Fore.RED}[✗] No credentials found for {username}. Set up .env or add account.{Style.RESET_ALL}")
                return
            with open(account_file, 'r') as f:
                account_data = json.load(f)

        try:
            print(f"\n{Fore.CYAN}Starting to unlike posts for @{username}...{Style.RESET_ALL}")
            if self.excluded_users:
                print(f"{Fore.YELLOW}ℹ️  Excluding {len(self.excluded_users)} users from unliking{Style.RESET_ALL}")

            try:
                from ensta import Web
                from instagrapi import Client as InstaClient

                # Login with ensta (handles 2FA well)
                totp_key = account_data.get('totp_token', None)
                web = Web(account_data['username'], account_data['password'], totp_token=totp_key)
                session_id = {c.name: c.value for c in web.request_session.cookies}.get('sessionid', '')

                # Use session with instagrapi (has working unlike)
                cl = InstaClient()
                cl.login_by_sessionid(session_id)
                print(f"{Fore.GREEN}✓ Successfully logged in{Style.RESET_ALL}")
                account_info = cl.account_info()
                print(f"{Fore.GREEN}Logged in as: {Fore.CYAN}{account_info.username}{Style.RESET_ALL}")
            except Exception as e:
                logging.error(f"Login failed: {e}")
                print(f"{Fore.RED}[✗] Login failed: {e}")
                print(f"→ Please check your username and password.{Style.RESET_ALL}")
                return

            if not os.path.exists('liked_posts.json'):
                logging.error("liked_posts.json file not found")
                print(f"{Fore.RED}[✗] liked_posts.json file not found. Please ensure it exists.{Style.RESET_ALL}")
                return

            try:
                with open('liked_posts.json', 'r') as f:
                    liked_data = json.load(f)

                # Handle both JSON formats:
                # Old format: {"likes_media_likes": [...]}
                # New format: [...] (plain list)
                if isinstance(liked_data, list):
                    posts_list = liked_data
                    is_list_format = True
                elif isinstance(liked_data, dict) and liked_data.get('likes_media_likes'):
                    posts_list = liked_data['likes_media_likes']
                    is_list_format = False
                else:
                    print(f"{Fore.YELLOW}[!] No liked posts found in JSON file!{Style.RESET_ALL}")
                    return

                # Filter out excluded users
                original_count = len(posts_list)
                filtered_posts = [
                    post for post in posts_list
                    if _get_post_owner(post) not in self.excluded_users
                ]
                excluded_count = original_count - len(filtered_posts)

                if excluded_count > 0:
                    print(f"{Fore.YELLOW}🚫 Skipped {excluded_count} posts from excluded users{Style.RESET_ALL}")

                posts_list = filtered_posts
                total_posts = len(filtered_posts)

                if total_posts == 0:
                    print(f"{Fore.YELLOW}No posts to unlike after filtering{Style.RESET_ALL}")
                    return

                unliked_count = 0
                skipped_count = 0
                hourly_limit = CONFIG.get('hourly_limit', 60)
                daily_limit = CONFIG.get('daily_limit', 400)
                hourly_count = 0
                hourly_start = time.time()

                print(f"{Fore.BLUE}Found {total_posts} posts to unlike{Style.RESET_ALL}")
                print(f"{Fore.YELLOW}⚡ Limits: {hourly_limit}/hour, {daily_limit}/day{Style.RESET_ALL}")

                progress_bar = tqdm(
                    total=total_posts,
                    desc="🔄 Unliking posts",
                    bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt} [ETA: {remaining}]'
                )

                consecutive_errors = 0
                request_log = self.logs_dir / "requests.log"

                while posts_list and self.running:
                    # Check daily limit
                    if unliked_count >= daily_limit:
                        progress_bar.write(f"{Fore.YELLOW}⚠️  Daily limit ({daily_limit}) reached. Stopping to protect your account.{Style.RESET_ALL}")
                        break

                    # Check hourly limit
                    if hourly_count >= hourly_limit:
                        elapsed = time.time() - hourly_start
                        if elapsed < 3600:
                            wait_time = 3600 - elapsed + random.uniform(60, 300)
                            progress_bar.write(f"{Fore.YELLOW}⚠️  Hourly limit reached. Pausing {wait_time/60:.0f} min...{Style.RESET_ALL}")
                            time.sleep(wait_time)
                        hourly_count = 0
                        hourly_start = time.time()

                    try:
                        post = posts_list.pop(0)
                        post_username = _get_post_owner(post)

                        # Double-check exclusion
                        if post_username and post_username in self.excluded_users:
                            skipped_count += 1
                            progress_bar.update(1)
                            continue

                        # Extract URL (supports both old and new format)
                        href = _get_post_href(post)
                        if not href:
                            logging.warning(f"Skipping post with missing link data: {post.get('title', 'unknown')}")
                            skipped_count += 1
                            progress_bar.update(1)
                            continue

                        # Delay before unlike
                        base_delay = random.uniform(CONFIG['delay']['min'], CONFIG['delay']['max'])
                        actual_delay = base_delay * CONFIG['accounts'].get(username, {}).get('delay_multiplier', 1.0)
                        time.sleep(actual_delay)

                        media_id = cl.media_pk_from_url(href)

                        # Unlike with retry + exponential backoff
                        for retry in range(CONFIG['max_retries']):
                            try:
                                result = cl.media_unlike(media_id)
                                if not result:
                                    raise Exception(f"Unlike returned False for {href}")
                                consecutive_errors = 0
                                break
                            except Exception as e:
                                logging.warning(f"Failed to unlike (attempt {retry + 1}/{CONFIG['max_retries']}): {e}")
                                if retry < CONFIG['max_retries'] - 1:
                                    backoff = CONFIG['retry_delay'] * (2 ** retry)
                                    time.sleep(backoff)
                                else:
                                    raise

                        unliked_count += 1
                        hourly_count += 1
                        account_data['total_unliked'] += 1
                        progress_bar.update(1)

                        # Log the unliked post
                        display_owner = post_username or '?'
                        short_url = href.replace('https://www.instagram.com/', '')
                        progress_bar.write(f"  {Fore.GREEN}✓{Style.RESET_ALL} {unliked_count}/{total_posts} — @{display_owner} — {short_url}")

                        speed_label = {2: "AGGRESSIVE", 3: "FAST", 10: "MODERATE", 30: "SAFE"}.get(CONFIG['delay']['min'], "CUSTOM")
                        with open(request_log, 'a') as log:
                            log.write(f"{datetime.now().isoformat()} | UNLIKE | {media_id} | @{display_owner} | {short_url} | OK | {speed_label}\n")

                        # Save progress
                        if is_list_format:
                            save_data = posts_list
                        else:
                            liked_data['likes_media_likes'] = posts_list
                            save_data = liked_data
                        with open('liked_posts.json', 'w') as f:
                            json.dump(save_data, f, indent=4)

                        # Random break
                        if random.random() < CONFIG['break']['probability']:
                            break_time = random.uniform(CONFIG['break']['min'], CONFIG['break']['max'])
                            progress_bar.write(f"{Fore.BLUE}[*] Taking a break for {break_time/60:.1f} minutes...{Style.RESET_ALL}")
                            time.sleep(break_time)

                    except Exception as e:
                        logging.error(f"Failed to unlike post: {e}", exc_info=True)
                        progress_bar.write(f"{Fore.RED}[✗] Failed to unlike post: {e}{Style.RESET_ALL}")
                        account_data['last_error'] = str(e)

                        with open(request_log, 'a') as log:
                            log.write(f"{datetime.now().isoformat()} | ERROR | {href} | {str(e)[:100]}\n")

                        # Detect action block
                        block_keywords = ['action blocked', 'action_blocked', 'temporarily blocked',
                                          'try again later', 'limit', 'challenge_required', 'checkpoint']
                        if any(kw in str(e).lower() for kw in block_keywords):
                            progress_bar.close()
                            print(f"\n{Fore.RED}{'='*60}")
                            print("🚨 ACTION BLOCKED — Instagram has rate-limited your account!")
                            print(f"{'='*60}{Style.RESET_ALL}")
                            print(f"{Fore.YELLOW}• Your account is NOT banned, just temporarily restricted")
                            print("• Wait 24-48 hours before running again")
                            print("• Progress has been saved — it will resume where you left off")
                            print(f"• Unliked so far this session: {unliked_count}{Style.RESET_ALL}")
                            if account_file:
                                account_data['last_run'] = datetime.now().isoformat()
                                with open(account_file, 'w') as f:
                                    json.dump(account_data, f, indent=4)
                            sys.exit(1)

                        consecutive_errors += 1
                        cooldown = min(300 * (2 ** (consecutive_errors - 1)), 3600)
                        progress_bar.write(f"{Fore.YELLOW}→ Cooldown {cooldown/60:.0f} min (errors: {consecutive_errors}){Style.RESET_ALL}")
                        time.sleep(cooldown)

                        if consecutive_errors >= 5:
                            progress_bar.write(f"{Fore.RED}⚠️  Too many errors. Likely rate-limited. Stopping.{Style.RESET_ALL}")
                            break

            finally:
                if progress_bar is not None:
                    progress_bar.close()

            # Update account stats
            if account_file:
                account_data['last_run'] = datetime.now().isoformat()
                with open(account_file, 'w') as f:
                    json.dump(account_data, f, indent=4)

            print(f"\n{Fore.GREEN}[✓] Unliking complete for {username}{Style.RESET_ALL}")
            print(f"{Fore.BLUE}[*] Total unliked: {unliked_count}{Style.RESET_ALL}")
            if skipped_count > 0:
                print(f"{Fore.YELLOW}[*] Skipped (excluded/invalid): {skipped_count}{Style.RESET_ALL}")

        except json.JSONDecodeError as e:
            logging.error(f"Invalid JSON format: {e}")
            print(f"{Fore.RED}[✗] Invalid JSON format: {e}{Style.RESET_ALL}")
        except Exception as e:
            logging.error(f"Unexpected error: {e}", exc_info=True)
            print(f"\n{Fore.RED}[✗] Unexpected error: {e}{Style.RESET_ALL}")

    def show_menu(self):
        """Display interactive menu."""
        while True:
            print(f"\n{Fore.CYAN}{Style.BRIGHT}╔{'═' * 46}╗")
            print(_center_text_in_box(f"{Style.BRIGHT}Instagram Mass Unliker{Style.RESET_ALL}{Fore.CYAN}{Style.BRIGHT}"))
            print(_center_text_in_box(f"{Style.BRIGHT}Erase your digital footprint{Style.RESET_ALL}{Fore.CYAN}{Style.BRIGHT}"))
            print(f"╚{'═' * 46}╝{Style.RESET_ALL}")

            accounts = self.list_accounts()
            if accounts:
                print(f"\n{Fore.BLUE}Connected Accounts: {Fore.GREEN}{len(accounts)}{Style.RESET_ALL}")
                for acc in accounts[:3]:
                    print(f"  • @{acc}")
                if len(accounts) > 3:
                    print(f"  • ...and {len(accounts) - 3} more")
            else:
                print(f"\n{Fore.YELLOW}No accounts connected yet{Style.RESET_ALL}")

            if self.excluded_users:
                print(f"{Fore.YELLOW}🚫 Excluding {len(self.excluded_users)} users{Style.RESET_ALL}")

            # Show current speed mode
            delay_min = CONFIG['delay']['min']
            delay_max = CONFIG['delay']['max']
            if delay_min <= 2:
                mode_label = f"{Fore.RED}💀 AGGRESSIVE{Style.RESET_ALL}"
            elif delay_min <= 5:
                mode_label = f"{Fore.RED}⚡ FAST{Style.RESET_ALL}"
            elif delay_min <= 15:
                mode_label = f"{Fore.YELLOW}🚀 MODERATE{Style.RESET_ALL}"
            else:
                mode_label = f"{Fore.GREEN}🐢 SAFE{Style.RESET_ALL}"
            print(f"\n{Fore.CYAN}Speed:{Style.RESET_ALL} {mode_label} ({delay_min}-{delay_max}s delay, {CONFIG.get('hourly_limit', 60)}/hr, {CONFIG.get('daily_limit', 400)}/day)")

            print(f"\n{Fore.CYAN}Available Actions:{Style.RESET_ALL}")
            print(f"╭{'─' * 40}╮")
            print(_menu_line("1", "Add Instagram Account"))
            print(_menu_line("2", "Remove Account"))
            print(_menu_line("3", "Start Unliking"))
            print(_menu_line("4", "Manage Excluded Users"))
            print(_menu_line("5", "View Stats"))
            print(_menu_line("6", "Settings"))
            print(_menu_line("7", "Speed Mode"))
            print(_menu_line("0", "Exit"))
            print(f"╰{'─' * 40}╯")

            try:
                print(f"\n╭─ Enter your choice")
                choice = input("╰─▸ ").strip()

                if choice == "1":
                    self.add_account()
                elif choice == "2":
                    self.remove_account()
                elif choice == "3":
                    self._start_unliking_menu()
                elif choice == "4":
                    self.manage_excluded_users()
                elif choice == "5":
                    self.show_statistics()
                elif choice == "6":
                    self.show_settings()
                elif choice == "7":
                    self.change_speed_mode()
                elif choice == "0":
                    print(f"\n{Fore.GREEN}✨ Thanks for using Instagram Unliker!")
                    print(f"👋 Have a great day!{Style.RESET_ALL}")
                    break
                else:
                    print(f"\n{Fore.RED}✗ Invalid choice. Please try again.{Style.RESET_ALL}")
                    time.sleep(1)

            except KeyboardInterrupt:
                print(f"\n\n{Fore.GREEN}✨ Thanks for using Instagram Unliker!")
                print(f"👋 Have a great day!{Style.RESET_ALL}")
                break
            except Exception as e:
                print(f"\n{Fore.RED}✗ Error: {e}{Style.RESET_ALL}")
                time.sleep(2)

    def _start_unliking_menu(self):
        """Display account selection menu for unliking."""
        accounts = self.list_accounts()
        if not accounts:
            print(f"{Fore.RED}[✗] No accounts configured. Please add an account first.{Style.RESET_ALL}")
            return

        print(f"\n{Fore.BLUE}[#] Select Account{Style.RESET_ALL}")
        print("-" * 30)

        for i, acc in enumerate(accounts, 1):
            account_file = self.accounts_dir / f"{acc}.json"
            status = "Ready"
            if account_file.exists():
                with open(account_file) as f:
                    data = json.load(f)
                    if data.get('last_error'):
                        status = "Error"
                    elif data.get('last_run'):
                        status = f"Last: {datetime.fromisoformat(data['last_run']).strftime('%Y-%m-%d %H:%M')}"

            print(f"{Style.BRIGHT}{i}{Style.RESET_ALL}. [{acc}] - {status}")

        try:
            choice = input(f"\n{Style.BRIGHT}[>] Select account (0 to cancel): {Style.RESET_ALL}")
            if not choice.isdigit() or int(choice) == 0:
                return

            idx = int(choice)
            if idx < 1 or idx > len(accounts):
                print(f"{Fore.RED}[✗] Invalid selection{Style.RESET_ALL}")
                return

            self.unlike_posts(accounts[idx - 1])
        except ValueError:
            print(f"{Fore.RED}[✗] Invalid input{Style.RESET_ALL}")
        except Exception as e:
            print(f"{Fore.RED}[✗] Error: {e}{Style.RESET_ALL}")

    def show_statistics(self):
        """Display statistics."""
        accounts = self.list_accounts()
        if not accounts:
            print(f"{Fore.YELLOW}No accounts added yet{Style.RESET_ALL}")
            input(f"\n{Style.BRIGHT}Press Enter to continue...{Style.RESET_ALL}")
            return

        print(f"\n{Fore.CYAN}📊 Statistics{Style.RESET_ALL}")
        print("=" * 40)

        total_unliked = 0
        for username in accounts:
            account_file = self.accounts_dir / f"{username}.json"
            try:
                with open(account_file, 'r') as f:
                    data = json.load(f)

                total_unliked += data.get('total_unliked', 0)
                print(f"\n{Style.BRIGHT}{Fore.BLUE}@{username}{Style.RESET_ALL}")
                print(f"📌 Unliked posts: {data.get('total_unliked', 0)}")
                if data.get('last_run'):
                    print(f"🕒 Last active: {datetime.fromisoformat(data['last_run']).strftime('%Y-%m-%d %H:%M')}")
                print(f"✨ Status: {'OK' if not data.get('last_error') else 'Error'}")
            except Exception:
                print(f"{Fore.RED}Could not read data for {username}{Style.RESET_ALL}")

        print(f"\n{Fore.GREEN}🎉 Total unliked: {total_unliked} posts{Style.RESET_ALL}")
        if self.excluded_users:
            print(f"{Fore.YELLOW}🚫 Excluding: {len(self.excluded_users)} users{Style.RESET_ALL}")
        input(f"\n{Style.BRIGHT}Press Enter to continue...{Style.RESET_ALL}")

    def show_settings(self):
        """Display and modify settings."""
        while True:
            print(f"\n{Fore.CYAN}{Style.BRIGHT}╔══════════════════════════════════╗")
            print("║          Settings Menu           ║")
            print(f"╚══════════════════════════════════╝{Style.RESET_ALL}")

            print(f"\n{Fore.YELLOW}▸ Delay Settings{Style.RESET_ALL}")
            print(f"  {Style.BRIGHT}1.{Style.RESET_ALL} Minimum Delay     : {Fore.GREEN}{CONFIG['delay']['min']}{Style.RESET_ALL} seconds")
            print(f"  {Style.BRIGHT}2.{Style.RESET_ALL} Maximum Delay     : {Fore.GREEN}{CONFIG['delay']['max']}{Style.RESET_ALL} seconds")

            print(f"\n{Fore.YELLOW}▸ Break Settings{Style.RESET_ALL}")
            print(f"  {Style.BRIGHT}3.{Style.RESET_ALL} Break Probability : {Fore.GREEN}{CONFIG['break']['probability'] * 100}%{Style.RESET_ALL}")
            print(f"  {Style.BRIGHT}4.{Style.RESET_ALL} Minimum Break     : {Fore.GREEN}{CONFIG['break']['min'] / 60:.1f}{Style.RESET_ALL} minutes")
            print(f"  {Style.BRIGHT}5.{Style.RESET_ALL} Maximum Break     : {Fore.GREEN}{CONFIG['break']['max'] / 60:.1f}{Style.RESET_ALL} minutes")

            print(f"\n{Fore.YELLOW}▸ Retry Settings{Style.RESET_ALL}")
            print(f"  {Style.BRIGHT}6.{Style.RESET_ALL} Maximum Retries   : {Fore.GREEN}{CONFIG['max_retries']}{Style.RESET_ALL}")
            print(f"  {Style.BRIGHT}7.{Style.RESET_ALL} Retry Delay       : {Fore.GREEN}{CONFIG['retry_delay']}{Style.RESET_ALL} seconds")

            print(f"\n{Fore.CYAN}▸ Navigation{Style.RESET_ALL}")
            print(f"  {Style.BRIGHT}0.{Style.RESET_ALL} Save and Return")

            try:
                print(f"\n╭─")
                choice = input("╰─▸ ").strip()

                if choice == "0":
                    print(f"\n{Fore.GREEN}✓ Settings saved successfully!{Style.RESET_ALL}")
                    time.sleep(1)
                    break

                if choice in ["1", "2", "3", "4", "5", "6", "7"]:
                    print("╭─")
                    try:
                        if choice == "1":
                            new_value = float(input("╰─▸ Enter new minimum delay (seconds): "))
                            CONFIG['delay']['min'] = new_value
                        elif choice == "2":
                            new_value = float(input("╰─▸ Enter new maximum delay (seconds): "))
                            CONFIG['delay']['max'] = new_value
                        elif choice == "3":
                            new_value = float(input("╰─▸ Enter new break probability (0-1): "))
                            if 0 <= new_value <= 1:
                                CONFIG['break']['probability'] = new_value
                            else:
                                raise ValueError("Probability must be between 0 and 1")
                        elif choice == "4":
                            new_value = float(input("╰─▸ Enter new minimum break time (minutes): "))
                            CONFIG['break']['min'] = new_value * 60
                        elif choice == "5":
                            new_value = float(input("╰─▸ Enter new maximum break time (minutes): "))
                            CONFIG['break']['max'] = new_value * 60
                        elif choice == "6":
                            new_value = int(input("╰─▸ Enter new maximum retries: "))
                            CONFIG['max_retries'] = new_value
                        elif choice == "7":
                            new_value = int(input("╰─▸ Enter new retry delay (seconds): "))
                            CONFIG['retry_delay'] = new_value

                        self.save_config()
                        print(f"\n{Fore.GREEN}✓ Setting updated successfully!{Style.RESET_ALL}")
                        time.sleep(1)
                    except ValueError as e:
                        print(f"\n{Fore.RED}✗ Invalid input: {e}{Style.RESET_ALL}")
                        time.sleep(2)
                else:
                    print(f"\n{Fore.RED}✗ Invalid choice{Style.RESET_ALL}")
                    time.sleep(1)

            except KeyboardInterrupt:
                break

    def change_speed_mode(self):
        """Let user pick a speed preset."""
        print(f"\n{Fore.CYAN}⚡ Speed Mode Selection{Style.RESET_ALL}")
        print("=" * 50)
        print(f"\n  {Fore.GREEN}1. 🐢 SAFE{Style.RESET_ALL}      — 30-120s delay, 60/hr, 400/day (~50 days)")
        print(f"  {Fore.YELLOW}2. 🚀 MODERATE{Style.RESET_ALL}  — 10-30s delay, 120/hr, 1000/day (~19 days)")
        print(f"  {Fore.RED}3. ⚡ FAST{Style.RESET_ALL}      — 3-8s delay, 200/hr, 2000/day (~10 days)")
        print(f"  {Fore.RED}4. 💀 AGGRESSIVE{Style.RESET_ALL} — 2-5s delay, 500/hr, 5000/day (~4 days)")
        print("\n  0. Cancel")

        choice = input(f"\n{Style.BRIGHT}Select mode: {Style.RESET_ALL}").strip()

        presets = {
            "1": {"delay": {"min": 30, "max": 120}, "hourly_limit": 60, "daily_limit": 400,
                  "break": {"min": 600, "max": 1800, "probability": 0.05}},
            "2": {"delay": {"min": 10, "max": 30}, "hourly_limit": 120, "daily_limit": 1000,
                  "break": {"min": 300, "max": 600, "probability": 0.03}},
            "3": {"delay": {"min": 3, "max": 8}, "hourly_limit": 200, "daily_limit": 2000,
                  "break": {"min": 120, "max": 300, "probability": 0.02}},
            "4": {"delay": {"min": 2, "max": 5}, "hourly_limit": 500, "daily_limit": 5000,
                  "break": {"min": 60, "max": 180, "probability": 0.01}},
        }

        if choice in presets:
            for key, value in presets[choice].items():
                CONFIG[key] = value
            self.save_config()
            names = {"1": "SAFE", "2": "MODERATE", "3": "FAST", "4": "AGGRESSIVE"}
            print(f"\n{Fore.GREEN}✓ Switched to {names[choice]} mode{Style.RESET_ALL}")
            time.sleep(1)
        elif choice != "0":
            print(f"{Fore.RED}Invalid option{Style.RESET_ALL}")

    def check_system_requirements(self) -> bool:
        """Check if system meets all requirements."""
        try:
            import psutil
            os_name = platform.system()
            logging.info(f"Operating System: {os_name}")
            return True
        except ImportError:
            logging.error("psutil not installed. Run: pip install -r requirements.txt")
            print(f"{Fore.RED}[✗] Missing dependencies. Run: pip install -r requirements.txt{Style.RESET_ALL}")
            return False

    def check_dependencies(self) -> bool:
        """Check and validate all required dependencies."""
        try:
            import ensta
            logging.info("Successfully imported ensta")
            return True
        except ImportError:
            logging.error("ensta library not found")
            print(f"{Fore.RED}[✗] ensta library not found. Run: pip install -r requirements.txt{Style.RESET_ALL}")
            return False
        except Exception as e:
            logging.error(f"Error importing ensta: {e}")
            print(f"{Fore.RED}[✗] Error importing ensta: {e}{Style.RESET_ALL}")
            return False


# --- Helper functions ---

def _get_post_owner(post: dict) -> str:
    """Extract owner username from both old and new export formats."""
    owner = post.get('title', '').lower()
    if not owner:
        for lv in post.get('label_values', []):
            if lv.get('title') == 'Owner':
                for d in lv.get('dict', []):
                    for entry in d.get('dict', []):
                        if entry.get('label') == 'Username':
                            return entry.get('value', '').lower()
    return owner


def _get_post_href(post: dict) -> Optional[str]:
    """Extract URL from both old and new export formats."""
    try:
        return post['string_list_data'][0]['href']
    except KeyError, IndexError, TypeError:
        pass
    try:
        for label_entry in post.get('label_values', []):
            if label_entry.get('label') == 'URL' and label_entry.get('href'):
                return label_entry['href']
    except KeyError, TypeError:
        pass
    return None


def _get_visible_length(text: str) -> int:
    """Calculate the visible length of text by removing ANSI color codes."""
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    return len(ansi_escape.sub('', text))


def _center_text_in_box(text: str, box_width: int = 48) -> str:
    """Center text in a box line, accounting for color codes."""
    visible_length = _get_visible_length(text)
    padding = (box_width - 2 - visible_length) // 2
    return f"║{' ' * padding}{text}{' ' * (box_width - 2 - visible_length - padding)}║"


def _menu_line(number: str, text: str, box_width: int = 40) -> str:
    """Create a properly aligned menu line."""
    prefix = f"│ {Style.BRIGHT}{number}.{Style.RESET_ALL} "
    content = text
    visible_length = _get_visible_length(f"{prefix}{content}")
    padding = box_width - visible_length + 1
    return f"{prefix}{content}{' ' * padding}│"


def main():
    """Main entry point."""
    try:
        print("\nWelcome to Instagram Mass Unliker!")
        print("Checking system requirements...")

        unliker = InstagramUnliker()

        if not unliker.check_dependencies():
            sys.exit(1)
        if not unliker.check_system_requirements():
            sys.exit(1)
        if not unliker.check_python_version():
            sys.exit(1)

        unliker.show_menu()

    except KeyboardInterrupt:
        print("\nProgram terminated by user.")
        sys.exit(0)
    except Exception as e:
        logging.error(f"Fatal error: {e}")
        print("\nAn unexpected error occurred. Please check the logs for details.")
        sys.exit(1)


if __name__ == "__main__":
    main()
