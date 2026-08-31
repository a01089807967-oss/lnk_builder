"""Backend for macOS alias files (the modern "bookmark" format).

Cross-platform, but best-effort outside macOS: the bookmark byte format
itself (``Bookmark.to_bytes()``/``from_bytes()``) is pure Python data
handling and works on any OS. What is *not* available off macOS is the
real filesystem metadata a genuine alias embeds — CNIDs (Catalog Node
IDs), the real volume UUID/creation date, etc. — because obtaining those
requires macOS-only syscalls (``mac_alias`` itself gates that behind
``sys.platform == "darwin"`` in its own ``Bookmark.for_file()``, which
this backend intentionally does not call).

So this backend builds the same TOC structure ``Bookmark.for_file()``
would, but fills the unobtainable fields with documented placeholders:
CNIDs are synthetic, so Finder falls back to path-based resolution
instead of ID-based resolution, which still works as long as the path is
correct on the destination Mac. Treat generated aliases as best-effort
and verify them on a real Mac before relying on them in production.
"""

from __future__ import annotations

import datetime
import os
import struct
import uuid as uuid_mod

from lnk_builder.core.errors import BackendUnavailableError
from lnk_builder.core.fsops import clear_link_path, ensure_parent_dir
from lnk_builder.core.result import LinkResult
from lnk_builder.core.spec import AliasSpec
from lnk_builder.utils.posixpath_mac import path_components, require_posix_path

try:
    from mac_alias.bookmark import (
        URL,
        Bookmark,
        Data,
        kBookmarkCNIDPath,
        kBookmarkContainingFolder,
        kBookmarkCreationOptions,
        kBookmarkFileCreationDate,
        kBookmarkFileProperties,
        kBookmarkPath,
        kBookmarkUID,
        kBookmarkUserName,
        kBookmarkVolumeCreationDate,
        kBookmarkVolumeIsRoot,
        kBookmarkVolumeName,
        kBookmarkVolumePath,
        kBookmarkVolumeProperties,
        kBookmarkVolumeURL,
        kBookmarkVolumeUUID,
        kBookmarkWasFileReference,
        kCFURLResourceIsDirectory,
        kCFURLResourceIsRegularFile,
        kCFURLVolumeSupportsPersistentIDs,
    )
except ImportError:  # pragma: no cover - exercised only when extra not installed
    Bookmark = None

# Finder "is alias" flag, stored in the fdFlags field (bytes 8-9, big
# endian) of the classic 32-byte com.apple.FinderInfo extended attribute.
_FINDER_INFO_SIZE = 32
_FINDER_FLAGS_OFFSET = 8
_FINDER_FLAG_IS_ALIAS = 0x8000


def is_cross_platform_capable() -> bool:
    return True


def _require_mac_alias() -> None:
    if Bookmark is None:  # pragma: no cover - exercised only when extra not installed
        raise BackendUnavailableError(
            "the 'alias' link type requires the 'mac_alias' package. Install it "
            "with 'pip install lnk_builder[alias]' (or 'lnk_builder[all]')."
        )


def validate(spec: AliasSpec) -> None:
    _require_mac_alias()
    require_posix_path(spec.target, field="target")
    require_posix_path(spec.volume_path, field="volume_path")
    path_components(spec.target, spec.volume_path)  # raises ConfigError if inconsistent


def _build_bookmark(spec: AliasSpec) -> Bookmark:
    name_path = path_components(spec.target, spec.volume_path)
    # Real Catalog Node IDs are unobtainable without macOS; using 0 for
    # every level means Finder cannot ID-resolve the alias and instead
    # falls back to resolving it by path, which is still correct as long
    # as the path exists on the destination volume.
    cnid_path = [0 for _ in name_path]

    is_directory = spec.target.endswith("/") or "." not in os.path.basename(spec.target)
    flags = kCFURLResourceIsDirectory if is_directory else kCFURLResourceIsRegularFile
    fileprops = Data(struct.pack(b"<QQQ", flags, 0x0F, 0))
    volprops = Data(
        struct.pack(
            b"<QQQ",
            0x81 | kCFURLVolumeSupportsPersistentIDs,
            0x13EF | kCFURLVolumeSupportsPersistentIDs,
            0,
        )
    )

    now = datetime.datetime.now(datetime.timezone.utc)
    volume_uuid = (spec.volume_uuid or str(uuid_mod.uuid4())).upper()

    toc = {
        kBookmarkPath: name_path,
        kBookmarkCNIDPath: cnid_path,
        kBookmarkFileCreationDate: now,
        kBookmarkFileProperties: fileprops,
        kBookmarkContainingFolder: max(len(name_path) - 2, 0),
        kBookmarkVolumePath: spec.volume_path,
        kBookmarkVolumeIsRoot: spec.volume_path == "/",
        kBookmarkVolumeURL: URL("file://" + spec.volume_path),
        kBookmarkVolumeName: spec.volume_name,
        kBookmarkVolumeCreationDate: now,
        kBookmarkVolumeUUID: volume_uuid,
        kBookmarkVolumeProperties: volprops,
        kBookmarkCreationOptions: 512,
        kBookmarkWasFileReference: True,
        kBookmarkUserName: "unknown",
        kBookmarkUID: 99,
    }
    return Bookmark([(1, toc)])


def _try_set_finder_alias_flag(link_path: str) -> None:
    """Best-effort: set the Finder "is alias" bit via the FinderInfo xattr.

    This is opportunistic. On a real macOS filesystem it makes Finder
    treat the file as an alias; on other OSes/filesystems ``setxattr`` may
    not be supported at all, or the attribute may not survive a later
    non-Mac-aware copy (plain ``cp``, generic zip, git, ...) — silently
    give up rather than fail the whole build over a cosmetic flag.
    """

    if not (hasattr(os, "setxattr")):
        return
    info = bytearray(_FINDER_INFO_SIZE)
    struct.pack_into(">H", info, _FINDER_FLAGS_OFFSET, _FINDER_FLAG_IS_ALIAS)
    try:
        os.setxattr(link_path, "com.apple.FinderInfo", bytes(info))
    except OSError:
        pass


def create(spec: AliasSpec) -> LinkResult:
    validate(spec)

    clear_link_path(spec.link_path, overwrite=spec.overwrite)
    ensure_parent_dir(spec.link_path)

    bookmark = _build_bookmark(spec)
    with open(spec.link_path, "wb") as fh:
        fh.write(bookmark.to_bytes())

    message = "alias file created (best-effort outside macOS — verify on a real Mac)"
    if spec.best_effort_finder_flag:
        _try_set_finder_alias_flag(spec.link_path)

    return LinkResult(spec=spec, ok=True, link_path=spec.link_path, message=message)


__all__ = ["create", "validate", "is_cross_platform_capable"]
