"""
wall_follow.py

Wall-following logic for a robot with a rotated RPLidar.

Coordinate system (LIDAR is rotated so that):
    0°   → faces RIGHT wall
    90°  → faces FORWARD
    180° → faces LEFT wall
    270° → faces BACKWARD

Zone definitions
----------------
Right-wall follow (left_mode = False):
    wall_side   :   350–10°   (right)
    front_side  :   310–349°  (front-right diagonal)
    back_side   :    11–50°   (back-right diagonal)
    front       :    80–100°  (forward)

Left-wall follow (left_mode = True):
    wall_side   :   170–190°  (left)
    front_side  :   191–230°  (front-left diagonal)
    back_side   :   130–169°  (back-left diagonal)
    front       :    80–100°  (forward)

Speed sign convention (matches robot_control):
    Positive left  + Negative right  → turns right
    Negative left  + Positive right  → turns left
    Both positive                    → forward (left motor runs in reverse
                                       physically, so signs are already handled
                                       by robot_control.drive())

For right-wall following the resulting (left, right) speeds are FLIPPED
(negated and swapped) so the robot still moves forward while reacting to the
wall on its right.

Parameters
----------
scan_data  : list[float], 360 elements, index = floor(angle), value = mm
             0 means no reading.
base_speed : int/float  forward cruise speed (positive = forward).
             Pass a negative value to cruise in reverse (unusual but supported).
left_mode  : bool  True → follow left wall, False → follow right wall.

Returns
-------
(left_speed, right_speed) : tuple[float, float]
"""

from math import floor

# ── tuneable constants ────────────────────────────────────────────────────────

TARGET_DIST   = 400    # mm  desired distance from the wall
INNER_THRESH  = 250    # mm  too close  – hard turn away
OUTER_THRESH  = 600    # mm  too far    – hard turn toward
FRONT_STOP    = 350    # mm  obstacle in front triggers stop / reverse-turn

# Steering correction magnitudes (fraction of base_speed added / subtracted)
CORRECTION_GENTLE = 0.30   # small nudge when inside the dead-band margins
CORRECTION_HARD   = 0.60   # strong correction outside the thresholds

# Dead-band around TARGET_DIST where no correction is applied
DEADBAND = 80   # mm  → comfortable range is TARGET_DIST ± DEADBAND

# ── helpers ───────────────────────────────────────────────────────────────────

def _zone_avg(scan_data: list, start: int, end: int) -> float:
    """
    Return the average of non-zero readings in [start, end] (degrees).
    Wraps correctly around 0°/360°.
    Returns 0.0 if no valid readings exist.
    """
    samples = []
    if start <= end:
        indices = range(start, end + 1)
    else:                           # wraps around 0°
        indices = list(range(start, 360)) + list(range(0, end + 1))

    for i in indices:
        v = scan_data[i % 360]
        if v > 0:
            samples.append(v)

    return sum(samples) / len(samples) if samples else 0.0


def _zone_min(scan_data: list, start: int, end: int) -> float:
    """Minimum non-zero distance in the zone; 0.0 if no valid readings."""
    samples = []
    if start <= end:
        indices = range(start, end + 1)
    else:
        indices = list(range(start, 360)) + list(range(0, end + 1))

    for i in indices:
        v = scan_data[i % 360]
        if v > 0:
            samples.append(v)

    return min(samples) if samples else 0.0


# ── main entry point ──────────────────────────────────────────────────────────

def find_speeds(scan_data: list, base_speed: float, left_mode: bool):
    """
    Compute (left_speed, right_speed) for wall following.

    See module docstring for full description.
    """

    abs_speed = abs(base_speed)

    # ── read sensor zones ─────────────────────────────────────────────────────

    # Front zone is the same regardless of which wall we follow
    front_dist = _zone_min(scan_data, 80, 100)

    if left_mode:
        # Left-wall zones  (180° = left wall)
        wall_dist       = _zone_avg(scan_data, 170, 190)   # lateral distance
        front_side_dist = _zone_avg(scan_data, 191, 230)   # front-left diagonal
        back_side_dist  = _zone_avg(scan_data, 130, 169)   # back-left diagonal
    else:
        # Right-wall zones (0° = right wall, wraps around)
        wall_dist       = _zone_avg(scan_data, 350, 10)    # lateral distance
        front_side_dist = _zone_avg(scan_data, 310, 349)   # front-right diagonal
        back_side_dist  = _zone_avg(scan_data,  11,  50)   # back-right diagonal

    # ── front obstacle check ──────────────────────────────────────────────────
    # If something is dead ahead and close, stop or spin away from wall.

    if 0 < front_dist < FRONT_STOP:
        # Turn away from the wall to avoid the obstacle
        # For left-mode: spin right (positive left, negative right)
        # For right-mode: spin left (negative left, positive right)
        spin = abs_speed * 0.8
        if left_mode:
            left_out, right_out =  spin, -spin
        else:
            left_out, right_out = -spin,  spin
        return _apply_side(left_out, right_out, left_mode)

    # ── wall lost recovery ────────────────────────────────────────────────────
    # If no valid wall reading, gently turn toward where the wall should be.

    if wall_dist == 0:
        recovery = abs_speed * CORRECTION_HARD
        if left_mode:
            # Turn left to find the left wall
            left_out, right_out = -recovery, recovery
        else:
            # Turn right to find the right wall
            left_out, right_out = recovery, -recovery
        return _apply_side(left_out, right_out, left_mode)

    # ── angle correction using diagonal sensors ───────────────────────────────
    # Positive angle_error → front is closer to wall than back → angling in.
    # We correct by steering away slightly even if lateral distance is OK.

    angle_error = 0.0
    if front_side_dist > 0 and back_side_dist > 0:
        angle_error = front_side_dist - back_side_dist   # mm

    # ── lateral distance PD-style correction ─────────────────────────────────

    dist_error = wall_dist - TARGET_DIST   # positive → too far, negative → too close

    if wall_dist < INNER_THRESH:
        # Hard turn away from wall
        correction = abs_speed * CORRECTION_HARD
        steer = -correction         # steer away (negative = toward open space)

    elif wall_dist > OUTER_THRESH:
        # Hard turn toward wall
        correction = abs_speed * CORRECTION_HARD
        steer = correction          # steer toward wall

    elif abs(dist_error) > DEADBAND:
        # Gentle proportional nudge inside the outer thresholds
        ratio = abs(dist_error) / (OUTER_THRESH - TARGET_DIST)
        correction = abs_speed * CORRECTION_GENTLE * min(ratio, 1.0)
        steer = correction if dist_error > 0 else -correction

    else:
        # Inside dead-band – only correct for angle if drifting
        steer = 0.0
        if abs(angle_error) > 80:          # mm threshold for diagonal sensors
            angle_correction = abs_speed * 0.15
            steer = angle_correction if angle_error > 0 else -angle_correction

    # ── blend steer with base_speed ───────────────────────────────────────────
    # steer > 0 → we want to turn toward wall
    # steer < 0 → we want to turn away from wall
    #
    # In left-mode:  turning toward left wall = negative left + positive right
    #                turning away             = positive left + negative right
    # (The _apply_side function handles the right-wall flip at the end.)

    if left_mode:
        left_out  = base_speed - steer
        right_out = base_speed + steer
    else:
        # Before flipping, compute as if following left wall, flip later
        left_out  = base_speed - steer
        right_out = base_speed + steer

    return _apply_side(left_out, right_out, left_mode)


# ── side flip ─────────────────────────────────────────────────────────────────

def _apply_side(left_out: float, right_out: float, left_mode: bool):
    """
    For right-wall following the motor outputs must be negated and swapped so
    the robot still drives forward (positive base_speed = forward) while the
    reactive logic mirrors correctly.
    """
    if left_mode:
        return left_out, right_out
    else:
        # Flip: negate both and swap so robot still goes forward
        return -right_out, -left_out