from pyrplidar import PyRPlidar
import robot_control
from math import floor
import time
import atexit
import wall_follow_new
import math

forward_left = -1
forward_right = 1


def average(scan_data):
    s = 0
    i = 1
    for data in scan_data:
        if data > 0:
            s += data
            i += 1
    return s / i


class Lidar:
    def __init__(self, robot):
        self.right_back = 0
        self.checkB = True
        self.checkF = True

        self.right_front = 0
        self.right = 0
        self.robot = robot
        self.lidar = PyRPlidar()
        self.left = 0
        self.left_back = 0
        self.left_front = 0
        self.scan_data = [0] * 360
        self.intersect_flag = False
        self.robot.FollowMode = True

    def get_info(self):
        lidar = PyRPlidar()
        lidar.connect(port="/dev/ttyUSB0", baudrate=115200, timeout=3)
        # Linux   : "/dev/ttyUSB0"
        # MacOS   : "/dev/cu.SLAB_USBtoUART"
        # Windows : "COM5"

        info = lidar.get_info()
        print("info :", info)

        health = lidar.get_health()
        print("health :", health)

        samplerate = lidar.get_samplerate()
        print("samplerate :", samplerate)

        scan_modes = lidar.get_scan_modes()
        print("scan modes :")
        for scan_mode in scan_modes:
            print(scan_mode)

        lidar.disconnect()

    def simple_scan(self):
        lidar = PyRPlidar()

        lidar.connect(port="/dev/ttyUSB0", baudrate=115200, timeout=3)

        lidar.set_motor_pwm(500)

        time.sleep(2)

        scan_generator = lidar.force_scan()

        for count, scan in enumerate(scan_generator()):
            print(count, scan)
            if count == 2000: break

        lidar.stop()
        lidar.set_motor_pwm(0)

        lidar.disconnect()

    def lidar_scan(self):
        print("1-----------------------------------------")
        self.lidar.connect(port="/dev/ttyUSB0", baudrate=115200, timeout=3)
        print("2-----------------------------------------")
        self.lidar.set_motor_pwm(500)
        print("3-----------------------------------------")
        time.sleep(2)
        print("4-----------------------------------------")

        scan_generator = self.lidar.force_scan()
        print("5------------------")

        count = 0
        try:
            for count, scan in enumerate(scan_generator()):
                self.scan_data[min([359, floor(scan.angle)])] = scan.distance

                # -------------------------------------------------------------
                if 260 < scan.angle < 280:
                    if 0 < scan.distance < 600:
                        if self.robot.currentSpeedL < 0 < self.robot.currentSpeedR:
                            self.robot.drive(0, 0)
                        self.checkF = True
                    else:
                        self.checkF = False

                if 120 < scan.angle < 140:
                    if 0 < scan.distance < 600:
                        if self.robot.currentSpeedL > 0 > self.robot.currentSpeedR:
                            self.robot.drive(0, 0)
                        self.checkB = True

                    else:
                        self.checkB = False
                # -------------------------------------------------------------

                if count % 360 == 0 and count > 1 and self.robot.FollowOn:
                    left_speed, right_speed = wall_follow_new.find_speeds(self.scan_data, -50, self.robot.FollowMode)
                    self.robot.drive(left_speed, right_speed)

                    print(self.scan_data[240])
                    print(left_speed, right_speed)
                    if (right_speed + left_speed) > 20:
                        self.intersect_flag = True
                    else:
                        self.intersect_flag = False
                    '''                   
                     if self.scan_data[240] > 1600:
                        self.intersect_flag = True
                    else:
                        self.intersect_flag = False
                    '''
                    '''
                    #if self.follow == "right":
                    self.left = average(scan_data[175:185])
                    self.left_back = average(scan_data[145:155]) #125, 135
                    self.left_front = average(scan_data[205:215]) #225, 235

                    print (self.left_front, self.left_back)
                    #in zone, go forward
                    if 700 < self.left < 1100:
                        # proactively adjust curve while in good zone, prevents departure form zone under normal operation
                        if self.left_front - self.left_back < -100:
                            self.robot.drive_joystick(15, 50)
                        if self.left_front - self.left_back > 100:
                            self.robot.drive_joystick(-15, 50)#
                        #good zone and angle
                        else:
                            self.robot.drive_joystick(0, 50)

                    #not in zone/lost wall recovery/corner recovery
                    #turn away
                    elif self.left < 700:
                        self.robot.drive_joystick(25, 25)
                    #turn towards
                    elif self.left > 1100:
                        self.robot.drive_joystick(-25, 25)

                    #coverage check
                    else:
                        print("OOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOO")


                    if self.follow == "left":
                        self.left = average(scan_data[355:5])
                        self.left_back = average(scan_data[45:55])
                        self.left_front = average(scan_data[305:315])

                    # in zone, go forward
                        if 500 < self.left < 700:
                            self.robot.drive_joystick(0, 50)

                    # not in zone
                        else:
                        # turn towards wall
                            if self.left_front > self.left_back:
                                self.robot.drive_joystick(25, 25)
                        # turn away from wall
                            else:
                                self.robot.drive_joystick(-25, 25)

                    '''

            # print(self.right)


        except KeyboardInterrupt:
            self.lidar.stop()
            self.lidar.set_motor_pwm(0)
            self.lidar.disconnect()

    def shutdown(self):
        self.lidar.stop()
        self.lidar.set_motor_pwm(0)
        self.lidar.disconnect()


if __name__ == "__main__":
    lidar = Lidar()
    lidar.simple_scan()



