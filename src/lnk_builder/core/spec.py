"""Declarative specifications for the links lnk_builder can create."""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field

from lnk_builder.core.types import LinkType, TargetPlatform


class BaseLinkSpec(BaseModel):
    """Fields shared by every link type."""

    model_config = ConfigDict(extra="forbid")

    target: str
    """Path (or, for ``lnk``, a Windows-notation path) the link points at."""

    link_path: str
    """Where the resulting link/shortcut file is created."""

    platform: TargetPlatform = TargetPlatform.AUTO
    """Which OS this link is meant for. ``auto`` = the OS running the build."""

    overwrite: bool = False
    """Replace ``link_path`` if it already exists."""


class SymlinkSpec(BaseLinkSpec):
    type: Literal[LinkType.SYMLINK]

    target_is_directory: bool | None = None
    """Hint passed to ``os.symlink`` on Windows when ``target`` doesn't exist yet."""


class HardlinkSpec(BaseLinkSpec):
    type: Literal[LinkType.HARDLINK]


class JunctionSpec(BaseLinkSpec):
    type: Literal[LinkType.JUNCTION]

    emit_descriptor_when_unavailable: bool = False
    """Experimental: write a side-car reparse-point descriptor instead of
    failing when not running on Windows. The descriptor is NOT a working
    junction by itself; it must later be applied on a real Windows host."""


class LnkSpec(BaseLinkSpec):
    type: Literal[LinkType.LNK]

    arguments: str | None = None
    description: str | None = None
    working_directory: str | None = None
    icon_location: str | None = None
    icon_index: int = 0
    window_style: Literal["Normal", "Maximized", "Minimized"] = "Normal"
    hotkey: str | None = None
    """E.g. ``"CONTROL+ALT+F"``."""


class AliasSpec(BaseLinkSpec):
    type: Literal[LinkType.ALIAS]

    volume_name: str = "Macintosh HD"
    volume_uuid: str | None = None
    """Real volume UUID if known; otherwise a synthetic one is generated
    (best-effort — see README limitations)."""
    volume_path: str = "/"
    best_effort_finder_flag: bool = True
    """Try to set the Finder "is alias" xattr bit. Best-effort outside macOS."""


LinkSpec = Annotated[
    SymlinkSpec | HardlinkSpec | JunctionSpec | LnkSpec | AliasSpec,
    Field(discriminator="type"),
]

__all__ = [
    "BaseLinkSpec",
    "SymlinkSpec",
    "HardlinkSpec",
    "JunctionSpec",
    "LnkSpec",
    "AliasSpec",
    "LinkSpec",
]
