"""Fail-closed classification of optional event mechanics."""

from __future__ import annotations

from typing import Any


def classify_optional_mechanics(capabilities: dict[str, Any] | None) -> dict[str, dict[str, Any]]:
    """Classify final selection and staking without inventing event mechanics."""
    caps = capabilities or {}
    return {
        "final_selection": _classify(caps.get("final_selection_available")),
        "staking": _classify(caps.get("staking_available")),
    }


def _classify(value: Any) -> dict[str, Any]:
    if value is True:
        return {"status": "AVAILABLE_HUMAN_AUTHORITY_REQUIRED", "available": True}
    if value is False:
        return {"status": "SKIPPED_NOT_APPLICABLE", "available": False}
    return {"status": "BLOCKED_CAPABILITY_UNKNOWN", "available": None}
