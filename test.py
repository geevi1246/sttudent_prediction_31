import streamlit as st
import pandas as pd
from datetime import datetime
from twilio.rest import Client
import os

# -----------------------------
# CONFIGURATION
# -----------------------------
CSV_FILE = "controlled_attendance.csv"

st.set_page_config(page_title="Manual Attendance System", layout="centered")

st.title("👩‍🏫 Teacher Attendance Marking System")
st.markdown("""
Mark student attendance manually and send **SMS notifications** to parents using **Twilio**.
""")

# -----------------------------
# TWILIO CREDENTIALS INPUT
# -----------------------------
st.sidebar.header("🔐 Twilio Settings")
account_sid = st.sidebar.text_input("Account SID", type="default")
auth_token = st.sidebar.text_input("Auth Token", type="password")
twilio_number = st.sidebar.text_input("Twilio Phone Number (e.g., +15017122661)")

# -----------------------------
# LOAD STUDENT DATA
# -----------------------------
if not os.path.exists(CSV_FILE):
    st.error(f"⚠️ {CSV_FILE} not found! Please upload or create it first.")
    st.stop()

students_df = pd.read_csv(CSV_FILE)

# Ensure correct columns exist
required_cols = ["student_id", "card_id", "name", "date", "attended", "phone"]
for col in required_cols:
    if col not in students_df.columns:
        st.error(f"Missing column in CSV: {col}")
        st.stop()

# -----------------------------
# MANUAL ATTENDANCE INPUT
# -----------------------------
st.subheader("📝 Mark Attendance Manually")

student_name = st.selectbox("Select Student", students_df["name"].tolist())
status = st.selectbox("Select Attendance Status", ["Present", "Late", "Absent"])
mark_btn = st.button("✅ Submit Attendance")

# -----------------------------
# ATTENDANCE LOGIC
# -----------------------------
if mark_btn:
    # Get current time and date
    now = datetime.now()
    date_today = now.strftime("%Y-%m-%d")

    # Find student details
    student_data = students_df[students_df["name"] == student_name].iloc[0]
    student_phone = student_data["phone"]

    # Update record
    students_df.loc[students_df["name"] == student_name, "date"] = date_today
    students_df.loc[students_df["name"] == student_name, "attended"] = status

    # Save back to CSV
    students_df.to_csv(CSV_FILE, index=False)

    st.success(f"✅ Marked {student_name} as **{status}** on {date_today}")

    # -----------------------------
    # SEND SMS
    # -----------------------------
    if account_sid and auth_token and twilio_number:
        try:
            client = Client(account_sid, auth_token)

            if status == "Absent":
                body = f"Dear Parent, your child {student_name} was marked ABSENT today ({date_today})."
            elif status == "Late":
                body = f"Dear Parent, your child {student_name} was marked LATE today ({date_today})."
            else:
                body = f"Dear Parent, your child {student_name} has ARRIVED and marked PRESENT today ({date_today})."

            client.messages.create(
                body=body,
                from_=twilio_number,
                to=student_phone
            )

            st.info(f"📩 SMS sent successfully to parent ({student_phone}).")

        except Exception as e:
            st.error(f"Error sending SMS: {e}")
    else:
        st.warning("⚠️ Enter Twilio credentials in the sidebar to enable SMS sending.")

# -----------------------------
# DISPLAY ATTENDANCE TABLE
# -----------------------------
st.subheader("📊 Current Attendance Records")
st.dataframe(students_df)
