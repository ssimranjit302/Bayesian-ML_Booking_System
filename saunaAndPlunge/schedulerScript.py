import subprocess
from datetime import datetime, timedelta, time
from pathlib import Path
import time
import json
from zoneinfo import ZoneInfo


# Path to your pipeline script
BASE_DIR = Path(__file__).resolve().parent
PIPELINE_PATH = BASE_DIR / "5_pipeline.py"

input_file = BASE_DIR / "saunaPlungeTemplate.json"
output_file = BASE_DIR / "Master.json"

# =========== Template Reset before running Scheduler ===========

# ----------  Get today's date in London ----------
london_tz = ZoneInfo("Europe/London")
london_today = datetime.now(london_tz).strftime("%Y-%m-%d")

# ---------- Read JSON template ----------
with open(input_file, "r", encoding="utf-8") as f:
    data = json.load(f)

# ----------  Update all 'Date' fields ----------
for entry in data:
    if "Date" in entry:
        entry["Date"] = london_today

# ---------- Save updated JSON ----------
with open(output_file, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=4, ensure_ascii=False)

print(f" Master.json created successfully with updated date: {london_today}")

# =======================================================

# Define all scheduled times (6:20 → 19:20, every 30 mins)
run_times_str = [
    "6:20", "6:50",
    "7:20", "7:50",
    "8:20", "8:50",
    "9:20", "9:50",
    "10:20", "10:50",
    "11:20", "11:50",
    "12:20", "12:50",
    "13:20", "13:50",
    "14:20", "14:50",
    "15:20", "15:50",
    "16:20", "16:50",
    "17:20", "17:50",
    "18:20", "18:50",
    "19:20"
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
