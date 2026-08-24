"""Strict JSON input/output helpers."""
from __future__ import annotations

from dataclasses import asdict, is_dataclass
from fractions import Fraction
from math import isfinite
from pathlib import Path
from typing import Any, Mapping, Sequence
import json

import numpy as np

from .model import WWInstance, from_one_based, to_one_based


def load_json(path: str | Path) -> dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError("the input JSON document must be an object")
    return value


def _numeric_list(raw: Any, field: str) -> list[float]:
    if not isinstance(raw, (list, tuple)):
        raise ValueError(f"instance field '{field}' must be an array")
    out: list[float] = []
    for v in raw:
        if isinstance(v, bool) or not isinstance(v, (int, float, str)):
            raise ValueError(f"instance field '{field}' must contain numbers or numeric strings")
        out.append(float(Fraction(v)) if isinstance(v, str) else float(v))
    return out


def instance_from_mapping(value: Mapping[str, Any]) -> WWInstance:
    """Float instance.  Entries may be numbers or exact numeric strings
    (decimal or ``p/q``); strings are rounded to the nearest float here and
    read exactly by :func:`exact_instance_from_mapping`."""
    missing = [key for key in ("K", "q", "demand") if key not in value]
    if missing:
        raise ValueError(f"missing required instance fields: {', '.join(missing)}")
    return WWInstance.create(
        K=_numeric_list(value["K"], "K"),
        q=_numeric_list(value["q"], "q"),
        demand=_numeric_list(value["demand"], "demand"),
        floor=None if value.get("floor") is None else _numeric_list(value["floor"], "floor"),
        weights=None if value.get("weights") is None else _numeric_list(value["weights"], "weights"),
        semantic_mode=str(value.get("semantic_mode", "forced_source_graph")),
    )


def exact_instance_from_mapping(value: Mapping[str, Any]):
    """Exact rational instance.  Numeric strings are parsed as exact decimals
    or fractions (``"0.999999999"``, ``"1/3"``); plain JSON numbers convert
    exactly from their binary floating-point form.

    The exact layer decides the rational problem actually supplied: users
    with decimal data who require decimal semantics should pass strings.
    """
    from .exactcert import ExactInstance

    missing = [key for key in ("K", "q", "demand") if key not in value]
    if missing:
        raise ValueError(f"missing required instance fields: {', '.join(missing)}")

    def rats(raw: Any, field: str) -> list:
        if not isinstance(raw, (list, tuple)):
            raise ValueError(f"instance field '{field}' must be an array")
        out = []
        for v in raw:
            if isinstance(v, bool) or not isinstance(v, (int, float, str)):
                raise ValueError(
                    f"instance field '{field}' must contain numbers or numeric strings"
                )
            out.append(Fraction(v) if isinstance(v, str) else v)
        return out

    return ExactInstance.from_rationals(
        rats(value["K"], "K"),
        rats(value["q"], "q"),
        rats(value["demand"], "demand"),
        None if value.get("floor") is None else rats(value["floor"], "floor"),
        None if value.get("weights") is None else rats(value["weights"], "weights"),
        semantic_mode=str(value.get("semantic_mode", "forced_source_graph")),
    )


def path_from_public(value: Sequence[int]) -> tuple[int, ...]:
    return from_one_based(value)


def path_to_public(value: Sequence[int] | None) -> list[int] | None:
    return None if value is None else list(to_one_based(value))


def json_safe(value: Any) -> Any:
    if is_dataclass(value):
        return json_safe(asdict(value))
    if isinstance(value, Fraction):
        return f"{value.numerator}/{value.denominator}"
    if isinstance(value, np.ndarray):
        return [json_safe(v) for v in value.tolist()]
    if isinstance(value, np.generic):
        return json_safe(value.item())
    if isinstance(value, (tuple, list)):
        return [json_safe(v) for v in value]
    if isinstance(value, dict):
        return {str(k): json_safe(v) for k, v in value.items()}
    if isinstance(value, float):
        if isfinite(value):
            return value
        return "inf" if value > 0 else "-inf"
    return value


def dump_json(value: Any, path: str | Path | None = None) -> str:
    text = json.dumps(json_safe(value), indent=2, sort_keys=True, allow_nan=False) + "\n"
    if path is not None:
        Path(path).write_text(text, encoding="utf-8")
    return text
