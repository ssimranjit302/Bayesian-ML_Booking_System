import asyncio
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
import datetime
from datetime import datetime as dt
import re
import csv
import time
from pathlib import Path
from zoneinfo import ZoneInfo


async def main():
    base_url = "https://www.1rebel.com/en-gb/reserve?concepts=5910&minDate="

    today = dt.now(ZoneInfo("Europe/London")).date()
    last_day = dt.now(ZoneInfo("Europe/London")).date()  # For testing only one day; adjust as needed

    # last_day = (
    #     datetime.date(today.year, today.month + 1, 1) - datetime.timedelta(days=1)
    #     if today.month < 12
    #     else datetime.date(today.year, 12, 31)
    # )

    BASE_DIR = Path(__file__).resolve().parent
    csv_file = BASE_DIR / "RebelSlots.csv"
    csv_columns = ["date", "start_time", "concept", "club", "trainer", "status",
                   "new_page_class", "new_page_time", "new_page_duration",
                   "new_page_trainer", "capacity", "booked"]
    all_data = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=200)
        context = await browser.new_context()
        page = await context.new_page()

        current_day = today
        logged_in = False

        while current_day <= last_day:
            date_str = current_day.strftime("%Y-%m-%d")
            print(f"\n📅 Processing date: {date_str}")

            # Retry navigation
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    await page.goto(base_url + date_str, wait_until="domcontentloaded", timeout=60000)
                    await page.wait_for_selector('button:has-text("FIND CLASS")', timeout=15000)
                    print(f" Loaded schedule page for {date_str}")
                    break
                except Exception as e:
                    print(f" Attempt {attempt + 1} failed for {date_str}: {e}")
                    if attempt == max_retries - 1:
                        print(f" Skipping {date_str} after {max_retries} failed attempts.")
                        current_day += datetime.timedelta(days=1)
                        continue
                    await asyncio.sleep(5)

            await page.wait_for_timeout(4000)
            await page.locator('button:has-text("FIND CLASS")').click()
            await page.wait_for_timeout(3000)

            # Click correct day button
            day_buttons = page.locator('button[aria-label="day selector button"]')
            count = await day_buttons.count()
            found = False
            for i in range(count):
                text = (await day_buttons.nth(i).inner_text()).replace('\n', ' ').strip()
                match = re.search(r'\b(\d{1,2})\b', text)
                if match and int(match.group(1)) == current_day.day:
                    await day_buttons.nth(i).click()
                    found = True
                    print(f"🗓️ Clicked day button: {text}")
                    break

            if not found:
                print(f" Could not find button for {current_day}")
                current_day += datetime.timedelta(days=1)
                continue

            await page.wait_for_timeout(5000)

            # Parse the day's cards
            container = page.locator(
                "body > div.py-\\[--item-to-item-gap\\].\\[--item-to-item-gap\\:4rem\\].lg\\:\\[--item-to-item-gap\\:5rem\\] > div > div > div:nth-child(3)"
            )
            await container.wait_for(state="visible", timeout=10000)
            html_content = await container.inner_html()
            soup = BeautifulSoup(html_content, "html.parser")
            cards = soup.find_all("div", class_=re.compile(r"group/table-card"))

            print(f"📦 Found {len(cards)} class cards")

            # Collect links first
            day_links = []
            for idx, card in enumerate(cards):
                # Extract club name for this card
                club_tag = card.select_one("p.hidden.flex-1.lg\\:block")
                club = club_tag.text.strip() if club_tag else card.select_one(
                    "p span.text-right.lg\\:hidden").text.strip()

                # Extract link for this card
                link_tag = card.find("a", string=re.compile(r"(BOOK NOW|STANDBY|WAITLIST|VIEW)", re.I))
                if link_tag and link_tag.get("href"):
                    day_links.append((link_tag["href"], club))

            if not day_links:
                print(f" No class links found for {date_str}")
                current_day += datetime.timedelta(days=1)
                continue

            print(f" Collected {len(day_links)} links for {date_str}")

            # --- Visit each link after handling login if needed ---
            for idx, (link, club) in enumerate(day_links):
                full_url = f"https://www.1rebel.com{link}" if link.startswith("/") else link
                print(f"🔍 Visiting Link {idx+1}: {full_url}")

                # --- LOGIN if needed ---
                if not logged_in:
                    try:
                        if await page.locator('button:has-text("Sign In")').is_visible():
                            await page.locator('button:has-text("Sign In")').click()
                            await page.wait_for_timeout(3000)

                        if await page.locator('input#id_username').is_visible():
                            print("Logging in to account...")
                            await page.fill('input#id_username', "ssimranjit302@gmail.com")
                            await page.fill('input#id_password', "Simranjit@2003")
                            await page.locator('button[data-test-button="log-in"]').click()
                            await page.wait_for_timeout(5000)
                            logged_in = True
                            print(" Logged in successfully.")

                            # Retry visiting current link after login
                            await page.goto(full_url, wait_until="domcontentloaded", timeout=60000)
                            await page.wait_for_timeout(3000)
                    except:
                        pass

                try:
                    await page.goto(full_url, wait_until="domcontentloaded", timeout=60000)
                    await page.wait_for_timeout(1000)
                    await page.wait_for_selector('div.bg-gray-lightLight', timeout=10000)

                    new_html = await page.content()
                    soup_new = BeautifulSoup(new_html, "html.parser")
                    main_div = soup_new.select_one('div.bg-gray-lightLight')

                    new_page_class = new_page_time = new_page_duration = new_page_trainer = capacity = booked = ""

                    if main_div:
                        new_page_class = main_div.select_one('h1').text.strip() if main_div.select_one('h1') else ""
                        time_span = main_div.select_one('span')
                        new_page_time = time_span.text.strip() if time_span else ""

                        # 3. Extract capacity / booked
                        capacity = booked = ""
                        cap_div = main_div.find('div', class_=re.compile(r'text-\[0\.8125rem\]'))
                        if cap_div:
                            numbers = re.findall(r'\d+', cap_div.get_text())
                            if len(numbers) >= 2:
                                capacity, booked = numbers[1], numbers[0]  # adjust order if needed

                    all_data.append({
                        "date": current_day.strftime("%d %b %Y"),
                        "start_time": "",
                        "concept": "",
                        "club": club,
                        "trainer": "",
                        "status": "",
                        "new_page_class": new_page_class,
                        "new_page_time": new_page_time,
                        "new_page_duration": new_page_duration,
                        "new_page_trainer": new_page_trainer,
                        "capacity": capacity,
                        "booked": booked
                    })

                except Exception as e:
                    print(f"️ Error visiting {full_url}: {e}")
                    continue

            current_day += datetime.timedelta(days=1)

        await browser.close()

    # Save CSV
    with open(csv_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=csv_columns)
        writer.writeheader()
        writer.writerows(all_data)

    print(f"\n Data saved to {csv_file} ({len(all_data)} entries)")


if __name__ == "__main__":
    asyncio.run(main())
