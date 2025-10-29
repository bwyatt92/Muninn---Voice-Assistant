#!/usr/bin/env python3

"""
Test script for Pi Hardware Controller
Tests Activity LED status indication and ReSpeaker mute button
"""

import sys
import os
import time

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from hardware import get_hardware_controller, StatusState

def test_pi_hardware():
    """Test Pi hardware controller functionality"""
    print("🧪 Testing Pi Hardware Controller")
    print("=" * 45)

    print("Note: This test requires root permissions to control the Activity LED")
    print("Run with: sudo python3 test_pi_hardware.py")
    print()

    # Initialize hardware controller
    controller = get_hardware_controller(mock_mode=False)

    try:
        print("1. Testing status states with Activity LED...")

        status_states = [
            (StatusState.WAKE_WORD_LISTENING, "Wake Word Listening - Slow Blink"),
            (StatusState.COMMAND_LISTENING, "Command Listening - Fast Blink"),
            (StatusState.PROCESSING, "Processing - Rapid Blink"),
            (StatusState.SPEAKING, "Speaking - Solid On"),
            (StatusState.MUTED, "Muted - Double Blink"),
            (StatusState.ERROR, "Error - SOS Pattern"),
            (StatusState.IDLE, "Idle - Off")
        ]

        for state, description in status_states:
            print(f"   Setting: {description}")
            controller.set_status(state)
            print("   Watch the Pi's Activity LED for the pattern...")
            time.sleep(4)

        print("\n2. Testing mute button detection...")
        print("   Try pressing the mute button on your ReSpeaker Lite...")
        print("   (Monitoring for 10 seconds)")

        for i in range(100):  # Check for 10 seconds
            mute_pressed = controller.check_mute_button()
            if mute_pressed:
                print(f"   🎯 MUTE BUTTON PRESSED! (detection #{i})")
                controller.set_status(StatusState.MUTED)
                time.sleep(2)
                controller.set_status(StatusState.WAKE_WORD_LISTENING)
            time.sleep(0.1)

        print("   Mute button monitoring complete")

        print("\n✅ Pi hardware controller test completed!")

    except KeyboardInterrupt:
        print("\n🛑 Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("\n🧹 Cleaning up...")
        controller.cleanup()

def test_mock_hardware():
    """Test mock hardware controller"""
    print("🎭 Testing Mock Pi Hardware Controller")
    print("=" * 45)

    controller = get_hardware_controller(mock_mode=True)

    print("\n1. Testing mock status states...")
    for state in StatusState:
        print(f"   Testing: {state.value}")
        controller.set_status(state)
        time.sleep(0.5)

    print("\n2. Testing mock mute button...")
    for i in range(20):
        mute_pressed = controller.check_mute_button()
        if mute_pressed:
            controller.set_status(StatusState.MUTED)
            time.sleep(1)
        time.sleep(0.1)

    controller.cleanup()
    print("\n✅ Mock hardware test completed!")

def demonstrate_status_flow():
    """Demonstrate typical Muninn status flow"""
    print("🎯 Demonstrating Muninn Status Flow")
    print("=" * 45)

    controller = get_hardware_controller(mock_mode=False)

    try:
        flow_steps = [
            (StatusState.WAKE_WORD_LISTENING, "Waiting for wake word", 3),
            (StatusState.COMMAND_LISTENING, "Listening for command", 2),
            (StatusState.PROCESSING, "Processing command", 1.5),
            (StatusState.SPEAKING, "Speaking response", 3),
            (StatusState.WAKE_WORD_LISTENING, "Back to listening", 2),
            (StatusState.IDLE, "Going idle", 1),
        ]

        for state, description, duration in flow_steps:
            print(f"   {description}...")
            controller.set_status(state)
            time.sleep(duration)

        print("\n✅ Status flow demonstration complete!")

    except KeyboardInterrupt:
        print("\n🛑 Demonstration interrupted")
    finally:
        controller.cleanup()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == '--mock':
            test_mock_hardware()
        elif sys.argv[1] == '--demo':
            demonstrate_status_flow()
        else:
            print("Usage: python3 test_pi_hardware.py [--mock|--demo]")
    else:
        test_pi_hardware()