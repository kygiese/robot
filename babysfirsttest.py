from controllers import maestro
from time import sleep

LEFT_WHEEL = 0
RIGHT_WHEEL = 1
WAIST = 2
HEAD_PAN = 3
HEAD_TILT = 4
MIN = 4000
MAX = 8000
CENTER = 6000
WAIT = 2

def main():
    #contorller
    controller = maestro.Controller()
    #sets limits for waist and head
    controller.setRange(WAIST, MIN, MAX)
    controller.setRange(HEAD_PAN, MIN, MAX)
    controller.setRange(HEAD_TILT, MIN, MAX)

    #movement
    #forward
    controller.setTarget(LEFT_WHEEL, 5000)
    controller.setTarget(RIGHT_WHEEL, 7000)
    sleep(2)
    controller.setTarget(LEFT_WHEEL, CENTER)
    controller.setTarget(RIGHT_WHEEL, CENTER)
    sleep(WAIT)
    #backward
    controller.setTarget(LEFT_WHEEL, 7000)
    controller.setTarget(RIGHT_WHEEL, 5000)
    sleep(2)
    controller.setTarget(LEFT_WHEEL, CENTER)
    controller.setTarget(RIGHT_WHEEL, CENTER)
    sleep(WAIT)
    #turn
    controller.setTarget(LEFT_WHEEL, 7000)
    controller.setTarget(RIGHT_WHEEL, 7000)
    sleep(2)
    controller.setTarget(LEFT_WHEEL, CENTER)
    controller.setTarget(RIGHT_WHEEL, CENTER)
    sleep(WAIT)
    #turn
    controller.setTarget(LEFT_WHEEL, 4000)
    controller.setTarget(RIGHT_WHEEL, 4000)
    sleep(2)
    controller.setTarget(LEFT_WHEEL, CENTER)
    controller.setTarget(RIGHT_WHEEL, CENTER)
    sleep(6)

    #waist
    controller.setSpeed(WAIST, 30)
    controller.setTarget(WAIST, MIN)
    sleep(WAIT)
    controller.setTarget(WAIST, MAX)
    sleep(WAIT)
    controller.setTarget(WAIST, CENTER)
    sleep(WAIT)

    #head
    controller.setTarget(HEAD_TILT, MIN)
    sleep(WAIT)
    controller.setTarget(HEAD_TILT, MAX)
    sleep(WAIT)
    controller.setTarget(HEAD_TILT, CENTER)
    sleep(WAIT)
    controller.setTarget(HEAD_PAN, MIN)
    sleep(WAIT)
    controller.setTarget(HEAD_PAN, MAX)
    sleep(WAIT)
    controller.setTarget(HEAD_PAN, CENTER)
    sleep(WAIT)

