"""
Robot Control Layer - Independent of Flask

This module provides a unified interface for controlling the robot's:
- Wheels (driving forward/backward/turning)
- Head (pan and tilt)
- Waist (rotation)

All functions enforce safe limits and provide a STOP/neutral state.
This layer is callable directly from Python for testing.
"""

import threading
import time

# Try to import maestro, but allow mock mode for testing
try:
    import maestro
    MOCK_MODE = False
except (ImportError, Exception):
    MOCK_MODE = True

# Servo channel assignments (based on servo_assignments.txt)
LEFT_WHEEL = 0
RIGHT_WHEEL = 1  # Note: may not be working per servo_assignments.txt
WAIST_CHANNEL = 2
HEAD_PAN_CHANNEL = 3
HEAD_TILT_CHANNEL = 4

# Safe limits for servo positions (quarter-microseconds)
# Standard servo range is 3000-9000, center at 6000
SERVO_MIN = 4000
SERVO_MAX = 8000
SERVO_CENTER = 6000

# Wheel-specific values (continuous rotation servos)
WHEEL_STOP = 6000  # Neutral/stopped position
WHEEL_MIN_SPEED = 4000  # Full speed one direction
WHEEL_MAX_SPEED = 8000  # Full speed other direction


class MockController:
    """Mock controller for testing without hardware"""
    def __init__(self, ttyStr=None, device=None):
        self.Targets = [SERVO_CENTER] * 24
        self.Mins = [0] * 24
        self.Maxs = [0] * 24
        
    def setRange(self, chan, min_val, max_val):
        self.Mins[chan] = min_val
        self.Maxs[chan] = max_val
        
    def setTarget(self, chan, target):
        # Enforce limits
        if self.Mins[chan] > 0 and target < self.Mins[chan]:
            target = self.Mins[chan]
        if self.Maxs[chan] > 0 and target > self.Maxs[chan]:
            target = self.Maxs[chan]
        self.Targets[chan] = target
        
    def getPosition(self, chan):
        return self.Targets[chan]
        
    def close(self):
        pass


class RobotControl:
    """
    Main robot control class that provides safe, validated control
    of all robot functions.
    
    Thread-safe and independent of Flask.
    """
    
    def __init__(self, mock_mode=None):
        """
        Initialize the robot control layer.
        
        Args:
            mock_mode: If True, use mock controller. If None, auto-detect.
        """
        self._lock = threading.Lock()
        self._mock_mode = mock_mode if mock_mode is not None else MOCK_MODE
        
        # Current state tracking
        self._left_wheel_speed = 0
        self._right_wheel_speed = 0
        self._head_pan = 0  # -100 to 100
        self._head_tilt = 0  # -100 to 100
        self._waist = 0  # -100 to 100
        
        # Heartbeat for connection monitoring
        self._last_command_time = time.time()
        self._heartbeat_timeout = 2.0  # seconds
        self._safety_thread = None
        self._running = False
        
        # Initialize controller
        self._init_controller()
        
        # Start safety monitoring
        self._start_safety_monitor()
    
    def _init_controller(self):
        """Initialize the servo controller"""
        try:
            if self._mock_mode:
                self._controller = MockController()
            else:
                self._controller = maestro.Controller()
            
            # Set safe ranges for all servos
            self._controller.setRange(LEFT_WHEEL, WHEEL_MIN_SPEED, WHEEL_MAX_SPEED)
            self._controller.setRange(RIGHT_WHEEL, WHEEL_MIN_SPEED, WHEEL_MAX_SPEED)
            self._controller.setRange(WAIST_CHANNEL, SERVO_MIN, SERVO_MAX)
            self._controller.setRange(HEAD_PAN_CHANNEL, SERVO_MIN, SERVO_MAX)
            self._controller.setRange(HEAD_TILT_CHANNEL, SERVO_MIN, SERVO_MAX)
            
            # Set to neutral/center position
            self.stop()
            
        except Exception as e:
            print(f"Warning: Could not initialize hardware controller: {e}")
            print("Running in mock mode")
            self._mock_mode = True
            self._controller = MockController()
    
    def _start_safety_monitor(self):
        """Start the safety monitoring thread"""
        self._running = True
        self._safety_thread = threading.Thread(target=self._safety_monitor, daemon=True)
        self._safety_thread.start()
    
    def _safety_monitor(self):
        """Background thread that stops the robot if no commands received"""
        while self._running:
            time.sleep(0.5)
            with self._lock:
                elapsed = time.time() - self._last_command_time
                if elapsed > self._heartbeat_timeout:
                    # No recent commands - stop wheels for safety
                    if self._left_wheel_speed != 0 or self._right_wheel_speed != 0:
                        self._set_wheel_speeds_internal(0, 0)
    
    def _validate_speed(self, value):
        """Validate and clamp speed value to -100 to 100 range"""
        try:
            value = float(value)
        except (ValueError, TypeError):
            return 0
        return max(-100, min(100, value))
    
    def _validate_position(self, value):
        """Validate and clamp position value to -100 to 100 range"""
        try:
            value = float(value)
        except (ValueError, TypeError):
            return 0
        return max(-100, min(100, value))
    
    def _speed_to_servo(self, speed):
        """
        Convert speed (-100 to 100) to servo value (4000 to 8000).
        0 speed = 6000 (stopped)
        Positive = one direction
        Negative = other direction
        """
        # Map -100...100 to 4000...8000
        # 0 -> 6000, -100 -> 4000, 100 -> 8000
        servo_value = int(SERVO_CENTER + (speed / 100.0) * (SERVO_MAX - SERVO_CENTER))
        return max(WHEEL_MIN_SPEED, min(WHEEL_MAX_SPEED, servo_value))
    
    def _position_to_servo(self, position):
        """
        Convert position (-100 to 100) to servo value (4000 to 8000).
        0 = center (6000)
        """
        servo_value = int(SERVO_CENTER + (position / 100.0) * (SERVO_MAX - SERVO_CENTER))
        return max(SERVO_MIN, min(SERVO_MAX, servo_value))
    
    def _set_wheel_speeds_internal(self, left_speed, right_speed):
        """Internal method to set wheel speeds (must hold lock)"""
        self._left_wheel_speed = left_speed
        self._right_wheel_speed = right_speed
        
        left_servo = self._speed_to_servo(left_speed)
        right_servo = self._speed_to_servo(right_speed)
        
        self._controller.setTarget(LEFT_WHEEL, left_servo)
        self._controller.setTarget(RIGHT_WHEEL, right_servo)
    
    def heartbeat(self):
        """
        Update the heartbeat timestamp.
        Call this periodically to keep the robot active.
        """
        with self._lock:
            self._last_command_time = time.time()
    
    def stop(self):
        """
        STOP - Set all motors to neutral/stopped state.
        This is the safe state for the robot.
        """
        with self._lock:
            self._last_command_time = time.time()
            
            # Stop wheels
            self._set_wheel_speeds_internal(0, 0)
            
            # Center head
            self._head_pan = 0
            self._head_tilt = 0
            self._controller.setTarget(HEAD_PAN_CHANNEL, SERVO_CENTER)
            self._controller.setTarget(HEAD_TILT_CHANNEL, SERVO_CENTER)
            
            # Center waist
            self._waist = 0
            self._controller.setTarget(WAIST_CHANNEL, SERVO_CENTER)
        
        return {"status": "ok", "message": "Robot stopped"}
    
    def drive(self, left_speed, right_speed):
        """
        Control wheel speeds for driving.
        
        Args:
            left_speed: Left wheel speed (-100 to 100)
            right_speed: Right wheel speed (-100 to 100)
            
        Returns:
            dict with status and actual values used
        """
        left_speed = self._validate_speed(left_speed)
        right_speed = self._validate_speed(right_speed)
        
        with self._lock:
            self._last_command_time = time.time()
            self._set_wheel_speeds_internal(left_speed, right_speed)
        
        return {
            "status": "ok",
            "left_speed": left_speed,
            "right_speed": right_speed
        }
    
    def drive_joystick(self, x, y):
        """
        Control driving using joystick coordinates.
        Converts joystick x/y to differential drive.
        
        Args:
            x: Joystick X position (-100 to 100, left/right)
            y: Joystick Y position (-100 to 100, forward/back)
            
        Returns:
            dict with status and computed wheel speeds
        """
        x = self._validate_speed(x)
        y = self._validate_speed(y)
        
        # Convert joystick to differential drive
        # y = forward/backward, x = turning
        # Simple mixing: left = y + x, right = y - x
        left_speed = y + x
        right_speed = y - x
        
        # Normalize if values exceed limits
        max_val = max(abs(left_speed), abs(right_speed))
        if max_val > 100:
            left_speed = (left_speed / max_val) * 100
            right_speed = (right_speed / max_val) * 100
        
        return self.drive(left_speed, right_speed)
    
    def head_pan(self, position):
        """
        Control head pan (left/right rotation).
        
        Args:
            position: Pan position (-100 to 100, left to right)
            
        Returns:
            dict with status and actual value used
        """
        position = self._validate_position(position)
        
        with self._lock:
            self._last_command_time = time.time()
            self._head_pan = position
            servo_value = self._position_to_servo(position)
            self._controller.setTarget(HEAD_PAN_CHANNEL, servo_value)
        
        return {
            "status": "ok",
            "head_pan": position
        }
    
    def head_tilt(self, position):
        """
        Control head tilt (up/down).
        
        Args:
            position: Tilt position (-100 to 100, down to up)
            
        Returns:
            dict with status and actual value used
        """
        position = self._validate_position(position)
        
        with self._lock:
            self._last_command_time = time.time()
            self._head_tilt = position
            servo_value = self._position_to_servo(position)
            self._controller.setTarget(HEAD_TILT_CHANNEL, servo_value)
        
        return {
            "status": "ok",
            "head_tilt": position
        }
    
    def waist(self, position):
        """
        Control waist rotation.
        
        Args:
            position: Waist position (-100 to 100, left to right)
            
        Returns:
            dict with status and actual value used
        """
        position = self._validate_position(position)
        
        with self._lock:
            self._last_command_time = time.time()
            self._waist = position
            servo_value = self._position_to_servo(position)
            self._controller.setTarget(WAIST_CHANNEL, servo_value)
        
        return {
            "status": "ok",
            "waist": position
        }
    
    def get_state(self):
        """
        Get current robot state.
        
        Returns:
            dict with all current positions/speeds
        """
        with self._lock:
            return {
                "left_wheel_speed": self._left_wheel_speed,
                "right_wheel_speed": self._right_wheel_speed,
                "head_pan": self._head_pan,
                "head_tilt": self._head_tilt,
                "waist": self._waist,
                "mock_mode": self._mock_mode
            }
    
    def shutdown(self):
        """Cleanup and shutdown the robot control"""
        self._running = False
        self.stop()
        if hasattr(self._controller, 'close'):
            self._controller.close()


# Predefined phrases for voice output
PHRASES = [
    "Hello, Hunter.",
    "Hunter is so cool.",
    "Please do not touch my wheels.",
    "Hunter is the greatest."
]


def get_phrases():
    """Get list of available phrases for voice output"""
    return PHRASES


# Singleton instance for easy access
_robot_instance = None


def get_robot(mock_mode=None):
    """Get or create the robot control singleton"""
    global _robot_instance
    if _robot_instance is None:
        _robot_instance = RobotControl(mock_mode=mock_mode)
    return _robot_instance


# For direct testing
if __name__ == "__main__":
    print("Testing Robot Control Layer")
    robot = RobotControl(mock_mode=True)
    
    print("\n1. Testing stop:")
    print(robot.stop())
    
    print("\n2. Testing drive:")
    print(robot.drive(50, 50))
    
    print("\n3. Testing joystick drive:")
    print(robot.drive_joystick(30, 50))
    
    print("\n4. Testing head pan:")
    print(robot.head_pan(45))
    
    print("\n5. Testing head tilt:")
    print(robot.head_tilt(-30))
    
    print("\n6. Testing waist:")
    print(robot.waist(60))
    
    print("\n7. Testing state:")
    print(robot.get_state())
    
    print("\n8. Testing validation with invalid values:")
    print(robot.drive("invalid", 200))  # Should clamp and handle
    
    print("\n9. Testing stop again:")
    print(robot.stop())
    
    print("\nRobot Control Layer test complete!")
    robot.shutdown()
