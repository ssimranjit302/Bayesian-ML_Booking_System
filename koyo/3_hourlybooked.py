import pandas as pd
from datetime import datetime, timedelta
import re
import os
from pathlib import Path


# CONFIGURATIONS

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


# UTILITIES

DATE_FORMAT_TRIES = ["%y-%m-%d", "%d-%m-%y", "%Y-%m-%d", "%d-%m-%Y", "%m-%d-%y", "%m-%d-%Y"]
TIME_FORMAT_TRIES = ["%H:%M", "%I:%M %p"]

def parse_date_flexible(s):
    s = str(s).strip()
    for fmt in DATE_FORMAT_TRIES:
        try:
            dt = datetime.strptime(s, fmt)
            return dt.date(), fmt
        except:
            continue
    raise ValueError(f"Unrecognized date format: '{s}'")

def parse_time_flexible(s):
    s = str(s).strip()
    for fmt in TIME_FORMAT_TRIES:
        try:
            t = datetime.strptime(s, fmt).time()
            return t, fmt
        except:
            continue
    raise ValueError(f"Unrecognized time format: '{s}'")

def compose_datetime_from_parts(date_obj, time_obj):
    return datetime.combine(date_obj, time_obj)

def normalize_text(s):
    s = str(s or "").strip()
    s = re.sub(r'\s+', ' ', s)
    return s.strip()

def simplify(s):
    s = normalize_text(s).lower()
    s = re.sub(r'[^a-z0-9\s]', '', s)
    s = re.sub(r'\s+', ' ', s).strip()
    return s

def map_input_room_to_canonical(service, input_room):
    if service not in service_rooms or not input_room:
        return None
    candidates = service_rooms[service]
    inp = normalize_text(input_room)
    inp_simple = simplify(inp)

    # 1) Exact match
    for c in candidates:
        if inp.lower() == c.lower():
            return c
    # 2) Simplified match
    for c in candidates:
        if inp_simple == simplify(c):
            return c
    # 3) Digit match
    digit_match = re.search(r'\b([12])\b', inp)
    if digit_match:
        d = digit_match.group(1)
        for c in candidates:
            if d in c:
                return c
    # 4) Cryotherapy
    if "cryotherapy" in inp_simple:
        for c in candidates:
            if "cryotherapy" in simplify(c):
                return c
    # 5) Token overlap
    inp_tokens = set(inp_simple.split())
    best = None
    best_score = 0
    for c in candidates:
        cand_tokens = set(simplify(c).split())
        score = len(inp_tokens & cand_tokens)
        if score > best_score:
            best_score = score
            best = c
    if best_score > 0:
        return best
    # 6) Single candidate fallback
    if len(candidates) == 1:
        return candidates[0]
    return None


# SLOTS

def generate_hourly_slots_from_dateobj(date_obj):
    weekday = date_obj.weekday()
    start_hour, end_hour = (7, 19) if weekday < 5 else (9, 17)
    slots = []
    for h in range(start_hour, end_hour):
        start = datetime.combine(date_obj, datetime.strptime(f"{h:02d}:00", "%H:%M").time())
        end = start + timedelta(hours=1)
        slots.append((start, end))
    return slots


# MAIN FUNCTION

def generate_output_csv(input_csv, output_csv):
    raw = pd.read_csv(input_csv, dtype=str).fillna("")
    raw.columns = [c.strip() for c in raw.columns]
    required = {"Date", "Start Time", "End Time", "Service/Class", "Staff/Centre"}
    if not required.issubset(set(raw.columns)):
        raise ValueError(f"Input CSV must contain columns: {required}")

    parsed_rows = []
    warnings = []
    date_canonical_to_original = {}
    detected_time_format = None


    # Parse input bookings

    for i, row in raw.iterrows():
        row_index = i + 1
        date_str = str(row["Date"]).strip()
        start_str = str(row["Start Time"]).strip()
        end_str = str(row["End Time"]).strip()
        service = normalize_text(row.get("Service/Class", ""))
        input_room_raw = row.get("Staff/Centre", "")
        input_room = normalize_text(input_room_raw)

        try:
            date_obj, date_fmt = parse_date_flexible(date_str)
            start_time_obj, tf1 = parse_time_flexible(start_str)
            end_time_obj, tf2 = parse_time_flexible(end_str)
        except ValueError as e:
            warnings.append(f"Row {row_index}: {e}")
            continue

        if detected_time_format is None:
            detected_time_format = tf1

        canonical_date_key = date_obj.strftime("%Y-%m-%d")
        date_canonical_to_original.setdefault(canonical_date_key, date_str)

        start_dt = compose_datetime_from_parts(date_obj, start_time_obj)
        end_dt = compose_datetime_from_parts(date_obj, end_time_obj)

        canonical_room = map_input_room_to_canonical(service, input_room)
        if canonical_room is None:
            warnings.append(f"Row {row_index}: could not map room '{input_room_raw}' for service '{service}'")
            continue

        parsed_rows.append({
            "canonical_date": canonical_date_key,
            "start_dt": start_dt,
            "end_dt": end_dt,
            "service": service,
            "canonical_room": canonical_room
        })

    if warnings:
        print("==== WARNINGS ====")
        for w in warnings:
            print(w)
        print("=================")

    # -----------------------------
    # Track per-room per-slot bookings
    # -----------------------------
    room_slot_bookings = {}  # key: (date, service, room, slot_start)
    unique_dates = sorted({r["canonical_date"] for r in parsed_rows})

    for r in parsed_rows:
        date_key = r["canonical_date"]
        service = r["service"]
        room = r["canonical_room"]
        start_dt = r["start_dt"]
        end_dt = r["end_dt"]

        increment_value = 2 if "for two" in service.lower() else 1
        date_obj = datetime.strptime(date_key, "%Y-%m-%d").date()
        slots = generate_hourly_slots_from_dateobj(date_obj)

        for slot_start, slot_end in slots:
            if slot_start < end_dt and start_dt < slot_end:
                key = (date_key, service, room, slot_start)
                cap = service_capacity.get(service, 1)
                room_slot_bookings[key] = min(room_slot_bookings.get(key, 0) + increment_value, cap)


    # Create template CSV (all Booked=0) based on actual bookings

    template_rows = []
    for key in room_slot_bookings.keys():
        date_key, service, room, slot_start = key
        original_date_str = date_canonical_to_original.get(date_key, date_key)
        cap = service_capacity.get(service, 1)
        template_rows.append({
            "Date": original_date_str,
            "Start Time": slot_start.strftime(detected_time_format),
            "End Time": (slot_start + timedelta(hours=1)).strftime(detected_time_format),
            "Service/Class": service,
            "Staff/Centre": room,
            "Capacity": cap,
            "Booked": 0
        })

    out_df = pd.DataFrame(template_rows)


    # Update booked counts exactly matching room & slot

    for key, count in room_slot_bookings.items():
        date_key, service, room, slot_start = key
        mask = (
                (out_df["Date"] == date_canonical_to_original[date_key]) &
                (out_df["Service/Class"] == service) &
                (out_df["Staff/Centre"] == room) &
                (out_df["Start Time"] == slot_start.strftime(detected_time_format))
        )
        out_df.loc[mask, "Booked"] = count

    # -----------------------------
    out_df.to_csv(output_csv, index=False)
    print(f" Output saved to: {output_csv}")


# RUN
BASE_DIR = Path(__file__).resolve().parent
input_csv_path = BASE_DIR / "booked_slots_master.csv"
output_csv_path = BASE_DIR / "tempHourlySlots.csv"
generate_output_csv(input_csv_path, output_csv_path)


json_path = os.path.splitext(output_csv_path)[0] + ".json"


# CONVERT CSV TO JSON

df = pd.read_csv(output_csv_path)
df.to_json(json_path, orient="records", indent=4)

print(f" JSON file saved to: {json_path}")
