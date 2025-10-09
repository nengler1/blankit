import cv2
import os
import numpy as np
from PIL import Image
import face_recognition

def faces_boxes(image_path):
    print("Looking for faces in:", image_path)
    
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
    print("Looking for license plates")

    gray = cv2.cvtColor(image_cv, cv2.COLOR_BGR2GRAY)

    # Load pretrained OpenCV cascade for license plate detection
    plate_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_russian_plate_number.xml')

    # Detect license plates
    plates = plate_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=4, minSize=(30,30))

    print("Found", len(plates), "plate(s)")

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

def blur_faces(image_cv, face_coords, blur_strength=50):
    for (top_left, bottom_right) in face_coords:
        (left, top) = top_left
        (right, bottom) = bottom_right
        face_region = image_cv[top:bottom, left:right]
        blurred_face = cv2.blur(face_region, (blur_strength, blur_strength))
        image_cv[top:bottom, left:right] = blurred_face
    return image_cv

MODEL_TYPE = 'hog'  # or 'cnn' for GPU acceleration

IMG_PATH = os.getcwd() + "\\images\\group_test.jpg"

faces_img, face_coords = faces_boxes(IMG_PATH)
output_image, plate_coords = plates_boxes(faces_img)

output_image = blur_faces(output_image, face_coords, 200)

resized = resize_image(output_image, 800)
cv2.imshow("Detections", resized)
cv2.waitKey(0)
cv2.destroyAllWindows()