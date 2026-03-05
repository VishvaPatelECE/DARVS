import cv2
import time

from recognizer import FaceRecognizer
from database import add_user
from cloud_sync import upload_file


class FaceRegister:

    def __init__(self, camera=None):

        self.recognizer = FaceRecognizer()

        if camera is None:
            self.cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        else:
            self.cap = camera.cap

        if not self.cap or not self.cap.isOpened():
            raise RuntimeError("Cannot open webcam")

    # -------------------------------------------------
    # CAPTURE EMBEDDINGS
    # -------------------------------------------------

    def capture_multiple_embeddings(self, instruction, samples=8):

        print(f"Prepare: {instruction}")

        embeddings = []
        attempts = 0
        max_attempts = 200

        # preparation countdown
        start_time = time.time()

        while time.time() - start_time < 2:

            ret, frame = self.cap.read()
            if not ret:
                continue

            cv2.putText(
                frame,
                instruction,
                (30, 40),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (0, 255, 0),
                2
            )

            cv2.imshow("Guided Registration", frame)
            cv2.waitKey(1)

        # capture embeddings

        while len(embeddings) < samples and attempts < max_attempts:

            attempts += 1

            ret, frame = self.cap.read()
            if not ret:
                continue

            detection = self.recognizer.detect_face(frame)

            if detection:

                box, _ = detection
                embedding = self.recognizer.get_embedding_from_box(frame, box)

                if embedding is not None:
                    embeddings.append(embedding)
                    print(f"{instruction}: {len(embeddings)}/{samples}")

            cv2.putText(
                frame,
                f"{instruction} ({len(embeddings)}/{samples})",
                (30, 40),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (0, 255, 0),
                2
            )

            cv2.imshow("Guided Registration", frame)

            if cv2.waitKey(1) & 0xFF == ord("q"):
                return None

        if len(embeddings) < samples:
            return None

        return embeddings

    # -------------------------------------------------
    # REGISTER USER
    # -------------------------------------------------

    def register_user(self, name):

        print(f"Registering {name}...")

        if not add_user(name):
            print("User already exists.")
            return False

        instructions = [
            "Look Straight",
            "Turn Left",
            "Turn Right",
            "Look Up",
            "Look Down"
        ]

        for instruction in instructions:

            embeddings = self.capture_multiple_embeddings(
                instruction,
                samples=8
            )

            if embeddings is None:
                self.cleanup()
                return False

            for emb in embeddings:
                self.recognizer.add_embedding(name, emb)

        self.cleanup()

        try:
            upload_file("encodings.pkl", "encodings.pkl")
        except Exception:
            pass

        print("Registration completed successfully.")

        return True

    # -------------------------------------------------
    # CLEANUP
    # -------------------------------------------------

    def cleanup(self):

        if self.cap:
            self.cap.release()

        cv2.destroyAllWindows()


# -------------------------------------------------

if __name__ == "__main__":

    name = input("Enter user name to register: ")

    registrar = FaceRegister()

    registrar.register_user(name)