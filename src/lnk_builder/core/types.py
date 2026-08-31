"""Shared enums used across the whole package."""

from __future__ import annotations

import platform
from enum import Enum


class LinkType(str, Enum):
    """The kind of link/shortcut a :class:`LinkSpec` describes."""

    SYMLINK = "symlink"
    HARDLINK = "hardlink"
    JUNCTION = "junction"
    LNK = "lnk"
    ALIAS = "alias"


class TargetPlatform(str, Enum):
    """The OS a link is meant for.

    ``AUTO`` means "whatever OS this process is currently running on".
    Explicit values are used to request generation for a *specific* OS,
    which for ``LNK`` and ``ALIAS`` may differ from the OS the builder
    itself is running on (cross-platform generation).
    """

    AUTO = "auto"
    WINDOWS = "windows"
    LINUX = "linux"
    MACOS = "macos"

    @classmethod
    def current(cls) -> TargetPlatform:
        """Return the :class:`TargetPlatform` matching the running OS."""

        system = platform.system()
        if system == "Windows":
            return cls.WINDOWS
        if system == "Darwin":
            return cls.MACOS
        return cls.LINUX

    def resolve(self) -> TargetPlatform:
        """Return the concrete platform, turning ``AUTO`` into the current OS."""

        return TargetPlatform.current() if self is TargetPlatform.AUTO else self
