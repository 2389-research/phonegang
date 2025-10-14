# ABOUTME: phonegang package - Android phone control suite using accessibility trees
# ABOUTME: Main package initialization exposing core functionality

from phonegang.device_manager import DeviceManager
from phonegang.adb_wrapper import ADBDevice
from phonegang.accessibility_tree import AccessibilityTree, Element
from phonegang.controller import DeviceController
from phonegang.scrcpy_wrapper import ScrcpyManager, ScrcpyConfig, mirror_device

__all__ = [
    "DeviceManager",
    "ADBDevice",
    "AccessibilityTree",
    "Element",
    "DeviceController",
    "ScrcpyManager",
    "ScrcpyConfig",
    "mirror_device",
]
__version__ = "0.1.0"
