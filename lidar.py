from math import floor

from adafruit_rplidar import RPLidar


class Lidar:
    def __init__(self):
        self.checkB = True
        self.checkF = True
        self.lidar = RPLidar(None, '/dev/ttyUSB0', timeout=5)


    def health_check(self):
        print(self.lidar.info())
        print(self.lidar.health())

    def test(self):
        scan_data = [0] * 360
        a = 0
        try:
            print(self.lidar.info)
            for scan in self.lidar.iter_scans():
                for (_, angle, distance) in scan:
                    scan_data[min([359, floor(angle)])] = distance
                break
            process_data(scan_data)
        except KeyboardInterrupt:
            print('Stopping.')
        self.lidar.stop()
        self.lidar.disconnect()

def process_data(data):
    for angle in range(360):
        distance = data[angle]
        print(angle, distance)

#https://github.com/Slamtec/rplidar_sdk/tree/master