import maestro

SHOULDER = 0
ELBOW = 1
WRIST = 2
CLAW = 3

class Arm:
    def __init__(self, min, max):
        self.controller = maestro.Controller()
        self.controller.setRange(SHOULDER, min, max)
        self.controller.setRange(ELBOW, min, max)
        self.controller.setRange(WRIST, min, max)
        self.controller.setRange(CLAW, min, max)

    def center(self):
        self.controller.setTarget(0, 6000)
        self.controller.setTarget(1, 6000)
        self.controller.setTarget(2, 6000)
        self.controller.setTarget(3, 6000)

    def moveTestAll(self):
        self.controller.setTarget(0, 4000)
        self.controller.setTarget(0, 8000)
        self.controller.setTarget(1, 4000)
        self.controller.setTarget(1, 8000)
        self.controller.setTarget(2, 4000)
        self.controller.setTarget(2, 8000)
        self.controller.setTarget(3, 4000)
        self.controller.setTarget(3, 8000)