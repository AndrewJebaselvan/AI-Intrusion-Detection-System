import cv2
from ultralytics import YOLO

# CHANGE THIS TO YOUR PHONE STREAM
CAMERA_URL = "http://192.0.0.4:8080/video"

model = YOLO("yolov8n.pt")
cap = cv2.VideoCapture(CAMERA_URL)

while True:
    ret, frame = cap.read()
    if not ret:
        break

    results = model(frame, conf=0.5)

    annotated = results[0].plot()
    cv2.imshow("AI Camera Feed", annotated)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()


import time

prev_time = time.time()

# Inside frame loop
current_time = time.time()
fps = 1 / (current_time - prev_time)
prev_time = current_time

print(f"FPS: {fps:.2f}")
