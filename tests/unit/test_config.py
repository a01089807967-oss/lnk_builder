from __future__ import annotations

import pytest

from lnk_builder.config import load_config
from lnk_builder.core.errors import ConfigError
from lnk_builder.core.spec import LnkSpec, SymlinkSpec

VALID_YAML = """
version: 1
defaults:
  overwrite: true
links:
  - type: symlink
    target: /a
    link_path: /b
  - type: lnk
    target: "C:\\\\a.exe"
    link_path: "C:\\\\a.lnk"
    overwrite: false
"""


def test_loads_valid_config(tmp_path):
    config_path = tmp_path / "links.yaml"
    config_path.write_text(VALID_YAML)

    config = load_config(str(config_path))

    assert len(config.links) == 2
    assert isinstance(config.links[0], SymlinkSpec)
    assert isinstance(config.links[1], LnkSpec)


def test_defaults_are_merged_but_overridable(tmp_path):
    config_path = tmp_path / "links.yaml"
    config_path.write_text(VALID_YAML)

    config = load_config(str(config_path))

    assert config.links[0].overwrite is True  # inherited from defaults
    assert config.links[1].overwrite is False  # explicit override wins


def test_missing_file_raises_config_error(tmp_path):
    with pytest.raises(ConfigError):
        load_config(str(tmp_path / "nope.yaml"))


def test_unknown_type_raises_config_error(tmp_path):
    config_path = tmp_path / "links.yaml"
    config_path.write_text(
        """
version: 1
links:
  - type: teleport
    target: /a
    link_path: /b
"""
    )

    with pytest.raises(ConfigError):
        load_config(str(config_path))


def test_missing_required_field_raises_config_error(tmp_path):
    config_path = tmp_path / "links.yaml"
    config_path.write_text(
        """
version: 1
links:
  - type: symlink
    target: /a
"""
    )

    with pytest.raises(ConfigError):
        load_config(str(config_path))
