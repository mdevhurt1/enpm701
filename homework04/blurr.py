import cv2

# Load the mask as grayscale (it is a single-channel binary image)
image = cv2.imread('./mask.jpg', cv2.IMREAD_GRAYSCALE)

# Morphological clean-up preserves the arrow shape while removing noise
# CLOSE fills small holes inside the white region
# OPEN  removes stray noise pixels outside the region
kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))
image = cv2.morphologyEx(image, cv2.MORPH_CLOSE, kernel)
image = cv2.morphologyEx(image, cv2.MORPH_OPEN,  kernel)

# Mild Gaussian blur reduces quantization roughness on the contour boundary
blurred_image = cv2.GaussianBlur(image, (5, 5), 0)

# Save the blurred image
cv2.imwrite('blurred_mask.jpg', blurred_image)
