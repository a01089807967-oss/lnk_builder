from __future__ import annotations

import pytest

from lnk_builder.core.dispatch import build_link
from lnk_builder.core.errors import ConfigError
from lnk_builder.core.spec import AliasSpec

mac_alias = pytest.importorskip("mac_alias")


def test_creates_alias_readable_by_mac_alias(tmp_path):
    link_path = tmp_path / "MyApp alias"
    spec = AliasSpec(
        type="alias",
        target="/Applications/MyApp.app",
        link_path=str(link_path),
        volume_name="Macintosh HD",
        volume_uuid="5C0B4B8E-2C2E-4F0A-9C3D-11223344AABB",
    )

    result = build_link(spec)
    assert result.ok, result.message

    data = link_path.read_bytes()
    assert data[:4] == b"book"

    bookmark = mac_alias.Bookmark.from_bytes(data)
    assert bookmark[mac_alias.kBookmarkPath] == ["Applications", "MyApp.app"]
    assert bookmark[mac_alias.kBookmarkVolumeName] == "Macintosh HD"
    assert bookmark[mac_alias.kBookmarkVolumeUUID] == "5C0B4B8E-2C2E-4F0A-9C3D-11223344AABB"


def test_generates_synthetic_volume_uuid_when_missing(tmp_path):
    link_path = tmp_path / "MyApp alias"
    spec = AliasSpec(type="alias", target="/Applications/MyApp.app", link_path=str(link_path))

    result = build_link(spec)
    assert result.ok, result.message

    bookmark = mac_alias.Bookmark.from_bytes(link_path.read_bytes())
    assert bookmark[mac_alias.kBookmarkVolumeUUID]


def test_rejects_relative_target(tmp_path):
    spec = AliasSpec(type="alias", target="Applications/MyApp.app", link_path=str(tmp_path / "a"))
    result = build_link(spec)

    assert not result.ok
    assert isinstance(result.error, ConfigError)
