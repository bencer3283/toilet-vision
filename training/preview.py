from picamera2 import Picamera2, Preview

ssh = False

pc = Picamera2()
sensor_mode = pc.sensor_modes[1]
pc.options["quality"] = 95
pc.options["compress_level"] = 1
preview_config = pc.create_preview_configuration()
still_config = pc.create_still_configuration(
    main={'format': 'BGR888', 'size': (4056, 3040)},
    sensor={'output_size': sensor_mode['size'], 'bit_depth': sensor_mode['bit_depth']},
    lores={'size': (1014, 760)},
    display='lores',
    controls={
        'AwbEnable': True,
        'AeMeteringMode': 0, # centre weighted
        'AeConstraintMode': 1, # highlight
        'AeExposureMode': 1, # short
        'Contrast': 3,
        'Brightness': -0.67,
        'Sharpness': 1.5
    })
pc.configure(still_config)
pc.start_preview(preview=Preview.QT if ssh else Preview.QTGL)
pc.start()
while True:
    pass