import csv
import pandas as pd
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

# Get London time
london_time = datetime.now(ZoneInfo("Europe/London")).strftime("%H:%M")
london_tz = ZoneInfo("Europe/London")
today_date = datetime.now(london_tz).strftime("%Y-%m-%d")

# ---------- Utility Functions ----------
def time_diff_minutes(t1: str, t2: str) -> int:
    fmt = "%H:%M"
    time1 = datetime.strptime(t1, fmt)
    time2 = datetime.strptime(t2, fmt)
    return int((time2 - time1).total_seconds() / 60)



# ---------- Code 1: 1-hour Slot Generator ----------


def subtract_1hr(time_str: str) -> str:
    time_obj = datetime.strptime(time_str, "%H:%M")
    new_time = time_obj - timedelta(hours=1)
    return new_time.strftime("%H:%M")

def generate_1hr_slots(start_times, is_weekend):
    bookings = []
    end_of_day = "19:00" if not is_weekend else "17:00"

    first_element = start_times[0]
    london_start_time = london_time

    ptr1 = first_element
    if time_diff_minutes(london_start_time, first_element) >= 120:
        for j in range(int(time_diff_minutes(london_start_time, first_element) / 60)):
            temp1 = subtract_1hr(ptr1)
            bookings.append((temp1, ptr1))
            ptr1 = temp1



    for i in range(len(start_times) - 1):
        diff = time_diff_minutes(start_times[i], start_times[i + 1])
        if diff < 60:
            continue
        elif diff > 60:
            ptr = start_times[i + 1]
            for _ in range(int(start_times[i + 1][:2]) - int(start_times[i][:2]) - 1):
                temp = subtract_1hr(ptr)
                bookings.append((temp, ptr))
                ptr = temp

    last_element = start_times[-1]
    if time_diff_minutes(last_element, end_of_day) > 60:
        ptr = end_of_day
        for _ in range(int(end_of_day[:2]) - int(last_element[:2]) - 1):
            temp = subtract_1hr(ptr)
            bookings.append((temp, ptr))
            ptr = temp
    return bookings



# ---------- Code 2: 45-minute Slot Generator ----------


def subtract_45min(time_str: str) -> str:
    time_obj = datetime.strptime(time_str, "%H:%M")
    new_time = time_obj - timedelta(minutes=45)
    return new_time.strftime("%H:%M")

def generate_45min_slots(start_times, is_weekend):
    bookings = []
    end_of_day = "19:00" if not is_weekend else "17:00"

    first_element = start_times[0]
    london_start_time = london_time

    ptr1 = first_element
    if time_diff_minutes(london_start_time, first_element) >= 90:
        for j in range(int(time_diff_minutes(london_start_time, first_element) / 45)):
            temp1 = subtract_45min(ptr1)
            bookings.append((temp1, ptr1))
            ptr1 = temp1


    for i in range(len(start_times) - 1):
        diff = time_diff_minutes(start_times[i], start_times[i + 1])
        if diff < 90:
            continue
        elif diff >= 90:
            ptr = start_times[i + 1]
            for _ in range(int(diff / 45) - 1):
                temp = subtract_45min(ptr)
                bookings.append((temp, ptr))
                ptr = temp

    last_element = start_times[-1]
    if time_diff_minutes(last_element, end_of_day) >= 90:
        ptr = end_of_day
        for _ in range(int(time_diff_minutes(last_element, end_of_day) / 45) - 1):
            temp = subtract_45min(ptr)
            bookings.append((temp, ptr))
            ptr = temp
    return bookings


# ---------- Code 3: 15-minute Slot Generator ----------


def subtract_15min(time_str: str) -> str:
    time_obj = datetime.strptime(time_str, "%H:%M")
    new_time = time_obj - timedelta(minutes=15)
    return new_time.strftime("%H:%M")

def generate_15min_slots(start_times, is_weekend):
    bookings = []
    end_of_day = "17:00"  # both weekday and weekend same

    first_element = start_times[0]
    london_start_time = london_time

    ptr1 = first_element
    if time_diff_minutes(london_start_time, first_element) >= 30:
        for j in range(int(time_diff_minutes(london_start_time, first_element) / 15)):
            temp1 = subtract_15min(ptr1)
            bookings.append((temp1, ptr1))
            ptr1 = temp1

    for i in range(len(start_times) - 1):
        diff = time_diff_minutes(start_times[i], start_times[i + 1])
        if diff < 30:
            continue
        elif diff >= 30:
            ptr = start_times[i + 1]
            for _ in range(int(diff / 15) - 1):
                temp = subtract_15min(ptr)
                bookings.append((temp, ptr))
                ptr = temp

    last_element = start_times[-1]
    if time_diff_minutes(last_element, end_of_day) >= 30:
        ptr = end_of_day
        for _ in range(int(time_diff_minutes(last_element, end_of_day) / 15) - 1):
            temp = subtract_15min(ptr)
            bookings.append((temp, ptr))
            ptr = temp
    return bookings



# ---------- Service/Class → Code Mapping ----------


service_to_code = {
    "Contrast Therapy Comprehensive (50 min)": 1,
    "Contrast Therapy Comprehensive (50min) for two": 1,
    "Infrared Sauna Comprehensive (50 min)": 1,
    "Infrared Sauna Comprehensive (50min) for two": 1,

    "Contrast Therapy Maintenance (25 min)": 2,
    "Contrast Therapy Maintenance (25min) for two": 2,
    "Infrared Sauna Maintenance (25 min)": 2,
    "Infrared Sauna Maintenance (25min) for two": 2,

    "Cryotherapy Session": 3,
    "Cryotherapy for two": 3,
}


# ---------- Main Booking Generation ----------
BASE_DIR = Path(__file__).resolve().parent
input_csv = BASE_DIR / "appointmentsRaw.csv"
output_csv = BASE_DIR / "booked_slots_master.csv"

slots = {}
services = {}

# Group by (date, room)
with open(input_csv, newline="") as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        date = row["Date"].strip()
        room = row["Staff/Centre"].strip()
        service = row["Service/Class"].strip()
        start_time = row["Start Time"].strip()

        key = (date, room, service)
        if key not in slots:
            slots[key] = []
        slots[key].append(start_time)

# ---------- Generate Booked Slots ----------


booked_rows = []

for (date, room, service), start_times in slots.items():
    start_times = sorted(start_times, key=lambda t: datetime.strptime(t, "%H:%M"))
    dt_obj = datetime.strptime(date, "%y-%m-%d")
    is_weekend = dt_obj.weekday() >= 5
    code = service_to_code.get(service)

    if code == 1:
        bookings = generate_1hr_slots(start_times, is_weekend)
    elif code == 2:
        bookings = generate_45min_slots(start_times, is_weekend)
    elif code == 3:
        bookings = generate_15min_slots(start_times, is_weekend)
    else:
        print(f"️ Unknown service skipped: {service}")
        continue

    for start, end in bookings:
        booked_rows.append({
            "Date": date,
            "Start Time": start,
            "End Time": end,
            "Service/Class": service,
            "Staff/Centre": room
        })


# ---------- Sorting + Output ----------


df = pd.DataFrame(booked_rows)
df["Start Time"] = pd.to_datetime(df["Start Time"], format="%H:%M").dt.time
df = df.sort_values(by=["Date", "Start Time", "Staff/Centre"])
df["Start Time"] = df["Start Time"].apply(lambda t: t.strftime("%H:%M"))
df.to_csv(output_csv, index=False)

print(" Master booked slots CSV generated:", output_csv)
