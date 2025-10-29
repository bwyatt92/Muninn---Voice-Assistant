#!/usr/bin/env python3

"""
Hardware Control Module for Muninn
Provides access to Pi hardware controls and ReSpeaker button inputs for status indication
"""

from .pi_hardware import PiHardwareController, MockPiHardwareController, StatusState

def get_hardware_controller(mock_mode: bool = False):
    """
    Factory function to get appropriate hardware controller

    Args:
        mock_mode: Use mock controller instead of real controller

    Returns:
        Hardware controller instance
    """
    if mock_mode:
        return MockPiHardwareController()

    return PiHardwareController()

__all__ = ['get_hardware_controller', 'PiHardwareController', 'MockPiHardwareController', 'StatusState']