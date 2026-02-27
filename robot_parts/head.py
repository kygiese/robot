from controllers import maestro

HEAD_PAN = 3
HEAD_TILT = 4


class Head:
    """
    Head control class that manages the robot's head movement.
    
    This class encapsulates all head control logic at the lowest level,
    including pan and tilt servo control with defined limits.
    """

    def __init__(self, min_val, max_val):
        """
        Initialize the head controller with limits.
        
        Args:
            min_val: Minimum servo value (typically 4000)
            max_val: Maximum servo value (typically 8000)
        """
        self.controller = maestro.Controller()
        self.min = min_val
        self.max = max_val
        self.center_position = 6000
        
        self.controller.setRange(HEAD_PAN, min_val, max_val)
        self.controller.setRange(HEAD_TILT, min_val, max_val)

    def center(self):
        """
        Center both pan and tilt to neutral position.
        """
        self.controller.setTarget(HEAD_PAN, self.center_position)
        self.controller.setTarget(HEAD_TILT, self.center_position)

    def pan(self, target):
        """
        Pan the head left/right to a target position.
        
        Args:
            target: Servo target value (4000-8000)
        """
        target = max(self.min, min(self.max, target))
        self.controller.setTarget(HEAD_PAN, target)

    def tilt(self, target):
        """
        Tilt the head up/down to a target position.
        
        Args:
            target: Servo target value (4000-8000)
        """
        target = max(self.min, min(self.max, target))
        self.controller.setTarget(HEAD_TILT, target)
