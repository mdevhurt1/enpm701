**Overview**

This repository contains course materials and homework for ENPM 701.

**Repository Structure**

- `homework02/`: Camera & video exercises
	- `confirm.py` - helper script for environment checks
	- `video.py` - capture and save video (uses Picamera2 + OpenCV)
	- `video.h264` - sample video file
- `homework03/`: Image processing and contour detection
	- `convert_reference.py` - color / format conversion utilities
	- `find_contours.py` - find and display contours in an image
	- `still.py` - capture still images (Picamera2)
- `lecture02/`
	- `qrcode01.py` - example QR code detection with OpenCV
- `lecture03/`
	- `range01.py` - Ultrasonic sensor range calculator

**Requirements**

- Python 3.8+ (3.10/3.11 recommended)
- Primary Python packages: `opencv-python`, `numpy`, `imutils`
- Optional (for Raspberry Pi camera scripts): `picamera2`, `RPi.GPIO`

On Raspberry Pi OS, install `picamera2` and related camera stack via the Raspberry Pi package manager as documented by the Raspberry Pi Foundation.

**Install (example)**

Run in a virtual environment:

```
python -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install opencv-python numpy imutils
```

For Pi-specific scripts:

```
pip install picamera2
sudo apt install -y python3-rpi.gpio
```

**Usage Examples**

- Run contour finder on an image:

```
python homework03/find_contours.py path/to/image.jpg
```

- Capture a still image (Raspberry Pi with camera):

```
python homework03/still.py
```

- Record video using the Picamera2 example:

```
python homework02/video.py
```

- QR code demo (uses OpenCV QR detector):

```
python lecture02/qrcode01.py path/to/image_or_video
```

**Notes & Tips**

- Many scripts were written to run on Raspberry Pi hardware; if you are running on a desktop, replace Picamera2 calls with a USB webcam or run the scripts that only use OpenCV.
- If `opencv-python` installation is problematic on ARM/Raspberry Pi, consider using a prebuilt package from the distribution or `opencv-python-headless` for non-GUI uses.
- Check each script header for usage details and required command-line arguments.
