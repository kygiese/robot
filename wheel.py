import maestro


class Wheel:
    left_wheel = 0
    right_wheel = 1
    def __init__(self):
        self.motor = maestro.Controller()

    def forward(self, speed):
        self.motor.setSpeed(0, speed)
        self.motor.setSpeed(1, speed)

    def backward(self, speed):
        self.motor.setSpeed(0, -speed)
        self.motor.setSpeed(0, -speed)