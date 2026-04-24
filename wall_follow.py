import math
import numpy as np

w = 394

def find_speeds(scan_data, default_speed, wall_side):

    if wall_side:
        arc = list(range(120, 241))
    else:
        arc = list(range(300, 360)) + list(range(0, 61))

    points = []
    for i in arc:
        if scan_data[i] > 0:
            x = scan_data[i] * math.cos(math.radians(i))
            y = scan_data[i] * math.sin(math.radians(i))
            points.append((x, y))

    if len(points) < 30:
        print(f"bad wall: only {len(points)} points")
        return default_speed, -default_speed

    x_arr = np.array([p[0] for p in points])
    y_arr = np.array([p[1] for p in points])


    if np.std(x_arr) > np.std(y_arr):
        m, b = np.polyfit(x_arr, y_arr, 1)
        target_x = 700
        target_y = m * target_x + b

        signed_dist = b / math.sqrt(m**2 + 1)
    else:
        m, b = np.polyfit(y_arr, x_arr, 1)
        target_x = m * 700 + b
        target_y = 700

        signed_dist = -b / math.sqrt(m**2 + 1)

    desired_distance = 300


    if wall_side:
        measured_distance =  signed_dist
        distance_error = measured_distance - desired_distance
        target_y -= distance_error * 2
    else:
        measured_distance = -signed_dist
        distance_error = measured_distance - desired_distance
        target_y += distance_error * 2

    ld = math.sqrt(target_x**2 + target_y**2)
    alpha = math.atan2(target_y, target_x)

    omega = (2 * math.sin(alpha) / ld) * default_speed

    left_speed  = default_speed - (omega * w / 2)
    right_speed = default_speed + (omega * w / 2)

    max_val = max(abs(left_speed), abs(right_speed))
    if max_val > 100:
        left_speed  = (left_speed  / max_val) * 100
        right_speed = (right_speed / max_val) * 100

    print(f"dist={measured_distance:.0f}mm  err={distance_error:.0f}  "
          f"alpha={math.degrees(alpha):.1f}deg  L={left_speed:.1f}  R={right_speed:.1f}")

    return left_speed, -right_speed