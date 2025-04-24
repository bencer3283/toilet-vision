from picamera2 import Picamera2, Preview
from libcamera import controls
from threading import Thread, Event
import time
import io
import roboflow
import queue as q
import os

ssh = False
rf_batch_name = 'one-led'

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
# print(sensor_mode)
preview_config = pc.create_preview_configuration()
still_config = pc.create_still_configuration(
    main={'format': 'BGR888', 'size': (4056, 3040)},
    sensor={'output_size': sensor_mode['size'], 'bit_depth': sensor_mode['bit_depth']},
    lores={'size': (1014, 760)},
    display='lores',
    controls={
        #'FrameDurationLimits':  (),
        'FrameRate': 15,
        'AwbEnable': True,
        'AeMeteringMode': controls.AeMeteringModeEnum.CentreWeighted, # 0 centre weighted
        'AeConstraintMode': controls.AeConstraintModeEnum.Highlight, # 1 highlight
        'AeExposureMode': controls.AeExposureModeEnum.Short, # 1 short
        'Contrast': 3.2,
        'ExposureValue': -1.7,
        'Sharpness': 1.5
    }
)
pc.configure(still_config)
pc.start_preview(preview=Preview.QT if ssh else Preview.QTGL)
pc.start()
# print(still_config['main'])

upload = UploadThread()
upload.start()

n = 0
while n < 15:
    n += 1
    bytes = io.BytesIO()
    pc.capture_file(name='main', file_output=bytes, format='jpeg', signal_function=capture_complete, wait=False)
    byte_queue.put(bytes)
    time.sleep(0.33)
byte_queue.join()
file_queue.join()
quit.set()
pc.stop_preview()
pc.stop()