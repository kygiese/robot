"""
Robot Control Layer - Independent of Flask

This module provides a unified interface for controlling the robot's:
- Wheels (driving forward/backward/turning)
- Head (pan and tilt)
- Waist (rotation)
- Arms (shoulder raise/lower)

Uses the hierarchical component structure from robot.py:
- wheel.Wheel for wheel control
- head.Head for head control
- waist.Waist for waist control
- arm.Arm for arm control

All functions enforce safe limits and provide a STOP/neutral state.
This layer is callable directly from Python for testing.
"""

import threading
import time

import lidarV2 as lidar

# Safe limits for servo positions (quarter-microseconds)
# Standard servo range is 3000-9000, center at 6000
SERVO_MIN = 4000
SERVO_MAX = 8000
SERVO_CENTER = 6000

# Try to import component modules
try:
    from robot_parts import wheel
    from robot_parts import head
    from robot_parts import waist
    from robot_parts import arm
    MOCK_MODE = False
except (ImportError, Exception):
    MOCK_MODE = True


class MockWheel:
    """Mock wheel controller for testing without hardware"""
    def __init__(self, min_val, max_val):
        self.left_target = SERVO_CENTER
        self.right_target = SERVO_CENTER
        
    def setLeftSpeed(self, target):
        self.left_target = target
        
    def setRightSpeed(self, target):
        self.right_target = target
        
    def stop(self):
        self.left_target = SERVO_CENTER
        self.right_target = SERVO_CENTER


class MockHead:
    """Mock head controller for testing without hardware"""
    def __init__(self, min_val, max_val):
        self.pan_target = SERVO_CENTER
        self.tilt_target = SERVO_CENTER
        
    def pan(self, target):
        self.pan_target = target
        
    def tilt(self, target):
        self.tilt_target = target
        
    def center(self):
        self.pan_target = SERVO_CENTER
        self.tilt_target = SERVO_CENTER


class MockWaist:
    """Mock waist controller for testing without hardware"""
    def __init__(self, min_val, max_val):
        self.target = SERVO_CENTER
        
    def turn(self, target):
        self.target = target


class MockArm:
    """Mock arm controller for testing without hardware"""
    def __init__(self, min_val, max_val):
        self.min = min_val
        self.max = max_val
        self.left_shoulder_y = SERVO_CENTER
        self.right_shoulder_y = SERVO_CENTER

    def shoulder_y(self, target, side='both'):
        target = max(self.min, min(self.max, target))
        if side in ('right', 'both'):
            self.right_shoulder_y = target
        if side in ('left', 'both'):
            self.left_shoulder_y = target

    def center(self):
        self.left_shoulder_y = SERVO_CENTER
        self.right_shoulder_y = SERVO_CENTER


class RobotControl:
    """
    Main robot control class that provides safe, validated control
    of all robot functions.
    
    Uses hierarchical component structure:
    - self._wheels: Wheel component for drive control
    - self._head: Head component for pan/tilt control  
    - self._waist_component: Waist component for rotation control
    
    Thread-safe and independent of Flask.
    """
    
    def __init__(self, mock_mode=None):
        """
        Initialize the robot control layer.
        
        Args:
            mock_mode: If True, use mock controllers. If None, auto-detect.
        """
        self._lock = threading.Lock()
        self._mock_mode = mock_mode if mock_mode is not None else MOCK_MODE
        
        # Current state tracking
        self._left_wheel_speed = 0
        self._right_wheel_speed = 0
        self._head_pan_pos = 0  # -100 to 100
        self._head_tilt_pos = 0  # -100 to 100
        self._waist_pos = 0  # -100 to 100
        self._arm_pos = 0  # -100 to 100 (shoulder Y for arm raise)
        
        # Heartbeat for connection monitoring
        self._last_command_time = time.time()
        self._heartbeat_timeout = 2.0  # seconds
        self._safety_thread = None
        self._running = False

        self._lidar = None
        self._lidar_thread = None
        
        # Initialize components using hierarchical structure
        self._init_components()
        
        # Start safety monitoring
        self._start_safety_monitor()
    
    def _init_components(self):
        """Initialize the robot components using hierarchical structure"""
        try:
            if self._mock_mode:
                # Use mock components for testing
                self._wheels = MockWheel(SERVO_MIN, SERVO_MAX)
                self._head = MockHead(SERVO_MIN, SERVO_MAX)
                self._waist_component = MockWaist(SERVO_MIN, SERVO_MAX)
                self._arm = MockArm(SERVO_MIN, SERVO_MAX)


            else:
                # Use real hardware components
                self._wheels = wheel.Wheel(SERVO_MIN, SERVO_MAX)
                self._head = head.Head(SERVO_MIN, SERVO_MAX)
                self._waist_component = waist.Waist(SERVO_MIN, SERVO_MAX)
                self._arm = arm.Arm(SERVO_MIN, SERVO_MAX)

                self._lidar = lidar.Lidar()
                self._lidar_thread = threading.Thread(target=self._lidar.lidar_scan())
                self._lidar_thread.start()
                time.sleep(6)
                print("thread init")
                print(self._lidar_thread.is_alive())
                print("-============================")
                print(self._lidar.checkB)
                print(self._lidar.checkF)
            
            # Set to neutral/center position
            self.stop()


        except Exception as e:
            print(f"Warning: Could not initialize hardware components: {e}")
            print("Running in mock mode")
            self._mock_mode = True
            self._wheels = MockWheel(SERVO_MIN, SERVO_MAX)
            self._head = MockHead(SERVO_MIN, SERVO_MAX)
            self._waist_component = MockWaist(SERVO_MIN, SERVO_MAX)
            self._arm = MockArm(SERVO_MIN, SERVO_MAX)
    
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
                print("Front: " + self._lidar.checkF + " Back: " + self._lidar.checkB)
                if elapsed > self._heartbeat_timeout or self._lidar.checkB or self._lidar.checkF:
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
        return max(SERVO_MIN, min(SERVO_MAX, servo_value))
    
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
        
        # Use wheel component methods
        if hasattr(self._wheels, 'setLeftSpeed'):
            self._wheels.setLeftSpeed(left_servo)
            self._wheels.setRightSpeed(right_servo)
        elif hasattr(self._wheels, 'motor'):
            # Direct access for original Wheel class
            self._wheels.motor.setTarget(0, left_servo)  # LEFT_WHEEL
            self._wheels.motor.setTarget(1, right_servo)  # RIGHT_WHEEL
    
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
            
            # Stop wheels using wheel component
            self._set_wheel_speeds_internal(0, 0)
            
            # Center head using head component
            self._head_pan_pos = 0
            self._head_tilt_pos = 0
            self._head.center()
            
            # Center waist using waist component
            self._waist_pos = 0
            self._waist_component.turn(SERVO_CENTER)
            
            # Center arms using arm component
            self._arm_pos = 0
            self._arm.center()
        
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
        left_speed = -y - x
        right_speed = y - x
        
        # Normalize if values exceed limits
        max_val = max(abs(left_speed), abs(right_speed))
        if max_val > 100:
            left_speed = (left_speed / max_val) * 100
            right_speed = (right_speed / max_val) * 100

        if self._lidar.checkF and left_speed < 0 < right_speed:
            return self.drive(0,0)
        elif self._lidar.checkB and left_speed > 0 > right_speed:
            return self.drive(0,0)
        else:
            return self.drive(left_speed, right_speed)
    
    def head_pan(self, position):
        """
        Control head pan (left/right rotation).
        Uses the head component for control.
        
        Args:
            position: Pan position (-100 to 100, left to right)
            
        Returns:
            dict with status and actual value used
        """
        position = self._validate_position(position)
        
        with self._lock:
            self._last_command_time = time.time()
            self._head_pan_pos = position
            servo_value = self._position_to_servo(position)
            # Use head component's pan method
            self._head.pan(servo_value)
        
        return {
            "status": "ok",
            "head_pan": position
        }
    
    def head_tilt(self, position):
        """
        Control head tilt (up/down).
        Uses the head component for control.
        
        Args:
            position: Tilt position (-100 to 100, down to up)
            
        Returns:
            dict with status and actual value used
        """
        position = self._validate_position(position)
        
        with self._lock:
            self._last_command_time = time.time()
            self._head_tilt_pos = position
            servo_value = self._position_to_servo(position)
            # Use head component's tilt method
            self._head.tilt(servo_value)
        
        return {
            "status": "ok",
            "head_tilt": position
        }
    
    def waist_rotate(self, position):
        """
        Control waist rotation.
        Uses the waist component for control.
        
        Args:
            position: Waist position (-100 to 100, left to right)
            
        Returns:
            dict with status and actual value used
        """
        position = self._validate_position(position)
        
        with self._lock:
            self._last_command_time = time.time()
            self._waist_pos = position
            servo_value = self._position_to_servo(position)
            # Use waist component's turn method
            self._waist_component.turn(servo_value)
        
        return {
            "status": "ok",
            "waist": position
        }
    
    def arm_raise(self, position, side='both'):
        """
        Control arm raise (shoulder Y movement).
        Uses the arm component for control.  The arm component's per-joint
        ranges (set in arm.Arm.__init__) are preserved; the maestro driver
        clamps any target that falls outside a channel's configured range.

        Args:
            position: Shoulder position (-100 to 100, down to up)
            side:     'left', 'right', or 'both'

        Returns:
            dict with status and actual value used
        """
        position = self._validate_position(position)

        with self._lock:
            self._last_command_time = time.time()
            self._arm_pos = position
            servo_value = self._position_to_servo(position)
            self._arm.shoulder_y(servo_value, side=side)

        return {
            "status": "ok",
            "arm_raise": position,
            "side": side,
        }

    # Backward compatibility alias
    def waist(self, position):
        """Alias for waist_rotate for backward compatibility"""
        return self.waist_rotate(position)
    
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
                "head_pan": self._head_pan_pos,
                "head_tilt": self._head_tilt_pos,
                "waist": self._waist_pos,
                "arm_raise": self._arm_pos,
                "mock_mode": self._mock_mode
            }
    
    def shutdown(self):
        """Cleanup and shutdown the robot control"""
        self._running = False
        self.stop()
        # Close component controllers if they have close methods
        for component in [self._wheels, self._head, self._waist_component, self._arm]:
            if hasattr(component, 'controller') and hasattr(component.controller, 'close'):
                component.controller.close()
            elif hasattr(component, 'motor') and hasattr(component.motor, 'close'):
                component.motor.close()


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
