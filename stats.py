#!/usr/bin/env python3
"""Analyze InstaRegretam logs and print stats."""

import sys
from datetime import datetime
from pathlib import Path
from collections import defaultdict

LOG_FILE = Path("logs/requests.log")


def parse_log():
    """Parse requests.log into structured events."""
    unlikes = []
    blocks = []
    errors = []
    sessions = []

    if not LOG_FILE.exists():
        print("No log file found at logs/requests.log")
        sys.exit(1)

    with open(LOG_FILE, 'r') as f:
        for line in f:
            parts = [p.strip() for p in line.strip().split('|')]
            if len(parts) < 2:
                continue

            timestamp_str = parts[0]
            event_type = parts[1]

            try:
                timestamp = datetime.fromisoformat(timestamp_str)
            except ValueError:
                continue

            if event_type == 'UNLIKE':
                unlikes.append(timestamp)
            elif event_type == 'BLOCKED':
                blocks.append(timestamp)
            elif event_type == 'ERROR':
                errors.append(timestamp)
            elif event_type == 'SESSION_START':
                sessions.append(timestamp)

    return unlikes, blocks, errors, sessions


def print_summary(unlikes, blocks, errors, sessions):
    """Print overall summary stats."""
    if not unlikes:
        print("No unlikes recorded yet.")
        return

    first = unlikes[0]
    last = unlikes[-1]
    days = (last.date() - first.date()).days + 1

    print("╔══════════════════════════════════════╗")
    print("║        InstaRegretam Stats           ║")
    print("╚══════════════════════════════════════╝")
    print()
    print(f"  Total unlikes:  {len(unlikes):,}")
    print(f"  Total blocks:   {len(blocks)}")
    print(f"  Total errors:   {len(errors)}")
    print(f"  Sessions:       {len(sessions)}")
    print(f"  Date range:     {first.strftime('%Y-%m-%d %H:%M')} → {last.strftime('%Y-%m-%d %H:%M')}")
    print(f"  Days active:    {days}")
    print(f"  Avg per day:    {len(unlikes) // days:,}")
    print()


def print_daily_breakdown(unlikes, blocks):
    """Print daily totals."""
    daily = defaultdict(int)
    daily_blocks = defaultdict(int)

    for ts in unlikes:
        daily[ts.strftime('%Y-%m-%d')] += 1
    for ts in blocks:
        daily_blocks[ts.strftime('%Y-%m-%d')] += 1

    print("─── Daily Breakdown ───────────────────")
    print(f"  {'Date':<12} {'Unlikes':>8} {'Blocks':>8}")
    print(f"  {'─'*12} {'─'*8} {'─'*8}")

    cumulative = 0
    for date in sorted(daily.keys()):
        count = daily[date]
        cumulative += count
        blk = daily_blocks.get(date, 0)
        blk_str = f"🚨 {blk}" if blk > 0 else ""
        print(f"  {date:<12} {count:>8,} {blk_str:>8}")

    print(f"  {'─'*12} {'─'*8}")
    print(f"  {'Total':<12} {cumulative:>8,}")
    print()


def print_hourly_breakdown(unlikes, blocks):
    """Print hourly breakdown."""
    hourly = defaultdict(int)
    block_hours = set()

    for ts in unlikes:
        hourly[ts.strftime('%Y-%m-%d %H:00')] += 1
    for ts in blocks:
        block_hours.add(ts.strftime('%Y-%m-%d %H:00'))

    print("─── Hourly Breakdown ──────────────────")
    print(f"  {'Hour':<17} {'Unlikes':>8} {'Rate/min':>9} {'Cumul':>8}  Note")
    print(f"  {'─'*17} {'─'*8} {'─'*9} {'─'*8}  {'─'*10}")

    cumulative = 0
    for hour in sorted(hourly.keys()):
        count = hourly[hour]
        cumulative += count
        rate = count / 60
        note = "🚨 BLOCKED" if hour in block_hours else ""
        print(f"  {hour:<17} {count:>8,} {rate:>8.1f} {cumulative:>8,}  {note}")

    print()


def print_current_session(unlikes, blocks):
    """Print stats for the most recent session (last hour of activity)."""
    if not unlikes:
        return

    last = unlikes[-1]
    # Get unlikes from the last hour
    recent = [ts for ts in unlikes if (last - ts).total_seconds() < 3600]
    recent_blocks = [ts for ts in blocks if (last - ts).total_seconds() < 3600]

    print("─── Last Hour ─────────────────────────")
    print(f"  Unlikes:    {len(recent):,}")
    print(f"  Rate:       {len(recent) / 60:.1f}/min ({len(recent):,}/hr)")
    if recent_blocks:
        print(f"  Blocks:     🚨 {len(recent_blocks)}")
    print(f"  Last at:    {last.strftime('%H:%M:%S')}")
    print()


def main():
    unlikes, blocks, errors, sessions = parse_log()
    print()
    print_summary(unlikes, blocks, errors, sessions)
    print_daily_breakdown(unlikes, blocks)
    print_hourly_breakdown(unlikes, blocks)
    print_current_session(unlikes, blocks)


if __name__ == "__main__":
    main()
