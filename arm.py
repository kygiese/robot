import maestro

SHOULDER = 0
ELBOW = 1
WRIST = 2
CLAW = 3

class Arm:
    def __init__(self):
        self.controller = maestro.Controller()

    def center(self):
        self.controller.setSpeed(0, 1)
        self.controller.setSpeed(1, 1)
        self.controller.setSpeed(2, 1)
        self.controller.setSpeed(3, 1)

        self.controller.setTarget(0, 6000)
        self.controller.setTarget(1, 6000)
        self.controller.setTarget(2, 6000)
        self.controller.setTarget(3, 6000)

    def moveTestAll(self):
        self.controller.setSpeed(0, 1)
        self.controller.setSpeed(1, 1)
        self.controller.setSpeed(2, 1)
        self.controller.setSpeed(3, 1)

        self.controller.setTarget(0, 4000)
        self.controller.setTarget(0, 8000)
        self.controller.setTarget(1, 4000)
        self.controller.setTarget(1, 8000)
        self.controller.setTarget(2, 4000)
        self.controller.setTarget(2, 8000)
        self.controller.setTarget(3, 4000)
        self.controller.setTarget(3, 8000)