import cv2
from camera import VideoCamera

cam = VideoCamera()

while True:
    frame = cam.get_frame()
    if frame is None:
        break

    cv2.imshow("Face Recognition", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cam.release()