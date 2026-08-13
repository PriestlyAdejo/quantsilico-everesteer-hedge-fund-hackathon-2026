"""Deterministic, policy-first backend selection.

The broker never provisions infrastructure.  It chooses among already-probed
capability records and returns an auditable BLOCKED decision when none qualify.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime

from qs_everesteer.execution.contracts import (
    BackendCapabilities,
    BackendLane,
    BudgetPolicy,
    DataEgressPolicy,
)


@dataclass(frozen=True)
class WorkloadProfile:
    units: float
    required_framework: str | None = None
    minimum_vram_gb: float = 0.0
    required_operations: tuple[str, ...] = ("submit", "status", "artifact")
    deadline: str | None = None
    prefer_local_below_units: float = 100.0


@dataclass(frozen=True)
class BrokerDecision:
    status: str
    lane: BackendLane | None
    reason: str
    estimated_finish_seconds: float | None = None
    rejected: dict[str, str] = field(default_factory=dict)


class ComputeBroker:
    def select(
        self,
        workload: WorkloadProfile,
        capabilities: list[BackendCapabilities],
        *,
        egress_policy: DataEgressPolicy,
        budget_policy: BudgetPolicy,
        now: datetime | None = None,
    ) -> BrokerDecision:
        now = now or datetime.now(UTC)
        rejected: dict[str, str] = {}
        eligible: list[tuple[float, float, BackendCapabilities]] = []

        for cap in capabilities:
            lane = cap.lane.value
            if not cap.actionable(workload.required_operations):
                rejected[lane] = cap.reason or "required operations are not verified"
                continue
            if not egress_policy.permits(cap.lane):
                rejected[lane] = "data egress policy forbids this provider"
                continue
            if workload.required_framework and workload.required_framework not in cap.frameworks:
                rejected[lane] = f"framework {workload.required_framework} is not verified"
                continue
            if workload.minimum_vram_gb and (cap.vram_gb or 0.0) < workload.minimum_vram_gb:
                rejected[lane] = "insufficient VRAM; resize or reroute"
                continue
            remote = cap.lane in {
                BackendLane.EVERESTEER_BUILTIN,
                BackendLane.EVERESTEER_CUSTOM_GPU,
                BackendLane.RUNPOD_GPU,
            }
            if remote and not budget_policy.permits(cap.funding_source, cap.estimated_cost):
                rejected[lane] = "funding source or estimated cost is not authorised"
                continue
            speed = cap.throughput_units_per_second or 0.0
            if speed <= 0:
                rejected[lane] = "no measured matched-workload throughput"
                continue
            finish = cap.queue_delay_seconds + workload.units / speed
            if workload.deadline:
                deadline = datetime.fromisoformat(workload.deadline)
                if deadline.tzinfo is None:
                    deadline = deadline.replace(tzinfo=UTC)
                if finish > max(0.0, (deadline - now).total_seconds()):
                    rejected[lane] = "queue and runtime would miss the deadline"
                    continue
            local_bias = 0.0
            if workload.units <= workload.prefer_local_below_units and remote:
                local_bias = 1_000_000.0
            eligible.append((finish + local_bias, finish, cap))

        if not eligible:
            reason = "; ".join(f"{lane}: {why}" for lane, why in sorted(rejected.items()))
            return BrokerDecision("BLOCKED", None, reason or "no capabilities supplied", rejected=rejected)

        _, finish, selected = min(eligible, key=lambda item: (item[0], item[2].lane.value))
        return BrokerDecision(
            "SELECTED",
            selected.lane,
            "lowest policy-compliant matched end-to-end time",
            estimated_finish_seconds=finish,
            rejected=rejected,
        )
