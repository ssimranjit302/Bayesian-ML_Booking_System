import json
from datetime import datetime
from zoneinfo import ZoneInfo
from pathlib import Path
# ---------- Step 1: Get today's date in London ----------
london_tz = ZoneInfo("Europe/London")
london_today = datetime.now(london_tz).strftime("%y-%m-%d")

# ---------- Step 2: File paths ----------
BASE_DIR = Path(__file__).resolve().parent

input_file = BASE_DIR / "KoyoTemplate.json"
output_file = BASE_DIR / "Master.json"

# ---------- Step 3: Read JSON template ----------
with open(input_file, "r", encoding="utf-8") as f:
    data = json.load(f)

# ---------- Step 4: Update all 'Date' fields ----------
for entry in data:
    if "Date" in entry:
        entry["Date"] = london_today

# ---------- Step 5: Save updated JSON ----------
with open(output_file, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=4, ensure_ascii=False)

print(f" Master.json created successfully with updated date: {london_today}")
