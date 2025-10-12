# ABOUTME: Screen renderer that visualizes accessibility tree as text/ASCII
# ABOUTME: Converts UI hierarchy into readable text representation for debugging and automation

from typing import List, Optional
from phonegang.accessibility_tree import AccessibilityTree, Element
from lxml import etree


class ScreenRenderer:
    """Renders accessibility tree as text-based screen visualization."""

    def __init__(self, tree: AccessibilityTree):
        """
        Initialize renderer with accessibility tree.

        Args:
            tree: AccessibilityTree to render
        """
        self.tree = tree

    def render_hierarchy(self, show_bounds: bool = False, show_props: bool = True) -> str:
        """
        Render the UI hierarchy as an indented tree.

        Args:
            show_bounds: Whether to show element bounds
            show_props: Whether to show element properties (clickable, etc.)

        Returns:
            String representation of the UI hierarchy
        """
        output = []
        output.append("=" * 80)
        output.append("UI HIERARCHY")
        output.append("=" * 80)

        def render_node(node, indent: int = 0):
            prefix = "  " * indent

            # Get node attributes
            text = node.get('text', '')
            resource_id = node.get('resource-id', '')
            class_name = node.get('class', '').split('.')[-1]  # Just the class name
            content_desc = node.get('content-desc', '')
            clickable = node.get('clickable', 'false') == 'true'
            bounds = node.get('bounds', '')

            # Build the line
            parts = []

            # Class name
            parts.append(f"[{class_name}]")

            # Text or content description
            if text:
                parts.append(f'"{text}"')
            elif content_desc:
                parts.append(f'({content_desc})')

            # Resource ID
            if resource_id:
                id_short = resource_id.split('/')[-1]  # Just the ID part
                parts.append(f"#{id_short}")

            # Properties
            if show_props:
                props = []
                if clickable:
                    props.append("clickable")
                if node.get('scrollable', 'false') == 'true':
                    props.append("scrollable")
                if node.get('focused', 'false') == 'true':
                    props.append("focused")
                if props:
                    parts.append(f"({', '.join(props)})")

            # Bounds
            if show_bounds and bounds:
                parts.append(f"@ {bounds}")

            line = prefix + " ".join(parts)
            output.append(line)

            # Recurse for children
            for child in node:
                render_node(child, indent + 1)

        # Start rendering from root
        for child in self.tree.root:
            render_node(child)

        return "\n".join(output)

    def render_clickable_map(self) -> str:
        """
        Render a map of all clickable elements.

        Returns:
            String showing all clickable elements with their locations
        """
        output = []
        output.append("=" * 80)
        output.append("CLICKABLE ELEMENTS")
        output.append("=" * 80)

        clickable = self.tree.find_clickable()

        if not clickable:
            output.append("No clickable elements found.")
            return "\n".join(output)

        for i, elem in enumerate(clickable, 1):
            # Build element description
            desc_parts = []
            if elem.text:
                desc_parts.append(f'Text: "{elem.text}"')
            if elem.resource_id:
                id_short = elem.resource_id.split('/')[-1]
                desc_parts.append(f'ID: {id_short}')
            if elem.content_desc:
                desc_parts.append(f'Desc: "{elem.content_desc}"')

            desc = " | ".join(desc_parts) if desc_parts else elem.class_name

            # Get center position
            cx, cy = elem.center

            output.append(f"{i:2d}. [{elem.class_name.split('.')[-1]}] {desc}")
            output.append(f"    Position: ({cx}, {cy}) | Bounds: {elem.bounds}")
            output.append("")

        return "\n".join(output)

    def render_compact(self) -> str:
        """
        Render a compact view showing only important elements.

        Returns:
            Compact string representation
        """
        output = []
        output.append("=" * 80)
        output.append("SCREEN OVERVIEW")
        output.append("=" * 80)

        # Show screen info
        info = {
            "total_elements": len(self.tree.elements),
            "clickable": len(self.tree.find_clickable()),
            "scrollable": len(self.tree.find_scrollable()),
        }

        output.append(f"Elements: {info['total_elements']} total, "
                     f"{info['clickable']} clickable, {info['scrollable']} scrollable")
        output.append("")

        # Show elements with text
        output.append("TEXT ELEMENTS:")
        text_elements = [e for e in self.tree.elements if e.text]
        for elem in text_elements[:20]:  # Limit to 20
            marker = "→" if elem.clickable else " "
            output.append(f"  {marker} {elem.text[:60]}")

        if len(text_elements) > 20:
            output.append(f"  ... and {len(text_elements) - 20} more")

        return "\n".join(output)

    def render_spatial(self, width: int = 80, height: int = 40) -> str:
        """
        Render a spatial ASCII representation of the screen.

        Args:
            width: Character width of output
            height: Character height of output

        Returns:
            ASCII art representation of screen layout
        """
        # This is a simplified spatial renderer
        output = []
        output.append("=" * width)
        output.append("SPATIAL LAYOUT (approximate)")
        output.append("=" * width)

        # Get screen dimensions from elements
        max_x = max(e.parse_bounds()[2] for e in self.tree.elements if e.bounds)
        max_y = max(e.parse_bounds()[3] for e in self.tree.elements if e.bounds)

        # Create grid
        grid = [[' ' for _ in range(width)] for _ in range(height)]

        # Map elements to grid
        for elem in self.tree.elements:
            if not elem.clickable and not elem.text:
                continue

            try:
                x1, y1, x2, y2 = elem.parse_bounds()

                # Map to grid coordinates
                gx1 = int((x1 / max_x) * (width - 1))
                gy1 = int((y1 / max_y) * (height - 1))
                gx2 = int((x2 / max_x) * (width - 1))
                gy2 = int((y2 / max_y) * (height - 1))

                # Draw element
                char = '█' if elem.clickable else '░'
                if elem.text:
                    # Try to place text
                    text = elem.text[:gx2-gx1].ljust(gx2-gx1)
                    for i, c in enumerate(text):
                        if gx1 + i < width and gy1 < height:
                            grid[gy1][gx1 + i] = c
                else:
                    # Draw box
                    for y in range(gy1, min(gy2 + 1, height)):
                        for x in range(gx1, min(gx2 + 1, width)):
                            if x < width and y < height:
                                grid[y][x] = char
            except:
                continue

        for row in grid:
            output.append(''.join(row))

        return "\n".join(output)


def render_screen(tree: AccessibilityTree, mode: str = "hierarchy") -> str:
    """
    Render the accessibility tree in various formats.

    Args:
        tree: AccessibilityTree to render
        mode: Rendering mode ('hierarchy', 'clickable', 'compact', 'spatial')

    Returns:
        Rendered string
    """
    renderer = ScreenRenderer(tree)

    if mode == "hierarchy":
        return renderer.render_hierarchy()
    elif mode == "clickable":
        return renderer.render_clickable_map()
    elif mode == "compact":
        return renderer.render_compact()
    elif mode == "spatial":
        return renderer.render_spatial()
    else:
        raise ValueError(f"Unknown render mode: {mode}")
