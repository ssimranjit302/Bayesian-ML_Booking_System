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
        "1_RebelRawData.py",
        "2_RebelSlotsExcel.py"
    ]

    for script in scripts:
        run_step(script)

    # Rename final output files
    excel_src = PROJECT_DIR / "RebelSlotsExcel.xlsx"
    json_src = PROJECT_DIR / "RebelSlotsData.json"
    excel_dst = PROJECT_DIR / "Master.xlsx"
    json_dst = PROJECT_DIR / "Master.json"

    if excel_src.exists():
        excel_src.rename(excel_dst)
        print(f"Renamed: {excel_src.name} → {excel_dst.name}")
    else:
        print("Warning: RebelSlotsExcel.xlsx not found.")

    if json_src.exists():
        json_src.rename(json_dst)
        print(f"Renamed: {json_src.name} → {json_dst.name}")
    else:
        print("Warning: RebelSlotsData.json not found.")

if __name__ == "__main__":
    main()
