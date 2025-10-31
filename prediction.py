import pandas as pd
import joblib

 # Load the trained model
model = joblib.load("attendance_model.pkl")
print("prediction.py loaded the model successfully.")
 # Load the CSV with student IDs
df = pd.read_csv("controlled_attendance.csv")  # Replace with your CSV filename
valid_ids = df['student_id'].tolist()  # List of valid IDs

 # Input from user
student_id = input("Enter student ID: ")

 # Check if ID exists
if student_id not in valid_ids:
     print(f"Student ID {student_id} is not in the database.")
else:
     # Prepare data for prediction
     new_data = pd.DataFrame({'student_id': [student_id]})
    
     # Make prediction
     prediction = model.predict(new_data)[0]
     probability = model.predict_proba(new_data)[0][1]
    
     # Show results
     print(f"Predicted Attendance: {prediction}")
     print(f"Probability of attending: {probability:.2f}")
