import json
from datetime import datetime, timedelta
import zoneinfo
from pathlib import Path

# --- Paths ---
BASE_DIR = Path(__file__).resolve().parent
INPUT_JSON = BASE_DIR / "FlutterBookedSlots.json"
OUTPUT_JSON = BASE_DIR / "Filtered_FlutterBookedSlots.json"

# --- Load JSON data ---
with open(INPUT_JSON, "r", encoding="utf-8") as f:
    events = json.load(f)

# --- Get current London time ---
london_tz = zoneinfo.ZoneInfo("Europe/London")
now_london = datetime.now(london_tz)
current_time = now_london.strftime("%H:%M")
print("Current London Time:", current_time)

# --- Filter slots after current time ---
filtered_events = []
for ev in events:
    event_time = datetime.strptime(ev["start_time"], "%H:%M").time()
    if event_time > now_london.time():
        filtered_events.append(ev)

# --- Save filtered events with same formatting ---
with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
    json.dump(filtered_events, f, ensure_ascii=False, indent=4)

print(f"Filtered {len(filtered_events)} future slots saved to {OUTPUT_JSON.name}")
