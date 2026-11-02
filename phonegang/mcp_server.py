# ABOUTME: MCP server for phonegang Android device control
# ABOUTME: Provides MCP tools for direct phone interaction via Claude

import time
import threading
from typing import Optional, Dict, Any
from mcp.server import Server
from mcp.types import Tool, TextContent
from phonegang.device_manager import DeviceManager, DeviceInfo
from phonegang.adb_wrapper import ADBDevice
from phonegang.controller import DeviceController
from phonegang.config import UI_CACHE_TIMEOUT_SECONDS


class MCPPhonegangServer:
    """MCP server that wraps phonegang functionality."""

    def __init__(self, cache_timeout: float = UI_CACHE_TIMEOUT_SECONDS):
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
        self._cache_lock = threading.Lock()  # Protect cache operations

    def _ensure_connected(self, serial: Optional[str] = None):
        """
        Ensure device is connected, connecting if necessary.

        Args:
            serial: Optional device serial. If None, uses first device.
        """
        # If already connected and no serial change, reuse
        if self._controller is not None and self._device_info is not None:
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
        with self._cache_lock:
            self._last_dump_time = 0.0

    def _invalidate_cache(self):
        """Mark cache as stale."""
        with self._cache_lock:
            self._last_dump_time = 0.0

    def _is_cache_fresh(self) -> bool:
        """
        Check if cached UI tree is still fresh.

        Returns:
            True if cache is fresh, False otherwise
        """
        with self._cache_lock:
            if self._last_dump_time == 0.0:
                return False

            age = time.time() - self._last_dump_time
            return age < self.cache_timeout

    def _update_cache_timestamp(self):
        """Update cache timestamp to current time."""
        with self._cache_lock:
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

            # Use cached tree if fresh, otherwise refresh
            if not self._is_cache_fresh() or self._controller.tree is None:
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

    def refresh(self, serial: Optional[str] = None) -> Dict[str, Any]:
        """
        Force refresh of UI tree, ignoring cache.

        Args:
            serial: Optional device serial

        Returns:
            Dict with success
        """
        try:
            self._ensure_connected(serial)
            self._controller.refresh_ui()
            self._update_cache_timestamp()

            return {
                "success": True,
                "message": "Screen refreshed"
            }
        except Exception as e:
            return {
                "success": False,
                "message": str(e)
            }

    def render_screen(self, mode: str = "hierarchy", serial: Optional[str] = None) -> Dict[str, Any]:
        """
        Render screen in specified format.

        Args:
            mode: Rendering mode (hierarchy, clickable, compact, spatial)
            serial: Optional device serial

        Returns:
            Dict with success and rendered output
        """
        try:
            if mode not in ["hierarchy", "clickable", "compact", "spatial"]:
                return {
                    "success": False,
                    "message": f"Invalid mode: {mode}. Use hierarchy, clickable, compact, or spatial."
                }

            self._ensure_connected(serial)

            # Use cached tree if fresh, otherwise refresh
            if not self._is_cache_fresh() or self._controller.tree is None:
                tree = self._controller.refresh_ui()
                self._update_cache_timestamp()
            else:
                tree = self._controller.tree

            output = tree.render(mode)

            return {
                "success": True,
                "output": output,
                "mode": mode
            }
        except Exception as e:
            return {
                "success": False,
                "message": str(e)
            }

    def take_screenshot(self, serial: Optional[str] = None) -> Dict[str, Any]:
        """
        Take a screenshot and return it as base64-encoded image.

        Args:
            serial: Optional device serial

        Returns:
            Dict with success, base64 image data, and mime type
        """
        import base64
        import os

        try:
            self._ensure_connected(serial)

            # Take screenshot and get file path
            screenshot_path = self._device.take_screenshot()

            # Read and encode as base64
            with open(screenshot_path, 'rb') as f:
                image_data = f.read()
                base64_data = base64.b64encode(image_data).decode('utf-8')

            # Clean up temp file if it was auto-generated
            if '/tmp/' in screenshot_path or '/sdcard/' in screenshot_path:
                try:
                    os.remove(screenshot_path)
                except:
                    pass

            return {
                "success": True,
                "image": base64_data,
                "mime_type": "image/png",
                "serial": self._device_info.serial
            }
        except Exception as e:
            return {
                "success": False,
                "message": str(e)
            }


def create_mcp_server() -> Server:
    """Create and configure MCP server with phonegang tools."""
    server = Server("phonegang")
    phone_server = MCPPhonegangServer()

    @server.list_tools()
    async def list_tools() -> list[Tool]:
        """List available MCP tools."""
        return [
            Tool(
                name="list_devices",
                description="List all connected Android devices",
                inputSchema={
                    "type": "object",
                    "properties": {},
                }
            ),
            Tool(
                name="get_screen",
                description="Get current screen state as compact tree view",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "serial": {
                            "type": "string",
                            "description": "Optional device serial number"
                        }
                    },
                }
            ),
            Tool(
                name="tap",
                description="Tap an element by text or resource ID",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "text": {
                            "type": "string",
                            "description": "Element text to find"
                        },
                        "resource_id": {
                            "type": "string",
                            "description": "Element resource ID to find"
                        },
                        "serial": {
                            "type": "string",
                            "description": "Optional device serial number"
                        }
                    },
                }
            ),
            Tool(
                name="type_text",
                description="Type text into currently focused field",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "text": {
                            "type": "string",
                            "description": "Text to type"
                        },
                        "serial": {
                            "type": "string",
                            "description": "Optional device serial number"
                        }
                    },
                    "required": ["text"]
                }
            ),
            Tool(
                name="wait_for",
                description="Wait for element to appear",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "text": {
                            "type": "string",
                            "description": "Element text to wait for"
                        },
                        "resource_id": {
                            "type": "string",
                            "description": "Element resource ID to wait for"
                        },
                        "timeout": {
                            "type": "number",
                            "description": "Maximum seconds to wait (default: 10)"
                        },
                        "serial": {
                            "type": "string",
                            "description": "Optional device serial number"
                        }
                    },
                }
            ),
            Tool(
                name="tap_xy",
                description="Tap at specific coordinates",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "x": {
                            "type": "number",
                            "description": "X coordinate"
                        },
                        "y": {
                            "type": "number",
                            "description": "Y coordinate"
                        },
                        "serial": {
                            "type": "string",
                            "description": "Optional device serial number"
                        }
                    },
                    "required": ["x", "y"]
                }
            ),
            Tool(
                name="swipe",
                description="Swipe between two points",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "x1": {"type": "number", "description": "Start X coordinate"},
                        "x2": {"type": "number", "description": "End X coordinate"},
                        "y1": {"type": "number", "description": "Start Y coordinate"},
                        "y2": {"type": "number", "description": "End Y coordinate"},
                        "duration": {
                            "type": "number",
                            "description": "Swipe duration in milliseconds (default: 300)"
                        },
                        "serial": {
                            "type": "string",
                            "description": "Optional device serial number"
                        }
                    },
                    "required": ["x1", "y1", "x2", "y2"]
                }
            ),
            Tool(
                name="press_key",
                description="Press a hardware/software key",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "keycode": {
                            "type": "string",
                            "description": "Android keycode (e.g., KEYCODE_BACK, KEYCODE_HOME)"
                        },
                        "serial": {
                            "type": "string",
                            "description": "Optional device serial number"
                        }
                    },
                    "required": ["keycode"]
                }
            ),
            Tool(
                name="get_ui_dump",
                description="Get raw XML UI dump",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "serial": {
                            "type": "string",
                            "description": "Optional device serial number"
                        }
                    },
                }
            ),
            Tool(
                name="refresh",
                description="Force refresh of UI tree, ignoring cache",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "serial": {
                            "type": "string",
                            "description": "Optional device serial number"
                        }
                    },
                }
            ),
            Tool(
                name="render_screen",
                description="Render screen in specified format (hierarchy, clickable, compact, spatial)",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "mode": {
                            "type": "string",
                            "description": "Rendering mode",
                            "enum": ["hierarchy", "clickable", "compact", "spatial"]
                        },
                        "serial": {
                            "type": "string",
                            "description": "Optional device serial number"
                        }
                    },
                }
            ),
            Tool(
                name="take_screenshot",
                description="Take a screenshot of the device screen and return as base64 image",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "serial": {
                            "type": "string",
                            "description": "Optional device serial number"
                        }
                    },
                }
            ),
        ]

    @server.call_tool()
    async def call_tool(name: str, arguments: dict) -> list[TextContent]:
        """Execute MCP tool."""
        import json

        # Route to appropriate method
        method = getattr(phone_server, name, None)
        if method is None:
            result = {"success": False, "error": f"Unknown tool: {name}"}
        else:
            result = method(**arguments)

        return [TextContent(type="text", text=json.dumps(result, indent=2))]

    return server


def main():
    """Run MCP server."""
    import asyncio
    from mcp.server.stdio import stdio_server

    async def run():
        async with stdio_server() as (read_stream, write_stream):
            server = create_mcp_server()
            await server.run(
                read_stream,
                write_stream,
                server.create_initialization_options()
            )

    asyncio.run(run())


if __name__ == "__main__":
    main()
