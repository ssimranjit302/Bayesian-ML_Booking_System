import subprocess
from datetime import datetime, timedelta, time
from pathlib import Path
import time
import json
from zoneinfo import ZoneInfo


# Path to your pipeline script
BASE_DIR = Path(__file__).resolve().parent
PIPELINE_PATH = BASE_DIR / "6_pipeline.py"

# =========== Template Reset before running Scheduler ===========

def run_step(script_name):
    script_path = BASE_DIR / script_name
    print(f"Running {script_path}...")
    result = subprocess.run(["python3", str(script_path)], capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error in {script_name}: {result.stderr}")
        exit(1)
    print(f"{script_name} completed successfully.\n")


def main():
    scripts = [
        "1_RebelRawData.py",
        "2_RebelSlotsExcel.py"
    ]

    for script in scripts:
        run_step(script)

    # Rename final output files
    excel_src = BASE_DIR / "RebelSlotsExcel.xlsx"
    json_src = BASE_DIR / "RebelSlotsData.json"
    excel_dst = BASE_DIR / "Master.xlsx"
    json_dst = BASE_DIR / "Master.json"

    if excel_src.exists():
        excel_src.rename(excel_dst)
        print(f"Renamed: {excel_src.name} → {excel_dst.name}")
    else:
        print("Warning: RebelSlotsExcel.xlsx not found.")

    if json_src.exists():
        json_src.rename(json_dst)
        print(f"Renamed: {json_src.name} → {json_dst.name}")
    else:
        print("Warning: RebelSlotsData.json not found.")

if __name__ == "__main__":
    main()

time.sleep(5)

# =======================================================

# Define all scheduled times (6:55 → 19:55, every 15 mins)
run_times_str = [
    "06:10",
    "07:10",
    "08:10",
    "09:10",
    "10:10",
    "11:10",
    "12:10",
    "13:10",
    "14:10",
    "15:10",
    "16:10",
    "17:10",
    "18:10",
    "19:10"
]

# Convert strings to datetime.time objects
run_times = [datetime.strptime(t, "%H:%M").time() for t in run_times_str]


def run_pipeline():
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Running pipeline...")
    subprocess.run(["python3", PIPELINE_PATH])


def get_next_times(run_times):
    now = datetime.now().time()
    remaining = [t for t in run_times if t > now]
    return remaining


def main():
    remaining_times = get_next_times(run_times)

    if not remaining_times:
        print("No scheduled times left today. Exiting.")
        return

    for t in remaining_times:
        # Compute seconds until next run
        now = datetime.now()
        next_run = datetime.combine(now.date(), t)
        delta_seconds = (next_run - now).total_seconds()

        if delta_seconds > 0:
            print(f"Next run at {t.strftime('%H:%M')} ({int(delta_seconds)} sec from now)")
            # Wait until the scheduled time
            time.sleep(delta_seconds)

        # Run pipeline
        run_pipeline()

    print("All remaining scheduled runs done. Exiting.")


if __name__ == "__main__":
    main()
