# Arrow direction detection using contour analysis and convexity defects.
# This replaces the goodFeaturesToTrack approach, which produced unreliable
# corner positions on blurred binary masks (only 3 of 7 corners detected).
#
# How it works:
#   1. Threshold the blurred mask back to a clean binary image
#   2. Find the arrow contour with findContours
#   3. Compute convexity defects — the deep "armpit" indentations where
#      the arrowhead widens from the shaft are the unique structural signature
#      of an arrow shape
#   4. The tip is the convex-hull point farthest from the deepest notch

import cv2
import numpy as np

img = cv2.imread('blurred_mask.jpg', cv2.IMREAD_GRAYSCALE)
if img is None:
	raise FileNotFoundError('blurred_mask.jpg not found in the current directory.')

# Re-threshold to clean binary (blur may have created gray pixels)
_, thresh = cv2.threshold(img, 127, 255, cv2.THRESH_BINARY)

# Find contours and take the largest one (the arrow)
cnts, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
if not cnts:
	print('No contours detected.')
	exit()

cnt = max(cnts, key=cv2.contourArea)

# Convex hull (as indices, required for convexityDefects)
hull_idx = cv2.convexHull(cnt, returnPoints=False)
defects  = cv2.convexityDefects(cnt, hull_idx)

if defects is None:
	print('No convexity defects found — arrow shape may be too simple or mask is noisy.')
	exit()

# The deepest defect is the notch (the armpit between shaft and arrowhead)
deepest  = max(defects[:, 0], key=lambda d: d[3])
notch_pt = tuple(cnt[deepest[2]][0])

# The tip is the hull point farthest from the notch
hull_pts = cv2.convexHull(cnt)  # shape (M, 1, 2) — actual coordinates
tip = max(hull_pts,
          key=lambda p: np.linalg.norm(np.array(p[0]) - np.array(notch_pt)))[0]

# Direction: vector from contour centroid to tip
M  = cv2.moments(cnt)
cx = int(M['m10'] / M['m00'])
cy = int(M['m01'] / M['m00'])
vec   = tip.astype(float) - np.array([cx, cy], dtype=float)
angle = np.degrees(np.arctan2(vec[1], vec[0]))

if   -45  <= angle <  45:  direction = "Right"
elif  45  <= angle < 135:  direction = "Down"
elif angle >= 135 or angle < -135: direction = "Left"
else:                      direction = "Up"

# Visualize
img_color = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
cv2.circle(img_color, notch_pt,   6, (255,   0,   0), -1)  # blue   = notch
cv2.circle(img_color, tuple(tip), 8, (  0,   0, 255), -1)  # red    = tip
cv2.circle(img_color, (cx, cy),   5, (  0, 255, 255), -1)  # yellow = centroid
cv2.putText(img_color, f'Direction: {direction}',
            (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
cv2.imwrite('corners_detected.jpg', img_color)
print(f'Direction: {direction}  |  tip={tuple(tip)}  notch={notch_pt}')
