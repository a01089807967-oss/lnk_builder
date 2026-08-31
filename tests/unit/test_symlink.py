from __future__ import annotations

import os
import sys

from lnk_builder.core.dispatch import build_link
from lnk_builder.core.errors import CrossPlatformNotSupportedError, LinkAlreadyExistsError
from lnk_builder.core.spec import SymlinkSpec
from lnk_builder.core.types import TargetPlatform


def test_creates_symlink(tmp_path):
    target = tmp_path / "target.txt"
    target.write_text("hello")
    link_path = tmp_path / "link.txt"

    spec = SymlinkSpec(type="symlink", target=str(target), link_path=str(link_path))
    result = build_link(spec)

    assert result.ok, result.message
    assert os.path.islink(link_path)
    assert os.path.realpath(link_path) == os.path.realpath(target)


def test_existing_link_path_without_overwrite_fails(tmp_path):
    target = tmp_path / "target.txt"
    target.write_text("hello")
    link_path = tmp_path / "link.txt"
    link_path.write_text("already here")

    spec = SymlinkSpec(type="symlink", target=str(target), link_path=str(link_path))
    result = build_link(spec)

    assert not result.ok
    assert isinstance(result.error, LinkAlreadyExistsError)


def test_overwrite_replaces_existing(tmp_path):
    target = tmp_path / "target.txt"
    target.write_text("hello")
    link_path = tmp_path / "link.txt"
    link_path.write_text("already here")

    spec = SymlinkSpec(
        type="symlink", target=str(target), link_path=str(link_path), overwrite=True
    )
    result = build_link(spec)

    assert result.ok, result.message
    assert os.path.islink(link_path)


def test_cross_platform_symlink_is_rejected(tmp_path):
    target = tmp_path / "target.txt"
    target.write_text("hello")
    link_path = tmp_path / "link.txt"

    other = TargetPlatform.WINDOWS if sys.platform != "win32" else TargetPlatform.LINUX
    spec = SymlinkSpec(type="symlink", target=str(target), link_path=str(link_path), platform=other)
    result = build_link(spec)

    assert not result.ok
    assert isinstance(result.error, CrossPlatformNotSupportedError)
