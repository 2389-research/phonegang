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
