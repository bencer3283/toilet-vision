from picamera2.devices.imx500 import IMX500
from picamera2 import Picamera2
import time

imx500 = IMX500('/usr/share/imx500-models/imx500_network_ssd_mobilenetv2_fpnlite_320x320_pp.rpk')

pc = Picamera2(imx500.camera_num)
still_config = pc.create_still_configuration()
pc.start(still_config)

while True:
    with pc.captured_request() as request:
        metadata = request.get_metadata()
        output_tensors = imx500.get_outputs(metadata)
        boxes, scores, classes = output_tensors[0][0], output_tensors[1][0], output_tensors[2][0]
        print(boxes)
        print(scores)
        print(classes)
    time.sleep(3)
