# ABOUTME: Command-line interface for phonegang Android device control suite
# ABOUTME: Provides CLI commands for device management, UI interaction, and automation

import click
from phonegang.device_manager import DeviceManager
from phonegang.adb_wrapper import ADBDevice
from phonegang.controller import DeviceController
from phonegang.scrcpy_wrapper import ScrcpyManager, ScrcpyConfig
from phonegang.web_viewer import start_viewer
from phonegang.http_api import start_http_api
from phonegang.mcp_http import start_mcp_http_server


@click.group()
def cli():
    """phonegang - Android phone control suite using accessibility trees."""
    pass


@cli.command()
def devices():
    """List all connected Android devices."""
    manager = DeviceManager()
    device_list = manager.list_devices()

    if not device_list:
        click.echo("No devices connected.")
        return

    click.echo(f"Found {len(device_list)} device(s):")
    for i, device in enumerate(device_list):
        click.echo(f"  [{i}] {device}")


@cli.command()
@click.option("--serial", "-s", help="Device serial number (optional if only one device)")
def info(serial):
    """Get detailed information about a device."""
    manager = DeviceManager()

    try:
        device_info = manager.get_device(serial)
        click.echo(f"Device: {device_info}")

        with ADBDevice(device_info.serial) as device:
            device.connect()
            screen_size = device.get_screen_size()
            current_pkg = device.get_current_package()

            click.echo(f"Screen size: {screen_size[0]}x{screen_size[1]}")
            click.echo(f"Current package: {current_pkg}")

    except ValueError as e:
        click.echo(f"Error: {e}", err=True)
        return 1


@cli.command()
@click.option("--serial", "-s", help="Device serial number")
def dump_ui(serial):
    """Dump the current UI tree."""
    manager = DeviceManager()

    try:
        device_info = manager.get_device(serial)

        with ADBDevice(device_info.serial) as device:
            device.connect()
            controller = DeviceController(device)
            controller.print_current_ui()

    except ValueError as e:
        click.echo(f"Error: {e}", err=True)
        return 1


@cli.command()
@click.option("--serial", "-s", help="Device serial number")
@click.argument("text")
def tap_text(serial, text):
    """Tap an element containing the specified text."""
    manager = DeviceManager()

    try:
        device_info = manager.get_device(serial)

        with ADBDevice(device_info.serial) as device:
            device.connect()
            controller = DeviceController(device)

            if controller.find_and_tap(text=text):
                click.echo(f"✓ Tapped element with text: {text}")
            else:
                click.echo(f"✗ Element with text '{text}' not found", err=True)
                return 1

    except ValueError as e:
        click.echo(f"Error: {e}", err=True)
        return 1


@cli.command()
@click.option("--serial", "-s", help="Device serial number")
@click.argument("resource_id")
def tap_id(serial, resource_id):
    """Tap an element with the specified resource ID."""
    manager = DeviceManager()

    try:
        device_info = manager.get_device(serial)

        with ADBDevice(device_info.serial) as device:
            device.connect()
            controller = DeviceController(device)

            if controller.find_and_tap(resource_id=resource_id):
                click.echo(f"✓ Tapped element with ID: {resource_id}")
            else:
                click.echo(f"✗ Element with ID '{resource_id}' not found", err=True)
                return 1

    except ValueError as e:
        click.echo(f"Error: {e}", err=True)
        return 1


@cli.command()
@click.option("--serial", "-s", help="Device serial number")
@click.argument("x", type=int)
@click.argument("y", type=int)
def tap(serial, x, y):
    """Tap at specific coordinates."""
    manager = DeviceManager()

    try:
        device_info = manager.get_device(serial)

        with ADBDevice(device_info.serial) as device:
            device.connect()
            device.tap(x, y)
            click.echo(f"✓ Tapped at ({x}, {y})")

    except ValueError as e:
        click.echo(f"Error: {e}", err=True)
        return 1


@cli.command()
@click.option("--serial", "-s", help="Device serial number")
@click.argument("text")
def type(serial, text):
    """Type text on the device."""
    manager = DeviceManager()

    try:
        device_info = manager.get_device(serial)

        with ADBDevice(device_info.serial) as device:
            device.connect()
            device.type_text(text)
            click.echo(f"✓ Typed: {text}")

    except ValueError as e:
        click.echo(f"Error: {e}", err=True)
        return 1


@cli.command()
@click.option("--serial", "-s", help="Device serial number")
@click.argument("output_path", required=False)
def screenshot(serial, output_path):
    """Take a screenshot."""
    manager = DeviceManager()

    try:
        device_info = manager.get_device(serial)

        with ADBDevice(device_info.serial) as device:
            device.connect()
            saved_path = device.take_screenshot(output_path)
            click.echo(f"✓ Screenshot saved to: {saved_path}")

    except ValueError as e:
        click.echo(f"Error: {e}", err=True)
        return 1


@cli.command()
@click.option("--serial", "-s", help="Device serial number")
@click.argument("package")
@click.argument("activity", required=False)
def start_app(serial, package, activity):
    """Start an app by package name (and optionally activity)."""
    manager = DeviceManager()

    try:
        device_info = manager.get_device(serial)

        with ADBDevice(device_info.serial) as device:
            device.connect()
            device.start_app(package, activity)
            click.echo(f"✓ Started app: {package}")

    except ValueError as e:
        click.echo(f"Error: {e}", err=True)
        return 1


@cli.command()
@click.option("--serial", "-s", help="Device serial number")
@click.argument("package")
def stop_app(serial, package):
    """Force stop an app."""
    manager = DeviceManager()

    try:
        device_info = manager.get_device(serial)

        with ADBDevice(device_info.serial) as device:
            device.connect()
            device.stop_app(package)
            click.echo(f"✓ Stopped app: {package}")

    except ValueError as e:
        click.echo(f"Error: {e}", err=True)
        return 1


@cli.command()
@click.option("--serial", "-s", help="Device serial number")
def back(serial):
    """Press the back button."""
    manager = DeviceManager()

    try:
        device_info = manager.get_device(serial)

        with ADBDevice(device_info.serial) as device:
            device.connect()
            device.press_back()
            click.echo("✓ Pressed back button")

    except ValueError as e:
        click.echo(f"Error: {e}", err=True)
        return 1


@cli.command()
@click.option("--serial", "-s", help="Device serial number")
def home(serial):
    """Press the home button."""
    manager = DeviceManager()

    try:
        device_info = manager.get_device(serial)

        with ADBDevice(device_info.serial) as device:
            device.connect()
            device.press_home()
            click.echo("✓ Pressed home button")

    except ValueError as e:
        click.echo(f"Error: {e}", err=True)
        return 1


@cli.command()
@click.option("--serial", "-s", help="Device serial number")
@click.argument("text")
@click.option("--max-scrolls", "-m", default=10, help="Maximum number of scrolls")
def scroll_to(serial, text, max_scrolls):
    """Scroll until element with text is found."""
    manager = DeviceManager()

    try:
        device_info = manager.get_device(serial)

        with ADBDevice(device_info.serial) as device:
            device.connect()
            controller = DeviceController(device)

            element = controller.scroll_to_text(text, max_scrolls=max_scrolls)
            if element:
                click.echo(f"✓ Found element: {element}")
            else:
                click.echo(f"✗ Element with text '{text}' not found after {max_scrolls} scrolls", err=True)
                return 1

    except ValueError as e:
        click.echo(f"Error: {e}", err=True)
        return 1


@cli.command()
@click.option("--serial", "-s", help="Device serial number")
@click.option("--mode", "-m", default="hierarchy",
              type=click.Choice(["hierarchy", "clickable", "compact", "spatial"]),
              help="Rendering mode")
def render(serial, mode):
    """Render the screen accessibility tree in various formats."""
    manager = DeviceManager()

    try:
        device_info = manager.get_device(serial)
        device_param = device_info.transport if device_info.transport else device_info.serial

        with ADBDevice(device_param) as device:
            device.connect()
            controller = DeviceController(device)

            # Get the accessibility tree
            tree = controller.refresh_ui()

            # Render it in the specified mode
            output = tree.render(mode)
            click.echo(output)

    except ValueError as e:
        click.echo(f"Error: {e}", err=True)
        return 1


@cli.command()
@click.option("--serial", "-s", help="Device serial number")
@click.option("--max-size", type=int, help="Maximum screen dimension (e.g., 1024)")
@click.option("--bit-rate", help="Video bit rate (e.g., '2M', '8M')")
@click.option("--max-fps", type=int, help="Maximum frame rate")
@click.option("--window-title", help="Custom window title")
@click.option("--fullscreen", is_flag=True, help="Start in fullscreen mode")
@click.option("--always-on-top", is_flag=True, help="Keep window always on top")
@click.option("--show-touches", is_flag=True, help="Show physical touches")
@click.option("--turn-screen-off", is_flag=True, help="Turn device screen off while mirroring")
@click.option("--no-stay-awake", is_flag=True, help="Don't keep device awake")
@click.option("--no-control", is_flag=True, help="Disable device control (display only)")
def mirror(serial, max_size, bit_rate, max_fps, window_title, fullscreen,
           always_on_top, show_touches, turn_screen_off, no_stay_awake, no_control):
    """Start screen mirroring with scrcpy."""
    try:
        scrcpy_mgr = ScrcpyManager()
    except RuntimeError as e:
        click.echo(f"Error: {e}", err=True)
        click.echo("\nInstall scrcpy: https://github.com/Genymobile/scrcpy#get-the-app", err=True)
        return 1

    # Verify device exists if serial provided
    if serial:
        manager = DeviceManager()
        try:
            manager.get_device(serial)
        except ValueError as e:
            click.echo(f"Error: {e}", err=True)
            return 1

    # Check if already running
    if scrcpy_mgr.is_running(serial):
        click.echo(f"Screen mirroring already running for device {serial or 'default'}", err=True)
        return 1

    # Configure scrcpy
    config = ScrcpyConfig(
        serial=serial,
        max_size=max_size,
        bit_rate=bit_rate,
        max_fps=max_fps,
        window_title=window_title or f"phonegang - {serial or 'default'}",
        fullscreen=fullscreen,
        always_on_top=always_on_top,
        show_touches=show_touches,
        turn_screen_off=turn_screen_off,
        stay_awake=not no_stay_awake,
        no_control=no_control
    )

    try:
        scrcpy_mgr.start(config)
        device_name = serial or "default device"
        click.echo(f"✓ Screen mirroring started for {device_name}")
        click.echo("  (scrcpy window should appear - close window to stop mirroring)")
    except RuntimeError as e:
        click.echo(f"Error starting scrcpy: {e}", err=True)
        return 1


@cli.command()
@click.option("--serial", "-s", help="Device serial number")
@click.option("--all", "stop_all", is_flag=True, help="Stop all mirroring sessions")
def stop_mirror(serial, stop_all):
    """Stop screen mirroring."""
    try:
        scrcpy_mgr = ScrcpyManager()
    except RuntimeError:
        click.echo("scrcpy is not installed", err=True)
        return 1

    if stop_all:
        count = scrcpy_mgr.stop_all()
        if count > 0:
            click.echo(f"✓ Stopped {count} mirroring session(s)")
        else:
            click.echo("No mirroring sessions running")
        return

    if scrcpy_mgr.stop(serial):
        device_name = serial or "default device"
        click.echo(f"✓ Stopped mirroring for {device_name}")
    else:
        device_name = serial or "default device"
        click.echo(f"No mirroring session running for {device_name}", err=True)
        return 1


@cli.command()
def mirror_status():
    """Check status of screen mirroring sessions."""
    try:
        scrcpy_mgr = ScrcpyManager()
    except RuntimeError:
        click.echo("scrcpy is not installed", err=True)
        return 1

    sessions = scrcpy_mgr.get_running_sessions()

    if not sessions:
        click.echo("No mirroring sessions running")
        return

    click.echo(f"Active mirroring sessions: {len(sessions)}")
    for serial in sessions:
        click.echo(f"  • {serial}")


@cli.command()
@click.option("--host", default="0.0.0.0", help="Host to bind to (default: 0.0.0.0)")
@click.option("--port", "-p", default=5000, type=int, help="Port to listen on (default: 5000)")
@click.option("--fps", default=15, type=int, help="Frames per second (default: 15)")
def viewer(host, port, fps):
    """Start web-based phone viewer for all connected devices."""
    manager = DeviceManager()

    try:
        devices = manager.list_devices()
        if not devices:
            click.echo("No devices found. Connect a device and try again.", err=True)
            return 1

        click.echo(f"Found {len(devices)} device(s):")
        for device in devices:
            click.echo(f"  • {device.serial}")

        click.echo(f"\nStarting web viewer on http://{host if host != '0.0.0.0' else 'localhost'}:{port}")
        click.echo(f"Default streaming: {fps} FPS (adjustable per device)")
        click.echo("\nPress Ctrl+C to stop")

        start_viewer(host=host, port=port, fps=fps)

    except KeyboardInterrupt:
        click.echo("\n\nStopping viewer...")
    except Exception as e:
        click.echo(f"Error starting viewer: {e}", err=True)
        return 1


@cli.command()
@click.option("--host", default="0.0.0.0", help="Host to bind to (default: 0.0.0.0)")
@click.option("--port", "-p", default=8000, type=int, help="Port to listen on (default: 8000)")
def api(host, port):
    """Start HTTP API server for remote phone control (REST + SSE)."""
    manager = DeviceManager()

    try:
        devices = manager.list_devices()
        if not devices:
            click.echo("Warning: No devices found. Connect devices to control them.", err=True)

        if devices:
            click.echo(f"Found {len(devices)} device(s):")
            for device in devices:
                click.echo(f"  • {device.serial}")

        click.echo(f"\nStarting HTTP API on http://{host if host != '0.0.0.0' else 'localhost'}:{port}")
        click.echo(f"Documentation: http://{host if host != '0.0.0.0' else 'localhost'}:{port}/")
        click.echo(f"SSE Stream: http://{host if host != '0.0.0.0' else 'localhost'}:{port}/stream/screen")
        click.echo("\nPress Ctrl+C to stop")

        start_http_api(host=host, port=port)

    except KeyboardInterrupt:
        click.echo("\n\nStopping API server...")
    except Exception as e:
        click.echo(f"Error starting API server: {e}", err=True)
        return 1


@cli.command()
@click.option("--host", default="0.0.0.0", help="Host to bind to (default: 0.0.0.0)")
@click.option("--port", "-p", default=8080, type=int, help="Port to listen on (default: 8080)")
@click.option("--auth-token", help="Static Bearer token for authentication (optional)")
@click.option("--base-url", help="Base URL for OAuth metadata (e.g., http://example.com:8080)")
def mcp_http(host, port, auth_token, base_url):
    """Start MCP HTTP server with full OAuth 2.0 support."""
    manager = DeviceManager()

    try:
        devices = manager.list_devices()
        if not devices:
            click.echo("Warning: No devices found. Connect devices to control them.", err=True)

        if devices:
            click.echo(f"Found {len(devices)} device(s):")
            for device in devices:
                click.echo(f"  • {device.serial}")

        click.echo("\nPress Ctrl+C to stop\n")

        start_mcp_http_server(host=host, port=port, auth_token=auth_token, base_url=base_url)

    except KeyboardInterrupt:
        click.echo("\n\nStopping MCP HTTP server...")
    except Exception as e:
        click.echo(f"Error starting MCP HTTP server: {e}", err=True)
        return 1


if __name__ == "__main__":
    cli()
