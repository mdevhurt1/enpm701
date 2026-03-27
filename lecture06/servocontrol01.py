import time
import cv2
import RPi.GPIO as GPIO
from picamera2 import Picamera2

SERVO_PIN = 36
SERVO_HZ  = 50
DWELL_S   = 1.5

WIDTH, HEIGHT = 640, 480
FPS           = 30
DWELL_FRAMES  = 45  # 45 frames @ 30 fps = 1.5 s per position in the video

POSITIONS = [
    (7.5, "open"),
    (5.5, "half"),
    (3.5, "closed"),
    (5.5, "half"),
    (7.5, "open"),
]


def annotate(img, text):
    """Draw text with a black outline near the bottom-left corner."""
    x, y = 20, HEIGHT - 20
    font       = cv2.FONT_HERSHEY_SIMPLEX
    scale      = 1.5
    white      = (255, 255, 255)
    black      = (0, 0, 0)
    thickness  = 3
    # Black outline
    cv2.putText(img, text, (x, y), font, scale, black, thickness + 2)
    # White fill
    cv2.putText(img, text, (x, y), font, scale, white, thickness)


def write_timelapse(frames, output_path):
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out = cv2.VideoWriter(output_path, fourcc, FPS, (WIDTH, HEIGHT))
    for frame in frames:
        for _ in range(DWELL_FRAMES):
            out.write(frame)
    out.release()
    print(f"Time-lapse saved: {output_path}")


def main():
    # --- Servo setup ---
    GPIO.setmode(GPIO.BOARD)
    GPIO.setup(SERVO_PIN, GPIO.OUT)
    pwm = GPIO.PWM(SERVO_PIN, SERVO_HZ)
    pwm.start(POSITIONS[0][0])  # start at open

    # --- Camera setup ---
    picam2 = Picamera2()
    config = picam2.create_still_configuration(
        main={"format": "RGB888", "size": (WIDTH, HEIGHT)}
    )
    picam2.configure(config)
    picam2.start()
    time.sleep(2)  # warm-up

    frames = []
    try:
        for duty, label in POSITIONS:
            print(f"Moving to {label} ({duty}%)...")
            pwm.ChangeDutyCycle(duty)
            time.sleep(DWELL_S)

            img_rgb = picam2.capture_array()
            img_bgr = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2BGR)
            img_bgr = cv2.resize(img_bgr, (WIDTH, HEIGHT))

            annotate(img_bgr, f"Duty: {duty}%  [{label}]")

            filename = f"gripper_{label}_{duty}.jpg"
            cv2.imwrite(filename, img_bgr)
            print(f"  Saved {filename}")

            frames.append(img_bgr)

        write_timelapse(frames, "gripper_timelapse.mp4")

    finally:
        pwm.stop()
        GPIO.cleanup()
        picam2.stop()


if __name__ == "__main__":
    main()
