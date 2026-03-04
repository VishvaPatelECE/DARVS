import time
import random
from eye_blink_detector import EyeBlinkDetector


class MovementLiveness:
    def __init__(self):

        self.timeout_per_step = 6
        self.shift_ratio = 0.07
        self.tilt_ratio = 0.05
        self.required_frames = 2

        self.actions = ["LEFT", "RIGHT", "UP", "DOWN", "BLINK"]

        self.challenge = []
        self.current_step = 0

        self.baseline_center = None
        self.baseline_nose = None
        self.baseline_height = None

        self.step_start_time = None
        self.frame_counter = 0

        self.blink_detector = EyeBlinkDetector()

        # -------- Spoof Detection (Timeout Based Only) --------
        self.timeout_counter = 0
        self.max_timeouts = 3  # must fail 3 times before spoof

        self.generate_challenge()

    # -----------------------------------------

    def generate_challenge(self):
        self.challenge = random.sample(self.actions, 3)
        self.current_step = 0
        self.reset_baseline()

    def reset_baseline(self):
        self.baseline_center = None
        self.baseline_nose = None
        self.baseline_height = None
        self.step_start_time = None
        self.frame_counter = 0
        self.blink_detector.reset()

    def reset(self):
        self.generate_challenge()

    # -----------------------------------------

    def process(self, frame, box, keypoints, frame_width):

        if box is None or keypoints is None:
            return {
                "passed": False,
                "message": "No Face Detected",
                "spoof_detected": False
            }

        x, y, w, h = box
        center_x = x + w / 2
        nose_y = keypoints["nose"][1]

        if self.step_start_time is None:
            self.step_start_time = time.time()

        # -------- TIMEOUT CHECK --------
        if time.time() - self.step_start_time > self.timeout_per_step:

            self.timeout_counter += 1

            # If repeated timeouts → spoof
            if self.timeout_counter >= self.max_timeouts:
                self.timeout_counter = 0
                self.reset()
                return {
                    "passed": False,
                    "message": "Spoof Detected",
                    "spoof_detected": True
                }

            # Normal timeout (retry)
            self.reset()
            return {
                "passed": False,
                "message": "Liveness Timeout",
                "spoof_detected": False
            }

        if self.baseline_center is None:
            self.baseline_center = center_x
            self.baseline_nose = nose_y
            self.baseline_height = h

        shift_required = frame_width * self.shift_ratio
        tilt_required = self.baseline_height * self.tilt_ratio

        current_action = self.challenge[self.current_step]

        # -------------------------------------------------
        # BLINK HANDLING
        # -------------------------------------------------

        if current_action == "BLINK":

            blink = self.blink_detector.detect_blink(frame, box, keypoints)

            if blink:
                self.timeout_counter = 0  # reset timeout tracker
                self.current_step += 1
                self.reset_baseline()

                if self.current_step >= len(self.challenge):
                    self.generate_challenge()
                    return {
                        "passed": True,
                        "message": "Liveness Passed",
                        "spoof_detected": False
                    }

                return {
                    "passed": False,
                    "message": self.challenge[self.current_step],
                    "spoof_detected": False
                }

            return {
                "passed": False,
                "message": "BLINK",
                "spoof_detected": False
            }

        # -------------------------------------------------
        # NORMAL MOVEMENT LOGIC
        # -------------------------------------------------

        movement_detected = False

        if current_action == "LEFT":
            if center_x > self.baseline_center + shift_required:
                movement_detected = True

        elif current_action == "RIGHT":
            if center_x < self.baseline_center - shift_required:
                movement_detected = True

        elif current_action == "UP":
            if nose_y < self.baseline_nose - tilt_required:
                movement_detected = True

        elif current_action == "DOWN":
            if nose_y > self.baseline_nose + tilt_required:
                movement_detected = True

        if movement_detected:
            self.frame_counter += 1
        else:
            self.frame_counter = 0

        if self.frame_counter >= self.required_frames:

            self.timeout_counter = 0  # reset timeout tracker
            self.current_step += 1
            self.reset_baseline()

            if self.current_step >= len(self.challenge):
                self.generate_challenge()
                return {
                    "passed": True,
                    "message": "Liveness Passed",
                    "spoof_detected": False
                }

            return {
                "passed": False,
                "message": self.challenge[self.current_step],
                "spoof_detected": False
            }

        return {
            "passed": False,
            "message": current_action,
            "spoof_detected": False
        }