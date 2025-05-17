from picamera2.devices.imx500 import IMX500, NetworkIntrinsics
from picamera2 import Picamera2
from libcamera import controls
from threading import Thread, Event
import time
import adafruit_pixelbuf
import board
from adafruit_led_animation.helper import PixelSubset
from adafruit_led_animation.color import TEAL
from adafruit_raspberry_pi5_neopixel_write import neopixel_write
import digitalio
from PIL import Image, ImageDraw, ImageFont
from adafruit_rgb_display import gc9a01a

# ---parameters---
# color_init = (230, 20, 17)
color_init = (100, 180, 30)
# color_target = (100, 180, 30)
color_target = (230, 20, 17)
color = color_init
blocks = 0
avg = 21

# ---picamera---
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
pccontrol = {
        #'FrameDurationLimits':  (),
        'FrameRate': 20,
        'AwbEnable': True,
        'AeMeteringMode': controls.AeMeteringModeEnum.CentreWeighted, # 0 centre weighted
        'AeConstraintMode': controls.AeConstraintModeEnum.Highlight, # 1 highlight
        'AeExposureMode': controls.AeExposureModeEnum.Short, # 1 short
        'Contrast': 3.2,
        'ExposureValue': -1.3,
        'Sharpness': 1.5
    }
still_config = pc.create_still_configuration()
preview_config = pc.create_preview_configuration(controls=pccontrol, buffer_count=12)
imx500.show_network_fw_progress_bar()
pc.start(preview_config, show_preview=False)

# ---neopixel---
class Pi5Pixelbuf(adafruit_pixelbuf.PixelBuf):
    def __init__(self, pin, size, **kwargs):
        self._pin = pin
        super().__init__(size=size, **kwargs)

    def _transmit(self, buf):
        neopixel_write(self._pin, buf)

pixels = Pi5Pixelbuf(board.D12, 24, auto_write=True, byteorder="GRB", brightness=0.6)
glow_subset_0 = PixelSubset(pixels, 0, 7)
glow_subset_1 = PixelSubset(pixels, 16, 23)
lamp_subset = PixelSubset(pixels, 8, 15)

# ---display---
# BORDER = 20
# FONTSIZE = 24

# cs_pin = digitalio.DigitalInOut(board.CE0)
# dc_pin = digitalio.DigitalInOut(board.D25)
# reset_pin = digitalio.DigitalInOut(board.D27)

# BAUDRATE = 24000000
# spi = board.SPI()

# disp = gc9a01a.GC9A01A(spi, rotation=0,
#     width=240, height=240,
#     x_offset=0, y_offset=0,
#     cs=cs_pin,
#     dc=dc_pin,
#     rst=reset_pin,
#     baudrate=BAUDRATE,
# )

# width = disp.width
# height = disp.height

# def drawJpg(path):
#     img = Image.open(path)
#     image_ratio = img.width / img.height
#     screen_ratio = width / height
#     scaled_width = width
#     scaled_height = img.height * width // img.width
#     img = img.resize((scaled_width, scaled_height), Image.BICUBIC)
#     x = scaled_width // 2 - width // 2
#     y = scaled_height // 2 - height // 2
#     img = img.crop((x, y, x + width, y + height))
#     return img

# ---threads---
quit = Event()
fire = Event()

class LEDThread(Thread):
    def run(self):
        while not quit.is_set():
            if fire.is_set():
                stops = color
                for i in range(5):
                    stops = tuple(int(x*0.7) for x in stops)
                    glow_subset_0.fill(stops)
                    glow_subset_1.fill(stops)
                    pixels.show()
                    time.sleep(0.05)
                for i in range(5):
                    stops = tuple(int(x*1.4) for x in stops)
                    glow_subset_0.fill(stops)
                    glow_subset_1.fill(stops)
                    pixels.show()
                    time.sleep(0.05)
                fire.clear()
                time.sleep(0.05)
                glow_subset_0.fill(color)
                glow_subset_1.fill(color)
                pixels.show()
                
# class DisplayThread(Thread):
#     def run(self):
#         while not quit.is_set():
#             disp.image(drawJpg('./screen-wipe/0.jpg'))
#             if fire.is_set():
#                 n = blocks // 7
#                 disp.image(drawJpg('./screen-wipe/' + str(n) + '.jpg'))

# ---main---
LED = LEDThread(args=fire)
LED.start()
# screen = DisplayThread()
# screen.run()
pixels.fill(color_init)
lamp_subset.fill((255, 255, 150))
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
                    if score > 0.2
                ]
                
                # print([(d['category'], d['score'], d['box'][0]) for d in detections])
                
                previous_seam = seam_in_frame
                if len(detections) > 0 and detections[0]['category'] == 'seam':
                    count_out = 0
                    count_in += 1
                    # print(count_in)
                    if count_in >= 1:
                        seam_in_frame = True
                        count_in = 0
                else:
                    count_in = 0
                    count_out += 1
                    if count_out >= 1:
                        seam_in_frame = False
                        count_out = 0
                # print(str(seam_in_frame)+'\n')
                if seam_in_frame != previous_seam and seam_in_frame: # and detections[0]['box'][0] > 250:
                    # print('fire')
                    blocks += 1
                    color = (int(color_init[0]+blocks/avg*(color_target[0]-color_init[0])), int(color_init[1]+blocks/avg*(color_target[1]-color_init[1])), int(color_init[2]+blocks/avg*(color_target[2]-color_init[2])))
                    fire.set()
                    time.sleep(0.05)
                    

        # time.sleep(0.1)
finally:
    time.sleep(.02)
    quit.set()
    pixels.fill(0)
    pixels.show()
    # spi.deinit()
    # cs_pin.deinit()
    # dc_pin.deinit()
    # reset_pin.deinit()
