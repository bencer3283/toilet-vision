from picamera2.devices.imx500 import IMX500, NetworkIntrinsics
from picamera2 import Picamera2
from libcamera import controls
from threading import Thread, Event
import time
import adafruit_pixelbuf
import board
from adafruit_led_animation.animation.pulse import Pulse
from adafruit_led_animation.sequence import AnimateOnce
from adafruit_led_animation.color import TEAL
from adafruit_raspberry_pi5_neopixel_write import neopixel_write

# color_init = (230, 20, 17)
color_init = (100, 180, 30)
# color_target = (100, 180, 30)
color_target = (230, 20, 17)
color = color_init
blocks = 0

class Pi5Pixelbuf(adafruit_pixelbuf.PixelBuf):
    def __init__(self, pin, size, **kwargs):
        self._pin = pin
        super().__init__(size=size, **kwargs)

    def _transmit(self, buf):
        neopixel_write(self._pin, buf)

pixels = Pi5Pixelbuf(board.D12, 8, auto_write=True, byteorder="GRB", brightness=0.6)
pulse = Pulse(pixels, 0.025, (210, 33, 10), period=0.4, breath=0.05, min_intensity=0.1, max_intensity=0.8) 
animation = AnimateOnce(pulse)

quit = Event()
fire = Event()

class LEDThread(Thread):
    def run(self):
        while not quit.is_set():
            if fire.is_set():
                stops = color
                for i in range(5):
                    stops = tuple(int(x*0.7) for x in stops)
                    pixels.fill(stops)
                    pixels.show()
                    time.sleep(0.05)
                for i in range(5):
                    stops = tuple(int(x*1.4) for x in stops)
                    pixels.fill(stops)
                    pixels.show()
                    time.sleep(0.05)
                fire.clear()
                time.sleep(0.05)
                pixels.fill(color)
                pixels.show()
                


imx500 = IMX500('../imx500pkg/network.rpk')
intrinsics = imx500.network_intrinsics

if not intrinsics:
    intrinsics = NetworkIntrinsics()
    intrinsics.task = 'object detection'
if intrinsics.labels is None:
    with open('../imx500pkg/labels.txt', mode='r') as lf:
        intrinsics.labels = lf.read().splitlines()
intrinsics.update_with_defaults()
labels = intrinsics.labels

pc = Picamera2(imx500.camera_num)
still_config = pc.create_still_configuration()
preview_config = pc.create_preview_configuration(
    controls={
            'FrameRate': 17,
            'AwbEnable': True,
            'AeMeteringMode': controls.AeMeteringModeEnum.CentreWeighted, # 0 centre weighted
            'AeConstraintMode': controls.AeConstraintModeEnum.Highlight, # 1 highlight
            'AeExposureMode': controls.AeExposureModeEnum.Short, # 1 short
            'Contrast': 2,
            'Brightness': -0.7,
            'Sharpness': 1.5
            },
        buffer_count=12
)
imx500.show_network_fw_progress_bar()
pc.start(preview_config, show_preview=False)

LED = LEDThread(args=fire)
LED.start()
pixels.fill(color_init)
pixels.show()

try:
    count_in = 0
    count_out = 0
    seam_in_frame = False
    while True:
        with pc.captured_request(flush=True) as request:
            metadata = request.get_metadata()
            output_tensors = imx500.get_outputs(metadata, add_batch=True)
            if (output_tensors != None):
                boxes, scores, classes = output_tensors[0][0], output_tensors[1][0], output_tensors[2][0]
                detections = [
                    {
                        'box': box,
                        'score': score,
                        'category': labels[int(category)]
                    }
                    for box, score, category in zip(boxes, scores, classes)
                    if score > 0.0
                ]
                
                print([(d['category'], d['box'][0]) for d in detections])
                
                # if (len(detections) > 0 and detections[0]['category'] == 'seam' and detections[0]['box'][0] < 600 and detections[0]['box'][0] > 400):
                #     print('one')
                #     print('\n')
                #     while animation.animate():
                #         pass
                #     animation.reset()
                #     pixels.fill(0)
                #     pixels.show()
                #     time.sleep(0.4)
                
                previous_seam = seam_in_frame
                if len(detections) > 0 and detections[0]['category'] == 'seam':
                    count_out = 0
                    count_in += 1
                    print(count_in)
                    if count_in >= 3:
                        seam_in_frame = True
                        count_in = 0
                else:
                    count_in = 0
                    count_out += 1
                    if count_out >= 3:
                        seam_in_frame = False
                        count_out = 0
                print(str(seam_in_frame)+'\n')
                if seam_in_frame != previous_seam and seam_in_frame: # and detections[0]['box'][0] > 250:
                    print('fire')
                    blocks += 1
                    color = (int(color_init[0]+blocks/15*(color_target[0]-color_init[0])), int(color_init[1]+blocks/15*(color_target[1]-color_init[1])), int(color_init[2]+blocks/15*(color_target[2]-color_init[2])))
                    fire.set()
                    time.sleep(0.5)
                    

        # time.sleep(0.1)
finally:
    time.sleep(.02)
    pixels.fill(0)
    pixels.show()
    quit.set()
