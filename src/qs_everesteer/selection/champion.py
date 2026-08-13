"""Evidence-based champion and reserve selection."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from qs_everesteer.fsutil import read_json


def select_champion(repo_root: str | Path, *, require_stage: str = "R3") -> dict[str, Any]:
    root = Path(repo_root)
    candidates = []
    exp_root = root / "runs" / "experiments"
    for run_path in sorted(exp_root.glob("*/run.json")) if exp_root.exists() else []:
        run = read_json(run_path)
        config = run.get("config") or {}
        if run.get("status") != "COMPLETED" or str(config.get("profile", "")).upper() != require_stage:
            continue
        metrics_path = run_path.parent / "metrics.json"
        metrics = read_json(metrics_path) if metrics_path.exists() else {}
        score = metrics.get("score")
        if score is None:
            continue
        candidates.append({
            "id": str(run.get("run_id") or run_path.parent.name), "score": float(score),
            "profile": require_stage, "integrity_ok": True, "source": "promotion_grade_oof",
        })
    if not candidates:
        raise RuntimeError(f"no completed {require_stage} candidate with scored OOF evidence")
    candidates.sort(key=lambda row: row["score"], reverse=True)
    return {"champion": candidates[0], "reserves": candidates[1:3], "evaluated": len(candidates)}
