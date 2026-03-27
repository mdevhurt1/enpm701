import RPi.GPIO as gpio
import time

# Motor pin allocations
IN1 = 31
IN2 = 33
IN3 = 35
IN4 = 37

# Ultrasonic sensor pin allocations
TRIG = 16
ECHO = 18

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
    gpio.output(IN1, False)
    gpio.output(IN2, True)
    gpio.output(IN3, False)
    gpio.output(IN4, True)
    time.sleep(tf)
    gameover()

def pivotright(tf):
    # Left wheels forward, right wheels reverse
    gpio.output(IN1, True)
    gpio.output(IN2, False)
    gpio.output(IN3, True)
    gpio.output(IN4, False)
    time.sleep(tf)
    gameover()

try:
    init()
    while True:
        key_press = input("Enter a key (w/a/s/d) to control the robot, or 'q' to quit: ")
        if key_press == 'q':
            print("Exiting...")
            break
        elif key_press == 'w':
            forward(1)
            measure_and_print()
        elif key_press == 's':
            reverse(1)
            measure_and_print()
        elif key_press == 'a':
            pivotleft(1)
            measure_and_print()
        elif key_press == 'd':
            pivotright(1)
            measure_and_print()
        else:
            print("Invalid key press. Use 'w', 'a', 's', or 'd'.")
finally:
    gameover()
    gpio.cleanup()
