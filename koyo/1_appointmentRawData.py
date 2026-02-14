from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import csv
import datetime
import time
from pathlib import Path

# Koyo URL
URL = "https://www.koyo-wellness.com/book/"

# Session types and durations
KOYO_SESSION_TYPES = {
    "11": "Contrast Therapy Comprehensive (50 min)",
    "31": "Contrast Therapy Comprehensive (50min) for two",
    "10": "Contrast Therapy Maintenance (25 min)",
    "30": "Contrast Therapy Maintenance (25min) for two",
    "5": "Cryotherapy Session",
    "1038": "Cryotherapy for two",
    "9": "Infrared Sauna Comprehensive (50 min)",
    "33": "Infrared Sauna Comprehensive (50min) for two",
    "7": "Infrared Sauna Maintenance (25 min)",
    "32": "Infrared Sauna Maintenance (25min) for two"
}

KOYO_SESSION_DURATIONS = {
    "11": 60,
    "31": 60,
    "10": 45,
    "30": 45,
    "5": 15,
    "1038": 20,
    "9": 60,
    "33": 60,
    "7": 45,
    "32": 45
}

def generate_batches(start_date, end_date, batch_days=7):
    current = start_date
    while current <= end_date:
        batch_start = current
        batch_end = min(current + datetime.timedelta(days=batch_days-1), end_date)
        yield batch_start, batch_end
        current = batch_end + datetime.timedelta(days=1)

def parse_time(time_str):
    for fmt in ("%I:%M %p", "%H:%M"):
        try:
            return datetime.datetime.strptime(time_str, fmt).time()
        except ValueError:
            continue
    raise ValueError(f"Unrecognized time format: {time_str}")

def add_minutes_to_time(time_obj, minutes):
    full_datetime = datetime.datetime.combine(datetime.date.today(), time_obj)
    new_datetime = full_datetime + datetime.timedelta(minutes=minutes)
    return new_datetime.time()

all_appointments = []

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    context = browser.new_context()
    page = context.new_page()
    page.goto(URL, wait_until="domcontentloaded")

    start = datetime.date.today()
    end = datetime.date.today()  # For testing only one day; adjust as needed
    # end = (
    #     datetime.date(start.year, start.month + 1, 1) - datetime.timedelta(days=1)
    #     if start.month < 12
    #     else datetime.date(start.year, 12, 31)
    # )

    for batch_start, batch_end in generate_batches(start, end):
        START_DATE = batch_start.strftime("%Y-%m-%d")
        END_DATE = batch_end.strftime("%Y-%m-%d")
        print(f"\n📅 Scraping batch {START_DATE} → {END_DATE}")

        for session_value, session_name in KOYO_SESSION_TYPES.items():
            print(f"   💡 Session: {session_name} ({session_value})")

            # Select session type
            page.select_option("select[name='options[session_type_ids]']", session_value)
            page.dispatch_event("select[name='options[session_type_ids]']", "change")
            page.evaluate(f"document.querySelector('#options_start_date').value='{START_DATE}'")
            page.evaluate(f"document.querySelector('#options_end_date').value='{END_DATE}'")
            page.click("a#hc-find-appt")
            time.sleep(5)  # wait 2-5 seconds for content to render
            page.wait_for_selector("div.healcode-trainer", timeout=10000)  # wait up to 10s

            # Wait until appointment-date-blocks exist
            for _ in range(100):
                blocks = page.query_selector_all("div.appointment-date-block")
                if blocks:
                    break
                time.sleep(0.2)
            else:
                print(f"      ️ No appointments found for {session_name}")
                continue

            # Loop through each date block
            for block in blocks:
                html = block.inner_html()
                soup = BeautifulSoup(html, 'html.parser')

                # Appointment date
                date_label = soup.find("h1", class_="healcode-date-label")
                if date_label:
                    appt_date = datetime.datetime.strptime(
                        date_label.text.strip(), "%A %B %d, %Y"
                    ).strftime("%y-%m-%d")  # output like 25-10-08
                else:
                    appt_date = batch_start.strftime("%y-%m-%d")  # fallback


                # Loop through each trainer block
                for trainer_block in soup.select("div.healcode-trainer"):
                    staff_label_tag = trainer_block.select_one("div.trainer-label a")
                    trainer = staff_label_tag.text.strip() if staff_label_tag else None

                    # Loop through each appointment under this trainer
                    for a in trainer_block.select('span.appointment a'):
                        start_time_text = a.text.strip()

                        # Parse & format start time
                        start_time_obj = parse_time(start_time_text)
                        start_time_formatted = start_time_obj.strftime("%H:%M")

                        # Duration → End time
                        duration = KOYO_SESSION_DURATIONS.get(session_value, 0)
                        end_time_obj = add_minutes_to_time(start_time_obj, duration)
                        end_time_formatted = end_time_obj.strftime("%H:%M")

                        item_div = a.find_parent('div', class_='item__details')
                        class_name = (
                            item_div.find('div', 'item__class').text.strip()
                            if item_div and item_div.find('div', 'item__class')
                            else session_name
                        )

                        all_appointments.append({
                            "Date": appt_date,
                            "Start Time": start_time_formatted,
                            "End Time": end_time_formatted,
                            "Service/Class": class_name,
                            "Staff/Centre": trainer
                        })

    browser.close()

# Save CSV
BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "appointmentsRaw.csv"
with open(OUTPUT_DIR, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(
        f,
        fieldnames=[
            "Date", "Start Time", "End Time",
            "Service/Class", "Staff/Centre"
        ]
    )
    writer.writeheader()
    writer.writerows(all_appointments)

print(" Saved appointmentsRaw.csv")
