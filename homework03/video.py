import cv2
import time
import numpy as np
from picamera2 import Picamera2


def main(duration_seconds: int = 30, fps: int = 30, width: int = 640, height: int = 480):
	"""
	Record a video for `duration_seconds` and write circle + centroid on each frame.
	Output file: output.avi
	"""
	picam2 = Picamera2()
	config = picam2.create_video_configuration(main={"size": (width, height), "format": "RGB888"})
	picam2.configure(config)
	picam2.start()

	# Allow sensor to adjust
	time.sleep(2)

	fourcc = cv2.VideoWriter_fourcc(*"MJPG")
	out = cv2.VideoWriter("output.avi", fourcc, fps, (width, height))

	lower_green = np.array([30, 75, 75], dtype=np.uint8)
	upper_green = np.array([85, 255, 255], dtype=np.uint8)

	# performance timing variables
	start_time = time.time()
	frame_counter = 0
	deltas_sum = 0.0
	min_delta = float("inf")
	max_delta = 0.0
	times_out = None

	try:
		# open timings file
		times_out = open("frame_times.txt", "w")
		while True:
			# mark start of this frame processing
			frame_start = time.perf_counter()

			frame = picam2.capture_array()
			
			# Picamera2 returns RGB. Convert to BGR for OpenCV drawing and color conversions
			try:
				frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
			except Exception:
				# If conversion fails, assume frame is already BGR
				pass

			# Flip vertically
			frame = cv2.flip(frame, 0)

			hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
			mask = cv2.inRange(hsv, lower_green, upper_green)

			contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
			if contours:
				# pick the largest contour
				c = max(contours, key=cv2.contourArea)
				((x, y), radius) = cv2.minEnclosingCircle(c)
				M = cv2.moments(c)
				if M.get("m00", 0) != 0:
					cx = int(M["m10"] / M["m00"])
					cy = int(M["m01"] / M["m00"])
					cv2.circle(frame, (cx, cy), 4, (0, 0, 255), -1)  # centroid (red)
				if radius > 5:
					cv2.circle(frame, (int(x), int(y)), int(radius), (0, 255, 0), 2)  # enclosing circle (green)


			# Overlay elapsed time
			elapsed = int(time.time() - start_time)
			cv2.putText(frame, f"Time: {elapsed}s", (10, height - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

			# compute frame delta BEFORE writing so we can overlay it on the frame
			frame_delta = time.perf_counter() - frame_start
			# draw delta on the frame (top-left)
			cv2.putText(frame, f"Delta: {frame_delta:.3f}s", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)

			out.write(frame)

			# update stats
			deltas_sum += frame_delta
			min_delta = min(min_delta, frame_delta)
			max_delta = max(max_delta, frame_delta)
            
			# write delta to file (frame index, seconds)
			if times_out is not None:
				times_out.write(f"{frame_counter},{frame_delta:.6f}\n")
				times_out.flush()
			# also print the delta for this frame to the console
			print(f"Frame {frame_counter}: {frame_delta:.6f}s")
			frame_counter += 1

			if time.time() - start_time >= duration_seconds:
				break
	finally:
		# write summary to timings file then close
		if times_out is not None:
			if frame_counter > 0:
				avg = deltas_sum / frame_counter
			else:
				avg = 0.0
			times_out.write(f"# frames={frame_counter}, avg={avg:.6f}, min={min_delta:.6f}, max={max_delta:.6f}\n")
			times_out.close()
		out.release()
		picam2.stop()


if __name__ == "__main__":
	main()