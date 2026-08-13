"""Local candidate inference and lineage-only packaging."""
from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

import pandas as pd

from qs_everesteer.data.fingerprint import fingerprint_dataset
from qs_everesteer.fsutil import atomic_write_json, read_json
from qs_everesteer.models.registry import ModelRegistry
from qs_everesteer.paths import ensure_dir


def infer_candidate(
    repo_root: str | Path, *, candidate_id: str, data_path: str | Path,
    output_path: str | Path | None = None,
) -> dict[str, Any]:
    root, source = Path(repo_root), Path(data_path)
    run_path = root / "runs" / "experiments" / candidate_id / "run.json"
    if not run_path.exists():
        raise FileNotFoundError(f"candidate run evidence not found: {candidate_id}")
    run = read_json(run_path)
    config = run.get("config") or {}
    frame = pd.read_parquet(source) if source.suffix.lower() == ".parquet" else pd.read_csv(source)
    features = config.get("features") or [c for c in frame if str(c).startswith("feature_")]
    if not features:
        raise ValueError("inference data has no configured feature columns")
    model = ModelRegistry(root).load(candidate_id)
    prediction = model.predict(frame[features])
    result = pd.DataFrame({"prediction": prediction})
    if "id" in frame:
        result.insert(0, "id", frame["id"].astype(str).values)
    if "exped" in frame:
        result.insert(1 if "id" in result else 0, "exped", frame["exped"].values)
    output = Path(output_path) if output_path else ensure_dir(root / "artifacts" / "predictions") / f"{candidate_id}.parquet"
    output.parent.mkdir(parents=True, exist_ok=True)
    result.to_parquet(output, index=False)
    digest = hashlib.sha256(output.read_bytes()).hexdigest()
    synthetic = "synthetic" in source.name.lower() or source.with_suffix(source.suffix + ".synthetic.json").exists()
    return {
        "candidate_id": candidate_id, "predictions_path": str(output),
        "prediction_sha256": digest, "input": fingerprint_dataset(source),
        "rows": len(result), "synthetic": synthetic,
    }


def package_candidate(
    repo_root: str | Path, *, candidate_id: str, predictions_path: str | Path,
) -> dict[str, Any]:
    root, predictions = Path(repo_root), Path(predictions_path)
    if not predictions.exists():
        raise FileNotFoundError(predictions)
    metadata = ModelRegistry(root).metadata(candidate_id)
    payload = {
        "schema_version": 1, "candidate_id": candidate_id,
        "model_artefact_sha256": metadata.get("artefact_hash"),
        "model_metadata_sha256": metadata.get("metadata_hash"),
        "predictions_path": str(predictions),
        "predictions_sha256": hashlib.sha256(predictions.read_bytes()).hexdigest(),
        "external_upload_performed": False,
    }
    out = ensure_dir(root / "artifacts" / "packages" / candidate_id) / "manifest.json"
    atomic_write_json(out, payload)
    return {**payload, "manifest_path": str(out)}
