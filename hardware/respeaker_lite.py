#!/usr/bin/env python3

"""
ReSpeaker Lite Hardware Controller
Controls LED status indicators and reads button states via I2C
"""

import time
import threading
from typing import Tuple, Optional
from enum import Enum

try:
    import smbus
    SMBUS_AVAILABLE = True
except ImportError:
    SMBUS_AVAILABLE = False
    print("Warning: smbus not available, hardware control disabled")


class LEDState(Enum):
    """LED states for different Muninn modes"""
    WAKE_WORD_LISTENING = "wake_word"      # Blue breathing
    COMMAND_LISTENING = "command"          # Green solid
    PROCESSING = "processing"              # Yellow pulsing
    SPEAKING = "speaking"                  # Purple solid
    ERROR = "error"                        # Red flashing
    IDLE = "idle"                         # Off or dim white
    MUTED = "muted"                       # Red solid


class ReSpeakerLiteController:
    """Hardware controller for ReSpeaker Lite LED and buttons"""

    # I2C Configuration
    I2C_BUS = 13  # Default I2C bus for ReSpeaker Lite
    XMOS_ADDR = 0x42  # ReSpeaker Lite I2C address

    # I2C Commands (based on Arduino examples)
    RESID_CONTROL = 0xF1  # Control resource ID
    RESID_INFO = 0xF0     # Information resource ID

    CMD_VNR_READ = 0x80        # Read Voice Activity Level (0-100)
    CMD_MUTE_STATUS = 0x81     # Read mute button status (1=muted, 0=not muted)
    CMD_SPEAKER_MUTE = 0x10    # Control speaker mute
    CMD_FIRMWARE_VER = 0xD8    # Read firmware version

    def __init__(self, i2c_bus: int = None):
        self.i2c_bus = i2c_bus or self.I2C_BUS
        self.bus = None
        self.current_led_state = LEDState.IDLE
        self.led_thread = None
        self.stop_led_thread = False
        self.mute_state = False
        self.last_button_check = 0

        self._initialize_i2c()

    def _initialize_i2c(self):
        """Initialize I2C bus connection"""
        if not SMBUS_AVAILABLE:
            print("❌ smbus not available - hardware control disabled")
            return

        try:
            self.bus = smbus.SMBus(self.i2c_bus)
            print(f"✓ ReSpeaker Lite I2C initialized on bus {self.i2c_bus}")

            # Test connection by reading firmware version
            firmware_version = self._read_firmware_version()
            if firmware_version:
                print(f"✓ ReSpeaker Lite firmware: v{firmware_version}")
            else:
                print("⚠️ Could not read ReSpeaker Lite firmware version")

        except Exception as e:
            print(f"❌ Failed to initialize ReSpeaker Lite I2C: {e}")
            self.bus = None

    def _xmos_read_bytes(self, resid: int, cmd: int, read_byte_num: int) -> Optional[bytes]:
        """
        Read bytes from XMOS chip via I2C

        Args:
            resid: Resource ID
            cmd: Command byte
            read_byte_num: Number of bytes to read

        Returns:
            Bytes read or None if failed
        """
        if not self.bus:
            return None

        try:
            # Send read command: write [resid, cmd, read_byte_count]
            command = [cmd, read_byte_num + 1]
            self.bus.write_i2c_block_data(self.XMOS_ADDR, resid, command)

            # Small delay to let device process
            time.sleep(0.01)

            # Read response - request the specified number of bytes
            response = self.bus.read_i2c_block_data(
                self.XMOS_ADDR,
                resid,  # Use resid as register for read
                read_byte_num + 1
            )

            # First byte is status, remaining bytes are data
            if response and len(response) > 1:
                return bytes(response[1:read_byte_num + 1])

            return None

        except Exception as e:
            print(f"❌ I2C read error (resid=0x{resid:02X}, cmd=0x{cmd:02X}): {e}")
            return None

    def _xmos_write_bytes(self, resid: int, cmd: int, data: bytes) -> bool:
        """
        Write bytes to XMOS chip via I2C

        Args:
            resid: Resource ID
            cmd: Command byte
            data: Data bytes to write

        Returns:
            True if successful, False otherwise
        """
        if not self.bus:
            return False

        try:
            # Prepare command following Arduino protocol: write [cmd, byte_count, ...data] to resid
            command = [cmd, len(data)] + list(data)
            self.bus.write_i2c_block_data(self.XMOS_ADDR, resid, command)
            return True

        except Exception as e:
            print(f"❌ I2C write error (resid=0x{resid:02X}, cmd=0x{cmd:02X}): {e}")
            return False

    def _read_firmware_version(self) -> Optional[str]:
        """Read ReSpeaker Lite firmware version"""
        data = self._xmos_read_bytes(self.RESID_INFO, self.CMD_FIRMWARE_VER, 3)
        if data and len(data) >= 3:
            return f"{data[0]}.{data[1]}.{data[2]}"
        return None

    def get_voice_activity_level(self) -> int:
        """
        Get current voice activity level (0-100)

        Returns:
            Voice activity level or 0 if failed
        """
        data = self._xmos_read_bytes(self.RESID_CONTROL, self.CMD_VNR_READ, 1)
        if data and len(data) >= 1:
            return data[0]
        return 0

    def get_mute_button_status(self) -> bool:
        """
        Check if mute button is pressed

        Returns:
            True if muted, False if not muted
        """
        data = self._xmos_read_bytes(self.RESID_CONTROL, self.CMD_MUTE_STATUS, 1)
        if data and len(data) >= 1:
            return data[0] == 1
        return False

    def set_speaker_mute(self, muted: bool) -> bool:
        """
        Control speaker mute state

        Args:
            muted: True to mute, False to unmute

        Returns:
            True if successful
        """
        mute_value = bytes([1 if muted else 0])
        return self._xmos_write_bytes(self.RESID_CONTROL, self.CMD_SPEAKER_MUTE, mute_value)

    def set_led_state(self, state: LEDState):
        """
        Set LED state for different Muninn modes

        Args:
            state: LED state to set
        """
        if state == self.current_led_state:
            return

        self.current_led_state = state
        print(f"🎨 LED State: {state.value}")

        # Stop current LED animation
        self.stop_led_thread = True
        if self.led_thread and self.led_thread.is_alive():
            self.led_thread.join(timeout=1.0)

        # Start new LED animation
        self.stop_led_thread = False
        self.led_thread = threading.Thread(target=self._led_animation_worker, args=(state,), daemon=True)
        self.led_thread.start()

    def _led_animation_worker(self, state: LEDState):
        """
        Worker thread for LED animations

        Args:
            state: LED state to animate
        """
        # Note: Since we don't have direct WS2812 control via I2C commands in the examples,
        # this is a placeholder for LED control. The actual implementation would need
        # additional I2C commands or GPIO control for the WS2812 LED.

        animation_map = {
            LEDState.WAKE_WORD_LISTENING: self._animate_breathing_blue,
            LEDState.COMMAND_LISTENING: self._animate_solid_green,
            LEDState.PROCESSING: self._animate_pulsing_yellow,
            LEDState.SPEAKING: self._animate_solid_purple,
            LEDState.ERROR: self._animate_flashing_red,
            LEDState.MUTED: self._animate_solid_red,
            LEDState.IDLE: self._animate_off,
        }

        animation_func = animation_map.get(state, self._animate_off)
        animation_func()

    def _animate_breathing_blue(self):
        """Animate breathing blue for wake word listening"""
        print("🎨 LED: Breathing blue (wake word listening)")
        # Placeholder - would control WS2812 RGB LED
        while not self.stop_led_thread:
            time.sleep(0.1)

    def _animate_solid_green(self):
        """Solid green for command listening"""
        print("🎨 LED: Solid green (command listening)")
        # Placeholder - would set WS2812 to solid green
        while not self.stop_led_thread:
            time.sleep(0.1)

    def _animate_pulsing_yellow(self):
        """Pulsing yellow for processing"""
        print("🎨 LED: Pulsing yellow (processing)")
        # Placeholder - would pulse WS2812 yellow
        while not self.stop_led_thread:
            time.sleep(0.1)

    def _animate_solid_purple(self):
        """Solid purple for speaking"""
        print("🎨 LED: Solid purple (speaking)")
        # Placeholder - would set WS2812 to solid purple
        while not self.stop_led_thread:
            time.sleep(0.1)

    def _animate_flashing_red(self):
        """Flashing red for error"""
        print("🎨 LED: Flashing red (error)")
        # Placeholder - would flash WS2812 red
        while not self.stop_led_thread:
            time.sleep(0.1)

    def _animate_solid_red(self):
        """Solid red for muted"""
        print("🎨 LED: Solid red (muted)")
        # Placeholder - would set WS2812 to solid red
        while not self.stop_led_thread:
            time.sleep(0.1)

    def _animate_off(self):
        """Turn off LED"""
        print("🎨 LED: Off (idle)")
        # Placeholder - would turn off WS2812
        while not self.stop_led_thread:
            time.sleep(0.1)

    def check_buttons(self) -> Tuple[bool, bool]:
        """
        Check button states (non-blocking)

        Returns:
            Tuple of (mute_pressed, user_pressed)
        """
        # Throttle button checking to avoid excessive I2C traffic
        current_time = time.time()
        if current_time - self.last_button_check < 0.1:  # Check max 10 times per second
            return False, False

        self.last_button_check = current_time

        mute_pressed = self.get_mute_button_status()

        # For now, we only have mute button detection via I2C
        # User button detection would need additional I2C commands
        user_pressed = False  # Placeholder

        return mute_pressed, user_pressed

    def cleanup(self):
        """Clean up hardware resources"""
        print("🧹 Cleaning up ReSpeaker Lite hardware controller...")

        # Stop LED animations
        self.stop_led_thread = True
        if self.led_thread and self.led_thread.is_alive():
            self.led_thread.join(timeout=2.0)

        # Turn off LED
        self.set_led_state(LEDState.IDLE)

        # Close I2C bus
        if self.bus:
            try:
                self.bus.close()
            except:
                pass


class MockReSpeakerLiteController:
    """Mock hardware controller for testing without physical hardware"""

    def __init__(self):
        self.current_led_state = LEDState.IDLE
        self.mute_state = False
        print("🎭 Mock ReSpeaker Lite controller initialized")

    def get_voice_activity_level(self) -> int:
        """Mock voice activity level"""
        return 50  # Mock medium activity

    def get_mute_button_status(self) -> bool:
        """Mock mute button status"""
        return self.mute_state

    def set_speaker_mute(self, muted: bool) -> bool:
        """Mock speaker mute control"""
        self.mute_state = muted
        print(f"🎭 [MOCK] Speaker {'muted' if muted else 'unmuted'}")
        return True

    def set_led_state(self, state: LEDState):
        """Mock LED state setting"""
        self.current_led_state = state
        print(f"🎭 [MOCK] LED State: {state.value}")

    def check_buttons(self) -> Tuple[bool, bool]:
        """Mock button checking"""
        # Randomly simulate button presses for testing
        import random
        mute_pressed = random.random() < 0.01  # 1% chance per check
        user_pressed = random.random() < 0.005  # 0.5% chance per check

        if mute_pressed:
            print("🎭 [MOCK] Mute button pressed!")
        if user_pressed:
            print("🎭 [MOCK] User button pressed!")

        return mute_pressed, user_pressed

    def cleanup(self):
        """Mock cleanup"""
        print("🎭 [MOCK] Cleaning up hardware controller")