"""Dispatch a :class:`LinkSpec` to the right backend module."""

from __future__ import annotations

from types import ModuleType

from lnk_builder.core.errors import LnkBuilderError
from lnk_builder.core.result import BuildReport, LinkResult
from lnk_builder.core.spec import LinkSpec
from lnk_builder.core.types import LinkType


def _load_registry() -> dict[LinkType, ModuleType]:
    # Imported lazily so importing lnk_builder never requires the optional
    # pylnk3/mac_alias dependencies unless that backend is actually used.
    from lnk_builder.backends import alias, hardlink, junction, lnk, symlink

    return {
        LinkType.SYMLINK: symlink,
        LinkType.HARDLINK: hardlink,
        LinkType.JUNCTION: junction,
        LinkType.LNK: lnk,
        LinkType.ALIAS: alias,
    }


def build_link(spec: LinkSpec, *, dry_run: bool = False) -> LinkResult:
    """Create the single link described by ``spec``.

    On any :class:`~lnk_builder.core.errors.LnkBuilderError` this returns a
    failed :class:`LinkResult` instead of raising, so callers (notably
    :func:`build_all`) can decide whether to stop or continue. Programming
    errors (anything not an ``LnkBuilderError``) still propagate.
    """

    backend = _load_registry()[spec.type]

    if dry_run:
        try:
            backend.validate(spec)
        except LnkBuilderError as exc:
            return LinkResult(
                spec=spec,
                ok=False,
                link_path=spec.link_path,
                error=exc,
                message=str(exc),
                dry_run=True,
            )
        return LinkResult(
            spec=spec,
            ok=True,
            link_path=spec.link_path,
            message="validated (dry run, nothing written)",
            dry_run=True,
        )

    try:
        return backend.create(spec)
    except LnkBuilderError as exc:
        return LinkResult(
            spec=spec, ok=False, link_path=spec.link_path, error=exc, message=str(exc)
        )


def build_all(
    specs: list[LinkSpec], *, continue_on_error: bool = False, dry_run: bool = False
) -> BuildReport:
    """Create every link in ``specs``.

    By default the first failure stops the batch; pass
    ``continue_on_error=True`` to attempt every spec regardless and collect
    every result.
    """

    report = BuildReport()
    for spec in specs:
        result = build_link(spec, dry_run=dry_run)
        report.results.append(result)
        if not result.ok and not continue_on_error:
            break
    return report


__all__ = ["build_link", "build_all"]
