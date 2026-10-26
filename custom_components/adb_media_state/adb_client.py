"""Thin wrapper around adb-shell: connection, RSA key, shell commands."""
from __future__ import annotations

import logging
import os

_LOGGER = logging.getLogger(__name__)

try:  # home-assistant ships adb-shell for its androidtv integration
    from adb_shell.adb_device import AdbDeviceTcp
    from adb_shell.auth.auth_keygen import keygen  # type: ignore[attr-defined]
except ImportError:  # pragma: no cover - older adb-shell layout
    try:
        from adb_shell.adb_device import AdbDeviceTcp
        from adb_shell.auth.keygen import keygen  # type: ignore[no-redef]
    except ImportError as exc:  # pragma: no cover
        AdbDeviceTcp = None  # type: ignore[assignment]
        keygen = None  # type: ignore[assignment]
        _IMPORT_ERROR = exc
    else:
        _IMPORT_ERROR = None
else:
    _IMPORT_ERROR = None

try:
    from adb_shell.auth.sign_cryptography import CryptographySigner
except ImportError:  # pragma: no cover
    try:
        from adb_shell.auth.sign_pythonrsa import PythonRSASigner as CryptographySigner  # type: ignore[assignment]
    except ImportError as exc:  # pragma: no cover
        CryptographySigner = None  # type: ignore[assignment]
        _IMPORT_ERROR = _IMPORT_ERROR or exc


class AdbError(Exception):
    """Raised when the device cannot be reached or a command fails."""


def ensure_key(key_path: str) -> str:
    """Create the RSA key pair when it does not exist yet."""
    if keygen is None:
        raise AdbError(f"adb-shell is not available: {_IMPORT_ERROR}")
    if not os.path.exists(key_path):
        os.makedirs(os.path.dirname(key_path), exist_ok=True)
        keygen(key_path)
        _LOGGER.warning(
            "Generated a new ADB key at %s - accept the prompt on the device "
            "(choose 'always allow')",
            key_path,
        )
    return key_path


class AdbSession:
    """Keeps one connection to a device and runs shell commands on it."""

    def __init__(self, host: str, port: int, key_path: str) -> None:
        self._host = host
        self._port = port
        self._key_path = key_path
        self._device = None

    def _connect(self) -> None:
        if AdbDeviceTcp is None or CryptographySigner is None:
            raise AdbError(f"adb-shell is not available: {_IMPORT_ERROR}")
        ensure_key(self._key_path)
        signer = CryptographySigner(self._key_path)
        device = AdbDeviceTcp(self._host, self._port, default_transport_timeout_s=15)
        device.connect(rsa_keys=[signer], auth_timeout_s=15)
        self._device = device

    def shell(self, command: str) -> str:
        """Run a shell command, reconnecting once on failure."""
        last_exc: Exception | None = None
        for _ in (1, 2):
            try:
                if self._device is None:
                    self._connect()
                if self._device is None:
                    raise AdbError("not connected")
                return self._device.shell(command) or ""
            except Exception as exc:  # noqa: BLE001
                last_exc = exc
                self.close()
        raise AdbError(f"{type(last_exc).__name__}: {last_exc}")

    def close(self) -> None:
        device, self._device = self._device, None
        if device is not None:
            try:
                device.close()
            except Exception:  # noqa: BLE001
                pass
