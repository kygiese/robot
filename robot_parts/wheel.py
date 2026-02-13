from time import sleep

from controllers import maestro

LEFT_WHEEL = 0
RIGHT_WHEEL = 1
CENTER = 6000


class Wheel:
    """
    Wheel control class that manages the robot's wheel motors.
    
    This class encapsulates all wheel control logic at the lowest level,
    including center position, limits, and movement implementation.
    Each wheel has its own center and the class handles the actual
    movement commands to the motors.
    """

    def __init__(self, min_val, max_val):
        """
        Initialize the wheel controller with limits.
        
        Args:
            min_val: Minimum servo value (typically 4000)
            max_val: Maximum servo value (typically 8000)
        """
        self.motor = maestro.Controller()
        self.min = min_val
        self.max = max_val
        self.center = CENTER
        
        # Set ranges for both wheels
        self.motor.setRange(LEFT_WHEEL, min_val, max_val)
        self.motor.setRange(RIGHT_WHEEL, min_val, max_val)

    def move(self, left_vector, right_vector):
        """
        Move wheels based on vector values.
        
        This is the core movement method that accepts vectors for each wheel.
        Positive values move wheel forward, negative values move backward.
        The vector values are relative to the center position.
        
        Args:
            left_vector: Movement vector for left wheel (-2000 to 2000)
            right_vector: Movement vector for right wheel (-2000 to 2000)
        """
        left_target = self.center + left_vector
        right_target = self.center + right_vector
        
        # Clamp to min/max limits
        left_target = max(self.min, min(self.max, left_target))
        right_target = max(self.min, min(self.max, right_target))
        
        self.motor.setTarget(LEFT_WHEEL, left_target)
        self.motor.setTarget(RIGHT_WHEEL, right_target)

    def setLeftSpeed(self, target):
        """
        Set left wheel to a specific servo target value.
        
        Args:
            target: Servo target value (4000-8000)
        """
        target = max(self.min, min(self.max, target))
        self.motor.setTarget(LEFT_WHEEL, target)

    def setRightSpeed(self, target):
        """
        Set right wheel to a specific servo target value.
        
        Args:
            target: Servo target value (4000-8000)
        """
        target = max(self.min, min(self.max, target))
        self.motor.setTarget(RIGHT_WHEEL, target)

    def forward(self, time, speed):
        """
        Move forward for a specified duration.
        
        Args:
            time: Duration in seconds
            speed: Speed value (typically 1000)
        """
        self.move(-speed, speed)
        sleep(time)
        self.stop()

    def backward(self, time, speed):
        """
        Move backward for a specified duration.
        
        Args:
            time: Duration in seconds
            speed: Speed value (typically 1000)
        """
        # Backward is the reverse of forward: reverse both wheel vectors
        self.move(speed, -speed)
        sleep(time)
        self.stop()

    def turn_left(self, time, speed):
        """
        Turn left for a specified duration.
        
        Args:
            time: Duration in seconds
            speed: Speed value for turn rate
        """
        # Turn left: both wheels move forward at same rate
        turn_offset = -1000  # Fixed offset for turning
        self.move(turn_offset, turn_offset)
        sleep(time)
        self.stop()

    def turn_right(self, time, speed):
        """
        Turn right for a specified duration.
        
        Args:
            time: Duration in seconds
            speed: Speed value for turn rate
        """
        # Turn right: both wheels move backward at same rate
        turn_offset = 1000  # Fixed offset for turning
        self.move(turn_offset, turn_offset)
        sleep(time)
        self.stop()

    def stop(self):
        """
        Stop both wheels by setting them to center position.
        """
        self.motor.setTarget(LEFT_WHEEL, self.center)
        self.motor.setTarget(RIGHT_WHEEL, self.center)
