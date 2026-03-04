import numpy as np
import cv2
import time


class AntiSpoofEngine:
    def __init__(self):

        # Buffers
        self.position_buffer = []
        self.area_buffer = []

        self.buffer_size = 20
        self.min_frames_required = 10

        # Illumination
        self.flash_active = False
        self.flash_start_time = None
        self.flash_duration = 0.15  # seconds

        self.before_flash_brightness = None
        self.after_flash_brightness = None

        self.spoof_counter = 0

    # -------------------------------------------------
    # UPDATE PER FRAME
    # -------------------------------------------------
    def update_motion(self, bbox):

        x, y, w, h = bbox

        center_x = x + w / 2
        center_y = y + h / 2
        area = w * h

        self.position_buffer.append((center_x, center_y))
        self.area_buffer.append(area)

        if len(self.position_buffer) > self.buffer_size:
            self.position_buffer.pop(0)
            self.area_buffer.pop(0)

    # -------------------------------------------------
    # MOTION SCORE
    # -------------------------------------------------
    def compute_motion_score(self):

        if len(self.position_buffer) < self.min_frames_required:
            return 90

        positions = np.array(self.position_buffer)
        areas = np.array(self.area_buffer)

        motion_std = np.std(positions)
        area_var = np.var(areas)

        if motion_std < 1:
            motion_score = 30
        elif motion_std < 2:
            motion_score = 60
        else:
            motion_score = 90

        if area_var < 100:
            depth_score = 40
        elif area_var < 400:
            depth_score = 70
        else:
            depth_score = 90

        return 0.6 * motion_score + 0.4 * depth_score

    # -------------------------------------------------
    # ILLUMINATION LOGIC
    # -------------------------------------------------
    def start_flash(self):
        self.flash_active = True
        self.flash_start_time = time.time()
        self.before_flash_brightness = None
        self.after_flash_brightness = None

    def process_flash(self, frame, bbox):

        if not self.flash_active:
            return frame, None

        x, y, w, h = bbox
        cheek_roi = frame[y + int(h * 0.3): y + int(h * 0.6),
                          x + int(w * 0.3): x + int(w * 0.7)]

        gray = cv2.cvtColor(cheek_roi, cv2.COLOR_BGR2GRAY)
        mean_brightness = np.mean(gray)

        elapsed = time.time() - self.flash_start_time

        if elapsed < self.flash_duration / 2:
            # Before flash
            self.before_flash_brightness = mean_brightness
            overlay = frame.copy()
            overlay[:] = (255, 255, 255)
            frame = cv2.addWeighted(frame, 0.5, overlay, 0.5, 0)

        elif elapsed < self.flash_duration:
            # After flash
            self.after_flash_brightness = mean_brightness

        else:
            self.flash_active = False

        return frame, self.compute_illumination_score()

    def compute_illumination_score(self):

        if self.before_flash_brightness is None or \
           self.after_flash_brightness is None:
            return None

        delta = abs(self.after_flash_brightness -
                    self.before_flash_brightness)

        # Phone screens usually produce larger uniform delta
        if delta > 25:
            return 30
        elif delta > 15:
            return 60
        else:
            return 90

    # -------------------------------------------------
    # FINAL SPOOF DECISION
    # -------------------------------------------------
    def evaluate(self, motion_score, illum_score):

        if illum_score is None:
            return False, 100

        combined = 0.6 * motion_score + 0.4 * illum_score

        if combined < 65:
            self.spoof_counter += 1
        else:
            self.spoof_counter = 0

        spoof_flag = self.spoof_counter >= 3

        return spoof_flag, combined

    # -------------------------------------------------
    def reset(self):
        self.position_buffer.clear()
        self.area_buffer.clear()
        self.flash_active = False
        self.spoof_counter = 0