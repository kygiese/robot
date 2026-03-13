"""
ActionRunner - Execute robot movement actions triggered by the dialog engine.

Actions are specified as tags embedded in dialog output (e.g. <nod>, <shake>).
All actions are bounded-time and use the robot_control interface.
"""

import time


# Maximum duration (seconds) for any single action — safety bound
_ACTION_TIMEOUT = 6.0

# Intermediate step duration for multi-step movements
_STEP_DELAY = 2


class ActionRunner:
    """
    Run named robot actions using the RobotControl interface.

    Args:
        robot: A RobotControl instance (or mock with the same API).
    """

    def __init__(self, robot):
        self.robot = robot

    def run_action(self, action):
        """
        Execute a named action. Unknown actions are silently ignored.
        All actions complete within _ACTION_TIMEOUT seconds.
        Wheels are guaranteed to stop after any driving action.

        Args:
            action (str): Action name (e.g. 'nod', 'shake', 'dance').
        """
        action = action.lower().strip()
        handler = {
            "head_yes": self._nod,
            "head_no": self._shake,
            "dance90": self._dance,
            "arm_raise": self._arm,
        }.get(action)
        if handler:
            try:
                handler()
            except Exception as exc:
                # Log but don't re-raise: a failed action must not crash the
                # dialog engine or leave the robot in an unsafe state.
                print(f"ActionRunner: action '{action}' raised {exc!r}")
            finally:
                # Deadman stop: always return to neutral after any action
                self.robot.stop()
        else:
            print(f"ActionRunner: unknown action '{action}' — ignoring")

    # ------------------------------------------------------------------ #
    # Individual actions                                                   #
    # ------------------------------------------------------------------ #

    def _nod(self):
        """Nod head: tilt down → tilt up → center."""
        self.robot.head_tilt(7000)
        time.sleep(.5)
        self.robot.head_tilt(6000)
        time.sleep(.5)
        self.robot.head_tilt(5000)

    def _shake(self):
        """Shake head: pan left → pan right → center."""
        self.robot.head_pan(100)
        time.sleep(.5)
        self.robot.head_pan(-100)
        time.sleep(1)
        self.robot.head_pan(0)

    def _dance(self):
        self.robot.drive(50,50)
        time.sleep(1)
        self.robot.drive(-50,-50)
        time.sleep(1)
        self.robot.drive(0,0)


    def _arm(self):
        """Raise both arms: shoulders up → hold → shoulders down → center."""
        self.robot.arm_raise(7000)
        time.sleep(1)
        self.robot.arm_raise(6000)

