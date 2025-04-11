import roboflow
import time
from picamera2 import Picamera2

key = open("keys.txt")

rf = roboflow.Roboflow(api_key=key.readline())
toilet_training = rf.workspace('ben-tnvt9').project('toilet-vision')
# print(toilet_training)

pc = Picamera2()
capture_config = pc.create_still_configuration()
pc.start(show_preview=False)
time.sleep(1)
pc.switch_mode_and_capture_file(capture_config, 'img.jpg')
time.sleep(1)
toilet_training.upload(
    image_path='img.jpg')