# Corner detection on blurred_mask.jpg using cv2.goodFeaturesToTrack
import cv2
import numpy as np

# Load the image (should be grayscale for goodFeaturesToTrack)
img = cv2.imread('blurred_mask.jpg', cv2.IMREAD_GRAYSCALE)
if img is None:
	raise FileNotFoundError('blurred_mask.jpg not found in the current directory.')

# Parameters for corner detection
max_corners = 5
quality_level = 0.01
min_distance = 50

# Detect corners
corners = cv2.goodFeaturesToTrack(img, maxCorners=max_corners, qualityLevel=quality_level, minDistance=min_distance)

# Convert to integer
if corners is not None:
	corners = np.int0(corners)
	# Convert grayscale to BGR for visualization
	img_color = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
	for i in corners:
		x, y = i.ravel()
		cv2.circle(img_color, (x, y), 5, (0, 0, 255), -1)
	# Save the result
	cv2.imwrite('corners_detected.jpg', img_color)
else:
	print('No corners detected.')
