import subprocess
import os
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent

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
        "1_BookedSlots.py",
        "2_trippedSlots.py",
        "3_Master_JSON.py",
        "4_HistoricalExcel.py",
    ]

    for script in scripts:
        run_step(script)

    print("Pipeline completed successfully — final output ready!")

if __name__ == "__main__":
    main()
