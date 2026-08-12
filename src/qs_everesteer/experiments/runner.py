"""Persisted, failure-retaining temporal experiment runner."""
from __future__ import annotations

import time
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pandas as pd
import psutil
import yaml

from qs_everesteer.api_schemas.pages import RaceDecision
from qs_everesteer.fsutil import atomic_write_json
from qs_everesteer.models import create_model
from qs_everesteer.models.registry import ModelRegistry
from qs_everesteer.paths import ensure_dir, find_repo_root
from qs_everesteer.validation.temporal import temporal_cv


class ExperimentRunner:
    """Config -> model -> OOF -> metrics -> artefacts -> immutable manifest."""

    def __init__(self, repo_root: str | Path | None = None) -> None:
        self.repo_root = Path(repo_root) if repo_root else find_repo_root()

    def run(self, config_path: str | Path | dict[str, Any]) -> dict[str, Any]:
        config = self._config(config_path)
        run_id = str(config.get("run_id") or f"run-{uuid.uuid4().hex[:12]}")
        run_dir = ensure_dir(self.repo_root / "runs" / "experiments" / run_id)
        started = time.perf_counter()
        manifest = {
            "run_id": run_id, "status": "RUNNING",
            "started_at": datetime.now(UTC).isoformat(), "config": config,
        }
        atomic_write_json(run_dir / "run.json", manifest)
        (run_dir / "config.resolved.yaml").write_text(
            yaml.safe_dump(config, sort_keys=True), encoding="utf-8"
        )
        metrics: dict[str, Any] = {}
        decision = RaceDecision.PENDING
        try:
            data = pd.read_parquet(config["data_path"])
            target = config.get("target", "target_everest_20")
            exped = config.get("exped_col", "exped")
            features = config.get("features") or [
                c for c in data.columns if str(c).startswith("feature_")
            ]
            model_spec = config.get("model", "ridge")
            if isinstance(model_spec, str):
                model_name, params = model_spec, dict(config.get("params") or {})
            else:
                model_name = model_spec["name"]
                params = dict(model_spec.get("params") or {})
            factory = lambda: create_model(model_name, **params)
            oof, metrics = temporal_cv(
                data, factory, features=features, target=target, exped_col=exped,
                profile=config.get("profile", "R1"),
            )
            oof.to_parquet(run_dir / "oof.parquet", index=False)
            final_model = factory().fit(data[features], data[target])
            model_meta = ModelRegistry(self.repo_root).save(
                final_model, model_id=run_id, training_data_hash=config.get("data_hash")
            )
            decision = RaceDecision.PROMOTE_EXPLORATION
            manifest.update(
                status="COMPLETED", model_id=run_id, model_metadata=model_meta,
                completed_at=datetime.now(UTC).isoformat(),
            )
        except Exception as exc:  # noqa: BLE001 — failed runs must retain all evidence
            manifest.update(
                status="FAILED", error_type=type(exc).__name__, error=str(exc),
                completed_at=datetime.now(UTC).isoformat(),
            )
            decision = (
                RaceDecision.FAILED_OOM if isinstance(exc, MemoryError)
                else RaceDecision.FAILED_TRAINING
            )
        elapsed = time.perf_counter() - started
        resources = {
            "runtime_seconds": elapsed,
            "rss_bytes": psutil.Process().memory_info().rss,
            "cpu_count": psutil.cpu_count(),
        }
        atomic_write_json(run_dir / "metrics.json", metrics)
        atomic_write_json(
            run_dir / "decision.json",
            {"decision": decision.value, "rationale": manifest.get("error") or "awaiting race"},
        )
        atomic_write_json(run_dir / "resource.json", resources)
        manifest["runtime_seconds"] = elapsed
        atomic_write_json(run_dir / "run.json", manifest)
        return manifest

    @staticmethod
    def _config(source: str | Path | dict[str, Any]) -> dict[str, Any]:
        if isinstance(source, dict):
            return dict(source)
        loaded = yaml.safe_load(Path(source).read_text(encoding="utf-8"))
        if not isinstance(loaded, dict):
            raise TypeError("experiment config must be a mapping")
        return loaded
