import maestro

WAIST = 0

class Waist:
    def __init__(self):
        self.controller = maestro.Controller()

    def turn(self, target):
        self.controller.setSpeed(0, 1)
        self.controller.setTarget(target)

