# ABOUTME: Device manager for discovering and managing connected Android devices
# ABOUTME: Handles device enumeration, selection, and basic device information

from typing import List, Optional
from adb_shell.adb_device import AdbDeviceUsb, UsbTransport
from phonegang.auth import get_signers
from phonegang.config import ADB_AUTH_TIMEOUT_SECONDS


class DeviceInfo:
    """Represents information about a connected Android device."""

    def __init__(self, serial: str, model: str = "Unknown", status: str = "device", transport=None):
        self.serial = serial
        self.model = model
        self.status = status
        self.transport = transport  # Store the USB transport for reuse

    def __repr__(self) -> str:
        return f"DeviceInfo(serial='{self.serial}', model='{self.model}', status='{self.status}')"

    def __str__(self) -> str:
        return f"{self.serial} - {self.model} ({self.status})"


class DeviceManager:
    """Manages discovery and connection to Android devices over USB/ADB."""

    def __init__(self):
        self._devices: List[DeviceInfo] = []
        self._adb_key = None

    def list_devices(self) -> List[DeviceInfo]:
        """
        List all connected Android devices.

        Returns:
            List of DeviceInfo objects for connected devices
        """
        # For USB devices, we use adb_shell's USB discovery
        try:
            # Get USB devices (this returns a generator of UsbTransport objects)
            usb_transports = UsbTransport.find_all_adb_devices()

            # Load RSA keys for authentication
            rsa_keys = get_signers()

            devices = []
            for usb_transport in usb_transports:
                try:
                    # Create ADB device with this transport
                    device = AdbDeviceUsb(usb_transport)
                    device.connect(rsa_keys=rsa_keys, auth_timeout_s=ADB_AUTH_TIMEOUT_SECONDS)

                    # Get model info
                    model = device.shell("getprop ro.product.model").strip()

                    devices.append(DeviceInfo(
                        serial=usb_transport.serial_number,
                        model=model,
                        status="device",
                        transport=usb_transport
                    ))

                    device.close()
                except Exception as e:
                    # If we can't connect, still add it with unknown status
                    devices.append(DeviceInfo(
                        serial=usb_transport.serial_number,
                        model="Unknown",
                        status="unauthorized" if "unauthorized" in str(e).lower() else "offline",
                        transport=usb_transport
                    ))

            self._devices = devices
            return devices

        except Exception as e:
            raise RuntimeError(f"Failed to list devices: {e}")

    def get_device(self, serial: Optional[str] = None) -> DeviceInfo:
        """
        Get a specific device or the only connected device.

        Args:
            serial: Device serial number. If None, returns the only device if exactly one is connected.

        Returns:
            DeviceInfo for the requested device

        Raises:
            ValueError: If no devices found or multiple devices when serial not specified
        """
        if not self._devices:
            self.list_devices()

        if not self._devices:
            raise ValueError("No devices connected")

        if serial is None:
            if len(self._devices) == 1:
                return self._devices[0]
            else:
                raise ValueError(
                    f"Multiple devices connected. Please specify serial. "
                    f"Available: {[d.serial for d in self._devices]}"
                )

        for device in self._devices:
            if device.serial == serial:
                return device

        raise ValueError(f"Device with serial '{serial}' not found")

    def select_device(self, index: int) -> DeviceInfo:
        """
        Select a device by index from the list.

        Args:
            index: Index of device in the list (0-based)

        Returns:
            DeviceInfo for the selected device
        """
        if not self._devices:
            self.list_devices()

        if not self._devices:
            raise ValueError("No devices connected")

        if index < 0 or index >= len(self._devices):
            raise ValueError(f"Invalid device index. Must be 0-{len(self._devices)-1}")

        return self._devices[index]
