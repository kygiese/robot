from rplidar import RPLidar

class Lidar():
    def __init__(self):
        self.lidar = RPLidar('/dev/tty/USB0')


    def health_check(self):
        print(self.lidar.get_info())
        print(self.lidar.get_health())

    def test(self):
         for i, measure in enumerate(self.lidar.iter_measurments()):
             print("------------------------------------")
             print(measure[1])
             print(measure[2])
             print(measure[3])
             if i > 10:
                 break
