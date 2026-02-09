import maestro
from time import sleep

R_SHOULDER_X = 6
R_SHOULDER_Y = 5
R_ELBOW = 7
R_WRIST_X = 9
R_WRIST_Y = 8
R_CLAW = 10

L_SHOULDER_X = 12
L_SHOULDER_Y = 11
L_ELBOW = 13
L_WRIST_X = 15
L_WRIST_Y = 14
L_CLAW = 16


class Arm:
    def __init__(self, min, max):
        self.controller = maestro.Controller()
        self.controller.setRange(R_SHOULDER_Y, min, max)
        self.controller.setRange(R_SHOULDER_X, 6000, max)
        self.controller.setRange(R_ELBOW, min, max)
        self.controller.setRange(R_WRIST_Y, min, max)
        self.controller.setRange(R_WRIST_X, min, max)
        self.controller.setRange(R_CLAW, min, max)

        self.controller.setRange(L_SHOULDER_Y, min, max)
        self.controller.setRange(L_SHOULDER_X, min, 6000)
        self.controller.setRange(L_ELBOW, 6000, max)
        self.controller.setRange(L_WRIST_Y, min, max)
        self.controller.setRange(L_WRIST_X, min, max)
        self.controller.setRange(L_CLAW, min, max)

    def moveTestAll(self):
        self.controller.setTarget(L_SHOULDER_X, 5000)
        sleep(2)
        self.controller.setTarget(R_SHOULDER_X, 7000)
        sleep(2)

        self.controller.setTarget(L_SHOULDER_Y, 8000)
        sleep(2)
        self.controller.setTarget(L_SHOULDER_Y, 4000)
        sleep(2)
        self.controller.setTarget(L_ELBOW, 8000)
        sleep(2)
        self.controller.setTarget(L_ELBOW, 4000)
        sleep(2)
        self.controller.setTarget(L_WRIST_Y, 8000)
        sleep(2)
        self.controller.setTarget(L_WRIST_Y, 4000)
        sleep(2)
        self.controller.setTarget(L_WRIST_X, 8000)
        sleep(2)
        self.controller.setTarget(L_WRIST_X, 4000)
        sleep(2)
        self.controller.setTarget(L_CLAW, 8000)
        sleep(2)
        self.controller.setTarget(L_CLAW, 4000)
        sleep(2)

        self.controller.setTarget(R_SHOULDER_Y, 4000)
        sleep(2)
        self.controller.setTarget(R_SHOULDER_Y, 8000)
        sleep(2)
        self.controller.setTarget(R_ELBOW, 4000)
        sleep(2)
        self.controller.setTarget(R_ELBOW, 8000)
        sleep(2)
        self.controller.setTarget(R_WRIST_Y, 4000)
        sleep(2)
        self.controller.setTarget(R_WRIST_Y, 8000)
        sleep(2)
        self.controller.setTarget(R_WRIST_X, 4000)
        sleep(2)
        self.controller.setTarget(R_WRIST_X, 8000)
        sleep(2)
        self.controller.setTarget(R_CLAW, 4000)
        sleep(2)
        self.controller.setTarget(R_CLAW, 8000)
        sleep(2)