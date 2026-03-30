import RPi.GPIO as gpio
import time
import threading
import cv2
from picamera2 import Picamera2

# Motor pin allocations
IN1 = 31
IN2 = 33
IN3 = 35
IN4 = 37

# Ultrasonic sensor pin allocations
TRIG = 16
ECHO = 18

# Servo (gripper) pin and PWM config
SERVO_PIN = 36
SERVO_HZ  = 50

GRIPPER_OPEN   = 7.5
GRIPPER_HALF   = 5.5
GRIPPER_CLOSED = 3.5

# Timelapse config
WIDTH, HEIGHT      = 640, 480
FPS                = 30
DWELL_FRAMES       = 45    # frames per capture in output video (1.5 s each @ 30 fps)
CAPTURE_INTERVAL   = 1.0   # seconds between captures
TIMELAPSE_DURATION = 30    # total capture window in seconds

pwm = None

def init():
    gpio.setmode(gpio.BOARD)
    # Motor pins
    gpio.setup(IN1, gpio.OUT)
    gpio.setup(IN2, gpio.OUT)
    gpio.setup(IN3, gpio.OUT)
    gpio.setup(IN4, gpio.OUT)
    # Ultrasonic sensor pins
    gpio.setup(TRIG, gpio.OUT)
    gpio.setup(ECHO, gpio.IN)
    # Servo (gripper)
    global pwm
    gpio.setup(SERVO_PIN, gpio.OUT)
    pwm = gpio.PWM(SERVO_PIN, SERVO_HZ)
    pwm.start(GRIPPER_OPEN)

def gameover():
    gpio.output(IN1, False)
    gpio.output(IN2, False)
    gpio.output(IN3, False)
    gpio.output(IN4, False)

def distance(timeout_s=0.02):
    # Ensure trigger has no value
    gpio.output(TRIG, False)
    time.sleep(0.01)

    # Generate trigger pulse
    gpio.output(TRIG, True)
    time.sleep(0.00001)
    gpio.output(TRIG, False)

    # Wait for echo to go high
    start_wait = time.monotonic()
    while gpio.input(ECHO) == 0:
        if time.monotonic() - start_wait > timeout_s:
            return None  # no echo start

    pulse_start = time.monotonic()

    # Wait for echo to go low
    while gpio.input(ECHO) == 1:
        if time.monotonic() - pulse_start > timeout_s:
            return None  # echo stuck high / too long

    pulse_end = time.monotonic()

    pulse_duration = pulse_end - pulse_start
    dist_cm = round(pulse_duration * 17150, 2)
    return dist_cm

def measure_and_print():
    d = distance()
    if d is None:
        print("Distance: no echo (timeout)")
    else:
        print(f"Distance: {d:.2f} cm")

def forward(tf):
    # Left wheels forward
    gpio.output(IN1, True)
    gpio.output(IN2, False)
    # Right wheels forward
    gpio.output(IN3, False)
    gpio.output(IN4, True)
    time.sleep(tf)
    gameover()

def reverse(tf):
    # Left wheels reverse
    gpio.output(IN1, False)
    gpio.output(IN2, True)
    # Right wheels reverse
    gpio.output(IN3, True)
    gpio.output(IN4, False)
    time.sleep(tf)
    gameover()

def pivotleft(tf):
    # Left wheels reverse, right wheels forward
    gpio.output(IN1, True)
    gpio.output(IN2, False)
    gpio.output(IN3, True)
    gpio.output(IN4, False)
    time.sleep(tf)
    gameover()

def write_timelapse(frames, output_path):
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out = cv2.VideoWriter(output_path, fourcc, FPS, (WIDTH, HEIGHT))
    for frame in frames:
        for _ in range(DWELL_FRAMES):
            out.write(frame)
    out.release()
    print(f"Time-lapse saved: {output_path}")


def timelapse_worker(picam2, frames, stop_event):
    start = time.monotonic()
    while not stop_event.is_set():
        if time.monotonic() - start >= TIMELAPSE_DURATION:
            break
        img_rgb = picam2.capture_array()
        img_bgr = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2BGR)
        frames.append(img_bgr)
        # Drift-corrected sleep until next 1-second mark
        next_capture = start + len(frames) * CAPTURE_INTERVAL
        sleep_time = next_capture - time.monotonic()
        if sleep_time > 0:
            stop_event.wait(timeout=sleep_time)
    print(f"Timelapse capture done ({len(frames)} frames)")


def set_gripper(duty):
    pwm.ChangeDutyCycle(duty)

def pivotright(tf):
    # Left wheels forward, right wheels reverse
    gpio.output(IN1, False)
    gpio.output(IN2, True)
    gpio.output(IN3, False)
    gpio.output(IN4, True)
    time.sleep(tf)
    gameover()

timelapse_frames = []
_stop_timelapse  = threading.Event()

picam2 = Picamera2()
_cam_config = picam2.create_still_configuration(
    main={"format": "RGB888", "size": (WIDTH, HEIGHT)}
)
picam2.configure(_cam_config)
picam2.start()
time.sleep(2)  # warm-up

_tl_thread = threading.Thread(
    target=timelapse_worker,
    args=(picam2, timelapse_frames, _stop_timelapse),
    daemon=False,
)
_tl_thread.start()
print("Timelapse started (30 s).")

try:
    init()
    while True:
        key_press = input("Enter a key (w/a/s/d/1/2/3) to control the robot, or 'q' to quit: ")
        if key_press == 'q':
            print("Exiting...")
            break
        elif key_press == 'w':
            forward(0.25)
            measure_and_print()
        elif key_press == 's':
            reverse(0.25)
            measure_and_print()
        elif key_press == 'a':
            pivotleft(0.25)
            measure_and_print()
        elif key_press == 'd':
            pivotright(0.25)
            measure_and_print()
        elif key_press == '1':
            set_gripper(GRIPPER_OPEN)
            print("Gripper: open")
        elif key_press == '2':
            set_gripper(GRIPPER_HALF)
            print("Gripper: half")
        elif key_press == '3':
            set_gripper(GRIPPER_CLOSED)
            print("Gripper: closed")
        else:
            print("Invalid key press. Use 'w', 'a', 's', 'd', or '1'/'2'/'3'.")
finally:
    gameover()
    pwm.stop()
    _stop_timelapse.set()
    _tl_thread.join()
    if timelapse_frames:
        write_timelapse(timelapse_frames, "teleop_timelapse.mp4")
    picam2.stop()
    gpio.cleanup()
