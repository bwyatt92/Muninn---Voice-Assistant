#!/usr/bin/env python3

"""
Debug script for speech recognition pattern matching
"""

import sys
import os
from difflib import SequenceMatcher

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Mock the config since we can't import the full module
class MockConfig:
    COMMAND_PATTERNS = {
        'play': ['play', 'playing'],
        'record': ['record', 'recording', 'create', 'save'],
        'all': ['all', 'every', 'everything'],
        'birthday': ['birthday', 'birth'],
        'message': ['message', 'messages', 'msg'],
        'stop': ['stop', 'halt', 'end'],
        'time': ['time', 'clock'],
        'weather': ['weather', 'forecast'],
        'list': ['list', 'show', 'tell'],
        'record_for': ['record for', 'save for'],
        'joke': ['joke', 'funny'],
        'dad_joke': ['dad joke', 'father joke']
    }

    FAMILY_NAMES = {
        'dad': ['dad', 'father', 'daddy', 'papa']
    }

def _fuzzy_contains_any(words, patterns):
    """Check if any word matches any pattern with similarity"""
    for word in words:
        for pattern in patterns:
            if word == pattern:
                return True
            similarity = SequenceMatcher(None, word, pattern).ratio()
            if similarity >= 0.7:
                return True
    return False

def _contains_phrase(text, phrases):
    """Check if any of the phrases are contained in text"""
    for phrase in phrases:
        if phrase in text:
            return True
    return False

def debug_smart_fuzzy_match(text):
    """Debug version of the smart fuzzy matching"""
    text_lower = text.lower().strip()
    words = text_lower.split()

    print(f"\nDebugging: '{text_lower}'")
    print(f"Words: {words}")

    # Strategy 1: Exact phrase matching
    phrases_to_check = ['play all birthday', 'all birthday message', 'play birthday message']
    print(f"\n1. Checking exact phrases: {phrases_to_check}")
    if _contains_phrase(text_lower, phrases_to_check):
        print("   MATCH: playAllMessages")
        return {'understood': True, 'intent': 'playAllMessages', 'slots': {}, 'confidence': 0.95}
    else:
        print("   No exact phrase match")

    # Strategy 2: Check for "last/recent" commands FIRST (higher priority)
    print(f"\n2. Checking play + last/recent patterns:")
    has_play = _fuzzy_contains_any(words, MockConfig.COMMAND_PATTERNS['play'])
    has_last = 'last' in text_lower or 'recent' in text_lower or 'latest' in text_lower
    print(f"   has_play: {has_play}")
    print(f"   has_last: {has_last}")

    if has_play and has_last:
        print("   MATCH: playLastRecording (Strategy 2)")
        return {'understood': True, 'intent': 'playLastRecording', 'slots': {}, 'confidence': 0.95}

    # Check for "play" + "recorded" (past tense indicates playback)
    print(f"\n3. Checking play + recorded:")
    has_recorded = 'recorded' in text_lower
    print(f"   has_recorded: {has_recorded}")
    if has_play and has_recorded:
        print("   MATCH: playLastRecording (Strategy 3)")
        return {'understood': True, 'intent': 'playLastRecording', 'slots': {}, 'confidence': 0.95}

    # Check for "play" + "memory" (specific to playback)
    print(f"\n4. Checking play + memory:")
    has_memory = 'memory' in text_lower
    print(f"   has_memory: {has_memory}")
    if has_play and has_memory:
        print("   MATCH: playLastRecording (Strategy 4)")
        return {'understood': True, 'intent': 'playLastRecording', 'slots': {}, 'confidence': 0.95}

    # Strategy 5: Record commands (present tense = new recording)
    print(f"\n5. Checking record commands:")
    has_record = _fuzzy_contains_any(words, MockConfig.COMMAND_PATTERNS['record'])
    print(f"   has_record: {has_record}")
    print(f"   has_play: {has_play} (should block record if true)")

    if has_record and not has_play:
        print("   MATCH: createMemory (Strategy 5)")
        return {'understood': True, 'intent': 'createMemory', 'slots': {}, 'confidence': 0.8}
    else:
        print("   No record match (blocked by has_play or no has_record)")

    print("\nNo matches found")
    return {'understood': False, 'intent': 'unknown', 'slots': {}, 'confidence': 0.0}

def test_problematic_cases():
    """Test the problematic cases"""
    test_cases = [
        "play the last recorded memory",
        "play last recording",
        "play recent recording",
        "record a message",
        "create memory",
        "record memory"
    ]

    print("Testing Problematic Speech Recognition Cases")
    print("=" * 60)

    for test_case in test_cases:
        print(f"\n{'='*60}")
        result = debug_smart_fuzzy_match(test_case)
        print(f"\nFINAL RESULT for '{test_case}':")
        print(f"   Intent: {result['intent']}")
        print(f"   Confidence: {result['confidence']}")

if __name__ == "__main__":
    test_problematic_cases()