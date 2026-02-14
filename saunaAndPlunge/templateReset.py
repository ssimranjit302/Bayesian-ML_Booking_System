import json
from datetime import datetime
from zoneinfo import ZoneInfo
from pathlib import Path
# ----------  Get today's date in London ----------
london_tz = ZoneInfo("Europe/London")
london_today = datetime.now(london_tz).strftime("%Y-%m-%d")

# ----------  File paths ----------
BASE_DIR = Path(__file__).resolve().parent

input_file = BASE_DIR / "saunaPlungeTemplate.json"
output_file = BASE_DIR / "Master.json"

# ----------  Read JSON template ----------
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
