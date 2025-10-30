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

try:
    from rapidfuzz import fuzz, process
    from jellyfish import soundex, metaphone
    ADVANCED_MATCHING_AVAILABLE = True
except ImportError:
    ADVANCED_MATCHING_AVAILABLE = False
    print("⚠️  rapidfuzz/jellyfish not available - using basic matching")

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
                            result['raw_text'] = all_text.strip()
                            return result
                    return {'understood': False, 'intent': 'timeout', 'slots': {}, 'raw_text': all_text.strip()}

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
                                command_result['raw_text'] = all_text.strip()
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
            return {'understood': False, 'intent': 'error', 'slots': {}, 'raw_text': ''}

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

        # Enhanced: Apply phonetic correction if available
        if ADVANCED_MATCHING_AVAILABLE:
            text_lower = self._apply_phonetic_corrections(text_lower)
            words = text_lower.split()
            print(f"🔊 After phonetic correction: '{text_lower}'")

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

        # Strategy 3: Story/Memory commands (MOVED UP - Higher priority than messages)
        has_story = self._fuzzy_contains_any(words, MuninnConfig.COMMAND_PATTERNS['story'])
        has_get = self._fuzzy_contains_any(words, MuninnConfig.COMMAND_PATTERNS['get'])

        # IMPORTANT: Check for RECORD commands FIRST before story playback
        # "record a story" should NOT match getMemory intent
        if 'record' in text_lower and (has_story or 'story' in text_lower or 'memory' in text_lower or 'memories' in text_lower):
            print(f"🎯 Record story command detected")
            return {
                'understood': True,
                'intent': 'recordStory',
                'slots': {},
                'confidence': 0.95
            }

        # Check for story keywords - this takes precedence over birthday messages
        if has_story or 'story' in text_lower or 'stories' in text_lower or 'tale' in text_lower or (has_get and 'memory' in text_lower):
            # Extract optional person
            person = self._extract_family_member(words)

            # Extract optional length (short, medium, long)
            length = None
            if 'short' in text_lower or 'quick' in text_lower or 'brief' in text_lower:
                length = 'short'
            elif 'long' in text_lower:
                length = 'long'
            elif 'medium' in text_lower:
                length = 'medium'

            # Extract optional story type (advice, birthday, etc.)
            story_type = None
            if 'advice' in text_lower:
                story_type = 'advice'
            elif 'wisdom' in text_lower or 'lesson' in text_lower:
                story_type = 'wisdom'
            elif 'funny' in text_lower:
                story_type = 'funny'
            # Note: Don't check for 'birthday' here as story type to avoid conflict

            slots = {}
            if person:
                slots['person'] = person
            if length:
                slots['length'] = length
            if story_type:
                slots['story'] = story_type

            print(f"🎯 Story request detected - person: {person}, type: {story_type}, length: {length}")

            return {
                'understood': True,
                'intent': 'getMemory',
                'slots': slots,
                'confidence': 0.95  # High confidence for story requests
            }

        # Strategy 4: Person-specific BIRTHDAY messages (lower priority than stories)
        has_message = self._fuzzy_contains_any(words, MuninnConfig.COMMAND_PATTERNS['message'])
        has_birthday = self._fuzzy_contains_any(words, MuninnConfig.COMMAND_PATTERNS['birthday'])

        # Only match birthday message if "message" or "birthday" keyword is present
        if (has_play or has_message) and (has_message or has_birthday):
            person = self._extract_family_member(words)
            if person:
                print(f"🎯 Detected birthday message request for: {person}")
                return {
                    'understood': True,
                    'intent': 'getMessage',
                    'slots': {'person': person},
                    'confidence': 0.9
                }

        # Strategy 5: Command + target detection for "all messages" (ONLY if no person detected)
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

        # Strategy 6: Record commands (REMOVED - now handled in Strategy 3)
        # Record story/memory commands are now detected earlier to prevent conflict with getMemory

        # Check for generic record commands (not story-related)
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

        # Strategy 7: Time and Weather commands
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

        # Strategy 8: List commands
        # Be more strict - only match if we have explicit "list" or "show" keywords
        has_list_keyword = 'list' in text_lower or 'show' in text_lower or 'what' in text_lower

        # List stories (check for story-related keywords)
        if has_list_keyword and (has_story or 'stories' in text_lower):
            return {
                'understood': True,
                'intent': 'listStories',
                'slots': {},
                'confidence': 0.9
            }

        # List messages
        if has_list_keyword and has_message:
            return {
                'understood': True,
                'intent': 'listMessages',
                'slots': {},
                'confidence': 0.9
            }

        # Strategy 9: Record for specific person
        if self._fuzzy_contains_any(words, MuninnConfig.COMMAND_PATTERNS['record_for']):
            person = self._extract_family_member(words)
            if person:
                return {
                    'understood': True,
                    'intent': 'recordForPerson',
                    'slots': {'person': person},
                    'confidence': 0.9
                }

        # Strategy 10: Joke commands
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
        """Extract family member name using fuzzy and phonetic matching"""
        best_match = None
        best_score = 0.0
        best_word = None

        for word in words:
            for family_name, variations in MuninnConfig.FAMILY_NAMES.items():
                for variation in variations:
                    if word == variation:
                        print(f"👨‍👩‍👧‍👦 Exact family match: '{word}' → {family_name}")
                        return family_name

                    # Basic fuzzy matching
                    similarity = SequenceMatcher(None, word, variation).ratio()

                    # Enhanced: Add phonetic matching if available
                    if ADVANCED_MATCHING_AVAILABLE:
                        try:
                            fuzzy_score = fuzz.ratio(word, variation) / 100.0
                            phonetic_same = soundex(word) == soundex(variation)
                            phonetic_score = 1.0 if phonetic_same else 0.0

                            # Weighted combination: fuzzy 60%, phonetic 40%
                            similarity = (fuzzy_score * 0.6) + (phonetic_score * 0.4)
                        except:
                            pass  # Fall back to basic similarity

                    # Reduced threshold to 0.65 with phonetic matching
                    threshold = 0.65 if ADVANCED_MATCHING_AVAILABLE else 0.75
                    if similarity >= threshold and similarity > best_score:
                        best_match = family_name
                        best_score = similarity
                        best_word = word

        if best_match:
            print(f"👨‍👩‍👧‍👦 Fuzzy family match: '{best_word}' → {best_match} (score: {best_score:.2f})")
            return best_match

        print(f"⚠️  No family member found in: {words}")
        return None

    def _apply_phonetic_corrections(self, text: str) -> str:
        """Apply phonetic corrections to common misheard phrases"""
        if not ADVANCED_MATCHING_AVAILABLE:
            return text

        # Common command misheard patterns
        corrections = {
            # Story commands - CRITICAL for "get a gumbo" → "from beau"
            'gumbo': 'from beau',
            'combo': 'from beau',
            'jumbo': 'from beau',

            # Action words
            'plate': 'play',
            'plates': 'play',
            'clay': 'play',
            'pale': 'play',

            # Story words
            'torah': 'story',
            'sorry': 'story',
            'storing': 'story',

            # People
            'bow': 'beau',
            'bough': 'beau',
            'bo': 'beau',

            # From/for confusion
            'form': 'from',
            'firm': 'from',
            'four': 'from',
        }

        text_words = text.split()
        corrected_words = []
        skip_next = 0

        for i, word in enumerate(text_words):
            if skip_next > 0:
                skip_next -= 1
                continue

            corrected = word

            # Direct single-word replacement
            if word in corrections:
                replacement = corrections[word]
                if ' ' in replacement:
                    # Multi-word replacement
                    corrected_words.extend(replacement.split())
                    continue
                else:
                    corrected = replacement

            # Context-aware: "get a gumbo" pattern
            if i >= 2 and word in ['gumbo', 'combo', 'jumbo']:
                # Check if preceded by "get/got a" or similar
                if text_words[i-1] in ['a', 'the'] and text_words[i-2] in ['get', 'got', 'give', 'play']:
                    # Replace "a gumbo" with "from beau"
                    corrected_words.pop()  # Remove 'a'
                    corrected_words.extend(['from', 'beau'])
                    continue

            corrected_words.append(corrected)

        return ' '.join(corrected_words)


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
            'confidence': 0.9,
            'raw_text': 'what time is it'
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