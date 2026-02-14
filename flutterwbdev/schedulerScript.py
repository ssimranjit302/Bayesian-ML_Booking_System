import subprocess
from datetime import datetime, timedelta, time
from pathlib import Path
import time
import json
from zoneinfo import ZoneInfo


# Path to your pipeline script
BASE_DIR = Path(__file__).resolve().parent
PIPELINE_PATH = BASE_DIR / "5_pipeline.py"
input1 = BASE_DIR / "templateWeekend.json"
output1 = BASE_DIR / "MasterWeekend.json"
input2 = BASE_DIR / "templateWeekday.json"
output2 = BASE_DIR / "MasterWeekday.json"

# ================

# --- Load timezone-aware current London date ---
london_tz = ZoneInfo("Europe/London")
today_london = datetime.now(london_tz).strftime("%Y-%m-%d")

# --- Function to update and save master file ---
def update_template(input_file, output_file):
    with open(input_file, "r") as f:
        data = json.load(f)

    # Update date for each entry
    for entry in data:
        entry["date"] = today_london

    # Save to new file
    with open(output_file, "w") as f:
        json.dump(data, f, indent=4)

    print(f"{output_file} created with date {today_london}")

# --- Run for both templates ---
update_template(input1, output1)
update_template(input2, output2)

# =======================================================

# Define all scheduled times (6:55 → 19:55, every 15 mins)
run_times_str = [
    "09:55",
    "10:25", "10:55",
    "11:25", "11:55",
    "17:55",
    "18:55",
    "19:55"
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
