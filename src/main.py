import cv2
import os
import numpy as np

from ultralytics import YOLO
from face import face_predict

from transformers import YolosForObjectDetection, YolosImageProcessor
from license import license_predict

FACE_MODEL_PATH = os.getcwd() + '/models/yolov8n-face.pt'
LICENSE_MODEL_PATH = os.getcwd() + '/models/yolos-license'
IMG_PATH = os.getcwd() + "/images/f_and_l.jpg"

img = cv2.imread(IMG_PATH)
img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

yolo_face_md = YOLO(FACE_MODEL_PATH)
license_feature_extractor = YolosImageProcessor.from_pretrained(LICENSE_MODEL_PATH)
license_model = YolosForObjectDetection.from_pretrained(LICENSE_MODEL_PATH)

face_image = face_predict(yolo_face_md, img)
face_arr = np.array(face_image)

output_image = license_predict(face_arr, img_rgb, license_feature_extractor, license_model)

cv2.imshow("Detections", output_image)
cv2.waitKey(0)
cv2.destroyAllWindows()
