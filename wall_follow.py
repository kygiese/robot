import math

w = 10

def find_speeds(scan_data, default_speed):
    x1 = scan_data[225]*math.cos(225)
    y1 = scan_data[225]*math.sin(225)
    x2 = scan_data[135]*math.cos(135)
    y2 = scan_data[135]*math.sin(135)

    m = (y1-y2)/(x1-x2)

    b = y1 - m*x1

    target_y = 500
    target_x = (target_y-b)/m

    ld = math.sqrt(target_x**2 + target_y**2)

    alpha = math.atan(m)

    r = (2*math.sin(alpha))/ld



    right_speed = ((default_speed*r*2) - (w*default_speed))/((r*2)+w)

    return default_speed, right_speed



