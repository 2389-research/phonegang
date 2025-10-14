# ABOUTME: ADB wrapper providing high-level operations for Android device control
# ABOUTME: Handles UI dumps, input simulation, app management, and screen operations

from typing import Optional, Tuple, List, Union
from adb_shell.adb_device import AdbDevice as BaseAdbDevice, AdbDeviceUsb, UsbTransport
from adb_shell.auth.sign_pythonrsa import PythonRSASigner
from pathlib import Path
import tempfile


class ADBDevice:
    """High-level wrapper around ADB operations for Android device control."""

    def __init__(self, transport_or_serial: Union[UsbTransport, str], rsa_keys: Optional[List[PythonRSASigner]] = None):
        """
        Initialize ADB device connection.

        Args:
            transport_or_serial: UsbTransport object or device serial number string
            rsa_keys: Optional list of RSA signers for authentication
        """
        if isinstance(transport_or_serial, str):
            # Legacy support: if given a serial string, use AdbDeviceUsb
            from phonegang.auth import get_signers
            serial = transport_or_serial
            self.serial = serial

            # AdbDeviceUsb will find the device by serial
            self._device = AdbDeviceUsb(serial=serial)

            # Load default keys if not provided
            if rsa_keys is None:
                rsa_keys = get_signers()
        else:
            # New way: use BaseAdbDevice with UsbTransport directly
            from phonegang.auth import get_signers
            self._device = BaseAdbDevice(transport_or_serial)
            self.serial = transport_or_serial.serial_number

            # Load default keys if not provided
            if rsa_keys is None:
                rsa_keys = get_signers()

        self._rsa_keys = rsa_keys or []
        self._connected = False

    def connect(self):
        """Establish connection to the device."""
        if not self._connected:
            self._device.connect(rsa_keys=self._rsa_keys, auth_timeout_s=10)
            self._connected = True

    def disconnect(self):
        """Close connection to the device."""
        if self._connected:
            self._device.close()
            self._connected = False

    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.disconnect()

    def shell(self, command: str) -> str:
        """
        Execute a shell command on the device.

        Args:
            command: Shell command to execute

        Returns:
            Command output as string
        """
        if not self._connected:
            raise RuntimeError("Device not connected. Call connect() first or use context manager.")

        return self._device.shell(command)

    def get_ui_dump(self) -> str:
        """
        Get the current UI hierarchy as XML using uiautomator.

        Returns:
            XML string of the UI hierarchy
        """
        # Dump UI to device
        self.shell("uiautomator dump /sdcard/window_dump.xml")

        # Pull the dump
        xml_content = self.shell("cat /sdcard/window_dump.xml")

        # Clean up
        self.shell("rm /sdcard/window_dump.xml")

        return xml_content

    def tap(self, x: int, y: int):
        """
        Simulate a tap at the given coordinates.

        Args:
            x: X coordinate
            y: Y coordinate
        """
        self.shell(f"input tap {x} {y}")

    def swipe(self, x1: int, y1: int, x2: int, y2: int, duration: int = 300):
        """
        Simulate a swipe gesture.

        Args:
            x1: Start X coordinate
            y1: Start Y coordinate
            x2: End X coordinate
            y2: End Y coordinate
            duration: Swipe duration in milliseconds
        """
        self.shell(f"input swipe {x1} {y1} {x2} {y2} {duration}")

    def type_text(self, text: str):
        """
        Type text into the currently focused input field.

        Args:
            text: Text to type (spaces will be replaced with %s)
        """
        # ADB input text command requires spaces to be escaped as %s
        escaped_text = text.replace(" ", "%s")
        self.shell(f"input text {escaped_text}")

    def press_key(self, keycode: str):
        """
        Press a key on the device.

        Args:
            keycode: Android keycode (e.g., 'KEYCODE_HOME', 'KEYCODE_BACK', or number)
        """
        self.shell(f"input keyevent {keycode}")

    def press_back(self):
        """Press the back button."""
        self.press_key("KEYCODE_BACK")

    def press_home(self):
        """Press the home button."""
        self.press_key("KEYCODE_HOME")

    def get_screen_size(self) -> Tuple[int, int]:
        """
        Get the device screen dimensions.

        Returns:
            Tuple of (width, height)
        """
        output = self.shell("wm size")
        # Output format: "Physical size: 1080x2340"
        size_str = output.strip().split(":")[-1].strip()
        width, height = map(int, size_str.split("x"))
        return width, height

    def take_screenshot(self, output_path: Optional[str] = None) -> str:
        """
        Take a screenshot and save it.

        Args:
            output_path: Local path to save screenshot. If None, saves to temp file.

        Returns:
            Path to the saved screenshot
        """
        device_path = "/sdcard/screenshot.png"

        # Take screenshot on device
        self.shell(f"screencap -p {device_path}")

        # Determine output path
        if output_path is None:
            output_path = tempfile.mktemp(suffix=".png", prefix="phonegang_")

        # Pull screenshot using proper binary transfer
        self._device.pull(device_path, output_path)

        # Clean up device
        self.shell(f"rm {device_path}")

        return output_path

    def start_app(self, package: str, activity: Optional[str] = None):
        """
        Start an app on the device.

        Args:
            package: Package name (e.g., 'com.android.settings')
            activity: Activity name (optional). If None, launches main activity.
        """
        if activity:
            self.shell(f"am start -n {package}/{activity}")
        else:
            self.shell(f"monkey -p {package} 1")

    def stop_app(self, package: str):
        """
        Force stop an app.

        Args:
            package: Package name to stop
        """
        self.shell(f"am force-stop {package}")

    def install_app(self, apk_path: str):
        """
        Install an APK on the device.

        Args:
            apk_path: Local path to APK file
        """
        # This requires push functionality which adb-shell supports
        with open(apk_path, "rb") as f:
            apk_data = f.read()

        device_path = f"/sdcard/{Path(apk_path).name}"
        self._device.push(apk_data, device_path)

        # Install from device storage
        result = self.shell(f"pm install -r {device_path}")

        # Clean up
        self.shell(f"rm {device_path}")

        if "Success" not in result:
            raise RuntimeError(f"Failed to install APK: {result}")

    def uninstall_app(self, package: str):
        """
        Uninstall an app from the device.

        Args:
            package: Package name to uninstall
        """
        result = self.shell(f"pm uninstall {package}")
        if "Success" not in result:
            raise RuntimeError(f"Failed to uninstall {package}: {result}")

    def get_current_package(self) -> str:
        """
        Get the package name of the currently focused app.

        Returns:
            Package name string
        """
        output = self.shell("dumpsys window windows | grep -E 'mCurrentFocus|mFocusedApp'")
        # Parse output to extract package name
        # Format: mCurrentFocus=Window{... u0 com.example.app/...}
        if "/" in output:
            package = output.split("/")[0].split()[-1]
            return package
        return "unknown"
