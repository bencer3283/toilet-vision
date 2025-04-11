from picamera2 import Picamera2, Preview
import time
import io

ssh = False

bytes = io.BytesIO()

def capture_complete(job):
    print(job)
    with open('img.jpg', mode='wb') as f:
        f.write(bytes.getbuffer())

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
        'AwbEnable': True,
        'AeMeteringMode': 0,
        'AeConstraintMode': 1
    })
pc.configure(still_config)
pc.start_preview(preview=Preview.QT if ssh else Preview.QTGL)
pc.start()
print(still_config['main'])
while True:
    pc.capture_file(name='main', file_output=bytes, format='jpeg', signal_function=capture_complete, wait=False)
    time.sleep(5)