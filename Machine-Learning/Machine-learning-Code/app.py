from tkinter import *
from tkinter import messagebox
import cv2
import mediapipe as mp
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
import os
import time
from fpdf import FPDF
import smtplib
from email.message import EmailMessage

# --- Config ---
PERSON_WEIGHT_KG = 50 # Average weight for calorie calculation
CSV_FILE = "exercise_log.csv"            # CSV log file name   
PDF_FILE = "exercise_summary.pdf"        # Output PDF file name 
SENDER_EMAIL = "************@gmail.com"  # Your email here
SENDER_PASSWORD = "************"         # Your app password here

SQUAT_DOWN = 160
SQUAT_UP = 70
CURL_DOWN = 150
CURL_UP = 60
HOLD_THRESHOLD = 3

# --- Globals ---
squat_counter = 0
curl_counter = 0
squat_stage = None
curl_stage = None
time_started = None
reps_over_time = []
user_name = ""
user_age = ""
receiver_email = ""
curl_hold_frames = 0

# --- Mediapipe setup ---
mp_drawing = mp.solutions.drawing_utils
mp_pose = mp.solutions.pose
pose = mp_pose.Pose()

# --- Prepare CSV ---
if not os.path.exists(CSV_FILE):
    pd.DataFrame(columns=["timestamp", "squat", "curls", "calories"]).to_csv(CSV_FILE, index=False)

# --- Helper functions ---
def calculate_angle(a, b, c):
    a, b, c = np.array(a), np.array(b), np.array(c)
    radians = np.arctan2(c[1]-b[1], c[0]-b[0]) - np.arctan2(a[1]-b[1], a[0]-b[0])
    angle = np.abs(radians * 180.0 / np.pi)
    return 360 - angle if angle > 180 else angle

def calculate_calories(squats, curls):
    squat_met = 5.0
    curl_met = 3.5
    time_min = 1
    cal = ((squat_met * PERSON_WEIGHT_KG * 3.5) / 200) * time_min * squats
    cal += ((curl_met * PERSON_WEIGHT_KG * 3.5) / 200) * time_min * curls
    return round(cal, 2)

def generate_summary_pdf(squats, curls, calories, duration):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=16)
    pdf.cell(200, 10, txt="Exercise Summary Report", ln=True, align="C")
    pdf.set_font("Arial", size=12)
    pdf.ln(10)
    pdf.cell(200, 10, f"Name: {user_name}", ln=True)
    pdf.cell(200, 10, f"Age: {user_age}", ln=True)
    pdf.cell(200, 10, f"Total Squats: {squats}", ln=True)
    pdf.cell(200, 10, f"Total Bicep Curls: {curls}", ln=True)
    pdf.cell(200, 10, f"Calories Burned: {calories} kcal", ln=True)
    pdf.cell(200, 10, f"Time Spent: {duration} seconds", ln=True)
    pdf.output(PDF_FILE)

def show_live_graph():
    if not reps_over_time:
        return
    times, squats_list, curls_list = zip(*reps_over_time)
    plt.plot(times, squats_list, label='Squats', marker='o')
    plt.plot(times, curls_list, label='Curls', marker='x')
    plt.xlabel('Time (s)')
    plt.ylabel('Reps')
    plt.title('Reps over Time')
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.show()

def send_email_with_pdf(receiver_email, subject="Your Exercise Summary", body="Attached is your summary report.", attachment_path=PDF_FILE):
    msg = EmailMessage()
    msg["From"] = SENDER_EMAIL
    msg["To"] = receiver_email
    msg["Subject"] = subject
    msg.set_content(body)

    with open(attachment_path, "rb") as f:
        file_data = f.read()
        file_name = os.path.basename(attachment_path)
        msg.add_attachment(file_data, maintype="application", subtype="pdf", filename=file_name)

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(SENDER_EMAIL, SENDER_PASSWORD)
            smtp.send_message(msg)
            print("📩 Email sent successfully.")
    except Exception as e:
        print(f"❌ Email failed: {e}")

# --- Main workout loop ---
def start_counter():
    global squat_counter, curl_counter, squat_stage, curl_stage, curl_hold_frames, time_started

    # cap = cv2.VideoCapture("http://192.168.1.101:8080/video")  # phone camera
    cap = cv2.VideoCapture(0)  # PC webcam
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    time_started = time.time()

    while True:
        ret, frame = cap.read()
        if not ret:
            continue

        frame = cv2.flip(frame, 1)
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = pose.process(rgb)

        if results.pose_landmarks:
            h, w, _ = frame.shape
            lm = results.pose_landmarks.landmark
            get_pt = lambda id: [lm[id].x * w, lm[id].y * h]

            # Squat detection
            hip = get_pt(mp_pose.PoseLandmark.RIGHT_HIP.value)
            knee = get_pt(mp_pose.PoseLandmark.RIGHT_KNEE.value)
            ankle = get_pt(mp_pose.PoseLandmark.RIGHT_ANKLE.value)
            squat_angle = calculate_angle(hip, knee, ankle)

            # Curl detection (both arms)
            shoulder_r = get_pt(mp_pose.PoseLandmark.RIGHT_SHOULDER.value)
            elbow_r = get_pt(mp_pose.PoseLandmark.RIGHT_ELBOW.value)
            wrist_r = get_pt(mp_pose.PoseLandmark.RIGHT_WRIST.value)
            shoulder_l = get_pt(mp_pose.PoseLandmark.LEFT_SHOULDER.value)
            elbow_l = get_pt(mp_pose.PoseLandmark.LEFT_ELBOW.value)
            wrist_l = get_pt(mp_pose.PoseLandmark.LEFT_WRIST.value)

            curl_angle_r = calculate_angle(shoulder_r, elbow_r, wrist_r)
            curl_angle_l = calculate_angle(shoulder_l, elbow_l, wrist_l)

            # --- Squat logic ---
            if squat_angle > SQUAT_DOWN:
                squat_stage = "up"
            if squat_angle < SQUAT_UP and squat_stage == "up":
                squat_stage = "down"
                squat_counter += 1

            # --- Curl logic (both arms together) ---
            if curl_angle_r > CURL_DOWN and curl_angle_l > CURL_DOWN:
                curl_stage = "down"
            if curl_angle_r < CURL_UP and curl_angle_l < CURL_UP and curl_stage == "down":
                curl_hold_frames += 1
                if curl_hold_frames >= HOLD_THRESHOLD:
                    curl_stage = "up"
                    curl_counter += 1
                    curl_hold_frames = 0

            mp_drawing.draw_landmarks(frame, results.pose_landmarks, mp_pose.POSE_CONNECTIONS)

            calories = calculate_calories(squat_counter, curl_counter)
            now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            log = pd.DataFrame([{
                "timestamp": now,
                "squat": squat_counter,
                "curls": curl_counter,
                "calories": calories
            }])
            log.to_csv(CSV_FILE, mode='a', header=False, index=False)

            elapsed = int(time.time() - time_started)
            reps_over_time.append((elapsed, squat_counter, curl_counter))

        # --- Display info ---
        cv2.putText(frame, f"Name: {user_name}", (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 200, 0), 3)
        cv2.putText(frame, f"Age: {user_age}", (10, 80), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 200, 0), 3)
        cv2.putText(frame, f"Squats: {squat_counter}", (10, 140), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 255, 0), 3)
        cv2.putText(frame, f"Curls: {curl_counter}", (10, 180), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 255, 255), 3)
        cv2.putText(frame, f"Calories: {calculate_calories(squat_counter, curl_counter)} kcal", (10, 220), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 0, 255), 3)
        cv2.putText(frame, "Press Q to Quit | R to Reset", (10, 270), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)

        cv2.imshow("Exercise Tracker", frame)
        key = cv2.waitKey(10) & 0xFF
        if key == ord('q'):
            print("❌ Q pressed. Stopping workout...")
            break
        elif key == ord('r'):
            squat_counter = 0
            curl_counter = 0
            reps_over_time.clear()
            if os.path.exists(CSV_FILE):
                os.remove(CSV_FILE)
                pd.DataFrame(columns=["timestamp", "squat", "curls", "calories"]).to_csv(CSV_FILE, index=False)

    cap.release()
    cv2.destroyAllWindows()

    duration = int(time.time() - time_started)
    calories = calculate_calories(squat_counter, curl_counter)
    generate_summary_pdf(squat_counter, curl_counter, calories, duration)
    show_live_graph()
    send_email_with_pdf(receiver_email)

# --- GUI ---
def launch_gui():
    def start():
        global user_name, user_age, receiver_email
        user_name = name_entry.get()
        user_age = age_entry.get()
        receiver_email = email_entry.get()
        if not user_name or not user_age or not receiver_email:
            messagebox.showerror("Error", "Please enter Name, Age, and Receiver Email.")
            return
        root.destroy()
        start_counter()

    root = Tk()
    root.title("Exercise Tracker Input")
    root.geometry("400x250")
    Label(root, text="Enter your name:").pack(pady=5)
    name_entry = Entry(root, width=30)
    name_entry.pack()
    Label(root, text="Enter your age:").pack(pady=5)
    age_entry = Entry(root, width=30)
    age_entry.pack()
    Label(root, text="Enter receiver email:").pack(pady=5)
    email_entry = Entry(root, width=30)
    email_entry.pack()
    Button(root, text="Start Workout", command=start, bg="green", fg="white", width=20).pack(pady=15)
    root.mainloop()

launch_gui()