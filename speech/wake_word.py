#!/usr/bin/env python3

"""
Wake Word Detection Module for Muninn
Handles Porcupine integration for wake word detection
"""

import time
import struct
import pyaudio
import pvporcupine
from typing import Optional


class WakeWordDetector:
    """Wake word detector using Porcupine"""

    def __init__(self, access_key: str, wake_word_path: str, audio_device_index: Optional[int] = None, audio: Optional[pyaudio.PyAudio] = None):
        self.access_key = access_key
        self.wake_word_path = wake_word_path
        self.audio_device_index = audio_device_index
        self.audio = audio
        self.porcupine = None

        # Audio settings
        self.sample_rate = 16000
        self.channels = 1
        self.frame_length = 512

        self._initialize_porcupine()

    def _initialize_porcupine(self):
        """Initialize Porcupine wake word detector"""
        try:
            self.porcupine = pvporcupine.create(
                access_key=self.access_key,
                keyword_paths=[self.wake_word_path]
            )
            print(f"✓ Porcupine wake word detector initialized")
        except Exception as e:
            print(f"❌ Failed to initialize Porcupine: {e}")
            raise

    def listen_for_wake_word(self, timeout: Optional[int] = None) -> bool:
        """
        Listen for wake word detection

        Args:
            timeout: Maximum time to listen in seconds (None for indefinite)

        Returns:
            bool: True if wake word detected, False if timeout
        """
        print("🎤 Listening for wake word...")

        stream = None
        try:
            stream = self.audio.open(
                rate=self.sample_rate,
                channels=self.channels,
                format=pyaudio.paInt16,
                input=True,
                input_device_index=self.audio_device_index,
                frames_per_buffer=self.frame_length
            )

            start_time = time.time()

            while True:
                if timeout and (time.time() - start_time) > timeout:
                    return False

                try:
                    pcm = stream.read(self.frame_length, exception_on_overflow=False)
                    pcm_int = struct.unpack_from(f'{self.frame_length}h', pcm)

                    keyword_index = self.porcupine.process(pcm_int)

                    if keyword_index >= 0:
                        print("🎯 Wake word detected!")
                        return True

                except Exception as e:
                    print(f"❌ Audio processing error: {e}")
                    time.sleep(0.1)
                    continue

        except Exception as e:
            print(f"❌ Wake word detection error: {e}")
            return False

        finally:
            if stream:
                try:
                    stream.stop_stream()
                    stream.close()
                except:
                    pass

    def cleanup(self):
        """Clean up resources"""
        try:
            if self.porcupine:
                self.porcupine.delete()
                print("✓ Porcupine cleaned up")
        except:
            pass


class MockWakeWordDetector:
    """Mock wake word detector for testing"""

    def __init__(self, access_key: str, wake_word_path: str, audio_device_index: Optional[int] = None, audio: Optional[pyaudio.PyAudio] = None):
        print("Mock wake word detector initialized")

    def listen_for_wake_word(self, timeout: Optional[int] = None) -> bool:
        """Mock wake word detection - always returns True after delay"""
        print("🎤 [MOCK] Listening for wake word...")
        time.sleep(2)  # Simulate listening time
        print("🎯 [MOCK] Wake word detected!")
        return True

    def cleanup(self):
        """Mock cleanup"""
        print("✓ [MOCK] Wake word detector cleaned up")


def get_wake_word_detector(access_key: str, wake_word_path: str, audio_device_index: Optional[int] = None, audio: Optional[pyaudio.PyAudio] = None, mock_mode: bool = False) -> WakeWordDetector:
    """
    Factory function to get appropriate wake word detector

    Args:
        access_key: Picovoice access key
        wake_word_path: Path to wake word model file
        audio_device_index: Audio device index for input
        audio: PyAudio instance
        mock_mode: Use mock detector instead of real detector

    Returns:
        WakeWordDetector instance
    """
    if mock_mode:
        return MockWakeWordDetector(access_key, wake_word_path, audio_device_index, audio)

    return WakeWordDetector(access_key, wake_word_path, audio_device_index, audio)