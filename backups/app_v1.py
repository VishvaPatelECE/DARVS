from flask import Flask, render_template, Response, jsonify
import cv2
from camera import VideoCamera
from collections import deque
import time
from admin_panel import register_admin_routes

app = Flask(__name__, template_folder="templates", static_folder="static")

# -----------------------------
# CORE SYSTEM OBJECTS
# -----------------------------

camera = VideoCamera()

RECENT_ACTIVITY = deque(maxlen=20)

SYSTEM_STATS = {
    "total_attempts": 0,
    "success_count": 0,
    "recognition_fail_count": 0,
    "liveness_fail_count": 0,
    "success_rate": 0.0
}

last_auth_state = False
last_system_state = None  # 🔥 REQUIRED FIX

# Register admin routes AFTER shared state is defined
register_admin_routes(app, camera, SYSTEM_STATS, RECENT_ACTIVITY)


# -----------------------------
# VIDEO STREAM
# -----------------------------
def generate_frames():
    global last_auth_state, last_system_state

    while True:
        frame = camera.get_frame()

        if frame is None:
            continue

        current_auth = camera.auth_time is not None
        current_state = camera.system_state

        # ==========================
        # SUCCESS (ONE-TIME EVENT)
        # ==========================
        if current_auth and not last_auth_state:

            SYSTEM_STATS["total_attempts"] += 1
            SYSTEM_STATS["success_count"] += 1

            RECENT_ACTIVITY.appendleft({
                "timestamp": time.strftime("%H:%M:%S"),
                "user": camera.last_name,
                "liveness": True,
                "confidence": round(camera.last_conf, 2),
                "result": "success"
            })

        # ==========================
        # RECOGNITION FAIL (STATE CHANGE)
        # ==========================
        if last_auth_state and not current_auth and current_state == "LIVENESS":

            SYSTEM_STATS["total_attempts"] += 1
            SYSTEM_STATS["recognition_fail_count"] += 1

            RECENT_ACTIVITY.appendleft({
                "timestamp": time.strftime("%H:%M:%S"),
                "user": camera.last_name or "Unknown",
                "liveness": True,
                "confidence": round(camera.last_conf, 2),
                "result": "fail"
            })

        # ==========================
        # LIVENESS FAIL (TRANSITION INTO HARD_FAIL)
        # ==========================
        if last_system_state != "HARD_FAIL" and current_state == "HARD_FAIL":

            SYSTEM_STATS["total_attempts"] += 1
            SYSTEM_STATS["liveness_fail_count"] += 1

            RECENT_ACTIVITY.appendleft({
                "timestamp": time.strftime("%H:%M:%S"),
                "user": "Unknown",
                "liveness": False,
                "confidence": 0,
                "result": "fail"
            })

        # ==========================
        # SUCCESS RATE UPDATE
        # ==========================
        if SYSTEM_STATS["total_attempts"] > 0:
            SYSTEM_STATS["success_rate"] = (
                SYSTEM_STATS["success_count"] /
                SYSTEM_STATS["total_attempts"]
            ) * 100

        # Update state trackers
        last_auth_state = current_auth
        last_system_state = current_state

        # Encode frame
        ret, buffer = cv2.imencode('.jpg', frame)
        if not ret:
            continue

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' +
               buffer.tobytes() +
               b'\r\n')


# -----------------------------
# ROUTES
# -----------------------------

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/video_feed")
def video_feed():
    return Response(
        generate_frames(),
        mimetype='multipart/x-mixed-replace; boundary=frame'
    )


# -----------------------------
# DASHBOARD API
# -----------------------------

@app.route("/api/dashboard-state")
def dashboard_state():

    state = camera.system_state

    if state == "HARD_FAIL":
        banner_state = "error"
        banner_msg = "ACCESS DENIED"

    elif camera.auth_time:
        banner_state = "success"
        banner_msg = "ACCESS GRANTED"

    else:
        banner_state = None
        banner_msg = "Awaiting authentication..."

    return jsonify({
        "system_state": state,
        "confidence": round(camera.last_conf, 2),
        "name": camera.last_name,
        "banner": {
            "state": banner_state,
            "msg": banner_msg
        },
        "system_stats": SYSTEM_STATS,
        "activity_log": list(RECENT_ACTIVITY)
    })


# -----------------------------
# MAIN
# -----------------------------

if __name__ == "__main__":
    app.run(debug=True, threaded=True)