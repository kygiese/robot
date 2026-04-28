import json
import sys

import pyaudio
from vosk import KaldiRecognizer, Model


def list_input_devices():
    """Print all available PyAudio input devices."""
    p = pyaudio.PyAudio()
    print("Available input devices:")
    for i in range(p.get_device_count()):
        info = p.get_device_info_by_index(i)
        if info["maxInputChannels"] > 0:
            print(f"  [{i}] {info['name']}")
    p.terminate()


def listen_for_phrases(
    model_path: str,
    phrases: dict[str, callable],
    sample_rate: int = 16000,
    device_index: int = None,
    chunk_size: int = 8000,
):
    """
    Continuously listens to microphone input and triggers a per-phrase
    callback whenever a registered phrase is detected.

    Args:
        model_path:   Path to a local Vosk model directory.
                      Download models from https://alphacephei.com/vosk/models
                      e.g. "models/vosk-model-small-en-us-0.15"
        phrases:      Dict mapping phrase strings to callback functions.
                      Each callback receives (phrase, transcript) as arguments.
                      Example: {"robot lab": on_robot_lab, "launch sequence": on_launch}
        sample_rate:  Microphone sample rate in Hz (Vosk expects 16000).
        device_index: PyAudio device index to use. Defaults to system default.
                      Run list_input_devices() to find the right index.
        chunk_size:   Audio chunk size in frames.
    """
    if not phrases:
        raise ValueError("Provide at least one phrase to listen for.")

    print(f"Loading Vosk model from '{model_path}'...")
    model = Model(model_path)
    recognizer = KaldiRecognizer(model, sample_rate)
    recognizer.SetWords(True)

    phrase_list = {p.lower(): cb for p, cb in phrases.items()}
    print(f"Listening for: {list(phrase_list.keys())}... (Ctrl+C to stop)\n")

    def check_and_dispatch(text: str, is_partial: bool = False):
        for phrase, callback in phrase_list.items():
            if phrase in text:
                label = "partial" if is_partial else "heard"
                print(f"  [{label}] '{text}'")
                print(f"  ✅ Matched: '{phrase}'")
                callback(phrase, text)

    p = pyaudio.PyAudio()

    idx = device_index if device_index is not None else p.get_default_input_device_info()["index"]
    info = p.get_device_info_by_index(idx)
    print(f"Using device: [{info['index']}] {info['name']}\n")

    stream = p.open(
        format=pyaudio.paInt16,
        channels=1,
        rate=sample_rate,
        input=True,
        input_device_index=device_index,
        frames_per_buffer=chunk_size,
    )

    try:
        while True:
            data = stream.read(chunk_size, exception_on_overflow=False)

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
    finally:
        stream.stop_stream()
        stream.close()
        p.terminate()


if __name__ == "__main__":
    # Small English model (~40MB): https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip
    MODEL_PATH = "models/vosk-model-small-en-us-0.15"

    # Uncomment to find your device index:
    # list_input_devices()

    def on_robot_lab(phrase, transcript):
        print(f"  → Robot lab action triggered!\n")

    def on_launch_sequence(phrase, transcript):
        print(f"  → Launch sequence initiated!\n")

    listen_for_phrases(
        model_path=MODEL_PATH,
        phrases={
            "robot lab": on_robot_lab,
            "launch sequence": on_launch_sequence,
        },
        # device_index=1,  # uncomment and set if default device is wrong
    )