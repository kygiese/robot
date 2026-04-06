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
        print("1-----------------------------------------")
        lidar.connect(port="/dev/ttyUSB0", baudrate=115200, timeout=3)
        print("2-----------------------------------------")
        lidar.set_motor_pwm(500)
        print("3-----------------------------------------")
        time.sleep(2)
        print("4-----------------------------------------")
        scan_generator = lidar.force_scan()
        scan_data = [0] * 360
        try:
            for count, scan in enumerate(scan_generator()):
                scan_data[min([359, floor(scan.angle)])] = scan.distance
                if 240 < scan.angle < 300:
                    if scan.distance < 600:
                        self.checkF = True
                    else:
                        self.checkB = False
                elif 100 < scan.angle < 160:
                    if scan.distance < 600:
                        self.checkB = True
                    else:
                        self.checkF = False

                if not scan.quality == 0:
                    print(self.checkF, self.checkB)

        except KeyboardInterrupt:
            lidar.stop()
            lidar.set_motor_pwm(0)
            lidar.disconnect()


if __name__ == "__main__":
    lidar = Lidar()
    lidar.simple_scan()