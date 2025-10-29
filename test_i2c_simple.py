#!/usr/bin/env python3

"""
Simple I2C test for ReSpeaker Lite
Tests basic communication without complex hardware controller
"""

import time

try:
    import smbus
    bus = smbus.SMBus(13)
    XMOS_ADDR = 0x42

    print("🧪 Simple I2C Test for ReSpeaker Lite")
    print("=" * 40)

    print(f"Testing I2C communication to address 0x{XMOS_ADDR:02X} on bus 13...")

    # Test 1: Try to read firmware version (ResID 0xF0, CMD 0xD8, 3 bytes)
    print("\nTest 1: Reading firmware version...")
    try:
        # Write command: [0xD8, 4] to register 0xF0
        bus.write_i2c_block_data(XMOS_ADDR, 0xF0, [0xD8, 4])
        time.sleep(0.05)  # Wait a bit

        # Try to read response
        response = bus.read_i2c_block_data(XMOS_ADDR, 0xF0, 4)
        print(f"Response: {[hex(x) for x in response]}")
        if len(response) >= 4:
            print(f"Firmware: v{response[1]}.{response[2]}.{response[3]}")
    except Exception as e:
        print(f"Failed: {e}")

    # Test 2: Try to read VNR value (ResID 0xF1, CMD 0x80, 1 byte)
    print("\nTest 2: Reading VNR value...")
    try:
        # Write command: [0x80, 2] to register 0xF1
        bus.write_i2c_block_data(XMOS_ADDR, 0xF1, [0x80, 2])
        time.sleep(0.05)

        # Try to read response
        response = bus.read_i2c_block_data(XMOS_ADDR, 0xF1, 2)
        print(f"Response: {[hex(x) for x in response]}")
        if len(response) >= 2:
            print(f"VNR Value: {response[1]}")
    except Exception as e:
        print(f"Failed: {e}")

    # Test 3: Try to read mute status (ResID 0xF1, CMD 0x81, 1 byte)
    print("\nTest 3: Reading mute status...")
    try:
        # Write command: [0x81, 2] to register 0xF1
        bus.write_i2c_block_data(XMOS_ADDR, 0xF1, [0x81, 2])
        time.sleep(0.05)

        # Try to read response
        response = bus.read_i2c_block_data(XMOS_ADDR, 0xF1, 2)
        print(f"Response: {[hex(x) for x in response]}")
        if len(response) >= 2:
            print(f"Mute Status: {'MUTED' if response[1] == 1 else 'NOT MUTED'}")
    except Exception as e:
        print(f"Failed: {e}")

    print("\n✅ Simple I2C test completed!")
    bus.close()

except ImportError:
    print("❌ smbus not available")
except Exception as e:
    print(f"❌ Test failed: {e}")
    import traceback
    traceback.print_exc()