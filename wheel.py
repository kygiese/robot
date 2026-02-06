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

    def forward(self, n):
        self.motor.setTarget(LEFT_WHEEL, 4000)
        self.motor.setTarget(RIGHT_WHEEL, 4000)
        sleep(n)
        self.motor.setTarget(LEFT_WHEEL, CENTER)
        self.motor.setTarget(RIGHT_WHEEL, CENTER)


    def backward(self, n):
        self.motor.setTarget(LEFT_WHEEL, 7000)
        self.motor.setTarget(RIGHT_WHEEL, 7000)
        sleep(n)
        self.motor.setTarget(LEFT_WHEEL, CENTER)
        self.motor.setTarget(RIGHT_WHEEL, CENTER)