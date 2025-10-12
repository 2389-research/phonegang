# ABOUTME: High-level device controller combining ADB and accessibility tree operations
# ABOUTME: Provides convenient methods for finding and interacting with UI elements

from typing import Optional, List
from phonegang.adb_wrapper import ADBDevice
from phonegang.accessibility_tree import AccessibilityTree, Element


class DeviceController:
    """High-level controller for Android device automation using accessibility tree."""

    def __init__(self, device: ADBDevice):
        """
        Initialize device controller.

        Args:
            device: Connected ADBDevice instance
        """
        self.device = device
        self._tree: Optional[AccessibilityTree] = None

    def refresh_ui(self) -> AccessibilityTree:
        """
        Refresh the UI hierarchy by dumping the current screen.

        Returns:
            Updated AccessibilityTree instance
        """
        xml_content = self.device.get_ui_dump()
        self._tree = AccessibilityTree(xml_content)
        return self._tree

    @property
    def tree(self) -> AccessibilityTree:
        """
        Get the current accessibility tree, refreshing if not available.

        Returns:
            Current AccessibilityTree instance
        """
        if self._tree is None:
            self.refresh_ui()
        return self._tree

    def find_and_tap(
        self,
        text: Optional[str] = None,
        resource_id: Optional[str] = None,
        content_desc: Optional[str] = None,
        class_name: Optional[str] = None,
        refresh: bool = True,
    ) -> bool:
        """
        Find an element and tap it.

        Args:
            text: Text to match (substring)
            resource_id: Resource ID to match (substring)
            content_desc: Content description to match (substring)
            class_name: Class name to match (substring)
            refresh: Whether to refresh UI before searching

        Returns:
            True if element found and tapped, False otherwise
        """
        if refresh:
            self.refresh_ui()

        element = self.tree.find_one(
            text=text,
            resource_id=resource_id,
            content_desc=content_desc,
            class_name=class_name,
            clickable=True,
        )

        if element:
            x, y = element.center
            self.device.tap(x, y)
            return True

        return False

    def tap_element(self, element: Element):
        """
        Tap a specific element.

        Args:
            element: Element to tap
        """
        x, y = element.center
        self.device.tap(x, y)

    def swipe_element(
        self,
        element: Element,
        direction: str = "up",
        distance: Optional[int] = None,
    ):
        """
        Swipe on an element in a given direction.

        Args:
            element: Element to swipe on
            direction: Direction to swipe ('up', 'down', 'left', 'right')
            distance: Swipe distance in pixels (default: half element size)
        """
        x1, y1, x2, y2 = element.parse_bounds()
        center_x = (x1 + x2) // 2
        center_y = (y1 + y2) // 2

        if distance is None:
            if direction in ['up', 'down']:
                distance = (y2 - y1) // 2
            else:
                distance = (x2 - x1) // 2

        if direction == 'up':
            self.device.swipe(center_x, center_y, center_x, center_y - distance)
        elif direction == 'down':
            self.device.swipe(center_x, center_y, center_x, center_y + distance)
        elif direction == 'left':
            self.device.swipe(center_x, center_y, center_x - distance, center_y)
        elif direction == 'right':
            self.device.swipe(center_x, center_y, center_x + distance, center_y)
        else:
            raise ValueError(f"Invalid direction: {direction}")

    def scroll_to_text(
        self,
        text: str,
        max_scrolls: int = 10,
        direction: str = "down",
    ) -> Optional[Element]:
        """
        Scroll until an element with given text is found.

        Args:
            text: Text to search for
            max_scrolls: Maximum number of scroll attempts
            direction: Scroll direction ('up' or 'down')

        Returns:
            Found element or None
        """
        for _ in range(max_scrolls):
            self.refresh_ui()
            elements = self.tree.find_by_text(text)
            if elements:
                return elements[0]

            # Find scrollable element and scroll
            scrollable = self.tree.find_scrollable()
            if scrollable:
                self.swipe_element(scrollable[0], direction=direction)
            else:
                # No scrollable element, try swiping screen
                width, height = self.device.get_screen_size()
                if direction == "down":
                    self.device.swipe(width // 2, height * 2 // 3, width // 2, height // 3)
                else:
                    self.device.swipe(width // 2, height // 3, width // 2, height * 2 // 3)

        return None

    def wait_for_text(
        self,
        text: str,
        timeout: int = 10,
        refresh_interval: float = 0.5,
    ) -> Optional[Element]:
        """
        Wait for an element with given text to appear.

        Args:
            text: Text to wait for
            timeout: Maximum wait time in seconds
            refresh_interval: How often to refresh UI in seconds

        Returns:
            Found element or None if timeout
        """
        import time

        start_time = time.time()
        while time.time() - start_time < timeout:
            self.refresh_ui()
            elements = self.tree.find_by_text(text)
            if elements:
                return elements[0]
            time.sleep(refresh_interval)

        return None

    def fill_text_field(
        self,
        text: str,
        field_id: Optional[str] = None,
        field_text: Optional[str] = None,
        tap_first: bool = True,
    ):
        """
        Fill a text field with given text.

        Args:
            text: Text to enter
            field_id: Resource ID of the text field
            field_text: Current text of the field (to identify it)
            tap_first: Whether to tap the field first to focus it
        """
        # Find the text field
        if field_id:
            elements = self.tree.find_by_resource_id(field_id)
        elif field_text:
            elements = self.tree.find_by_text(field_text)
        else:
            # Find EditText elements
            elements = self.tree.find_by_class("EditText")

        if not elements:
            raise ValueError("Text field not found")

        element = elements[0]

        if tap_first:
            self.tap_element(element)

        self.device.type_text(text)

    def print_current_ui(self):
        """Print the current UI tree in a human-readable format."""
        self.refresh_ui()
        self.tree.print_tree()

    def get_current_screen_info(self) -> dict:
        """
        Get information about the current screen.

        Returns:
            Dictionary with screen info including package, clickable elements count, etc.
        """
        self.refresh_ui()
        return {
            "total_elements": len(self.tree.elements),
            "clickable_elements": len(self.tree.find_clickable()),
            "scrollable_elements": len(self.tree.find_scrollable()),
            "current_package": self.device.get_current_package(),
        }
