"""Stake mode classification and recommendation safety."""

from __future__ import annotations

from qs_everesteer.contracts import StakeMode
from qs_everesteer.staking.classify import classify_staking, recommend_allocations


def test_classify_unknown_on_empty():
    c = classify_staking(None)
    assert c.mode is StakeMode.UNKNOWN
    assert c.human_only is True


def test_classify_virtual():
    c = classify_staking({"mode": "VIRTUAL_EVENT_BALANCE", "event_balance": 1000})
    assert c.mode is StakeMode.VIRTUAL_EVENT_BALANCE
    assert c.human_only is False


def test_classify_real_usdc_from_deposit():
    c = classify_staking(
        {
            "deposit_address": "0xabc",
            "currency": "USDC",
            "principal_micro": 1_000_000,
            "staking_armed": True,
        }
    )
    assert c.mode is StakeMode.REAL_USDC_OR_WALLET
    assert c.human_only is True
    assert c.to_dict()["figma_stake_mode"] == "REAL_USDC"


def test_classify_no_staking():
    c = classify_staking({"enabled": False})
    assert c.mode is StakeMode.NO_STAKING


def test_recommend_real_never_executable():
    c = classify_staking({"mode": "REAL_USDC"})
    rec = recommend_allocations(c, model_ids=["m1", "m2"], risk_profile="aggressive")
    assert rec.executable_automatically is False
    assert rec.requires_human is True
    assert all(s.get("suggested_micro") is None for s in rec.slots)


def test_recommend_virtual_weights_without_inventing_balance():
    c = classify_staking({"mode": "VIRTUAL", "virtual_balance": None})
    rec = recommend_allocations(
        c,
        model_ids=["champ", "chal1", "chal2"],
        risk_profile="aggressive",
        autopilot_virtual=True,
    )
    assert rec.executable_automatically is True
    assert rec.requires_human is False
    assert len(rec.slots) == 3
    assert abs(sum(s["suggested_weight"] for s in rec.slots) - 1.0) < 1e-9
    assert all(s["suggested_micro"] is None for s in rec.slots)


def test_mixed_signals_are_unknown():
    c = classify_staking(
        {
            "deposit_address": "0x1",
            "currency": "USDC",
            "virtual_balance": 10,
            "event_balance": 10,
        }
    )
    assert c.mode is StakeMode.UNKNOWN
    assert c.human_only is True
