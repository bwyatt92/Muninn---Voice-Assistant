#!/usr/bin/env python3

"""
Raspberry Pi Hardware Controller for Muninn
Uses Pi built-in LEDs and available ReSpeaker button inputs for status indication
"""

import time
import threading
from typing import Tuple, Optional
from enum import Enum
import os

try:
    import smbus
    SMBUS_AVAILABLE = True
except ImportError:
    SMBUS_AVAILABLE = False
    print("Warning: smbus not available, button reading disabled")


class StatusState(Enum):
    """Status states for different Muninn modes"""
    WAKE_WORD_LISTENING = "wake_word"      # Activity LED slow blink
    COMMAND_LISTENING = "command"          # Activity LED fast blink
    PROCESSING = "processing"              # Activity LED rapid blink
    SPEAKING = "speaking"                  # Activity LED solid on
    ERROR = "error"                        # Activity LED SOS pattern
    IDLE = "idle"                         # Activity LED off
    MUTED = "muted"                       # Activity LED double blink pattern


class PiHardwareController:
    """Hardware controller using Raspberry Pi built-in LEDs and ReSpeaker buttons"""

    # Pi LED paths
    ACT_LED_PATH = "/sys/class/leds/ACT"
    ACT_BRIGHTNESS = "/sys/class/leds/ACT/brightness"
    ACT_TRIGGER = "/sys/class/leds/ACT/trigger"

    # ReSpeaker I2C (for button reading only)
    I2C_BUS = 13
    XMOS_ADDR = 0x42
    RESID_CONTROL = 0xF1
    CMD_MUTE_STATUS = 0x81

    def __init__(self):
        self.current_state = StatusState.IDLE
        self.led_thread = None
        self.stop_led_thread = False
        self.bus = None
        self.last_button_check = 0

        self._initialize_hardware()

    def _initialize_hardware(self):
        """Initialize Pi LEDs and attempt ReSpeaker I2C for buttons"""
        # Initialize Pi Activity LED
        self._setup_activity_led()

        # Try to initialize ReSpeaker I2C for button reading
        if SMBUS_AVAILABLE:
            try:
                self.bus = smbus.SMBus(self.I2C_BUS)
                print("✓ ReSpeaker I2C initialized for button reading")
            except Exception as e:
                print(f"⚠️ ReSpeaker I2C not available: {e}")
                self.bus = None

        print("✓ Pi hardware controller initialized")

    def _setup_activity_led(self):
        """Setup Pi Activity LED for manual control"""
        try:
            # Disable default trigger so we can control manually
            with open(self.ACT_TRIGGER, 'w') as f:
                f.write('none')

            # Turn off initially
            with open(self.ACT_BRIGHTNESS, 'w') as f:
                f.write('0')

            print("✓ Activity LED ready for status indication")

        except PermissionError:
            print("⚠️ No permission to control Activity LED (try running as root)")
        except Exception as e:
            print(f"⚠️ Could not setup Activity LED: {e}")

    def _set_activity_led(self, on: bool):
        """Control Pi Activity LED"""
        try:
            with open(self.ACT_BRIGHTNESS, 'w') as f:
                f.write('1' if on else '0')
        except:
            pass  # Silently ignore LED control errors

    def _read_mute_button_i2c(self) -> bool:
        """Try to read mute button via I2C"""
        if not self.bus:
            return False

        try:
            # Send command to read mute status
            self.bus.write_i2c_block_data(self.XMOS_ADDR, self.RESID_CONTROL, [self.CMD_MUTE_STATUS, 2])
            time.sleep(0.01)

            # Read response
            response = self.bus.read_i2c_block_data(self.XMOS_ADDR, self.RESID_CONTROL, 2)
            if response and len(response) >= 2:
                return response[1] == 1

        except:
            pass  # Silently ignore I2C errors

        return False

    def set_status(self, state: StatusState):
        """
        Set hardware status indication

        Args:
            state: Status state to indicate
        """
        if state == self.current_state:
            return

        self.current_state = state
        print(f"🎯 Hardware Status: {state.value}")

        # Stop current animation
        self.stop_led_thread = True
        if self.led_thread and self.led_thread.is_alive():
            self.led_thread.join(timeout=1.0)

        # Start new animation
        self.stop_led_thread = False
        self.led_thread = threading.Thread(target=self._status_animation_worker, args=(state,), daemon=True)
        self.led_thread.start()

    def _status_animation_worker(self, state: StatusState):
        """Worker thread for status animations using Activity LED"""

        animation_map = {
            StatusState.WAKE_WORD_LISTENING: self._animate_slow_blink,     # Slow blink
            StatusState.COMMAND_LISTENING: self._animate_fast_blink,      # Fast blink
            StatusState.PROCESSING: self._animate_rapid_blink,            # Rapid blink
            StatusState.SPEAKING: self._animate_solid_on,                 # Solid on
            StatusState.ERROR: self._animate_sos,                         # SOS pattern
            StatusState.MUTED: self._animate_double_blink,                # Double blink
            StatusState.IDLE: self._animate_off,                          # Off
        }

        animation_func = animation_map.get(state, self._animate_off)
        animation_func()

    def _animate_slow_blink(self):
        """Slow blink for wake word listening"""
        while not self.stop_led_thread:
            self._set_activity_led(True)
            if self._wait_interruptible(1.0): break
            self._set_activity_led(False)
            if self._wait_interruptible(1.0): break

    def _animate_fast_blink(self):
        """Fast blink for command listening"""
        while not self.stop_led_thread:
            self._set_activity_led(True)
            if self._wait_interruptible(0.3): break
            self._set_activity_led(False)
            if self._wait_interruptible(0.3): break

    def _animate_rapid_blink(self):
        """Rapid blink for processing"""
        while not self.stop_led_thread:
            self._set_activity_led(True)
            if self._wait_interruptible(0.1): break
            self._set_activity_led(False)
            if self._wait_interruptible(0.1): break

    def _animate_solid_on(self):
        """Solid on for speaking"""
        self._set_activity_led(True)
        while not self.stop_led_thread:
            if self._wait_interruptible(0.1): break

    def _animate_double_blink(self):
        """Double blink pattern for muted"""
        while not self.stop_led_thread:
            # Two quick blinks
            for _ in range(2):
                self._set_activity_led(True)
                if self._wait_interruptible(0.15): return
                self._set_activity_led(False)
                if self._wait_interruptible(0.15): return
            # Longer pause
            if self._wait_interruptible(1.0): break

    def _animate_sos(self):
        """SOS pattern for errors"""
        # SOS: ... --- ...
        sos_pattern = [0.2, 0.2, 0.2, 0.2, 0.2, 0.2,  # 3 short
                       0.6, 0.2, 0.6, 0.2, 0.6, 0.4,  # 3 long
                       0.2, 0.2, 0.2, 0.2, 0.2, 1.5]  # 3 short + pause

        while not self.stop_led_thread:
            for i, duration in enumerate(sos_pattern):
                led_on = (i % 2) == 0  # On for even indices
                self._set_activity_led(led_on)
                if self._wait_interruptible(duration): return

    def _animate_off(self):
        """Turn off LED"""
        self._set_activity_led(False)
        while not self.stop_led_thread:
            if self._wait_interruptible(0.1): break

    def _wait_interruptible(self, duration: float) -> bool:
        """
        Wait for duration but can be interrupted

        Returns:
            True if interrupted, False if completed normally
        """
        start_time = time.time()
        while (time.time() - start_time) < duration:
            if self.stop_led_thread:
                return True
            time.sleep(0.05)
        return False

    def check_mute_button(self) -> bool:
        """
        Check mute button state (non-blocking)

        Returns:
            True if mute button is pressed
        """
        # Throttle button checking
        current_time = time.time()
        if current_time - self.last_button_check < 0.1:
            return False

        self.last_button_check = current_time
        return self._read_mute_button_i2c()

    def cleanup(self):
        """Clean up hardware resources"""
        print("🧹 Cleaning up Pi hardware controller...")

        # Stop LED animations
        self.stop_led_thread = True
        if self.led_thread and self.led_thread.is_alive():
            self.led_thread.join(timeout=2.0)

        # Turn off Activity LED
        self._set_activity_led(False)

        # Close I2C bus
        if self.bus:
            try:
                self.bus.close()
            except:
                pass


class MockPiHardwareController:
    """Mock hardware controller for testing"""

    def __init__(self):
        self.current_state = StatusState.IDLE
        self.mute_state = False
        print("🎭 Mock Pi hardware controller initialized")

    def set_status(self, state: StatusState):
        """Mock status setting"""
        self.current_state = state
        print(f"🎭 [MOCK] Hardware Status: {state.value}")

    def check_mute_button(self) -> bool:
        """Mock mute button checking"""
        import random
        if random.random() < 0.01:  # 1% chance
            print("🎭 [MOCK] Mute button pressed!")
            return True
        return False

    def cleanup(self):
        """Mock cleanup"""
        print("🎭 [MOCK] Cleaning up hardware controller")