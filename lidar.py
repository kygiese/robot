from rplidar import RPLidar

class Lidar:
    def __init__(self):
        self.lidar = RPLidar('/dev/ttyUSB0', 115200)


    def health_check(self):
        print(self.lidar.get_info())
        print(self.lidar.get_health())

    def test(self):
        for scan_idx, scan in enumerate(self.lidar.iter_scans()):
            print(f"\n=== scan {scan_idx}  points={len(scan)} ===")

            for i, (quality, angle, distance) in enumerate(scan):
                print(f"{i}: quality={quality} angle={angle:.2f} distance={distance:.1f}")