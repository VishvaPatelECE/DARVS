import numpy as np
from flask import Flask, render_template, Response, jsonify
import cv2
from camera import VideoCamera
from collections import deque
import time
from admin_panel import register_admin_routes

app = Flask(__name__, template_folder="templates", static_folder="static")

# ===============================
# CREATE CAMERA OBJECT
# ===============================
video_camera = VideoCamera()

# ===============================
# SYSTEM STATE STORAGE
# ===============================
RECENT_ACTIVITY = deque(maxlen=20)

SYSTEM_STATS = {
    "total_attempts": 0,
    "success_count": 0,
    "recognition_fail_count": 0,
    "liveness_fail_count": 0,
    "success_rate": 0.0
}

last_auth_state = False
last_system_state = None

# ===============================
# REGISTER ADMIN ROUTES
# ===============================
register_admin_routes(app, video_camera, SYSTEM_STATS, RECENT_ACTIVITY)

# ===============================
# VIDEO STREAM
# ===============================
def generate_frames():
    global last_auth_state, last_system_state

    # 🔥 Ensure camera is started
    video_camera.start()

    first_frame_sent = False

    while True:
        frame = video_camera.get_frame()

        # -------------------------------------------------
        # If camera not ready yet → send temporary frame
        # -------------------------------------------------
        if frame is None:
            if not first_frame_sent:
                blank = np.zeros((480, 640, 3), dtype=np.uint8)
                cv2.putText(blank, "Initializing Camera...",
                            (120, 250),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            1,
                            (0, 255, 0),
                            2)

                ret, buffer = cv2.imencode('.jpg', blank)

                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' +
                       buffer.tobytes() +
                       b'\r\n')

                first_frame_sent = True

            time.sleep(0.05)
            continue

        # -------------------------------------------------
        # NORMAL STATE LOGIC
        # -------------------------------------------------
        current_auth = video_camera.auth_time is not None
        current_state = video_camera.system_state

        if current_auth and not last_auth_state:
            SYSTEM_STATS["total_attempts"] += 1
            SYSTEM_STATS["success_count"] += 1

            RECENT_ACTIVITY.appendleft({
                "timestamp": time.strftime("%H:%M:%S"),
                "user": video_camera.last_name,
                "confidence": round(video_camera.last_conf, 2),
                "result": "success"
            })

        if last_system_state != "HARD_FAIL" and current_state == "HARD_FAIL":
            SYSTEM_STATS["total_attempts"] += 1
            SYSTEM_STATS["liveness_fail_count"] += 1

            RECENT_ACTIVITY.appendleft({
                "timestamp": time.strftime("%H:%M:%S"),
                "user": "Unknown",
                "confidence": 0,
                "result": "fail"
            })

        if SYSTEM_STATS["total_attempts"] > 0:
            SYSTEM_STATS["success_rate"] = (
                SYSTEM_STATS["success_count"] /
                SYSTEM_STATS["total_attempts"]
            ) * 100

        last_auth_state = current_auth
        last_system_state = current_state

        # -------------------------------------------------
        # Encode and stream frame
        # -------------------------------------------------
        ret, buffer = cv2.imencode('.jpg', frame)
        if not ret:
            continue

        first_frame_sent = True

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' +
               buffer.tobytes() +
               b'\r\n')
# ===============================
# ROUTES
# ===============================
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/video_feed")
def video_feed():
    video_camera.start()  # 🔥 START CAMERA HERE
    return Response(
        generate_frames(),
        mimetype='multipart/x-mixed-replace; boundary=frame'
    )


@app.route("/api/dashboard-state")
def dashboard_state():

    state = video_camera.system_state

    return jsonify({
        "system_state": state,
        "confidence": round(video_camera.last_conf, 2),
        "name": video_camera.last_name,
        "system_stats": SYSTEM_STATS,
        "activity_log": list(RECENT_ACTIVITY)
    })


# ===============================
# MAIN
# ===============================
if __name__ == "__main__":
    app.run(debug=True, threaded=True)