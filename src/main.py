import cv2
import os
import numpy as np
from PIL import Image
import face_recognition

def faces_boxes(image_path):
    image = face_recognition.load_image_file(image_path)

    # Detect face locations
    face_locations = face_recognition.face_locations(image, model=MODEL_TYPE)

    print("Found", len(face_locations), "face(s)")

    # Convert to OpenCV image
    image_cv = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

    # Draw boxes around faces
    boxes = []
    for (top, right, bottom, left) in face_locations:
        boxes.append(((left, top), (right, bottom)))
        cv2.rectangle(image_cv, (left, top), (right, bottom), (0, 255, 0), 2)

    return image_cv, boxes

def plates_boxes(image_cv):
    gray = cv2.cvtColor(image_cv, cv2.COLOR_BGR2GRAY)

    # Load pretrained OpenCV cascade for license plate detection
    plate_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_russian_plate_number.xml')

    # Detect license plates
    plates = plate_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=4, minSize=(30,30))

    print("Found", len(plates), "face(s)")

    # Using coords, draw boxes around plates
    boxes = []
    for (x, y, w, h) in plates:
        boxes.append(((x, y), (x+w, y+h)))
        cv2.rectangle(image_cv, (x, y), (x+w, y+h), (255, 0, 0), 2)

    return image_cv, boxes

# Resize image for better display
def resize_image(image, width):
    aspect_ratio = image.shape[1] / image.shape[0]
    new_height = int(width / aspect_ratio)
    resized_image = cv2.resize(image, (width, new_height))
    return resized_image

MODEL_TYPE = 'hog'  # or 'cnn' for GPU acceleration

IMG_PATH = os.getcwd() + "/images/2.jpg"

faces_img, face_coords = faces_boxes(IMG_PATH)
output_image, plate_coords = plates_boxes(faces_img)

resized = resize_image(output_image, 800)
cv2.imshow("Detections", resized)
cv2.waitKey(0)
cv2.destroyAllWindows()