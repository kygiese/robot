#states: waiting, greeting, listening, turning, following, turning, following, finished
import time

import json
import queue
import sys
import threading

import sounddevice as sd


from statemachine import StateChart, State, StateMachine

from services.text_to_speech import TextToSpeech
from vosk import Model, KaldiRecognizer

MODEL_PATH = "static\\vosk-model-small-en-us-0.15"

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




'''
if __name__ == "__main__":
    # Download a model and point this path to it.
    # Small English model (~40MB): https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip
    MODEL_PATH = "models/vosk-model-small-en-us-0.15"

    listen_for_robot_lab(model_path=MODEL_PATH)
'''



def average(scan_data):
    s = 0
    i = 1
    for data in scan_data:
        if data > 0:
            s += data
            i += 1
    return s / i


def listen_complete(model_path: str, phrases: dict[str, callable], sample_rate: int = 16000):
    """
    Continuously listens to microphone input and triggers a per-phrase
    callback whenever a registered phrase is detected.

    Args:
    model_path:  Path to a local Vosk model directory.
                 Download models from https://alphacephei.com/vosk/models
                 e.g. "models/vosk-model-small-en-us-0.15"
    phrases:     Dict mapping phrase strings to callback functions.
                 Each callback receives (phrase, transcript) as arguments.
                 Example: {"robot lab": on_robot_lab, "launch sequence": on_launch}
    sample_rate: Microphone sample rate in Hz (Vosk expects 16000).
    """
    if not phrases:
        raise ValueError("Provide at least one phrase to listen for.")

    print(f"Loading Vosk model from '{model_path}'...")
    model = Model(model_path)
    recognizer = KaldiRecognizer(model, sample_rate)
    recognizer.SetWords(True)

    audio_queue = queue.Queue()
    phrase_list = {p.lower(): cb for p, cb in phrases.items()}

    print(f"Listening for: {[p for p in phrase_list]}... (Ctrl+C to stop)\n")

    def audio_callback(indata, frames, time, status):
        if status:
            print(f"[audio warning] {status}", file=sys.stderr)
        audio_queue.put(bytes(indata))

    def check_and_dispatch(text: str, is_partial: bool = False):
        """Check transcript against all phrases and fire matching callbacks."""
        for phrase, callback in phrase_list.items():
            if phrase in text:
                label = "partial" if is_partial else "heard"
                print(f"  [{label}] '{text}'")
                print(f"  ✅ Matched: '{phrase}'")
                callback(phrase, text)

    try:
        with sd.RawInputStream(
            samplerate=sample_rate,
            blocksize=8000,
            dtype="int16",
            channels=1,
            callback=audio_callback,
        ):
            while True:
                data = audio_queue.get()

                if recognizer.AcceptWaveform(data):
                    result = json.loads(recognizer.Result())
                    transcript = result.get("text", "").lower()
                    if transcript:
                        check_and_dispatch(transcript, is_partial=False)
                else:
                    partial = json.loads(recognizer.PartialResult())
                    partial_text = partial.get("partial", "").lower()
                    if partial_text:
                        check_and_dispatch(partial_text, is_partial=True)

    except KeyboardInterrupt:
        print("\nStopped.")
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        raise


def listen():
    time.sleep(2)
    return "bathroom"


class RobotGuide:
    def __init__(self, robot):
        self.robot_guide_machine = RobotGuideMachine(self)
        self.robot = robot
        self.tts = TextToSpeech()
        self.destination = ""

    def valid(self, response):
        if response == "bathroom":
            self.destination = "bathroom"
            return True
        if response == "robot lab":
            self.destination = "robot lab"
            return True
        return False

    def on_human_detected(self):
        print("speaking...")
        self.tts.speak("hello, how can I help you", None, False)
        self.robot_guide_machine.send("greeting_finished")

    def on_greeting_finished(self):
        print("listening...")
        #listen_fake()
        #then remove valid check
        self.robot_guide_machine.send("response_detected", listen())

    def on_response_detected(self):
        self.tts.speak("follow me")
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
        time.sleep(2)
        while not intersection:
            intersection = self.robot.lidar.intersect_flag
        time.sleep(0.3)
        self.robot_guide_machine.send("intersection_detected")

    def on_intersection_detected(self):
        self.robot.FollowOn = False
        self.robot.stop()
        print("turning...")
        if self.destination == "robot lab":
            self.robot.drive_joystick(50, 50)
        else:
            self.robot.drive_joystick(-50, 50)
        time.sleep(0.4)
        self.robot.drive_joystick(0, 0)
        self.robot_guide_machine.send("turning_complete")

    def on_turning_complete(self):
        print("driving...")
        self.robot.drive_joystick(0, 50)
        time.sleep(2)
        self.robot.drive_joystick(0, 0)
        self.robot_guide_machine.send("destination_reached")

    def after_destination_reached(self):
        self.tts.speak("We have arrived at the " + self.destination, None, False)
        print("speaking...")

    def guide(self):
        # state 0 waiting for person
        print("starting..........")
        human_detected = False
        while not human_detected:
            if self.robot.lidar.checkF:
                human_detected = True
        self.robot_guide_machine.send("human_detected")

    def on_robot_lab(self, phrase, transcript):
        print(f"  → Robot lab action triggered!\n")
        self.destination = "robot lab"

    def on_bathroom(self, phrase, transcript):
        print(f"  → Bathroom initiated!\n")
        self.destination = "bathroom"

    def listen_fake(self):
        listen_complete(model_path=MODEL_PATH, phrases={"robot lab": self.on_robot_lab, "bathroom": self.on_bathroom})

