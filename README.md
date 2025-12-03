AI Exercise Tracker using MediaPipe & OpenCV

This project is an AI-powered fitness tracker that uses computer vision to automatically count squats and bicep curls in real time.
It tracks reps using webcam pose detection, estimates calories burned, logs workout data, generates a PDF summary, and even emails the report automatically.
A simple Tkinter GUI collects user information and launches the workout session.

🚀 Features

🎥 Real-time pose detection using MediaPipe

🔢 Automatic squat & curl counting based on joint angles

🔥 Calorie calculation using MET-based estimation

🗂️ CSV logging of reps, timestamps & calories

📄 Auto-generated PDF summary after workout

📧 Email delivery of the PDF report (SMTP)

📊 Live graph showing reps over time

🖥️ Tkinter GUI for user input (name, age, email)

🔁 Reset option to clear data mid-session

📂 Project Structure
├── exercise_log.csv              # Auto-generated workout log
├── exercise_summary.pdf          # Auto-generated PDF summary
├── main_script.py                # (Your uploaded code)
├── outputs/                      # (Optional folder for graphs)
└── README.md


Note: CSV & PDF files are created automatically after running the program.

🧠 How It Works
1️⃣ GUI Input

User enters:

Name

Age

Email address (to receive PDF)

2️⃣ Real-Time Tracking

Using MediaPipe Pose landmarks:

Squats are detected using hip-knee-ankle angle

Curls are detected using shoulder-elbow-wrist angle

Thresholds determine up/down stages

Reps increase when a full motion is completed

3️⃣ Logging & Graphing

Every frame logs:

Timestamp

Squat count

Curl count

Calories

A graph of reps vs time is shown at the end.

4️⃣ PDF Summary

The PDF includes:

Name & age

Total squats

Total curls

Calories burned

Total workout time

5️⃣ Email Sending

The PDF is emailed using Gmail SMTP credentials.

▶️ Running the Project
Install dependencies
pip install opencv-python mediapipe numpy pandas matplotlib fpdf

Run the program
python main_script.py

Controls

Q → Quit session

R → Reset counters & CSV

📊 Sample Outputs

exercise_log.csv → Continuous workout log

exercise_summary.pdf → Final workout report

Graph window → Reps over time

⚙️ Configuration Inside Code

You can modify:

Variable	Purpose
PERSON_WEIGHT_KG	Used for calorie estimation
SQUAT_DOWN, SQUAT_UP	Angle thresholds for squats
CURL_DOWN, CURL_UP	Angle thresholds for curls
HOLD_THRESHOLD	Frames required for curl detection
SENDER_EMAIL, SENDER_PASSWORD	For sending PDF via email

👨‍💻 Author

Vivek Rao
GitHub: https://github.com/vivekkrao07
