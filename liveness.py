import cv2
import mediapipe as mp
import numpy as np
import time


class BlinkLiveness:
    def __init__(self):
        self.face_mesh = mp.solutions.face_mesh.FaceMesh(
            static_image_mode=False,
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )

        self.EAR_THRESHOLD = 0.20
        self.EAR_CONSEC_FRAMES = 2

        self.blink_count = 0
        self.frame_counter = 0
        self.required_blinks = 2

        self.challenge_start_time = None
        self.challenge_timeout = 5

    def eye_aspect_ratio(self, eye):
        A = np.linalg.norm(eye[1] - eye[5])
        B = np.linalg.norm(eye[2] - eye[4])
        C = np.linalg.norm(eye[0] - eye[3])
        return (A + B) / (2.0 * C)

    def process_frame(self, frame):
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.face_mesh.process(rgb)

        if not results.multi_face_landmarks:
            return False, "No Face Detected"

        face_landmarks = results.multi_face_landmarks[0]
        h, w, _ = frame.shape

        LEFT_EYE = [33, 160, 158, 133, 153, 144]
        RIGHT_EYE = [362, 385, 387, 263, 373, 380]

        left_eye = np.array([
            [face_landmarks.landmark[i].x * w,
             face_landmarks.landmark[i].y * h]
            for i in LEFT_EYE
        ])

        right_eye = np.array([
            [face_landmarks.landmark[i].x * w,
             face_landmarks.landmark[i].y * h]
            for i in RIGHT_EYE
        ])

        leftEAR = self.eye_aspect_ratio(left_eye)
        rightEAR = self.eye_aspect_ratio(right_eye)
        ear = (leftEAR + rightEAR) / 2.0

        if ear < self.EAR_THRESHOLD:
            self.frame_counter += 1
        else:
            if self.frame_counter >= self.EAR_CONSEC_FRAMES:
                self.blink_count += 1
            self.frame_counter = 0

        if self.challenge_start_time is None:
            self.challenge_start_time = time.time()

        elapsed = time.time() - self.challenge_start_time

        if self.blink_count >= self.required_blinks:
            return True, "Liveness Passed"

        if elapsed > self.challenge_timeout:
            self.reset()
            return False, "Liveness Failed"

        remaining = self.required_blinks - self.blink_count
        return False, f"Blink {remaining} more time(s)"

    def reset(self):
        self.blink_count = 0
        self.frame_counter = 0
        self.challenge_start_time = None