from rplidar import RPLidar, RPLidarException


class Lidar:
    def __init__(self):
        self.lidar = RPLidar('/dev/ttyUSB0', 115200)


    def health_check(self):
        print(self.lidar.get_info())
        print(self.lidar.get_health())

    def test(self):
        lidar = self.lidar

        # Good practice: start from a clean state
        lidar.stop()
        lidar.stop_motor()
        lidar.disconnect()
        lidar.connect()
        lidar.start_motor()
        lidar.clear_input()

        try:
            for scan_idx, scan in enumerate(lidar.iter_scans()):
                print(f"\n=== scan {scan_idx} points={len(scan)} ===")
                for i, (quality, angle, distance) in enumerate(scan):
                    print(f"{i}: quality={quality} angle={angle:.2f} distance={distance:.1f}")

                if scan_idx >= 5:
                    break

        except RPLidarException as e:
            print("RPLidarException:", e)
            # common recovery: clear buffer and try again
            lidar.clear_input()
            raise

        finally:
            # Clean shutdown
            try:
                lidar.stop()
                lidar.stop_motor()
            finally:
                lidar.disconnect()