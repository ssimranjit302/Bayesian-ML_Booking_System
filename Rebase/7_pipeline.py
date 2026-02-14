import subprocess
import os
import json
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo

PROJECT_DIR = Path(__file__).resolve().parent
MASTER_FILE = PROJECT_DIR / "Master.json"
TEMPLATE_SCRIPT = PROJECT_DIR / "templateReset.py"

# ------------------------------------------------------------------
# PRE-CHECK: Ensure Master.json exists and is fresh (London time)
# ------------------------------------------------------------------

def ensure_fresh_master():
    london_time = datetime.now(ZoneInfo("Europe/London"))
    today_str = london_time.strftime("%Y-%m-%d")  # e.g. 2025-11-14

    # Case 1: Master.json does not exist
    if not MASTER_FILE.exists():
        print("Master.json not found. Running templateReset.py...")
        subprocess.run(["python3", str(TEMPLATE_SCRIPT)], check=True)
        return

    # Case 2: Master.json exists → validate date
    try:
        with open(MASTER_FILE, "r") as f:
            data = json.load(f)

        # Empty or malformed Master.json
        if not data or "Date" not in data[0]:
            print("Master.json is empty or malformed. Regenerating...")
            subprocess.run(["python3", str(TEMPLATE_SCRIPT)], check=True)
            return

        master_date = data[0]["Date"]

        if master_date != today_str:
            print(
                f"Master.json date mismatch "
                f"(found: {master_date}, expected: {today_str}). "
                f"Regenerating..."
            )
            subprocess.run(["python3", str(TEMPLATE_SCRIPT)], check=True)
        else:
            print("Master.json is up-to-date for today (London time).")

    except Exception as e:
        print(f"Error validating Master.json ({e}). Regenerating...")
        subprocess.run(["python3", str(TEMPLATE_SCRIPT)], check=True)

# ------------------------------------------------------------------
# EXISTING PIPELINE LOGIC (UNCHANGED)
# ------------------------------------------------------------------

def run_step(script_name):
    script_path = PROJECT_DIR / script_name
    print(f"Running {script_path}...")
    result = subprocess.run(["python3", str(script_path)], capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error in {script_name}: {result.stderr}")
        exit(1)
    print(f"{script_name} completed successfully.\n")


def main():
    # Ensure Master.json is present and fresh before pipeline runs
    ensure_fresh_master()

    scripts = [
        "1_appointmentRawData.py",
        "2_BookedSlotsRaw.py",
        "3_HourlyTrends.py",
        "4_TripedUpcomingHourly.py",
        "5_MasterJSON.py",
        "6_HistoricalExcel.py"
    ]

    for script in scripts:
        run_step(script)

    print("Pipeline completed successfully — final output ready!")


if __name__ == "__main__":
    main()
