import cv2
import numpy as np
import tensorflow as tf
from mtcnn import MTCNN
from keras_facenet import FaceNet

print("OpenCV:", cv2.__version__)
print("NumPy:", np.__version__)
print("TensorFlow:", tf.__version__)

detector = MTCNN()
embedder = FaceNet()

print("MTCNN + FaceNet loaded successfully.")