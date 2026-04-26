import math
import numpy as np

#w = 394

def find_speeds(scan_data, default_speed, wall_side, distance=300, target=700, w=394):

    points = []

    if wall_side: # left wall
        arc = list(range(120, 240))
    else:
        arc = list(range(300, 360)) + list(range(0, 60))


    for i in arc:
        if scan_data[i] > 0:
            x = scan_data[i] * math.cos(math.radians(i))
            y = scan_data[i] * math.sin(math.radians(i))
            points.append((x, y))

    if len(points) < 10:
        print("bad wall")
        return default_speed, -default_speed

    x_arr = np.array([p[0] for p in points])
    y_arr = np.array([p[1] for p in points])

    m,b = np.polyfit(x_arr, y_arr, 1)

#----------------- distance calc -------
    distance = distance # the wanted distance
    mesuredDistance = abs(b)/math.sqrt(m**2 +1)
    distanceTarget = mesuredDistance - distance
#--------------  ------------ - -- -



    target_x = target
    target_y = (m * target_x + b)

    if wall_side:  # left wall
        target_y -= (distanceTarget * 2)
    else:
        target_y += (distanceTarget * 2)


    ld = math.sqrt(target_x**2 + target_y**2)

    alpha = math.atan2(target_y, target_x)


    r = ld/(2*math.sin(alpha))

    #print(r)

    vel = (2 * math.sin(alpha) /ld) * default_speed

    right_speed = default_speed + (vel*w/2)
    left_speed = default_speed - (vel*w/2)

    print(mesuredDistance)
    print(target_x, target_y)

    return left_speed, -right_speed



