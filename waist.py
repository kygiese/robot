import maestro

WAIST = 0

class Waist:
    def __init__(self, min, max):
        self.controller = maestro.Controller()
        self.controller.setRange(WAIST, min, max)

    def turn(self, target):
        self.controller.setTarget(WAIST, target)

