# ABOUTME: Authentication helper for ADB connections
# ABOUTME: Handles RSA key generation, loading, and management for device authorization

from pathlib import Path
from typing import List
from adb_shell.auth.keygen import keygen, write_public_keyfile
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
    Load existing RSA keys, generating a new pair only if none exist.

    An existing private key is never overwritten: every device that has
    authorized it (on this machine or any other sharing ~/.android) would be
    invalidated and need re-approval. If the private key is present but its
    public counterpart is missing, the public key is re-derived from it.

    Args:
        key_path: Path to the ADB key directory. If None, uses default (~/.android)

    Returns:
        List of PythonRSASigner objects for authentication

    Raises:
        RuntimeError: If an existing private key is present but unusable, or if
            key generation fails.
    """
    if key_path is None:
        key_path = get_default_key_path()

    private_key_path = key_path / "adbkey"
    public_key_path = key_path / "adbkey.pub"

    if private_key_path.exists():
        # Derive the public key rather than regenerating the pair, so existing
        # device authorizations survive.
        if not public_key_path.exists():
            try:
                write_public_keyfile(str(private_key_path), str(public_key_path))
            except Exception as e:
                raise RuntimeError(
                    f"ADB private key at {private_key_path} exists but its public key "
                    f"could not be derived: {e}\n"
                    f"Refusing to generate a new key, which would revoke this machine's "
                    f"existing device authorizations. Move {private_key_path} aside to "
                    f"start over with a fresh key."
                ) from e

        try:
            return [PythonRSASigner.FromRSAKeyPath(str(private_key_path))]
        except Exception as e:
            raise RuntimeError(
                f"Failed to load ADB key at {private_key_path}: {e}\n"
                f"Refusing to overwrite it, which would revoke this machine's existing "
                f"device authorizations. Move it aside to generate a fresh key."
            ) from e

    # No private key on disk: safe to create one.
    try:
        keygen(str(private_key_path))
    except Exception as e:
        raise RuntimeError(f"Failed to generate ADB key at {private_key_path}: {e}") from e

    print(f"Generated a new ADB key at {private_key_path}")
    print("Accept the 'Allow USB debugging' prompt on the device to authorize it.")
    return [PythonRSASigner.FromRSAKeyPath(str(private_key_path))]


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
