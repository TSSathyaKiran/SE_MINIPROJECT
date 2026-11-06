#!/usr/bin/env python3
"""Uptime check for the SRS app (SRS-NF-002, TC-Ops-01).

Calls GET /health on a fixed interval, appends `time,status` rows to a CSV
log and prints the availability percentage so far. Uses only the standard
library, so it runs anywhere Python does.

    python scripts/uptime_check.py
    python scripts/uptime_check.py --url http://localhost:8000 --interval 60 \
        --csv logs/uptime.csv

Stop with Ctrl+C; the final availability line prints before exit.
"""
import argparse
import csv
import sys
import time
import urllib.request
import urllib.error
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_URL = "http://localhost:8000"
DEFAULT_CSV = Path("logs") / "uptime.csv"


def check_health(base_url, timeout=5):
    """One probe of /health. Returns True when the app answers 200 OK."""
    try:
        with urllib.request.urlopen(base_url.rstrip("/") + "/health",
                                    timeout=timeout) as res:
            return res.status == 200
    except (urllib.error.URLError, OSError):
        return False


def append_row(csv_path, ok, when=None):
    """Append one `time,status` row (ISO 8601 UTC, ok/down) to the CSV log."""
    when = when or datetime.now(timezone.utc)
    new_file = not Path(csv_path).exists()
    with open(csv_path, "a", newline="") as f:
        writer = csv.writer(f)
        if new_file:
            writer.writerow(["time", "status"])
        writer.writerow([when.isoformat(timespec="seconds"),
                         "ok" if ok else "down"])


def availability(total, ok):
    """Availability percentage over the checks run so far."""
    return round(ok / total * 100, 2) if total else 0.0


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--url", default=DEFAULT_URL,
                        help=f"app base URL (default {DEFAULT_URL})")
    parser.add_argument("--interval", type=float, default=60,
                        help="seconds between checks (default 60)")
    parser.add_argument("--csv", default=str(DEFAULT_CSV),
                        help=f"log file (default {DEFAULT_CSV})")
    parser.add_argument("--checks", type=int, default=0,
                        help="stop after N checks (default: run until Ctrl+C)")
    args = parser.parse_args(argv)

    Path(args.csv).parent.mkdir(parents=True, exist_ok=True)
    total = ok_count = 0
    print(f"Checking {args.url}/health every {args.interval:g}s -> {args.csv}")
    try:
        while True:
            ok = check_health(args.url)
            total += 1
            ok_count += ok
            append_row(args.csv, ok)
            print(f"{datetime.now(timezone.utc).isoformat(timespec='seconds')} "
                  f"{'ok' if ok else 'down'} "
                  f"(availability {availability(total, ok_count)}%)")
            if args.checks and total >= args.checks:
                break
            time.sleep(args.interval)
    except KeyboardInterrupt:
        print()
    print(f"Availability: {availability(total, ok_count)}% "
          f"({ok_count}/{total} checks ok)")
    return 0 if ok_count == total else 1


if __name__ == "__main__":
    sys.exit(main())
