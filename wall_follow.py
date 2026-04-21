import math

w = 394

def find_speeds(scan_data, default_speed):

    i = 255
    while scan_data[i] == 0:
        i += 1
    x1 = scan_data[i]*math.cos(math.radians(i))
    y1 = scan_data[i]*math.sin(math.radians(i))
    i = 135
    while scan_data[i] == 0:
        i -= 1
    x2 = scan_data[i]*math.cos(math.radians(i))
    y2 = scan_data[i]*math.sin(math.radians(i))


    m = (y1-y2)/(x1-x2)

    b = y1 - (m*x1)

    target_y = 500
    target_x = (target_y-b)/m

    ld = math.sqrt(target_x**2 + target_y**2)

    alpha = math.atan2(-target_x, target_y)

    r = ld/(2*math.sin(alpha))

    print(r)

    fuckyou = (2* math.sin(alpha) /ld) * default_speed

    right_speed = default_speed - (fuckyou*w/2)
    left_speed = default_speed + (fuckyou*w/2)
    return left_speed, right_speed



