# ABOUTME: Wrapper for scrcpy screen mirroring tool
# ABOUTME: Manages scrcpy processes for real-time Android device mirroring

import subprocess
import shutil
import signal
import time
from typing import Optional, Dict
from dataclasses import dataclass


@dataclass
class ScrcpyConfig:
    """Configuration for scrcpy mirroring."""
    max_size: Optional[int] = None  # Max screen dimension (e.g., 1024)
    bit_rate: Optional[str] = None  # Video bit rate (e.g., "2M")
    max_fps: Optional[int] = None  # Max frame rate
    window_title: Optional[str] = None  # Window title
    fullscreen: bool = False  # Start in fullscreen
    always_on_top: bool = False  # Keep window on top
    show_touches: bool = False  # Show physical touches
    turn_screen_off: bool = False  # Turn screen off while mirroring
    stay_awake: bool = True  # Keep device awake while plugged in
    no_control: bool = False  # Disable device control (display only)
    serial: Optional[str] = None  # Device serial number


class ScrcpyManager:
    """Manages scrcpy screen mirroring processes."""

    # Class-level registry of running processes
    _processes: Dict[str, subprocess.Popen] = {}

    def __init__(self):
        """Initialize the scrcpy manager."""
        self._check_scrcpy_installed()

    @staticmethod
    def _check_scrcpy_installed() -> bool:
        """Check if scrcpy is installed and available."""
        if not shutil.which("scrcpy"):
            raise RuntimeError(
                "scrcpy is not installed or not in PATH. "
                "Install it from https://github.com/Genymobile/scrcpy"
            )
        return True

    @staticmethod
    def is_installed() -> bool:
        """Check if scrcpy is available without raising an error."""
        return shutil.which("scrcpy") is not None

    def start(self, config: Optional[ScrcpyConfig] = None) -> subprocess.Popen:
        """
        Start a scrcpy mirroring session.

        Args:
            config: Configuration for the mirroring session

        Returns:
            The subprocess.Popen object for the scrcpy process
        """
        if config is None:
            config = ScrcpyConfig()

        # Build command
        cmd = ["scrcpy"]

        if config.serial:
            cmd.extend(["-s", config.serial])

        if config.max_size:
            cmd.extend(["-m", str(config.max_size)])

        if config.bit_rate:
            cmd.extend(["-b", config.bit_rate])

        if config.max_fps:
            cmd.extend(["--max-fps", str(config.max_fps)])

        if config.window_title:
            cmd.extend(["--window-title", config.window_title])

        if config.fullscreen:
            cmd.append("-f")

        if config.always_on_top:
            cmd.append("--always-on-top")

        if config.show_touches:
            cmd.append("-t")

        if config.turn_screen_off:
            cmd.append("--turn-screen-off")

        if config.stay_awake:
            cmd.append("--stay-awake")

        if config.no_control:
            cmd.append("--no-control")

        # Start process
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            start_new_session=True
        )

        # Give it a moment to start
        time.sleep(0.5)

        # Check if process started successfully
        if process.poll() is not None:
            stdout, stderr = process.communicate()
            error_msg = stderr.decode() if stderr else "Unknown error"
            raise RuntimeError(f"Failed to start scrcpy: {error_msg}")

        # Register process
        serial = config.serial or "default"
        self._processes[serial] = process

        return process

    def stop(self, serial: Optional[str] = None) -> bool:
        """
        Stop a running scrcpy session.

        Args:
            serial: Device serial number (None for default device)

        Returns:
            True if a process was stopped, False if no process was running
        """
        serial = serial or "default"

        if serial not in self._processes:
            return False

        process = self._processes[serial]

        # Try graceful termination first
        try:
            process.terminate()
            process.wait(timeout=2)
        except subprocess.TimeoutExpired:
            # Force kill if termination doesn't work
            process.kill()
            process.wait()

        del self._processes[serial]
        return True

    def stop_all(self) -> int:
        """
        Stop all running scrcpy sessions.

        Returns:
            Number of processes stopped
        """
        count = 0
        serials = list(self._processes.keys())

        for serial in serials:
            if self.stop(serial):
                count += 1

        return count

    def is_running(self, serial: Optional[str] = None) -> bool:
        """
        Check if a scrcpy session is running.

        Args:
            serial: Device serial number (None for default device)

        Returns:
            True if a session is running, False otherwise
        """
        serial = serial or "default"

        if serial not in self._processes:
            return False

        process = self._processes[serial]

        # Check if process is still alive
        if process.poll() is not None:
            # Process has ended, clean it up
            del self._processes[serial]
            return False

        return True

    def get_running_sessions(self) -> Dict[str, subprocess.Popen]:
        """
        Get all running scrcpy sessions.

        Returns:
            Dictionary mapping serial numbers to process objects
        """
        # Clean up dead processes
        dead_serials = []
        for serial, process in self._processes.items():
            if process.poll() is not None:
                dead_serials.append(serial)

        for serial in dead_serials:
            del self._processes[serial]

        return self._processes.copy()


# Convenience function for quick mirroring
def mirror_device(serial: Optional[str] = None, **kwargs) -> subprocess.Popen:
    """
    Quickly start mirroring a device.

    Args:
        serial: Device serial number (optional)
        **kwargs: Additional configuration options (see ScrcpyConfig)

    Returns:
        The subprocess.Popen object for the scrcpy process

    Example:
        >>> mirror_device(max_size=1024, show_touches=True)
    """
    config = ScrcpyConfig(serial=serial, **kwargs)
    manager = ScrcpyManager()
    return manager.start(config)
