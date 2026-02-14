import json
from pathlib import Path

# ---------- CONFIG ----------
BASE_DIR = Path(__file__).resolve().parent
master_json = BASE_DIR / "Master.json"
filtered_json = BASE_DIR / "RebelSlotsData_filtered.json"
# ----------------------------

def update_master(master_file, filtered_file):
    # Load both JSON files
    with open(master_file, "r") as f:
        master_data = json.load(f)
    with open(filtered_file, "r") as f:
        filtered_data = json.load(f)

    # Define keys used for matching (ignore Booked and Slots left)
    match_keys = ["Date", "Start Time", "End Time", "Location/Club", "Concept Name", "Capacity"]

    # Convert filtered data into a lookup dictionary for fast access
    filtered_lookup = {
        tuple(entry[k] for k in match_keys): entry for entry in filtered_data
    }

    updated_count = 0

    # Update Master.json entries where a match is found
    for master_entry in master_data:
        master_key = tuple(master_entry.get(k) for k in match_keys)
        if master_key in filtered_lookup:
            filtered_entry = filtered_lookup[master_key]

            # Update Booked and Slots left
            booked = filtered_entry.get("Booked")
            capacity = master_entry.get("Capacity", 0)

            try:
                booked = int(booked)
                capacity = int(capacity)
                slots_left = capacity - booked
            except:
                booked = filtered_entry.get("Booked")
                slots_left = master_entry.get("Slots left")

            master_entry["Booked"] = booked
            master_entry["Slots left"] = slots_left
            updated_count += 1

    # Save the updated Master.json file (in place)
    with open(master_file, "w") as f:
        json.dump(master_data, f, indent=4)

    print(f"Updated {updated_count} matching records in {master_file.name}")

if __name__ == "__main__":
    update_master(master_json, filtered_json)
