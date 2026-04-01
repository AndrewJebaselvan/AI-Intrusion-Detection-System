from flask import Flask, render_template, Response, request, jsonify
from detector import gen_frames, set_zone, get_latest_alert, run_detection  # ✅ ADD THIS
import os  # ✅ ADD THIS
from llama_query import ask_question

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"  # ✅ ADD THIS
os.makedirs(UPLOAD_FOLDER, exist_ok=True)  # ✅ ADD THIS


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/video_feed")
def video_feed():
    return Response(gen_frames(),
                    mimetype="multipart/x-mixed-replace; boundary=frame")


@app.route("/set_zone", methods=["POST"])
def set_zone_api():
    data = request.json
    zone = [data["x1"], data["y1"], data["x2"], data["y2"]]
    set_zone(zone)
    return jsonify({"status": "Zone updated", "zone": zone})


@app.route("/alert_status")
def alert_status():
    return jsonify(get_latest_alert())


# ---------------- NEW UPLOAD ROUTE ----------------
@app.route("/upload", methods=["POST"])
def upload():
    file = request.files["file"]

    if not file:
        return jsonify({"error": "No file uploaded"}), 400

    path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(path)

    print(f"Processing uploaded video: {path}")

    run_detection(path)  # 🔥 THIS CALLS YOUR SYSTEM

    return jsonify({"status": "Processing complete"})


@app.route("/ask", methods=["POST"])
def ask():
    data = request.json
    query = data.get("query")

    answer = ask_question(query)

    return jsonify({"answer": answer})



if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False) 