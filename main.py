# ABOUTME: Example script demonstrating phonegang usage
# ABOUTME: Shows basic device control and UI automation patterns

import argparse
import sys
from phonegang import DeviceManager, ADBDevice, DeviceController


def main():
    """Example phonegang automation script."""
    parser = argparse.ArgumentParser(description='phonegang - Android Device Control Suite')
    parser.add_argument('-s', '--serial', help='Device serial number')
    parser.add_argument('-d', '--device', type=int, help='Device index (0-based)')
    args = parser.parse_args()

    print("🤖 phonegang - Android Device Control Suite")
    print("=" * 50)

    # Initialize device manager
    manager = DeviceManager()

    # List all connected devices
    print("\n📱 Scanning for connected devices...")
    devices = manager.list_devices()

    if not devices:
        print("❌ No devices found. Please connect an Android device with USB debugging enabled.")
        return

    print(f"\n✅ Found {len(devices)} device(s):")
    for i, device in enumerate(devices):
        print(f"  [{i}] {device}")

    # Get the device based on arguments
    try:
        if args.serial:
            device_info = manager.get_device(serial=args.serial)
        elif args.device is not None:
            device_info = manager.select_device(args.device)
        elif len(devices) == 1:
            device_info = manager.get_device()
        else:
            print("\n⚠️  Multiple devices detected. Please specify which device to use:")
            print("   Use -s SERIAL or -d INDEX")
            print(f"   Example: {sys.argv[0]} -d 0")
            return
    except (ValueError, IndexError) as e:
        print(f"\n❌ Error: {e}")
        return

    print(f"\n🔗 Connecting to: {device_info.serial}")

    # Connect to device and perform operations
    # Use the transport if available, otherwise fall back to serial
    device_param = device_info.transport if device_info.transport else device_info.serial
    with ADBDevice(device_param) as device:
        device.connect()
        controller = DeviceController(device)

        # Get device info
        width, height = device.get_screen_size()
        current_app = device.get_current_package()

        print(f"\n📊 Device Information:")
        print(f"  Screen Size: {width}x{height}")
        print(f"  Current App: {current_app}")

        # Get UI tree info
        info = controller.get_current_screen_info()
        print(f"\n🌳 UI Tree Information:")
        print(f"  Total Elements: {info['total_elements']}")
        print(f"  Clickable Elements: {info['clickable_elements']}")
        print(f"  Scrollable Elements: {info['scrollable_elements']}")

        print("\n✨ Example complete! Use the phonegang CLI or API to automate your device.")


if __name__ == "__main__":
    main()
