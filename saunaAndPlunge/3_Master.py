import json
from pathlib import Path

# ---------- CONFIG ----------
BASE_DIR = Path(__file__).resolve().parent

MASTER_FILE = BASE_DIR / "Master.json"
FILTERED_FILE = BASE_DIR / "sauna_slots_filtered.json"

# ---------- Load both JSON files ----------
with open(MASTER_FILE, "r") as f:
    master_data = json.load(f)

with open(FILTERED_FILE, "r") as f:
    filtered_data = json.load(f)

# ---------- Build a lookup from filtered data ----------
# Use a tuple of identifying fields as a unique key
filtered_lookup = {
    (
        slot["Date"],
        slot["Start Time"],
        slot["End Time"],
        slot["Service"],
        slot["Max Capacity"],
    ): slot["Booked"]
    for slot in filtered_data
}

# ---------- Update the Master data ----------
updated_count = 0

for m_slot in master_data:
    key = (
        m_slot["Date"],
        m_slot["Start Time"],
        m_slot["End Time"],
        m_slot["Service"],
        m_slot["Max Capacity"],
    )

    if key in filtered_lookup:
        m_slot["Booked"] = filtered_lookup[key]
        updated_count += 1

# ---------- Save changes back to Master.json (in place) ----------
with open(MASTER_FILE, "w") as f:
    json.dump(master_data, f, indent=4)

print(f"Updated {updated_count} matching slots in '{MASTER_FILE}'.")
