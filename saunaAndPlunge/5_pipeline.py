import subprocess
import os
import json
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo

PROJECT_DIR = Path(__file__).resolve().parent

# =======================
# PRE-CHECK BLOCK (ADDED)
# =======================

def run_template_reset():
    reset_script = PROJECT_DIR / "templateReset.py"
    print("Running templateReset.py ...")
    result = subprocess.run(["python3", str(reset_script)], capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error in templateReset.py: {result.stderr}")
        exit(1)
    print("templateReset.py completed successfully.\n")

master_path = PROJECT_DIR / "Master.json"

london_time = datetime.now(ZoneInfo("Europe/London"))
today_london_date = london_time.strftime("%Y-%m-%d")

if not master_path.exists():
    print("Master.json not found. Triggering template reset.")
    run_template_reset()
else:
    try:
        with open(master_path, "r") as f:
            data = json.load(f)

        if not data or "Date" not in data[0]:
            print("Master.json is empty or malformed. Triggering template reset.")
            run_template_reset()
        else:
            master_date = data[0]["Date"]

            if master_date != today_london_date:
                print(
                    f"Date mismatch detected.\n"
                    f"Master.json date: {master_date}\n"
                    f"Today's London date: {today_london_date}\n"
                    f"Triggering template reset."
                )
                run_template_reset()
            else:
                print("Master.json date matches today's London date. Proceeding with pipeline.\n")

    except Exception as e:
        print(f"Error reading Master.json ({e}). Triggering template reset.")
        run_template_reset()

# =======================
# ORIGINAL PIPELINE LOGIC
# =======================

def run_step(script_name):
    script_path = PROJECT_DIR / script_name
    print(f"Running {script_path}...")
    result = subprocess.run(["python3", str(script_path)], capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error in {script_name}: {result.stderr}")
        exit(1)
    print(f"{script_name} completed successfully.\n")


def main():
    scripts = [
        "1_bothBooked.py",
        "2_trippedSlots.py",
        "3_Master.py",
        "4_HistoricalExcel.py"
    ]

    for script in scripts:
        run_step(script)

    print("Pipeline completed successfully — final output ready!")


if __name__ == "__main__":
    main()
