from time import sleep

from robot_parts import wheel
from robot_parts import arm
from robot_parts import head
from robot_parts import waist

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
        sleep(0.5)
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
        sleep(2)
        self.waist.center()
        sleep(1)
    
    def   def move_waist(self, target):
        self.waist.turn(target)

    def tilt_head(self, target):
        self.head.tilt(target)

    def pan_head(self, target):
        self.head.pan(target)

    def center_all(self):
        self.waist.center()
        self.head.center()

    def forward(self, time, speed):
        self.wheels.stop()
        self.wheels.forward(time, speed)

    def backward(self, time, speed):
        self.wheels.stop()
        self.wheels.backward(time, speed)

    def turn_left(self, time, speed):
        self.wheels.stop()
        self.wheels.turn_left(time, speed)

    def turn_right(self, time, speed):
        self.wheels.stop()
        self.wheels.turn_right(time, speed)

    def move_by_vector(self, left, right, time):
        self.wheels.stop()
        self.wheels.move(left, right)
        sleep(time)
        self.wheels.stop()
