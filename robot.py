import wheel
import arm
import head
import waist

MAX = 8000
MIN = 4000

class Robot:
    def __init__(self):

            self.wheels = wheel.Wheel()
            self.leftArm = arm.Arm()
            self.rightArm = arm.Arm()
            self.head = head.Head()
            self.waist = waist.Waist()

    def fullBodyTest(self):
        #hopefully this many seconds of moving
        self.wheels.forward(2)
        self.wheels.backward(2)
        self.leftArm.moveTestAll()
        self.rightArm.moveTestAll()
        self.head.tilt(4000)
        self.head.tilt(8000)
        self.waist.turn(4000)
        self.waist.turn(8000)