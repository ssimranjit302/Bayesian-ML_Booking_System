import pandas as pd
from datetime import datetime, timedelta
import re
import os
from pathlib import Path


# CONFIG (use your exact maps)

service_capacity = {
    "Contrast Therapy Comprehensive (50 min)": 1,
    "Contrast Therapy Comprehensive (50min) for two": 2,
    "Contrast Therapy Maintenance (25 min)": 2,
    "Contrast Therapy Maintenance (25min) for two": 4,
    "Cryotherapy Session": 4,
    "Cryotherapy for two": 8,
    "Infrared Sauna Comprehensive (50 min)": 1,
    "Infrared Sauna Comprehensive (50min) for two": 2,
    "Infrared Sauna Maintenance (25 min)": 2,
    "Infrared Sauna Maintenance (25min) for two": 4,
}

service_rooms = {
    "Contrast Therapy Comprehensive (50 min)": ["Contrast Room 1", "Contrast Room 2"],
    "Contrast Therapy Comprehensive (50min) for two": ["Contrast Room 1", "Contrast Room 2"],
    "Contrast Therapy Maintenance (25 min)": ["Contrast Room 1", "Contrast Room 2"],
    "Contrast Therapy Maintenance (25min) for two": ["Contrast Room 1", "Contrast Room 2"],
    "Cryotherapy Session": ["Cryotherapy Room"],
    "Cryotherapy for two": ["Cryotherapy Room"],
    "Infrared Sauna Comprehensive (50 min)": ["Contrast Room 1", "Contrast Room 2"],
    "Infrared Sauna Comprehensive (50min) for two": ["Contrast Room 1", "Contrast Room 2"],
    "Infrared Sauna Maintenance (25 min)": ["Contrast Room 1", "Contrast Room 2"],
    "Infrared Sauna Maintenance (25min) for two": ["Contrast Room 1", "Contrast Room 2"],
}


# Date/time parsing helpers

DATE_FORMAT_TRIES = [
    "%y-%m-%d", "%d-%m-%y", "%Y-%m-%d", "%d-%m-%Y", "%m-%d-%y", "%m-%d-%Y"
]
TIME_FORMAT_TRIES = ["%H:%M", "%I:%M %p"]

def parse_date_flexible(s):
    s = str(s).strip()
    for fmt in DATE_FORMAT_TRIES:
        try:
            dt = datetime.strptime(s, fmt)
            return dt.date(), fmt
        except Exception:
            continue
    raise ValueError(f"Unrecognized date format: '{s}'")

def parse_time_format_from_examples(example_times):
    for t in example_times:
        if not t or str(t).strip() == "":
            continue
        s = str(t).strip()
        for fmt in TIME_FORMAT_TRIES:
            try:
                datetime.strptime(s, fmt)
                return fmt
            except Exception:
                continue
    return "%H:%M"


# Hourly slot generator

def generate_hourly_slots_for_date(date_obj):
    if date_obj.weekday() < 5:
        start_hour, end_hour = 7, 19
    else:
        start_hour, end_hour = 9, 17
    slots = []
    for h in range(start_hour, end_hour):
        start = datetime.combine(date_obj, datetime.strptime(f"{h:02d}:00", "%H:%M").time())
        end = start + timedelta(hours=1)
        slots.append((start, end))
    return slots


# Build template CSV and JSON

def build_template_from_input_dates(input_csv_path, output_csv_path):
    df_in = pd.read_csv(input_csv_path, dtype=str).fillna("")
    df_in.columns = [c.strip() for c in df_in.columns]

    if "Date" not in df_in.columns:
        raise ValueError("Input CSV must contain a 'Date' column.")

    canonical_to_original = {}
    canonical_dates = set()
    example_time_values = []

    for i, row in df_in.iterrows():
        raw_date = str(row.get("Date", "")).strip()
        if raw_date == "":
            continue
        try:
            date_obj, used_fmt = parse_date_flexible(raw_date)
        except ValueError:
            continue
        canonical = date_obj.strftime("%Y-%m-%d")
        canonical_dates.add(canonical)
        canonical_to_original.setdefault(canonical, raw_date)
        if "Start Time" in df_in.columns:
            example_time_values.append(row.get("Start Time", ""))
        if "End Time" in df_in.columns:
            example_time_values.append(row.get("End Time", ""))

    if not canonical_dates:
        raise ValueError("No valid dates found in input CSV.")

    detected_time_format = parse_time_format_from_examples(example_time_values)

    # ---- Build template ----
    template_rows = []
    for canonical in sorted(canonical_dates):
        date_obj = datetime.strptime(canonical, "%Y-%m-%d").date()
        original_date_str = canonical_to_original.get(canonical, canonical)
        slots = generate_hourly_slots_for_date(date_obj)
        for slot_start, slot_end in slots:
            start_out = slot_start.strftime(detected_time_format)
            end_out = slot_end.strftime(detected_time_format)
            for service, rooms in service_rooms.items():
                cap = service_capacity.get(service, 1)
                for room in rooms:
                    template_rows.append({
                        "Date": original_date_str,
                        "Start Time": start_out,
                        "End Time": end_out,
                        "Service/Class": service,
                        "Staff/Centre": room,
                        "Capacity": cap,
                        "Booked": 0
                    })

    out_df = pd.DataFrame(template_rows, columns=[
        "Date", "Start Time", "End Time", "Service/Class", "Staff/Centre", "Capacity", "Booked"
    ])

    # ---- Save CSV ----
    out_df.to_csv(output_csv_path, index=False)
    print(f" Template CSV written to: {output_csv_path}")

    # ---- Save JSON ----
    json_output_path = os.path.splitext(output_csv_path)[0] + ".json"
    out_df.to_json(json_output_path, orient="records", indent=4)
    print(f" Template JSON written to: {json_output_path}")

    print(f" Dates included: {sorted(canonical_dates)}")
    print(f" Time format used for slots: {detected_time_format}")

# RUN

if __name__ == "__main__":
    BASE_DIR = Path(__file__).resolve().parent
    input_csv_path = BASE_DIR / "booked_slots_master.csv"
    output_csv_path = BASE_DIR / "template_schedule.csv"
    build_template_from_input_dates(input_csv_path, output_csv_path)

json_path = os.path.splitext(output_csv_path)[0] + ".json"


# CONVERT CSV TO JSON

df = pd.read_csv(output_csv_path)
df.to_json(json_path, orient="records", indent=4)

print(f" JSON file saved to: {json_path}")
