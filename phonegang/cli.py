# ABOUTME: Command-line interface for phonegang Android device control suite
# ABOUTME: Provides CLI commands for device management, UI interaction, and automation

import click
from phonegang.device_manager import DeviceManager
from phonegang.adb_wrapper import ADBDevice
from phonegang.controller import DeviceController


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


if __name__ == "__main__":
    cli()
