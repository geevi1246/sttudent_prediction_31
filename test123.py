import streamlit as st
import pandas as pd
from datetime import datetime
from twilio.rest import Client
import os

# -----------------------------
# CONFIG
# -----------------------------
CSV_FILE = "controlled_attendance.csv"

st.set_page_config(page_title="RFID Attendance System", layout="centered")

st.title("🎓 RFID Student Attendance & SMS System")

st.markdown("""
Automatically mark attendance when a student scans their RFID card  
and send instant SMS notifications to parents using **Twilio**.
""")

# -----------------------------
# TWILIO CREDENTIALS INPUT
# -----------------------------
account_sid = st.text_input("🔑 Twilio Account SID(AC0bd7198f9b8b9cc6e7e40b2f41b35c12)", type="default")
auth_token = st.text_input("🧩 Twilio Auth Token(68b6278f050d5e23da7a6ac421e7343e)", type="password")
twilio_number = st.text_input("📱 Twilio Phone Number (e.g., +18587861499)")

# -----------------------------
# LOAD STUDENT DATABASE
# -----------------------------
if not os.path.exists(CSV_FILE):
    st.error(f"⚠️ {CSV_FILE} not found! Please upload or create it first.")
    st.stop()

students_df = pd.read_csv(CSV_FILE)

# -----------------------------
# RFID SCAN INPUT
# -----------------------------
st.subheader("🎫 RFID Scanner Input")
card_id = st.text_input("Scan or Enter Student Card ID")

# -----------------------------
# ATTENDANCE LOGIC
# -----------------------------
if st.button("✅ Mark Attendance"):
    if not card_id:
        st.error("Please enter a valid Card ID.")
    else:
        # Find student by card ID
        student = students_df.loc[students_df["card_id"] == card_id]

        if student.empty:
            st.error("❌ Card ID not found in database.")
        else:
            student_name = student["name"].values[0]
            student_phone = student["phone"].values[0]

            # Get current date and time
            now = datetime.now()
            date_today = now.strftime("%Y-%m-%d")
            time_now = now.strftime("%H:%M:%S")

            # Mark attendance
            cutoff_time = datetime.strptime("08:30:00", "%H:%M:%S").time()
            status = "Present" if now.time() <= cutoff_time else "Late"

            # Update DataFrame
            students_df.loc[students_df["card_id"] == card_id, "date"] = date_today
            students_df.loc[students_df["card_id"] == card_id, "attended"] = status
            students_df.to_csv(CSV_FILE, index=False)

            st.success(f"🎉 {student_name} marked as **{status}** on {date_today}")

            # Send SMS
            if account_sid and auth_token and twilio_number:
                try:
                    client = Client(account_sid, auth_token)
                    if status == "Late":
                        body = f"Dear Parent, your child {student_name} was LATE to school today ({date_today})."
                    else:
                        body = f"Dear Parent, your child {student_name} has ARRIVED at school on time ({date_today})."

                    client.messages.create(
                        body=body,
                        from_=twilio_number,
                        to=student_phone
                    )
                    st.info(f"📩 SMS sent to parent ({student_phone}).")
                except Exception as e:
                    st.error(f"Error sending SMS: {e}")
            else:
                st.warning("⚠️ Enter your Twilio credentials and number to send SMS.")

# -----------------------------
# DISPLAY ATTENDANCE TABLE
# -----------------------------
st.subheader("📊 Attendance Records")
st.dataframe(students_df)
