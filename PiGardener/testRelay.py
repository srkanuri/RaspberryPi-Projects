#!/usr/bin/python
import RPi.GPIO as GPIO
import time

GPIO.setmode(GPIO.BCM)

# init list with pin numbers

pinList = [2, 3, 4, 17]



# loop through pins and set mode and state to 'high'
GPIO.setup(2, GPIO.OUT)
GPIO.output(2, GPIO.HIGH)
    
# time to sleep between operations in the main loop
SleepTimeL = 2
# main loop
try:
    GPIO.output(2, GPIO.LOW)
    print ("Relay On")
    #time.sleep(SleepTimeL)
    
# End program cleanly with keyboard
except KeyboardInterrupt:
    print ("  Quit")
    # Reset GPIO settings
    GPIO.cleanup()
