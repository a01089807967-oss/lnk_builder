"""lnk_builder — cross-platform link/shortcut builder.

Automates the creation of symlinks, hardlinks, Windows junctions,
Windows ``.lnk`` shortcut files and macOS alias files from a declarative
YAML/JSON configuration.
"""

from __future__ import annotations

from lnk_builder.core.dispatch import build_all, build_link
from lnk_builder.core.result import BuildReport, LinkResult
from lnk_builder.core.spec import (
    AliasSpec,
    HardlinkSpec,
    JunctionSpec,
    LinkSpec,
    LnkSpec,
    SymlinkSpec,
)
from lnk_builder.core.types import LinkType, TargetPlatform

__version__ = "0.1.0"

__all__ = [
    "__version__",
    "build_link",
    "build_all",
    "LinkResult",
    "BuildReport",
    "LinkSpec",
    "SymlinkSpec",
    "HardlinkSpec",
    "JunctionSpec",
    "LnkSpec",
    "AliasSpec",
    "LinkType",
    "TargetPlatform",
]
