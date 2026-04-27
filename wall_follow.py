import math
import numpy as np

w = 394

def find_speeds(scan_data, default_speed, wall_side):

    points = []

    if wall_side: # left wall
        arc = list(range(120, 240))
    else:
        arc = list(range(330, 360)) + list(range(0, 30))


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

    if np.std(x_arr) < 50:  # almost strait wall
        print("degenerate fit")
        return default_speed, -default_speed

    m,b = np.polyfit(x_arr, y_arr, 1)

#----------------- distance calc -------
    distance = 800 # the wanted distance
    mesuredDistance = abs(b)/math.sqrt(m**2 +1)
    distanceTarget = mesuredDistance - distance
#--------------  ------------ - -- -



    target_x = -700 if wall_side else 700
    target_y = (m * target_x + b)

    if wall_side:  # left wall
        target_y -= (distanceTarget * 2)
    else:
        target_y += (distanceTarget * 2) if mesuredDistance < 0 else -(distanceTarget * 2)


    ld = math.sqrt(target_x**2 + target_y**2)

    alpha = math.atan2(target_y, target_x)


    r = ld/(2*math.sin(alpha))

    #print(r)

    vel = (2 * math.sin(alpha) /ld) * default_speed

    if wall_side:  # left wal
        right_speed = default_speed + (vel * w / 2)
        left_speed = default_speed - (vel * w / 2)
    else:
        right_speed = default_speed - (vel * w / 2)
        left_speed = default_speed + (vel * w / 2)


    print(mesuredDistance)
    print(target_x, target_y)

    return left_speed, -right_speed



