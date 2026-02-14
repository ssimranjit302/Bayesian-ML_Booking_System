from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import csv
import datetime
import time
from datetime import datetime as dt
from pathlib import Path

URL = "https://www.rebaserecovery.com/appointments"

SESSION_TYPES = {
    "18": "Infrared Sauna/Ice bath (45 mins)",
    "19": "Infrared Sauna/Ice bath (90 mins)",
    "13": "Premium Suite (45 mins)",
    "15": "Premium Suite (90 mins)",
    "5": "Cryotherapy"
}

SESSION_DURATIONS = {
    "18": 60,
    "19": 105,
    "13": 60,
    "15": 105,
    "5": 30
}

def generate_batches(start_date, end_date, batch_days=7):
    current = start_date
    while current <= end_date:
        batch_start = current
        batch_end = min(current + datetime.timedelta(days=batch_days-1), end_date)
        yield batch_start, batch_end
        current = batch_end + datetime.timedelta(days=1)

def parse_time(time_str):
    time_str = time_str.strip()
    try:
        # Try parsing with AM/PM
        return datetime.datetime.strptime(time_str, "%I:%M %p").time()
    except ValueError:
        # Fall back to 24-hour format if AM/PM is missing
        try:
            return datetime.datetime.strptime(time_str, "%H:%M").time()
        except ValueError:
            print(f"Skipping unrecognized time format: {time_str}")
            return None


def add_minutes_to_time(time_obj, minutes):
    full_datetime = datetime.datetime.combine(datetime.date.today(), time_obj)
    new_datetime = full_datetime + datetime.timedelta(minutes=minutes)
    return new_datetime.time()

all_appointments = []

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
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

        for session_value, session_name in SESSION_TYPES.items():
            print(f"   💡 Session: {session_name} ({session_value})")

            page.select_option("select[name='options[session_type_ids]']", session_value)
            page.dispatch_event("select[name='options[session_type_ids]']", "change")
            page.evaluate(f"document.querySelector('#options_start_date').value='{START_DATE}'")
            page.evaluate(f"document.querySelector('#options_end_date').value='{END_DATE}'")
            page.click("a#hc-find-appt")
            time.sleep(5)

            # Wait until appointment-date-blocks exist
            for _ in range(100):
                blocks = page.query_selector_all("div.appointment-date-block")
                if blocks:
                    break
                time.sleep(0.2)
            else:
                print(f"      ⚠️ No appointments found for {session_name}")
                continue

            # Loop through each date block
            for block in blocks:
                html = block.inner_html()
                soup = BeautifulSoup(html, 'html.parser')

                date_label = soup.find("h1", class_="healcode-date-label")
                if date_label:
                    appt_date = datetime.datetime.strptime(date_label.text.strip(), "%A %B %d, %Y").strftime("%Y-%m-%d")
                else:
                    appt_date = batch_start.strftime("%Y-%m-%d")  # fallback

                for a in soup.select('span.appointment a'):
                    start_time_text = a.text.strip()
                    start_time_obj = parse_time(start_time_text)
                    if not start_time_obj:
                        continue
                    start_time_text = start_time_obj.strftime("%H:%M")
                    duration = SESSION_DURATIONS.get(session_value, 0)
                    end_time_obj = add_minutes_to_time(start_time_obj, duration)
                    end_time_text = dt.strptime(end_time_obj.strftime("%I:%M %p"), "%I:%M %p").strftime("%H:%M")

                    item_div = a.find_parent('div', class_='item__details')
                    class_name = item_div.find('div', 'item__class').text.strip() if item_div and item_div.find('div', 'item__class') else session_name
                    trainer = session_name.split()[0] + " " + "Suite."


                    all_appointments.append({
                        "Date": appt_date,
                        "Start Time": start_time_text,
                        "End Time": end_time_text,
                        "Service/Class": class_name,
                        "Staff/Suite.": trainer,
                    })

    browser.close()

# Save CSV
BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "rawAppointments.csv"
with open(OUTPUT_DIR, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=["Date", "Start Time", "End Time", "Service/Class", "Staff/Suite."])
    writer.writeheader()
    writer.writerows(all_appointments)

print(" Saved rawAppointments.csv")

