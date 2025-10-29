#!/usr/bin/env python3

"""
Speech Recognition Module for Muninn
Handles Vosk integration and command processing with fuzzy matching
"""

import json
import time
import pyaudio
import vosk
from typing import Dict, Any, Optional, List
from difflib import SequenceMatcher

from config.settings import MuninnConfig


class SpeechRecognizer:
    """Speech recognizer using Vosk with smart fuzzy matching"""

    def __init__(self, vosk_model_path: str, audio_device_index: Optional[int] = None, audio: Optional[pyaudio.PyAudio] = None):
        self.vosk_model_path = vosk_model_path
        self.audio_device_index = audio_device_index
        self.audio = audio

        # Audio settings
        self.sample_rate = MuninnConfig.SAMPLE_RATE
        self.channels = MuninnConfig.CHANNELS
        self.chunk_size = MuninnConfig.CHUNK_SIZE

        # Initialize Vosk
        self.vosk_model = None
        self.vosk_recognizer = None
        self._initialize_vosk()

    def _initialize_vosk(self):
        """Initialize Vosk speech recognition model"""
        try:
            print("Loading Vosk model...")
            self.vosk_model = vosk.Model(self.vosk_model_path)
            self.vosk_recognizer = vosk.KaldiRecognizer(self.vosk_model, self.sample_rate)
            print("✓ Vosk model loaded")
        except Exception as e:
            print(f"❌ Failed to initialize Vosk: {e}")
            raise

    def listen_for_command(self, timeout: int = 8) -> Dict[str, Any]:
        """
        Listen for voice command and process with fuzzy matching

        Args:
            timeout: Maximum time to listen in seconds

        Returns:
            Dict containing intent, slots, and confidence
        """
        print("👂 Listening for command...")

        stream = None
        try:
            stream = self.audio.open(
                format=pyaudio.paInt16,
                channels=self.channels,
                rate=self.sample_rate,
                input=True,
                input_device_index=self.audio_device_index,
                frames_per_buffer=self.chunk_size
            )

            start_time = time.time()
            all_text = ""

            while True:
                if (time.time() - start_time) > timeout:
                    if all_text.strip():
                        print(f"🔍 Final analysis: '{all_text.strip()}'")
                        result = self._smart_fuzzy_match(all_text.strip())
                        if result['understood']:
                            return result
                    return {'understood': False, 'intent': 'timeout', 'slots': {}}

                try:
                    data = stream.read(self.chunk_size, exception_on_overflow=False)

                    if self.vosk_recognizer.AcceptWaveform(data):
                        result = json.loads(self.vosk_recognizer.Result())
                        text = result.get('text', '')

                        if text:
                            all_text += " " + text
                            print(f"🎧 Heard: '{text.strip()}'")

                            # Try smart matching
                            command_result = self._smart_fuzzy_match(all_text.strip())
                            if command_result['understood'] and command_result['confidence'] > 0.7:
                                print(f"🎯 High confidence match: {command_result}")
                                return command_result

                            # Reset if too long
                            if len(all_text) > 80:
                                all_text = text

                except Exception as e:
                    print(f"❌ Command error: {e}")
                    time.sleep(0.1)
                    continue

        except Exception as e:
            print(f"❌ Command listening error: {e}")
            return {'understood': False, 'intent': 'error', 'slots': {}}

        finally:
            if stream:
                try:
                    stream.stop_stream()
                    stream.close()
                except:
                    pass

    def _smart_fuzzy_match(self, text: str) -> Dict[str, Any]:
        """Advanced fuzzy matching using multiple strategies"""
        text_lower = text.lower().strip()
        words = text_lower.split()

        print(f"🔍 Smart fuzzy matching: '{text_lower}'")

        # Strategy 1: Exact phrase matching
        if self._contains_phrase(text_lower, ['play all birthday', 'all birthday message', 'play birthday message']):
            return {
                'understood': True,
                'intent': 'playAllMessages',
                'slots': {},
                'confidence': 0.95
            }

        # Strategy 2: Check for "last/recent" commands FIRST (higher priority)
        has_play = self._fuzzy_contains_any(words, MuninnConfig.COMMAND_PATTERNS['play'])
        has_last = 'last' in text_lower or 'recent' in text_lower or 'latest' in text_lower

        # More specific check for playback vs recording
        # Look for "play" + ("last"/"recent") OR "play" + "recorded" (past tense = playback)
        if has_play and has_last:
            return {
                'understood': True,
                'intent': 'playLastRecording',
                'slots': {},
                'confidence': 0.95
            }

        # Check for "play" + "recorded" (past tense indicates playback)
        if has_play and 'recorded' in text_lower:
            return {
                'understood': True,
                'intent': 'playLastRecording',
                'slots': {},
                'confidence': 0.95
            }

        # Check for "play" + "memory" (specific to playback)
        if has_play and 'memory' in text_lower:
            return {
                'understood': True,
                'intent': 'playLastRecording',
                'slots': {},
                'confidence': 0.95
            }

        # Strategy 3: Person-specific messages (CHECK FIRST before "play all")
        has_message = self._fuzzy_contains_any(words, MuninnConfig.COMMAND_PATTERNS['message'])

        if has_play or has_message:
            person = self._extract_family_member(words)
            if person:
                print(f"🎯 Detected person-specific request for: {person}")
                return {
                    'understood': True,
                    'intent': 'getMessage',
                    'slots': {'person': person},
                    'confidence': 0.9  # Increased confidence for person-specific
                }

        # Strategy 4: Command + target detection for "all messages" (ONLY if no person detected)
        has_all = self._fuzzy_contains_any(words, MuninnConfig.COMMAND_PATTERNS['all'])
        has_birthday = self._fuzzy_contains_any(words, MuninnConfig.COMMAND_PATTERNS['birthday'])

        # Play all birthday messages - but be more restrictive
        # Require explicit "all" keyword OR both "birthday" and "message" without a person name
        if (has_play and has_all) or (has_all and has_birthday):
            return {
                'understood': True,
                'intent': 'playAllMessages',
                'slots': {},
                'confidence': 0.85
            }

        # Strategy 5: Record commands (present tense = new recording)
        # Only match if it's NOT a playback command
        has_record = self._fuzzy_contains_any(words, MuninnConfig.COMMAND_PATTERNS['record'])

        if has_record and not has_play:
            # Make sure this is about recording NEW content, not playing recorded content
            # Use word boundaries to avoid matching "recorded" in playback contexts
            record_indicators = ['record', 'recording']
            has_record_intent = any(word in words for word in record_indicators)

            if has_record_intent:
                return {
                    'understood': True,
                    'intent': 'createMemory',
                    'slots': {},
                    'confidence': 0.8
                }

        if self._fuzzy_contains_any(words, MuninnConfig.COMMAND_PATTERNS['stop']):
            return {
                'understood': True,
                'intent': 'stop',
                'slots': {},
                'confidence': 0.9
            }

        # Strategy 6: Time and Weather commands
        if self._fuzzy_contains_any(words, MuninnConfig.COMMAND_PATTERNS['time']) or 'time' in text_lower:
            return {
                'understood': True,
                'intent': 'getTime',
                'slots': {},
                'confidence': 0.9
            }

        if self._fuzzy_contains_any(words, MuninnConfig.COMMAND_PATTERNS['weather']) or 'weather' in text_lower:
            return {
                'understood': True,
                'intent': 'getWeather',
                'slots': {},
                'confidence': 0.9
            }

        # Note: playLastRecording is now handled in Strategy 2 above

        # Strategy 7: List messages command
        # Be more strict - only match if we have explicit "list" or "show" keywords
        has_list_keyword = 'list' in text_lower or 'show' in text_lower
        if has_list_keyword and has_message:
            return {
                'understood': True,
                'intent': 'listMessages',
                'slots': {},
                'confidence': 0.9
            }

        # Strategy 8: Record for specific person
        if self._fuzzy_contains_any(words, MuninnConfig.COMMAND_PATTERNS['record_for']):
            person = self._extract_family_member(words)
            if person:
                return {
                    'understood': True,
                    'intent': 'recordForPerson',
                    'slots': {'person': person},
                    'confidence': 0.9
                }

        # Strategy 9: Joke commands
        if self._fuzzy_contains_any(words, MuninnConfig.COMMAND_PATTERNS['dad_joke']) or ('dad' in text_lower and 'joke' in text_lower):
            return {
                'understood': True,
                'intent': 'tellDadJoke',
                'slots': {},
                'confidence': 0.9
            }

        if self._fuzzy_contains_any(words, MuninnConfig.COMMAND_PATTERNS['joke']) or 'joke' in text_lower:
            return {
                'understood': True,
                'intent': 'tellJoke',
                'slots': {},
                'confidence': 0.9
            }

        return {'understood': False, 'intent': 'unknown', 'slots': {}, 'confidence': 0.0}

    def _contains_phrase(self, text: str, phrases: List[str]) -> bool:
        """Check if any of the phrases are contained in text"""
        for phrase in phrases:
            if phrase in text:
                return True
        return False

    def _fuzzy_contains_any(self, words: List[str], patterns: List[str], threshold: float = 0.8) -> bool:
        """Check if any word matches any pattern with similarity"""
        for word in words:
            for pattern in patterns:
                if word == pattern:
                    return True
                similarity = SequenceMatcher(None, word, pattern).ratio()
                if similarity >= threshold:
                    print(f"  🔍 Fuzzy match: '{word}' ≈ '{pattern}' (score: {similarity:.2f})")
                    return True
        return False

    def _extract_family_member(self, words: List[str]) -> Optional[str]:
        """Extract family member name using fuzzy matching"""
        best_match = None
        best_score = 0.0
        best_word = None

        for word in words:
            for family_name, variations in MuninnConfig.FAMILY_NAMES.items():
                for variation in variations:
                    if word == variation:
                        print(f"👨‍👩‍👧‍👦 Exact family match: '{word}' → {family_name}")
                        return family_name

                    similarity = SequenceMatcher(None, word, variation).ratio()
                    # Increased threshold from 0.7 to 0.75 for better accuracy
                    if similarity >= 0.75 and similarity > best_score:
                        best_match = family_name
                        best_score = similarity
                        best_word = word

        if best_match:
            print(f"👨‍👩‍👧‍👦 Fuzzy family match: '{best_word}' → {best_match} (score: {best_score:.2f})")
            return best_match

        print(f"⚠️  No family member found in: {words}")
        return None


class MockSpeechRecognizer:
    """Mock speech recognizer for testing"""

    def __init__(self, vosk_model_path: str, audio_device_index: Optional[int] = None, audio: Optional[pyaudio.PyAudio] = None):
        print("Mock speech recognizer initialized")

    def listen_for_command(self, timeout: int = 8) -> Dict[str, Any]:
        """Mock command listening - returns predefined commands"""
        print("👂 [MOCK] Listening for command...")
        time.sleep(2)  # Simulate listening

        # Return a mock command
        return {
            'understood': True,
            'intent': 'getTime',
            'slots': {},
            'confidence': 0.9
        }


def get_speech_recognizer(vosk_model_path: str, audio_device_index: Optional[int] = None, audio: Optional[pyaudio.PyAudio] = None, mock_mode: bool = False) -> SpeechRecognizer:
    """
    Factory function to get appropriate speech recognizer

    Args:
        vosk_model_path: Path to Vosk model directory
        audio_device_index: Audio device index for input
        audio: PyAudio instance
        mock_mode: Use mock recognizer instead of real recognizer

    Returns:
        SpeechRecognizer instance
    """
    if mock_mode:
        return MockSpeechRecognizer(vosk_model_path, audio_device_index, audio)

    return SpeechRecognizer(vosk_model_path, audio_device_index, audio)