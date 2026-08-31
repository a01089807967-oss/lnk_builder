"""Loading and validating the YAML/JSON link configuration file."""

from __future__ import annotations

import json
import os
from typing import Any

import yaml
from pydantic import BaseModel, ConfigDict, ValidationError

from lnk_builder.core.errors import ConfigError
from lnk_builder.core.spec import LinkSpec
from lnk_builder.core.types import TargetPlatform


class Defaults(BaseModel):
    model_config = ConfigDict(extra="forbid")

    overwrite: bool = False
    platform: TargetPlatform = TargetPlatform.AUTO


class Config(BaseModel):
    model_config = ConfigDict(extra="forbid")

    version: int = 1
    defaults: Defaults = Defaults()
    links: list[LinkSpec]


def _read_raw(path: str) -> dict[str, Any]:
    if not os.path.isfile(path):
        raise ConfigError(f"config file not found: '{path}'")

    with open(path, encoding="utf-8") as fh:
        text = fh.read()

    try:
        if path.endswith(".json"):
            return json.loads(text)
        return yaml.safe_load(text)
    except (yaml.YAMLError, json.JSONDecodeError) as exc:
        raise ConfigError(f"could not parse '{path}': {exc}") from exc


def _apply_defaults(raw: dict[str, Any]) -> dict[str, Any]:
    defaults = raw.get("defaults") or {}
    links = raw.get("links") or []
    merged_links = []
    for link in links:
        merged = {**defaults, **link}
        merged_links.append(merged)
    return {**raw, "links": merged_links}


def load_config(path: str) -> Config:
    """Load and validate a link configuration file.

    Values under ``defaults`` (``overwrite``, ``platform``) are merged
    into every entry in ``links`` that doesn't set them explicitly.
    """

    raw = _read_raw(path)
    if not isinstance(raw, dict):
        raise ConfigError(f"'{path}' must contain a YAML/JSON mapping at the top level")

    merged = _apply_defaults(raw)

    try:
        return Config.model_validate(merged)
    except ValidationError as exc:
        raise ConfigError(f"invalid configuration in '{path}':\n{exc}") from exc


__all__ = ["Config", "Defaults", "load_config"]
