from __future__ import annotations

import os
from pathlib import Path

from click.testing import CliRunner

from lnk_builder.cli import main

FIXTURE = Path(__file__).parent / "fixtures" / "sample_config.yaml"


def _render_config(tmp_path) -> Path:
    target = tmp_path / "target.txt"
    target.write_text("hello")
    link_path = tmp_path / "link.txt"
    lnk_path = tmp_path / "MyApp.lnk"

    template = FIXTURE.read_text()
    rendered = template.format(
        target=str(target).replace("\\", "\\\\"),
        link_path=str(link_path).replace("\\", "\\\\"),
        lnk_path=str(lnk_path).replace("\\", "\\\\"),
    )
    config_path = tmp_path / "config.yaml"
    config_path.write_text(rendered)
    return config_path


def test_build_creates_every_link(tmp_path):
    config_path = _render_config(tmp_path)
    runner = CliRunner()

    result = runner.invoke(main, ["build", str(config_path)])

    assert result.exit_code == 0, result.output
    assert os.path.islink(tmp_path / "link.txt")
    assert (tmp_path / "MyApp.lnk").is_file()


def test_validate_does_not_write_files(tmp_path):
    config_path = _render_config(tmp_path)
    runner = CliRunner()

    result = runner.invoke(main, ["validate", str(config_path)])

    assert result.exit_code == 0, result.output
    assert not (tmp_path / "link.txt").exists()
    assert not (tmp_path / "MyApp.lnk").exists()


def test_build_fails_on_conflict_without_force(tmp_path):
    config_path = _render_config(tmp_path)
    (tmp_path / "link.txt").write_text("already here")
    runner = CliRunner()

    result = runner.invoke(main, ["build", str(config_path)])

    assert result.exit_code != 0


def test_build_force_overwrites(tmp_path):
    config_path = _render_config(tmp_path)
    (tmp_path / "link.txt").write_text("already here")
    runner = CliRunner()

    result = runner.invoke(main, ["build", str(config_path), "--force"])

    assert result.exit_code == 0, result.output
    assert os.path.islink(tmp_path / "link.txt")


def test_init_writes_example_config(tmp_path):
    runner = CliRunner()
    config_path = tmp_path / "links.yaml"

    result = runner.invoke(main, ["init", str(config_path)])

    assert result.exit_code == 0, result.output
    assert config_path.is_file()


def test_doctor_runs(tmp_path):
    runner = CliRunner()
    result = runner.invoke(main, ["doctor"])
    assert result.exit_code == 0, result.output
