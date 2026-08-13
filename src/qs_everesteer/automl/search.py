"""Compute-bounded family discovery, tuning, and diversity challengers."""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from qs_everesteer.experiments.runner import ExperimentRunner
from qs_everesteer.fsutil import atomic_write_json, read_json
from qs_everesteer.paths import ensure_dir, find_repo_root

RESEARCH_SEQUENCE = (
    "OFFICIAL_BASELINE", "FAMILY_R0", "PROMOTE_R1", "TUNE_R2",
    "DIVERSITY_R1", "PROMOTE_R2_R3", "OOF_STACK", "CHAMPION",
)

FAMILY_SPECS: dict[str, dict[str, Any]] = {
    "reference_lgbm": {"n_estimators": 80},
    "lgbm": {"n_estimators": 100, "num_leaves": 15},
    "xgboost": {"n_estimators": 100, "max_depth": 4},
    "catboost": {"iterations": 100, "depth": 5},
    "extra_trees": {"n_estimators": 80, "max_depth": 7},
    "ridge": {"alpha": 10.0},
    "shallow_mlp": {"hidden_layer_sizes": (32,), "max_iter": 100},
}

ADVANCED_SPECS: dict[str, dict[str, Any]] = {
    "tabular_hist": {"max_iter": 100, "max_leaf_nodes": 15},
    "realmlp_style": {"hidden_layer_sizes": (48, 24), "max_iter": 100},
    "feature_bin": {"n_bins": 12, "max_iter": 100},
}

TUNING_GRIDS: dict[str, tuple[dict[str, Any], ...]] = {
    "lgbm": (
        {"n_estimators": 180, "num_leaves": 15, "learning_rate": 0.03},
        {"n_estimators": 220, "num_leaves": 31, "learning_rate": 0.02},
    ),
    "reference_lgbm": ({"n_estimators": 180},),
    "xgboost": (
        {"n_estimators": 180, "max_depth": 4, "learning_rate": 0.03},
        {"n_estimators": 220, "max_depth": 6, "learning_rate": 0.02},
    ),
    "catboost": (
        {"iterations": 180, "depth": 5, "learning_rate": 0.03},
        {"iterations": 220, "depth": 7, "learning_rate": 0.02},
    ),
    "extra_trees": (
        {"n_estimators": 180, "max_depth": 7, "max_features": 0.7},
        {"n_estimators": 220, "max_depth": 10, "max_features": 0.9},
    ),
    "ridge": ({"alpha": 1.0}, {"alpha": 30.0}),
    "shallow_mlp": (
        {"hidden_layer_sizes": (32,), "alpha": 0.01, "max_iter": 160},
        {"hidden_layer_sizes": (64, 32), "alpha": 0.03, "max_iter": 160},
    ),
}

RIDGE_ALPHA_GRID = (1.0, 30.0, 300.0, 3_000.0, 30_000.0)


@dataclass(frozen=True)
class SearchTrial:
    run_id: str
    kind: str
    family: str
    profile: str
    params: dict[str, Any]
    parent_run_id: str | None = None

    def config(self, *, data_path: str, target: str) -> dict[str, Any]:
        return {
            "run_id": self.run_id, "search_kind": self.kind,
            "parent_run_id": self.parent_run_id, "data_path": data_path,
            "target": target, "profile": self.profile,
            "model": {"name": self.family, "params": self.params},
        }


class AutoMLSearch:
    """Create and optionally execute deterministic, bounded trial sets."""

    def __init__(self, repo_root: str | Path | None = None) -> None:
        self.repo_root = Path(repo_root) if repo_root else find_repo_root()
        self.runner = ExperimentRunner(self.repo_root)

    @staticmethod
    def _id(kind: str, family: str, profile: str, params: dict[str, Any], parent: str | None) -> str:
        blob = json.dumps(
            {"kind": kind, "family": family, "profile": profile, "params": params, "parent": parent},
            sort_keys=True, default=str,
        )
        return f"{kind}-{family}-{hashlib.sha256(blob.encode()).hexdigest()[:10]}"

    def family_trials(self, *, profile: str = "R0", max_trials: int = 7) -> list[SearchTrial]:
        trials = []
        for family, params in list(FAMILY_SPECS.items())[:max(0, max_trials)]:
            trials.append(SearchTrial(self._id("family", family, profile, params, None), "family", family, profile, dict(params)))
        return trials

    def advanced_trials(self, *, profile: str = "R1", max_trials: int = 3) -> list[SearchTrial]:
        trials = []
        for family, params in list(ADVANCED_SPECS.items())[:max(0, max_trials)]:
            trials.append(SearchTrial(self._id("advanced", family, profile, params, None), "advanced", family, profile, dict(params)))
        return trials

    def ridge_trials(self, *, profile: str = "R1", max_trials: int = 5) -> list[SearchTrial]:
        """Build a bounded real-data Ridge regularisation sweep.

        The run prefix is deliberately distinct from the earlier synthetic family
        evidence so the adaptive controller cannot promote synthetic scores.
        """
        trials = []
        for alpha in RIDGE_ALPHA_GRID[:max(0, max_trials)]:
            params = {"alpha": alpha}
            run_id = self._id("ridge-real", "ridge", profile, params, None)
            trials.append(SearchTrial(run_id, "ridge-real", "ridge", profile, params))
        return trials

    def tune_trials(
        self, survivors: list[dict[str, Any]], *, profile: str = "R2", max_trials: int = 8,
    ) -> list[SearchTrial]:
        trials: list[SearchTrial] = []
        for survivor in survivors:
            family = str(survivor.get("family") or survivor.get("model") or "")
            parent = str(survivor.get("run_id") or survivor.get("candidate_id") or "") or None
            for params in TUNING_GRIDS.get(family, ()):
                trials.append(SearchTrial(self._id("tune", family, profile, params, parent), "tune", family, profile, dict(params), parent))
                if len(trials) >= max_trials:
                    return trials
        return trials

    def execute(
        self, trials: list[SearchTrial], *, data_path: str | Path, target: str = "target_everest_20",
    ) -> dict[str, Any]:
        results = []
        for trial in trials:
            manifest = self.runner.run(trial.config(data_path=str(Path(data_path)), target=target))
            results.append({
                "run_id": trial.run_id, "family": trial.family, "profile": trial.profile,
                "parent_run_id": trial.parent_run_id, "status": manifest.get("status"),
                "error": manifest.get("error"),
            })
        payload = {"sequence": list(RESEARCH_SEQUENCE), "trials": results}
        out = ensure_dir(self.repo_root / "runs" / "search") / "latest.json"
        atomic_write_json(out, payload)
        return {**payload, "manifest_path": str(out)}

    def survivor_records(self) -> list[dict[str, Any]]:
        """Read promoted R0/R1 outcomes and recover private families from run configs."""
        state_path = self.repo_root / "runs" / "state" / "research_state.json"
        state = read_json(state_path) if state_path.exists() else {}
        promoted = {
            str(row.get("candidate_id"))
            for row in state.get("race_outcomes", [])
            if str(row.get("decision", "")).startswith("PROMOTE_")
        }
        records = []
        for run_id in sorted(promoted):
            run_path = self.repo_root / "runs" / "experiments" / run_id / "run.json"
            if not run_path.exists():
                continue
            run = read_json(run_path)
            spec = (run.get("config") or {}).get("model")
            family = spec.get("name") if isinstance(spec, dict) else spec
            if family:
                records.append({"run_id": run_id, "family": family})
        return records
