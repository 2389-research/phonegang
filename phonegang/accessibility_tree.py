# ABOUTME: Accessibility tree parser for Android UI automation
# ABOUTME: Parses uiautomator XML dumps and provides element finding and interaction capabilities

from typing import List, Optional, Dict, Any, Callable
from lxml import etree
from dataclasses import dataclass
import re


@dataclass
class Element:
    """Represents a UI element from the accessibility tree."""

    index: int
    text: str
    resource_id: str
    class_name: str
    package: str
    content_desc: str
    checkable: bool
    checked: bool
    clickable: bool
    enabled: bool
    focusable: bool
    focused: bool
    scrollable: bool
    long_clickable: bool
    password: bool
    selected: bool
    bounds: str  # Format: "[x1,y1][x2,y2]"

    @property
    def center(self) -> tuple[int, int]:
        """Get the center coordinates of the element."""
        x1, y1, x2, y2 = self.parse_bounds()
        center_x = (x1 + x2) // 2
        center_y = (y1 + y2) // 2
        return center_x, center_y

    def parse_bounds(self) -> tuple[int, int, int, int]:
        """
        Parse bounds string into coordinates.

        Returns:
            Tuple of (x1, y1, x2, y2)
        """
        # Bounds format: "[x1,y1][x2,y2]"
        matches = re.findall(r'\[(\d+),(\d+)\]', self.bounds)
        if len(matches) != 2:
            raise ValueError(f"Invalid bounds format: {self.bounds}")

        x1, y1 = int(matches[0][0]), int(matches[0][1])
        x2, y2 = int(matches[1][0]), int(matches[1][1])
        return x1, y1, x2, y2

    def __repr__(self) -> str:
        return (
            f"Element(text='{self.text}', resource_id='{self.resource_id}', "
            f"class='{self.class_name}', clickable={self.clickable})"
        )


class AccessibilityTree:
    """Parses and queries Android accessibility tree from uiautomator XML dumps."""

    def __init__(self, xml_content: str):
        """
        Initialize accessibility tree from XML content.

        Args:
            xml_content: XML string from uiautomator dump
        """
        self.xml_content = xml_content
        self.root = etree.fromstring(xml_content.encode('utf-8'))
        self.elements: List[Element] = []
        self._parse_tree()

    def _parse_tree(self):
        """Parse the XML tree and extract all elements."""
        self.elements = []

        def _parse_node(node, index: int = 0) -> int:
            """Recursively parse XML nodes into Element objects."""
            # Convert string boolean values
            def to_bool(val: str) -> bool:
                return val.lower() == 'true'

            element = Element(
                index=index,
                text=node.get('text', ''),
                resource_id=node.get('resource-id', ''),
                class_name=node.get('class', ''),
                package=node.get('package', ''),
                content_desc=node.get('content-desc', ''),
                checkable=to_bool(node.get('checkable', 'false')),
                checked=to_bool(node.get('checked', 'false')),
                clickable=to_bool(node.get('clickable', 'false')),
                enabled=to_bool(node.get('enabled', 'true')),
                focusable=to_bool(node.get('focusable', 'false')),
                focused=to_bool(node.get('focused', 'false')),
                scrollable=to_bool(node.get('scrollable', 'false')),
                long_clickable=to_bool(node.get('long-clickable', 'false')),
                password=to_bool(node.get('password', 'false')),
                selected=to_bool(node.get('selected', 'false')),
                bounds=node.get('bounds', '[0,0][0,0]'),
            )

            self.elements.append(element)
            current_index = index + 1

            # Parse children
            for child in node:
                current_index = _parse_node(child, current_index)

            return current_index

        # Start parsing from root
        for child in self.root:
            _parse_node(child)

    def find_by_text(self, text: str, exact: bool = False) -> List[Element]:
        """
        Find elements by text content.

        Args:
            text: Text to search for
            exact: If True, match exact text. If False, match substring.

        Returns:
            List of matching elements
        """
        if exact:
            return [e for e in self.elements if e.text == text]
        else:
            return [e for e in self.elements if text in e.text]

    def find_by_resource_id(self, resource_id: str) -> List[Element]:
        """
        Find elements by resource ID.

        Args:
            resource_id: Resource ID to search for (can be partial)

        Returns:
            List of matching elements
        """
        return [e for e in self.elements if resource_id in e.resource_id]

    def find_by_content_desc(self, content_desc: str, exact: bool = False) -> List[Element]:
        """
        Find elements by content description.

        Args:
            content_desc: Content description to search for
            exact: If True, match exact content-desc. If False, match substring.

        Returns:
            List of matching elements
        """
        if exact:
            return [e for e in self.elements if e.content_desc == content_desc]
        else:
            return [e for e in self.elements if content_desc in e.content_desc]

    def find_by_class(self, class_name: str) -> List[Element]:
        """
        Find elements by class name.

        Args:
            class_name: Class name to search for (can be partial, e.g., 'Button')

        Returns:
            List of matching elements
        """
        return [e for e in self.elements if class_name in e.class_name]

    def find_clickable(self) -> List[Element]:
        """
        Find all clickable elements.

        Returns:
            List of clickable elements
        """
        return [e for e in self.elements if e.clickable]

    def find_scrollable(self) -> List[Element]:
        """
        Find all scrollable elements.

        Returns:
            List of scrollable elements
        """
        return [e for e in self.elements if e.scrollable]

    def find_one(
        self,
        text: Optional[str] = None,
        resource_id: Optional[str] = None,
        content_desc: Optional[str] = None,
        class_name: Optional[str] = None,
        clickable: Optional[bool] = None,
    ) -> Optional[Element]:
        """
        Find a single element matching all specified criteria.

        Args:
            text: Text to match (substring)
            resource_id: Resource ID to match (substring)
            content_desc: Content description to match (substring)
            class_name: Class name to match (substring)
            clickable: Whether element should be clickable

        Returns:
            First matching element or None
        """
        for element in self.elements:
            if text is not None and text not in element.text:
                continue
            if resource_id is not None and resource_id not in element.resource_id:
                continue
            if content_desc is not None and content_desc not in element.content_desc:
                continue
            if class_name is not None and class_name not in element.class_name:
                continue
            if clickable is not None and element.clickable != clickable:
                continue

            return element

        return None

    def find_all(
        self,
        text: Optional[str] = None,
        resource_id: Optional[str] = None,
        content_desc: Optional[str] = None,
        class_name: Optional[str] = None,
        clickable: Optional[bool] = None,
    ) -> List[Element]:
        """
        Find all elements matching all specified criteria.

        Args:
            text: Text to match (substring)
            resource_id: Resource ID to match (substring)
            content_desc: Content description to match (substring)
            class_name: Class name to match (substring)
            clickable: Whether element should be clickable

        Returns:
            List of matching elements
        """
        results = []
        for element in self.elements:
            if text is not None and text not in element.text:
                continue
            if resource_id is not None and resource_id not in element.resource_id:
                continue
            if content_desc is not None and content_desc not in element.content_desc:
                continue
            if class_name is not None and class_name not in element.class_name:
                continue
            if clickable is not None and element.clickable != clickable:
                continue

            results.append(element)

        return results

    def filter(self, predicate: Callable[[Element], bool]) -> List[Element]:
        """
        Filter elements using a custom predicate function.

        Args:
            predicate: Function that takes an Element and returns bool

        Returns:
            List of elements where predicate returns True
        """
        return [e for e in self.elements if predicate(e)]

    def print_tree(self, indent: int = 0, node=None):
        """
        Print the accessibility tree in a human-readable format.

        Args:
            indent: Current indentation level (used internally)
            node: XML node to print (used internally)
        """
        if node is None:
            node = self.root

        for child in node:
            prefix = "  " * indent
            text = child.get('text', '')
            resource_id = child.get('resource-id', '')
            class_name = child.get('class', '')

            desc = []
            if text:
                desc.append(f"text='{text}'")
            if resource_id:
                desc.append(f"id='{resource_id}'")
            desc.append(f"class='{class_name}'")

            print(f"{prefix}{' '.join(desc)}")

            # Recurse for children
            self.print_tree(indent + 1, child)

    def render(self, mode: str = "hierarchy") -> str:
        """
        Render the accessibility tree in various formats.

        Args:
            mode: Rendering mode ('hierarchy', 'clickable', 'compact', 'spatial')

        Returns:
            Rendered string representation

        Example:
            >>> tree = controller.refresh_ui()
            >>> print(tree.render('clickable'))
        """
        from phonegang.renderer import render_screen
        return render_screen(self, mode)
