import pandas as pd
from datetime import datetime, timedelta, time
from pathlib import Path

import sys, os
if os.getcwd() not in sys.path:
    sys.path.insert(0, os.path.join(os.getcwd(), "venv/lib/python3.12/site-packages"))

# CONFIGURATION

service_capacity = {
    "Infrared Sauna/Ice bath (45 mins)": 1,
    "Infrared Sauna/Ice bath (90 mins)": 1,
    "Premium Suite (45 mins)": 1,
    "Premium Suite (90 mins)": 1,
    "Cryotherapy": 2
}

service_suite = {
    "Infrared Sauna/Ice bath (45 mins)": "Infrared Suite.",
    "Infrared Sauna/Ice bath (90 mins)": "Infrared Suite.",
    "Premium Suite (45 mins)": "Premium Suite.",
    "Premium Suite (90 mins)": "Premium Suite.",
    "Cryotherapy": "Cryotherapy Suite."
}

weekday_hours = (7, 21)  # 7:00 - 21:00
weekend_hours = (8, 20)  # 8:00 - 20:00


# HELPER FUNCTIONS

def parse_time(date_str, time_str):
    """Parse '9:30 AM' with date into datetime"""
    return datetime.strptime(f"{date_str} {time_str.strip().replace('.', '')}", "%Y-%m-%d %I:%M %p")

def generate_hourly_slots(date):
    weekday = date.weekday()  # Monday=0, Sunday=6
    start_hour, end_hour = weekday_hours if weekday < 5 else weekend_hours
    slots = []
    for h in range(start_hour, end_hour):
        start_dt = datetime.combine(date, time(h, 0))
        end_dt = start_dt + timedelta(hours=1)
        slots.append((start_dt, end_dt))
    return slots

def overlaps(booked_start, booked_end, slot_start, slot_end):

    return not (booked_end < slot_start or booked_start >= slot_end)


# MAIN LOGIC
def build_schedule(input_csv, output_csv):
    # Read input CSV
    df = pd.read_csv(input_csv)
    df.columns = [c.strip() for c in df.columns]

    # Clean trailing periods in End Time if any
    df['End Time'] = df['End Time'].astype(str).str.replace(r'\.$', '', regex=True)

    # Collect all unique dates
    dates = sorted(pd.to_datetime(df['Date']).dt.date.unique())

    output_rows = []

    for date in dates:
        slots = generate_hourly_slots(date)

        # For each hourly slot
        for slot_start, slot_end in slots:
            start_str = slot_start.strftime("%I:%M %p")
            end_str = slot_end.strftime("%I:%M %p")

            for service, cap in service_capacity.items():
                row = {
                    "Date": date.strftime("%Y-%m-%d"),
                    "Start Time": start_str,
                    "End Time": end_str,
                    "Service/Class": service,
                    "Staff/Suite.": service_suite[service],
                    "Capacity": cap,
                    "Booked": 0
                }
                output_rows.append(row)

    output_df = pd.DataFrame(output_rows)

    # Now fill in the Booked column based on input slots
    for _, row in df.iterrows():
        date_str = str(row['Date']).strip()
        service = row['Service/Class'].strip()
        try:
            booked_start = parse_time(date_str, row['Start Time'])
            booked_end = parse_time(date_str, row['End Time'])
        except Exception as e:
            continue

        # Iterate over all hourly slots of this date and service
        mask = output_df['Date'].eq(date_str) & output_df['Service/Class'].eq(service)
        for idx, slot_row in output_df[mask].iterrows():
            slot_start = datetime.strptime(f"{date_str} {slot_row['Start Time']}", "%Y-%m-%d %I:%M %p")
            slot_end = datetime.strptime(f"{date_str} {slot_row['End Time']}", "%Y-%m-%d %I:%M %p")

            if overlaps(booked_start, booked_end, slot_start, slot_end):
                new_val = output_df.at[idx, 'Booked'] + 1
                cap = output_df.at[idx, 'Capacity']
                output_df.at[idx, 'Booked'] = min(new_val, cap)  # cap limit

    # Sort neatly
    output_df['Start_dt'] = pd.to_datetime(output_df['Date'] + " " + output_df['Start Time'])
    output_df = output_df.sort_values(['Start_dt', 'Service/Class']).drop(columns='Start_dt')

    # Save to CSV
    output_df.to_csv(output_csv, index=False)
    print(f" Output written to: {output_csv}")

    # Also save as JSON
    output_json = output_csv.with_suffix('.json')  # same filename, .json extension
    output_df.to_json(output_json, orient="records", indent=4)
    print(f" JSON output written to: {output_json}")


# RUN SCRIPT

BASE_DIR = Path(__file__).resolve().parent
INPUT_DIR = BASE_DIR / "booked_slots.csv"
OUTPUT_DIR = BASE_DIR / "RebaseHourlyTrends.csv"

build_schedule(INPUT_DIR, OUTPUT_DIR)
