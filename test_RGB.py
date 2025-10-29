#!/usr/bin/env python3
"""
Test ReSpeaker Lite RGB LED
"""
from pixel_ring import pixel_ring
import time

# Detect and setup the device
pixel_ring.change_pattern('echo')  # For ReSpeaker USB devices

# Test 1: Different colors
print("Testing colors...")
pixel_ring.set_color(rgb=(255, 0, 0))  # Red
time.sleep(1)
pixel_ring.set_color(rgb=(0, 255, 0))  # Green
time.sleep(1)
pixel_ring.set_color(rgb=(0, 0, 255))  # Blue
time.sleep(1)
pixel_ring.set_color(rgb=(255, 255, 0))  # Yellow
time.sleep(1)
pixel_ring.set_color(rgb=(255, 0, 255))  # Magenta
time.sleep(1)
pixel_ring.set_color(rgb=(0, 255, 255))  # Cyan
time.sleep(1)

# Test 2: Patterns
print("Testing patterns...")
pixel_ring.think()  # Spinning pattern
time.sleep(3)

pixel_ring.spin()  # Another spinning pattern
time.sleep(3)

pixel_ring.speak()  # Speaking animation
time.sleep(3)

# Test 3: Brightness
print("Testing brightness...")
for brightness in range(0, 100, 10):
    pixel_ring.set_brightness(brightness)
    pixel_ring.set_color(rgb=(255, 255, 255))  # White
    time.sleep(0.3)

# Turn off
pixel_ring.off()
print("Test complete!")