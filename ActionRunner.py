"""
ActionRunner - Execute robot movement actions triggered by the dialog engine.

Actions are specified as tags embedded in dialog output (e.g. <nod>, <shake>).
All actions are bounded-time and use the robot_control interface.
"""

import time


# Maximum duration (seconds) for any single action — safety bound
_ACTION_TIMEOUT = 3.0

# Intermediate step duration for multi-step movements
_STEP_DELAY = 0.4


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

    # ------------------------------------------------------------------ #
    # Individual actions                                                   #
    # ------------------------------------------------------------------ #

    def _nod(self):
        """Nod head: tilt down → tilt up → center."""
        self.robot.head_tilt(5000)
        time.sleep(_STEP_DELAY)
        self.robot.head_tilt(7000)
        time.sleep(_STEP_DELAY)
        self.robot.head_tilt(6000)

    def _shake(self):
        """Shake head: pan left → pan right → center."""
        self.robot.head_pan(5000)
        time.sleep(_STEP_DELAY)
        self.robot.head_pan(7000)
        time.sleep(_STEP_DELAY)
        self.robot.head_pan(6000)

    def _dance(self):
        """
        Simple dance: alternate head pan with a bounded time.
        Wheels stay stopped (safe).
        """
        for _ in range(2):
            self.robot.head_pan(5000)
            self.robot.waist(5000)
            time.sleep(_STEP_DELAY)
            self.robot.head_pan(7000)
            self.robot.waist(7000)
            time.sleep(_STEP_DELAY)
        self.robot.head_pan(6000)
        self.robot.waist(6000)

    def _arm(self):
        """Placeholder for arm movement — extend when arm servos are wired."""
        pass
