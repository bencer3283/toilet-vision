from picamera2 import Picamera2, Preview
from libcamera import controls
from threading import Thread, Event
import time
import io
import roboflow
import queue as q
import os
import adafruit_pixelbuf
import board
from adafruit_led_animation.helper import PixelSubset
from adafruit_raspberry_pi5_neopixel_write import neopixel_write

ssh = False
rf_batch_name = 'neopixel-illumination-fast-pull'

NEOPIXEL = board.D12
num_pixels = 24

class Pi5Pixelbuf(adafruit_pixelbuf.PixelBuf):
    def __init__(self, pin, size, **kwargs):
        self._pin = pin
        super().__init__(size=size, **kwargs)

    def _transmit(self, buf):
        neopixel_write(self._pin, buf)

pixels = Pi5Pixelbuf(NEOPIXEL, num_pixels, auto_write=True, byteorder="GRB", brightness=0.6)
glow_subset_0 = PixelSubset(pixels, 1, 8)
glow_subset_1 = PixelSubset(pixels, 17, 24)
lamp_subset = PixelSubset(pixels, 9, 16)

byte_queue = q.Queue(maxsize=-1)
file_queue = q.Queue(maxsize=-1)
quit = Event()

class UploadThread(Thread):
    def run(self):
        keys = dict()
        keys_file = open('keys.txt', mode='r')
        keys_file_line = keys_file.readline()
        while(keys_file_line != ''):
            keys.update({
                keys_file_line.split('=')[0]: keys_file_line.split('=')[1]
            })
            keys_file_line = keys_file.readline()

        rf = roboflow.Roboflow(api_key=keys['roboflow'])
        toilet_training = rf.workspace('ben-tnvt9').project('toilet-vision')
        while not quit.is_set():
            if not file_queue.empty():
                file_path = file_queue.get()
                print('uploading: '+file_path)
                toilet_training.upload(image_path=file_path, batch_name=rf_batch_name, num_retry_uploads=2)
                os.remove(file_path)
                byte_queue.task_done()
                file_queue.task_done()


def capture_complete(job):
    n = hash(job) + time.clock_gettime_ns(time.CLOCK_MONOTONIC)
    print(n)
    with open(str(n)+'.jpg', mode='wb') as f:
        f.write(byte_queue.get().getbuffer())
        file_queue.put(str(n)+'.jpg')

pc = Picamera2()
sensor_mode = pc.sensor_modes[1]
pc.options["quality"] = 95
pc.options["compress_level"] = 1
pccontrol = {
        #'FrameDurationLimits':  (),
        'FrameRate': 30,
        'AwbEnable': True,
        'AeMeteringMode': controls.AeMeteringModeEnum.CentreWeighted, # 0 centre weighted
        'AeConstraintMode': controls.AeConstraintModeEnum.Highlight, # 1 highlight
        'AeExposureMode': controls.AeExposureModeEnum.Short, # 1 short
        'Contrast': 3.2,
        'ExposureValue': -1.3,
        'Sharpness': 1.5
    }
preview_config = pc.create_preview_configuration(controls=pccontrol)
still_config = pc.create_still_configuration(
    main={'format': 'BGR888', 'size': (4056, 3040)},
    sensor={'output_size': sensor_mode['size'], 'bit_depth': sensor_mode['bit_depth']},
    lores={'size': (1014, 760)},
    display='lores',
    controls=pccontrol
)
pc.configure(preview_config)
pc.start_preview(preview=Preview.QT if ssh else Preview.QTGL)
pc.start()
# print(still_config['main'])

upload = UploadThread()
upload.start()

pixels.fill(0)
lamp_subset.fill((255, 255, 180))
pixels.show()

n = 0
while n < 30:
    n += 1
    bytes = io.BytesIO()
    pc.capture_file(name='main', file_output=bytes, format='jpeg', signal_function=capture_complete, wait=False)
    byte_queue.put(bytes)
    time.sleep(0.33)
pixels.fill(0)
pixels.show()
byte_queue.join()
file_queue.join()
quit.set()
pc.stop_preview()
pc.stop()
