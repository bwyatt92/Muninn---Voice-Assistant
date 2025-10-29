#!/usr/bin/env python3

"""
Test script for the specific "play last recorded memory" fix
"""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Create a minimal test that simulates the exact issue
def test_word_matching():
    """Test the word matching logic"""
    text = "play the last recorded memory"
    words = text.split()

    print(f"Testing phrase: '{text}'")
    print(f"Words: {words}")

    # Test the old problematic logic
    print("\nOLD LOGIC:")
    if 'record' in text.lower() or 'recording' in text.lower():
        print("  OLD: Would match createMemory (WRONG!)")
    else:
        print("  OLD: Would not match createMemory")

    # Test the new logic
    print("\nNEW LOGIC:")
    record_indicators = ['record', 'recording']
    has_record_intent = any(word in words for word in record_indicators)
    print(f"  record_indicators: {record_indicators}")
    print(f"  has_record_intent: {has_record_intent}")

    if has_record_intent:
        print("  NEW: Would match createMemory")
    else:
        print("  NEW: Would NOT match createMemory (CORRECT!)")

def test_various_phrases():
    """Test various phrases to make sure we don't break other commands"""
    test_cases = [
        "play the last recorded memory",  # Should NOT match record
        "record a message",               # Should match record
        "recording something",           # Should match record
        "I recorded this",               # Should NOT match record (wrong tense context)
        "play last recording",           # Should NOT match record
    ]

    print(f"\n{'='*60}")
    print("TESTING VARIOUS PHRASES")
    print(f"{'='*60}")

    for phrase in test_cases:
        print(f"\nPhrase: '{phrase}'")
        words = phrase.split()

        # New logic test
        record_indicators = ['record', 'recording']
        has_record_intent = any(word in words for word in record_indicators)

        print(f"  Words: {words}")
        print(f"  has_record_intent: {has_record_intent}")

        if has_record_intent:
            print("  -> Would trigger createMemory")
        else:
            print("  -> Would NOT trigger createMemory")

if __name__ == "__main__":
    test_word_matching()
    test_various_phrases()