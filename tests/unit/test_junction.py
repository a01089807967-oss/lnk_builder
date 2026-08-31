from __future__ import annotations

import json
import os
import sys

import pytest

from lnk_builder.backends.junction import DESCRIPTOR_SUFFIX
from lnk_builder.core.dispatch import build_link
from lnk_builder.core.errors import CrossPlatformNotSupportedError
from lnk_builder.core.spec import JunctionSpec
from lnk_builder.core.types import TargetPlatform


@pytest.mark.skipif(sys.platform != "win32", reason="native junctions require Windows")
def test_creates_native_junction(tmp_path):
    target_dir = tmp_path / "target"
    target_dir.mkdir()
    link_path = tmp_path / "link"

    spec = JunctionSpec(type="junction", target=str(target_dir), link_path=str(link_path))
    result = build_link(spec)

    assert result.ok, result.message
    assert os.path.isdir(link_path)


def test_fails_without_descriptor_flag_off_windows(tmp_path):
    if sys.platform == "win32":
        pytest.skip("this checks the off-Windows failure path")

    spec = JunctionSpec(
        type="junction",
        target=r"C:\Data\Shared",
        link_path=str(tmp_path / "link"),
        platform=TargetPlatform.WINDOWS,
    )
    result = build_link(spec)

    assert not result.ok
    assert isinstance(result.error, CrossPlatformNotSupportedError)


def test_emits_descriptor_when_flag_set(tmp_path):
    if sys.platform == "win32":
        pytest.skip("this checks the off-Windows descriptor fallback")

    link_path = tmp_path / "link"
    spec = JunctionSpec(
        type="junction",
        target=r"C:\Data\Shared",
        link_path=str(link_path),
        platform=TargetPlatform.WINDOWS,
        emit_descriptor_when_unavailable=True,
    )
    result = build_link(spec)

    assert result.ok, result.message
    descriptor_path = str(link_path) + DESCRIPTOR_SUFFIX
    assert os.path.isfile(descriptor_path)
    descriptor = json.loads(open(descriptor_path, encoding="utf-8").read())
    assert descriptor["target"] == r"C:\Data\Shared"
    assert descriptor["link_path"] == str(link_path)
