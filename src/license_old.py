# NOT USED ANYMORE

import torch
import cv2

def license_predict(img, img_rgb, fe, model):
    inputs = fe(images=img_rgb, return_tensors="pt")
    outputs = model(**inputs)
    img_size = torch.tensor([img_rgb.shape[:2]])
    processed_outputs = fe.post_process_object_detection(outputs, threshold=0.0, target_sizes=img_size)

    output_dict = processed_outputs[0]

    res_coords = []

    keep = output_dict['scores'] > 0.5
    boxes = output_dict['boxes'][keep].tolist()
    scores = output_dict['scores'][keep].tolist()
    labels = output_dict['labels'][keep].tolist()

    for score, (xmin, ymin, xmax, ymax), label in zip(scores, boxes, labels):
        pt1 = (int(xmin), int(ymin))
        pt2 = (int(xmax), int(ymax))

        cv2.rectangle(img, pt1, pt2, (0, 255, 0), 2)
        
        text = f'{model.config.id2label[label]}: {score:.2f}'
        cv2.putText(img, text, 
                            (int(xmin), int(ymin)-10), 
                            cv2.FONT_HERSHEY_SIMPLEX, 
                            0.7, (0,255,0), 2)
        
        res_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

        res_coords.append([pt1, pt2])

    print(len(res_coords), "License(s) detected")
    return res_img, res_coords