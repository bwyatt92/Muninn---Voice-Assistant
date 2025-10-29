#!/usr/bin/env python3

"""
Test script for enhanced message functionality
Run with: python3 test_messages.py
"""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from speech import get_tts_engine
from commands import get_command_processor
from audio import get_audio_manager

def test_message_functionality():
    """Test the enhanced message functionality in mock mode"""
    print("🧪 Testing Enhanced Message Functionality")
    print("=" * 50)

    # Initialize components in mock mode
    tts = get_tts_engine(mock_mode=True)
    audio_manager = get_audio_manager(mock_mode=True)
    command_processor = get_command_processor(tts, audio_manager, mock_mode=True)

    print("📊 Mock Data Available:")
    message_counts = audio_manager.get_message_count_by_person()
    for person, count in message_counts.items():
        print(f"  {person.title()}: {count} messages")

    print(f"\n💬 Testing Commands:")

    # Test 1: List messages
    print(f"\n1. Testing 'list messages'")
    conversation_state = command_processor.process_command('listMessages', {})
    print(f"   Conversation continues: {conversation_state['continue_conversation']}")

    # Test 2: Play all messages
    print(f"\n2. Testing 'play all messages'")
    conversation_state = command_processor.process_command('playAllMessages', {})
    print(f"   Conversation continues: {conversation_state['continue_conversation']}")

    # Test 3: Play specific person's messages
    print(f"\n3. Testing 'play dad's messages'")
    conversation_state = command_processor.process_command('getMessage', {'person': 'dad'})
    print(f"   Conversation continues: {conversation_state['continue_conversation']}")

    # Test 4: Play messages from person with no messages
    print(f"\n4. Testing 'play scott's messages' (no messages)")
    conversation_state = command_processor.process_command('getMessage', {'person': 'scott'})
    print(f"   Conversation continues: {conversation_state['continue_conversation']}")

    # Test 5: Record for specific person
    print(f"\n5. Testing 'record for carrie'")
    conversation_state = command_processor.process_command('recordForPerson', {'person': 'carrie'})
    print(f"   Conversation continues: {conversation_state['continue_conversation']}")

    print(f"\n✅ Enhanced message functionality test completed!")
    print(f"\n💡 New Voice Commands Available:")
    print(f"   'Muninn, play all messages' - Cycles through all family members")
    print(f"   'Muninn, play dad's messages' - Plays all messages from dad")
    print(f"   'Muninn, list messages' - Shows message counts")
    print(f"   'Muninn, record for mom' - Records message specifically for mom")
    print(f"\n🎯 Conversational Examples:")
    print(f"   User: 'Muninn, list messages'")
    print(f"   Muninn: 'I have 4 messages from 3 family members...'")
    print(f"   User: 'Play dad's messages' (no wake word needed!)")
    print(f"   Muninn: 'Playing 2 messages from dad...'")

if __name__ == "__main__":
    test_message_functionality()