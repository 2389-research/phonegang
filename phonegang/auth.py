# ABOUTME: Authentication helper for ADB connections
# ABOUTME: Handles RSA key generation, loading, and management for device authorization

import os
from pathlib import Path
from typing import List
from adb_shell.auth.sign_pythonrsa import PythonRSASigner


def get_default_key_path() -> Path:
    """
    Get the default path for ADB keys.

    Returns:
        Path to the default ADB key directory
    """
    home = Path.home()
    adb_dir = home / ".android"
    adb_dir.mkdir(exist_ok=True)
    return adb_dir


def load_or_generate_keys(key_path: Path = None) -> List[PythonRSASigner]:
    """
    Load existing RSA keys or generate new ones if they don't exist.

    Args:
        key_path: Path to the ADB key directory. If None, uses default (~/.android)

    Returns:
        List of PythonRSASigner objects for authentication
    """
    if key_path is None:
        key_path = get_default_key_path()

    private_key_path = key_path / "adbkey"
    public_key_path = key_path / "adbkey.pub"

    # Try to load existing keys
    if private_key_path.exists() and public_key_path.exists():
        try:
            signer = PythonRSASigner.FromRSAKeyPath(str(private_key_path))
            return [signer]
        except Exception as e:
            print(f"Warning: Failed to load existing keys: {e}")
            print("Generating new keys...")

    # Generate new keys using system adb command
    try:
        import subprocess

        print(f"No ADB keys found. Generating new keys at {key_path}...")
        print("Please run 'adb devices' once to generate the keys, or they will be created on first connection attempt.")

        # Try to generate using adb keygen if available
        try:
            subprocess.run(
                ['adb', 'keygen', str(private_key_path)],
                check=True,
                capture_output=True,
                timeout=10
            )
            print(f"Generated new ADB keys at {key_path}")
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
            # If adb keygen doesn't work, create a message for the user
            print("Could not generate keys automatically. Please:")
            print(f"1. Run 'adb devices' to generate keys")
            print(f"2. Or manually place RSA keys at {private_key_path}")
            print("Then try connecting again.")
            return []

        # Load the generated keys
        if private_key_path.exists():
            signer = PythonRSASigner.FromRSAKeyPath(str(private_key_path))
            return [signer]
        else:
            print("Keys were not created. Returning empty list.")
            return []

    except Exception as e:
        print(f"Warning: Failed to generate RSA keys: {e}")
        print("Returning empty signer list. Connection may fail if device requires authentication.")
        return []


def get_signers(key_path: Path = None) -> List[PythonRSASigner]:
    """
    Get RSA signers for ADB authentication.

    Convenience function that loads or generates keys.

    Args:
        key_path: Path to the ADB key directory. If None, uses default.

    Returns:
        List of PythonRSASigner objects
    """
    return load_or_generate_keys(key_path)
