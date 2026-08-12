"""Ensemble build / compare commands."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd
import typer

from qs_everesteer.cli_app.common import console, print_json, print_mutation_context, repo_root
from qs_everesteer.ensemble.blend import greedy_forward, persist_blend, rank_average
from qs_everesteer.fsutil import read_json
from qs_everesteer.paths import ensure_dir
from qs_everesteer.state.research import update_research_state
from qs_everesteer.validation.scoring import local_grouped_corr

ensemble_app = typer.Typer(help="Ensemble blending.", no_args_is_help=True)


def _collect_oof(root: Path) -> tuple[pd.DataFrame | None, np.ndarray | None]:
    """Stack OOF prediction columns from experiment runs when available."""
    exp_root = root / "runs" / "experiments"
    cols: dict[str, np.ndarray] = {}
    y_true: np.ndarray | None = None
    if not exp_root.is_dir():
        return None, None
    for run_dir in sorted(exp_root.iterdir()):
        oof_path = run_dir / "oof.parquet"
        if not oof_path.exists():
            continue
        try:
            df = pd.read_parquet(oof_path)
        except Exception:  # noqa: BLE001
            continue
        pred_col = None
        for name in ("prediction", "pred", "oof", "y_pred"):
            if name in df.columns:
                pred_col = name
                break
        if pred_col is None:
            numeric = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]
            pred_col = numeric[-1] if numeric else None
        if pred_col is None:
            continue
        cols[run_dir.name] = df[pred_col].to_numpy(dtype=float)
        if y_true is None:
            for tname in ("target", "target_everest_20", "y", "y_true"):
                if tname in df.columns:
                    y_true = df[tname].to_numpy(dtype=float)
                    break
    if not cols:
        return None, None
    return pd.DataFrame(cols), y_true


@ensemble_app.command("build")
def ensemble_build(
    strategy: str = typer.Option("rank_average", "--strategy", help="rank_average|greedy_forward"),
    out: Optional[Path] = typer.Option(None, "--out", help="Blend manifest path."),
) -> None:
    """Build a blend from available experiment OOF predictions."""
    root = repo_root()
    print_mutation_context(lane="practice", candidate="ensemble")
    preds, y_true = _collect_oof(root)
    if preds is None or preds.empty:
        console.print("[yellow]no OOF predictions found under runs/experiments/[/yellow]")
        print_json({"ok": False, "reason": "no_oof", "members": []})
        raise typer.Exit(code=1)

    strategy_norm = strategy.strip().lower()
    if strategy_norm == "rank_average":
        blended = rank_average(preds)
        result = {
            "strategy": "rank_average",
            "member_ids": list(preds.columns),
            "weights": [1.0 / len(preds.columns)] * len(preds.columns),
            "prediction": blended,
        }
    elif strategy_norm == "greedy_forward":
        if y_true is None:
            console.print("[red]greedy_forward requires OOF target column[/red]")
            raise typer.Exit(code=1)

        def _scorer(y, p):
            return local_grouped_corr(y, p)

        result = greedy_forward(preds, y_true, _scorer)
        result["strategy"] = "greedy_forward"
    else:
        console.print("[red]unknown strategy[/red]")
        raise typer.Exit(code=1)

    out_path = out or (ensure_dir(root / "artifacts" / "ensembles") / "blend.json")
    persist_blend(out_path, result, predictions=preds)

    def _mutate(state: dict) -> None:
        state["ensemble"] = {
            "members": result.get("member_ids") or [],
            "blend_id": out_path.stem,
            "strategy": result.get("strategy"),
        }

    update_research_state(_mutate, repo_root=root)
    print_json(
        {
            "ok": True,
            "path": str(out_path),
            "strategy": result.get("strategy"),
            "member_ids": result.get("member_ids"),
            "weights": result.get("weights"),
            "score": result.get("score"),
        }
    )


@ensemble_app.command("compare")
def ensemble_compare() -> None:
    """List persisted blend manifests under artifacts/ensembles/."""
    root = repo_root()
    ens_dir = root / "artifacts" / "ensembles"
    blends = []
    if ens_dir.is_dir():
        for path in sorted(ens_dir.glob("*.json")):
            try:
                data = read_json(path)
            except Exception:  # noqa: BLE001
                continue
            if isinstance(data, dict):
                blends.append(
                    {
                        "path": str(path),
                        "strategy": data.get("strategy"),
                        "member_ids": data.get("member_ids"),
                        "score": data.get("score"),
                    }
                )
    print_json({"blends": blends})
