import cv2
import time
import os
from ultralytics import YOLO
from datetime import datetime

# ---------------- MODEL ----------------
model = YOLO("yolov8n.pt")

# ---------------- CAMERA ----------------
CAMERA_URL = "http://192.0.0.4:8080"

# ---------------- ACTIVE SOURCE ----------------
CURRENT_SOURCE = CAMERA_URL

# ---------------- CONFIG ----------------
RESTRICTED_ZONE = [200, 100, 500, 500]

PERSISTENCE_FRAMES = 10
MAX_PERSISTENCE = 30
ZONE_CRITICALITY = 1.0
IOT_TRIGGER_THRESHOLD = 75

INPUT_SIZE = 640

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
    "reason": "Monitoring",
    "iot": "OFF",
    "fps": 0,
    "detections": 0
}


# ---------------- SOURCE CONTROL ----------------
def set_video_source(source):
    global CURRENT_SOURCE

    if source is None:
        CURRENT_SOURCE = CAMERA_URL
        print("[INFO] Switched to LIVE CAMERA")
    else:
        CURRENT_SOURCE = source
        print(f"[INFO] Switched to VIDEO FILE: {source}")


# ---------------- API ----------------
def set_zone(zone):
    global RESTRICTED_ZONE
    RESTRICTED_ZONE = zone


def get_latest_alert():
    return latest_alert


# ---------------- HELPERS ----------------
def log_event(message):

    with open("events.log", "a") as f:
        f.write(f"[{datetime.now()}] {message}\n")


def box_intersects_zone(box, zone):

    bx1, by1, bx2, by2 = box
    zx1, zy1, zx2, zy2 = zone

    return not (
        bx2 < zx1 or
        bx1 > zx2 or
        by2 < zy1 or
        by1 > zy2
    )


def compute_threat_score(conf, persistence):

    persistence_ratio = min(
        persistence / MAX_PERSISTENCE,
        1.0
    )

    return int(
        conf * 40 +
        persistence_ratio * 40 +
        ZONE_CRITICALITY * 20
    )


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


# ---------------- FRAME PROCESSING ----------------
def process_frame(frame):

    global inside_counter
    global intrusion_confirmed
    global last_confidence

    frame = cv2.resize(frame, (INPUT_SIZE, INPUT_SIZE))

    results = model(frame, conf=0.5)

    person_inside = False
    detection_count = 0

    # ---------------- DETECTIONS ----------------
    for box, cls, conf in zip(
        results[0].boxes.xyxy,
        results[0].boxes.cls,
        results[0].boxes.conf
    ):

        if int(cls) == 0:

            detection_count += 1

            x1, y1, x2, y2 = map(int, box)

            # PERSON BOX
            cv2.rectangle(
                frame,
                (x1, y1),
                (x2, y2),
                (0, 255, 0),
                2
            )

            cv2.putText(
                frame,
                f"Person {conf:.2f}",
                (x1, y1 - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (0, 255, 0),
                2
            )

            # ZONE CHECK
            if box_intersects_zone(
                (x1, y1, x2, y2),
                RESTRICTED_ZONE
            ):

                person_inside = True
                last_confidence = float(conf)

                cv2.rectangle(
                    frame,
                    (x1, y1),
                    (x2, y2),
                    (0, 0, 255),
                    3
                )

    # ---------------- PERSISTENCE ----------------
    if person_inside:
        inside_counter += 1
    else:
        inside_counter = 0
        intrusion_confirmed = False

    if inside_counter >= PERSISTENCE_FRAMES:
        intrusion_confirmed = True

    # ---------------- ZONE ----------------
    zx1, zy1, zx2, zy2 = RESTRICTED_ZONE

    cv2.rectangle(
        frame,
        (zx1, zy1),
        (zx2, zy2),
        (0, 255, 255),
        2
    )

    cv2.putText(
        frame,
        "RESTRICTED ZONE",
        (zx1, zy1 - 10),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (0, 255, 255),
        2
    )

    # ---------------- THREAT ----------------
    if intrusion_confirmed:

        score = compute_threat_score(
            last_confidence,
            inside_counter
        )

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

        color = (
            (0, 0, 255)
            if level == "HIGH"
            else (0, 165, 255)
        )

        cv2.putText(
            frame,
            f"THREAT: {level} | SCORE: {score}",
            (20, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            color,
            3
        )

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

        cv2.putText(
            frame,
            f"Monitoring ({inside_counter}/{PERSISTENCE_FRAMES})",
            (20, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 255, 0),
            2
        )

    latest_alert["detections"] = detection_count

    return frame


# ---------------- STREAMING ----------------
def gen_frames():

    global CURRENT_SOURCE

    cap = None
    active_source = None

    while True:

        # SOURCE CHANGED
        if active_source != CURRENT_SOURCE:

            if cap is not None:
                cap.release()

            active_source = CURRENT_SOURCE

            print(f"[INFO] Opening source: {active_source}")

            cap = cv2.VideoCapture(active_source)

            time.sleep(1)

        # SOURCE FAILED
        if cap is None or not cap.isOpened():

            print("[WARNING] Source unavailable")

            time.sleep(2)

            continue

        success, frame = cap.read()

        # VIDEO ENDED
        if not success:

            # uploaded video finished
            if active_source != CAMERA_URL:

                print("[INFO] Uploaded video finished")

                cap.release()

                CURRENT_SOURCE = CAMERA_URL

                active_source = None

                continue

            else:
                cap.release()
                active_source = None
                time.sleep(1)
                continue

        # ---------------- FPS ----------------
        start = time.time()

        frame = process_frame(frame)

        fps = int(1 / max(time.time() - start, 0.001))

        latest_alert["fps"] = fps

        cv2.putText(
            frame,
            f"FPS: {fps}",
            (20, 80),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (255, 255, 0),
            2
        )

        # ---------------- ENCODE ----------------
        _, buffer = cv2.imencode(".jpg", frame)

        frame_bytes = buffer.tobytes()

        yield (
            b"--frame\r\n"
            b"Content-Type: image/jpeg\r\n\r\n" +
            frame_bytes +
            b"\r\n"
        )