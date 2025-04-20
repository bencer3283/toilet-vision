from ultralytics import YOLO

# Load a YOLOV8n PyTorch model
model = YOLO('best.pt')

# Export the model
model.export(format="imx", data='/home/ben/Documents/toilet-vision/conversion/dataset/data.yaml')  # exports with PTQ quantization by default

# Load the exported model
imx_model = YOLO("yolo8n_imx_model")

# Run inference
results = imx_model('img/*.jpg')

for i, result in enumerate(results):
    boxes = result.boxes  # Boxes object for bounding box outputs
    masks = result.masks  # Masks object for segmentation masks outputs
    keypoints = result.keypoints  # Keypoints object for pose outputs
    probs = result.probs  # Probs object for classification outputs
    obb = result.obb  # Oriented boxes object for OBB outputs
    print(boxes)
    # result.show()  # display to screen
    # result.save(filename="/Users/poshengcheng/Documents/Spring 25/Grad Studio/toilet-vision-training/img/predicted/{i}.jpg")  # save to disk