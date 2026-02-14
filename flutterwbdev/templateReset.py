import json
from datetime import datetime
from zoneinfo import ZoneInfo
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

input1 = BASE_DIR / "templateWeekend.json"
output1 = BASE_DIR / "MasterWeekend.json"
input2 = BASE_DIR / "templateWeekday.json"
output2 = BASE_DIR / "MasterWeekday.json"

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
