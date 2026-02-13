"""
Text-to-Speech Service

This module provides a unified interface for text-to-speech functionality
using espeak or other available TTS engines.
"""

import subprocess
import threading


class TextToSpeech:
    """
    Text-to-speech service that uses espeak or fallback TTS engines.
    
    This class encapsulates all text-to-speech functionality, making it
    easy to change TTS engines or settings in one place.
    """
    
    def __init__(self, default_speed=100, timeout=10):
        """
        Initialize the text-to-speech service.
        
        Args:
            default_speed: Default speaking speed (words per minute for espeak)
            timeout: Maximum time to allow for speech command execution (seconds)
        """
        self.default_speed = default_speed
        self.timeout = timeout
        self._tts_engine = self._detect_tts_engine()
    
    def _detect_tts_engine(self):
        """
        Detect which TTS engine is available on the system.
        
        Returns:
            str: Name of available TTS engine ('espeak', 'say', or 'none')
        """
        # Try espeak (common on Linux/Raspberry Pi)
        try:
            subprocess.run(["espeak", "--version"], capture_output=True, timeout=2)
            return "espeak"
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass
        
        # Try say (macOS)
        try:
            subprocess.run(["say", "--version"], capture_output=True, timeout=2)
            return "say"
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass
        
        return "none"
    
    def speak(self, text, speed=None, async_mode=True):
        """
        Speak the given text using the available TTS engine.
        
        Args:
            text: Text to speak (string)
            speed: Speaking speed (words per minute for espeak), uses default if None
            async_mode: If True, speak in background thread (non-blocking)
            
        Returns:
            dict: Status information about the speech request
        """
        if speed is None:
            speed = self.default_speed
        
        # Limit text length for safety
        text = str(text)[:200]
        
        if async_mode:
            # Run speech in background thread to not block
            thread = threading.Thread(target=self._speak_sync, args=(text, speed))
            thread.daemon = True
            thread.start()
            return {"status": "ok", "text": text, "async": True}
        else:
            # Run synchronously
            return self._speak_sync(text, speed)
    
    def _speak_sync(self, text, speed):
        """
        Internal method to speak synchronously.
        
        Args:
            text: Text to speak
            speed: Speaking speed
            
        Returns:
            dict: Status information
        """
        try:
            if self._tts_engine == "espeak":
                # espeak command with speed parameter
                subprocess.run(
                    ["espeak", text, "-s", str(speed)],
                    timeout=self.timeout,
                    capture_output=True
                )
                return {"status": "ok", "text": text, "engine": "espeak"}
            
            elif self._tts_engine == "say":
                # macOS say command (doesn't use speed parameter the same way)
                subprocess.run(
                    ["say", text],
                    timeout=self.timeout,
                    capture_output=True
                )
                return {"status": "ok", "text": text, "engine": "say"}
            
            else:
                # No TTS engine available - just print
                print(f"Speech output (no TTS available): {text}")
                return {"status": "ok", "text": text, "engine": "none"}
        
        except subprocess.TimeoutExpired:
            return {"status": "error", "message": "Speech timeout", "text": text}
        except Exception as e:
            return {"status": "error", "message": str(e), "text": text}
    
    def get_engine(self):
        """
        Get the name of the currently detected TTS engine.
        
        Returns:
            str: Name of TTS engine ('espeak', 'say', or 'none')
        """
        return self._tts_engine


# Predefined phrases for robot voice output
DEFAULT_PHRASES = [
    "Maybe Sisyphus wasn't happy.",
    "My favorite food is enriched uranium.",
    "Please do not touch my wheels.",
    "Bread before toasters."
]


def get_default_phrases():
    """Get list of default phrases for voice output"""
    return DEFAULT_PHRASES
