from __future__ import annotations

import os
import sys

from lnk_builder.core.dispatch import build_link
from lnk_builder.core.errors import (
    CrossPlatformNotSupportedError,
    TargetNotFoundError,
    UnsupportedLinkForTargetError,
)
from lnk_builder.core.spec import HardlinkSpec
from lnk_builder.core.types import TargetPlatform


def test_creates_hardlink(tmp_path):
    target = tmp_path / "target.txt"
    target.write_text("hello")
    link_path = tmp_path / "link.txt"

    spec = HardlinkSpec(type="hardlink", target=str(target), link_path=str(link_path))
    result = build_link(spec)

    assert result.ok, result.message
    assert not os.path.islink(link_path)
    assert os.stat(link_path).st_ino == os.stat(target).st_ino
    assert os.stat(target).st_nlink == 2


def test_target_missing(tmp_path):
    spec = HardlinkSpec(
        type="hardlink", target=str(tmp_path / "nope.txt"), link_path=str(tmp_path / "link.txt")
    )
    result = build_link(spec)

    assert not result.ok
    assert isinstance(result.error, TargetNotFoundError)


def test_directory_target_rejected(tmp_path):
    target_dir = tmp_path / "adir"
    target_dir.mkdir()

    spec = HardlinkSpec(type="hardlink", target=str(target_dir), link_path=str(tmp_path / "link"))
    result = build_link(spec)

    assert not result.ok
    assert isinstance(result.error, UnsupportedLinkForTargetError)


def test_cross_platform_hardlink_is_rejected(tmp_path):
    target = tmp_path / "target.txt"
    target.write_text("hello")

    other = TargetPlatform.WINDOWS if sys.platform != "win32" else TargetPlatform.LINUX
    spec = HardlinkSpec(
        type="hardlink", target=str(target), link_path=str(tmp_path / "link.txt"), platform=other
    )
    result = build_link(spec)

    assert not result.ok
    assert isinstance(result.error, CrossPlatformNotSupportedError)
