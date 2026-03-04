import RPi.GPIO as gpio
import time
import numpy as np
import cv2
import imutils
import os
from picamera2 import Picamera2

# Define pin allocations
trig = 16
echo = 18

def distance(timeout_s=0.02):
  gpio.setmode(gpio.BOARD)
  gpio.setup(trig, gpio.OUT)
  gpio.setup(echo, gpio.IN)

  # Ensure output has no value
  gpio.output(trig, False)
  time.sleep(0.01)

  # Generate trigger pulse
  gpio.output(trig, True)
  time.sleep(0.00001)
  gpio.output(trig, False)

  start_wait = time.monotonic()
  while gpio.input(echo) == 0:
    if time.monotonic() - start_wait > timeout_s:
      gpio.cleanup()
      return None  # no echo start

  pulse_start = time.monotonic()

  while gpio.input(echo) == 1:
    if time.monotonic() - pulse_start > timeout_s:
      gpio.cleanup()
      return None  # echo stuck high / too long

  pulse_end = time.monotonic()

  pulse_duration = pulse_end - pulse_start
  dist_cm = round(pulse_duration * 17150, 2)

  gpio.cleanup()
  return dist_cm

# Initialize the camera
picam2 = Picamera2()

# Configure the camera for preview
camera_config = picam2.create_still_configuration()
picam2.configure(camera_config)
picam2.start()

# Wait for 2 seconds to allow the camera to adjust
time.sleep(2)

# Capture the image
picam2.capture_file("lecture4inclass.jpg")
picam2.stop()

# Record 10 successive distance measurements from the RPi to the object
ranges = []
for i in range(10):
  d = distance()
  if d is None:
    print("no echo (timeout)")
  else:
    ranges.append(d)
    print("Distance: ", ranges[i], " cm")
  time.sleep(1)

# Calculate the average of the 10 measurements
average = sum(ranges) / len(ranges)

# Load the image into OpenCV
image = cv2.imread('./lecture4inclass.jpg')

# Define the text properties
position = (100, 250)
font = cv2.FONT_HERSHEY_SIMPLEX
font_scale = 1.2
text = f"{average:.2f} cm"
color = (255, 255, 255) # BGR format
thickness = 5

# Put the text on the image
cv2.putText(image, text, position, font, font_scale, color, thickness)

# Save the image
cv2.imwrite("lecture4inclass.jpg", image)
