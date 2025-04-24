import time

import adafruit_pixelbuf
import board
from adafruit_led_animation.animation.rainbow import Rainbow
from adafruit_led_animation.animation.rainbowchase import RainbowChase
from adafruit_led_animation.animation.rainbowcomet import RainbowComet
from adafruit_led_animation.animation.rainbowsparkle import RainbowSparkle
from adafruit_led_animation.animation.pulse import Pulse
from adafruit_led_animation.animation.colorcycle import ColorCycle
from adafruit_led_animation.helper import PixelSubset
from adafruit_led_animation.sequence import AnimationSequence, AnimateOnce
from adafruit_led_animation.group import AnimationGroup
from adafruit_raspberry_pi5_neopixel_write import neopixel_write

NEOPIXEL = board.D18
num_pixels = 8

class Pi5Pixelbuf(adafruit_pixelbuf.PixelBuf):
    def __init__(self, pin, size, **kwargs):
        self._pin = pin
        super().__init__(size=size, **kwargs)

    def _transmit(self, buf):
        neopixel_write(self._pin, buf)

pixels = Pi5Pixelbuf(NEOPIXEL, num_pixels, auto_write=True, byteorder="BRG", brightness=0.6)
glow_subset = PixelSubset(pixels, 1, 7)

rainbow = Rainbow(pixels, speed=0.02, period=2)
rainbow_chase = RainbowChase(pixels, speed=0.02, size=5, spacing=3)
rainbow_comet = RainbowComet(pixels, speed=0.02, tail_length=7, bounce=True)
rainbow_sparkle = RainbowSparkle(pixels, speed=0.02, num_sparkles=15)
pulse = Pulse(glow_subset, 0.025, (210, 33, 10), period=0.4, breath=0.05, min_intensity=0.1, max_intensity=0.8) 
color_cycle = ColorCycle(glow_subset, speed=0.8, colors=[(210, 33, 10), (62, 9, 3), (7, 250, 117), (0, 0, 0)])

animations = AnimationSequence(
    rainbow,
    rainbow_chase,
    rainbow_comet,
    rainbow_sparkle,
    pulse,
    advance_interval=5,
    auto_clear=True,
)

animation = AnimateOnce(pulse)

# while animation.animate():
#     pass

glow_subset.fill((210, 33, 10))
pixels.show()
time.sleep(1)
glow_subset.fill(0)
pixels.show()

# try:
#     while True:
#         # animations.animate()
#         # pulse.animate()
        
# finally:
#     time.sleep(.02)
#     pixels.fill(0)
#     pixels.show()