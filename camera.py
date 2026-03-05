import cv2
import numpy as np
import time
from recognizer import FaceRecognizer
from movement_liveness import MovementLiveness
from security_logger import log_event
from config_manager import load_config


class VideoCamera:

    def __init__(self):

        # DO NOT OPEN CAMERA HERE
        self.cap = None
        self.camera_active = False

        self.recognizer = FaceRecognizer()
        self.liveness = MovementLiveness()

        config = load_config()
        self.threshold = config["threshold"]
        self.liveness.shift_ratio = config["shift_ratio"]
        self.system_enabled = config["system_enabled"]

        # -------- System State --------
        self.system_state = "LIVENESS"
        self.liveness_fail_count = 0
        self.hard_fail_until = None
        self.hard_fail_duration = 3

        # -------- Recognition --------
        self.recognition_start_time = None
        self.recognition_timeout = 8

        self.auth_time = None
        self.auth_display_duration = 2

        # -------- Performance --------
        self.frame_count = 0
        self.process_interval = 7
        self.scale = 0.5

        # -------- Recognition Buffer --------
        self.conf_buffer = []
        self.buffer_size = 3
        self.last_name = "Waiting..."
        self.last_conf = 0
        self.last_box = None

    # -------------------------------------------------
    # START CAMERA
    # -------------------------------------------------

    def start(self):

        if not self.camera_active:

            self.cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)

            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

            if not self.cap.isOpened():
                raise RuntimeError("Cannot open webcam")

            self.camera_active = True

            print("[CAMERA] Started")

    # -------------------------------------------------
    # GET FRAME
    # -------------------------------------------------

    def get_frame(self):

        if not self.camera_active:
            return None

        ret, frame = self.cap.read()

        if not ret:
            return None

        # -------------------------------------------------
        # REGISTRATION MODE (skip recognition)
        # -------------------------------------------------
        if not self.system_enabled:
            return frame

        self.frame_count += 1

        small_frame = cv2.resize(frame, (0, 0), fx=self.scale, fy=self.scale)

        detection = self.recognizer.detect_face(small_frame)

        if detection:

            box_small, keypoints_small = detection
            x_small, y_small, w_small, h_small = box_small

            x = int(x_small / self.scale)
            y = int(y_small / self.scale)
            w = int(w_small / self.scale)
            h = int(h_small / self.scale)

            box_full = (x, y, w, h)

            keypoints = {}

            for key, value in keypoints_small.items():
                keypoints[key] = (
                    int(value[0] / self.scale),
                    int(value[1] / self.scale)
                )

        else:
            box_full = None
            keypoints = None

        # ---------------- HARD FAIL ----------------

        if self.system_state == "HARD_FAIL":

            if time.time() < self.hard_fail_until:

                cv2.putText(
                    frame,
                    "ACCESS DENIED",
                    (130, 250),
                    cv2.FONT_HERSHEY_DUPLEX,
                    1.2,
                    (0, 0, 255),
                    3
                )

                return frame

            else:
                self.reset_system()

        # ---------------- LIVENESS ----------------

        if self.system_state == "LIVENESS":

            result = self.liveness.process(
                frame,
                box_full,
                keypoints,
                frame.shape[1]
            )

            cv2.putText(
                frame,
                result["message"],
                (20, 50),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.9,
                (255, 200, 0),
                3
            )

            if box_full:
                x, y, w, h = box_full

                cv2.rectangle(
                    frame,
                    (x, y),
                    (x + w, y + h),
                    (255, 200, 0),
                    2
                )

            if result.get("spoof_detected"):

                self.system_state = "HARD_FAIL"
                self.liveness_fail_count += 1
                self.hard_fail_until = time.time() + self.hard_fail_duration

                log_event(
                    "Unknown",
                    0,
                    "FAILED",
                    "FAILED_LIVENESS"
                )

                return frame

            if result["passed"]:

                self.system_state = "RECOGNITION"
                self.recognition_start_time = time.time()
                self.conf_buffer.clear()

            return frame

        # ---------------- RECOGNITION TIMEOUT ----------------

        if self.system_state == "RECOGNITION":

            if time.time() - self.recognition_start_time > self.recognition_timeout:

                log_event(
                    "Unknown",
                    0,
                    "FAILED",
                    "RECOGNITION_TIMEOUT"
                )

                self.reset_system()

                return frame

        # ---------------- RECOGNITION ----------------

        if (
            self.system_state == "RECOGNITION"
            and box_full
            and self.frame_count % self.process_interval == 0
        ):

            embedding = self.recognizer.get_embedding_from_box(frame, box_full)

            if embedding is not None:

                result = self.recognizer.recognize(embedding)

                confidence = result["confidence"]

                self.conf_buffer.append(confidence)

                if len(self.conf_buffer) > self.buffer_size:
                    self.conf_buffer.pop(0)

                avg_conf = sum(self.conf_buffer) / len(self.conf_buffer)

                self.last_conf = avg_conf
                self.last_box = box_full

                if avg_conf >= self.threshold:

                    self.last_name = result["name"]

                    if self.auth_time is None:

                        log_event(
                            result["name"],
                            avg_conf,
                            "SUCCESS",
                            "PASSED"
                        )

                        self.auth_time = time.time()

                else:
                    self.last_name = "Unknown"

        # ---------------- DRAW BOX ----------------

        if self.last_box:

            x, y, w, h = self.last_box

            color = (
                (0, 200, 0)
                if self.last_conf >= self.threshold
                else (0, 0, 255)
            )

            cv2.rectangle(
                frame,
                (x, y),
                (x + w, y + h),
                color,
                2
            )

            label = f"{self.last_name} ({round(self.last_conf,1)}%)"

            cv2.putText(
                frame,
                label,
                (x, y - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                color,
                2
            )

        # ---------------- ACCESS DISPLAY ----------------

        if self.auth_time:

            if time.time() - self.auth_time < self.auth_display_duration:

                cv2.putText(
                    frame,
                    "ACCESS GRANTED",
                    (140, 250),
                    cv2.FONT_HERSHEY_DUPLEX,
                    1.2,
                    (0, 255, 0),
                    3
                )

            else:
                self.reset_system()

        return frame

    # -------------------------------------------------
    # RESET SYSTEM
    # -------------------------------------------------

    def reset_system(self):

        self.liveness.reset()
        self.system_state = "LIVENESS"
        self.recognition_start_time = None
        self.auth_time = None
        self.conf_buffer.clear()
        self.last_name = "Waiting..."
        self.last_conf = 0
        self.last_box = None

    # -------------------------------------------------
    # RELEASE CAMERA
    # -------------------------------------------------

    def release(self):

        if self.cap:

            self.cap.release()
            cv2.destroyAllWindows()

        self.cap = None
        self.camera_active = False

        print("[CAMERA] Released")