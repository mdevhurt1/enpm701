# Corner detection on blurred_mask.jpg using cv2.goodFeaturesToTrack.
#
# How it works:
#   1. Detect up to 7 corners with goodFeaturesToTrack (Shi-Tomasi)
#   2. Compute the mask's pixel centroid — center of mass of all white pixels.
#      The large rectangular shaft pushes this centroid toward the tail side.
#   3. The tip is the detected corner farthest from the pixel centroid.
#      The arrowhead is always the most extreme feature relative to the center
#      of mass, regardless of how many corners were detected.

import cv2
import numpy as np

img = cv2.imread('blurred_mask.jpg', cv2.IMREAD_GRAYSCALE)
if img is None:
	raise FileNotFoundError('blurred_mask.jpg not found in the current directory.')

# Detect corners (Shi-Tomasi)
# maxCorners=7: an arrow has up to 7 geometric corners
# qualityLevel=0.01: low threshold — catches weaker tail corners too
# minDistance=30: prevents clustering multiple detections on the same corner
corners = cv2.goodFeaturesToTrack(img, maxCorners=7, qualityLevel=0.01, minDistance=30)

if corners is None or len(corners) < 1:
	print('No corners detected.')
	exit()

corners = np.int0(corners)
pts = corners.reshape(-1, 2).astype(float)

# Pixel centroid — center of mass of all white pixels in the mask.
# Unlike the corner centroid, this is stable even with few or clustered corners.
white_pixels = np.column_stack(np.where(img > 127))  # shape (N, 2): (row, col)
mask_cx = float(white_pixels[:, 1].mean())  # col = x
mask_cy = float(white_pixels[:, 0].mean())  # row = y
mask_centroid = np.array([mask_cx, mask_cy])

# Tip = corner farthest from the pixel centroid
tip_idx = max(range(len(pts)), key=lambda i: np.linalg.norm(pts[i] - mask_centroid))
tip = pts[tip_idx].astype(int)

# Direction: vector from pixel centroid to tip
vec       = pts[tip_idx] - mask_centroid
angle_deg = np.degrees(np.arctan2(vec[1], vec[0]))

if   -45  <= angle_deg <  45:  direction = "Right"
elif  45  <= angle_deg < 135:  direction = "Down"
elif angle_deg >= 135 or angle_deg < -135: direction = "Left"
else:                          direction = "Up"

# Visualize
img_color = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
for pt in pts.astype(int):
	cv2.circle(img_color, tuple(pt), 4, (0, 255, 255), -1)    # yellow = all corners
cv2.circle(img_color, tuple(tip),                    8, (0,   0, 255), -1)  # red  = tip
cv2.circle(img_color, (int(mask_cx), int(mask_cy)),  5, (255, 0,   0), -1)  # blue = centroid
cv2.arrowedLine(img_color, (int(mask_cx), int(mask_cy)), tuple(tip),
                (0, 255, 0), 2, tipLength=0.3)
cv2.putText(img_color, f'Direction: {direction}',
            (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
cv2.imwrite('corners_detected.jpg', img_color)
print(f'Direction: {direction}  |  tip={tuple(tip)}  corners={len(pts)}')
