from math import floor
from adafruit_rplidar import RPLidar
import threading
import subprocess
from time import sleep

class Lidar:
    def __init__(self):
        self.checkB = True
        self.checkF = True
        self.lidar = RPLidar(None, '/dev/ttyUSB0', timeout=5)
        threading.Thread(target=self.test(), daemon=True).start()

    def health_check(self):
        print(self.lidar.info())
        print(self.lidar.health())

    def test(self):
        scan_data = [0] * 360
        a = 0
        # print(self.lidar.info)
        for scan in self.lidar.iter_scans():
            for (_, angle, distance) in scan:
                scan_data[min([359, floor(angle)])] = distance
                if angle > 240 and angle < 300:
                    if distance < 600:
                        self.checkF = True
                elif angle > 100 and angle < 160:
                    if distance < 600:
                        self.checkB = True
            # print(self.checkF, self.checkB)
            self.checkF = False
            self.checkB = False

        self.lidar.stop()
        self.lidar.disconnect()

    def mock_test(self):
        while(True):
            self.checkB = True
            self.checkF = False
            sleep(5)
            self.checkB = False
            self.checkF = True
            sleep(5)




def process_data(data):
    for angle in range(360):
        distance = data[angle]
        print(angle, distance)

