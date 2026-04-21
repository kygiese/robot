import math

w = 394  # track width in mm (match units with scan data)

def find_speeds(scan_data, default_speed):

    # Find two points on the right wall (~180° to 270° range)
    i = 255
    while scan_data[i] == 0:
        i += 1
    x1 = scan_data[i] * math.cos(math.radians(i))
    y1 = scan_data[i] * math.sin(math.radians(i))

    i = 135
    while scan_data[i] == 0:
        i -= 1
    x2 = scan_data[i] * math.cos(math.radians(i))
    y2 = scan_data[i] * math.sin(math.radians(i))

    # Fit line through two wall points
    m = (y1 - y2) / (x1 - x2)
    b = y1 - m * x1

    # Lookahead point on the wall line
    target_y = 500  # lookahead distance forward (mm)
    target_x = (target_y - b) / m

    # Pure pursuit
    ld = math.sqrt(target_x**2 + target_y**2)
    alpha = math.atan2(target_x, target_y)  # angle to lookahead point

    # Curvature -> angular velocity -> wheel speeds
    kappa = (2 * math.sin(alpha)) / ld
    omega = kappa * default_speed

    left_speed  = default_speed + (omega * w / 2)
    right_speed = default_speed - (omega * w / 2)

    return left_speed, right_speed