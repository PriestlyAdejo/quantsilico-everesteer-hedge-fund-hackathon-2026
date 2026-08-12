"""Stake-mode classification and allocation recommendations (never execute real txs)."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from qs_everesteer.contracts import StakeMode

# Figma API layer maps REAL_USDC ↔ StakeMode.REAL_USDC_OR_WALLET later.


@dataclass
class StakeClassification:
    mode: StakeMode
    confidence: str
    reasons: list[str] = field(default_factory=list)
    raw_signals: dict[str, Any] = field(default_factory=dict)
    human_only: bool = False

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["mode"] = self.mode.value
        # Convenience for later API mapping (Figma REAL_USDC).
        d["figma_stake_mode"] = (
            "REAL_USDC" if self.mode is StakeMode.REAL_USDC_OR_WALLET else self.mode.value
        )
        return d


@dataclass
class AllocationRecommendation:
    mode: StakeMode
    executable_automatically: bool
    slots: list[dict[str, Any]] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    requires_human: bool = False

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["mode"] = self.mode.value
        return d


def classify_staking(payload: dict[str, Any] | None) -> StakeClassification:
    """
    Classify VIRTUAL_EVENT_BALANCE | REAL_USDC_OR_WALLET | NO_STAKING | UNKNOWN.

    Uses only explicit signals from event staking / capability payloads.
    Never invents balances or treats missing data as zero.
    """
    if not payload:
        return StakeClassification(
            mode=StakeMode.UNKNOWN,
            confidence="none",
            reasons=["no staking payload"],
            human_only=True,
        )

    signals: dict[str, Any] = {}
    reasons: list[str] = []

    # Normalize nested shapes: get_event_staking summary, inspect raw.staking, etc.
    staking = payload.get("staking") if isinstance(payload.get("staking"), dict) else payload
    if not isinstance(staking, dict):
        return StakeClassification(
            mode=StakeMode.UNKNOWN,
            confidence="low",
            reasons=["staking payload is not an object"],
            human_only=True,
        )

    for key in (
        "staking_armed",
        "stake_window_open",
        "deposit_address",
        "principal_micro",
        "forwarder_balance_micro",
        "min_stake_micro",
        "mode",
        "stake_mode",
        "currency",
        "asset",
        "chain",
        "wallet",
        "virtual_balance",
        "event_balance",
        "enabled",
        "available",
    ):
        if key in staking:
            signals[key] = staking.get(key)

    # Explicit mode strings
    explicit = str(staking.get("mode") or staking.get("stake_mode") or "").strip().upper()
    if explicit in {
        StakeMode.VIRTUAL_EVENT_BALANCE.value,
        "VIRTUAL",
        "VIRTUAL_BALANCE",
        "EVENT_BALANCE",
    }:
        return StakeClassification(
            mode=StakeMode.VIRTUAL_EVENT_BALANCE,
            confidence="high",
            reasons=[f"explicit mode={explicit}"],
            raw_signals=signals,
            human_only=False,
        )
    if explicit in {
        StakeMode.REAL_USDC_OR_WALLET.value,
        "REAL_USDC",
        "USDC",
        "WALLET",
        "ON_CHAIN",
    }:
        return StakeClassification(
            mode=StakeMode.REAL_USDC_OR_WALLET,
            confidence="high",
            reasons=[f"explicit mode={explicit}"],
            raw_signals=signals,
            human_only=True,
        )
    if explicit in {StakeMode.NO_STAKING.value, "NONE", "DISABLED", "OFF"}:
        return StakeClassification(
            mode=StakeMode.NO_STAKING,
            confidence="high",
            reasons=[f"explicit mode={explicit}"],
            raw_signals=signals,
            human_only=False,
        )

    # Availability flags
    if staking.get("available") is False or staking.get("enabled") is False:
        return StakeClassification(
            mode=StakeMode.NO_STAKING,
            confidence="medium",
            reasons=["staking marked unavailable/disabled"],
            raw_signals=signals,
            human_only=False,
        )

    deposit = staking.get("deposit_address")
    currency = str(staking.get("currency") or staking.get("asset") or "").upper()
    chain = staking.get("chain") or staking.get("wallet")
    principal = staking.get("principal_micro")
    forwarder = staking.get("forwarder_balance_micro")
    virtual = staking.get("virtual_balance")
    event_bal = staking.get("event_balance")

    real_signals = [
        deposit not in (None, "", 0),
        currency in {"USDC", "USD"},
        chain not in (None, "", False),
        principal not in (None,),
        forwarder not in (None,),
        bool(staking.get("staking_armed")),
    ]
    virtual_signals = [
        virtual not in (None,),
        event_bal not in (None,),
        "virtual" in str(staking.get("type") or "").lower(),
        "event_balance" in staking,
    ]

    if any(real_signals) and not any(virtual_signals):
        reasons.append("on-chain / USDC / deposit signals present")
        return StakeClassification(
            mode=StakeMode.REAL_USDC_OR_WALLET,
            confidence="medium" if sum(bool(x) for x in real_signals) >= 2 else "low",
            reasons=reasons,
            raw_signals=signals,
            human_only=True,
        )

    if any(virtual_signals) and not any(real_signals):
        reasons.append("virtual / event-balance signals present")
        return StakeClassification(
            mode=StakeMode.VIRTUAL_EVENT_BALANCE,
            confidence="medium",
            reasons=reasons,
            raw_signals=signals,
            human_only=False,
        )

    if any(real_signals) and any(virtual_signals):
        reasons.append("mixed virtual and real-money signals — refusing to auto-classify as virtual")
        return StakeClassification(
            mode=StakeMode.UNKNOWN,
            confidence="low",
            reasons=reasons,
            raw_signals=signals,
            human_only=True,
        )

    if not signals:
        return StakeClassification(
            mode=StakeMode.UNKNOWN,
            confidence="none",
            reasons=["empty staking signals"],
            human_only=True,
        )

    return StakeClassification(
        mode=StakeMode.UNKNOWN,
        confidence="low",
        reasons=["insufficient signals to classify"],
        raw_signals=signals,
        human_only=True,
    )


def recommend_allocations(
    classification: StakeClassification,
    *,
    model_ids: list[str] | None = None,
    risk_profile: str = "aggressive",
    max_slots: int | None = None,
    autopilot_virtual: bool = True,
) -> AllocationRecommendation:
    """
    Recommend stake allocations. Never executes wallet / chain transactions.

    Real-money modes are always human-only regardless of profile.
    """
    models = list(model_ids or [])
    notes: list[str] = []
    slots: list[dict[str, Any]] = []

    if classification.mode is StakeMode.NO_STAKING:
        return AllocationRecommendation(
            mode=classification.mode,
            executable_automatically=False,
            slots=[],
            notes=["staking not available for this event"],
            requires_human=False,
        )

    if classification.mode is StakeMode.UNKNOWN:
        return AllocationRecommendation(
            mode=classification.mode,
            executable_automatically=False,
            slots=[],
            notes=["stake mode UNKNOWN — no automatic allocation"],
            requires_human=True,
        )

    if classification.mode is StakeMode.REAL_USDC_OR_WALLET:
        notes.append("REAL_USDC_OR_WALLET requires explicit human action")
        notes.append("no wallet transaction will be constructed or broadcast by this module")
        for mid in models[: (max_slots or len(models) or 0)]:
            slots.append(
                {
                    "model_id": mid,
                    "suggested_weight": None,
                    "suggested_micro": None,
                    "note": "human must confirm amount and sign",
                }
            )
        return AllocationRecommendation(
            mode=classification.mode,
            executable_automatically=False,
            slots=slots,
            notes=notes,
            requires_human=True,
        )

    # VIRTUAL_EVENT_BALANCE
    if not autopilot_virtual:
        notes.append("virtual autopilot disabled by profile")
        return AllocationRecommendation(
            mode=classification.mode,
            executable_automatically=False,
            slots=[],
            notes=notes,
            requires_human=True,
        )

    n = len(models)
    limit = max_slots if max_slots is not None else n
    chosen = models[:limit]
    if not chosen:
        notes.append("no models provided for virtual allocation recommendation")
        return AllocationRecommendation(
            mode=classification.mode,
            executable_automatically=False,
            slots=[],
            notes=notes,
            requires_human=False,
        )

    if risk_profile == "aggressive":
        # Concentrate on champion first, then taper.
        weights = _aggressive_weights(len(chosen))
    else:
        weights = [1.0 / len(chosen)] * len(chosen)

    for mid, w in zip(chosen, weights, strict=True):
        slots.append(
            {
                "model_id": mid,
                "suggested_weight": w,
                "suggested_micro": None,  # UNKNOWN balance → no invented micro amounts
                "note": "virtual event balance recommendation only",
            }
        )
    notes.append("amounts left null when balance UNKNOWN — never invent balances")
    notes.append("recommendation only; execution is a separate explicit operator action")
    return AllocationRecommendation(
        mode=classification.mode,
        executable_automatically=True,
        slots=slots,
        notes=notes,
        requires_human=False,
    )


def _aggressive_weights(n: int) -> list[float]:
    if n <= 0:
        return []
    if n == 1:
        return [1.0]
    # Champion-heavy geometric taper.
    raw = [0.5 ** i for i in range(n)]
    total = sum(raw)
    return [x / total for x in raw]
