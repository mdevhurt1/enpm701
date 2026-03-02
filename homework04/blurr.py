import cv2

# Load the mask
image = cv2.imread('./mask.jpg')

# Apply a blur to the image
blurred_image = cv2.GaussianBlur(image, (15, 15), 0)

# Save the blurred image
cv2.imwrite('blurred_mask.jpg', blurred_image)
