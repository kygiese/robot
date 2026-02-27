#takes in: actions from dialogengine (nod, shake, arm, dance)
#produces: motion using robot class

class ActionRunner:
    def __init__(self, robot):
        self.robot = robot

    def run_action(self, action):
        if action == "nod":
            self.robot.tilt_head(5000)
            self.robot.tilt_head(7000)
            self.robot.tilt_head(6000)
        elif action == "shake":
            self.robot.pan_head(5000)
            self.robot.pan_head(7000)
            self.robot.pan_head(6000)
        elif action == "arm":
            #add arm methods to robot class
            pass