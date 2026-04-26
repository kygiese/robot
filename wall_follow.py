import math
import numpy as np

w = 394

def find_speeds(scan_data, default_speed, wall_side):

    if wall_side:  # left wall, centered on 180°
        arc = list(range(150, 211))
    else:          # right wall, centered on 0°
        arc = list(range(330, 360)) + list(range(0, 31))

    points = []
    for i in arc:
        if scan_data[i] > 200:
            x = scan_data[i] * math.cos(math.radians(i))
            y = scan_data[i] * math.sin(math.radians(i))
            points.append((x, y))

    if len(points) < 10:
        print("bad wall")
        return default_speed, -default_speed

    x_arr = np.array([p[0] for p in points])
    y_arr = np.array([p[1] for p in points])

    desired_distance = 800

    if wall_side:
        # Left wall (~180°): points have large negative x, varying y
        # Wall is roughly vertical so fit x = my + b
        m, b = np.polyfit(y_arr, x_arr, 1)
        # Distance from origin to line (x - my - b = 0)
        measured_distance = abs(b) / math.sqrt(m**2 + 1)
        distance_error = measured_distance - desired_distance
        # Lookahead: project forward (along +x direction, 90°=forward)
        target_x = 700
        target_y = (target_x - b) / m
        # Too far from left wall → target_y should go more negative (steer left)
        target_y -= distance_error * 0.3

    else:
        # Right wall (~0°): points have large positive x, varying y
        # Wall is roughly vertical so fit x = my + b
        m, b = np.polyfit(y_arr, x_arr, 1)
        # Distance from origin to line
        measured_distance = abs(b) / math.sqrt(m**2 + 1)
        distance_error = measured_distance - desired_distance
        # Lookahead
        target_x = 700
        target_y = (target_x - b) / m
        # Too far from right wall → target_y should go more positive (steer right)
        target_y += distance_error * 0.3

    ld = math.sqrt(target_x**2 + target_y**2)
    alpha = math.atan2(target_y, target_x)

    omega = (2 * math.sin(alpha) / ld) * default_speed

    left_speed  = default_speed - (omega * w / 2)
    right_speed = default_speed + (omega * w / 2)

    max_val = max(abs(left_speed), abs(right_speed))
    if max_val > 100:
        left_speed  = (left_speed / max_val) * 100
        right_speed = (right_speed / max_val) * 100

    print(f"dist={measured_distance:.0f}  err={distance_error:.0f}  "
          f"target=({target_x:.0f},{target_y:.0f})  "
          f"alpha={math.degrees(alpha):.1f}  L={left_speed:.1f}  R={right_speed:.1f}")

    return left_speed, -right_speed