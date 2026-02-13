# Robot Control System

A modular robot control system with organized code structure following best practices for hardware abstraction and component-based design.

## Project Structure

```
robot/
├── robot_parts/          # Robot component classes
│   ├── wheel.py         # Wheel control with vector-based movement
│   ├── head.py          # Head pan/tilt control
│   ├── waist.py         # Waist rotation control
│   └── arm.py           # Arm joints control
├── controllers/          # Hardware controllers
│   └── maestro.py       # Pololu Maestro servo controller
├── services/            # Service modules
│   └── text_to_speech.py # Text-to-speech service (espeak)
├── robot.py             # High-level Robot class
├── robot_control.py     # Robot control layer
├── app.py              # Flask web server
├── main.py             # Main entry point
└── babysfirsttest.py   # Hardware test script
```

## Design Pattern

This codebase follows a **component-based architecture** where:

1. **Low-level control exists in component classes** - Each robot part (wheels, head, waist, arm) has its own class that encapsulates:
   - Center position and limits
   - Direct hardware control methods
   - Movement logic specific to that component

2. **Vector-based movement** - The Wheel class now supports `move(left_vector, right_vector)` for intuitive control:
   ```python
   # Move forward: left wheel backward vector, right wheel forward vector
   wheels.move(-1000, 1000)
   
   # Stop: both wheels at center (vector = 0)
   wheels.move(0, 0)
   ```

3. **Separation of concerns**:
   - `robot_parts/` - Physical component control
   - `controllers/` - Hardware communication layer (Maestro servo controller)
   - `services/` - Utility services (text-to-speech)
   - Root level - High-level robot logic and interfaces

## Key Features

### Component Classes (robot_parts/)

Each component class manages its own:
- **Limits**: Min/max values for safe operation
- **Center position**: Neutral/stopped state
- **Control methods**: Component-specific movement functions

Example - Wheel class:
```python
from robot_parts.wheel import Wheel

wheels = Wheel(min_val=4000, max_val=8000)
wheels.move(-1000, 1000)  # Move with vectors
wheels.stop()             # Return to center
```

### Text-to-Speech Service (services/)

Centralized text-to-speech functionality:
```python
from services.text_to_speech import TextToSpeech

tts = TextToSpeech()
tts.speak("Hello, world!")
```

Supports:
- espeak (Linux/Raspberry Pi)
- say (macOS)
- Fallback to console output

### Robot Control Layer

The `robot_control.py` provides a unified, thread-safe interface:
- Normalized control values (-100 to 100)
- Safety features (heartbeat, auto-stop)
- Mock mode for testing without hardware

### Web Interface

Flask-based web server (`app.py`) provides:
- REST API for robot control
- Joystick-based driving
- Head and waist control
- Text-to-speech output

## Usage

### Running the Web Interface

```bash
python app.py
```

Access at: `http://localhost:5000/`

### Direct Control

```python
from robot_parts.wheel import Wheel

# Create wheel controller with limits
wheels = Wheel(min_val=4000, max_val=8000)

# Move with vectors relative to center (6000)
wheels.move(-1000, 1000)  # Forward motion

# Or use convenience methods
wheels.forward(time=2, speed=1000)
wheels.backward(time=2, speed=1000)
wheels.stop()
```

### Text-to-Speech

```python
from services.text_to_speech import TextToSpeech

tts = TextToSpeech(default_speed=100)
tts.speak("Robot initialized", async_mode=True)
```

## Benefits of This Structure

1. **Easier to modify** - Want to change wheel limits? Edit `robot_parts/wheel.py` only
2. **Clear separation** - Each module has a single responsibility
3. **Testable** - Components can be tested independently
4. **Reusable** - Robot parts can be used in different projects
5. **Maintainable** - New developers can understand the structure quickly

## Hardware Requirements

- Pololu Maestro servo controller (connected via /dev/ttyACM0)
- Servo motors for wheels, head, waist, and arms
- Optional: espeak for text-to-speech

## Dependencies

```bash
pip install -r requirements.txt
```

Required packages:
- Flask (web interface)
- flask-cors (CORS support)
- pyserial (serial communication)
