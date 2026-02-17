import cv2
import sys

# Load the image
image = cv2.imread('./reference.jpg')
if image is None:
	print("Error: could not read './reference.jpg'")
	sys.exit(1)

# Convert to HSV color space
hsv_image = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

# Define lower and upper bounds for the color green in HSV
lower_green = (30, 75, 75)
upper_green = (85, 255, 255)

# Create a mask for green regions
mask = cv2.inRange(hsv_image, lower_green, upper_green)

# Find contours in the mask
contours, _ = cv2.findContours(mask.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

# If any contours were found, draw the minimum enclosing circle and centroid
if contours:
	# pick the largest contour by area
	c = max(contours, key=cv2.contourArea)

	# minimum enclosing circle
	(x, y), radius = cv2.minEnclosingCircle(c)
	center = (int(x), int(y))
	radius = int(radius)

	# compute moments to get the centroid
	M = cv2.moments(c)
	if M.get('m00', 0) != 0:
		cx = int(M['m10'] / M['m00'])
		cy = int(M['m01'] / M['m00'])
	else:
		cx, cy = center

	# Draw the enclosing circle and centroid
	if radius > 0:
		cv2.circle(image, center, radius, (0, 0, 255), 4)
		cv2.circle(image, (cx, cy), 5, (255, 0, 0), -1)
else:
	print('No green contour found.')

# Save the annotated image
cv2.imwrite('reference_contours.jpg', image)
