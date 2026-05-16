from flask import Flask, render_template, Response, request, jsonify
from detector import (
    gen_frames,
    set_zone,
    get_latest_alert,
    set_video_source
)
import os
from llama_query import ask_question

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


# ---------------- HOME ----------------
@app.route("/")
def index():
    return render_template("index.html")


# ---------------- VIDEO STREAM ----------------
@app.route("/video_feed")
def video_feed():
    return Response(
        gen_frames(),
        mimetype="multipart/x-mixed-replace; boundary=frame"
    )


# ---------------- SET ZONE ----------------
@app.route("/set_zone", methods=["POST"])
def set_zone_api():
    data = request.json

    zone = [
        data["x1"],
        data["y1"],
        data["x2"],
        data["y2"]
    ]

    set_zone(zone)

    return jsonify({
        "status": "Zone updated",
        "zone": zone
    })


# ---------------- ALERT STATUS ----------------
@app.route("/alert_status")
def alert_status():
    return jsonify(get_latest_alert())


# ---------------- VIDEO UPLOAD ----------------
@app.route("/upload", methods=["POST"])
def upload():

    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["file"]

    if file.filename == "":
        return jsonify({"error": "Empty filename"}), 400

    save_path = os.path.join(UPLOAD_FOLDER, file.filename)

    file.save(save_path)

    print(f"[INFO] Uploaded video: {save_path}")

    # 🔥 SWITCH STREAM SOURCE
    set_video_source(save_path)

    return jsonify({
        "status": "Video uploaded successfully",
        "source": save_path
    })


# ---------------- SWITCH BACK TO CAMERA ----------------
@app.route("/use_camera", methods=["POST"])
def use_camera():

    set_video_source(None)

    return jsonify({
        "status": "Switched back to live camera"
    })


# ---------------- AI QUERY ----------------
@app.route("/ask", methods=["POST"])
def ask():

    data = request.json
    query = data.get("query")

    answer = ask_question(query)

    return jsonify({
        "answer": answer
    })


# ---------------- MAIN ----------------
if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=False,
        threaded=True
    )