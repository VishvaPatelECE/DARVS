import cv2
import tensorflow as tf


class EyeBlinkDetector:
    def __init__(self, model_path="eye_model.h5"):

        self.model = tf.keras.models.load_model(model_path)

        # Blink state machine
        self.closed_frames = 0
        self.open_frames = 0
        self.blink_in_progress = False

        # You can tune this if needed
        self.threshold = 0.85
        self.required_closed_frames = 2
        self.required_open_frames = 2

    def _predict_eye(self, eye_img):

        eye_img = cv2.resize(eye_img, (24, 24))
        eye_img = cv2.cvtColor(eye_img, cv2.COLOR_BGR2GRAY)
        eye_img = eye_img / 255.0
        eye_img = eye_img.reshape(1, 24, 24, 1)

        prediction = self.model.predict(eye_img, verbose=0)[0][0]

        # IMPORTANT: model is inverted
        # High value = OPEN
        return "open" if prediction > self.threshold else "closed"

    def detect_blink(self, frame, box, keypoints):

        x, y, w, h = box

        face_width = w
        face_height = h

        left_eye = keypoints["left_eye"]
        right_eye = keypoints["right_eye"]

        eye_w = int(face_width * 0.28)
        eye_h = int(face_height * 0.18)

        eye_states = []

        for eye in [left_eye, right_eye]:

            ex, ey = eye

            x1 = max(ex - eye_w // 2, 0)
            y1 = max(ey - eye_h // 2, 0)
            x2 = ex + eye_w // 2
            y2 = ey + eye_h // 2

            eye_img = frame[y1:y2, x1:x2]

            if eye_img.size == 0:
                continue

            state = self._predict_eye(eye_img)
            eye_states.append(state)

        if len(eye_states) != 2:
            return False

        # BOTH eyes must be closed
        if eye_states[0] == "closed" and eye_states[1] == "closed":
            self.closed_frames += 1
            self.open_frames = 0

            if self.closed_frames >= self.required_closed_frames:
                self.blink_in_progress = True

        else:
            self.open_frames += 1
            self.closed_frames = 0

            if self.blink_in_progress and self.open_frames >= self.required_open_frames:
                self.blink_in_progress = False
                self.open_frames = 0
                return True

        return False

    def reset(self):
        self.closed_frames = 0
        self.open_frames = 0
        self.blink_in_progress = False