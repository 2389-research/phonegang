# Phonegang

A powerful suite of tools for controlling Android phones over USB using accessibility trees. Built with Python, phonegang provides both a CLI and programmatic API for automating Android device interactions.

## Features

- **Accessibility Tree-based UI Automation**: Robust element finding using semantic properties (text, resource-id, content-desc) instead of fragile pixel coordinates
- **Multiple Device Support**: Manage and control multiple connected Android devices
- **Comprehensive CLI**: Rich command-line interface for common operations
- **Python API**: Full programmatic access for building custom automation scripts
- **Rich Element Finding**: Find UI elements by text, resource ID, content description, class name, or custom predicates
- **High-level Operations**: Tap, swipe, scroll, type text, and more
- **Screenshot Capture**: Take and save screenshots programmatically
- **App Management**: Install, uninstall, start, and stop apps
- **Screen Mirroring**: Real-time screen mirroring with scrcpy integration for visual feedback

## Installation

### Prerequisites

- Python 3.10 or higher
- Android device with USB debugging enabled
- ADB (Android Debug Bridge) - typically installed with Android SDK
- [scrcpy](https://github.com/Genymobile/scrcpy) (optional, for screen mirroring)

### Install with uv (recommended)

```bash
git clone <repo-url>
cd phonegang
uv sync
```

### Install with pip

```bash
pip install -e .
```

## MCP Server & HTTP API

Phonegang includes multiple interfaces for automation:

### MCP Server (stdio)
MCP server for Claude Code integration. See [docs/mcp-setup.md](docs/mcp-setup.md) for setup.

```bash
phonegang-mcp
```

### HTTP API (REST + SSE)
RESTful API with Server-Sent Events for remote control and integration:

```bash
phonegang api --port 8000
```

Features:
- RESTful endpoints for all phone operations
- Server-Sent Events (SSE) for real-time screen updates
- CORS enabled for web clients
- Multi-device support

With these interfaces, you can:
- Ask Claude to explore your phone's UI
- Describe automation tasks in natural language
- Have Claude execute multi-step phone interactions
- Debug automation scripts with Claude's help
- Build web apps that control phones remotely

## Quick Start

### CLI Usage

#### List Connected Devices

```bash
phonegang devices
```

#### Get Device Info

```bash
phonegang info
phonegang info -s <serial>  # for specific device
```

#### Dump UI Tree

```bash
phonegang dump-ui
```

#### Tap Elements

```bash
# Tap by text
phonegang tap-text "Login"

# Tap by resource ID
phonegang tap-id "com.example:id/button"

# Tap at coordinates
phonegang tap 500 1000
```

#### Type Text

```bash
phonegang type "Hello World"
```

#### Take Screenshot

```bash
phonegang screenshot
phonegang screenshot /path/to/save.png
```

#### App Management

```bash
# Start an app
phonegang start-app com.example.app

# Stop an app
phonegang stop-app com.example.app
```

#### Navigation

```bash
phonegang back
phonegang home
```

#### Scrolling

```bash
phonegang scroll-to "Settings"
```

#### Screen Mirroring & Remote Control

```bash
# Web-based viewer (for visual control)
phonegang viewer
# Opens web interface at http://localhost:5000
# Shows device selector, then full screen viewer with controls

# HTTP API (for programmatic control)
phonegang api --port 8000
# RESTful API with SSE streaming
# Documentation at http://localhost:8000/

# Local mirroring with scrcpy (requires GUI)
phonegang mirror --show-touches --always-on-top

# Check scrcpy mirroring status
phonegang mirror-status

# Stop scrcpy mirroring
phonegang stop-mirror
```

### Python API Usage

#### Basic Device Control

```python
from phonegang import DeviceManager, ADBDevice, DeviceController

# Get a device
manager = DeviceManager()
device_info = manager.get_device()  # Gets the only device if one is connected

# Connect to device
with ADBDevice(device_info.serial) as device:
    device.connect()

    # Take a screenshot
    screenshot_path = device.take_screenshot()

    # Press buttons
    device.press_home()
    device.press_back()

    # Type text
    device.type_text("Hello World")
```

#### UI Automation with Accessibility Tree

```python
from phonegang import DeviceManager, ADBDevice, DeviceController

manager = DeviceManager()
device_info = manager.get_device()

with ADBDevice(device_info.serial) as device:
    device.connect()
    controller = DeviceController(device)

    # Find and tap elements
    controller.find_and_tap(text="Login")
    controller.find_and_tap(resource_id="com.example:id/submit")

    # Fill text fields
    controller.fill_text_field("username@example.com", field_id="email")

    # Scroll to find elements
    element = controller.scroll_to_text("Settings")
    if element:
        controller.tap_element(element)

    # Wait for elements to appear
    element = controller.wait_for_text("Success", timeout=10)

    # Get screen info
    info = controller.get_current_screen_info()
    print(f"Total elements: {info['total_elements']}")
    print(f"Current package: {info['current_package']}")
```

#### Advanced Element Finding

```python
from phonegang import DeviceManager, ADBDevice, DeviceController

manager = DeviceManager()
device_info = manager.get_device()

with ADBDevice(device_info.serial) as device:
    device.connect()
    controller = DeviceController(device)

    # Refresh UI tree
    tree = controller.refresh_ui()

    # Find by various criteria
    buttons = tree.find_by_class("Button")
    login_elements = tree.find_by_text("Login", exact=True)
    clickable = tree.find_clickable()

    # Find with multiple criteria
    element = tree.find_one(
        text="Submit",
        clickable=True,
        class_name="Button"
    )

    # Custom filtering
    large_elements = tree.filter(
        lambda e: (e.parse_bounds()[2] - e.parse_bounds()[0]) > 500
    )

    # Access element properties
    for elem in buttons:
        print(f"Text: {elem.text}")
        print(f"Resource ID: {elem.resource_id}")
        print(f"Bounds: {elem.bounds}")
        print(f"Center: {elem.center}")
        print(f"Clickable: {elem.clickable}")
```

#### Screen Mirroring with scrcpy

```python
from phonegang.scrcpy_wrapper import ScrcpyManager, ScrcpyConfig

# Quick start with defaults
manager = ScrcpyManager()
process = manager.start()  # Starts mirroring the default device

# Configure mirroring options
config = ScrcpyConfig(
    serial="YOUR_DEVICE_SERIAL",
    max_size=1024,              # Limit screen dimension
    bit_rate="4M",              # Video quality
    max_fps=30,                 # Frame rate limit
    show_touches=True,          # Show touch points
    always_on_top=True,         # Keep window on top
    window_title="My Phone"
)
process = manager.start(config)

# Check if mirroring is running
if manager.is_running():
    print("Mirroring is active")

# Stop mirroring
manager.stop()

# Or stop all sessions
manager.stop_all()

# Convenience function
from phonegang.scrcpy_wrapper import mirror_device
mirror_device(max_size=1024, show_touches=True)
```

## Architecture

phonegang is built with a layered architecture:

1. **ADB Layer** (`adb_wrapper.py`): Low-level ADB operations using `adb-shell` library
2. **Accessibility Tree Parser** (`accessibility_tree.py`): Parses uiautomator XML dumps into queryable objects
3. **Device Controller** (`controller.py`): High-level automation combining ADB and accessibility tree
4. **CLI** (`cli.py`): Command-line interface built with Click

## Development

### Running Tests

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=phonegang

# Run specific test file
uv run pytest tests/test_accessibility_tree.py -v
```

### Project Structure

```
phonegang/
 phonegang/
    __init__.py
    device_manager.py      # Device discovery and management
    adb_wrapper.py          # ADB operations wrapper
    accessibility_tree.py   # UI tree parsing and element finding
    controller.py           # High-level device controller
    cli.py                  # Command-line interface
 tests/
    test_accessibility_tree.py  # Unit tests
    test_controller.py          # Integration tests
 pyproject.toml
 README.md
```

## Screen Mirroring

Phonegang provides two ways to view your phone screen:

### 1. Web Viewer (Recommended for Remote Access)

Perfect for remote servers or headless systems. Streams the phone screen to your browser:

```bash
# Start web viewer
phonegang viewer

# Custom port and FPS
phonegang viewer --port 8080 --fps 10

# Make accessible from other machines
phonegang viewer --host 0.0.0.0
```

Then open in your browser: `http://your-server-ip:5000`

**Features:**
- Works over SSH/remote connections
- Click to tap on screen
- Hardware buttons (Back, Home, Recents)
- Adjustable frame rate (1-30 FPS)
- Screenshot capture
- No additional software required

**Performance Tips:**
- Start with 5 FPS for responsive control
- Increase to 10-15 FPS for smoother video
- Lower FPS on slow connections

### 2. scrcpy Integration (Local Only)

For local machines with GUI, [scrcpy](https://github.com/Genymobile/scrcpy) provides high-performance mirroring:

```bash
# Install scrcpy first
brew install scrcpy  # macOS
apt install scrcpy   # Linux

# Start mirroring
phonegang mirror --show-touches --max-size 1024
```

**Common scrcpy Options:**
- `--max-size 1024` - Limit screen size
- `--bit-rate 4M` - Adjust video quality
- `--show-touches` - Show touch points
- `--always-on-top` - Keep window on top
- `--no-control` - Display only mode

## Troubleshooting

### Device Not Found

1. Ensure USB debugging is enabled on your Android device
2. Check that ADB recognizes the device: `adb devices`
3. Accept the USB debugging prompt on your device
4. Try reconnecting the device

### Permission Denied

Make sure you've accepted the USB debugging authorization on your device.

### Element Not Found

1. Use `phonegang dump-ui` to see the current UI tree
2. Check that you're using the correct text/resource-id
3. Try using partial matches or content-desc instead
4. Ensure the element is visible on screen (not scrolled off)

### Web Viewer Issues

If the web viewer doesn't work:

1. Check device is connected: `phonegang devices`
2. Ensure port is not in use: Try a different port with `--port 8080`
3. Check firewall settings if accessing remotely
4. Verify Flask is installed: `pip install flask`

### scrcpy Issues

If `phonegang mirror` fails:

1. Check scrcpy is installed: `scrcpy --version`
2. Test scrcpy directly: `scrcpy`
3. Ensure device is connected: `phonegang devices`
4. Check USB debugging is enabled
5. Try reducing quality: `phonegang mirror --max-size 800 --bit-rate 2M`

## Contributing

Contributions are welcome! Please ensure:

1. All tests pass: `uv run pytest`
2. Code follows project style
3. New features include tests
4. Documentation is updated

## License

[Add your license here]

## Credits

Built with:
- [adb-shell](https://github.com/JeffLIrion/adb_shell) - Pure Python ADB implementation
- [Click](https://click.palletsprojects.com/) - CLI framework
- [lxml](https://lxml.de/) - XML parsing
