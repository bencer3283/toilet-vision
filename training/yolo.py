from picamera2.devices.imx500 import IMX500, NetworkIntrinsics
from picamera2 import Picamera2
import time

imx500 = IMX500('/usr/share/imx500-models/imx500_network_ssd_mobilenetv2_fpnlite_320x320_pp.rpk')
intrinsics = imx500.network_intrinsics

if not intrinsics:
    intrinsics = NetworkIntrinsics()
    intrinsics.task = 'object detection'
if intrinsics.labels is None:
    with open('coco_labels.txt', mode='r') as lf:
        intrinsics.labels = lf.read().splitlines()
intrinsics.update_with_defaults()
labels = intrinsics.labels

pc = Picamera2(imx500.camera_num)
still_config = pc.create_still_configuration()
pc.start(still_config)

while True:
    with pc.captured_request() as request:
        metadata = request.get_metadata()
        output_tensors = imx500.get_outputs(metadata, add_batch=True)
        boxes, scores, classes = output_tensors[0][0], output_tensors[1][0], output_tensors[2][0]
        detections = [
            {
                'box': box,
                'score': score,
                'category': labels[int(category)]
            }
            for box, score, category in zip(boxes, scores, classes)
            if score > 0.5
        ]
        
        print([d['category'] for d in detections])
        print('\n')
    time.sleep(1)
