import json
import csv
import shutil
import os
from pathlib import Path

# CONFIG
BASE_DIR = Path(__file__).resolve().parent

template_path = BASE_DIR / "template_schedule.json"
output_path = BASE_DIR / "tempHourlySlots.json"

output_dir = BASE_DIR

# Make a copy of template JSON

template_copy_path = os.path.join(output_dir, "template_schedule_copy.json")
shutil.copy(template_path, template_copy_path)

print(f" Template copied to: {template_copy_path}")


#  Load both JSONs

with open(template_copy_path, "r") as f:
    template_data = json.load(f)

with open(output_path, "r") as f:
    output_data = json.load(f)


#  Update 'Booked' where matching

for out_row in output_data:
    for temp_row in template_data:
        if (
            temp_row["Date"] == out_row["Date"]
            and temp_row["Start Time"] == out_row["Start Time"]
            and temp_row["End Time"] == out_row["End Time"]
            and temp_row["Service/Class"] == out_row["Service/Class"]
            and temp_row["Staff/Centre"] == out_row["Staff/Centre"]
            and int(temp_row["Capacity"]) == int(out_row["Capacity"])
        ):
            temp_row["Booked"] = out_row["Booked"]
            break  # stop searching once match found

print(" Booked values updated where matches found.")

#  Save updated JSON

updated_json_path = os.path.join(output_dir, "updated_schedule.json")
with open(updated_json_path, "w") as f:
    json.dump(template_data, f, indent=4)

print(f" Updated JSON saved to: {updated_json_path}")


# Also save as CSV

csv_path = os.path.join(output_dir, "KoyoHourlyTrends.csv")

with open(csv_path, "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=template_data[0].keys())
    writer.writeheader()
    writer.writerows(template_data)

print(f" Updated CSV saved to: {csv_path}")
