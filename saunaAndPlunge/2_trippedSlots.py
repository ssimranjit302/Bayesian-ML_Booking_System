import json
from datetime import datetime
from zoneinfo import ZoneInfo
from pathlib import Path

# ---------- CONFIG ----------
BASE_DIR = Path(__file__).resolve().parent

INPUT_FILE = BASE_DIR / "sauna_slots_today.json"
OUTPUT_FILE = BASE_DIR / "sauna_slots_filtered.json"

# ---------- Load input JSON ----------
with open(INPUT_FILE, "r") as f:
    data = json.load(f)

# ---------- Get current London time ----------
london_time = datetime.now(ZoneInfo("Europe/London"))
print(f"Current London time: {london_time.strftime('%I:%M %p')}")

# ---------- Convert and filter ----------
filtered = []
for slot in data:
    # Combine date + start time string into a full datetime (in London timezone)
    slot_datetime = datetime.strptime(
        f"{slot['Date']} {slot['Start Time']}", "%Y-%m-%d %I:%M %p"
    ).replace(tzinfo=ZoneInfo("Europe/London"))

    # Keep only slots that start after the current time
    if slot_datetime >= london_time:
        filtered.append(slot)

# ---------- Write filtered slots ----------
with open(OUTPUT_FILE, "w") as f:
    json.dump(filtered, f, indent=4)

print(f"\nFiltered {len(filtered)} upcoming slots saved to '{OUTPUT_FILE}'.")
