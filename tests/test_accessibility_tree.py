# ABOUTME: Unit tests for accessibility tree parser
# ABOUTME: Tests XML parsing, element finding, and tree navigation functionality

import pytest
from phonegang.accessibility_tree import AccessibilityTree, Element


# Sample XML data for testing
SAMPLE_XML = """<?xml version="1.0" encoding="UTF-8"?>
<hierarchy rotation="0">
  <node index="0" text="" resource-id="" class="android.widget.FrameLayout" package="com.example.app"
        content-desc="" checkable="false" checked="false" clickable="false" enabled="true"
        focusable="false" focused="false" scrollable="false" long-clickable="false"
        password="false" selected="false" bounds="[0,0][1080,2340]">
    <node index="1" text="Settings" resource-id="com.example.app:id/title" class="android.widget.TextView"
          package="com.example.app" content-desc="Settings title" checkable="false" checked="false"
          clickable="false" enabled="true" focusable="false" focused="false" scrollable="false"
          long-clickable="false" password="false" selected="false" bounds="[40,100][520,180]"/>
    <node index="2" text="" resource-id="" class="android.widget.LinearLayout" package="com.example.app"
          content-desc="" checkable="false" checked="false" clickable="false" enabled="true"
          focusable="false" focused="false" scrollable="true" long-clickable="false"
          password="false" selected="false" bounds="[0,200][1080,2340]">
      <node index="3" text="Enable notifications" resource-id="com.example.app:id/notification_toggle"
            class="android.widget.Switch" package="com.example.app" content-desc="Notification toggle"
            checkable="true" checked="false" clickable="true" enabled="true" focusable="true"
            focused="false" scrollable="false" long-clickable="false" password="false"
            selected="false" bounds="[40,220][1040,320]"/>
      <node index="4" text="Save" resource-id="com.example.app:id/save_button"
            class="android.widget.Button" package="com.example.app" content-desc="Save settings"
            checkable="false" checked="false" clickable="true" enabled="true" focusable="true"
            focused="false" scrollable="false" long-clickable="false" password="false"
            selected="false" bounds="[400,2200][680,2300]"/>
    </node>
  </node>
</hierarchy>"""


class TestElement:
    """Test the Element dataclass."""

    def test_element_creation(self):
        """Test creating an Element with various attributes."""
        element = Element(
            index=0,
            text="Test",
            resource_id="com.test:id/button",
            class_name="android.widget.Button",
            package="com.test",
            content_desc="Test button",
            checkable=False,
            checked=False,
            clickable=True,
            enabled=True,
            focusable=True,
            focused=False,
            scrollable=False,
            long_clickable=False,
            password=False,
            selected=False,
            bounds="[100,200][300,400]"
        )

        assert element.text == "Test"
        assert element.clickable is True
        assert element.resource_id == "com.test:id/button"

    def test_parse_bounds(self):
        """Test parsing bounds string into coordinates."""
        element = Element(
            index=0, text="", resource_id="", class_name="", package="",
            content_desc="", checkable=False, checked=False, clickable=False,
            enabled=True, focusable=False, focused=False, scrollable=False,
            long_clickable=False, password=False, selected=False,
            bounds="[100,200][300,400]"
        )

        x1, y1, x2, y2 = element.parse_bounds()
        assert x1 == 100
        assert y1 == 200
        assert x2 == 300
        assert y2 == 400

    def test_center_property(self):
        """Test calculating center coordinates of element."""
        element = Element(
            index=0, text="", resource_id="", class_name="", package="",
            content_desc="", checkable=False, checked=False, clickable=False,
            enabled=True, focusable=False, focused=False, scrollable=False,
            long_clickable=False, password=False, selected=False,
            bounds="[100,200][300,400]"
        )

        center_x, center_y = element.center
        assert center_x == 200  # (100 + 300) / 2
        assert center_y == 300  # (200 + 400) / 2


class TestAccessibilityTree:
    """Test the AccessibilityTree parser."""

    def test_parse_xml(self):
        """Test parsing XML content into accessibility tree."""
        tree = AccessibilityTree(SAMPLE_XML)
        assert tree is not None
        assert len(tree.elements) > 0

    def test_parse_elements_count(self):
        """Test that all elements are parsed correctly."""
        tree = AccessibilityTree(SAMPLE_XML)
        # Should have: FrameLayout, TextView, LinearLayout, Switch, Button = 5 elements
        assert len(tree.elements) == 5

    def test_find_by_text_exact(self):
        """Test finding elements by exact text match."""
        tree = AccessibilityTree(SAMPLE_XML)
        results = tree.find_by_text("Settings", exact=True)

        assert len(results) == 1
        assert results[0].text == "Settings"
        assert results[0].resource_id == "com.example.app:id/title"

    def test_find_by_text_substring(self):
        """Test finding elements by text substring."""
        tree = AccessibilityTree(SAMPLE_XML)
        results = tree.find_by_text("notification")

        assert len(results) == 1
        assert "notification" in results[0].text.lower()

    def test_find_by_resource_id(self):
        """Test finding elements by resource ID."""
        tree = AccessibilityTree(SAMPLE_XML)
        results = tree.find_by_resource_id("save_button")

        assert len(results) == 1
        assert results[0].text == "Save"
        assert "save_button" in results[0].resource_id

    def test_find_by_content_desc(self):
        """Test finding elements by content description."""
        tree = AccessibilityTree(SAMPLE_XML)
        results = tree.find_by_content_desc("Settings title", exact=True)

        assert len(results) == 1
        assert results[0].content_desc == "Settings title"

    def test_find_by_class(self):
        """Test finding elements by class name."""
        tree = AccessibilityTree(SAMPLE_XML)
        results = tree.find_by_class("Button")

        assert len(results) == 1
        assert results[0].text == "Save"
        assert "Button" in results[0].class_name

    def test_find_clickable(self):
        """Test finding all clickable elements."""
        tree = AccessibilityTree(SAMPLE_XML)
        clickable = tree.find_clickable()

        assert len(clickable) == 2  # Switch and Button are clickable
        texts = [e.text for e in clickable]
        assert "Enable notifications" in texts
        assert "Save" in texts

    def test_find_scrollable(self):
        """Test finding all scrollable elements."""
        tree = AccessibilityTree(SAMPLE_XML)
        scrollable = tree.find_scrollable()

        assert len(scrollable) == 1
        assert scrollable[0].class_name == "android.widget.LinearLayout"

    def test_find_one_with_multiple_criteria(self):
        """Test finding a single element with multiple criteria."""
        tree = AccessibilityTree(SAMPLE_XML)
        element = tree.find_one(
            text="Save",
            clickable=True,
            class_name="Button"
        )

        assert element is not None
        assert element.text == "Save"
        assert element.clickable is True
        assert "Button" in element.class_name

    def test_find_one_no_match(self):
        """Test that find_one returns None when no match found."""
        tree = AccessibilityTree(SAMPLE_XML)
        element = tree.find_one(text="Nonexistent")

        assert element is None

    def test_find_all_with_criteria(self):
        """Test finding all elements matching criteria."""
        tree = AccessibilityTree(SAMPLE_XML)
        results = tree.find_all(clickable=True)

        assert len(results) == 2

    def test_filter_with_predicate(self):
        """Test filtering elements with custom predicate."""
        tree = AccessibilityTree(SAMPLE_XML)

        # Find elements with bounds height > 100
        def height_filter(elem: Element) -> bool:
            x1, y1, x2, y2 = elem.parse_bounds()
            height = y2 - y1
            return height > 100

        results = tree.filter(height_filter)

        assert len(results) > 0
        # FrameLayout and LinearLayout should match
        for elem in results:
            x1, y1, x2, y2 = elem.parse_bounds()
            assert (y2 - y1) > 100

    def test_element_properties(self):
        """Test that element boolean properties are parsed correctly."""
        tree = AccessibilityTree(SAMPLE_XML)

        # Find the Switch element
        switch = tree.find_by_class("Switch")[0]

        assert switch.checkable is True
        assert switch.checked is False
        assert switch.clickable is True
        assert switch.enabled is True
        assert switch.focusable is True

    def test_empty_xml(self):
        """Test handling of minimal XML."""
        minimal_xml = '<?xml version="1.0" encoding="UTF-8"?><hierarchy rotation="0"></hierarchy>'
        tree = AccessibilityTree(minimal_xml)

        assert len(tree.elements) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
