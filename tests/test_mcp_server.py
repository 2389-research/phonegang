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


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
