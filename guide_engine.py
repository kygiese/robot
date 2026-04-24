#states: waiting, greeting, listening, turning, following, turning, following, finished
import time

from statemachine import StateChart, State, StateMachine

from services.text_to_speech import TextToSpeech


class RobotGuideMachine(StateChart):
    allow_event_without_transition = False
    waiting = State(initial=True)
    greeting = State()
    listening = State()
    turning_around = State()
    aligning_to_hallway = State()
    moving_to_t = State()
    turning_to_destination = State()
    final_movement = State()
    stopped = State(final=True)

    human_detected = waiting.to(greeting)
    greeting_finished = greeting.to(listening)
    response_detected = listening.to(turning_around, cond="valid") | listening.to(listening, unless="valid")
    turning_around_complete = turning_around.to(aligning_to_hallway)
    aligning_complete = aligning_to_hallway.to(moving_to_t)
    intersection_detected = moving_to_t.to(turning_to_destination)
    turning_complete = turning_to_destination.to(final_movement)
    destination_reached = final_movement.to(stopped)


def listen():
    time.sleep(2)
    return "bathroom"


def average(scan_data):
    s = 0
    i = 1
    for data in scan_data:
        if data > 0:
            s += data
            i += 1
    return s / i


class RobotGuide:
    def __init__(self, robot):
        self.robot_guide_machine = RobotGuideMachine(self)
        self.robot = robot
        self.tts = TextToSpeech()

    def valid(self, response):
        if response == "bathroom" or response == "lab":
            return True
        return False

    def on_human_detected(self):
        print("speaking...")
        self.tts.speak("hello, how can I help you", None, False)
        self.robot_guide_machine.send("greeting_finished")

    def on_greeting_finished(self):
        print("listening...")
        self.robot_guide_machine.send("response_detected", listen())

    def on_response_detected(self):
        self.robot.drive_joystick(50, 50)
        time.sleep(1.1)
        self.robot.drive_joystick(0, 0)
        print("turning...")
        self.robot_guide_machine.send("turning_around_complete")

    def on_turning_around_complete(self):
        print("finding wall...")
        self.robot_guide_machine.send("aligning_complete")

    def on_aligning_complete(self):
        print("driving...")

        self.robot.FollowOn = True
        intersection = False
        while not intersection:
            intersection = self.robot.lidar.intersect_flag
            print(intersection)

        self.robot_guide_machine.send("intersection_detected")

    def on_intersection_detected(self):
        self.robot.FollowOn = False
        self.robot.stop()
        print("turning...")
        self.robot_guide_machine.send("turning_complete")

    def on_turning_complete(self):
        print("driving...")
        self.robot_guide_machine.send("destination_reached")

    def after_destination_reached(self):
        self.tts.speak("We have arrived", None, False)
        print("speaking...")

    def guide(self):
        # state 0 waiting for person
        print("starting..........")
        human_detected = True
        while not human_detected:
            if self.robot.lidar.checkF:
                human_detected = True
        self.robot_guide_machine.send("human_detected")

        '''
        # state 1 listening
        response_detected = False
        while not response_detected:
            response_detected = valid(listen())
        self.robot_guide_machine.send("response_detected")

        # state 2 following
        intersection_detected = False
        self.robot.FollowOn()
        while not intersection_detected:
            pass
        self.robot_guide_machine.send("intersection_detected")

        # state 3 turning
        turning = True
        while turning:
            if self.robot_guide_machine.turning_right.is_active:
                self.robot_guide_machine.send("turning_right")
                turning = False
            else:
                self.robot_guide_machine.send("turning_left")
                turning = False


        # state 4 end
        final_drive = True
        while final_drive:
            if self.robot_guide_machine.final_navigation.is_active:
                self.robot_guide_machine.send("destination_reached")
                final_drive = False
        '''

