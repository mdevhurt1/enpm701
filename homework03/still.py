import time
from picamera2 import Picamera2

# Initialize the camera
picam2 = Picamera2()

# Configure the camera
camera_config = picam2.create_still_configuration()
picam2.configure(camera_config)
picam2.start()

# Wait for 2 seconds to allow the camera to adjust
time.sleep(2)

# Capture the image
picam2.capture_file("reference.jpg")
picam2.stop()
