from __future__ import annotations

from lnk_builder.core import capabilities
from lnk_builder.core.types import TargetPlatform


def test_current_platform_is_consistent_with_capability_helpers():
    current = TargetPlatform.current()

    assert capabilities.is_windows() == (current is TargetPlatform.WINDOWS)
    assert capabilities.is_macos() == (current is TargetPlatform.MACOS)
    assert capabilities.is_linux() == (current is TargetPlatform.LINUX)


def test_non_windows_symlink_check_is_always_true():
    if not capabilities.is_windows():
        assert capabilities.can_create_windows_symlink() is True


def test_non_windows_has_no_junction_support():
    if not capabilities.is_windows():
        assert capabilities.has_winapi_junction_support() is False
