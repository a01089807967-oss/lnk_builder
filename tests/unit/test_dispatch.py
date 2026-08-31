from __future__ import annotations

from lnk_builder.core.dispatch import build_all, build_link
from lnk_builder.core.errors import LinkAlreadyExistsError
from lnk_builder.core.spec import SymlinkSpec


def _spec(tmp_path, name, target):
    return SymlinkSpec(type="symlink", target=str(target), link_path=str(tmp_path / name))


def test_build_link_dry_run_does_not_write(tmp_path):
    target = tmp_path / "target.txt"
    target.write_text("x")
    spec = _spec(tmp_path, "link.txt", target)

    result = build_link(spec, dry_run=True)

    assert result.ok
    assert result.dry_run
    assert not (tmp_path / "link.txt").exists()


def test_build_all_stops_at_first_failure_by_default(tmp_path):
    target = tmp_path / "target.txt"
    target.write_text("x")

    ok_spec = _spec(tmp_path, "ok.txt", target)
    (tmp_path / "conflict.txt").write_text("already here")
    fail_spec = _spec(tmp_path, "conflict.txt", target)
    unreached_spec = _spec(tmp_path, "unreached.txt", target)

    report = build_all([ok_spec, fail_spec, unreached_spec])

    assert len(report) == 2
    assert report.succeeded == [report.results[0]]
    assert isinstance(report.failed[0].error, LinkAlreadyExistsError)
    assert not (tmp_path / "unreached.txt").exists()


def test_build_all_continue_on_error_attempts_everything(tmp_path):
    target = tmp_path / "target.txt"
    target.write_text("x")

    ok_spec = _spec(tmp_path, "ok.txt", target)
    (tmp_path / "conflict.txt").write_text("already here")
    fail_spec = _spec(tmp_path, "conflict.txt", target)
    second_ok_spec = _spec(tmp_path, "ok2.txt", target)

    report = build_all([ok_spec, fail_spec, second_ok_spec], continue_on_error=True)

    assert len(report) == 3
    assert not report.ok
    assert len(report.succeeded) == 2
    assert len(report.failed) == 1
    assert (tmp_path / "ok2.txt").exists()
