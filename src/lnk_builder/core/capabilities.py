"""Detection of what the current OS/process is actually allowed to do."""

from __future__ import annotations

import ctypes
import os
import sys


def is_windows() -> bool:
    return sys.platform == "win32"


def is_macos() -> bool:
    return sys.platform == "darwin"


def is_linux() -> bool:
    return sys.platform.startswith("linux")


def can_create_windows_symlink() -> bool:
    """Whether the current process can call ``os.symlink`` on Windows.

    True if the process is elevated (administrator) or Developer Mode is
    enabled (``AllowDevelopmentWithoutDevMode`` under
    ``HKLM\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\AppModelUnlock``).
    Not meaningful outside Windows — always returns True there, since the
    check does not apply.
    """

    if not is_windows():  # pragma: no cover - trivial branch on non-Windows
        return True

    try:  # pragma: no cover - exercised only on Windows CI
        if ctypes.windll.shell32.IsUserAnAdmin():  # type: ignore[attr-defined]
            return True
    except Exception:
        pass

    try:  # pragma: no cover - exercised only on Windows CI
        import winreg

        key = winreg.OpenKey(  # type: ignore[attr-defined]
            winreg.HKEY_LOCAL_MACHINE,  # type: ignore[attr-defined]
            r"SOFTWARE\Microsoft\Windows\CurrentVersion\AppModelUnlock",
        )
        value, _ = winreg.QueryValueEx(key, "AllowDevelopmentWithoutDevMode")  # type: ignore[attr-defined]
        return bool(value)
    except OSError:
        return False


def has_winapi_junction_support() -> bool:
    """Whether ``_winapi.CreateJunction`` is available in this interpreter."""

    if not is_windows():
        return False
    try:
        import _winapi

        return hasattr(_winapi, "CreateJunction")
    except ImportError:  # pragma: no cover - defensive
        return False


def supports_xattr() -> bool:
    """Whether ``os.setxattr``/``os.getxattr`` exist on this platform."""

    return hasattr(os, "setxattr") and hasattr(os, "getxattr")
