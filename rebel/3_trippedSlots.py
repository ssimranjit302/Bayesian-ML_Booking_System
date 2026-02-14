import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

# ---------- CONFIG ----------
BASE_DIR = Path(__file__).resolve().parent
input_json = BASE_DIR / "RebelSlotsData.json"
output_json = BASE_DIR / "RebelSlotsData_filtered.json"
# ----------------------------

def filter_future_slots(input_file, output_file):
    # Load JSON data
    with open(input_file, "r") as f:
        data = json.load(f)

    # Get current London time
    now_london = datetime.now(ZoneInfo("Europe/London"))

    filtered = []
    for entry in data:
        try:
            date_str = entry.get("Date", "").strip()
            time_str = entry.get("Start Time", "").strip()

            # Combine and localize to London
            dt_str = f"{date_str} {time_str}"
            dt_obj = datetime.strptime(dt_str, "%d %b %Y %I:%M %p")
            dt_obj = dt_obj.replace(tzinfo=ZoneInfo("Europe/London"))

            # Keep only entries at or after current time
            if dt_obj >= now_london:
                filtered.append(entry)
        except Exception as e:
            print(f"Skipping invalid entry: {entry} ({e})")

    # Save filtered data to new JSON file
    with open(output_file, "w") as f:
        json.dump(filtered, f, indent=4)

    print(f"Filtered data saved as: {output_file}")
    print(f"Kept {len(filtered)} out of {len(data)} entries")

if __name__ == "__main__":
    filter_future_slots(input_json, output_json)
