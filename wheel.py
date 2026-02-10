from time import sleep

import maestro

LEFT_WHEEL = 0
RIGHT_WHEEL = 1
CENTER = 6000

class Wheel:

    def __init__(self, min, max):
        self.motor = maestro.Controller()
        self.motor.setRange(LEFT_WHEEL, min, max)
        self.motor.setRange(RIGHT_WHEEL, min, max)

    def forward(self, time, speed):
        self.motor.setTarget(LEFT_WHEEL, CENTER-speed)
        self.motor.setTarget(RIGHT_WHEEL, CENTER+speed)
        sleep(time)
        self.stop()


    def backward(self, time, speed):
        self.motor.setTarget(LEFT_WHEEL, CENTER+speed)
        self.motor.setTarget(RIGHT_WHEEL, CENTER+speed)
        sleep(time)
        self.stop()

    def turn_left(self, time, speed):
        self.motor.setTarget(LEFT_WHEEL, 5000)
        self.motor.setTarget(RIGHT_WHEEL, 5000)
        sleep(time)
        self.stop()

    def turn_right(self, time, speed):
        self.motor.setTarget(LEFT_WHEEL, 7000)
        self.motor.setTarget(RIGHT_WHEEL, 7000)
        sleep(time)
        self.stop()

    def stop(self):
        self.motor.setTarget(LEFT_WHEEL, CENTER)
        self.motor.setTarget(RIGHT_WHEEL, CENTER)