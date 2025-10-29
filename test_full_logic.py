#!/usr/bin/env python3

"""
Test script that follows the full speech recognition logic flow
"""

import sys
import os
from difflib import SequenceMatcher

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Mock the config
class MockConfig:
    COMMAND_PATTERNS = {
        'play': ['play', 'playing', 'played'],
        'record': ['record', 'recorded', 'recording', 'report', 'recall'],
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

def test_full_logic_flow(text):
    """Test the full speech recognition logic flow"""
    text_lower = text.lower().strip()
    words = text_lower.split()

    print(f"\nTesting: '{text_lower}'")
    print(f"Words: {words}")

    # Strategy 2: Check for "last/recent" commands FIRST (higher priority)
    has_play = _fuzzy_contains_any(words, MockConfig.COMMAND_PATTERNS['play'])
    has_last = 'last' in text_lower or 'recent' in text_lower or 'latest' in text_lower

    print(f"has_play: {has_play}")
    print(f"has_last: {has_last}")

    if has_play and has_last:
        print("-> RESULT: playLastRecording (Strategy 2)")
        return {'intent': 'playLastRecording', 'confidence': 0.95}

    # Check for "play" + "recorded" (past tense indicates playback)
    has_recorded = 'recorded' in text_lower
    print(f"has_recorded: {has_recorded}")
    if has_play and has_recorded:
        print("-> RESULT: playLastRecording (Strategy 3)")
        return {'intent': 'playLastRecording', 'confidence': 0.95}

    # Check for "play" + "memory" (specific to playback)
    has_memory = 'memory' in text_lower
    print(f"has_memory: {has_memory}")
    if has_play and has_memory:
        print("-> RESULT: playLastRecording (Strategy 4)")
        return {'intent': 'playLastRecording', 'confidence': 0.95}

    # Strategy 5: Record commands (present tense = new recording)
    has_record = _fuzzy_contains_any(words, MockConfig.COMMAND_PATTERNS['record'])
    print(f"has_record: {has_record}")
    print(f"Condition: has_record={has_record} AND not has_play={not has_play}")

    if has_record and not has_play:
        # Use the NEW fixed logic
        record_indicators = ['record', 'recording']
        has_record_intent = any(word in words for word in record_indicators)
        print(f"has_record_intent: {has_record_intent}")

        if has_record_intent:
            print("-> RESULT: createMemory (Strategy 5)")
            return {'intent': 'createMemory', 'confidence': 0.8}

    print("-> RESULT: No match")
    return {'intent': 'unknown', 'confidence': 0.0}

def test_all_cases():
    """Test all the problematic cases"""
    test_cases = [
        "play the last recorded memory",
        "play last recording",
        "record a message",
        "recording something",
        "I recorded this"
    ]

    print("FULL LOGIC FLOW TEST")
    print("="*50)

    for case in test_cases:
        result = test_full_logic_flow(case)
        print(f"FINAL: {result['intent']} (confidence: {result['confidence']})")
        print("-"*50)

if __name__ == "__main__":
    test_all_cases()