# NOT USED ANYMORE

# load libraries
from PIL import Image
import cv2

def face_predict(model, img):
    # run model on the PIL image
    output = model.predict(img, verbose=False)

    res_coords = []
    if output:
        for bbox in output:
            for idx, points in enumerate(bbox):
                points = points.to("cpu")

                coords = points.boxes.xyxy[0]
                prob = points.boxes.conf[0]

                xmin, ymin, xmax, ymax = map(int, coords)

                pt1 = (int(xmin), int(ymin))
                pt2 = (int(xmax), int(ymax))

                cv2.rectangle(img, pt1, pt2, (0, 255, 0), 2)

                cv2.putText(img, f"{prob:.2f}", 
                            (xmin, ymin - 10), 
                            cv2.FONT_HERSHEY_SIMPLEX, 
                            0.9, (0,255,0), 2)
                
                res_coords.append([pt1, pt2])

        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

        pil_image = Image.fromarray(img_rgb)

        print(len(res_coords), "Face(s) detected")
        return pil_image, res_coords
