from controllers import maestro
from time import sleep

R_SHOULDER_X = 6
R_SHOULDER_Y = 5
R_ELBOW = 7
R_WRIST_X = 9
R_WRIST_Y = 8
R_CLAW = 10

L_SHOULDER_X = 12
L_SHOULDER_Y = 11
L_ELBOW = 13
L_WRIST_X = 15
L_WRIST_Y = 14
L_CLAW = 16


class Arm:
    """
    Arm control class that manages the robot's arm servos.
    
    This class encapsulates all arm control logic at the lowest level,
    including shoulder, elbow, wrist, and claw servo control with
    individual limits for each joint.
    """
    
    def __init__(self, min_val, max_val):
        """
        Initialize the arm controller with limits.
        
        Args:
            min_val: Minimum servo value (typically 4000)
            max_val: Maximum servo value (typically 8000)
        """
        self.controller = maestro.Controller()
        self.min = min_val
        self.max = max_val
        
        # Set ranges for right arm joints
        self.controller.setRange(R_SHOULDER_Y, min_val, max_val)
        self.controller.setRange(R_SHOULDER_X, 6000, max_val)
        self.controller.setRange(R_ELBOW, min_val, max_val)
        self.controller.setRange(R_WRIST_Y, min_val, max_val)
        self.controller.setRange(R_WRIST_X, min_val, max_val)
        self.controller.setRange(R_CLAW, min_val, max_val)

        # Set ranges for left arm joints
        self.controller.setRange(L_SHOULDER_Y, min_val, max_val)
        self.controller.setRange(L_SHOULDER_X, min_val, 6000)
        self.controller.setRange(L_ELBOW, 6000, max_val)
        self.controller.setRange(L_WRIST_Y, min_val, max_val)
        self.controller.setRange(L_WRIST_X, min_val, max_val)
        self.controller.setRange(L_CLAW, min_val, max_val)

    def shoulder_y(self, target, side='both'):
        """
        Move shoulder Y (up/down) servo(s) to target position.

        The maestro controller enforces per-channel ranges set in __init__,
        so targets are clamped to each joint's safe limits automatically.

        Args:
            target: Servo target value (4000-8000)
            side:   'left', 'right', or 'both'
        """
        target = max(self.min, min(self.max, target))
        if side in ('right', 'both'):
            self.controller.setTarget(R_SHOULDER_Y, target)
        if side in ('left', 'both'):
            self.controller.setTarget(L_SHOULDER_Y, target)

    def center(self):
        """
        Return all arm servos to the center position (6000).

        6000 falls within every joint's configured range, so this is
        always a safe resting state.
        """
        center = 6000
        for ch in (R_SHOULDER_X, R_SHOULDER_Y, R_ELBOW,
                   R_WRIST_X, R_WRIST_Y, R_CLAW,
                   L_SHOULDER_X, L_SHOULDER_Y, L_ELBOW,
                   L_WRIST_X, L_WRIST_Y, L_CLAW):
            self.controller.setTarget(ch, center)

    def moveTestAll(self):
        """
        Test all arm joints by moving them through their range.
        """
        self.controller.setTarget(L_SHOULDER_X, 5000)
        sleep(2)
        self.controller.setTarget(R_SHOULDER_X, 7000)
        sleep(2)

        self.controller.setTarget(L_SHOULDER_Y, 8000)
        sleep(2)
        self.controller.setTarget(L_SHOULDER_Y, 4000)
        sleep(2)
        self.controller.setTarget(L_ELBOW, 8000)
        sleep(2)
        self.controller.setTarget(L_ELBOW, 4000)
        sleep(2)
        self.controller.setTarget(L_WRIST_Y, 8000)
        sleep(2)
        self.controller.setTarget(L_WRIST_Y, 4000)
        sleep(2)
        self.controller.setTarget(L_WRIST_X, 8000)
        sleep(2)
        self.controller.setTarget(L_WRIST_X, 4000)
        sleep(2)
        self.controller.setTarget(L_CLAW, 8000)
        sleep(2)
        self.controller.setTarget(L_CLAW, 4000)
        sleep(2)

        self.controller.setTarget(R_SHOULDER_Y, 4000)
        sleep(2)
        self.controller.setTarget(R_SHOULDER_Y, 8000)
        sleep(2)
        self.controller.setTarget(R_ELBOW, 4000)
        sleep(2)
        self.controller.setTarget(R_ELBOW, 8000)
        sleep(2)
        self.controller.setTarget(R_WRIST_Y, 4000)
        sleep(2)
        self.controller.setTarget(R_WRIST_Y, 8000)
        sleep(2)
        self.controller.setTarget(R_WRIST_X, 4000)
        sleep(2)
        self.controller.setTarget(R_WRIST_X, 8000)
        sleep(2)
        self.controller.setTarget(R_CLAW, 4000)
        sleep(2)
        self.controller.setTarget(R_CLAW, 8000)
        sleep(2)
