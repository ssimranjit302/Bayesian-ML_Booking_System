import json
from datetime import datetime, timezone, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

# ---------- Step 1: Get current London time ----------
# London is UTC+0 or UTC+1 depending on DST.
london_time = datetime.now(ZoneInfo("Europe/London"))
print(london_time)

# Extract the next full hour (e.g., if 15:24 → next hour = 16)
next_hour = (london_time + timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)
next_hour_12 = next_hour.strftime("%I:00 %p")  # e.g., "04:00 PM"

print(f"Current London time: {london_time.strftime('%H:%M')}")
print(f"Filtering data starting from next hour: {next_hour_12}")

# ---------- Step 2: Load JSON file ----------
BASE_DIR = Path(__file__).resolve().parent

input_file = BASE_DIR / "RebaseHourlyTrends.json"
output_file = BASE_DIR / "UpcomingHourData.json"

with open(input_file, "r") as f:
    data = json.load(f)

# ---------- Step 3: Parse and filter ----------
filtered_data = []
for block in data:
    start_time_str = block.get("Start Time")
    if not start_time_str:
        continue

    # Parse "Start Time" like "04:00 PM" → 24-hour integer 16
    start_dt = datetime.strptime(start_time_str, "%I:%M %p")
    start_hour = start_dt.hour
    next_hour_int = next_hour.hour

    # Select all blocks with start time >= next hour
    if start_hour >= next_hour_int:
        filtered_data.append(block)

# ---------- Step 4: Save filtered data ----------
with open(output_file, "w") as f:
    json.dump(filtered_data, f, indent=4)

print(f" Output saved to {output_file} — contains {len(filtered_data)} records.")
