"""Command-line interface: ``lnk-builder`` / ``python -m lnk_builder``."""

from __future__ import annotations

import sys

import click

from lnk_builder import __version__
from lnk_builder.config import load_config
from lnk_builder.core import capabilities
from lnk_builder.core.dispatch import build_all
from lnk_builder.core.errors import ConfigError
from lnk_builder.core.types import TargetPlatform

_EXAMPLE_CONFIG = """\
version: 1

defaults:
  overwrite: false
  platform: auto

links:
  - type: symlink
    target: /opt/app/bin/tool
    link_path: /usr/local/bin/tool

  # - type: hardlink
  #   target: /data/shared/report.csv
  #   link_path: /data/exports/report.csv

  # - type: junction
  #   target: C:\\Data\\Shared
  #   link_path: C:\\Users\\me\\Links\\Shared
  #   platform: windows

  # - type: lnk
  #   target: "C:\\\\Program Files\\\\MyApp\\\\app.exe"
  #   link_path: "C:\\\\Users\\\\me\\\\Desktop\\\\MyApp.lnk"
  #   arguments: "--start-minimized"
  #   description: "Launch MyApp"
  #   working_directory: "C:\\\\Program Files\\\\MyApp"
  #   icon_location: "C:\\\\Program Files\\\\MyApp\\\\app.exe"
  #   window_style: Normal

  # - type: alias
  #   target: /Applications/MyApp.app
  #   link_path: "/Users/me/Desktop/MyApp alias"
  #   volume_name: "Macintosh HD"
"""


@click.group()
@click.version_option(__version__, prog_name="lnk-builder")
def main() -> None:
    """lnk-builder — cross-platform link/shortcut builder."""


@main.command()
@click.argument("config_path", type=click.Path(exists=True, dir_okay=False))
@click.option("--force", is_flag=True, help="Overwrite every link_path, regardless of the config.")
@click.option("--dry-run", is_flag=True, help="Validate everything without writing any files.")
@click.option(
    "--continue-on-error",
    is_flag=True,
    help="Attempt every link even if an earlier one fails, instead of stopping at the first "
    "failure.",
)
def build(config_path: str, force: bool, dry_run: bool, continue_on_error: bool) -> None:
    """Create every link described in CONFIG_PATH."""

    try:
        config = load_config(config_path)
    except ConfigError as exc:
        raise click.ClickException(str(exc)) from exc

    specs = config.links
    if force:
        for spec in specs:
            spec.overwrite = True

    report = build_all(specs, continue_on_error=continue_on_error, dry_run=dry_run)

    for result in report:
        prefix = click.style("OK", fg="green") if result.ok else click.style("FAIL", fg="red")
        click.echo(f"[{prefix}] {result.spec.type.value}: {result.link_path} — {result.message}")

    if not report.ok:
        click.echo(f"\n{len(report.failed)} of {len(report)} link(s) failed.", err=True)
        sys.exit(1)

    click.echo(f"\n{len(report.succeeded)} link(s) built successfully.")


@main.command()
@click.argument("config_path", type=click.Path(exists=True, dir_okay=False))
def validate(config_path: str) -> None:
    """Validate CONFIG_PATH (and every link's preconditions) without creating anything."""

    try:
        config = load_config(config_path)
    except ConfigError as exc:
        raise click.ClickException(str(exc)) from exc

    report = build_all(config.links, continue_on_error=True, dry_run=True)
    for result in report:
        prefix = click.style("OK", fg="green") if result.ok else click.style("FAIL", fg="red")
        click.echo(f"[{prefix}] {result.spec.type.value}: {result.link_path} — {result.message}")

    if not report.ok:
        sys.exit(1)


@main.command()
@click.argument("config_path", type=click.Path(dir_okay=False), default="links.yaml")
@click.option("--force", is_flag=True, help="Overwrite CONFIG_PATH if it already exists.")
def init(config_path: str, force: bool) -> None:
    """Write an example configuration file to CONFIG_PATH."""

    import os

    if os.path.exists(config_path) and not force:
        raise click.ClickException(f"'{config_path}' already exists (pass --force to overwrite)")

    with open(config_path, "w", encoding="utf-8") as fh:
        fh.write(_EXAMPLE_CONFIG)

    click.echo(f"Wrote example configuration to '{config_path}'.")


@main.command()
def doctor() -> None:
    """Report what this OS/process can actually build."""

    current = TargetPlatform.current()
    click.echo(f"Current OS: {current.value}")
    click.echo("Cross-platform capable link types: lnk, alias (always available)")
    click.echo("Native-only link types: symlink, hardlink, junction")
    click.echo("")

    if current is TargetPlatform.WINDOWS:
        ok = capabilities.can_create_windows_symlink()
        status = click.style("yes", fg="green") if ok else click.style("no", fg="red")
        click.echo(f"Can create Windows symlinks (admin/Developer Mode): {status}")
        junction_ok = capabilities.has_winapi_junction_support()
        junction_status = (
            click.style("yes", fg="green")
            if junction_ok
            else click.style("no, will fall back to mklink", fg="yellow")
        )
        click.echo(f"Native junction support (_winapi.CreateJunction): {junction_status}")
    else:
        click.echo("symlink/hardlink: available for this OS's own targets only")
        click.echo("junction: only via the experimental descriptor fallback (see README)")

    click.echo(
        f"xattr support (for best-effort alias Finder flag): {capabilities.supports_xattr()}"
    )

    try:
        import pylnk3  # noqa: F401

        click.echo("pylnk3 (lnk backend): " + click.style("installed", fg="green"))
    except ImportError:
        click.echo("pylnk3 (lnk backend): " + click.style("NOT installed", fg="red"))

    try:
        import mac_alias  # noqa: F401

        click.echo("mac_alias (alias backend): " + click.style("installed", fg="green"))
    except ImportError:
        click.echo("mac_alias (alias backend): " + click.style("NOT installed", fg="red"))


if __name__ == "__main__":
    main()
