import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import numpy as np
import cv2

INPUT_IMG = 'images/image.png'
MODEL_FILE = 'models/detector.tflite'

base_options = python.BaseOptions
face_detector = vision.FaceDetector
face_detector_options = vision.FaceDetectorOptions
vision_running_mode = vision.RunningMode

orignal_image = cv2.imread(INPUT_IMG)
image = cv2.resize(orignal_image, (0, 0), fx=0.5, fy=0.5, interpolation=cv2.INTER_LINEAR)

mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=image)

options = face_detector_options(
    base_options=base_options(model_asset_path=MODEL_FILE),
    running_mode=vision_running_mode.IMAGE,
    min_detection_confidence=0.5
)

with face_detector.create_from_options(options) as face_detection:
    results = face_detection.detect(mp_image)

    if results and results.detections:
        h_img, w_img = image.shape[:2]
        for detection in results.detections:
            # Tasks API detection has a bounding_box attribute (not location_data)
            bbox = detection.bounding_box

            # Extract bbox values (handle both normalized [0..1] or absolute pixel coords)
            ox, oy, bw, bh = bbox.origin_x, bbox.origin_y, bbox.width, bbox.height

            # If values look normalized (<= 1), convert to pixel coords
            if 0.0 <= ox <= 1.0 and 0.0 <= oy <= 1.0 and 0.0 <= bw <= 1.0 and 0.0 <= bh <= 1.0:
                x1 = int(ox * w_img)
                y1 = int(oy * h_img)
                x2 = int((ox + bw) * w_img)
                y2 = int((oy + bh) * h_img)
            else:
                x1 = int(ox)
                y1 = int(oy)
                x2 = int(ox + bw)
                y2 = int(oy + bh)

            # Draw keypoints (if present)
            kp_list = []
            for kp in detection.keypoints:
                # Normalize keypoint coordinates to image pixels if needed
                if 0.0 <= kp.x <= 1.0 and 0.0 <= kp.y <= 1.0:
                    kp_x = int(kp.x * w_img)
                    kp_y = int(kp.y * h_img)
                else:
                    kp_x = int(kp_x)
                    kp_y = int(kp_y)

                kp_list.append((kp_x, kp_y))
                # Draw keypoint
                color, thickness, radius = (255, 127, 0), 2, 3
                cv2.circle(image, (kp_x, kp_y),
                        thickness=thickness, 
                        color=color, 
                        radius=radius)
                
            if len(kp_list) >= 3:
                pts = np.array(kp_list, dtype=np.int32)
                hull = cv2.convexHull(pts)
                cv2.polylines(image, [hull], isClosed=True, color=(255, 127, 0), thickness=2)

            # Draw rectangle and confidence in top left
            cv2.rectangle(image, (x1, y1), (x2, y2), (0, 255, 0), 2)
            score = detection.categories[0].score if detection.categories else None

            if score:
                cv2.putText(image, f"{score:.2f}", (x1, max(y1 - 6, 0)),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

#sized_image = cv2.resize(image, (0, 0), fx=0.2, fy=0.2, interpolation=cv2.INTER_LINEAR)
cv2.imshow('Face Detection', image)
cv2.waitKey(0)
cv2.destroyAllWindows()