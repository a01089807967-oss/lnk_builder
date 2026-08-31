"""Result objects returned by :mod:`lnk_builder.core.dispatch`."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from lnk_builder.core.spec import LinkSpec


@dataclass
class LinkResult:
    """Outcome of building a single :class:`LinkSpec`."""

    spec: LinkSpec
    ok: bool
    link_path: str
    message: str = ""
    error: BaseException | None = None
    dry_run: bool = False

    def __bool__(self) -> bool:
        return self.ok


@dataclass
class BuildReport:
    """Aggregate outcome of :func:`lnk_builder.core.dispatch.build_all`."""

    results: list[LinkResult] = field(default_factory=list)

    @property
    def succeeded(self) -> list[LinkResult]:
        return [r for r in self.results if r.ok]

    @property
    def failed(self) -> list[LinkResult]:
        return [r for r in self.results if not r.ok]

    @property
    def ok(self) -> bool:
        return all(r.ok for r in self.results)

    def __bool__(self) -> bool:
        return self.ok

    def __iter__(self):
        return iter(self.results)

    def __len__(self) -> int:
        return len(self.results)
