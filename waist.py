import maestro

WAIST = 2

class Waist:
    def __init__(self, min, max):
        self.controller = maestro.Controller()
        self.controller.setSpeed(WAIST, 30)
        self.controller.setRange(WAIST, min, max)

    def turn(self, target):
        self.controller.setTarget(WAIST, target)

    def center(self):
        self.controller.setTarget(WAIST, 6000)