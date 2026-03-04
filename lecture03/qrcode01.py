import cv2
import os

# Open video capture
cap = cv2.VideoCapture("/dev/video0", cv2.CAP_V4L2)

# Force YUYV
cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"YUYV"))
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

print("opened: ", cap.isOpened())

if not cap.isOpened():
  raise RuntimeError("Could not open /dev/video19")

# Define detector
detector = cv2.QRCodeDetector()

while True:

  check, img = cap.read()
  if not check or img is None or img.size == 0:
    print("no frame")
    continue

  data, bbox, _ = detector.detectAndDecode(img)

  if(bbox is not None):
    for i in range(len(bbox)):
      cv2.line(img, tuple(bbox[i][0]), tuple(bbox[(i+1) % len(bbox)][0]), color = (0, 0, 255), thickness = 4)
      cv2.putText(img, data, (int(bbox[0][0][0]), int(bbox[0][0][1]) - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)

  if data:
    print("Data: ", data)

  # Show result to the screen
  cv2.imshow("QR Code detector", img)

  # Break out of loop by pressing the q key
  if(cv2.waitKey(1) & 0xFF) == ord("q"):
    break

cap.release()
cv2.destroyAllWindows()

