#states: waiting, greeting, listening, turning, following, turning, following, finished
import time

import json
import queue
import sys
import threading

import pyaudio
import sounddevice as sd


from statemachine import StateChart, State, StateMachine

from services.text_to_speech import TextToSpeech
from vosk import Model, KaldiRecognizer

MODEL_PATH = "static/vosk-model-small-en-us-0.15"

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


def listen_complete(model_path: str,
    phrases: list[str],
    sample_rate: int = 16000,
    device_index: int = None,
    chunk_size: int = 8000,
) -> str:
    """
    Listens to microphone input and returns the first matching phrase found.

    Args:
        model_path:   Path to a local Vosk model directory.
        phrases:      List of phrases to listen for.
        sample_rate:  Microphone sample rate in Hz (Vosk expects 16000).
        device_index: PyAudio device index. Run list_input_devices() to find it.
        chunk_size:   Audio chunk size in frames.

    Returns:
        The first phrase detected.
    """
    print(f"Loading Vosk model from '{model_path}'...")
    model = Model(model_path)
    recognizer = KaldiRecognizer(model, sample_rate)
    recognizer.SetWords(True)

    phrase_list = [p.lower() for p in phrases]
    result_queue = queue.Queue()

    print(f"Listening for: {phrase_list}... (Ctrl+C to stop)\n")

    def check_and_dispatch(text: str):
        for phrase in phrase_list:
            if phrase in text:
                result_queue.put(phrase)

    p = pyaudio.PyAudio()
    stream = p.open(
        format=pyaudio.paInt16,
        channels=1,
        rate=sample_rate,
        input=True,
        input_device_index=device_index,
        frames_per_buffer=chunk_size,
    )

    try:
        while result_queue.empty():
            data = stream.read(chunk_size, exception_on_overflow=False)

            if recognizer.AcceptWaveform(data):
                result = json.loads(recognizer.Result())
                transcript = result.get("text", "").lower()
                if transcript:
                    check_and_dispatch(transcript)
            else:
                partial = json.loads(recognizer.PartialResult())
                partial_text = partial.get("partial", "").lower()
                if partial_text:
                    check_and_dispatch(partial_text)

        return result_queue.get()

    except KeyboardInterrupt:
        print("\nStopped.")
        return None
    finally:
        stream.stop_stream()
        stream.close()
        p.terminate()


def listen():
    time.sleep(2)
    return "robot lab"


def listen_fake():
    phrase = listen_complete(
        model_path=MODEL_PATH,
        phrases=["robot lab", "bathroom"],
    )
    return phrase


class RobotGuide:
    def __init__(self, robot):
        self.robot_guide_machine = RobotGuideMachine(self)
        self.robot = robot
        self.tts = TextToSpeech()
        self.destination = ""

    def valid(self, response):
        if response == "bathroom":
            print("bathroom")
            self.destination = "bathroom"
            self.robot.FollowMode = True
            return True
        if response == "robot lab":
            self.destination = "robot lab"
            self.robot.FollowMode = False
            return True
        return False

    def on_human_detected(self):
        print("speaking...")
        self.tts.speak("hello, how can I help you", None, False)
        self.robot_guide_machine.send("greeting_finished")

    def on_greeting_finished(self):
        print("listening...")
        self.robot.FollowSide = True
        self.robot_guide_machine.send("response_detected", listen_fake())

    def on_response_detected(self):
        time.sleep(2)
        self.robot.drive_joystick(50, 50)
        if self.destination == "bathroom":
            time.sleep(1)
        else:
            time.sleep(1.4)
        self.robot.drive_joystick(0, 0)
        print("turning...")
        self.robot_guide_machine.send("turning_around_complete")

    def on_turning_around_complete(self):
        print("finding wall...")
        self.robot_guide_machine.send("aligning_complete")

    def on_aligning_complete(self):
        print("driving...")
        self.robot.FollowOn = True
        print(self.robot.FollowMode)
        time.sleep(3)
        #stop_event = threading.Event()
        #thread = threading.Thread(target=self.worker, args=(stop_event,))
        #thread.start()
        #thread.join()
        #while not intersection:
        #    intersection = self.robot.lidar.intersect_flag
        time.sleep(0.5)
        self.robot_guide_machine.send("intersection_detected")

    def on_intersection_detected(self):
        self.robot.FollowOn = False
        self.robot.stop()
        print("turning...")
        if self.destination == "robot lab":
            #self.robot.drive_joystick(50, 50)
            pass
        else:
            #self.robot.drive_joystick(-50, 50)
            pass
        time.sleep(0.4)
        self.robot_guide_machine.send("turning_complete")



    def on_turning_complete(self):
        print("driving...")
        self.robot.drive_joystick(0, 50)
        time.sleep(1)
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

    def worker(self, stop_event: threading.Event):
        """
        Runs in a background thread until stop_event is set.
        Accumulates results, then returns when the condition is met.
        """
        while not stop_event.is_set():
            intersect = self.robot.lidar.intersect_flag
            time.sleep(0.5)
            if intersect:
                stop_event.set()

        print(f"Worker done")





