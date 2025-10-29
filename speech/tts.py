#!/usr/bin/env python3

"""
Text-to-Speech Module for Muninn
Handles KittenTTS integration and audio playback
"""

import time
import pyaudio
import numpy as np
from typing import Optional

# KittenTTS imports with availability check
KITTENTTS_AVAILABLE = False
try:
    import soundfile as sf
    import librosa
    from kittentts import KittenTTS
    KITTENTTS_AVAILABLE = True
except ImportError as e:
    print(f"KittenTTS not available: {e}")
except Exception as e:
    print(f"Error loading KittenTTS: {e}")


class TTSEngine:
    """Text-to-Speech engine using KittenTTS"""

    def __init__(self, voice: str = 'expr-voice-4-f', audio_device_index: Optional[int] = None, audio: Optional[pyaudio.PyAudio] = None):
        self.voice = voice
        self.audio_device_index = audio_device_index
        self.audio = audio
        self.tts = None

        if KITTENTTS_AVAILABLE:
            try:
                print("Loading KittenTTS model...")
                self.tts = KittenTTS("KittenML/kitten-tts-nano-0.2")
                print(f"✓ KittenTTS initialized with voice: {voice}")
            except Exception as e:
                print(f"❌ Error loading KittenTTS: {e}")
                self.tts = None

    def speak(self, text: str) -> bool:
        """
        Convert text to speech and play through audio device

        Args:
            text: Text to speak

        Returns:
            bool: True if successful, False otherwise
        """
        # Clean text for better TTS processing
        cleaned_text = text.replace("°", " degrees").replace("fahrenheit", "").strip()

        # Ensure sentence ends with punctuation for proper TTS
        if cleaned_text and not cleaned_text.endswith(('.', '!', '?')):
            cleaned_text += '.'

        print(f"🗣️ Muninn says: '{cleaned_text}'")

        if not self.tts:
            print("TTS not available - would speak:", cleaned_text)
            time.sleep(2)  # Simulate speaking time
            return False

        try:
            # Generate audio with KittenTTS using cleaned text
            audio = self.tts.generate(cleaned_text, voice=self.voice)

            # Convert to ReSpeaker's format: 16kHz, mono, int16
            audio_16k = librosa.resample(audio, orig_sr=24000, target_sr=16000)
            audio_int16 = (audio_16k * 32767).astype(np.int16)

            # Use PyAudio streaming
            stream = self.audio.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=16000,
                output=True,
                output_device_index=self.audio_device_index,
                frames_per_buffer=1024
            )

            # Stream audio in chunks
            CHUNK = 1024
            for i in range(0, len(audio_int16), CHUNK):
                chunk = audio_int16[i:i+CHUNK]
                if len(chunk) < CHUNK:
                    chunk = np.pad(chunk, (0, CHUNK - len(chunk)), 'constant')
                stream.write(chunk.tobytes())

            # Brief wait to ensure stream completes
            time.sleep(0.1)

            stream.stop_stream()
            stream.close()

            print("✅ TTS playback completed!")
            return True

        except Exception as e:
            print(f"Error in KittenTTS: {e}")
            return False

    def is_available(self) -> bool:
        """Check if TTS is available and initialized"""
        return self.tts is not None


class MockTTSEngine:
    """Mock TTS engine for testing without hardware"""

    def __init__(self, voice: str = 'mock', audio_device_index: Optional[int] = None, audio: Optional[pyaudio.PyAudio] = None):
        self.voice = voice
        print("Mock TTS engine initialized")

    def speak(self, text: str) -> bool:
        """Mock speech - just print and simulate time"""
        print(f"🗣️ [MOCK] Muninn says: '{text}'")
        time.sleep(1)  # Simulate speaking time
        return True

    def is_available(self) -> bool:
        """Mock TTS is always available"""
        return True


def get_tts_engine(voice: str = 'expr-voice-4-f', audio_device_index: Optional[int] = None, audio: Optional[pyaudio.PyAudio] = None, mock_mode: bool = False) -> TTSEngine:
    """
    Factory function to get appropriate TTS engine

    Args:
        voice: Voice to use for TTS
        audio_device_index: Audio device index for output
        audio: PyAudio instance
        mock_mode: Use mock TTS instead of real TTS

    Returns:
        TTSEngine instance
    """
    if mock_mode or not KITTENTTS_AVAILABLE:
        return MockTTSEngine(voice, audio_device_index, audio)

    return TTSEngine(voice, audio_device_index, audio)