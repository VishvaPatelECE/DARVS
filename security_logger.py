import threading
import datetime
import platform
from cloud_sheet_logger import append_to_sheet


def log_event(name, confidence, status, liveness_result):

    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    device_name = platform.node()

    row = [
        timestamp,
        name,
        confidence,
        status,
        liveness_result,
        device_name
    ]

    def background_log():
        try:
            append_to_sheet(row)
            print("Cloud log sent:", row)
        except Exception as e:
            print("Cloud log error:", e)

    threading.Thread(target=background_log, daemon=True).start()