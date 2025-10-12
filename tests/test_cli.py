# ABOUTME: Unit tests for CLI commands
# ABOUTME: Tests command-line interface functionality including device management and UI interaction

import pytest
from click.testing import CliRunner
from phonegang.cli import cli
from phonegang.accessibility_tree import AccessibilityTree
from unittest.mock import Mock, patch, MagicMock


# Sample XML for testing rendering
SAMPLE_XML = """<?xml version="1.0" encoding="UTF-8"?>
<hierarchy rotation="0">
  <node index="0" text="Hello" resource-id="com.test:id/text" class="android.widget.TextView"
        package="com.test" content-desc="" checkable="false" checked="false" clickable="true"
        enabled="true" focusable="false" focused="false" scrollable="false" long-clickable="false"
        password="false" selected="false" bounds="[0,0][100,100]"/>
</hierarchy>"""


class TestRenderCommand:
    """Test the render CLI command."""

    def test_render_command_hierarchy_mode(self):
        """Test render command with hierarchy mode."""
        runner = CliRunner()

        # Mock the device manager and device
        with patch('phonegang.cli.DeviceManager') as mock_manager_class:
            mock_manager = Mock()
            mock_manager_class.return_value = mock_manager

            mock_device_info = Mock()
            mock_device_info.serial = "test_serial"
            mock_device_info.transport = None
            mock_manager.get_device.return_value = mock_device_info

            with patch('phonegang.cli.ADBDevice') as mock_device_class:
                mock_device = MagicMock()
                mock_device.__enter__ = Mock(return_value=mock_device)
                mock_device.__exit__ = Mock(return_value=None)
                mock_device.get_ui_dump.return_value = SAMPLE_XML
                mock_device_class.return_value = mock_device

                # Run the command
                result = runner.invoke(cli, ['render', '--mode', 'hierarchy'])

                # Verify output
                assert result.exit_code == 0
                assert "UI HIERARCHY" in result.output
                assert "TextView" in result.output

    def test_render_command_clickable_mode(self):
        """Test render command with clickable mode."""
        runner = CliRunner()

        with patch('phonegang.cli.DeviceManager') as mock_manager_class:
            mock_manager = Mock()
            mock_manager_class.return_value = mock_manager

            mock_device_info = Mock()
            mock_device_info.serial = "test_serial"
            mock_device_info.transport = None
            mock_manager.get_device.return_value = mock_device_info

            with patch('phonegang.cli.ADBDevice') as mock_device_class:
                mock_device = MagicMock()
                mock_device.__enter__ = Mock(return_value=mock_device)
                mock_device.__exit__ = Mock(return_value=None)
                mock_device.get_ui_dump.return_value = SAMPLE_XML
                mock_device_class.return_value = mock_device

                result = runner.invoke(cli, ['render', '--mode', 'clickable'])

                assert result.exit_code == 0
                assert "CLICKABLE ELEMENTS" in result.output

    def test_render_command_compact_mode(self):
        """Test render command with compact mode."""
        runner = CliRunner()

        with patch('phonegang.cli.DeviceManager') as mock_manager_class:
            mock_manager = Mock()
            mock_manager_class.return_value = mock_manager

            mock_device_info = Mock()
            mock_device_info.serial = "test_serial"
            mock_device_info.transport = None
            mock_manager.get_device.return_value = mock_device_info

            with patch('phonegang.cli.ADBDevice') as mock_device_class:
                mock_device = MagicMock()
                mock_device.__enter__ = Mock(return_value=mock_device)
                mock_device.__exit__ = Mock(return_value=None)
                mock_device.get_ui_dump.return_value = SAMPLE_XML
                mock_device_class.return_value = mock_device

                result = runner.invoke(cli, ['render', '--mode', 'compact'])

                assert result.exit_code == 0
                assert "SCREEN OVERVIEW" in result.output

    def test_render_command_spatial_mode(self):
        """Test render command with spatial mode."""
        runner = CliRunner()

        with patch('phonegang.cli.DeviceManager') as mock_manager_class:
            mock_manager = Mock()
            mock_manager_class.return_value = mock_manager

            mock_device_info = Mock()
            mock_device_info.serial = "test_serial"
            mock_device_info.transport = None
            mock_manager.get_device.return_value = mock_device_info

            with patch('phonegang.cli.ADBDevice') as mock_device_class:
                mock_device = MagicMock()
                mock_device.__enter__ = Mock(return_value=mock_device)
                mock_device.__exit__ = Mock(return_value=None)
                mock_device.get_ui_dump.return_value = SAMPLE_XML
                mock_device_class.return_value = mock_device

                result = runner.invoke(cli, ['render', '--mode', 'spatial'])

                assert result.exit_code == 0
                assert "SPATIAL LAYOUT" in result.output

    def test_render_command_default_mode(self):
        """Test render command defaults to hierarchy mode."""
        runner = CliRunner()

        with patch('phonegang.cli.DeviceManager') as mock_manager_class:
            mock_manager = Mock()
            mock_manager_class.return_value = mock_manager

            mock_device_info = Mock()
            mock_device_info.serial = "test_serial"
            mock_device_info.transport = None
            mock_manager.get_device.return_value = mock_device_info

            with patch('phonegang.cli.ADBDevice') as mock_device_class:
                mock_device = MagicMock()
                mock_device.__enter__ = Mock(return_value=mock_device)
                mock_device.__exit__ = Mock(return_value=None)
                mock_device.get_ui_dump.return_value = SAMPLE_XML
                mock_device_class.return_value = mock_device

                result = runner.invoke(cli, ['render'])

                assert result.exit_code == 0
                assert "UI HIERARCHY" in result.output


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
