from time import sleep

import wheel
import arm
import head
import waist

MAX = 8000
MIN = 4000

class Robot:
    def __init__(self):

            self.wheels = wheel.Wheel(MIN, MAX)
            self.leftArm = arm.Arm(MIN, MAX)
            self.rightArm = arm.Arm(MIN, MAX)
            self.head = head.Head(MIN, MAX)
            self.waist = waist.Waist(MIN, MAX)

    def fullBodyTest(self):
        #movement
        self.wheels.forward(2, 1000)
        self.wheels.backward(2, 1000)
        self.wheels.turn_left(2, 1000)
        self.wheels.turn_right(2, 1000)

        #head and waist
        self.head.tilt(4000)
        sleep(1)
        self.head.tilt(8000)
        sleep(1)
        self.head.center()
        sleep(1)
        self.head.pan(4000)
        sleep(1)
        self.head.pan(8000)
        sleep(1)
        self.head.center()
        sleep(1)
        self.waist.turn(4000)
        sleep(1)
        self.waist.turn(8000)
        sleep(1)
        self.waist.center()
        sleep(1)