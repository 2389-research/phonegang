# ABOUTME: Integration tests for device controller
# ABOUTME: Tests high-level UI interaction and device control with mocked ADB

import pytest
from unittest.mock import Mock, MagicMock, patch
from phonegang.controller import DeviceController
from phonegang.adb_wrapper import ADBDevice


# Sample UI dump XML for testing
SAMPLE_UI_XML = """<?xml version="1.0" encoding="UTF-8"?>
<hierarchy rotation="0">
  <node index="0" text="" resource-id="" class="android.widget.FrameLayout" package="com.test"
        content-desc="" checkable="false" checked="false" clickable="false" enabled="true"
        focusable="false" focused="false" scrollable="false" long-clickable="false"
        password="false" selected="false" bounds="[0,0][1080,2340]">
    <node index="1" text="Login" resource-id="com.test:id/login_button" class="android.widget.Button"
          package="com.test" content-desc="Login button" checkable="false" checked="false"
          clickable="true" enabled="true" focusable="true" focused="false" scrollable="false"
          long-clickable="false" password="false" selected="false" bounds="[400,1000][680,1100]"/>
    <node index="2" text="" resource-id="com.test:id/scroll_view" class="android.widget.ScrollView"
          package="com.test" content-desc="" checkable="false" checked="false" clickable="false"
          enabled="true" focusable="false" focused="false" scrollable="true" long-clickable="false"
          password="false" selected="false" bounds="[0,200][1080,2000]">
      <node index="3" text="Settings" resource-id="com.test:id/settings_text" class="android.widget.TextView"
            package="com.test" content-desc="" checkable="false" checked="false" clickable="true"
            enabled="true" focusable="true" focused="false" scrollable="false" long-clickable="false"
            password="false" selected="false" bounds="[40,300][1040,400]"/>
    </node>
  </node>
</hierarchy>"""


class TestDeviceController:
    """Test the DeviceController class."""

    @pytest.fixture
    def mock_device(self):
        """Create a mock ADBDevice for testing."""
        device = Mock(spec=ADBDevice)
        device.get_ui_dump.return_value = SAMPLE_UI_XML
        device.get_screen_size.return_value = (1080, 2340)
        device.get_current_package.return_value = "com.test"
        return device

    @pytest.fixture
    def controller(self, mock_device):
        """Create a DeviceController with mocked device."""
        return DeviceController(mock_device)

    def test_refresh_ui(self, controller, mock_device):
        """Test refreshing the UI tree."""
        tree = controller.refresh_ui()

        assert tree is not None
        assert len(tree.elements) > 0
        mock_device.get_ui_dump.assert_called_once()

    def test_tree_property_lazy_load(self, controller, mock_device):
        """Test that tree property loads UI on first access."""
        # Access tree for the first time
        tree = controller.tree

        assert tree is not None
        mock_device.get_ui_dump.assert_called_once()

    def test_find_and_tap_success(self, controller, mock_device):
        """Test successfully finding and tapping an element."""
        result = controller.find_and_tap(text="Login")

        assert result is True
        # Should tap at center of button bounds [400,1000][680,1100]
        # Center: x=(400+680)/2=540, y=(1000+1100)/2=1050
        mock_device.tap.assert_called_once_with(540, 1050)

    def test_find_and_tap_by_resource_id(self, controller, mock_device):
        """Test finding and tapping by resource ID."""
        result = controller.find_and_tap(resource_id="login_button")

        assert result is True
        mock_device.tap.assert_called_once_with(540, 1050)

    def test_find_and_tap_not_found(self, controller, mock_device):
        """Test that find_and_tap returns False when element not found."""
        result = controller.find_and_tap(text="Nonexistent")

        assert result is False
        mock_device.tap.assert_not_called()

    def test_tap_element(self, controller, mock_device):
        """Test tapping a specific element."""
        controller.refresh_ui()
        elements = controller.tree.find_by_text("Login")
        element = elements[0]

        controller.tap_element(element)

        mock_device.tap.assert_called_once_with(540, 1050)

    def test_swipe_element_up(self, controller, mock_device):
        """Test swiping up on an element."""
        controller.refresh_ui()
        scroll_view = controller.tree.find_by_resource_id("scroll_view")[0]

        controller.swipe_element(scroll_view, direction="up")

        # Bounds: [0,200][1080,2000]
        # Center: x=540, y=1100
        # Distance: (2000-200)/2 = 900
        # Swipe from (540, 1100) to (540, 200)
        mock_device.swipe.assert_called_once_with(540, 1100, 540, 200)

    def test_swipe_element_down(self, controller, mock_device):
        """Test swiping down on an element."""
        controller.refresh_ui()
        scroll_view = controller.tree.find_by_resource_id("scroll_view")[0]

        controller.swipe_element(scroll_view, direction="down")

        # Swipe from (540, 1100) to (540, 2000)
        mock_device.swipe.assert_called_once_with(540, 1100, 540, 2000)

    def test_swipe_element_left(self, controller, mock_device):
        """Test swiping left on an element."""
        controller.refresh_ui()
        scroll_view = controller.tree.find_by_resource_id("scroll_view")[0]

        controller.swipe_element(scroll_view, direction="left")

        # Width: 1080, so distance = 540
        # Swipe from (540, 1100) to (0, 1100)
        mock_device.swipe.assert_called_once_with(540, 1100, 0, 1100)

    def test_swipe_element_custom_distance(self, controller, mock_device):
        """Test swiping with custom distance."""
        controller.refresh_ui()
        scroll_view = controller.tree.find_by_resource_id("scroll_view")[0]

        controller.swipe_element(scroll_view, direction="up", distance=500)

        # Swipe from (540, 1100) to (540, 600)
        mock_device.swipe.assert_called_once_with(540, 1100, 540, 600)

    def test_scroll_to_text_found_immediately(self, controller, mock_device):
        """Test scroll_to_text when element is already visible."""
        element = controller.scroll_to_text("Settings")

        assert element is not None
        assert element.text == "Settings"
        # Should only refresh once (no scrolling needed)
        assert mock_device.get_ui_dump.call_count == 1

    def test_scroll_to_text_not_found(self, controller, mock_device):
        """Test scroll_to_text when element is never found."""
        element = controller.scroll_to_text("Nonexistent", max_scrolls=2)

        assert element is None
        # Should try max_scrolls times
        assert mock_device.get_ui_dump.call_count == 2

    def test_fill_text_field_by_id(self, controller, mock_device):
        """Test filling a text field by resource ID."""
        # Add an EditText to the mock UI
        edit_xml = SAMPLE_UI_XML.replace(
            "</hierarchy>",
            '<node index="4" text="" resource-id="com.test:id/username" '
            'class="android.widget.EditText" package="com.test" content-desc="" '
            'checkable="false" checked="false" clickable="true" enabled="true" '
            'focusable="true" focused="false" scrollable="false" long-clickable="false" '
            'password="false" selected="false" bounds="[100,500][980,600]"/></hierarchy>'
        )
        mock_device.get_ui_dump.return_value = edit_xml

        controller.fill_text_field("testuser", field_id="username")

        # Should tap at center (540, 550) and then type
        mock_device.tap.assert_called_once_with(540, 550)
        mock_device.type_text.assert_called_once_with("testuser")

    def test_get_current_screen_info(self, controller, mock_device):
        """Test getting current screen information."""
        info = controller.get_current_screen_info()

        assert info["total_elements"] == 4
        assert info["clickable_elements"] == 2  # Login button and Settings text
        assert info["scrollable_elements"] == 1  # ScrollView
        assert info["current_package"] == "com.test"

    def test_wait_for_text_found(self, controller, mock_device):
        """Test waiting for text that appears."""
        import time

        # Simulate text appearing after first check
        call_count = [0]

        def ui_dump_side_effect():
            call_count[0] += 1
            if call_count[0] == 1:
                # First call: element not present
                return SAMPLE_UI_XML.replace("Settings", "Loading")
            else:
                # Subsequent calls: element appears
                return SAMPLE_UI_XML

        mock_device.get_ui_dump.side_effect = ui_dump_side_effect

        element = controller.wait_for_text("Settings", timeout=2, refresh_interval=0.1)

        assert element is not None
        assert element.text == "Settings"

    def test_wait_for_text_timeout(self, controller, mock_device):
        """Test waiting for text that never appears."""
        element = controller.wait_for_text("Nonexistent", timeout=0.5, refresh_interval=0.1)

        assert element is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
