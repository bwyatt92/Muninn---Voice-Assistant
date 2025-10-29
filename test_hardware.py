#!/usr/bin/env python3

"""
Test script for ReSpeaker Lite hardware control
Tests I2C communication, button reading, and LED control
"""

import sys
import os
import time

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from hardware import get_hardware_controller
from hardware.respeaker_lite import LEDState

def test_hardware_controller():
    """Test the hardware controller functionality"""
    print("🧪 Testing ReSpeaker Lite Hardware Controller")
    print("=" * 50)

    # Initialize hardware controller
    controller = get_hardware_controller(mock_mode=False)

    try:
        print("\n1. Testing firmware version and basic I2C...")
        firmware = controller._read_firmware_version()
        if firmware:
            print(f"✅ Firmware version: {firmware}")
        else:
            print("❌ Could not read firmware version")

        print("\n2. Testing voice activity level...")
        for i in range(3):
            vnr = controller.get_voice_activity_level()
            print(f"   Voice Activity Level: {vnr}")
            time.sleep(1)

        print("\n3. Testing mute button status...")
        for i in range(5):
            mute_status = controller.get_mute_button_status()
            mute_pressed, user_pressed = controller.check_buttons()
            print(f"   Mute button: {'PRESSED' if mute_status else 'released'} | Check result: mute={mute_pressed}, user={user_pressed}")
            time.sleep(0.5)

        print("\n4. Testing LED states...")
        led_states = [
            LEDState.WAKE_WORD_LISTENING,
            LEDState.COMMAND_LISTENING,
            LEDState.PROCESSING,
            LEDState.SPEAKING,
            LEDState.ERROR,
            LEDState.MUTED,
            LEDState.IDLE
        ]

        for state in led_states:
            print(f"   Setting LED to: {state.value}")
            controller.set_led_state(state)
            time.sleep(2)

        print("\n5. Testing speaker mute control...")
        print("   Muting speaker...")
        controller.set_speaker_mute(True)
        time.sleep(1)

        print("   Unmuting speaker...")
        controller.set_speaker_mute(False)
        time.sleep(1)

        print("\n✅ Hardware controller tests completed!")

    except KeyboardInterrupt:
        print("\n🛑 Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("\n🧹 Cleaning up...")
        controller.cleanup()

def test_mock_controller():
    """Test the mock hardware controller"""
    print("\n🎭 Testing Mock Hardware Controller")
    print("=" * 50)

    controller = get_hardware_controller(mock_mode=True)

    print("\n1. Testing mock functions...")
    vnr = controller.get_voice_activity_level()
    print(f"   Mock VNR: {vnr}")

    mute_status = controller.get_mute_button_status()
    print(f"   Mock mute status: {mute_status}")

    print("\n2. Testing mock LED states...")
    controller.set_led_state(LEDState.WAKE_WORD_LISTENING)
    time.sleep(1)
    controller.set_led_state(LEDState.SPEAKING)
    time.sleep(1)

    print("\n3. Testing mock buttons...")
    for i in range(5):
        mute_pressed, user_pressed = controller.check_buttons()
        if mute_pressed or user_pressed:
            print(f"   Button event: mute={mute_pressed}, user={user_pressed}")
        time.sleep(0.2)

    controller.cleanup()
    print("✅ Mock controller test completed!")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == '--mock':
        test_mock_controller()
    else:
        print("Testing real hardware controller...")
        print("Use --mock flag to test mock controller instead")
        print()
        test_hardware_controller()