import requests
import pandas as pd
from datetime import datetime, timedelta
import pytz
import calendar
from pathlib import Path

# --- CONFIG ---
BOARD_ID = 79524
BASE_URL = f"https://api.momence.com/plugin/appointment-boards/{BOARD_ID}/available-times"

# Define all services to scrape
SERVICES = [
    {"id": 110021, "name": "Contrast Experience (30 min)", "duration": 30},
    {"id": 117450, "name": "Contrast Experience (60 min)", "duration": 60},
]

# --- Date range: only today (00:00:00 → 23:59:59 UTC) ---
today_utc = datetime.utcnow()
start_of_day = datetime(today_utc.year, today_utc.month, today_utc.day, 0, 0, 0)
end_of_day = datetime(today_utc.year, today_utc.month, today_utc.day, 23, 59, 59)

from_time = start_of_day.isoformat() + "Z"
to_time = end_of_day.isoformat() + "Z"


headers = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json"
}

records = []

# --- Loop over each service ---
for svc in SERVICES:
    params = {
        "from": from_time,
        "to": to_time,
        "attendeeCount": 1,
        "serviceId": svc["id"],
        "durationInMinutes": svc["duration"],
        "includeUnavailable": "false"
    }

    print(f"Fetching data for {svc['name']} ...")

    resp = requests.get(BASE_URL, params=params, headers=headers)
    resp.raise_for_status()
    data = resp.json()

    # --- Parse & flatten ---
    for day_slots in data:
        for slot in day_slots:
            time_utc = slot["value"]
            is_taken = slot["isTaken"]
            occ = slot["occupiedByExistingReservations"]
            num_att = occ[0]["numberOfAttendees"] if occ else 0

            # If taken → assume full (8 attendees)
            if is_taken:
                num_att = 8

            records.append({
                "slot_time_utc": time_utc,
                "isTaken": is_taken,
                "numberOfAttendees": num_att,
                "maxCapacity": 8,
                "Service": svc["name"],
                "duration": svc["duration"]
            })

# --- Convert to DataFrame ---
df = pd.DataFrame(records)

# --- Convert UTC → UK time (BST handled automatically) ---
uk_tz = pytz.timezone("Europe/London")
df["slot_time_uk"] = pd.to_datetime(df["slot_time_utc"], utc=True).dt.tz_convert(uk_tz)

# --- Extract formatted Date, Start, End Time ---
df["Date"] = df["slot_time_uk"].dt.strftime("%Y-%m-%d")
df["Start Time"] = df["slot_time_uk"].dt.strftime("%I:%M %p")
df["End Time"] = (df["slot_time_uk"] + pd.to_timedelta(df["duration"], unit="m")).dt.strftime("%I:%M %p")

# --- Select and reorder columns ---
final_df = df[["Date", "Start Time", "End Time", "Service", "numberOfAttendees", "maxCapacity"]]
final_df.rename(columns={
    "numberOfAttendees": "Booked",
    "maxCapacity": "Max Capacity"
}, inplace=True)

# --- Proper sorting (by date + actual time) ---
temp_dt = pd.to_datetime(final_df["Date"] + " " + final_df["Start Time"], format="%Y-%m-%d %I:%M %p")
final_df = final_df.loc[temp_dt.argsort()].reset_index(drop=True)

# --- Save ---
BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "sauna_slots.csv"
JSON_PATH = BASE_DIR / "sauna_slots_today.json"

final_df.to_csv(OUTPUT_DIR, index=False)
final_df.to_json(JSON_PATH, orient="records", indent=4)

print(final_df.head(10))
print(f"\n Saved {len(final_df)} slots for all services to:")
print(f"   • CSV:  {OUTPUT_DIR}")
print(f"   • JSON: {JSON_PATH}")
