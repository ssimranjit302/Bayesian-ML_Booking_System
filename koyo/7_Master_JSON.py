import json
from pathlib import Path

# ====== CONFIG ======
BASE_DIR = Path(__file__).resolve().parent

MASTER_FILE = BASE_DIR / "Master.json"
FILTERED_FILE = BASE_DIR / "filtered_schedule.json"


def load_json(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(data, file_path):
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)


def update_master(master_data, filtered_data):
    # Create lookup dict for filtered data keyed by tuple of identifying fields
    def make_key(block):
        return tuple((k, v) for k, v in sorted(block.items()) if k != "Booked")

    filtered_lookup = {make_key(block): block["Booked"] for block in filtered_data}

    # Iterate over master blocks and update Booked where matching block exists
    updates = 0
    for block in master_data:
        key = make_key(block)
        if key in filtered_lookup:
            old_value = block.get("Booked", None)
            new_value = filtered_lookup[key]
            if old_value != new_value:
                block["Booked"] = new_value
                updates += 1

    print(f" Updated {updates} matching blocks in Master.json")
    return master_data


def main():
    master_data = load_json(MASTER_FILE)
    filtered_data = load_json(FILTERED_FILE)

    updated_master = update_master(master_data, filtered_data)
    save_json(updated_master, MASTER_FILE)


if __name__ == "__main__":
    main()
