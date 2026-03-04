import os
import pickle
import numpy as np
from mtcnn import MTCNN
from keras_facenet import FaceNet
from cloud_sync import download_file

ENCODINGS_FILE = "encodings.pkl"


class FaceRecognizer:
    def __init__(self):
        try:
            download_file("encodings.pkl", "encodings.pkl")
        except:
            pass

        self.detector = MTCNN()
        self.embedder = FaceNet()
        self.data = self.load_encodings()

    # =================================================
    # STORAGE
    # =================================================

    def load_encodings(self):
        if not os.path.exists(ENCODINGS_FILE):
            with open(ENCODINGS_FILE, "wb") as f:
                pickle.dump({}, f)
            return {}

        try:
            with open(ENCODINGS_FILE, "rb") as f:
                return pickle.load(f)
        except:
            return {}

    def save_encodings(self):
        with open(ENCODINGS_FILE, "wb") as f:
            pickle.dump(self.data, f)

    # =================================================
    # UTIL
    # =================================================

    def normalize(self, embedding):
        norm = np.linalg.norm(embedding)
        if norm == 0:
            return embedding
        return embedding / norm

    # =================================================
    # FACE DETECTION
    # =================================================

    def detect_face(self, frame):
        rgb = frame[:, :, ::-1]
        faces = self.detector.detect_faces(rgb)

        if not faces:
            return None

        face = faces[0]
        x, y, w, h = face["box"]
        x, y = abs(x), abs(y)

        keypoints = face["keypoints"]

        return (x, y, w, h), keypoints

    # =================================================
    # EMBEDDING
    # =================================================

    def get_embedding_from_box(self, frame, box):
        if box is None:
            return None

        x, y, w, h = box
        rgb = frame[:, :, ::-1]
        face = rgb[y:y + h, x:x + w]

        if face.size == 0:
            return None

        embedding = self.embedder.embeddings([face])[0]
        embedding = self.normalize(embedding)

        return embedding

    # =================================================
    # RECOGNITION ENGINE (NEW)
    # =================================================

    def recognize(self, embedding):
        """
        Returns:
        {
            "name": str,
            "confidence": float (0–100),
            "raw_score": float
        }
        """

        if embedding is None or not self.data:
            return {
                "name": "Unknown",
                "confidence": 0,
                "raw_score": 0
            }

        best_match = None
        best_score = -np.inf

        for name, info in self.data.items():

            stored_embeddings = info["embeddings"]

            # Vectorized cosine similarity
            scores = np.dot(stored_embeddings, embedding)

            max_score = np.max(scores)

            if max_score > best_score:
                best_score = max_score
                best_match = name

        confidence = round(float(best_score) * 100, 2)

        return {
            "name": best_match,
            "confidence": confidence,
            "raw_score": float(best_score)
        }

    # =================================================
    # USER MANAGEMENT
    # =================================================

    def add_embedding(self, name, embedding):
        if name not in self.data:
            self.data[name] = {
                "embeddings": [],
                "centroid": None
            }

        self.data[name]["embeddings"].append(embedding)

        embeddings = np.array(self.data[name]["embeddings"])
        centroid = np.mean(embeddings, axis=0)
        centroid = self.normalize(centroid)

        self.data[name]["centroid"] = centroid
        self.save_encodings()

    def delete_user(self, name):
        if name in self.data:
            del self.data[name]
            self.save_encodings()