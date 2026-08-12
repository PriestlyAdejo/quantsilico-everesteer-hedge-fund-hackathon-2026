"""Central RaceDecision → human copy mapping (mirrors Figma humanize.ts)."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from qs_everesteer.api_schemas.pages import RaceDecision


class DecisionTone(StrEnum):
    GOOD = "good"
    WARN = "warn"
    MUTED = "muted"
    ERROR = "error"
    NEUTRAL = "neutral"


@dataclass(frozen=True)
class HumanDecision:
    label: str
    tone: DecisionTone
    code: RaceDecision


_DECISION_MAP: dict[RaceDecision, tuple[str, DecisionTone]] = {
    RaceDecision.PROMOTE_TOP_SCORE: (
        "Advance — best local score so far",
        DecisionTone.GOOD,
    ),
    RaceDecision.PROMOTE_DIVERSITY: (
        "Advance to next round — adds useful independent signal",
        DecisionTone.GOOD,
    ),
    RaceDecision.PROMOTE_EXPLORATION: (
        "Advance — this branch is worth more exploration",
        DecisionTone.GOOD,
    ),
    RaceDecision.KEEP_ENSEMBLE: (
        "Keep in the blend — contributes independent signal",
        DecisionTone.GOOD,
    ),
    RaceDecision.RETEST: (
        "Retest — evidence is not yet conclusive",
        DecisionTone.WARN,
    ),
    RaceDecision.RETIRE_DOMINATED: (
        "Stop exploring — another candidate is better on the same trade-offs",
        DecisionTone.MUTED,
    ),
    RaceDecision.RETIRE_SATURATED: (
        "Stop this branch — recent variants are no longer improving",
        DecisionTone.MUTED,
    ),
    RaceDecision.FAILED_OOM: (
        "Failed — ran out of memory",
        DecisionTone.ERROR,
    ),
    RaceDecision.FAILED_TRAINING: (
        "Failed — training error",
        DecisionTone.ERROR,
    ),
    RaceDecision.INVALID_INTEGRITY: (
        "Blocked — an integrity check failed",
        DecisionTone.ERROR,
    ),
    RaceDecision.INVALID_ID_ALIGNMENT: (
        "Blocked — prediction IDs do not match the current split",
        DecisionTone.ERROR,
    ),
    RaceDecision.PENDING: (
        "Pending — awaiting evidence",
        DecisionTone.NEUTRAL,
    ),
}


def humanize_decision(code: RaceDecision | str) -> HumanDecision:
    """Return human label/tone for a race decision; raw code remains on `.code`."""
    decision = RaceDecision(code) if not isinstance(code, RaceDecision) else code
    mapped = _DECISION_MAP.get(decision)
    if mapped is None:
        return HumanDecision(label=str(decision), tone=DecisionTone.NEUTRAL, code=decision)
    label, tone = mapped
    return HumanDecision(label=label, tone=tone, code=decision)
