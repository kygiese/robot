from pyrplidar import PyRPlidar
import robot_control
from math import floor
import time
import atexit

class Lidar:
    def __init__(self, robot):
        self.checkB = True
        self.checkF = True
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
              #  if 240 < scan.angle < 300 and scan.quality > 0 and scan.distance < 600 and self.robot.currentSpeedL < 0 < self.robot.currentSpeedR:
               #     self.robot.drive(0, 0)
                #    self.checkF = True
                 #   print("run")
               # else:
               #     self.checkF = False
               #     print("--------------")

               # if 100 < scan.angle < 160 and scan.quality > 0 and scan.distance < 600 and self.robot.currentSpeedL > 0 > self.robot.currentSpeedR:
                #    self.robot.drive(0, 0)
                #    self.checkB = True
               # else:
                # self.checkB = False

                if 260 < scan.angle < 280:
                    if 0 < scan.distance < 600:
                        self.checkF = True
                    else:
                        self.checkF = False

                if 120 < scan.angle < 140:
                    if 0 < scan.distance < 600:
                        self.checkB = True
                    else:
                        self.checkB = False

             #   if(scan.angle > 260 and scan.angle < 270):
              #      print(scan.distance)
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