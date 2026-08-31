from __future__ import annotations

import pytest

from lnk_builder.core.dispatch import build_link
from lnk_builder.core.errors import ConfigError
from lnk_builder.core.spec import LnkSpec

pylnk3 = pytest.importorskip("pylnk3")


def test_creates_lnk_readable_by_pylnk3(tmp_path):
    link_path = tmp_path / "MyApp.lnk"
    spec = LnkSpec(
        type="lnk",
        target=r"C:\Program Files\MyApp\app.exe",
        link_path=str(link_path),
        arguments="--start-minimized",
        description="Launch MyApp",
        working_directory=r"C:\Program Files\MyApp",
        icon_location=r"C:\Program Files\MyApp\app.exe",
        icon_index=2,
        window_style="Maximized",
        hotkey="CONTROL+ALT+M",
    )

    result = build_link(spec)
    assert result.ok, result.message

    parsed = pylnk3.parse(str(link_path))
    assert parsed.arguments == "--start-minimized"
    assert parsed.description == "Launch MyApp"
    assert parsed.work_dir == r"C:\Program Files\MyApp"
    assert parsed.icon == r"C:\Program Files\MyApp\app.exe"
    assert parsed.icon_index == 2
    assert parsed.window_mode == pylnk3.WINDOW_MAXIMIZED
    assert parsed.hot_key == "CONTROL+ALT+M"


def test_rejects_posix_style_target(tmp_path):
    spec = LnkSpec(type="lnk", target="/opt/app/tool", link_path=str(tmp_path / "tool.lnk"))
    result = build_link(spec)

    assert not result.ok
    assert isinstance(result.error, ConfigError)


def test_rejects_unknown_hotkey_modifier(tmp_path):
    spec = LnkSpec(
        type="lnk",
        target=r"C:\tool.exe",
        link_path=str(tmp_path / "tool.lnk"),
        hotkey="CTRL+M",
    )
    result = build_link(spec)

    assert not result.ok
    assert isinstance(result.error, ConfigError)
