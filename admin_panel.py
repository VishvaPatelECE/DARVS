from flask import render_template, request, redirect, session, send_file
import io
import csv
from config_manager import load_config, save_config

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

        config = load_config()

        return render_template(
            "admin_dashboard.html",
            stats=SYSTEM_STATS,
            users=list(camera.recognizer.data.keys()),
            config=config,
            system_enabled=camera.system_enabled
        )

    # -----------------------
    # LOGOUT
    # -----------------------
    @app.route("/admin/logout")
    def admin_logout():
        session.clear()
        return redirect("/admin")

    # -----------------------
    # DELETE USER
    # -----------------------
    @app.route("/admin/delete-user/<username>")
    def delete_user(username):

        if not session.get("admin_logged_in"):
            return redirect("/admin")

        camera.recognizer.delete_user(username)
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
                entry["result"]
            ])

        output.seek(0)

        return send_file(
            io.BytesIO(output.getvalue().encode()),
            mimetype="text/csv",
            as_attachment=True,
            download_name="darvs_logs.csv"
        )