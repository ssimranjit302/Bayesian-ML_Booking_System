import json
from pathlib import Path

# ---------- File paths ----------
BASE_DIR = Path(__file__).resolve().parent

rebase_file = BASE_DIR / "UpcomingHourData.json"
master_file = BASE_DIR / "Master.json"

# ---------- Load both JSON files ----------
with open(rebase_file, "r") as f:
    rebase_data = json.load(f)

with open(master_file, "r") as f:
    master_data = json.load(f)

# ---------- Update Logic ----------
for rebase_entry in rebase_data:
    # Create version of rebase entry without 'Booked'
    rebase_key = {k: v for k, v in rebase_entry.items() if k != "Booked"}

    for master_entry in master_data:
        master_key = {k: v for k, v in master_entry.items() if k != "Booked"}

        # If all fields except 'Booked' match → update
        if rebase_key == master_key:
            master_entry["Booked"] = rebase_entry["Booked"]
            break  # move to next rebase_entry after match

# ---------- Overwrite Master.json ----------
with open(master_file, "w") as f:
    json.dump(master_data, f, indent=4)

print(" Master.json has been successfully updated in place.")
