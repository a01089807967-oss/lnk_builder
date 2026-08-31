"""Backend for POSIX/Windows symbolic links."""

from __future__ import annotations

import os

from lnk_builder.core import capabilities
from lnk_builder.core.errors import (
    CrossPlatformNotSupportedError,
    PermissionRequiredError,
)
from lnk_builder.core.fsops import clear_link_path, ensure_parent_dir
from lnk_builder.core.result import LinkResult
from lnk_builder.core.spec import SymlinkSpec
from lnk_builder.core.types import TargetPlatform


def is_cross_platform_capable() -> bool:
    return False


def validate(spec: SymlinkSpec) -> None:
    requested = spec.platform.resolve()
    current = TargetPlatform.current()
    if requested is not current:
        raise CrossPlatformNotSupportedError(
            f"symlink cannot be generated for '{requested.value}' while running on "
            f"'{current.value}': a symlink is a filesystem record, not a portable "
            "file format, so it can only be created on the OS it targets."
        )

    if capabilities.is_windows() and not capabilities.can_create_windows_symlink():
        raise PermissionRequiredError(
            "creating a symlink on Windows requires either Developer Mode "
            "(Settings > Update & Security > For developers) or running as "
            "Administrator."
        )


def create(spec: SymlinkSpec) -> LinkResult:
    validate(spec)

    # POSIX symlinks may legitimately point at a target that doesn't exist
    # yet, so existence is never required here. On Windows the OS still
    # needs to know upfront whether the target is a directory; when the
    # caller didn't say and the target happens to not exist yet, this
    # simply falls back to False (a file symlink).
    target_is_directory = spec.target_is_directory
    if target_is_directory is None:
        target_is_directory = os.path.isdir(spec.target)

    clear_link_path(spec.link_path, overwrite=spec.overwrite)
    ensure_parent_dir(spec.link_path)

    kwargs = {"target_is_directory": target_is_directory} if capabilities.is_windows() else {}
    os.symlink(spec.target, spec.link_path, **kwargs)

    return LinkResult(spec=spec, ok=True, link_path=spec.link_path, message="symlink created")


__all__ = ["create", "validate", "is_cross_platform_capable"]
