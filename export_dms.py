#!/usr/bin/env python3
"""Extract DM participant list from Instagram data export zip."""

import json
import sys
import zipfile
from pathlib import Path

def find_export_zip():
    """Find the Instagram export zip in the current directory."""
    zips = sorted(Path('.').glob('instagram-*.zip'), key=lambda p: p.stat().st_mtime, reverse=True)
    if not zips:
        print("No instagram-*.zip file found in current directory.")
        sys.exit(1)
    return zips[0]


def extract_dm_participants(zip_path):
    """Extract participant usernames from DM message files in the zip."""
    participants = {}

    with zipfile.ZipFile(zip_path) as zf:
        # Find all message_1.json files (first page of each conversation)
        msg_files = [f for f in zf.namelist()
                     if '/messages/inbox/' in f and f.endswith('message_1.json')]

        for msg_file in msg_files:
            try:
                data = json.loads(zf.read(msg_file))
                # Get participants from the message file
                thread_participants = data.get('participants', [])
                title = data.get('title', '')
                messages = data.get('messages', [])

                # Extract usernames (exclude self)
                usernames = [p.get('name', '') for p in thread_participants]

                # Get message count and last message date
                msg_count = len(messages)
                last_msg = None
                if messages:
                    last_ts = messages[0].get('timestamp_ms', 0)
                    if last_ts:
                        from datetime import datetime
                        last_msg = datetime.fromtimestamp(last_ts / 1000).strftime('%Y-%m-%d')

                for username in usernames:
                    if username and username.lower() != 'kayatar':
                        if username not in participants:
                            participants[username] = {
                                'messages': msg_count,
                                'last_active': last_msg,
                                'is_group': len(usernames) > 2,
                                'title': title if len(usernames) > 2 else None,
                            }
                        else:
                            participants[username]['messages'] += msg_count

            except (json.JSONDecodeError, KeyError):
                continue

    return participants


def main():
    zip_path = find_export_zip()
    print(f"Reading: {zip_path}")
    print()

    participants = extract_dm_participants(zip_path)

    # Sort by message count (most active first)
    sorted_participants = sorted(participants.items(), key=lambda x: x[1]['messages'], reverse=True)

    print(f"╔══════════════════════════════════════╗")
    print(f"║       DM Participants ({len(sorted_participants):,})        ║")
    print(f"╚══════════════════════════════════════╝")
    print()
    print(f"  {'Username':<30} {'Messages':>8}  {'Last Active':<12} {'Group'}")
    print(f"  {'─'*30} {'─'*8}  {'─'*12} {'─'*5}")

    for username, info in sorted_participants:
        group = "👥" if info['is_group'] else ""
        last = info['last_active'] or '?'
        print(f"  {username:<30} {info['messages']:>8}  {last:<12} {group}")

    print()
    print(f"  Total conversations: {len(sorted_participants):,}")
    print()

    # Save to file
    output_file = 'dm_participants.txt'
    with open(output_file, 'w') as f:
        f.write(f"DM Participants ({len(sorted_participants)} conversations)\n")
        f.write(f"{'='*60}\n\n")
        for username, info in sorted_participants:
            group = " [GROUP]" if info['is_group'] else ""
            last = info['last_active'] or '?'
            f.write(f"@{username} — {info['messages']} msgs — last: {last}{group}\n")

    print(f"  Saved to: {output_file}")


if __name__ == "__main__":
    main()
