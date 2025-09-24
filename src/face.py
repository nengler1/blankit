# load libraries

from PIL import Image
import cv2

def face_predict(model, img):
    # run model on the PIL image
    output = model.predict(img, verbose=False)

    if output:
        for bbox in output:
            for idx, points in enumerate(bbox):
                points = points.to("cpu")

                coords = points.boxes.xyxy[0]

                xmin, ymin, xmax, ymax = map(int, coords)

                xmin = int(xmin)
                ymin = int(ymin)
                xmax = int(xmax)
                ymax = int(ymax)

                prob = points.boxes.conf[0]

                cv2.rectangle(img, (xmin, ymin), (xmax, ymax), (0, 255, 0), 2)

                cv2.putText(img, f"{prob:.2f}", 
                            (xmin, ymin - 10), 
                            cv2.FONT_HERSHEY_SIMPLEX, 
                            0.9, (0,255,0), 2)

        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

        pil_image = Image.fromarray(img_rgb)
        return pil_image
