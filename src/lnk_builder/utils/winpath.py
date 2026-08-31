"""Validation helpers for Windows-notation paths.

``.lnk`` files are generated cross-platform: ``pylnk3`` builds a shell
item ID list directly from the path string, and it expects Windows
notation (``C:\\...`` or a UNC share ``\\\\server\\share\\...``). There is
no automatic POSIX -> Windows path translation — this module only
*validates* that a string already looks like a Windows path, so mistakes
are caught before a corrupt ``.lnk`` gets written.
"""

from __future__ import annotations

import re

_DRIVE_RE = re.compile(r"^[A-Za-z]:\\")
_UNC_RE = re.compile(r"^\\\\")


def is_windows_path(value: str) -> bool:
    return bool(_DRIVE_RE.match(value) or _UNC_RE.match(value))


def require_windows_path(value: str, *, field: str) -> None:
    from lnk_builder.core.errors import ConfigError

    if not is_windows_path(value):
        raise ConfigError(
            f"{field}='{value}' does not look like a Windows path. "
            r"lnk files need Windows notation, e.g. 'C:\Apps\tool.exe' or "
            r"a UNC path '\\server\share\tool.exe' — there is no automatic "
            "POSIX-to-Windows path translation."
        )


__all__ = ["is_windows_path", "require_windows_path"]
