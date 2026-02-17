import cv2
import numpy as np

# Load the image
image = cv2.imread('./reference.jpg')

# Convert to HSV color space
hsv_image = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

# Create black canvas
black_canvas = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
black_canvas[:] = 0

# Define lower and upper bounds for the color green in HSV

# Got the edge of the green light
# lower_green = (35, 100, 100)
# upper_green = (85, 255, 255)

# Got all of the green light and the edges of the yellow and red lights
# lower_green = (25, 50, 50)
# upper_green = (95, 255, 255)

lower_green = (30, 75, 75)
upper_green = (85, 255, 255)

# Set pixels within the green range to white on the black canvas
mask = cv2.inRange(hsv_image, lower_green, upper_green)
black_canvas[mask > 0] = 255

# Stack the RGB, HSV, and masked images horizontally
stacked_image = np.hstack((image, cv2.cvtColor(hsv_image, cv2.COLOR_HSV2BGR), cv2.cvtColor(black_canvas, cv2.COLOR_GRAY2BGR)))

# Save the stacked image
cv2.imwrite('reference_stacked.jpg', stacked_image)
