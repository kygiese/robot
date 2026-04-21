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

    print(x1,y1)
    print(x2,y2)

    m = (y1-y2)/(x1-x2)

    b = y1 - (m*x1)

    target_y = 500
    target_x = (target_y-b)/m

    ld = math.sqrt(target_x**2 + target_y**2)

    alpha = math.atan2(target_y, target_x)

    r = ld/(2*math.sin(alpha))


    right_speed = ((default_speed*r*2) - (w*default_speed))/((r*2)+w)

    return default_speed, right_speed



