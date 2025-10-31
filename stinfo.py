import pandas as pd
import random
from datetime import datetime, timedelta
import os

# -----------------------------
# CONFIGURATION
# -----------------------------
num_days = 1000  # number of days
attendance_prob = 0.75  # probability student attends
output_folder = os.getcwd()  # current folder
csv_filename = os.path.join(output_folder, "controlled_attendance.csv")

# -----------------------------
# STUDENTS
# -----------------------------
student_data = [
    {"student_id": 1, "name": "sasith", "card_id": "0000744920"},
    {"student_id": 2, "name": "suhada", "card_id": "0002026244"},
    {"student_id": 3, "name": "prabath", "card_id": "0001922654"},
    {"student_id": 4, "name": "vidula", "card_id": "0002027310"},
    {"student_id": 5, "name": "chinthaka", "card_id": "0002068183"}
]

# -----------------------------
# GENERATE DATES
# -----------------------------
start_date = datetime.today() - timedelta(days=num_days)
dates = [start_date + timedelta(days=i) for i in range(num_days)]

# -----------------------------
# GENERATE DATASET
# -----------------------------
data = []
for date_item in dates:
    for student in student_data:
        attended = 1 if random.random() < attendance_prob else 0
        data.append([
            student["student_id"],
            student["card_id"],
            student["name"],
            date_item.strftime("%Y-%m-%d"),
            attended,
            attended  # same as attended
        ])

# -----------------------------
# CREATE DATAFRAME AND SAVE
# -----------------------------
df = pd.DataFrame(data, columns=["student_id", "card_id", "name", "date", "attended", "attendance"])
df.to_csv(csv_filename, index=False)

print(f"CSV generated successfully at: {csv_filename}")
print(df.head())
print(f"Total records: {len(df)}")
