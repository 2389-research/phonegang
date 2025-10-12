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
        mock_manager.list_devices.return_value = [mock_device_info]
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

    @patch('phonegang.mcp_server.DeviceManager')
    @patch('phonegang.mcp_server.ADBDevice')
    @patch('phonegang.mcp_server.DeviceController')
    def test_ensure_connected_switches_devices_when_serial_changes(self, mock_controller_class, mock_device_class, mock_manager_class):
        """Test that ensure_connected disconnects and reconnects when different serial is requested."""
        # Setup mocks
        mock_manager = Mock()
        mock_manager_class.return_value = mock_manager

        # First device
        mock_device_info_1 = Mock()
        mock_device_info_1.serial = "device_1"
        mock_device_info_1.transport = None

        # Second device
        mock_device_info_2 = Mock()
        mock_device_info_2.serial = "device_2"
        mock_device_info_2.transport = None

        mock_manager.list_devices.return_value = [mock_device_info_1, mock_device_info_2]
        mock_manager.get_device.side_effect = lambda serial: mock_device_info_1 if serial == "device_1" else mock_device_info_2

        mock_device_1 = Mock()
        mock_device_2 = Mock()
        mock_device_class.side_effect = [mock_device_1, mock_device_2]

        mock_controller_1 = Mock()
        mock_controller_2 = Mock()
        mock_controller_class.side_effect = [mock_controller_1, mock_controller_2]

        # Test
        server = MCPPhonegangServer()

        # Connect to first device
        server._ensure_connected("device_1")
        assert server._controller is mock_controller_1
        assert server._device_info.serial == "device_1"

        # Connect to second device - should disconnect and reconnect
        server._ensure_connected("device_2")
        assert server._controller is mock_controller_2
        assert server._device_info.serial == "device_2"

        # Verify disconnect was called on first device
        mock_device_1.disconnect.assert_called_once()

    @patch('phonegang.mcp_server.DeviceManager')
    def test_ensure_connected_raises_error_when_no_devices(self, mock_manager_class):
        """Test that ensure_connected raises error when no devices are connected."""
        # Setup mocks
        mock_manager = Mock()
        mock_manager_class.return_value = mock_manager
        mock_manager.list_devices.return_value = []

        # Test
        server = MCPPhonegangServer()

        with pytest.raises(ValueError, match="No devices connected"):
            server._ensure_connected()

    def test_disconnect_cleans_up_state(self):
        """Test that disconnect properly cleans up all state."""
        server = MCPPhonegangServer()

        # Setup some state
        mock_device = Mock()
        mock_controller = Mock()
        mock_device_info = Mock()

        server._device = mock_device
        server._controller = mock_controller
        server._device_info = mock_device_info
        server._last_dump_time = 123.45

        # Disconnect
        server._disconnect()

        # Verify all state cleaned up
        assert server._device is None
        assert server._controller is None
        assert server._device_info is None
        assert server._last_dump_time == 0.0

        # Verify device disconnect was called
        mock_device.disconnect.assert_called_once()


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


SAMPLE_XML = """<?xml version="1.0" encoding="UTF-8"?>
<hierarchy rotation="0">
  <node index="0" text="Hello" resource-id="com.test:id/text" class="android.widget.TextView"
        package="com.test" content-desc="" checkable="false" checked="false" clickable="true"
        enabled="true" focusable="false" focused="false" scrollable="false" long-clickable="false"
        password="false" selected="false" bounds="[0,0][100,100]"/>
</hierarchy>"""


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


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
