"""Backend for Windows ``.lnk`` shortcut files.

Fully cross-platform: ``pylnk3`` builds and writes the binary ``.lnk``
format in pure Python, without any Windows API calls, so this backend
works the same way on Linux, macOS and Windows.
"""

from __future__ import annotations

from lnk_builder.core.errors import BackendUnavailableError, ConfigError
from lnk_builder.core.fsops import clear_link_path, ensure_parent_dir
from lnk_builder.core.result import LinkResult
from lnk_builder.core.spec import LnkSpec
from lnk_builder.utils.winpath import require_windows_path

try:
    import pylnk3
except ImportError:  # pragma: no cover - exercised only when extra not installed
    pylnk3 = None

_WINDOW_STYLES = {
    "Normal": "Normal",
    "Maximized": "Maximized",
    "Minimized": "Minimized",
}


def is_cross_platform_capable() -> bool:
    return True


def _require_pylnk3() -> None:
    if pylnk3 is None:  # pragma: no cover - exercised only when extra not installed
        raise BackendUnavailableError(
            "the 'lnk' link type requires the 'pylnk3' package. Install it with "
            "'pip install lnk_builder[lnk]' (or 'lnk_builder[all]')."
        )


def validate(spec: LnkSpec) -> None:
    _require_pylnk3()
    require_windows_path(spec.target, field="target")
    if spec.icon_location is not None:
        require_windows_path(spec.icon_location, field="icon_location")
    if spec.working_directory is not None:
        require_windows_path(spec.working_directory, field="working_directory")
    if spec.hotkey:
        _validate_hotkey(spec.hotkey)


def _validate_hotkey(hotkey: str) -> None:
    # pylnk3 only recognizes these three modifier names (SHIFT/CONTROL/ALT
    # — not "CTRL") and single alphanumeric/function keys; check upfront so
    # a typo fails fast with a clear message instead of pylnk3's
    # InvalidKeyException surfacing mid-write.
    parts = [p.strip().upper() for p in hotkey.split("+") if p.strip()]
    if len(parts) < 2:
        raise ConfigError(
            f"hotkey='{hotkey}' must combine at least one modifier with a key, "
            "e.g. 'CONTROL+ALT+F'"
        )
    allowed_modifiers = {"CONTROL", "ALT", "SHIFT"}
    modifiers, key = parts[:-1], parts[-1]
    unknown = [m for m in modifiers if m not in allowed_modifiers]
    if unknown:
        raise ConfigError(
            f"hotkey='{hotkey}' has unknown modifier(s) {unknown}; pylnk3 only "
            "recognizes CONTROL, ALT and SHIFT (not CTRL)"
        )
    if key not in pylnk3._KEY_CODES:
        raise ConfigError(f"hotkey='{hotkey}' has an unrecognized key '{key}'")


def create(spec: LnkSpec) -> LinkResult:
    validate(spec)

    clear_link_path(spec.link_path, overwrite=spec.overwrite)
    ensure_parent_dir(spec.link_path)

    shortcut = pylnk3.for_file(
        spec.target,
        arguments=spec.arguments,
        description=spec.description,
        icon_file=spec.icon_location,
        icon_index=spec.icon_index,
        work_dir=spec.working_directory,
        window_mode=_WINDOW_STYLES[spec.window_style],
    )
    if spec.hotkey:
        shortcut.hot_key = spec.hotkey

    shortcut.save(spec.link_path)

    return LinkResult(spec=spec, ok=True, link_path=spec.link_path, message=".lnk shortcut created")


__all__ = ["create", "validate", "is_cross_platform_capable"]
