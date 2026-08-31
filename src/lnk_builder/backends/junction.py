"""Backend for Windows NTFS junction points.

Junctions are directory-level NTFS reparse points — like hardlinks, they
are a record inside a specific filesystem, not a portable file format.
Creating a real one requires an actual NTFS volume reachable through the
Windows I/O manager, so this backend is native-only by default.

When ``emit_descriptor_when_unavailable`` is set, instead of failing on a
non-Windows host it writes a JSON side-car describing the reparse point
that *would* be created. That descriptor is NOT a working junction by
itself — it is meant to be applied later by a separate tool running on
the actual Windows host. This is an explicitly experimental fallback,
not the primary path.
"""

from __future__ import annotations

import json
import os
import subprocess

from lnk_builder.core import capabilities
from lnk_builder.core.errors import (
    CrossPlatformNotSupportedError,
    TargetNotFoundError,
    UnsupportedLinkForTargetError,
)
from lnk_builder.core.fsops import clear_link_path, ensure_parent_dir
from lnk_builder.core.result import LinkResult
from lnk_builder.core.spec import JunctionSpec
from lnk_builder.core.types import TargetPlatform

DESCRIPTOR_SUFFIX = ".reparse.json"


def is_cross_platform_capable() -> bool:
    return False


def validate(spec: JunctionSpec) -> None:
    requested = spec.platform.resolve()
    current = TargetPlatform.current()

    if requested is TargetPlatform.WINDOWS and current is not TargetPlatform.WINDOWS:
        if spec.emit_descriptor_when_unavailable:
            return
        raise CrossPlatformNotSupportedError(
            "junction cannot be generated for 'windows' while running on "
            f"'{current.value}': a junction is an NTFS reparse point, not a "
            "portable file format, and needs a real NTFS volume to create. Run "
            "this build on Windows, or set emit_descriptor_when_unavailable: true "
            "to write an experimental descriptor to apply later on Windows."
        )

    if requested is not TargetPlatform.WINDOWS:
        raise CrossPlatformNotSupportedError(
            f"junction is a Windows-only concept; platform='{requested.value}' "
            "is not supported for this link type."
        )

    if current is TargetPlatform.WINDOWS and not os.path.isdir(spec.target):
        if not os.path.exists(spec.target):
            raise TargetNotFoundError(f"junction target '{spec.target}' does not exist")
        raise UnsupportedLinkForTargetError(
            f"'{spec.target}' is not a directory: junctions can only point at directories"
        )


def _create_native(spec: JunctionSpec) -> LinkResult:
    clear_link_path(spec.link_path, overwrite=spec.overwrite)
    ensure_parent_dir(spec.link_path)

    if capabilities.has_winapi_junction_support():  # pragma: no cover - Windows only
        import _winapi

        _winapi.CreateJunction(spec.target, spec.link_path)  # type: ignore[attr-defined]
    else:  # pragma: no cover - Windows only, legacy interpreter fallback
        subprocess.run(
            ["cmd", "/c", "mklink", "/J", spec.link_path, spec.target],
            check=True,
            capture_output=True,
        )

    return LinkResult(spec=spec, ok=True, link_path=spec.link_path, message="junction created")


def _create_descriptor(spec: JunctionSpec) -> LinkResult:
    descriptor_path = spec.link_path + DESCRIPTOR_SUFFIX
    clear_link_path(descriptor_path, overwrite=spec.overwrite)
    ensure_parent_dir(descriptor_path)

    descriptor = {
        "format": "lnk_builder.junction_descriptor.v1",
        "target": spec.target,
        "link_path": spec.link_path,
        "note": (
            "Experimental: this file is NOT a working junction. Apply it on a "
            "real Windows host, e.g. via 'mklink /J <link_path> <target>'."
        ),
    }
    with open(descriptor_path, "w", encoding="utf-8") as fh:
        json.dump(descriptor, fh, indent=2)

    return LinkResult(
        spec=spec,
        ok=True,
        link_path=descriptor_path,
        message=(
            "wrote experimental junction descriptor (NOT a working junction) — "
            f"apply it on Windows: mklink /J \"{spec.link_path}\" \"{spec.target}\""
        ),
    )


def create(spec: JunctionSpec) -> LinkResult:
    validate(spec)

    if TargetPlatform.current() is TargetPlatform.WINDOWS:
        return _create_native(spec)
    return _create_descriptor(spec)


__all__ = ["create", "validate", "is_cross_platform_capable"]
