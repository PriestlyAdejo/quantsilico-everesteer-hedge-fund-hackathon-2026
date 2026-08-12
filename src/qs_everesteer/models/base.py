"""Common model protocol and reproducible metadata."""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from typing import Any, Protocol, runtime_checkable

import numpy as np


def stable_hash(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, default=str, separators=(",", ":"))
    return hashlib.sha256(payload.encode()).hexdigest()


def opaque_alias(private_name: str, params: dict[str, Any]) -> str:
    """Public identifier which intentionally does not disclose model family."""
    return f"candidate-{stable_hash({'name': private_name, 'params': params})[:12]}"


@dataclass
class ModelMetadata:
    private_name: str
    public_alias: str
    family: str
    params: dict[str, Any]
    params_hash: str
    training_data_hash: str | None = None
    artefact_hash: str | None = None
    created_at: str = field(
        default_factory=lambda: datetime.now(UTC).replace(microsecond=0).isoformat()
    )
    extra: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@runtime_checkable
class ResearchModel(Protocol):
    metadata: ModelMetadata

    def fit(
        self, X: Any, y: Any, sample_weight: Any | None = None
    ) -> ResearchModel: ...

    def predict(self, X: Any) -> np.ndarray: ...


class SklearnResearchModel:
    """Thin estimator adapter retaining private and public identities."""

    def __init__(
        self,
        estimator: Any,
        *,
        private_name: str,
        family: str,
        params: dict[str, Any],
        metadata_extra: dict[str, Any] | None = None,
    ) -> None:
        self.estimator = estimator
        self.metadata = ModelMetadata(
            private_name=private_name,
            public_alias=opaque_alias(private_name, params),
            family=family,
            params=dict(params),
            params_hash=stable_hash(params),
            extra=dict(metadata_extra or {}),
        )

    def fit(self, X: Any, y: Any, sample_weight: Any | None = None) -> SklearnResearchModel:
        kwargs = {"sample_weight": sample_weight} if sample_weight is not None else {}
        try:
            self.estimator.fit(X, y, **kwargs)
        except TypeError:
            self.estimator.fit(X, y)
        return self

    def predict(self, X: Any) -> np.ndarray:
        return np.asarray(self.estimator.predict(X), dtype=float)
