import os
import numpy as np
import cv2
import tensorflow as tf
from tensorflow.keras import layers, models
from tensorflow.keras.preprocessing.image import ImageDataGenerator

DATASET_DIR = "eye_dataset"
IMG_SIZE = 24

def load_data():
    images = []
    labels = []

    for label_name, label_value in [("open", 0), ("closed", 1)]:
        folder = os.path.join(DATASET_DIR, label_name)
        for filename in os.listdir(folder):
            path = os.path.join(folder, filename)

            img = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
            if img is None:
                continue

            img = cv2.resize(img, (IMG_SIZE, IMG_SIZE))
            img = img / 255.0
            images.append(img)
            labels.append(label_value)

    images = np.array(images)
    labels = np.array(labels)

    images = images.reshape(-1, IMG_SIZE, IMG_SIZE, 1)

    return images, labels


print("Loading dataset...")
X, y = load_data()
print("Dataset shape:", X.shape)

# Shuffle
indices = np.arange(len(X))
np.random.shuffle(indices)
X = X[indices]
y = y[indices]

# Train-test split
split = int(0.8 * len(X))
X_train, X_test = X[:split], X[split:]
y_train, y_test = y[:split], y[split:]

# ---- Manual Class Weights ----
open_count = np.sum(y_train == 0)
closed_count = np.sum(y_train == 1)
total = len(y_train)

weight_for_open = total / (2 * open_count)
weight_for_closed = total / (2 * closed_count)

class_weights = {
    0: weight_for_open,
    1: weight_for_closed
}

print("Class Weights:", class_weights)

# Augmentation
datagen = ImageDataGenerator(
    rotation_range=10,
    width_shift_range=0.1,
    height_shift_range=0.1,
    zoom_range=0.1
)

datagen.fit(X_train)

# Model
model = models.Sequential([
    layers.Conv2D(32, (3,3), activation='relu', input_shape=(24,24,1)),
    layers.MaxPooling2D(2,2),

    layers.Conv2D(64, (3,3), activation='relu'),
    layers.MaxPooling2D(2,2),

    layers.Flatten(),
    layers.Dense(64, activation='relu'),
    layers.Dropout(0.4),
    layers.Dense(1, activation='sigmoid')
])

model.compile(
    optimizer='adam',
    loss='binary_crossentropy',
    metrics=['accuracy']
)

print("Training...")
model.fit(
    datagen.flow(X_train, y_train, batch_size=32),
    epochs=20,
    validation_data=(X_test, y_test),
    class_weight=class_weights
)

print("Evaluating...")
loss, acc = model.evaluate(X_test, y_test)
print("Final Test Accuracy:", acc)

model.save("eye_model.h5")
print("Model saved as eye_model.h5")