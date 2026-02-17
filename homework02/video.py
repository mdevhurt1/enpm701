from picamera2 import Picamera2
import cv2
import time

# Open camera
picam2 = Picamera2()
config = picam2.create_video_configuration(main={"format": "RGB888", "size": (640, 480)})
picam2.configure(config)
picam2.start()

# Give the camera time to warm up
time.sleep(2)

# Set up video writer
fps = 30.0
fourcc = cv2.VideoWriter_fourcc(*"mp4v")
out = cv2.VideoWriter("video.mp4", fourcc, fps, (640, 480))

duration = 30  # seconds
frame_count = 0
start_time = time.time()

print(f"Recording for {duration} seconds...")

while time.time() - start_time < duration:
  img = picam2.capture_array()
  img_bgr = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)

  out.write(img_bgr)
  frame_count += 1

print(f"Recording complete. Captured {frame_count} frames.")

out.release()
picam2.stop()
