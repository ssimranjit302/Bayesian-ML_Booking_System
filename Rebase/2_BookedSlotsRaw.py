import csv
from datetime import datetime, timezone, timedelta
import re
import unicodedata
from pathlib import Path
# ---------- Functions ----------

# Get London time
utc_time = datetime.now(timezone.utc) + timedelta(hours=1)
london_time = utc_time.strftime("%H:%M")

london_tz = timezone(timedelta(hours=1))
today_date = datetime.now(london_tz).strftime("%Y-%m-%d")


# Subtract time functions for each service
def subtract_1hr(time_str: str) -> str:
    time_obj = datetime.strptime(time_str, "%H:%M")
    new_time = time_obj - timedelta(hours=1, minutes=0)
    return new_time.strftime("%H:%M")
def subtract_1hr45min(time_str: str) -> str:
    time_obj = datetime.strptime(time_str, "%H:%M")
    new_time = time_obj - timedelta(hours=1, minutes=45)
    return new_time.strftime("%H:%M")

def subtract_30min(time_str: str) -> str:
    time_obj = datetime.strptime(time_str, "%H:%M")
    new_time = time_obj - timedelta(minutes=30)
    return new_time.strftime("%H:%M")

# Time difference in minutes
def time_diff_minutes(t1: str, t2: str) -> int:
    fmt = "%H:%M"
    time1 = datetime.strptime(t1, fmt)
    time2 = datetime.strptime(t2, fmt)
    return int((time2 - time1).total_seconds() / 60)

def time_to_minutes(t):
    """Convert HH:MM string to total minutes (for easy comparison)."""
    return int(datetime.strptime(t, "%H:%M").hour) * 60 + int(datetime.strptime(t, "%H:%M").minute)

# Booking algorithms for each service class

def get_bookings_45(start_times, is_weekend, count=0):
    bookings = []
    # Define the end of the day for booking calculation
    end_of_day = "21:00" if not is_weekend else "20:00"

    if count:
        first_element = start_times[0]
        london_start_time = london_time
    else:
        first_element = end_of_day
        london_start_time = "08:00" if is_weekend else "07:00"

    ptr1 = first_element
    if time_diff_minutes(london_start_time, first_element) >= 120:
        for j in range(int(time_diff_minutes(london_start_time, first_element) / 60)):
            temp1 = subtract_1hr(ptr1)
            bookings.append((temp1, ptr1))
            ptr1 = temp1

    if count == 0:
        return bookings

    for i in range(len(start_times) - 1):
        diff = time_diff_minutes(start_times[i], start_times[i + 1])
        # print(f"i={i}, start_times={start_times[i]}, next={start_times[i + 1]}, diff={diff}")
        if diff < 120:
            continue
        elif diff >= 120:
            ptr = start_times[i + 1]
            for j in range(int(diff / 60) - 1):
                temp = subtract_1hr(ptr)
                bookings.append((temp, ptr))
                ptr = temp

    last_element = start_times[-1]
    if time_diff_minutes(last_element, end_of_day) >= 120:
        ptr = end_of_day
        for j in range(int(time_diff_minutes(last_element, end_of_day) / 60) - 1):
            temp = subtract_1hr(ptr)
            bookings.append((temp, ptr))
            ptr = temp

    return bookings

def get_bookings_90(start_times, is_weekend, count=0):
    bookings = []
    end_of_day = "21:00" if not is_weekend else "20:00"

    if count:
        first_element = start_times[0]
        london_start_time = london_time
    else:
        first_element = end_of_day
        london_start_time = "08:00" if is_weekend else "07:00"

    ptr1 = first_element

    if time_diff_minutes(london_start_time, first_element) >= 210:
        for j in range(int(time_diff_minutes(london_start_time, first_element) / 105)):
            temp1 = subtract_1hr45min(ptr1)
            bookings.append((temp1, ptr1))
            ptr1 = temp1
#######
    if count == 0:
        return bookings

    for i in range(len(start_times) - 1):
        diff = time_diff_minutes(start_times[i], start_times[i+1])
        if diff < 210:
            continue
        elif diff >= 210:
            ptr = start_times[i+1]
            for j in range(int(diff / 105) -1):
                temp = subtract_1hr45min(ptr)
                bookings.append((temp, ptr))
                ptr = temp

    last_element = start_times[-1]
    ptr = end_of_day
    if time_diff_minutes(last_element, end_of_day) >= 210:
        for j in range(int(time_diff_minutes(last_element, end_of_day) / 105) - 1):
            temp = subtract_1hr45min(ptr)
            bookings.append((temp, ptr))
            ptr = temp
    return bookings

def get_bookings_cryotherapy(start_times, is_weekend, count=0):

    bookings = []
    end_of_day = "21:00" if not is_weekend else "20:00"

    if count:
        first_element = start_times[0]
        london_start_time = london_time
    else:
        first_element = end_of_day
        london_start_time = "08:00" if is_weekend else "07:00"

    ptr1 = first_element
    if time_diff_minutes(london_start_time, first_element) >= 60:
        for j in range(int(time_diff_minutes(london_start_time, first_element) / 30)):
            temp1 = subtract_30min(ptr1)
            bookings.append((temp1, ptr1))
            ptr1 = temp1

    if count == 0:
        return bookings

    for i in range(len(start_times) - 1):
        diff = time_diff_minutes(start_times[i], start_times[i+1])
        if diff < 60:
            continue
        elif diff >= 60:
            ptr = start_times[i+1]
            for j in range(int(diff / 30) - 1):
                temp = subtract_30min(ptr)
                bookings.append((temp, ptr))
                ptr = temp
    last_element = start_times[-1]
    if time_diff_minutes(last_element, end_of_day) >= 60:
        ptr = end_of_day
        for j in range(int(time_diff_minutes(last_element, end_of_day) / 30) - 1):
            temp = subtract_30min(ptr)
            bookings.append((temp, ptr))
            ptr = temp
    return bookings


# ---------- Master Script ----------

BASE_DIR = Path(__file__).resolve().parent
available_csv = BASE_DIR / "rawAppointments.csv"
booked_csv = BASE_DIR / "booked_slots.csv"


# Read CSV and separate start times by date and service class
slots_by_service = {
    "Infrared Sauna/Ice bath (45 mins)": {},
    "Infrared Sauna/Ice bath (90 mins)": {},
    "Premium Suite (45 mins)": {},
    "Premium Suite (90 mins)": {},
    "Cryotherapy": {}
}


# ---------- Clear previous data ----------
for service in slots_by_service:
    slots_by_service[service] = {}



# ---------- Read CSV and preserve exact start times ----------
def clean_time(t):
    # Normalize Unicode, strip whitespace, remove BOM/zero-width chars
    return unicodedata.normalize("NFKC", t).replace('\u200b','').replace('\ufeff','').strip()

with open(available_csv, newline='') as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        date = row['Date'].strip()
        service = row['Service/Class'].strip()
        start_time = clean_time(row['Start Time'])


        if service in slots_by_service:
            if date not in slots_by_service[service]:
                slots_by_service[service][date] = []
            times_list = slots_by_service[service][date]

            if times_list:
                last_time = times_list[-1]
                if time_to_minutes(start_time) < time_to_minutes(last_time):
                    break

            if start_time in slots_by_service[service][date]:
                break
            slots_by_service[service][date].append(start_time)


# ---------- Print start times per service/date ----------

booked_slots =[]

service_booking_func = {
    "Cryotherapy": get_bookings_cryotherapy,
    "Infrared Sauna/Ice bath (90 mins)": get_bookings_90,
    "Infrared Sauna/Ice bath (45 mins)": get_bookings_45,
    "Premium Suite (45 mins)": get_bookings_45,
    "Premium Suite (90 mins)": get_bookings_90
}

for service, dates in slots_by_service.items():
    booking_func = service_booking_func.get(service, get_bookings_45)  # default to 45 if missing
    if not dates:  # dictionary is empty
        # call function once with empty start_times
        weekday = datetime.strptime(today_date, "%Y-%m-%d").weekday()
        is_weekend = weekday >= 5
        count = 0
        bookings = booking_func([], is_weekend, count)
        for start, end in bookings:
            booked_slots.append((today_date, start, end, service))
        continue  # skip to next service

    # existing nested loop for non-empty dates
    for date, start_times in dates.items():
        weekday = datetime.strptime(date, "%Y-%m-%d").weekday()
        is_weekend = weekday >= 5
        count = len(start_times)

        if service == "Cryotherapy":
            bookings = get_bookings_cryotherapy(start_times, is_weekend, count)
        elif service == "Infrared Sauna/Ice bath (90 mins)":
            bookings = get_bookings_90(start_times, is_weekend, count)
        elif service == "Premium Suite (45 mins)":
            bookings = get_bookings_45(start_times, is_weekend, count)
        elif service == "Premium Suite (90 mins)":
            bookings = get_bookings_90(start_times, is_weekend, count)
        else:
            bookings = get_bookings_45(start_times, is_weekend, count)

        for start, end in bookings:
            booked_slots.append((date, start, end, service))


# Remove duplicates and sort
booked_slots = list(set(booked_slots))
booked_slots.sort(key=lambda x: (datetime.strptime(x[0], "%Y-%m-%d"), datetime.strptime(x[1], "%H:%M")))

# Write CSV
with open(booked_csv, mode='w', newline='') as csvfile:
    fieldnames = ["Date", "Start Time", "End Time", "Service/Class", "Staff/Suite."]
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()
    for row in booked_slots:
        writer.writerow({
            "Date": row[0],
            "Start Time": datetime.strptime(row[1], "%H:%M").strftime("%-I:%M %p") ,
            "End Time": (datetime.strptime(row[2], "%H:%M") - timedelta(minutes=15)).strftime("%I:%M %p"),
            "Service/Class": row[3],
            "Staff/Suite." : row[3].split()[0] + " " + "Suite."
        })

print(f"Booked slots saved to {booked_csv}")
