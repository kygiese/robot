from controllers import maestro

WAIST = 2


class Waist:
    """
    Waist control class that manages the robot's waist rotation.
    
    This class encapsulates all waist control logic at the lowest level,
    including rotation servo control with defined limits.
    """
    
    def __init__(self, min_val, max_val):
        """
        Initialize the waist controller with limits.
        
        Args:
            min_val: Minimum servo value (typically 4000)
            max_val: Maximum servo value (typically 8000)
        """
        self.controller = maestro.Controller()
        self.min = min_val
        self.max = max_val
        self.center_position = 6000
        
        self.controller.setSpeed(WAIST, 30)
        self.controller.setRange(WAIST, min_val, max_val)

    def turn(self, target):
        """
        Turn the waist to a target position.
        
        Args:
            target: Servo target value (4000-8000)
        """
        target = max(self.min, min(self.max, target))
        self.controller.setTarget(WAIST, target)

    def center(self):
        """
        Center the waist to neutral position.
        """
        self.controller.setTarget(WAIST, self.center_position)
