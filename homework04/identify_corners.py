# Corner detection on blurred_mask.jpg using cv2.goodFeaturesToTrack.
#
# How it works:
#   1. Detect up to 7 corners with goodFeaturesToTrack (Shi-Tomasi)
#   2. Sort corners by angle around their centroid to form a polygon ordering
#   3. Find the corner with the SMALLEST interior angle - the arrowhead tip is
#      always the most acute (pointy) vertex, regardless of arrow length
#   4. Direction is the vector from the centroid to the identified tip

import cv2
import numpy as np

img = cv2.imread('blurred_mask.jpg', cv2.IMREAD_GRAYSCALE)
if img is None:
	raise FileNotFoundError('blurred_mask.jpg not found in the current directory.')

# Detect corners (Shi-Tomasi)
# maxCorners=7: an arrow has up to 7 geometric corners
# qualityLevel=0.05: more selective than 0.01 - avoids spurious noise corners
# minDistance=30: prevents merging nearby true corners
corners = cv2.goodFeaturesToTrack(img, maxCorners=7, qualityLevel=0.05, minDistance=30)

if corners is None or len(corners) < 3:
	print('Not enough corners detected.')
	exit()

corners = np.int0(corners)
pts = corners.reshape(-1, 2).astype(float)

# Centroid of all detected corners
cx, cy = pts.mean(axis=0)

# Sort corners by polar angle around the centroid so they form a polygon order
polar_angles = np.arctan2(pts[:, 1] - cy, pts[:, 0] - cx)
pts = pts[np.argsort(polar_angles)]
n = len(pts)

# Tip = corner with the smallest interior angle in the sorted polygon
# The arrowhead creates the sharpest angle; the tail corners are ~90 degrees
min_angle = float('inf')
tip_idx = 0
for i in range(n):
	v1 = pts[(i-1) % n] - pts[i]
	v2 = pts[(i+1) % n] - pts[i]
	denom = np.linalg.norm(v1) * np.linalg.norm(v2)
	if denom < 1e-8:
		continue
	angle = np.arccos(np.clip(np.dot(v1, v2) / denom, -1, 1))
	if angle < min_angle:
		min_angle = angle
		tip_idx = i

tip = pts[tip_idx].astype(int)
centroid = np.array([int(cx), int(cy)])

# Direction: vector from centroid to tip
vec   = pts[tip_idx] - np.array([cx, cy])
angle_deg = np.degrees(np.arctan2(vec[1], vec[0]))

if   -45  <= angle_deg <  45:  direction = "Right"
elif  45  <= angle_deg < 135:  direction = "Down"
elif angle_deg >= 135 or angle_deg < -135: direction = "Left"
else:                          direction = "Up"

# Visualize
img_color = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
for pt in pts.astype(int):
	cv2.circle(img_color, tuple(pt), 4, (0, 255, 255), -1)    # yellow = all corners
cv2.circle(img_color, tuple(tip),      8, (0,   0, 255), -1)  # red    = tip
cv2.circle(img_color, tuple(centroid), 5, (255, 0,   0), -1)  # blue   = centroid
cv2.arrowedLine(img_color, tuple(centroid), tuple(tip), (0, 255, 0), 2, tipLength=0.3)
cv2.putText(img_color, f'Direction: {direction}',
            (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
cv2.imwrite('corners_detected.jpg', img_color)
print(f'Direction: {direction}  |  tip={tuple(tip)}  corners detected={n}')
