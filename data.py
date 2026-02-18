#!/usr/bin/env python3
"""
Calculate total internet data usage across multiple devices for a month.
- For the current machine (Windows/Fedora), optionally auto-fetch cumulative usage since boot
  (useful only if you rebooted at the start of the month).
- Manual entry for all other devices (iPhone, Samsung, and the other PC).
- All values are converted to MB for summation.
"""

import re
import platform
import sys

try:
    import psutil
except ImportError:
    print("Warning: psutil not installed. Auto-fetch will be disabled.")
    psutil = None

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def parse_size(size_str):
    """Convert a string like '10 GB' or '500 MB' into megabytes (float)."""
    size_str = size_str.strip().upper()
    match = re.match(r'^([\d.]+)\s*(MB|GB|TB)?$', size_str)
    if not match:
        raise ValueError(f"Invalid size format: {size_str}")

    value, unit = match.groups()
    value = float(value)

    if unit == 'TB':
        return value * 1024 * 1024
    elif unit == 'GB':
        return value * 1024
    elif unit == 'MB' or not unit:
        return value
    else:
        return value

def manual_entry(device_name):
    """Ask user to enter data usage for a device."""
    while True:
        inp = input(f"Enter data used by {device_name} (e.g., '15 GB', '500 MB'): ").strip()
        if not inp:
            return 0.0
        try:
            return parse_size(inp)
        except ValueError as e:
            print(f"Invalid input: {e}. Try again.")

def auto_fetch_current_machine():
    """
    Get cumulative network I/O (sent+received) since boot for the current machine.
    Returns MB as float, or None if not possible.
    """
    if not psutil:
        return None

    try:
        net_io = psutil.net_io_counters()
        total_bytes = net_io.bytes_sent + net_io.bytes_recv
        total_mb = total_bytes / (1024 * 1024)
        return total_mb
    except Exception as e:
        print(f"Auto-fetch failed: {e}")
        return None

# ----------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------
def main():
    print("=" * 60)
    print("MONTHLY INTERNET DATA USAGE CALCULATOR")
    print("=" * 60)
    print("\nThis script sums data usage across your devices for a month.")
    print("For mobile devices, you will need to look up the values manually.")
    print("For the PC you're running this on, you can optionally auto-fetch")
    print("cumulative usage since boot – but this is only accurate if you")
    print("rebooted at the very start of the month.")
    print("-" * 60)

    os_name = platform.system()
    total_mb = 0.0

    # ------------------------------------------------------------------
    # Windows PC
    # ------------------------------------------------------------------
    if os_name == "Windows":
        print("\n--- Windows PC (this machine) ---")
        print("Auto-fetch gives total data since last boot.")
        choice = input("Use auto-fetch (y) or manual entry (n)? (y/n): ").strip().lower()
        if choice == 'y':
            mb = auto_fetch_current_machine()
            if mb is not None:
                print(f"Auto-fetched: {mb:.2f} MB ({mb/1024:.2f} GB) since boot.")
                total_mb += mb
            else:
                print("Falling back to manual entry.")
                total_mb += manual_entry("Windows PC")
        else:
            total_mb += manual_entry("Windows PC")
    else:
        # Not running on Windows – ask manually
        total_mb += manual_entry("Windows PC")

    # ------------------------------------------------------------------
    # Fedora PC
    # ------------------------------------------------------------------
    if os_name == "Linux" and "fedora" in platform.version().lower():   # crude detection
        print("\n--- Fedora PC (this machine) ---")
        print("Auto-fetch gives total data since last boot.")
        choice = input("Use auto-fetch (y) or manual entry (n)? (y/n): ").strip().lower()
        if choice == 'y':
            mb = auto_fetch_current_machine()
            if mb is not None:
                print(f"Auto-fetched: {mb:.2f} MB ({mb/1024:.2f} GB) since boot.")
                total_mb += mb
            else:
                print("Falling back to manual entry.")
                total_mb += manual_entry("Fedora PC")
        else:
            total_mb += manual_entry("Fedora PC")
    else:
        total_mb += manual_entry("Fedora PC")

    # ------------------------------------------------------------------
    # iPhone 11 Pro
    # ------------------------------------------------------------------
    print("\n--- iPhone 11 Pro ---")
    print("Tip: Settings > Cellular > Current Period (scroll to bottom).")
    total_mb += manual_entry("iPhone 11 Pro")

    # ------------------------------------------------------------------
    # Samsung S8
    # ------------------------------------------------------------------
    print("\n--- Samsung S8 ---")
    print("Tip: Settings > Connections > Data Usage > Mobile data usage.")
    total_mb += manual_entry("Samsung S8")

    # ------------------------------------------------------------------
    # Results
    # ------------------------------------------------------------------
    print("\n" + "=" * 60)
    print("TOTAL MONTHLY DATA USAGE (ALL DEVICES)")
    print("=" * 60)
    print(f"{total_mb:.2f} MB")
    print(f"{total_mb / 1024:.2f} GB")
    if total_mb > 1024 * 1024:
        print(f"{total_mb / (1024*1024):.2f} TB")

if __name__ == "__main__":
    main()