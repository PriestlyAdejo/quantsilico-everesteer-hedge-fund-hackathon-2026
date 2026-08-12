"""Model artefact registry backed by joblib and JSON metadata."""
from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

import joblib

from qs_everesteer.fsutil import atomic_write_json, read_json
from qs_everesteer.models.base import stable_hash
from qs_everesteer.paths import ensure_dir, find_repo_root


class ModelRegistry:
    def __init__(self, repo_root: str | Path | None = None) -> None:
        self.repo_root = Path(repo_root) if repo_root else find_repo_root()
        self.root = ensure_dir(self.repo_root / "artifacts" / "models")

    def save(
        self, model: Any, *, model_id: str | None = None,
        training_data_hash: str | None = None,
    ) -> dict[str, Any]:
        metadata = model.metadata
        candidate_id = model_id or metadata.public_alias
        folder = ensure_dir(self.root / candidate_id)
        artefact = folder / "model.joblib"
        joblib.dump(model, artefact)
        artefact_hash = hashlib.sha256(artefact.read_bytes()).hexdigest()
        metadata.training_data_hash = training_data_hash
        metadata.artefact_hash = artefact_hash
        payload = {
            **metadata.to_dict(), "model_id": candidate_id,
            "artefact_path": str(artefact), "metadata_hash": stable_hash(metadata.to_dict()),
        }
        atomic_write_json(folder / "metadata.json", payload)
        return payload

    def load(self, model_id: str):
        return joblib.load(self.root / model_id / "model.joblib")

    def metadata(self, model_id: str) -> dict[str, Any]:
        return read_json(self.root / model_id / "metadata.json")

    def list(self) -> list[dict[str, Any]]:
        return [
            read_json(path) for path in sorted(self.root.glob("*/metadata.json"))
        ]
