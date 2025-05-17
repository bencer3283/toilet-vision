from picamera2 import Picamera2, Preview
from libcamera import controls
import adafruit_pixelbuf
import board
from adafruit_led_animation.helper import PixelSubset
from adafruit_raspberry_pi5_neopixel_write import neopixel_write

ssh = False

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

pixels.fill(0)
lamp_subset.fill((255, 255, 150))
pixels.show()

try:
    while True:
        pass
finally:
    pixels.fill(0)
    pixels.show()