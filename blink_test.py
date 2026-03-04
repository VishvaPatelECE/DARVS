import cv2
from mtcnn import MTCNN
from eye_blink_detector import EyeBlinkDetector

cap = cv2.VideoCapture(0)
detector = MTCNN()
blink_detector = EyeBlinkDetector()

while True:
    ret, frame = cap.read()
    if not ret:
        break

    rgb = frame[:, :, ::-1]
    faces = detector.detect_faces(rgb)

    status_text = "No Face"

    if faces:
        face = faces[0]
        x, y, w, h = face["box"]
        x, y = abs(x), abs(y)

        keypoints = face["keypoints"]

        blink = blink_detector.detect_blink(frame, (x, y, w, h), keypoints)

        if blink:
            status_text = "BLINK DETECTED"
        else:
            status_text = "Face Detected"

        cv2.rectangle(frame, (x, y), (x + w, y + h), (0,255,0), 2)

    cv2.putText(
        frame,
        status_text,
        (30, 50),
        cv2.FONT_HERSHEY_SIMPLEX,
        1,
        (0, 255, 0),
        2
    )

    cv2.imshow("Blink Test", frame)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()