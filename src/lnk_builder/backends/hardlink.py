"""Backend for hardlinks.

A hardlink is a second directory entry pointing at the same inode/MFT
record as an existing file. It has no independent on-disk representation
of its own — there is no byte sequence to "generate" for another OS —
so, unlike ``.lnk``/alias, hardlinks can only ever be created natively,
on the OS (and filesystem) that will host them.
"""

from __future__ import annotations

import errno
import os

from lnk_builder.core.errors import (
    CrossPlatformNotSupportedError,
    TargetNotFoundError,
    UnsupportedLinkForTargetError,
)
from lnk_builder.core.fsops import clear_link_path, ensure_parent_dir
from lnk_builder.core.result import LinkResult
from lnk_builder.core.spec import HardlinkSpec
from lnk_builder.core.types import TargetPlatform


def is_cross_platform_capable() -> bool:
    return False


def validate(spec: HardlinkSpec) -> None:
    requested = spec.platform.resolve()
    current = TargetPlatform.current()
    if requested is not current:
        raise CrossPlatformNotSupportedError(
            f"hardlink cannot be generated for '{requested.value}' while running on "
            f"'{current.value}': a hardlink is an entry in that filesystem's own "
            "inode/MFT table, not a file format — there is nothing to write from "
            "another OS. Run this build on the target OS instead."
        )

    if not os.path.exists(spec.target):
        raise TargetNotFoundError(f"hardlink target '{spec.target}' does not exist")

    if os.path.isdir(spec.target):
        raise UnsupportedLinkForTargetError(
            f"'{spec.target}' is a directory: hardlinks to directories are not "
            "supported by NTFS or POSIX filesystems through the standard API — "
            "use a symlink or junction instead."
        )


def create(spec: HardlinkSpec) -> LinkResult:
    validate(spec)

    clear_link_path(spec.link_path, overwrite=spec.overwrite)
    ensure_parent_dir(spec.link_path)

    try:
        os.link(spec.target, spec.link_path)
    except OSError as exc:
        if exc.errno == errno.EXDEV:
            raise UnsupportedLinkForTargetError(
                f"cannot hardlink '{spec.target}' -> '{spec.link_path}': they are on "
                "different filesystems/volumes. Hardlinks require both paths to live "
                "on the same volume — use a symlink instead."
            ) from exc
        raise

    return LinkResult(spec=spec, ok=True, link_path=spec.link_path, message="hardlink created")


__all__ = ["create", "validate", "is_cross_platform_capable"]
