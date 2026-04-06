from pyrplidar import PyRPlidar
from math import floor
import time


class Lidar:
    def __init__(self):
        self.checkB = True
        self.checkF = True

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
            if count == 20: break

        lidar.stop()
        lidar.set_motor_pwm(0)

        lidar.disconnect()

    def lidar_scan(self):
        lidar = PyRPlidar()
        lidar.connect(port="/dev/ttyUSB0", baudrate=115200, timeout=3)

        lidar.set_motor_pwm(500)
        time.sleep(2)

        scan_generator = lidar.force_scan()
        scan_data = [0] * 360

        for count, scan in enumerate(scan_generator()):
            scan_data[min([359, floor(scan[2])])] = scan[3]
            if 240 < scan[2] < 300:
                if scan[3] < 600:
                    self.checkF = True
            elif 100 < scan[2] < 160:
                if scan[3] < 600:
                    self.checkB = True

            print(self.checkF, self.checkB)
            self.checkF = False
            self.checkB = False

        lidar.stop()
        lidar.set_motor_pwm(0)

        lidar.disconnect()

if __name__ == "__main__":
    lidar = Lidar()
    lidar.simple_scan()