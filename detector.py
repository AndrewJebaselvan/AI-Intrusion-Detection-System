import cv2
import time
import os
from ultralytics import YOLO
from datetime import datetime

# ---------------- CAMERA ----------------
CAMERA_URL = "http://192.0.0.4:8080"
model = YOLO("yolov8n.pt")

# ---------------- CONFIG ----------------
RESTRICTED_ZONE = [200, 100, 500, 500]

PERSISTENCE_FRAMES = 10
MAX_PERSISTENCE = 30
ZONE_CRITICALITY = 1.0
IOT_TRIGGER_THRESHOLD = 75

INPUT_SIZE = 640
FRAME_SKIP = 1
LOG_PERFORMANCE = True

# ---------------- STATE ----------------
inside_counter = 0
intrusion_confirmed = False
last_confidence = 0.0
iot_triggered = False

latest_alert = {
    "level": "NONE",
    "score": 0,
    "confidence": 0.0,
    "persistence": 0,
    "zone": "N/A",
    "reason": "No intrusion detected",
    "iot": "OFF",
    "fps": 0,
    "detections": 0
}

# ---------------- API FUNCTIONS ----------------
def set_zone(zone):
    global RESTRICTED_ZONE
    RESTRICTED_ZONE = zone
    print(f"[INFO] Zone updated to: {zone}")

def get_latest_alert():
    return latest_alert

# ---------------- HELPERS ----------------
def log_event(message):
    with open("events.log", "a") as f:
        f.write(f"[{datetime.now()}] {message}\n")

def log_performance(fps, detections):
    if not LOG_PERFORMANCE:
        return
    
    os.makedirs("results", exist_ok=True)
    with open("results/performance.csv", "a") as f:
        f.write(f"{datetime.now()},{round(fps,2)},{detections}\n")

def box_intersects_zone(box, zone):
    bx1, by1, bx2, by2 = box
    zx1, zy1, zx2, zy2 = zone
    return not (bx2 < zx1 or bx1 > zx2 or by2 < zy1 or by1 > zy2)

def compute_threat_score(conf, persistence):
    persistence_ratio = min(persistence / MAX_PERSISTENCE, 1.0)
    return int(conf * 40 + persistence_ratio * 40 + ZONE_CRITICALITY * 20)

def threat_level(score):
    if score >= 75:
        return "HIGH"
    elif score >= 40:
        return "MEDIUM"
    return "LOW"

def trigger_iot(score):
    global iot_triggered
    if score >= IOT_TRIGGER_THRESHOLD:
        if not iot_triggered:
            iot_triggered = True
            log_event("IoT ALERT TRIGGERED")
        return "ON"
    else:
        iot_triggered = False
        return "OFF"

# ---------------- CORE PROCESSING ----------------
def process_frame(frame):
    global inside_counter, intrusion_confirmed, last_confidence

    frame = cv2.resize(frame, (INPUT_SIZE, INPUT_SIZE))
    results = model(frame, conf=0.5)

    person_inside = False
    detection_count = 0

    for box, cls, conf in zip(
        results[0].boxes.xyxy,
        results[0].boxes.cls,
        results[0].boxes.conf
    ):
        if int(cls) == 0:
            detection_count += 1
            x1, y1, x2, y2 = map(int, box)

            if box_intersects_zone((x1, y1, x2, y2), RESTRICTED_ZONE):
                person_inside = True
                last_confidence = float(conf)
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 2)

    # -------- Persistence --------
    if person_inside:
        inside_counter += 1
    else:
        inside_counter = 0
        intrusion_confirmed = False
        latest_alert["iot"] = "OFF"

    if inside_counter >= PERSISTENCE_FRAMES:
        intrusion_confirmed = True

    # Draw zone
    zx1, zy1, zx2, zy2 = RESTRICTED_ZONE
    cv2.rectangle(frame, (zx1, zy1), (zx2, zy2), (0, 255, 255), 2)

    # -------- Threat Logic --------
    if intrusion_confirmed:
        score = compute_threat_score(last_confidence, inside_counter)
        level = threat_level(score)
        iot_state = trigger_iot(score)

        latest_alert.update({
            "level": level,
            "score": score,
            "confidence": round(last_confidence, 2),
            "persistence": inside_counter,
            "zone": "Restricted Area",
            "reason": f"Intrusion for {inside_counter} frames",
            "iot": iot_state
        })

        log_event(f"Intrusion | Level={level} | Score={score}")

        color = (0, 0, 255) if level == "HIGH" else (0, 165, 255)
        cv2.putText(frame, f"THREAT: {level} | SCORE: {score}",
                    (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, color, 3)
    else:
        latest_alert.update({
            "level": "NONE",
            "score": 0,
            "confidence": 0.0,
            "persistence": 0,
            "zone": "N/A",
            "reason": "Monitoring",
            "iot": "OFF"
        })

        cv2.putText(frame, f"Monitoring ({inside_counter}/{PERSISTENCE_FRAMES})",
                    (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.8,
                    (0, 255, 0), 2)

    return frame, detection_count

# ---------------- LIVE STREAM ----------------
def gen_frames():
    while True:
        cap = cv2.VideoCapture(CAMERA_URL)

        if not cap.isOpened():
            print("Camera retry...")
            time.sleep(2)
            continue

        prev_time = time.time()

        while True:
            success, frame = cap.read()
            if not success:
                cap.release()
                break

            frame, detections = process_frame(frame)

            fps = 1 / (time.time() - prev_time)
            prev_time = time.time()

            latest_alert["fps"] = int(fps)
            latest_alert["detections"] = detections

            log_performance(fps, detections)

            cv2.putText(frame, f"FPS: {int(fps)}",
                        (20, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.8,
                        (255, 255, 0), 2)

            _, buffer = cv2.imencode(".jpg", frame)
            yield (b"--frame\r\n"
                   b"Content-Type: image/jpeg\r\n\r\n" +
                   buffer.tobytes() + b"\r\n")

# ---------------- RECORDED VIDEO ----------------
def run_detection(source):
    cap = cv2.VideoCapture(source)

    prev_time = time.time()

    while True:
        success, frame = cap.read()
        if not success:
            break

        frame, detections = process_frame(frame)

        fps = 1 / (time.time() - prev_time)
        prev_time = time.time()

        latest_alert["fps"] = int(fps)
        latest_alert["detections"] = detections

        log_performance(fps, detections)

    cap.release()