#!/usr/bin/env python3

"""
Test script for conversational flow
Run with: python3 test_conversation.py
"""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config.settings import MuninnConfig
from speech import get_tts_engine, get_speech_recognizer
from commands import get_command_processor
from audio import get_audio_manager

def test_conversation_flow():
    """Test the conversational flow in mock mode"""
    print("🧪 Testing Conversational Flow")
    print("=" * 40)

    # Initialize components in mock mode
    tts = get_tts_engine(mock_mode=True)
    speech_recognizer = get_speech_recognizer("./mock", mock_mode=True)
    audio_manager = get_audio_manager(mock_mode=True)
    command_processor = get_command_processor(tts, audio_manager, mock_mode=True)

    print(f"📊 Configuration:")
    print(f"  Max conversation turns: {MuninnConfig.MAX_CONVERSATION_TURNS}")
    print(f"  Follow-up timeout: {MuninnConfig.FOLLOW_UP_TIMEOUT} seconds")
    print(f"  Conversation timeout: {MuninnConfig.CONVERSATION_TIMEOUT} seconds")

    # Test conversation state
    print(f"\n💬 Testing conversation state...")

    # Simulate first command
    conversation_state = command_processor.process_command('getTime', {})
    print(f"First command state: {conversation_state}")

    # Simulate second command
    conversation_state = command_processor.process_command('getWeather', {})
    print(f"Second command state: {conversation_state}")

    # Simulate stop command (should end conversation)
    conversation_state = command_processor.process_command('stop', {})
    print(f"Stop command state: {conversation_state}")

    print(f"\n✅ Conversational flow test completed!")
    print(f"\n💡 To test on real hardware:")
    print(f"   python3 muninn.py")
    print(f"\n💡 To test in full mock mode:")
    print(f"   python3 muninn.py --mock")

if __name__ == "__main__":
    test_conversation_flow()