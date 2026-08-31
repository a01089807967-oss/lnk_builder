"""Helpers for the POSIX-style paths used by macOS alias/bookmark files.

Deliberately built on :mod:`posixpath` rather than :mod:`os.path`: alias
files are generated cross-platform, so path handling must not depend on
the host OS's own path conventions (e.g. this may run on Windows to
produce an alias for a Mac).
"""

from __future__ import annotations

import posixpath

from lnk_builder.core.errors import ConfigError


def require_posix_path(value: str, *, field: str) -> None:
    if not value.startswith("/"):
        raise ConfigError(
            f"{field}='{value}' must be an absolute POSIX path on the target Mac "
            "volume, e.g. '/Applications/MyApp.app'"
        )


def path_components(target: str, volume_path: str) -> list[str]:
    """Split ``target`` into path components relative to ``volume_path``."""

    rel = posixpath.relpath(target, volume_path)
    if rel in (".", ""):
        raise ConfigError(
            f"target='{target}' is the same as volume_path='{volume_path}'"
        )
    if rel.startswith(".."):
        raise ConfigError(
            f"target='{target}' is not inside volume_path='{volume_path}'"
        )
    return [part for part in rel.split("/") if part]


__all__ = ["require_posix_path", "path_components"]
