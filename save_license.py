from transformers import YolosForObjectDetection, YolosFeatureExtractor
import torch
import cv2

image = cv2.imread("images/f_and_l.jpg")
image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
feature_extractor = YolosFeatureExtractor.from_pretrained('models/yolos-license')
model = YolosForObjectDetection.from_pretrained('models/yolos-license')

inputs = feature_extractor(images=image_rgb, return_tensors="pt")
outputs = model(**inputs)
img_size = torch.tensor([image_rgb.shape[:2]])
processed_outputs = feature_extractor.post_process(outputs, img_size)

output_dict = processed_outputs[0]

keep = output_dict['scores'] > 0.5
boxes = output_dict['boxes'][keep].tolist()
scores = output_dict['scores'][keep].tolist()
labels = output_dict['labels'][keep].tolist()

for score, (xmin, ymin, xmax, ymax), label in zip(scores, boxes, labels):
    pt1 = (int(xmin), int(ymin))
    pt2 = (int(xmax), int(ymax))
    cv2.rectangle(image, pt1, pt2, (0, 255, 0), 2)
    text = f'{model.config.id2label[label]}: {score:.2f}'
    cv2.putText(image, text, 
                        (int(xmin), int(ymin)-10), 
                        cv2.FONT_HERSHEY_SIMPLEX, 
                        0.7, (0,255,0), 2)
    

cv2.imshow("Detections", image)
cv2.waitKey(0)
cv2.destroyAllWindows()