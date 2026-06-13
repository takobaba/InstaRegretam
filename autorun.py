#!/usr/bin/env python3
"""Auto-retry wrapper for InstaRegretam.

Runs the unliker, and if it gets rate-limited (exit code 1),
waits and retries automatically. The main script remains unchanged
and can still be run manually.

Usage:
    python3 autorun.py
"""
import sys
import time
from datetime import datetime

WAIT_HOURS = 2
MAX_RETRIES = 5

def run():
    """Run the unliker directly."""
    from instaregretam import InstagramUnliker
    try:
        unliker = InstagramUnliker()
        if not unliker.check_dependencies():
            return 1
        if not unliker.check_system_requirements():
            return 1
        if not unliker.check_python_version():
            return 1
        accounts = unliker.list_accounts()
        if not accounts:
            print("No accounts configured.")
            return 1
        unliker.unlike_posts(accounts[0])
        return 0
    except SystemExit as e:
        return e.code
    except Exception as e:
        print(f"Error: {e}")
        return 1

def main():
    retries = 0

    while retries < MAX_RETRIES:
        print(f"\n{'='*50}")
        print(f"[{datetime.now().strftime('%b %d %H:%M')}] Starting run (attempt {retries + 1}/{MAX_RETRIES})")
        print(f"{'='*50}\n")

        exit_code = run()

        if exit_code == 0:
            print(f"\n✅ Completed successfully!")
            break
        elif exit_code == 1:
            retries += 1
            if retries >= MAX_RETRIES:
                print(f"\n❌ Max retries ({MAX_RETRIES}) reached. Giving up.")
                break
            resume_time = datetime.now().strftime('%H:%M')
            wait_seconds = WAIT_HOURS * 3600
            print(f"\n⏳ Rate limited. Waiting {WAIT_HOURS} hours before retry...")
            print(f"   Started waiting at: {resume_time}")
            print(f"   Will retry at: {datetime.fromtimestamp(time.time() + wait_seconds).strftime('%H:%M')}")
            print(f"   (Ctrl+C to stop)")
            try:
                time.sleep(wait_seconds)
            except KeyboardInterrupt:
                print("\n\n🛑 Stopped by user.")
                break
        else:
            print(f"\n❌ Script exited with unexpected code: {exit_code}")
            break

if __name__ == "__main__":
    main()
