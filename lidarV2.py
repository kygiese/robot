from pyrplidar import PyRPlidar
import robot_control
from math import floor
import time
import atexit

forward_left = -1
forward_right = 1


def average(scan_data):
    s = 0
    i = 0
    for data in scan_data:
        if data > 0:
            s += data
            i += 1
    return s / i


class Lidar:
    def __init__(self, robot):
        self.right_back = []
        self.checkB = True
        self.checkF = True
        self.right_front = []
        self.right = []
        self.robot = robot
        self.lidar = PyRPlidar()


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
        scan_data = [0] * 360
        count = 0
        try:
            for count, scan in enumerate(scan_generator()):
                scan_data[min([359, floor(scan.angle)])] = scan.distance

            #-------------------------------------------------------------
                if 260 < scan.angle < 280:
                    if 0 < scan.distance < 600:
                        if self.robot.currentSpeedL < 0 < self.robot.currentSpeedR:
                            self.robot.drive_joystick(0, 0)
                        self.checkF = True
                    else:
                        self.checkF = False

                if 120 < scan.angle < 140:
                    if 0 < scan.distance < 600:
                        if self.robot.currentSpeedL > 0 > self.robot.currentSpeedR:
                            self.robot.drive_joystick(0, 0)
                        self.checkB = True

                    else:
                        self.checkB = False
            # -------------------------------------------------------------


                if count % 360 == 0 and count > 1:
                    self.right = average(scan_data[175:185])
                    self.right_front = average(scan_data[125:135])
                    self.right_back = average(scan_data[225:235])

                    #in zone, go forward
                    if 500 < self.right < 1000:
                        self.robot.drive_joystick(50, 50)

                    #not in zone
                    else:
                        #turn towards wall
                        if self.right_front > self.right_back:
                            self.robot.drive_joystick(-50, 50)
                        #turn away from wall
                        else:
                            self.robot.drive_joystick(50, -50)



                print("Front: ", self.checkF, " Back: ", self.checkB)



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



