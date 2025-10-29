#!/usr/bin/env python3

"""
Command Processing Module for Muninn
Handles intent processing and response generation
"""

import os
import time
from typing import Dict, Any, Optional

from utils.time_weather import get_current_time, get_weather
from utils.jokes import get_random_joke, get_dad_joke
from audio.manager import AudioManager
from config.settings import MuninnConfig


class CommandProcessor:
    """Processes voice commands and generates appropriate responses"""

    def __init__(self, tts_engine, audio_manager: AudioManager):
        self.tts_engine = tts_engine
        self.audio_manager = audio_manager

    def process_command(self, intent: str, slots: Dict[str, Any]):
        """
        Process detected command and execute appropriate action

        Args:
            intent: The detected intent
            slots: Dictionary of extracted slot values

        Returns:
            Dict containing conversation state information
        """
        print(f"\n🎯 Processing command: {intent}")
        print(f"📦 Slots: {slots}")

        # Default conversation state - continue listening for follow-up
        conversation_state = {
            'continue_conversation': True,
            'timeout': MuninnConfig.FOLLOW_UP_TIMEOUT,
            'prompt_message': None
        }

        if intent == 'playAllMessages':
            self._handle_play_all_messages()

        elif intent == 'getMessage':
            person = slots.get('person', 'unknown')
            self._handle_get_message(person)

        elif intent == 'createMemory':
            self._handle_create_memory()
            # After recording, return to wake word mode
            conversation_state['continue_conversation'] = False

        elif intent == 'stop':
            self._handle_stop()
            # Stop command ends conversation
            conversation_state['continue_conversation'] = False

        elif intent == 'getTime':
            self._handle_get_time()

        elif intent == 'getWeather':
            self._handle_get_weather()

        elif intent == 'playLastRecording':
            self._handle_play_last_recording()

        elif intent == 'listMessages':
            self._handle_list_messages()

        elif intent == 'recordForPerson':
            person = slots.get('person', 'unknown')
            self._handle_record_for_person(person)
            # After recording, return to wake word mode
            conversation_state['continue_conversation'] = False

        elif intent == 'tellJoke':
            self._handle_tell_joke()

        elif intent == 'tellDadJoke':
            self._handle_tell_dad_joke()

        elif intent == 'timeout':
            self._handle_timeout()
            # Timeout ends conversation
            conversation_state['continue_conversation'] = False

        else:
            self._handle_unknown_command()

        return conversation_state

    def _handle_play_all_messages(self):
        """Handle playing all birthday messages - cycle through all family members"""
        family_members = self.audio_manager.get_all_family_members_with_messages()

        if not family_members:
            self.tts_engine.speak("I don't have any messages to play.")
            return

        message_counts = self.audio_manager.get_message_count_by_person()
        total_messages = sum(message_counts.values())

        self.tts_engine.speak(f"Playing all {total_messages} birthday messages from {len(family_members)} family members.")

        # Play messages from each family member
        for i, person in enumerate(family_members):
            messages = self.audio_manager.get_messages_for_person(person)
            if messages:
                self.tts_engine.speak(f"Messages from {person.title()}.")

                # Wait for TTS to finish and audio device to be released
                time.sleep(0.5)

                # Play each message for this person
                for j, message in enumerate(messages):
                    if os.path.exists(message['file_path']):
                        print(f"🎵 Playing message {j+1} from {person}: {os.path.basename(message['file_path'])}")
                        success = self.audio_manager.play_audio_file(message['file_path'])
                        if not success:
                            print(f"❌ Failed to play message from {person}")
                        # Brief pause between messages to ensure audio device is released
                        time.sleep(0.3)
                    else:
                        print(f"❌ Message file not found: {message['file_path']}")

                # Brief pause between family members (except for the last one)
                if i < len(family_members) - 1:
                    time.sleep(0.5)

        self.tts_engine.speak("All birthday messages have been played.")

    def _handle_get_message(self, person: str):
        """Handle getting a specific person's message"""
        # Map common name variations to actual family member names
        name_mapping = {
            # CARRIE variations
            'carrie': 'carrie',
            'carey': 'carrie',
            'carry': 'carrie',
            'caryl': 'carrie',
            'mom': 'carrie',
            # CASSIE variations
            'cassie': 'cassie',
            'cassidy': 'cassie',
            'cass': 'cassie',
            # SCOTT variations
            'scott': 'scott',
            'scotty': 'scott',
            # BEAU variations
            'beau': 'beau',
            'bo': 'beau',
            # LIZZIE variations
            'lizzie': 'lizzie',
            'liz': 'lizzie',
            'lizzy': 'lizzie',
            'elizabeth': 'lizzie',
            # JEAN variations
            'jean': 'jean',
            'jeanie': 'jean',
            # NICK variations
            'nick': 'nick',
            'nicholas': 'nick',
            'nicky': 'nick',
            # DAKOTA variations
            'dakota': 'dakota',
            'de': 'dakota',
            'kota': 'dakota',
            # BEA variations
            'bea': 'bea',
            'beatrice': 'bea',
            # CHARLIE variations
            'charlie': 'charlie',
            'charles': 'charlie',
            'chuck': 'charlie',
            # ALLIE variations
            'allie': 'allie',
            'ally': 'allie',
            'allison': 'allie',
            # LUKE variations
            'luke': 'luke',
            'lucas': 'luke',
            # LYRA variations
            'lyra': 'lyra',
            'lira': 'lyra',
            # TUI variations
            'tui': 'tui',
            'tooi': 'tui',
            'twi': 'tui',
            # SEVRO variations
            'sevro': 'sevro',
            'sev': 'sevro',
        }

        # Normalize the person name using the mapping
        normalized_person = name_mapping.get(person.lower(), person.lower())

        messages = self.audio_manager.get_messages_for_person(normalized_person)

        if not messages:
            self.tts_engine.speak(f"I don't have any messages from {person}.")
            return

        message_count = len(messages)
        if message_count == 1:
            self.tts_engine.speak(f"Playing {person}'s message.")
        else:
            self.tts_engine.speak(f"Playing {message_count} messages from {person}.")

        # Wait for TTS to finish and audio device to be released
        time.sleep(0.5)

        # Play all messages from this person
        for i, message in enumerate(messages):
            if os.path.exists(message['file_path']):
                print(f"🎵 Playing message {i+1}/{message_count} from {person}: {os.path.basename(message['file_path'])}")
                success = self.audio_manager.play_audio_file(message['file_path'])
                if not success:
                    print(f"❌ Failed to play message {i+1} from {person}")
                # Brief pause between messages to ensure audio device is released
                time.sleep(0.3)
            else:
                print(f"❌ Message file not found: {message['file_path']}")

        if message_count == 1:
            self.tts_engine.speak(f"That was {person}'s message.")
        else:
            self.tts_engine.speak(f"Those were all {message_count} messages from {person}.")

    def _handle_create_memory(self):
        """Handle recording a new memory"""
        self.tts_engine.speak("Recording your message now. Please speak clearly.")

        # Record audio for 10 seconds
        recording_file = self.audio_manager.record_audio(duration=10)

        if recording_file:
            self.tts_engine.speak("Recording complete. Your memory has been saved.")
            print(f"🎙️ Recorded: {recording_file}")
        else:
            self.tts_engine.speak("Sorry, there was an error with the recording.")
            print("❌ Recording failed")

    def _handle_stop(self):
        """Handle stop command"""
        self.tts_engine.speak("Stopping playback.")
        print("⏹️ Would stop playback...")

    def _handle_get_time(self):
        """Handle time request"""
        time_info = get_current_time()
        self.tts_engine.speak(time_info)
        print(f"🕐 Current time: {time_info}")

    def _handle_get_weather(self):
        """Handle weather request"""
        weather_info = get_weather()
        self.tts_engine.speak(weather_info)
        print(f"🌤️ Weather: {weather_info}")

    def _handle_play_last_recording(self):
        """Handle playing last recording"""
        last_recording = self.audio_manager.get_last_recording()

        if last_recording and os.path.exists(last_recording):
            self.tts_engine.speak("Playing your last recording.")
            success = self.audio_manager.play_audio_file(last_recording)
            if success:
                self.tts_engine.speak("Playback complete.")
            else:
                self.tts_engine.speak("Sorry, I couldn't play the recording.")
        else:
            recent_recordings = self.audio_manager.get_recent_recordings(1)
            if recent_recordings:
                self.tts_engine.speak("Playing your most recent recording.")
                success = self.audio_manager.play_audio_file(recent_recordings[0])
                if success:
                    self.tts_engine.speak("Playback complete.")
                else:
                    self.tts_engine.speak("Sorry, I couldn't play the recording.")
            else:
                self.tts_engine.speak("I don't have any recordings to play.")

    def _handle_timeout(self):
        """Handle command timeout"""
        self.tts_engine.speak("I did not hear a command. Returning to sleep mode.")

    def _handle_list_messages(self):
        """Handle listing messages command"""
        message_counts = self.audio_manager.get_message_count_by_person()

        if not message_counts:
            self.tts_engine.speak("There are no messages recorded yet.")
            return

        total_messages = sum(message_counts.values())
        family_count = len(message_counts)

        self.tts_engine.speak(f"I have {total_messages} messages from {family_count} family members.")

        # List each family member and their message count
        for person, count in message_counts.items():
            if count == 1:
                self.tts_engine.speak(f"{person.title()} has 1 message.")
            else:
                self.tts_engine.speak(f"{person.title()} has {count} messages.")

    def _handle_record_for_person(self, person: str):
        """Handle recording a message for a specific person"""
        # Map common name variations to actual family member names (same as _handle_get_message)
        name_mapping = {
            'carrie': 'carrie', 'carey': 'carrie', 'carry': 'carrie', 'caryl': 'carrie', 'mom': 'carrie',
            'cassie': 'cassie', 'cassidy': 'cassie', 'cass': 'cassie',
            'scott': 'scott', 'scotty': 'scott',
            'beau': 'beau', 'bo': 'beau',
            'lizzie': 'lizzie', 'liz': 'lizzie', 'lizzy': 'lizzie', 'elizabeth': 'lizzie',
            'jean': 'jean', 'jeanie': 'jean',
            'nick': 'nick', 'nicholas': 'nick', 'nicky': 'nick',
            'dakota': 'dakota', 'de': 'dakota', 'kota': 'dakota',
            'bea': 'bea', 'beatrice': 'bea',
            'charlie': 'charlie', 'charles': 'charlie', 'chuck': 'charlie',
            'allie': 'allie', 'ally': 'allie', 'allison': 'allie',
            'luke': 'luke', 'lucas': 'luke',
            'lyra': 'lyra', 'lira': 'lyra',
            'tui': 'tui', 'tooi': 'tui', 'twi': 'tui',
            'sevro': 'sevro', 'sev': 'sevro',
        }

        # Normalize the person name using the mapping
        normalized_person = name_mapping.get(person.lower(), person.lower())

        self.tts_engine.speak(f"Recording a message for {normalized_person}. Please speak clearly.")

        # Record audio for 10 seconds
        recording_file = self.audio_manager.record_audio(duration=10)

        if recording_file:
            # Save the message for the specific person
            success = self.audio_manager.save_message_for_person(
                normalized_person,
                recording_file,
                f"Birthday message for {normalized_person}"
            )

            if success:
                self.tts_engine.speak(f"Message for {normalized_person} has been saved.")
                print(f"🎙️ Recorded message for {normalized_person}: {recording_file}")
            else:
                self.tts_engine.speak("Sorry, there was an error saving the message.")
        else:
            self.tts_engine.speak("Sorry, there was an error with the recording.")
            print("❌ Recording failed")

    def _handle_tell_joke(self):
        """Handle telling a random joke"""
        self.tts_engine.speak("Here's a joke for you.")
        time.sleep(0.5)  # Brief pause before joke

        joke = get_random_joke()

        # Split joke at the pause for better comedic timing
        if "......" in joke:
            setup, punchline = joke.split("......", 1)
            self.tts_engine.speak(setup.strip())
            time.sleep(1.5)  # Longer pause for comedic effect
            self.tts_engine.speak(punchline.strip())
        else:
            self.tts_engine.speak(joke)

        print(f"😄 Told joke: {joke}")

    def _handle_tell_dad_joke(self):
        """Handle telling a dad joke"""
        self.tts_engine.speak("Here's a dad joke for you.")
        time.sleep(0.5)  # Brief pause before joke

        joke = get_dad_joke()

        # Split joke at the pause for better comedic timing
        if "......" in joke:
            setup, punchline = joke.split("......", 1)
            self.tts_engine.speak(setup.strip())
            time.sleep(1.5)  # Longer pause for comedic effect
            self.tts_engine.speak(punchline.strip())
        else:
            self.tts_engine.speak(joke)

        print(f"👨 Told dad joke: {joke}")

    def _handle_unknown_command(self):
        """Handle unknown/unrecognized commands"""
        self.tts_engine.speak("I did not understand that command. Please try again.")


class MockCommandProcessor:
    """Mock command processor for testing"""

    def __init__(self, tts_engine, audio_manager):
        self.tts_engine = tts_engine
        self.audio_manager = audio_manager
        print("Mock command processor initialized")

    def process_command(self, intent: str, slots: Dict[str, Any]):
        """Mock command processing"""
        print(f"\n🎯 [MOCK] Processing command: {intent}")
        print(f"📦 [MOCK] Slots: {slots}")

        if intent == 'getTime':
            time_info = get_current_time()
            self.tts_engine.speak(time_info)
        elif intent == 'tellJoke':
            self.tts_engine.speak("Here's a mock joke for you.")
            self.tts_engine.speak("Why did the mock object cross the road? To get to the other side of the test!")
        elif intent == 'tellDadJoke':
            self.tts_engine.speak("Here's a mock dad joke.")
            self.tts_engine.speak("I'm afraid for the calendar. Its days are numbered!")
        else:
            self.tts_engine.speak(f"Mock processing {intent} command.")

        # Return mock conversation state
        return {
            'continue_conversation': True,
            'timeout': 8,
            'prompt_message': None
        }


def get_command_processor(tts_engine, audio_manager, mock_mode: bool = False) -> CommandProcessor:
    """
    Factory function to get appropriate command processor

    Args:
        tts_engine: TTS engine instance
        audio_manager: Audio manager instance
        mock_mode: Use mock processor instead of real processor

    Returns:
        CommandProcessor instance
    """
    if mock_mode:
        return MockCommandProcessor(tts_engine, audio_manager)

    return CommandProcessor(tts_engine, audio_manager)