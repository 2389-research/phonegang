# ABOUTME: MCP server for phonegang Android device control
# ABOUTME: Provides MCP tools for direct phone interaction via Claude

import time
from typing import Optional, Dict, Any
from mcp.server import Server
from mcp.types import Tool, TextContent
from phonegang.device_manager import DeviceManager, DeviceInfo
from phonegang.adb_wrapper import ADBDevice
from phonegang.controller import DeviceController


class MCPPhonegangServer:
    """MCP server that wraps phonegang functionality."""

    def __init__(self, cache_timeout: float = 2.0):
        """
        Initialize MCP server.

        Args:
            cache_timeout: How long to cache UI tree in seconds
        """
        self.cache_timeout = cache_timeout
        self._controller: Optional[DeviceController] = None
        self._device_info: Optional[DeviceInfo] = None
        self._device: Optional[ADBDevice] = None
        self._manager = DeviceManager()
        self._last_dump_time = 0.0

    def _ensure_connected(self, serial: Optional[str] = None):
        """
        Ensure device is connected, connecting if necessary.

        Args:
            serial: Optional device serial. If None, uses first device.
        """
        # If already connected and no serial change, reuse
        if self._controller is not None:
            if serial is None or serial == self._device_info.serial:
                return
            # Different serial requested, disconnect and reconnect
            self._disconnect()

        # Connect to device
        devices = self._manager.list_devices()
        if not devices:
            raise ValueError("No devices connected")

        if serial:
            self._device_info = self._manager.get_device(serial)
        else:
            self._device_info = devices[0]

        # Create connection
        device_param = self._device_info.transport if self._device_info.transport else self._device_info.serial
        self._device = ADBDevice(device_param)
        self._device.connect()

        # Create controller
        self._controller = DeviceController(self._device)

    def _disconnect(self):
        """Disconnect from device and clean up."""
        if self._device:
            self._device.disconnect()
            self._device = None
        self._controller = None
        self._device_info = None
        self._last_dump_time = 0.0

    def _invalidate_cache(self):
        """Mark cache as stale."""
        self._last_dump_time = 0.0

    def _is_cache_fresh(self) -> bool:
        """
        Check if cached UI tree is still fresh.

        Returns:
            True if cache is fresh, False otherwise
        """
        if self._last_dump_time == 0.0:
            return False

        age = time.time() - self._last_dump_time
        return age < self.cache_timeout

    def _update_cache_timestamp(self):
        """Update cache timestamp to current time."""
        self._last_dump_time = time.time()

    def list_devices(self) -> Dict[str, Any]:
        """
        List all connected Android devices.

        Returns:
            Dict with success, count, and device list
        """
        try:
            devices = self._manager.list_devices()

            device_list = [
                {
                    "serial": d.serial,
                    "model": d.model,
                    "status": d.status
                }
                for d in devices
            ]

            return {
                "success": True,
                "count": len(devices),
                "devices": device_list
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "count": 0,
                "devices": []
            }

    def get_screen(self, serial: Optional[str] = None) -> Dict[str, Any]:
        """
        Get current screen state as compact tree view.

        Args:
            serial: Optional device serial

        Returns:
            Dict with success, output (rendered tree), and serial
        """
        try:
            self._ensure_connected(serial)

            # Use cached tree if fresh
            if not self._is_cache_fresh():
                tree = self._controller.refresh_ui()
                self._update_cache_timestamp()
            else:
                tree = self._controller.tree

            # Render in compact mode
            output = tree.render("compact")

            return {
                "success": True,
                "output": output,
                "serial": self._device_info.serial
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def tap(self, text: Optional[str] = None, resource_id: Optional[str] = None,
            serial: Optional[str] = None) -> Dict[str, Any]:
        """
        Tap an element by text or resource ID.

        Args:
            text: Element text to find
            resource_id: Element resource ID to find
            serial: Optional device serial

        Returns:
            Dict with success and message
        """
        try:
            if text is None and resource_id is None:
                return {
                    "success": False,
                    "message": "Must provide either text or resource_id"
                }

            self._ensure_connected(serial)

            # Find and tap element
            success = self._controller.find_and_tap(text=text, resource_id=resource_id)

            # Invalidate cache since UI changed
            self._invalidate_cache()

            if success:
                identifier = text if text else resource_id
                return {
                    "success": True,
                    "message": f"Tapped element: {identifier}"
                }
            else:
                identifier = text if text else resource_id
                return {
                    "success": False,
                    "message": f"Element not found: {identifier}"
                }
        except Exception as e:
            return {
                "success": False,
                "message": str(e)
            }

    def type_text(self, text: str, serial: Optional[str] = None) -> Dict[str, Any]:
        """
        Type text into currently focused field.

        Args:
            text: Text to type
            serial: Optional device serial

        Returns:
            Dict with success
        """
        try:
            self._ensure_connected(serial)
            self._device.type_text(text)
            self._invalidate_cache()

            return {
                "success": True,
                "message": f"Typed: {text}"
            }
        except Exception as e:
            return {
                "success": False,
                "message": str(e)
            }

    def wait_for(self, text: Optional[str] = None, resource_id: Optional[str] = None,
                 timeout: int = 10, serial: Optional[str] = None) -> Dict[str, Any]:
        """
        Wait for element to appear.

        Args:
            text: Element text to wait for
            resource_id: Element resource ID to wait for
            timeout: Maximum seconds to wait
            serial: Optional device serial

        Returns:
            Dict with success, found status, and optional element info
        """
        try:
            if text is None and resource_id is None:
                return {
                    "success": False,
                    "found": False,
                    "message": "Must provide either text or resource_id"
                }

            self._ensure_connected(serial)

            # Wait for element
            if text:
                element = self._controller.wait_for_text(text, timeout=timeout)
            else:
                # For resource_id, we need to implement polling
                import time
                start_time = time.time()
                element = None
                while time.time() - start_time < timeout:
                    tree = self._controller.refresh_ui()
                    elements = tree.find_by_resource_id(resource_id)
                    if elements:
                        element = elements[0]
                        break
                    time.sleep(0.5)

            if element:
                return {
                    "success": True,
                    "found": True,
                    "element": {
                        "text": element.text,
                        "resource_id": element.resource_id,
                        "clickable": element.clickable
                    }
                }
            else:
                identifier = text if text else resource_id
                return {
                    "success": True,
                    "found": False,
                    "message": f"Element not found after {timeout}s: {identifier}"
                }
        except Exception as e:
            return {
                "success": False,
                "found": False,
                "message": str(e)
            }

    def tap_xy(self, x: int, y: int, serial: Optional[str] = None) -> Dict[str, Any]:
        """
        Tap at specific coordinates.

        Args:
            x: X coordinate
            y: Y coordinate
            serial: Optional device serial

        Returns:
            Dict with success
        """
        try:
            self._ensure_connected(serial)
            self._device.tap(x, y)
            self._invalidate_cache()

            return {
                "success": True,
                "message": f"Tapped at ({x}, {y})"
            }
        except Exception as e:
            return {
                "success": False,
                "message": str(e)
            }

    def swipe(self, x1: int, y1: int, x2: int, y2: int, duration: int = 300,
              serial: Optional[str] = None) -> Dict[str, Any]:
        """
        Swipe between two points.

        Args:
            x1: Start X coordinate
            y1: Start Y coordinate
            x2: End X coordinate
            y2: End Y coordinate
            duration: Swipe duration in milliseconds
            serial: Optional device serial

        Returns:
            Dict with success
        """
        try:
            self._ensure_connected(serial)
            self._device.swipe(x1, y1, x2, y2, duration)
            self._invalidate_cache()

            return {
                "success": True,
                "message": f"Swiped from ({x1}, {y1}) to ({x2}, {y2})"
            }
        except Exception as e:
            return {
                "success": False,
                "message": str(e)
            }

    def press_key(self, keycode: str, serial: Optional[str] = None) -> Dict[str, Any]:
        """
        Press a key.

        Args:
            keycode: Android keycode (e.g., 'KEYCODE_BACK', 'KEYCODE_HOME')
            serial: Optional device serial

        Returns:
            Dict with success
        """
        try:
            self._ensure_connected(serial)
            self._device.press_key(keycode)
            self._invalidate_cache()

            return {
                "success": True,
                "message": f"Pressed key: {keycode}"
            }
        except Exception as e:
            return {
                "success": False,
                "message": str(e)
            }

    def get_ui_dump(self, serial: Optional[str] = None) -> Dict[str, Any]:
        """
        Get raw XML UI dump.

        Args:
            serial: Optional device serial

        Returns:
            Dict with success and XML content
        """
        try:
            self._ensure_connected(serial)
            xml = self._device.get_ui_dump()

            return {
                "success": True,
                "xml": xml
            }
        except Exception as e:
            return {
                "success": False,
                "message": str(e)
            }


if __name__ == "__main__":
    # Server will be started via mcp CLI
    pass
