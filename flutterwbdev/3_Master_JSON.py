import json
from datetime import datetime
import zoneinfo
from pathlib import Path

# --- Paths ---
BASE_DIR = Path(__file__).resolve().parent
FILTERED_JSON = BASE_DIR / "Filtered_FlutterBookedSlots.json"
MASTER_WEEKEND = BASE_DIR / "MasterWeekend.json"
MASTER_WEEKDAY = BASE_DIR / "MasterWeekday.json"

# --- Load Filtered Slots ---
with open(FILTERED_JSON, "r", encoding="utf-8") as f:
    filtered_slots = json.load(f)

# --- Determine today's London day ---
london_tz = zoneinfo.ZoneInfo("Europe/London")
today_london = datetime.now(london_tz)
is_weekend = today_london.weekday() >= 5  # 5 = Saturday, 6 = Sunday

# Select correct Master JSON
MASTER_FILE = MASTER_WEEKEND if is_weekend else MASTER_WEEKDAY
print(f"Updating {'Weekend' if is_weekend else 'Weekday'} master file -> {MASTER_FILE.name}")

# --- Load Master Data ---
with open(MASTER_FILE, "r", encoding="utf-8") as f:
    master_data = json.load(f)

# --- Update Matching Blocks ---
for master_event in master_data:
    for filtered_event in filtered_slots:
        # Compare all keys except booked and Available Slots
        if (
            master_event["date"] == filtered_event["date"]
            and master_event["start_time"] == filtered_event["start_time"]
            and master_event["end_time"] == filtered_event["end_time"]
            and master_event["event_name"] == filtered_event["event_name"]
            and master_event["capacity"] == filtered_event["capacity"]
        ):
            master_event["booked"] = filtered_event["booked"]
            master_event["Available Slots"] = (
                master_event["capacity"] - master_event["booked"]
            )

# --- Save updated data back to same Master file ---
with open(MASTER_FILE, "w", encoding="utf-8") as f:
    json.dump(master_data, f, ensure_ascii=False, indent=4)

print(f"Master file '{MASTER_FILE.name}' successfully updated with new bookings.")
