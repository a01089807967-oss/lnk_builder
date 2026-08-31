"""Small filesystem helpers shared by dispatch and the backends."""

from __future__ import annotations

import os
import shutil

from lnk_builder.core.errors import LinkAlreadyExistsError


def clear_link_path(link_path: str, *, overwrite: bool) -> None:
    """Ensure ``link_path`` does not exist, honouring ``overwrite``.

    Raises :class:`LinkAlreadyExistsError` when something is already there
    and ``overwrite`` is False. Symlinks are checked with ``lexists`` so a
    dangling symlink is still treated as "existing".
    """

    if not os.path.lexists(link_path):
        return

    if not overwrite:
        raise LinkAlreadyExistsError(
            f"'{link_path}' already exists (pass overwrite: true / --force to replace it)"
        )

    if os.path.islink(link_path) or os.path.isfile(link_path):
        os.remove(link_path)
    elif os.path.isdir(link_path):
        shutil.rmtree(link_path)
    else:  # pragma: no cover - defensive, e.g. broken special files
        os.remove(link_path)


def ensure_parent_dir(link_path: str) -> None:
    """Create the parent directory of ``link_path`` if it doesn't exist."""

    parent = os.path.dirname(os.path.abspath(link_path))
    if parent:
        os.makedirs(parent, exist_ok=True)
