import maestro
HEAD_PAN = 3
HEAD_TILT = 4

class Head:

    def __init__(self, min, max):
        self.controller = maestro.Controller()
        self.controller.setRange(HEAD_PAN, min, max)
        self.controller.setRange(HEAD_TILT, min, max)

    def center(self):
        self.controller.setTarget(HEAD_PAN, 6000)
        self.controller.setTarget(HEAD_TILT, 6000)

    def pan(self, target):
        self.controller.setTarget(HEAD_PAN, target)

    def tilt(self, target):
        self.controller.setTarget(HEAD_TILT, target)