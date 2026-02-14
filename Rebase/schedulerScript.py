import subprocess
from datetime import datetime, timedelta, time
from pathlib import Path
import time
import json
from zoneinfo import ZoneInfo


# Path to your pipeline script
BASE_DIR = Path(__file__).resolve().parent
PIPELINE_PATH = BASE_DIR / "7_pipeline.py"

input_file = BASE_DIR / "RebaseTemplate.json"
output_file = BASE_DIR / "Master.json"

# =========== Template Reset before running Scheduler ===========

# ----------  Get today's date in London ----------
london_tz = ZoneInfo("Europe/London")
london_today = datetime.now(london_tz).strftime("%Y-%m-%d")

# ----------  Read JSON template ----------
with open(input_file, "r", encoding="utf-8") as f:
    data = json.load(f)

# ---------- Update all 'Date' fields ----------
for entry in data:
    if "Date" in entry:
        entry["Date"] = london_today

# ---------- Save updated JSON ----------
with open(output_file, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=4, ensure_ascii=False)

print(f" Master.json created successfully with updated date: {london_today}")

# =======================================================

# Define all scheduled times (6:55 → 19:55, every 15 mins)
run_times_str = [
    "06:55", "07:10", "07:25", "07:40", "07:55",
    "08:10", "08:25", "08:40", "08:55",
    "09:10", "09:25", "09:40", "09:55",
    "10:10", "10:25", "10:40", "10:55",
    "11:10", "11:25", "11:40", "11:55",
    "12:10", "12:25", "12:40", "12:55",
    "13:10", "13:25", "13:40", "13:55",
    "14:10", "14:25", "14:40", "14:55",
    "15:10", "15:25", "15:40", "15:55",
    "16:10", "16:25", "16:40", "16:55",
    "17:10", "17:25", "17:40", "17:55",
    "18:10", "18:25", "18:40", "18:55",
    "19:10", "19:25", "19:40", "19:55"
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
