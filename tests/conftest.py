from __future__ import annotations

import sys

import pytest


@pytest.fixture
def windows_only():
    if sys.platform != "win32":
        pytest.skip("requires Windows")


@pytest.fixture
def not_windows():
    if sys.platform == "win32":
        pytest.skip("requires a non-Windows OS")
