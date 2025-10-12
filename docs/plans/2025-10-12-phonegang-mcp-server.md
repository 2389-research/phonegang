# Phonegang MCP Server Implementation Plan

> **For Claude:** Use `${SUPERPOWERS_SKILLS_ROOT}/skills/collaboration/executing-plans/SKILL.md` to implement this plan task-by-task.

**Goal:** Build an MCP server that lets Claude directly interact with Android phones via phonegang for exploration and automation.

**Architecture:** A Python MCP server that wraps the existing phonegang library, maintaining a persistent DeviceController with automatic connection management and UI tree caching. Tools are divided into high-level (semantic operations), low-level (direct control), and management (device/cache control).

**Tech Stack:** Python 3.10+, mcp library, existing phonegang infrastructure (DeviceManager, ADBDevice, DeviceController, AccessibilityTree)

---

## Task 1: Add MCP Dependency and Server Scaffolding

**Files:**
- Modify: `pyproject.toml`
- Create: `phonegang/mcp_server.py`
- Create: `tests/test_mcp_server.py`

**Step 1: Add MCP dependency to pyproject.toml**

Edit `pyproject.toml` dependencies section:

```toml
dependencies = [
    "adb-shell[usb]>=0.4.4",
    "click>=8.3.0",
    "lxml>=6.0.2",
    "mcp>=1.0.0",
]
```

**Step 2: Install dependency**

Run: `uv sync`
Expected: MCP library installed

**Step 3: Write failing test for MCP server initialization**

Create `tests/test_mcp_server.py`:

```python
# ABOUTME: Unit tests for MCP server
# ABOUTME: Tests MCP tool handlers and server lifecycle

import pytest
from unittest.mock import Mock, patch, MagicMock
from phonegang.mcp_server import MCPPhonegangServer


class TestMCPServerInit:
    """Test MCP server initialization."""

    def test_server_creates_without_errors(self):
        """Test that server can be instantiated."""
        server = MCPPhonegangServer()
        assert server is not None

    def test_server_has_no_controller_initially(self):
        """Test that controller is None until first use."""
        server = MCPPhonegangServer()
        assert server._controller is None
        assert server._device_info is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
```

**Step 4: Run test to verify it fails**

Run: `uv run pytest tests/test_mcp_server.py -v`
Expected: ImportError for phonegang.mcp_server

**Step 5: Write minimal MCP server implementation**

Create `phonegang/mcp_server.py`:

```python
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


if __name__ == "__main__":
    # Server will be started via mcp CLI
    pass
```

**Step 6: Run test to verify it passes**

Run: `uv run pytest tests/test_mcp_server.py -v`
Expected: 2 tests PASS

**Step 7: Commit**

```bash
git add pyproject.toml phonegang/mcp_server.py tests/test_mcp_server.py
git commit -m "feat: add MCP server scaffolding and initialization"
```

---

## Task 2: Implement Device Connection Management

**Files:**
- Modify: `phonegang/mcp_server.py`
- Modify: `tests/test_mcp_server.py`

**Step 1: Write failing test for device connection**

Add to `tests/test_mcp_server.py`:

```python
class TestDeviceConnection:
    """Test device connection management."""

    @patch('phonegang.mcp_server.DeviceManager')
    @patch('phonegang.mcp_server.ADBDevice')
    @patch('phonegang.mcp_server.DeviceController')
    def test_ensure_connected_creates_controller(self, mock_controller_class, mock_device_class, mock_manager_class):
        """Test that ensure_connected creates controller on first call."""
        # Setup mocks
        mock_manager = Mock()
        mock_manager_class.return_value = mock_manager

        mock_device_info = Mock()
        mock_device_info.serial = "test_serial"
        mock_device_info.transport = None
        mock_manager.get_device.return_value = mock_device_info

        mock_device = MagicMock()
        mock_device.__enter__ = Mock(return_value=mock_device)
        mock_device.__exit__ = Mock(return_value=None)
        mock_device_class.return_value = mock_device

        mock_controller = Mock()
        mock_controller_class.return_value = mock_controller

        # Test
        server = MCPPhonegangServer()
        server._ensure_connected()

        assert server._controller is not None
        assert server._device_info is not None

    @patch('phonegang.mcp_server.DeviceManager')
    def test_ensure_connected_reuses_existing_controller(self, mock_manager_class):
        """Test that ensure_connected reuses existing controller."""
        server = MCPPhonegangServer()
        mock_controller = Mock()
        server._controller = mock_controller

        server._ensure_connected()

        # Should not create new controller
        assert server._controller is mock_controller
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_mcp_server.py::TestDeviceConnection -v`
Expected: AttributeError '_ensure_connected' not found

**Step 3: Write minimal implementation**

Add to `MCPPhonegangServer` class in `phonegang/mcp_server.py`:

```python
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
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_mcp_server.py::TestDeviceConnection -v`
Expected: 2 tests PASS

**Step 5: Run all tests**

Run: `uv run pytest tests/test_mcp_server.py -v`
Expected: All tests PASS

**Step 6: Commit**

```bash
git add phonegang/mcp_server.py tests/test_mcp_server.py
git commit -m "feat: add device connection management with lazy initialization"
```

---

## Task 3: Implement Cache Management

**Files:**
- Modify: `phonegang/mcp_server.py`
- Modify: `tests/test_mcp_server.py`

**Step 1: Write failing test for cache management**

Add to `tests/test_mcp_server.py`:

```python
class TestCacheManagement:
    """Test UI tree cache management."""

    def test_invalidate_cache_resets_timestamp(self):
        """Test that invalidate_cache resets timestamp to 0."""
        server = MCPPhonegangServer()
        server._last_dump_time = 100.0

        server._invalidate_cache()

        assert server._last_dump_time == 0.0

    @patch('phonegang.mcp_server.time.time')
    def test_is_cache_fresh_returns_true_when_fresh(self, mock_time):
        """Test cache freshness check when cache is fresh."""
        mock_time.return_value = 105.0

        server = MCPPhonegangServer(cache_timeout=2.0)
        server._last_dump_time = 104.0

        assert server._is_cache_fresh() is True

    @patch('phonegang.mcp_server.time.time')
    def test_is_cache_fresh_returns_false_when_stale(self, mock_time):
        """Test cache freshness check when cache is stale."""
        mock_time.return_value = 107.0

        server = MCPPhonegangServer(cache_timeout=2.0)
        server._last_dump_time = 100.0

        assert server._is_cache_fresh() is False

    @patch('phonegang.mcp_server.time.time')
    def test_is_cache_fresh_returns_false_when_never_cached(self, mock_time):
        """Test cache freshness check when never cached."""
        mock_time.return_value = 100.0

        server = MCPPhonegangServer()
        server._last_dump_time = 0.0

        assert server._is_cache_fresh() is False
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_mcp_server.py::TestCacheManagement -v`
Expected: AttributeError for _invalidate_cache, _is_cache_fresh

**Step 3: Write minimal implementation**

Add to `MCPPhonegangServer` class in `phonegang/mcp_server.py`:

```python
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
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_mcp_server.py::TestCacheManagement -v`
Expected: 4 tests PASS

**Step 5: Run all tests**

Run: `uv run pytest tests/test_mcp_server.py -v`
Expected: All tests PASS

**Step 6: Commit**

```bash
git add phonegang/mcp_server.py tests/test_mcp_server.py
git commit -m "feat: add UI tree cache management with freshness checks"
```

---

## Task 4: Implement list_devices Tool

**Files:**
- Modify: `phonegang/mcp_server.py`
- Modify: `tests/test_mcp_server.py`

**Step 1: Write failing test for list_devices**

Add to `tests/test_mcp_server.py`:

```python
class TestListDevicesTool:
    """Test list_devices MCP tool."""

    @patch('phonegang.mcp_server.DeviceManager')
    def test_list_devices_returns_device_list(self, mock_manager_class):
        """Test that list_devices returns formatted device list."""
        mock_manager = Mock()
        mock_manager_class.return_value = mock_manager

        mock_device1 = Mock()
        mock_device1.serial = "ABC123"
        mock_device1.model = "Pixel 6"
        mock_device1.status = "device"

        mock_device2 = Mock()
        mock_device2.serial = "DEF456"
        mock_device2.model = "Galaxy S21"
        mock_device2.status = "device"

        mock_manager.list_devices.return_value = [mock_device1, mock_device2]

        server = MCPPhonegangServer()
        result = server.list_devices()

        assert result["success"] is True
        assert result["count"] == 2
        assert len(result["devices"]) == 2
        assert result["devices"][0]["serial"] == "ABC123"

    @patch('phonegang.mcp_server.DeviceManager')
    def test_list_devices_returns_empty_when_no_devices(self, mock_manager_class):
        """Test list_devices with no connected devices."""
        mock_manager = Mock()
        mock_manager_class.return_value = mock_manager
        mock_manager.list_devices.return_value = []

        server = MCPPhonegangServer()
        result = server.list_devices()

        assert result["success"] is True
        assert result["count"] == 0
        assert result["devices"] == []
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_mcp_server.py::TestListDevicesTool -v`
Expected: AttributeError 'list_devices' not found

**Step 3: Write minimal implementation**

Add to `MCPPhonegangServer` class in `phonegang/mcp_server.py`:

```python
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
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_mcp_server.py::TestListDevicesTool -v`
Expected: 2 tests PASS

**Step 5: Run all tests**

Run: `uv run pytest -v`
Expected: All tests PASS

**Step 6: Commit**

```bash
git add phonegang/mcp_server.py tests/test_mcp_server.py
git commit -m "feat: add list_devices MCP tool"
```

---

## Task 5: Implement get_screen Tool

**Files:**
- Modify: `phonegang/mcp_server.py`
- Modify: `tests/test_mcp_server.py`

**Step 1: Write failing test for get_screen**

Add to `tests/test_mcp_server.py`:

```python
SAMPLE_XML = """<?xml version="1.0" encoding="UTF-8"?>
<hierarchy rotation="0">
  <node index="0" text="Hello" resource-id="com.test:id/text" class="android.widget.TextView"
        package="com.test" content-desc="" checkable="false" checked="false" clickable="true"
        enabled="true" focusable="false" focused="false" scrollable="false" long-clickable="false"
        password="false" selected="false" bounds="[0,0][100,100]"/>
</hierarchy>"""


class TestGetScreenTool:
    """Test get_screen MCP tool."""

    @patch('phonegang.mcp_server.DeviceManager')
    @patch('phonegang.mcp_server.ADBDevice')
    @patch('phonegang.mcp_server.DeviceController')
    def test_get_screen_returns_compact_view(self, mock_controller_class, mock_device_class, mock_manager_class):
        """Test get_screen returns compact tree view."""
        # Setup device mocks
        mock_manager = Mock()
        mock_manager_class.return_value = mock_manager
        mock_device_info = Mock()
        mock_device_info.serial = "test_serial"
        mock_device_info.transport = None
        mock_manager.list_devices.return_value = [mock_device_info]
        mock_manager.get_device.return_value = mock_device_info

        mock_device = MagicMock()
        mock_device.__enter__ = Mock(return_value=mock_device)
        mock_device.__exit__ = Mock(return_value=None)
        mock_device_class.return_value = mock_device

        # Setup controller mock
        mock_tree = Mock()
        mock_tree.render.return_value = "SCREEN OVERVIEW\nElements: 1 total"
        mock_tree.elements = [Mock(text="Hello", clickable=True)]

        mock_controller = Mock()
        mock_controller.refresh_ui.return_value = mock_tree
        mock_controller_class.return_value = mock_controller

        # Test
        server = MCPPhonegangServer()
        result = server.get_screen()

        assert result["success"] is True
        assert "SCREEN OVERVIEW" in result["output"]
        assert result["serial"] == "test_serial"

    @patch('phonegang.mcp_server.DeviceManager')
    def test_get_screen_fails_when_no_devices(self, mock_manager_class):
        """Test get_screen returns error when no devices connected."""
        mock_manager = Mock()
        mock_manager_class.return_value = mock_manager
        mock_manager.list_devices.return_value = []

        server = MCPPhonegangServer()
        result = server.get_screen()

        assert result["success"] is False
        assert "No devices connected" in result["error"]
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_mcp_server.py::TestGetScreenTool -v`
Expected: AttributeError 'get_screen' not found

**Step 3: Write minimal implementation**

Add to `MCPPhonegangServer` class in `phonegang/mcp_server.py`:

```python
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
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_mcp_server.py::TestGetScreenTool -v`
Expected: 2 tests PASS

**Step 5: Run all tests**

Run: `uv run pytest -v`
Expected: All tests PASS

**Step 6: Commit**

```bash
git add phonegang/mcp_server.py tests/test_mcp_server.py
git commit -m "feat: add get_screen MCP tool with caching"
```

---

## Task 6: Implement tap Tool

**Files:**
- Modify: `phonegang/mcp_server.py`
- Modify: `tests/test_mcp_server.py`

**Step 1: Write failing test for tap**

Add to `tests/test_mcp_server.py`:

```python
class TestTapTool:
    """Test tap MCP tool."""

    @patch('phonegang.mcp_server.DeviceManager')
    @patch('phonegang.mcp_server.ADBDevice')
    @patch('phonegang.mcp_server.DeviceController')
    def test_tap_by_text_succeeds(self, mock_controller_class, mock_device_class, mock_manager_class):
        """Test tapping element by text."""
        # Setup mocks
        mock_manager = Mock()
        mock_manager_class.return_value = mock_manager
        mock_device_info = Mock()
        mock_device_info.serial = "test_serial"
        mock_device_info.transport = None
        mock_manager.list_devices.return_value = [mock_device_info]

        mock_device = MagicMock()
        mock_device.__enter__ = Mock(return_value=mock_device)
        mock_device.__exit__ = Mock(return_value=None)
        mock_device_class.return_value = mock_device

        mock_controller = Mock()
        mock_controller.find_and_tap.return_value = True
        mock_controller_class.return_value = mock_controller

        # Test
        server = MCPPhonegangServer()
        result = server.tap(text="Login")

        assert result["success"] is True
        assert "Login" in result["message"]
        mock_controller.find_and_tap.assert_called_once_with(text="Login", resource_id=None)

    @patch('phonegang.mcp_server.DeviceManager')
    @patch('phonegang.mcp_server.ADBDevice')
    @patch('phonegang.mcp_server.DeviceController')
    def test_tap_by_resource_id_succeeds(self, mock_controller_class, mock_device_class, mock_manager_class):
        """Test tapping element by resource ID."""
        # Setup mocks
        mock_manager = Mock()
        mock_manager_class.return_value = mock_manager
        mock_device_info = Mock()
        mock_device_info.serial = "test_serial"
        mock_device_info.transport = None
        mock_manager.list_devices.return_value = [mock_device_info]

        mock_device = MagicMock()
        mock_device.__enter__ = Mock(return_value=mock_device)
        mock_device.__exit__ = Mock(return_value=None)
        mock_device_class.return_value = mock_device

        mock_controller = Mock()
        mock_controller.find_and_tap.return_value = True
        mock_controller_class.return_value = mock_controller

        # Test
        server = MCPPhonegangServer()
        result = server.tap(resource_id="login_button")

        assert result["success"] is True
        mock_controller.find_and_tap.assert_called_once_with(text=None, resource_id="login_button")

    @patch('phonegang.mcp_server.DeviceManager')
    @patch('phonegang.mcp_server.ADBDevice')
    @patch('phonegang.mcp_server.DeviceController')
    def test_tap_element_not_found(self, mock_controller_class, mock_device_class, mock_manager_class):
        """Test tap fails gracefully when element not found."""
        # Setup mocks
        mock_manager = Mock()
        mock_manager_class.return_value = mock_manager
        mock_device_info = Mock()
        mock_device_info.serial = "test_serial"
        mock_device_info.transport = None
        mock_manager.list_devices.return_value = [mock_device_info]

        mock_device = MagicMock()
        mock_device.__enter__ = Mock(return_value=mock_device)
        mock_device.__exit__ = Mock(return_value=None)
        mock_device_class.return_value = mock_device

        mock_controller = Mock()
        mock_controller.find_and_tap.return_value = False
        mock_controller_class.return_value = mock_controller

        # Test
        server = MCPPhonegangServer()
        result = server.tap(text="Nonexistent")

        assert result["success"] is False
        assert "not found" in result["message"]
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_mcp_server.py::TestTapTool -v`
Expected: AttributeError 'tap' not found

**Step 3: Write minimal implementation**

Add to `MCPPhonegangServer` class in `phonegang/mcp_server.py`:

```python
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
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_mcp_server.py::TestTapTool -v`
Expected: 3 tests PASS

**Step 5: Run all tests**

Run: `uv run pytest -v`
Expected: All tests PASS

**Step 6: Commit**

```bash
git add phonegang/mcp_server.py tests/test_mcp_server.py
git commit -m "feat: add tap MCP tool with cache invalidation"
```

---

## Task 7: Implement Additional High-Level Tools

**Files:**
- Modify: `phonegang/mcp_server.py`
- Modify: `tests/test_mcp_server.py`

**Step 1: Write failing tests for type_text and wait_for**

Add to `tests/test_mcp_server.py`:

```python
class TestTypeTextTool:
    """Test type_text MCP tool."""

    @patch('phonegang.mcp_server.DeviceManager')
    @patch('phonegang.mcp_server.ADBDevice')
    def test_type_text_succeeds(self, mock_device_class, mock_manager_class):
        """Test typing text."""
        # Setup mocks
        mock_manager = Mock()
        mock_manager_class.return_value = mock_manager
        mock_device_info = Mock()
        mock_device_info.serial = "test_serial"
        mock_device_info.transport = None
        mock_manager.list_devices.return_value = [mock_device_info]

        mock_device = MagicMock()
        mock_device.__enter__ = Mock(return_value=mock_device)
        mock_device.__exit__ = Mock(return_value=None)
        mock_device.type_text = Mock()
        mock_device_class.return_value = mock_device

        # Test
        server = MCPPhonegangServer()
        result = server.type_text("Hello World")

        assert result["success"] is True
        mock_device.type_text.assert_called_once_with("Hello World")


class TestWaitForTool:
    """Test wait_for MCP tool."""

    @patch('phonegang.mcp_server.DeviceManager')
    @patch('phonegang.mcp_server.ADBDevice')
    @patch('phonegang.mcp_server.DeviceController')
    def test_wait_for_element_found(self, mock_controller_class, mock_device_class, mock_manager_class):
        """Test waiting for element that exists."""
        # Setup mocks
        mock_manager = Mock()
        mock_manager_class.return_value = mock_manager
        mock_device_info = Mock()
        mock_device_info.serial = "test_serial"
        mock_device_info.transport = None
        mock_manager.list_devices.return_value = [mock_device_info]

        mock_device = MagicMock()
        mock_device.__enter__ = Mock(return_value=mock_device)
        mock_device.__exit__ = Mock(return_value=None)
        mock_device_class.return_value = mock_device

        mock_element = Mock()
        mock_element.text = "Done"

        mock_controller = Mock()
        mock_controller.wait_for_text.return_value = mock_element
        mock_controller_class.return_value = mock_controller

        # Test
        server = MCPPhonegangServer()
        result = server.wait_for(text="Done", timeout=5)

        assert result["success"] is True
        assert result["found"] is True
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_mcp_server.py::TestTypeTextTool -v`
Run: `uv run pytest tests/test_mcp_server.py::TestWaitForTool -v`
Expected: AttributeError for 'type_text' and 'wait_for'

**Step 3: Write minimal implementation**

Add to `MCPPhonegangServer` class in `phonegang/mcp_server.py`:

```python
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
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_mcp_server.py::TestTypeTextTool -v`
Run: `uv run pytest tests/test_mcp_server.py::TestWaitForTool -v`
Expected: All tests PASS

**Step 5: Run all tests**

Run: `uv run pytest -v`
Expected: All tests PASS

**Step 6: Commit**

```bash
git add phonegang/mcp_server.py tests/test_mcp_server.py
git commit -m "feat: add type_text and wait_for MCP tools"
```

---

## Task 8: Implement Low-Level Tools

**Files:**
- Modify: `phonegang/mcp_server.py`
- Modify: `tests/test_mcp_server.py`

**Step 1: Write failing tests for low-level tools**

Add to `tests/test_mcp_server.py`:

```python
class TestLowLevelTools:
    """Test low-level MCP tools."""

    @patch('phonegang.mcp_server.DeviceManager')
    @patch('phonegang.mcp_server.ADBDevice')
    def test_tap_xy_succeeds(self, mock_device_class, mock_manager_class):
        """Test tapping at specific coordinates."""
        mock_manager = Mock()
        mock_manager_class.return_value = mock_manager
        mock_device_info = Mock()
        mock_device_info.serial = "test_serial"
        mock_device_info.transport = None
        mock_manager.list_devices.return_value = [mock_device_info]

        mock_device = MagicMock()
        mock_device.__enter__ = Mock(return_value=mock_device)
        mock_device.__exit__ = Mock(return_value=None)
        mock_device.tap = Mock()
        mock_device_class.return_value = mock_device

        server = MCPPhonegangServer()
        result = server.tap_xy(100, 200)

        assert result["success"] is True
        mock_device.tap.assert_called_once_with(100, 200)

    @patch('phonegang.mcp_server.DeviceManager')
    @patch('phonegang.mcp_server.ADBDevice')
    def test_swipe_succeeds(self, mock_device_class, mock_manager_class):
        """Test swiping."""
        mock_manager = Mock()
        mock_manager_class.return_value = mock_manager
        mock_device_info = Mock()
        mock_device_info.serial = "test_serial"
        mock_device_info.transport = None
        mock_manager.list_devices.return_value = [mock_device_info]

        mock_device = MagicMock()
        mock_device.__enter__ = Mock(return_value=mock_device)
        mock_device.__exit__ = Mock(return_value=None)
        mock_device.swipe = Mock()
        mock_device_class.return_value = mock_device

        server = MCPPhonegangServer()
        result = server.swipe(100, 200, 100, 500, duration=300)

        assert result["success"] is True
        mock_device.swipe.assert_called_once_with(100, 200, 100, 500, 300)

    @patch('phonegang.mcp_server.DeviceManager')
    @patch('phonegang.mcp_server.ADBDevice')
    def test_press_key_succeeds(self, mock_device_class, mock_manager_class):
        """Test pressing key."""
        mock_manager = Mock()
        mock_manager_class.return_value = mock_manager
        mock_device_info = Mock()
        mock_device_info.serial = "test_serial"
        mock_device_info.transport = None
        mock_manager.list_devices.return_value = [mock_device_info]

        mock_device = MagicMock()
        mock_device.__enter__ = Mock(return_value=mock_device)
        mock_device.__exit__ = Mock(return_value=None)
        mock_device.press_key = Mock()
        mock_device_class.return_value = mock_device

        server = MCPPhonegangServer()
        result = server.press_key("KEYCODE_BACK")

        assert result["success"] is True
        mock_device.press_key.assert_called_once_with("KEYCODE_BACK")

    @patch('phonegang.mcp_server.DeviceManager')
    @patch('phonegang.mcp_server.ADBDevice')
    def test_get_ui_dump_succeeds(self, mock_device_class, mock_manager_class):
        """Test getting raw UI dump."""
        mock_manager = Mock()
        mock_manager_class.return_value = mock_manager
        mock_device_info = Mock()
        mock_device_info.serial = "test_serial"
        mock_device_info.transport = None
        mock_manager.list_devices.return_value = [mock_device_info]

        mock_device = MagicMock()
        mock_device.__enter__ = Mock(return_value=mock_device)
        mock_device.__exit__ = Mock(return_value=None)
        mock_device.get_ui_dump.return_value = "<xml>test</xml>"
        mock_device_class.return_value = mock_device

        server = MCPPhonegangServer()
        result = server.get_ui_dump()

        assert result["success"] is True
        assert result["xml"] == "<xml>test</xml>"
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_mcp_server.py::TestLowLevelTools -v`
Expected: AttributeError for various methods

**Step 3: Write minimal implementation**

Add to `MCPPhonegangServer` class in `phonegang/mcp_server.py`:

```python
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
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_mcp_server.py::TestLowLevelTools -v`
Expected: 4 tests PASS

**Step 5: Run all tests**

Run: `uv run pytest -v`
Expected: All tests PASS

**Step 6: Commit**

```bash
git add phonegang/mcp_server.py tests/test_mcp_server.py
git commit -m "feat: add low-level MCP tools (tap_xy, swipe, press_key, get_ui_dump)"
```

---

## Task 9: Implement Cache Control Tools

**Files:**
- Modify: `phonegang/mcp_server.py`
- Modify: `tests/test_mcp_server.py`

**Step 1: Write failing tests for cache control**

Add to `tests/test_mcp_server.py`:

```python
class TestCacheControlTools:
    """Test cache control MCP tools."""

    @patch('phonegang.mcp_server.DeviceManager')
    @patch('phonegang.mcp_server.ADBDevice')
    @patch('phonegang.mcp_server.DeviceController')
    def test_refresh_forces_new_dump(self, mock_controller_class, mock_device_class, mock_manager_class):
        """Test refresh forces new UI dump."""
        mock_manager = Mock()
        mock_manager_class.return_value = mock_manager
        mock_device_info = Mock()
        mock_device_info.serial = "test_serial"
        mock_device_info.transport = None
        mock_manager.list_devices.return_value = [mock_device_info]

        mock_device = MagicMock()
        mock_device.__enter__ = Mock(return_value=mock_device)
        mock_device.__exit__ = Mock(return_value=None)
        mock_device_class.return_value = mock_device

        mock_tree = Mock()
        mock_controller = Mock()
        mock_controller.refresh_ui.return_value = mock_tree
        mock_controller_class.return_value = mock_controller

        server = MCPPhonegangServer()
        result = server.refresh()

        assert result["success"] is True
        mock_controller.refresh_ui.assert_called_once()

    @patch('phonegang.mcp_server.DeviceManager')
    @patch('phonegang.mcp_server.ADBDevice')
    @patch('phonegang.mcp_server.DeviceController')
    def test_render_screen_returns_formatted_tree(self, mock_controller_class, mock_device_class, mock_manager_class):
        """Test render_screen with different modes."""
        mock_manager = Mock()
        mock_manager_class.return_value = mock_manager
        mock_device_info = Mock()
        mock_device_info.serial = "test_serial"
        mock_device_info.transport = None
        mock_manager.list_devices.return_value = [mock_device_info]

        mock_device = MagicMock()
        mock_device.__enter__ = Mock(return_value=mock_device)
        mock_device.__exit__ = Mock(return_value=None)
        mock_device_class.return_value = mock_device

        mock_tree = Mock()
        mock_tree.render.return_value = "UI HIERARCHY\ntest output"
        mock_controller = Mock()
        mock_controller.refresh_ui.return_value = mock_tree
        mock_controller.tree = mock_tree
        mock_controller_class.return_value = mock_controller

        server = MCPPhonegangServer()
        result = server.render_screen(mode="hierarchy")

        assert result["success"] is True
        assert "UI HIERARCHY" in result["output"]
        mock_tree.render.assert_called_with("hierarchy")
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_mcp_server.py::TestCacheControlTools -v`
Expected: AttributeError for 'refresh' and 'render_screen'

**Step 3: Write minimal implementation**

Add to `MCPPhonegangServer` class in `phonegang/mcp_server.py`:

```python
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

        # Use cached tree if fresh
        if not self._is_cache_fresh():
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
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_mcp_server.py::TestCacheControlTools -v`
Expected: 2 tests PASS

**Step 5: Run all tests**

Run: `uv run pytest -v`
Expected: All tests PASS

**Step 6: Commit**

```bash
git add phonegang/mcp_server.py tests/test_mcp_server.py
git commit -m "feat: add cache control tools (refresh, render_screen)"
```

---

## Task 10: Wire Up MCP Protocol

**Files:**
- Modify: `phonegang/mcp_server.py`
- Modify: `pyproject.toml`

**Step 1: Add MCP server boilerplate**

Add to `phonegang/mcp_server.py` at the bottom:

```python
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
```

**Step 2: Add CLI entry point**

Edit `pyproject.toml` to add script entry point:

```toml
[project.scripts]
phonegang = "phonegang.cli:cli"
phonegang-mcp = "phonegang.mcp_server:main"
```

**Step 3: Test MCP server manually**

Run: `uv run phonegang-mcp`

This will start the MCP server. It should wait for stdin (MCP protocol messages). Press Ctrl+C to stop.

Expected: Server starts without errors

**Step 4: Commit**

```bash
git add phonegang/mcp_server.py pyproject.toml
git commit -m "feat: wire up MCP protocol and add CLI entry point"
```

---

## Task 11: Documentation and MCP Configuration

**Files:**
- Create: `docs/mcp-setup.md`
- Modify: `README.md`

**Step 1: Create MCP setup documentation**

Create `docs/mcp-setup.md`:

```markdown
# Phonegang MCP Server Setup

This document explains how to set up the phonegang MCP server so Claude Code can directly interact with your Android phone.

## Prerequisites

1. Android phone with USB debugging enabled
2. USB cable to connect phone to computer
3. phonegang installed: `uv sync`
4. Phone authorized (run `adb devices` once and accept prompt on phone)

## MCP Configuration

Add this to your Claude Code MCP settings file:

**Location:** `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS)

```json
{
  "mcpServers": {
    "phonegang": {
      "command": "uv",
      "args": ["--directory", "/Users/harper/Public/src/2389/phonegang", "run", "phonegang-mcp"]
    }
  }
}
```

**Note:** Update the path `/Users/harper/Public/src/2389/phonegang` to match your actual phonegang installation directory.

## Restart Claude Code

After adding the configuration, restart Claude Code to load the MCP server.

## Verify Connection

In Claude Code, you should now see phonegang MCP tools available. Try:

```
Can you list my connected Android devices?
```

Claude will use the `list_devices` tool to show your connected phones.

## Available Tools

### High-Level Tools
- `get_screen()` - Get current screen state as compact tree view
- `tap(text=..., resource_id=...)` - Tap an element
- `type_text(text)` - Type text into focused field
- `wait_for(text=..., timeout=10)` - Wait for element to appear

### Low-Level Tools
- `tap_xy(x, y)` - Tap at specific coordinates
- `swipe(x1, y1, x2, y2, duration=300)` - Swipe gesture
- `press_key(keycode)` - Press hardware key (KEYCODE_BACK, KEYCODE_HOME, etc.)
- `get_ui_dump()` - Get raw XML accessibility tree

### Device Management
- `list_devices()` - Show all connected devices

### Cache Control
- `refresh()` - Force fresh UI dump, ignore cache
- `render_screen(mode)` - Get formatted tree (hierarchy/clickable/compact/spatial)

## Example Interactions

**Explore what's on screen:**
```
"What's currently showing on my phone?"
```

**Automate a task:**
```
"Open Settings, find WiFi, and tap it"
```

**Wait for UI state:**
```
"Wait for the 'Done' button to appear, then tap it"
```

## Troubleshooting

**No devices found:**
- Check USB connection
- Run `adb devices` and accept authorization on phone
- Make sure USB debugging is enabled

**Connection errors:**
- Kill existing adb server: `adb kill-server`
- Reconnect phone

**Tools not appearing:**
- Check MCP config path is correct
- Restart Claude Code
- Check Claude Code logs for MCP server errors
```

**Step 2: Update README**

Add section to `README.md` before usage examples:

```markdown
## MCP Server

Phonegang includes an MCP (Model Context Protocol) server that lets Claude Code directly interact with your Android phone. See [docs/mcp-setup.md](docs/mcp-setup.md) for setup instructions.

With the MCP server, you can:
- Ask Claude to explore your phone's UI
- Describe automation tasks in natural language
- Have Claude execute multi-step phone interactions
- Debug automation scripts with Claude's help
```

**Step 3: Commit**

```bash
git add docs/mcp-setup.md README.md
git commit -m "docs: add MCP server setup guide and update README"
```

---

## Summary

This plan implements a complete MCP server for phonegang with:
- 12 MCP tools (high-level, low-level, management, cache control)
- Automatic device connection management
- Smart UI tree caching with invalidation
- Error handling and graceful failures
- Full test coverage
- Documentation for setup and usage

After completion, Claude Code will be able to directly interact with your Android phone for exploration and automation.
