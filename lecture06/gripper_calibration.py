import RPi.GPIO as GPIO

def setup() :
    GPIO.setmode(GPIO.BOARD)
    GPIO.setup(36, GPIO.OUT)
    pwm = GPIO.PWM(36, 50)
    pwm.start(5)
    return pwm

pwm = setup()
while True :
    duty_cycle = input("Enter duty cycle (0-100), or 'q' to quit: ")

    if duty_cycle == 'q':
        pwm.stop()
        GPIO.cleanup()
        print("Exiting...")
        break

    pwm.ChangeDutyCycle(float(duty_cycle))
