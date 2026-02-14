import json
from datetime import datetime, timedelta
import pytz
from pathlib import Path

# ====== CONFIG ======
BASE_DIR = Path(__file__).resolve().parent

INPUT_FILE = BASE_DIR / "updated_schedule.json"
OUTPUT_FILE = BASE_DIR / "filtered_schedule.json"
LONDON_TZ = pytz.timezone("Europe/London")


def load_schedule(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def filter_future_slots(data):
    # Get current London time
    now_london = datetime.now(LONDON_TZ)

    # Round up to the next full hour (e.g. 6:18 → 7:00)
    next_hour = (now_london + timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)
    next_hour_str = next_hour.strftime("%H:%M")
    print(f"Current London time: {now_london.strftime('%H:%M')}, keeping slots from {next_hour_str} onwards")

    # Filter data where Start Time >= next hour
    filtered = []
    for block in data:
        start_time = block.get("Start Time", "")
        try:
            block_time = datetime.strptime(start_time, "%H:%M").time()
            if block_time >= next_hour.time():
                filtered.append(block)
        except ValueError:
            continue  # skip malformed entries

    return filtered


def save_filtered_data(data, output_path):
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)
    print(f"Filtered data saved to {output_path}")


def main():
    # Load data
    data = load_schedule(INPUT_FILE)
    # Filter based on current London time
    filtered_data = filter_future_slots(data)
    # Save result
    save_filtered_data(filtered_data, OUTPUT_FILE)


if __name__ == "__main__":
    main()
