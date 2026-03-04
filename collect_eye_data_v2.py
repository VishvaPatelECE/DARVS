import cv2
import os
from mtcnn import MTCNN

detector = MTCNN()
cap = cv2.VideoCapture(0)

SAVE_DIR = "eye_dataset"
OPEN_DIR = os.path.join(SAVE_DIR, "open")
CLOSED_DIR = os.path.join(SAVE_DIR, "closed")

os.makedirs(OPEN_DIR, exist_ok=True)
os.makedirs(CLOSED_DIR, exist_ok=True)

mode = "open"
img_count = 0

print("Press 'o' for OPEN mode")
print("Press 'c' for CLOSED mode")
print("Press 'q' to quit")

while True:
    ret, frame = cap.read()
    if not ret:
        break

    rgb = frame[:, :, ::-1]
    faces = detector.detect_faces(rgb)

    if faces:
        face = faces[0]
        x, y, w, h = face["box"]
        x, y = abs(x), abs(y)

        keypoints = face["keypoints"]
        left_eye = keypoints["left_eye"]
        right_eye = keypoints["right_eye"]

        # --- Face-relative eye crop ---
        face_width = w
        face_height = h

        eye_w = int(face_width * 0.28)
        eye_h = int(face_height * 0.18)

        for eye in [left_eye, right_eye]:
            ex, ey = eye

            x1 = max(ex - eye_w // 2, 0)
            y1 = max(ey - eye_h // 2, 0)
            x2 = ex + eye_w // 2
            y2 = ey + eye_h // 2

            eye_img = frame[y1:y2, x1:x2]

            if eye_img.size > 0:
                eye_img = cv2.resize(eye_img, (24, 24))
                eye_img = cv2.cvtColor(eye_img, cv2.COLOR_BGR2GRAY)

                if mode == "open":
                    path = os.path.join(OPEN_DIR, f"{img_count}.jpg")
                else:
                    path = os.path.join(CLOSED_DIR, f"{img_count}.jpg")

                cv2.imwrite(path, eye_img)
                img_count += 1

                cv2.imshow("Eye Crop", eye_img)

        cv2.rectangle(frame, (x, y), (x + w, y + h), (0,255,0), 2)

    cv2.imshow("Frame", frame)

    key = cv2.waitKey(1)

    if key == ord('o'):
        mode = "open"
        print("Mode: OPEN")

    elif key == ord('c'):
        mode = "closed"
        print("Mode: CLOSED")

    elif key == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()