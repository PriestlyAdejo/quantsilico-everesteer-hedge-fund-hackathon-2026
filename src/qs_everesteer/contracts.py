from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class Provenance(StrEnum):
    OFFICIAL_EVENT_STATE = "OFFICIAL_EVENT_STATE"
    OFFICIAL_EVENT_DATA = "OFFICIAL_EVENT_DATA"
    OFFICIAL_PLATFORM_OBSERVATION = "OFFICIAL_PLATFORM_OBSERVATION"
    LOCAL_EXPERIMENT = "LOCAL_EXPERIMENT"
    SYNTHETIC_FIXTURE = "SYNTHETIC_FIXTURE"
    MANUALLY_RECORDED = "MANUALLY_RECORDED"


class CandidateStatus(StrEnum):
    SCAFFOLDED = "SCAFFOLDED"
    SMOKE_VALID = "SMOKE_VALID"
    SCOUT = "SCOUT"
    PROMISING = "PROMISING"
    CHALLENGER = "CHALLENGER"
    FRONTIER = "FRONTIER"
    CHAMPION = "CHAMPION"
    ENSEMBLE_MEMBER = "ENSEMBLE_MEMBER"
    SUBMISSION_READY = "SUBMISSION_READY"
    SUBMITTED_PRACTICE = "SUBMITTED_PRACTICE"
    SUBMITTED_LIVE = "SUBMITTED_LIVE"
    LIVE_PROVEN = "LIVE_PROVEN"
    RETIRED = "RETIRED"
    FAILED = "FAILED"
    INVALID = "INVALID"


class StakeMode(StrEnum):
    VIRTUAL_EVENT_BALANCE = "VIRTUAL_EVENT_BALANCE"
    REAL_USDC_OR_WALLET = "REAL_USDC_OR_WALLET"
    NO_STAKING = "NO_STAKING"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class EventCapabilities:
    sdk_version: str
    api_scope: str | None = None
    tournament: str | None = None
    validation_available: bool | None = None
    live_available: bool | None = None
    standings_available: bool | None = None
    staking_available: bool | None = None
    final_selection_available: bool | None = None
    server_compute_available: bool | None = None
    submission_cap: int | None = None
    current_round: str | None = None
    raw: dict[str, Any] = field(default_factory=dict)
