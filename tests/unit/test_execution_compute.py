from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

from qs_everesteer.execution.benchmark import autotune_from_latest
from qs_everesteer.execution.broker import ComputeBroker, WorkloadProfile
from qs_everesteer.execution.contracts import (
    BackendCapabilities,
    BackendLane,
    BudgetPolicy,
    DataClassification,
    DataEgressPolicy,
    FundingSource,
)
from qs_everesteer.fsutil import atomic_write_json
from qs_everesteer.jobs.model import JobKind, JobPriority
from qs_everesteer.jobs.queue import claim_next_job, enqueue

OPS = ("submit", "status", "artifact")


def cap(lane, speed, *, frameworks=("sklearn",), vram=None, available=True, cost=0.0,
        funding=FundingSource.INCLUDED_CREDIT, delay=0.0):
    return BackendCapabilities(
        lane=lane, available=available, verified_operations=OPS if available else (),
        frameworks=frameworks, vram_gb=vram, throughput_units_per_second=speed,
        estimated_cost=cost, funding_source=funding, queue_delay_seconds=delay,
    )


def policies(*, third_party=False, spend=10.0):
    allowed = tuple(BackendLane) if third_party else DataEgressPolicy().allowed_providers
    return (
        DataEgressPolicy(
            classification=DataClassification.ORGANISER,
            third_party_data_egress_allowed=third_party,
            allowed_providers=allowed,
            authority="EVENT_TERMS" if third_party else "UNKNOWN",
        ),
        BudgetPolicy(maximum_authorised_spend=spend),
    )


def test_priority_and_equal_priority_fifo(tmp_path: Path):
    first = enqueue(JobKind.TRAIN, {}, repo_root=tmp_path, priority=JobPriority.AUTOML)
    urgent = enqueue(JobKind.INFER, {}, repo_root=tmp_path, priority=JobPriority.LIVE_INTEGRITY)
    third = enqueue(JobKind.VALIDATE, {}, repo_root=tmp_path, priority=JobPriority.AUTOML)
    assert claim_next_job("w1", tmp_path).id == urgent
    assert claim_next_job("w2", tmp_path).id == first
    assert claim_next_job("w3", tmp_path).id == third


def test_dependency_is_not_claimed_early(tmp_path: Path):
    parent = enqueue(JobKind.TRAIN, {}, repo_root=tmp_path, priority=JobPriority.PRACTICE)
    enqueue(JobKind.INFER, {}, repo_root=tmp_path, priority=JobPriority.LIVE_INTEGRITY,
            dependencies=[parent])
    assert claim_next_job("w", tmp_path).id == parent


def test_broker_decisions_vary_with_measurements_and_framework():
    egress, budget = policies()
    broker = ComputeBroker()
    slow_gpu = [cap(BackendLane.LOCAL_CPU, 20), cap(BackendLane.LOCAL_NATIVE_GPU, 5, vram=8)]
    fast_gpu = [cap(BackendLane.LOCAL_CPU, 20), cap(BackendLane.LOCAL_NATIVE_GPU, 100, vram=8)]
    assert broker.select(WorkloadProfile(20), slow_gpu, egress_policy=egress,
                         budget_policy=budget).lane == BackendLane.LOCAL_CPU
    assert broker.select(WorkloadProfile(1000), fast_gpu, egress_policy=egress,
                         budget_policy=budget).lane == BackendLane.LOCAL_NATIVE_GPU
    neural = [cap(BackendLane.LOCAL_CPU, 20),
              cap(BackendLane.LOCAL_LINUX_JAX, 200, frameworks=("jax",), vram=8)]
    assert broker.select(WorkloadProfile(500, required_framework="jax"), neural,
                         egress_policy=egress, budget_policy=budget).lane == BackendLane.LOCAL_LINUX_JAX


def test_runpod_egress_and_unknown_funding_fail_closed():
    broker = ComputeBroker()
    runpod = cap(BackendLane.RUNPOD_GPU, 1000, vram=80, cost=1.0)
    egress, budget = policies()
    denied = broker.select(WorkloadProfile(10_000), [runpod], egress_policy=egress,
                           budget_policy=budget)
    assert denied.status == "BLOCKED" and "egress" in denied.reason
    egress, budget = policies(third_party=True)
    unknown = cap(BackendLane.RUNPOD_GPU, 1000, vram=80, cost=1.0,
                  funding=FundingSource.UNKNOWN)
    denied = broker.select(WorkloadProfile(10_000), [unknown], egress_policy=egress,
                           budget_policy=budget)
    assert denied.status == "BLOCKED" and "funding" in denied.reason


def test_remote_selection_and_deadline_rejection():
    egress, budget = policies(third_party=True)
    broker, now = ComputeBroker(), datetime(2026, 8, 13, tzinfo=UTC)
    remote = cap(BackendLane.RUNPOD_GPU, 1000, vram=80, cost=1.0, delay=30)
    selected = broker.select(
        WorkloadProfile(100_000, deadline=(now + timedelta(minutes=5)).isoformat()),
        [cap(BackendLane.LOCAL_CPU, 10), remote], egress_policy=egress,
        budget_policy=budget, now=now)
    assert selected.lane == BackendLane.RUNPOD_GPU
    blocked = broker.select(
        WorkloadProfile(100_000, deadline=(now + timedelta(seconds=20)).isoformat()),
        [remote], egress_policy=egress, budget_policy=budget, now=now)
    assert blocked.status == "BLOCKED" and "deadline" in blocked.reason


def test_oom_reroutes_and_no_backend_blocks():
    egress, budget = policies()
    decision = ComputeBroker().select(
        WorkloadProfile(1000, minimum_vram_gb=12),
        [cap(BackendLane.LOCAL_NATIVE_GPU, 200, vram=8),
         cap(BackendLane.EVERESTEER_CUSTOM_GPU, 300, vram=40, cost=2.0)],
        egress_policy=egress, budget_policy=budget)
    assert decision.lane == BackendLane.EVERESTEER_CUSTOM_GPU
    assert "VRAM" in decision.rejected[BackendLane.LOCAL_NATIVE_GPU.value]
    blocked = ComputeBroker().select(
        WorkloadProfile(1), [cap(BackendLane.LOCAL_CPU, 1, available=False)],
        egress_policy=egress, budget_policy=budget)
    assert blocked.status == "BLOCKED" and blocked.lane is None


def test_autotune_uses_real_passing_evidence(tmp_path: Path):
    path = tmp_path / "runs" / "benchmarks" / "latest.json"
    atomic_write_json(
        path,
        {
            "family": "xgboost",
            "profile": "tiny",
            "records": [
                {"lane": "LOCAL_CPU", "status": "PASSED", "steady_state_seconds": 2.0},
                {
                    "lane": "LOCAL_NATIVE_GPU",
                    "status": "PASSED",
                    "steady_state_seconds": 0.5,
                },
            ],
        },
    )
    result = autotune_from_latest(tmp_path)
    assert result["status"] == "SELECTED"
    assert result["lane"] == "LOCAL_NATIVE_GPU"
