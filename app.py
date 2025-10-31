import streamlit as st
import pandas as pd
from datetime import datetime, date, time as dtime
from twilio.rest import Client
import os
import joblib

# -----------------------
# CONFIG
# -----------------------
CSV_FILE = "controlled_attendance.csv"

# Twilio config
ACCOUNT_SID = 'AC0bd7198f9b8b9cc6e7e40b2f41c12'
AUTH_TOKEN = '68b6278f050d5e23da7a6ac421e7343e'
TWILIO_NUMBER = '+18777804236'

client = Client(ACCOUNT_SID, AUTH_TOKEN)

# -----------------------
# UTILITY FUNCTIONS
# -----------------------
def load_attendance():
    if os.path.exists(CSV_FILE):
        df = pd.read_csv(CSV_FILE, dtype=str)
        if 'phone' not in df.columns:
            df['phone'] = ""
        return df.fillna("")
    else:
        return pd.DataFrame(columns=["student_id","card_id","name","date","attended","phone"])

def save_attendance(df):
    df.to_csv(CSV_FILE, index=False)

def normalize_id(raw):
    return ''.join(filter(str.isdigit, str(raw).strip()))

def send_sms(phone_number, message_body):
    if not phone_number or str(phone_number).strip() == "":
        print("No phone number provided, skipping SMS.")
        return
    try:
        message = client.messages.create(
            from_=TWILIO_NUMBER,
            body=message_body,
            to=str(phone_number)
        )
        st.success(f"SMS sent to {phone_number}")
        print(message.sid)
    except Exception as e:
        st.error(f"Failed to send SMS to {phone_number}: {e}")
        print(f"Failed to send SMS to {phone_number}: {e}")

# -----------------------
# Attendance Functions
# -----------------------
def mark_attendance(card_input, attendance_df):
    today = date.today().isoformat()
    now = datetime.now()
    current_time = now.time()
    cutoff_time = dtime(hour=8, minute=30)

    cid = str(card_input).zfill(10)

    # Master student list (rows without a date)
    master_records = attendance_df[attendance_df['date'].isnull() | (attendance_df['date'] == '')].drop_duplicates(subset=['student_id'])
    master_records["card_id"] = master_records["card_id"].astype(str).str.strip().str.zfill(10)

    # Find student
    row = master_records[master_records["card_id"] == cid]
    if row.empty:
        return False, attendance_df, "Card ID not found in the database!"

    student = row.iloc[0]
    student_name = student["name"]
    student_id = student["student_id"]
    phone_number = student["phone"]

    # Check if already marked today
    if not attendance_df[(attendance_df["card_id"] == cid) & (attendance_df["date"] == today)].empty:
        return False, attendance_df, f"{student_name} already checked in today."

    # Determine attendance: 1 if on time, 0 if late
    attended_flag = 1 if current_time <= cutoff_time else 0

    # Add attendance row
    new_row = {
        "student_id": student_id,
        "card_id": cid,
        "name": student_name,
        "date": today,
        "attended": attended_flag,
        "phone": phone_number
    }
    attendance_df = pd.concat([attendance_df, pd.DataFrame([new_row])], ignore_index=True)
    save_attendance(attendance_df)

    # Send SMS
    sms_text = f"✅ {student_name} has been marked {'present' if attended_flag==1 else 'absent'} on {today}."
    send_sms(phone_number, sms_text)

    return True, attendance_df, f"✅ Marked {'present' if attended_flag==1 else 'absent'}: {student_name} | SMS sent!"

# Automatically mark absent for students not checked in by 8:30 AM
def mark_absent_for_late_students(attendance_df):
    today = date.today().isoformat()
    now = datetime.now()
    cutoff_time = dtime(hour=8, minute=30)

    if now.time() < cutoff_time:
        return attendance_df  # Do not mark early

    master_records = attendance_df[attendance_df['date'].isnull() | (attendance_df['date'] == '')].drop_duplicates(subset=['student_id'])
    master_records["card_id"] = master_records["card_id"].astype(str).str.strip().str.zfill(10)
    today_students = attendance_df[attendance_df['date'] == today]['student_id'].tolist()

    absent_students = master_records[~master_records['student_id'].isin(today_students)]

    for _, student in absent_students.iterrows():
        new_row = {
            "student_id": student['student_id'],
            "card_id": student['card_id'],
            "name": student['name'],
            "date": today,
            "attended": 0,
            "phone": student['phone']
        }
        attendance_df = pd.concat([attendance_df, pd.DataFrame([new_row])], ignore_index=True)

        if student['phone'] and str(student['phone']).strip():
            sms_text = f"⚠️ {student['name']} has NOT attended school today ({today})."
            send_sms(student['phone'], sms_text)

    save_attendance(attendance_df)
    return attendance_df

# -----------------------
# STREAMLIT UI
# -----------------------
tab1, tab2 = st.tabs(["🎓 RFID Attendance", "📊 Prediction Viewer"])

# -----------------------
# Tab 1: RFID Attendance
# -----------------------
with tab1:
    st.header("RFID Attendance")
    attendance_df = load_attendance()
    attendance_df = mark_absent_for_late_students(attendance_df)  # auto-mark absent after 8:30

    col1, col2 = st.columns([3,1])
    with col1:
        raw_card = st.text_input("Scan or enter card ID", "")
    with col2:
        mark_btn = st.button("Mark Present")

    if mark_btn and raw_card:
        normalized = normalize_id(raw_card)
        success, attendance_df, msg = mark_attendance(normalized, attendance_df)
        if success:
            st.success(msg)
        else:
            st.error(msg)

    # Show today's attendance
    today = date.today().isoformat()
    today_df = attendance_df[attendance_df["date"] == today]
    st.subheader(f"Attendance for {today} ({len(today_df)} entries)")
    st.dataframe(today_df.reset_index(drop=True))

# -----------------------
# Tab 2: Prediction Viewer
# -----------------------
with tab2:
    st.header("Prediction Viewer")
    uploaded = st.file_uploader("Upload predictions CSV (must contain student_id and probability columns)", type=["csv"])
    if uploaded is not None:
        preds = pd.read_csv(uploaded, dtype=str)
        st.subheader("Preview")
        st.dataframe(preds.head(50))

        if 'student_id' not in preds.columns:
            st.error("Uploaded file must have a 'student_id' column.")
        elif 'probability' not in preds.columns and 'prob' not in preds.columns:
            st.error("Uploaded file must have a 'probability' or 'prob' column.")
        else:
            prob_col = 'probability' if 'probability' in preds.columns else 'prob'
            preds[prob_col] = pd.to_numeric(preds[prob_col], errors='coerce').fillna(0.0)

            top_n = st.number_input("Notify top N predicted present", min_value=1, max_value=100, value=5, step=1)
            notify_btn = st.button("Notify Top N")

            if notify_btn:
                master = load_attendance()
                master_records = master[master['date'].isnull() | (master['date'] == '')].drop_duplicates(subset=['student_id'])
                master_records['student_id'] = master_records['student_id'].astype(str)

                preds['student_id'] = preds['student_id'].astype(str)
                merged = preds.merge(master_records[['student_id','name','phone','card_id']], on='student_id', how='left')
                merged = merged.sort_values(by=prob_col, ascending=False).head(int(top_n))

                notified = 0
                for _, row in merged.iterrows():
                    phone = row.get('phone', "")
                    name = row.get('name') or row.get('student_id')
                    prob = float(row[prob_col]) if not pd.isna(row[prob_col]) else 0.0
                    if phone and str(phone).strip():
                        text = f"Prediction: {name} — Probability: {prob:.2f}"
                        try:
                            send_sms(phone, text)
                            notified += 1
                        except Exception as e:
                            print(f"Error sending SMS to {phone}: {e}")
                    else:
                        print(f"No phone for student {row.get('student_id')}, skipping.")

                st.success(f"Notification attempts sent for {notified} students.")
