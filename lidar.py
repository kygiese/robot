from rplidar import RPLidar, RPLidarException


class Lidar:
    def __init__(self):
        self.lidar = RPLidar('/dev/ttyUSB0', 115200)


    def health_check(self):
        print(self.lidar.get_info())
        print(self.lidar.get_health())

    def test(self):
        