import requests
import json
import pandas as pd
from datetime import datetime
from pathlib import Path
import zoneinfo

# --- CONFIG ---
tenant_id = 1152
london_tz = zoneinfo.ZoneInfo("Europe/London")

# Get today's London date
london_today = datetime.now(london_tz)
year = london_today.year
month = london_today.month
today_str = london_today.strftime("%Y-%m-%d")

# --- Fetch available dates for the month ---
url_dates = f"https://api.wunderbook.com/api/services/app/MobileEventSchedule/GetScheduleDates?month={month}&year={year}&tenantId={tenant_id}"
response = requests.get(url_dates)
dates_json = response.json()

# Extract and filter for today's date only
available_dates = [
    datetime.fromisoformat(d.replace("Z", ""))
    for d in dates_json['result']
]
available_dates = [d for d in available_dates if d.strftime("%Y-%m-%d") == today_str]

print("London Today:", today_str)
print("Available Dates:", available_dates)

# --- Schedule events for today ---
url_events = "https://api.wunderbook.com/api/services/app/MobileEventSchedule/ListScheduledEventsNEW"
all_events = []

for date_obj in available_dates:
    schedule_date = date_obj.strftime("%Y-%m-%d")
    print(f"Extracting events scheduled for: {schedule_date}")
    payload = {
        "tenantId": tenant_id,
        "scheduleDate": schedule_date
    }

    response = requests.post(url_events, json=payload)
    events_json = response.json()

    for event in events_json['result']:
        # Handle both time-only and datetime formats safely
        start_raw = event['startTime']
        end_raw = event['endTime']

        try:
            start_time = datetime.fromisoformat(start_raw.replace("Z", "")).strftime("%H:%M")
            end_time = datetime.fromisoformat(end_raw.replace("Z", "")).strftime("%H:%M")
        except ValueError:
            # Fallback if it's time-only (e.g., '10:00:00')
            start_time = datetime.strptime(start_raw, "%H:%M:%S").strftime("%H:%M")
            end_time = datetime.strptime(end_raw, "%H:%M:%S").strftime("%H:%M")

        all_events.append({
            "date": schedule_date,
            "start_time": start_time,
            "end_time": end_time,
            "event_name": event['eventName'],
            "capacity": event['attendanceLimit'],
            "booked": event['totalBookings'],
            "Available Slots": event['attendanceLimit'] - event['totalBookings']
        })

# --- Save to CSV ---
df = pd.DataFrame(all_events).drop_duplicates()

BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "FlutterBookedSlots.csv"

df.to_csv(OUTPUT_DIR, index=False)

import json

# --- Remove duplicate dictionaries (preserve key order) ---
seen = set()
unique_events = []
for ev in all_events:
    ev_str = json.dumps(ev, sort_keys=False)
    if ev_str not in seen:
        seen.add(ev_str)
        unique_events.append(ev)

# --- Save to JSON ---
JSON_OUTPUT = BASE_DIR / "FlutterBookedSlots.json"
with open(JSON_OUTPUT, "w", encoding="utf-8") as f:
    json.dump(unique_events, f, ensure_ascii=False, indent=4)

print("Saved schedule JSON with", len(unique_events), "unique entries")

print("Saved schedule CSV with", len(df), "entries")
