from flask import render_template, request, redirect, session, send_file, jsonify
import io
import csv

from config_manager import load_config, save_config
from register import FaceRegister
from database import delete_user

ADMIN_PASSWORD = "darvs_admin_2026"


def register_admin_routes(app, camera, SYSTEM_STATS, RECENT_ACTIVITY):

    app.secret_key = "darvs_secret_key"

    # -----------------------
    # LOGIN
    # -----------------------

    @app.route("/admin", methods=["GET", "POST"])
    def admin_login():

        if request.method == "POST":
            password = request.form.get("password")

            if password == ADMIN_PASSWORD:
                session["admin_logged_in"] = True
                return redirect("/admin/dashboard")

        return render_template("admin_login.html")

    # -----------------------
    # DASHBOARD
    # -----------------------

    @app.route("/admin/dashboard")
    def admin_dashboard():

        if not session.get("admin_logged_in"):
            return redirect("/admin")

        camera.recognizer.data = camera.recognizer.load_encodings()

        config = load_config()

        users = list(camera.recognizer.data.keys())

        return render_template(
            "admin_dashboard.html",
            stats=SYSTEM_STATS,
            users=users,
            config=config,
            system_enabled=camera.system_enabled,
        )

    # -----------------------
    # LOGOUT
    # -----------------------

    @app.route("/admin/logout")
    def admin_logout():
        session.clear()
        return redirect("/admin")

    # -----------------------
    # REGISTER USER
    # -----------------------

    @app.route("/admin/register-user", methods=["POST"])
    def register_user():

        if not session.get("admin_logged_in"):
            return jsonify({"status": "unauthorized"}), 403

        username = request.form.get("username")

        if not username:
            return jsonify({"status": "error", "message": "Username required"})

        try:

            print(f"[ADMIN] Registering {username}")

            camera.system_enabled = False

            # release camera for registration
            camera.release()

            registrar = FaceRegister()
            success = registrar.register_user(username)

            # restart main camera
            camera.start()
            camera.system_enabled = True

            # reload embeddings
            camera.recognizer.data = camera.recognizer.load_encodings()

            # reset recognition pipeline
            camera.reset_system()

            if success:
                return jsonify({"status": "success"})
            else:
                return jsonify({"status": "failed"})

        except Exception as e:

            print("[ADMIN ERROR]", e)

            camera.start()
            camera.system_enabled = True

            return jsonify({
                "status": "error",
                "message": str(e)
            })

    # -----------------------
    # DELETE USER
    # -----------------------

    @app.route("/admin/delete-user/<username>")
    def delete_user_route(username):

        if not session.get("admin_logged_in"):
            return redirect("/admin")

        try:

            print(f"[ADMIN] Deleting user {username}")

            camera.recognizer.delete_user(username)

            delete_user(username)

            camera.recognizer.data = camera.recognizer.load_encodings()

            camera.reset_system()

        except Exception as e:
            print("[DELETE ERROR]", e)

        return redirect("/admin/dashboard")

    # -----------------------
    # UPDATE THRESHOLD
    # -----------------------

    @app.route("/admin/update-threshold", methods=["POST"])
    def update_threshold():

        config = load_config()

        config["threshold"] = int(request.form.get("threshold"))

        save_config(config)

        camera.threshold = config["threshold"]

        return redirect("/admin/dashboard")

    # -----------------------
    # UPDATE LIVENESS
    # -----------------------

    @app.route("/admin/update-liveness", methods=["POST"])
    def update_liveness():

        config = load_config()

        config["shift_ratio"] = float(request.form.get("shift_ratio"))

        save_config(config)

        camera.liveness.shift_ratio = config["shift_ratio"]

        return redirect("/admin/dashboard")

    # -----------------------
    # TOGGLE SYSTEM
    # -----------------------

    @app.route("/admin/toggle-system")
    def toggle_system():

        config = load_config()

        config["system_enabled"] = not config["system_enabled"]

        save_config(config)

        camera.system_enabled = config["system_enabled"]

        return redirect("/admin/dashboard")

    # -----------------------
    # RESET STATS
    # -----------------------

    @app.route("/admin/reset-stats")
    def reset_stats():

        for key in SYSTEM_STATS:
            if isinstance(SYSTEM_STATS[key], (int, float)):
                SYSTEM_STATS[key] = 0

        return redirect("/admin/dashboard")

    # -----------------------
    # DOWNLOAD LOGS
    # -----------------------

    @app.route("/admin/download-logs")
    def download_logs():

        output = io.StringIO()

        writer = csv.writer(output)

        writer.writerow(["Timestamp", "User", "Confidence", "Result"])

        for entry in RECENT_ACTIVITY:
            writer.writerow([
                entry["timestamp"],
                entry["user"],
                entry["confidence"],
                entry["result"],
            ])

        output.seek(0)

        return send_file(
            io.BytesIO(output.getvalue().encode()),
            mimetype="text/csv",
            as_attachment=True,
            download_name="darvs_logs.csv",
        )