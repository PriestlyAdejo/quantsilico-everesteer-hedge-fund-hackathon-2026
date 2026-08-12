"""Envelope, provenance, and action-result contracts mirroring Figma types.ts."""

from __future__ import annotations

from enum import StrEnum
from typing import Generic, Literal, TypeVar

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel

SCHEMA_VERSION = 2

T = TypeVar("T")


class ApiModel(BaseModel):
    """Shared base: camelCase JSON aliases, ignore unknown fields."""

    model_config = ConfigDict(
        populate_by_name=True,
        extra="ignore",
        alias_generator=to_camel,
    )


class Provenance(StrEnum):
    OFFICIAL_EVENT_STATE = "OFFICIAL_EVENT_STATE"
    OFFICIAL_EVENT_DATA = "OFFICIAL_EVENT_DATA"
    OFFICIAL_PLATFORM_OBSERVATION = "OFFICIAL_PLATFORM_OBSERVATION"
    LOCAL_EXPERIMENT = "LOCAL_EXPERIMENT"
    SYNTHETIC_FIXTURE = "SYNTHETIC_FIXTURE"
    MANUALLY_RECORDED = "MANUALLY_RECORDED"


class ProvenanceMeta(ApiModel):
    provenance: Provenance
    generated_at: str
    source_id: str | None = None
    event_snapshot_id: str | None = None


class DataEnvelope(ApiModel, Generic[T]):
    schema_version: int = Field(default=SCHEMA_VERSION)
    kind: str
    provenance: Provenance
    generated_at: str
    stale: bool
    source: str
    refresh_mode: Literal["push", "poll", "manual"] | None = None
    stale_after_seconds: int | None = None
    source_id: str | None = None
    event_snapshot_id: str | None = None
    data: T


class ActionResult(ApiModel):
    ok: bool
    message: str
    timestamp: str
    code: str | None = None
