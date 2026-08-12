"""Shared domain primitives used across Research Console page DTOs."""

from __future__ import annotations

from enum import StrEnum
from typing import Literal

from qs_everesteer.api_schemas.envelope import ApiModel, ProvenanceMeta


class ConnectionState(StrEnum):
    LIVE = "LIVE"
    RECONNECTING = "RECONNECTING"
    DISCONNECTED = "DISCONNECTED"
    NOT_CONNECTED = "NOT_CONNECTED"


class JobStatus(StrEnum):
    RUNNING = "RUNNING"
    QUEUED = "QUEUED"
    PENDING = "PENDING"
    DONE = "DONE"
    FAILED = "FAILED"


class Job(ApiModel):
    id: str
    name: str
    type: str
    status: JobStatus
    device: str
    candidate: str | None = None
    started_at: str | None = None
    eta_seconds: int | None = None
    total_seconds: int | None = None
    progress: float | None = None
    queue_position: int | None = None


class MetricCardData(ProvenanceMeta):
    label: str
    value: str | int | float | None
    unit: str | None = None
    delta: str | None = None
    trend: Literal["up", "down", "flat"] | None = None
    warn: bool | None = None
    critical: bool | None = None
    term: str | None = None


class FlowState(StrEnum):
    WAITING = "waiting"
    READY = "ready"
    ACTIVE = "active"
    COMPLETE = "complete"
    ATTENTION = "attention"
    BLOCKED = "blocked"


class FlowNode(ApiModel):
    id: str
    label: str
    state: FlowState


class ScoringComponent(ApiModel):
    name: str
    weight: float | None
    value: float | None
    provided: bool


class CapabilityStatus(StrEnum):
    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"
    UNKNOWN = "unknown"
