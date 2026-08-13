"""Public-safe, versioned contracts shared by local and remote execution lanes.

These records deliberately contain references and hashes rather than credentials or
organiser data.  They are JSON-friendly so a task has the same immutable description
whether it runs locally, in WSL, or on an authenticated organiser backend.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import StrEnum
from typing import Any


class BackendLane(StrEnum):
    LOCAL_CPU = "LOCAL_CPU"
    LOCAL_NATIVE_GPU = "LOCAL_NATIVE_GPU"
    LOCAL_LINUX_JAX = "LOCAL_LINUX_JAX"
    EVERESTEER_BUILTIN = "EVERESTEER_BUILTIN"
    EVERESTEER_CUSTOM_GPU = "EVERESTEER_CUSTOM_GPU"
    RUNPOD_GPU = "RUNPOD_GPU"


class FundingSource(StrEnum):
    INCLUDED_CREDIT = "INCLUDED_CREDIT"
    USER_AUTHORISED_CREDIT_BALANCE = "USER_AUTHORISED_CREDIT_BALANCE"
    CASH_BILLING = "CASH_BILLING"
    UNKNOWN = "UNKNOWN"


class DataClassification(StrEnum):
    PUBLIC = "PUBLIC"
    SYNTHETIC = "SYNTHETIC"
    ORGANISER = "ORGANISER"


@dataclass(frozen=True)
class DataEgressPolicy:
    classification: DataClassification = DataClassification.ORGANISER
    third_party_data_egress_allowed: bool = False
    allowed_providers: tuple[BackendLane, ...] = (
        BackendLane.LOCAL_CPU,
        BackendLane.LOCAL_NATIVE_GPU,
        BackendLane.LOCAL_LINUX_JAX,
        BackendLane.EVERESTEER_BUILTIN,
        BackendLane.EVERESTEER_CUSTOM_GPU,
    )
    authority: str = "UNKNOWN"

    def permits(self, lane: BackendLane) -> bool:
        if lane not in self.allowed_providers:
            return False
        if lane == BackendLane.RUNPOD_GPU and self.classification == DataClassification.ORGANISER:
            return self.third_party_data_egress_allowed and self.authority != "UNKNOWN"
        return True


@dataclass(frozen=True)
class BudgetPolicy:
    allowed_funding_sources: tuple[FundingSource, ...] = (
        FundingSource.INCLUDED_CREDIT,
        FundingSource.USER_AUTHORISED_CREDIT_BALANCE,
    )
    maximum_authorised_spend: float = 0.0
    maximum_wall_time_seconds: int = 3600
    maximum_concurrent_workers: int = 1
    maximum_storage_gb_hours: float = 0.0
    idle_shutdown_seconds: int = 300
    checkpoint_reserve_seconds: int = 120

    def permits(self, funding: FundingSource, estimated_cost: float | None) -> bool:
        if funding not in self.allowed_funding_sources:
            return False
        if estimated_cost is None:
            return False
        return 0 <= estimated_cost <= self.maximum_authorised_spend


@dataclass(frozen=True)
class BackendCapabilities:
    lane: BackendLane
    available: bool
    verified_operations: tuple[str, ...] = ()
    frameworks: tuple[str, ...] = ()
    accelerator: str | None = None
    vram_gb: float | None = None
    queue_delay_seconds: float = 0.0
    throughput_units_per_second: float | None = None
    estimated_cost: float | None = 0.0
    funding_source: FundingSource = FundingSource.UNKNOWN
    reason: str | None = None

    def actionable(self, required_operations: tuple[str, ...] = ("submit", "status", "artifact")) -> bool:
        return self.available and set(required_operations).issubset(self.verified_operations)


@dataclass(frozen=True)
class ExperimentSpecV1:
    experiment_id: str
    dataset_fingerprint: str
    model_alias: str
    target: str
    transforms: tuple[str, ...] = ()
    validation: dict[str, Any] = field(default_factory=dict)
    resources: dict[str, Any] = field(default_factory=dict)
    seed: int = 0
    data_egress_policy: DataEgressPolicy = field(default_factory=DataEgressPolicy)
    schema_version: str = "ExperimentSpecV1"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class TaskSpecV1:
    task_id: str
    experiment_id: str
    operation: str
    priority: int = 4
    deadline: str | None = None
    attempt: int = 0
    maximum_attempts: int = 2
    dependencies: tuple[str, ...] = ()
    allowed_backends: tuple[BackendLane, ...] = tuple(BackendLane)
    required_framework: str | None = None
    minimum_vram_gb: float = 0.0
    schema_version: str = "TaskSpecV1"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ArtifactManifest:
    task_id: str
    attempt: int
    backend: BackendLane
    source_hash: str
    config_hash: str
    dataset_fingerprint: str
    environment_hash: str
    artifacts: dict[str, str] = field(default_factory=dict)
    metrics: dict[str, float] = field(default_factory=dict)
    provider_job_id: str | None = None
    runtime_seconds: float | None = None
    cost: float | None = None
    complete: bool = False
    schema_version: str = "ArtifactManifestV1"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
