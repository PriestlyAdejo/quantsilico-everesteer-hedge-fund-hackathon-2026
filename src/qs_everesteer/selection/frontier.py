"""Pareto selection for mixed maximize/minimize objectives."""
from __future__ import annotations

import math


def pareto_frontier(records: list[dict], objectives: list[tuple[str, str]]) -> list[dict]:
    for _name, direction in objectives:
        if direction not in {"max", "maximize", "min", "minimize"}:
            raise ValueError(f"invalid objective direction {direction!r}")

    def value(record, name, direction):
        raw = record.get(name)
        if raw is None or not math.isfinite(float(raw)):
            return float("-inf") if direction.startswith("max") else float("inf")
        return float(raw)

    def dominates(left, right):
        no_worse, strictly_better = True, False
        for name, direction in objectives:
            a, b = value(left, name, direction), value(right, name, direction)
            if direction.startswith("max"):
                no_worse &= a >= b
                strictly_better |= a > b
            else:
                no_worse &= a <= b
                strictly_better |= a < b
        return no_worse and strictly_better

    return [
        record for i, record in enumerate(records)
        if not any(dominates(other, record) for j, other in enumerate(records) if i != j)
    ]
