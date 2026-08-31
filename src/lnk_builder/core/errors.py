"""Exception hierarchy raised by lnk_builder."""

from __future__ import annotations


class LnkBuilderError(Exception):
    """Base class for every error raised by lnk_builder."""


class ConfigError(LnkBuilderError):
    """The configuration file is malformed or fails validation."""


class TargetNotFoundError(LnkBuilderError):
    """The ``target`` referenced by a link spec does not exist on disk."""


class LinkAlreadyExistsError(LnkBuilderError):
    """``link_path`` already exists and ``overwrite``/``--force`` was not set."""


class CrossPlatformNotSupportedError(LnkBuilderError):
    """The requested link type cannot physically be generated for another OS.

    Symlinks, hardlinks and junctions are records inside a specific
    filesystem, not self-contained file formats — there is no byte
    sequence that can be written from Linux to produce a real hardlink on
    a Windows/NTFS volume. Only ``.lnk`` and macOS alias files are true
    binary formats and can be generated cross-platform.
    """


class PermissionRequiredError(LnkBuilderError):
    """The current user/OS lacks the privilege needed to create this link.

    Typically Windows symlinks, which require either Developer Mode or
    an elevated (administrator) process.
    """


class UnsupportedLinkForTargetError(LnkBuilderError):
    """The link type is incompatible with the nature of the target.

    E.g. a hardlink pointing at a directory, or a hardlink whose target
    lives on a different filesystem/volume (``EXDEV``).
    """


class BackendUnavailableError(LnkBuilderError):
    """A backend's optional dependency (or OS API) is not available."""
