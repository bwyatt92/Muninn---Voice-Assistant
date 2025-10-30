#!/usr/bin/env python3

"""
Muninn Voice Assistant - Modular Version
Main application coordinator that orchestrates all components
"""

import os
import sys
import time
import pyaudio
from typing import Optional

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config.settings import MuninnConfig
from speech import get_tts_engine, get_wake_word_detector, get_speech_recognizer
from commands import get_command_processor
from audio import get_audio_manager
from hardware import get_hardware_controller, StatusState


class MuninnVoiceAssistant:
    """
    Modular Muninn Voice Assistant
    Coordinates all components for voice interaction
    """

    def __init__(self,
                 access_key: str,
                 wake_word_path: str = "./munin_en_raspberry-pi_v3_0_0.ppn",
                 vosk_model_path: str = "./vosk-model-small-en-us-0.15",
                 voice: str = 'expr-voice-4-f',
                 mock_mode: bool = False):

        self.access_key = access_key
        self.wake_word_path = wake_word_path
        self.vosk_model_path = vosk_model_path
        self.voice = voice
        self.mock_mode = mock_mode

        # Hardware detection
        self.respeaker_index = None
        self.audio = None

        # Component instances
        self.tts_engine = None
        self.wake_word_detector = None
        self.speech_recognizer = None
        self.command_processor = None
        self.audio_manager = None
        self.hardware_controller = None

        print("🧙‍♂️ Initializing Modular Muninn Voice Assistant...")
        self._initialize_components()

    def _initialize_components(self):
        """Initialize all voice assistant components"""
        try:
            # Initialize PyAudio
            self.audio = pyaudio.PyAudio()
            print("✓ PyAudio initialized")

            # Find ReSpeaker device (unless in mock mode)
            if not self.mock_mode:
                if not self._find_respeaker():
                    print("❌ ReSpeaker not found, using default audio device")
                    self.respeaker_index = None

            # Initialize components using factory functions
            self.tts_engine = get_tts_engine(
                voice=self.voice,
                audio_device_index=self.respeaker_index,
                audio=self.audio,
                mock_mode=self.mock_mode
            )

            self.wake_word_detector = get_wake_word_detector(
                access_key=self.access_key,
                wake_word_path=self.wake_word_path,
                audio_device_index=self.respeaker_index,
                audio=self.audio,
                mock_mode=self.mock_mode
            )

            self.speech_recognizer = get_speech_recognizer(
                vosk_model_path=self.vosk_model_path,
                audio_device_index=self.respeaker_index,
                audio=self.audio,
                mock_mode=self.mock_mode
            )

            self.audio_manager = get_audio_manager(
                audio_device_index=self.respeaker_index,
                audio=self.audio,
                mock_mode=self.mock_mode
            )

            self.command_processor = get_command_processor(
                tts_engine=self.tts_engine,
                audio_manager=self.audio_manager,
                mock_mode=self.mock_mode
            )

            self.hardware_controller = get_hardware_controller(
                mock_mode=self.mock_mode
            )

            print("🎉 Modular Muninn ready!")

        except Exception as e:
            print(f"❌ Failed to initialize: {e}")
            raise

    def _find_respeaker(self) -> bool:
        """Find ReSpeaker device"""
        print("🔍 Searching for ReSpeaker...")

        for i in range(self.audio.get_device_count()):
            info = self.audio.get_device_info_by_index(i)
            if info['maxInputChannels'] > 0:
                print(f"  {i}: {info['name']} (channels: {info['maxInputChannels']})")
                if "ReSpeaker" in info['name']:
                    self.respeaker_index = i
                    print(f"✓ Found ReSpeaker at index {i}")
                    return True

        return False

    def run(self):
        """Main execution loop"""
        print("Starting Muninn Voice Assistant...")

        # Initial greeting and set initial hardware status
        self.tts_engine.speak("Muninn is ready to serve you. Say my name to begin.")
        self.hardware_controller.set_status(StatusState.WAKE_WORD_LISTENING)

        try:
            conversation_turns = 0

            while True:
                print("\n🎤 Listening for wake word...")
                self.hardware_controller.set_status(StatusState.WAKE_WORD_LISTENING)

                # Check for mute button during wake word listening
                mute_pressed = self.hardware_controller.check_mute_button()
                if mute_pressed:
                    print("🔇 Mute button pressed - temporarily muting")
                    self.hardware_controller.set_status(StatusState.MUTED)
                    time.sleep(1.0)  # Show muted state briefly (reduced from 2.0)
                    continue

                wake_detected = self.wake_word_detector.listen_for_wake_word(timeout=30)

                if wake_detected:
                    print("✅ Wake word detected!")
                    time.sleep(0.1)  # Reduced from 0.2 for faster response
                    conversation_turns = 0  # Reset conversation counter

                    # Start conversation mode
                    in_conversation = True

                    while in_conversation:
                        # Prompt user for first command or follow-up
                        if conversation_turns == 0:
                            self.hardware_controller.set_status(StatusState.SPEAKING)
                            self.tts_engine.speak("How may I serve you?")
                        else:
                            # Brief pause before listening for follow-up
                            print("💬 Listening for follow-up command...")
                            time.sleep(0.1)  # Reduced from 0.3 for faster response

                        # Set status for command listening
                        self.hardware_controller.set_status(StatusState.COMMAND_LISTENING)

                        # Listen for command
                        timeout = MuninnConfig.FOLLOW_UP_TIMEOUT if conversation_turns > 0 else 8
                        command_result = self.speech_recognizer.listen_for_command(timeout=timeout)

                        if command_result['understood']:
                            # Set processing status while handling command
                            self.hardware_controller.set_status(StatusState.PROCESSING)

                            conversation_state = self.command_processor.process_command(
                                command_result['intent'],
                                command_result['slots']
                            )

                            conversation_turns += 1

                            # Check if we should continue conversation
                            if (conversation_state['continue_conversation'] and
                                conversation_turns < MuninnConfig.MAX_CONVERSATION_TURNS):
                                in_conversation = True
                                print(f"💬 Conversation turn {conversation_turns}, continuing...")
                            else:
                                in_conversation = False
                                if conversation_turns >= MuninnConfig.MAX_CONVERSATION_TURNS:
                                    print(f"💬 Reached max conversation turns ({MuninnConfig.MAX_CONVERSATION_TURNS}), returning to wake word mode")
                                else:
                                    print("💬 Command ended conversation, returning to wake word mode")

                        else:
                            if conversation_turns == 0:
                                # First command not understood
                                self.hardware_controller.set_status(StatusState.ERROR)
                                self.tts_engine.speak("I did not understand that command. Please try again.")
                                in_conversation = False
                            else:
                                # Follow-up command timeout or not understood
                                if command_result['intent'] == 'timeout':
                                    print("💬 Follow-up timeout, returning to wake word mode")
                                    in_conversation = False
                                else:
                                    # Command not understood but stay in conversation for one more try
                                    self.hardware_controller.set_status(StatusState.SPEAKING)
                                    self.tts_engine.speak("I didn't catch that. Please try again.")
                                    conversation_turns += 1  # Count this as a turn
                                    if conversation_turns >= MuninnConfig.MAX_CONVERSATION_TURNS:
                                        print("💬 Reached max turns after misunderstanding, returning to wake word mode")
                                        in_conversation = False
                                    else:
                                        print(f"💬 Command not understood, staying in conversation (turn {conversation_turns})")
                                        in_conversation = True

                    time.sleep(0.1)  # Reduced from 0.2 for faster wake word listening
                else:
                    print("⏰ Wake word timeout - trying again...")

        except KeyboardInterrupt:
            print("\n🛑 Shutting down...")
        except Exception as e:
            print(f"❌ Runtime error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            self.cleanup()

    def cleanup(self):
        """Clean up all resources"""
        try:
            if self.hardware_controller:
                self.hardware_controller.cleanup()
            if self.wake_word_detector:
                self.wake_word_detector.cleanup()
            if self.audio:
                self.audio.terminate()
                print("✓ Audio resources cleaned up")
        except Exception as e:
            print(f"❌ Cleanup error: {e}")


def main():
    """Main entry point"""
    # Configuration
    access_key = 'rH1XROuTeb28rsds7Ntcrx1keazKZWxxUA2m1NhQzLKYgpF8rma+UQ=='

    # Determine if we should use mock mode
    mock_mode = len(sys.argv) > 1 and sys.argv[1] == '--mock'

    if mock_mode:
        print("🎭 Running in MOCK mode for testing")

    try:
        assistant = MuninnVoiceAssistant(
            access_key=access_key,
            voice='expr-voice-4-f',
            mock_mode=mock_mode
        )
        assistant.run()
    except Exception as e:
        print(f"❌ Failed to start Muninn: {e}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())