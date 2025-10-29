#!/usr/bin/env python3

"""
Test script for joke functionality
Run with: python3 test_jokes.py
"""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.jokes import get_random_joke, get_dad_joke, test_joke_apis
from speech import get_tts_engine
from commands import get_command_processor
from audio import get_audio_manager

def test_joke_functionality():
    """Test the joke functionality"""
    print("🧪 Testing Joke Functionality")
    print("=" * 40)

    # Test 1: Test joke APIs directly
    print("1. Testing joke APIs directly...")
    test_joke_apis()

    print("\n2. Testing joke integration with Muninn...")

    # Initialize components in mock mode
    tts = get_tts_engine(mock_mode=True)
    audio_manager = get_audio_manager(mock_mode=True)
    command_processor = get_command_processor(tts, audio_manager, mock_mode=True)

    # Test 3: Test random joke command
    print("\n3. Testing 'tell me a joke' command...")
    conversation_state = command_processor.process_command('tellJoke', {})
    print(f"   Conversation continues: {conversation_state['continue_conversation']}")

    # Test 4: Test dad joke command
    print("\n4. Testing 'tell me a dad joke' command...")
    conversation_state = command_processor.process_command('tellDadJoke', {})
    print(f"   Conversation continues: {conversation_state['continue_conversation']}")

    print(f"\n✅ Joke functionality test completed!")
    print(f"\n💡 New Voice Commands Available:")
    print(f"   'Muninn, tell me a joke' - Random joke from API")
    print(f"   'Muninn, tell me a dad joke' - Dad joke (perfect for birthday!)")
    print(f"   'Muninn, make me laugh' - Another way to request jokes")
    print(f"\n🎯 Conversational Example:")
    print(f"   User: 'Muninn, what time is it?'")
    print(f"   Muninn: 'It's 3:45 PM...'")
    print(f"   User: 'Tell me a joke' (no wake word needed!)")
    print(f"   Muninn: 'Here's a joke for you. What's 50 Cent's name in Zimbabwe?... 200 Dollars.'")
    print(f"   User: 'Tell me a dad joke'")
    print(f"   Muninn: 'Here's a dad joke for you. Why don't scientists trust atoms?... Because they make up everything!'")

if __name__ == "__main__":
    test_joke_functionality()