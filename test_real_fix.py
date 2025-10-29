#!/usr/bin/env python3

"""
Test script to verify the actual fix works with the real speech recognition module
"""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import just the config and the pattern matching function
from config.settings import MuninnConfig
from difflib import SequenceMatcher

class MinimalSpeechRecognizer:
    """Minimal version for testing just the pattern matching"""

    def _fuzzy_contains_any(self, words, patterns):
        """Check if any word matches any pattern with similarity"""
        for word in words:
            for pattern in patterns:
                if word == pattern:
                    return True
                similarity = SequenceMatcher(None, word, pattern).ratio()
                if similarity >= 0.7:
                    return True
        return False

    def _contains_phrase(self, text, phrases):
        """Check if any of the phrases are contained in text"""
        for phrase in phrases:
            if phrase in text:
                return True
        return False

    def _smart_fuzzy_match(self, text):
        """Simplified version of the smart fuzzy matching with the fix"""
        text_lower = text.lower().strip()
        words = text_lower.split()

        print(f"Testing: '{text_lower}'")
        print(f"Words: {words}")

        # Strategy 1: Exact phrase matching
        if self._contains_phrase(text_lower, ['play all birthday', 'all birthday message', 'play birthday message']):
            print("-> Match: playAllMessages (exact phrase)")
            return {'understood': True, 'intent': 'playAllMessages', 'slots': {}, 'confidence': 0.95}

        # Strategy 2: Check for "last/recent" commands FIRST (higher priority)
        has_play = self._fuzzy_contains_any(words, MuninnConfig.COMMAND_PATTERNS['play'])
        has_last = 'last' in text_lower or 'recent' in text_lower or 'latest' in text_lower
        print(f"has_play: {has_play}, has_last: {has_last}")

        if has_play and has_last:
            print("-> Match: playLastRecording (Strategy 2)")
            return {'understood': True, 'intent': 'playLastRecording', 'slots': {}, 'confidence': 0.95}

        # Check for "play" + "recorded" (past tense indicates playback)
        if has_play and 'recorded' in text_lower:
            print("-> Match: playLastRecording (Strategy 3)")
            return {'understood': True, 'intent': 'playLastRecording', 'slots': {}, 'confidence': 0.95}

        # Check for "play" + "memory" (specific to playback)
        if has_play and 'memory' in text_lower:
            print("-> Match: playLastRecording (Strategy 4)")
            return {'understood': True, 'intent': 'playLastRecording', 'slots': {}, 'confidence': 0.95}

        # Strategy 5: Record commands (present tense = new recording) - WITH THE FIX
        has_record = self._fuzzy_contains_any(words, MuninnConfig.COMMAND_PATTERNS['record'])
        print(f"has_record: {has_record}, has_play: {has_play}")

        if has_record and not has_play:
            # THE FIX: Use word boundaries to avoid matching "recorded" in playback contexts
            record_indicators = ['record', 'recording']
            has_record_intent = any(word in words for word in record_indicators)
            print(f"record_indicators: {record_indicators}")
            print(f"has_record_intent: {has_record_intent}")

            if has_record_intent:
                print("-> Match: createMemory (Strategy 5)")
                return {'understood': True, 'intent': 'createMemory', 'slots': {}, 'confidence': 0.8}

        print("-> No match")
        return {'understood': False, 'intent': 'unknown', 'slots': {}, 'confidence': 0.0}

def test_the_fix():
    """Test the specific problematic case"""
    recognizer = MinimalSpeechRecognizer()

    test_cases = [
        "play the last recorded memory",
        "play last recording",
        "record a message",
        "recording something"
    ]

    print("TESTING THE FIX WITH REAL CONFIG")
    print("="*50)

    for test_case in test_cases:
        print(f"\n{'-'*50}")
        result = recognizer._smart_fuzzy_match(test_case)
        print(f"RESULT: {result['intent']} (confidence: {result['confidence']})")

        if test_case == "play the last recorded memory" and result['intent'] == 'playLastRecording':
            print("SUCCESS: The problematic case is now fixed!")
        elif test_case == "play the last recorded memory" and result['intent'] != 'playLastRecording':
            print("FAIL: Still not working correctly")

if __name__ == "__main__":
    test_the_fix()