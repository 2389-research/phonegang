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


if __name__ == "__main__":
    # Server will be started via mcp CLI
    pass
