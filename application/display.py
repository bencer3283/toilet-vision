# SPDX-FileCopyrightText: 2025 Liz Clark for Adafruit Industries
# SPDX-FileCopyrightText: Adapted from Melissa LeBlanc-Williams's Pi Demo Code
#
# SPDX-License-Identifier: MIT

'''Raspberry Pi Graphics example for the 240x240 Round Display'''

import time
import digitalio
import board
from PIL import Image, ImageDraw, ImageFont
from adafruit_rgb_display import gc9a01a

BORDER = 20
FONTSIZE = 24

cs_pin = digitalio.DigitalInOut(board.CE0)
dc_pin = digitalio.DigitalInOut(board.D25)
reset_pin = digitalio.DigitalInOut(board.D27)

BAUDRATE = 24000000


spi = board.SPI()

disp = gc9a01a.GC9A01A(spi, rotation=0,
    width=240, height=240,
    x_offset=0, y_offset=0,
    cs=cs_pin,
    dc=dc_pin,
    rst=reset_pin,
    baudrate=BAUDRATE,
)

width = disp.width
height = disp.height

# -------TEXT AND SHAPES---------
image1 = Image.new("RGB", (width, height))
draw1 = ImageDraw.Draw(image1)
draw1.ellipse((0, 0, width, height), fill=(0, 255, 0))  # Green background

draw1.ellipse(
    (BORDER, BORDER, width - BORDER - 1, height - BORDER - 1), fill=(170, 0, 136)
)
font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", FONTSIZE)
text = "Hello World!"
(font_width, font_height) = font.getbbox(text)[2], font.getbbox(text)[3]
draw1.text(
    (width // 2 - font_width // 2, height // 2 - font_height // 2),
    text,
    font=font,
    fill=(255, 255, 0),
)

# ------ADABOT JPEG DISPLAY----------
image2 = Image.open("butt.jpg")
image_ratio = image2.width / image2.height
screen_ratio = width / height
scaled_width = width
scaled_height = image2.height * width // image2.width
image2 = image2.resize((scaled_width, scaled_height), Image.BICUBIC)
x = scaled_width // 2 - width // 2
y = scaled_height // 2 - height // 2
image2 = image2.crop((x, y, x + width, y + height))

# ------ADABOT JPEG DISPLAY----------
image3 = Image.open("butt-2.jpg")
image_ratio = image3.width / image3.height
screen_ratio = width / height
scaled_width = width
scaled_height = image3.height * width // image3.width
image3 = image3.resize((scaled_width, scaled_height), Image.BICUBIC)
x = scaled_width // 2 - width // 2
y = scaled_height // 2 - height // 2
image3 = image3.crop((x, y, x + width, y + height))

try:
    while True:
        disp.image(image2)  # show text
        time.sleep(2)
        disp.image(image3)  # show adabot
        time.sleep(2)
finally:
    spi.deinit()
    cs_pin.deinit()
    dc_pin.deinit()
    reset_pin.deinit()
