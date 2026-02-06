import maestro
HEAD_PAN = 0
HEAD_TILT = 1

class Head:

    def __init__(self):
        self.controller = maestro.Controller()

    def center(self):
        self.controller.setTarget(HEAD_PAN, 6000)
        self.controller.setTarget(HEAD_TILT, 6000)

    def pan(self, target):
        self.controller.setSpeed(HEAD_PAN, 1)
        self.controller.setTarget(HEAD_PAN, target)

    def tilt(self, target):
        self.controller.setSpeed(HEAD_TILT, 1)
        self.controller.setTarget(HEAD_TILT, target)