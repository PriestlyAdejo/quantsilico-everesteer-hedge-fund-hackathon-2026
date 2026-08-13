"""Ensemble build / compare commands."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import typer

from qs_everesteer.cli_app.common import console, print_json, print_mutation_context, repo_root
from qs_everesteer.ensemble.blend import (
    greedy_forward,
    persist_blend,
    rank_average,
    ridge_oof_stack,
)
from qs_everesteer.fsutil import read_json
from qs_everesteer.paths import ensure_dir
from qs_everesteer.state.research import update_research_state
from qs_everesteer.validation.scoring import local_grouped_corr

ensemble_app = typer.Typer(help="Ensemble blending.", no_args_is_help=True)


def _collect_oof(
    root: Path,
) -> tuple[pd.DataFrame | None, np.ndarray | None, np.ndarray | None]:
    """Key-align promotion-grade OOF columns; never blend by row position."""
    exp_root = root / "runs" / "experiments"
    aligned: pd.DataFrame | None = None
    if not exp_root.is_dir():
        return None, None, None
    for run_dir in sorted(exp_root.iterdir()):
        oof_path = run_dir / "oof.parquet"
        if not oof_path.exists():
            continue
        run_path = run_dir / "run.json"
        if not run_path.exists():
            continue
        try:
            run = read_json(run_path)
            df = pd.read_parquet(oof_path)
        except Exception:  # noqa: BLE001, S112 -- corrupt runs are excluded as evidence
            continue
        if str((run.get("config") or {}).get("profile", "")).upper() not in {"R2", "R3"}:
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
        keys = [name for name in ("id", "exped") if name in df.columns]
        if "exped" not in keys:
            continue
        if "id" not in keys and "row_index" in df.columns:
            keys.insert(0, "row_index")
        if df.duplicated(keys).any():
            continue
        target_col = next((name for name in ("target", "target_everest_20", "y", "y_true") if name in df), None)
        if target_col is None:
            continue
        part = df[keys + [target_col, pred_col]].rename(
            columns={target_col: "target", pred_col: run_dir.name}
        )
        if aligned is None:
            aligned = part
        else:
            candidate = aligned.merge(part, on=keys, how="inner", suffixes=("", "_candidate"))
            if "target_candidate" in candidate:
                if not np.allclose(candidate["target"], candidate["target_candidate"], equal_nan=False):
                    continue
                candidate = candidate.drop(columns="target_candidate")
            aligned = candidate
    if aligned is None or len(aligned.columns) <= 3:
        return None, None, None
    model_cols = [c for c in aligned if c not in {*[c for c in ("id", "row_index", "exped") if c in aligned], "target"}]
    return aligned[model_cols], aligned["target"].to_numpy(float), aligned["exped"].to_numpy()


@ensemble_app.command("build")
def ensemble_build(
    strategy: str = typer.Option("rank_average", "--strategy", help="rank_average|greedy_forward"),
    method: str | None = typer.Option(None, "--method", help="Alias for --strategy."),
    out: Path | None = typer.Option(  # noqa: B008
        None, "--out", help="Blend manifest path."
    ),
) -> None:
    """Build a blend from available experiment OOF predictions."""
    root = repo_root()
    print_mutation_context(lane="practice", candidate="ensemble")
    preds, y_true, groups = _collect_oof(root)
    if preds is None or preds.empty:
        console.print("[yellow]no OOF predictions found under runs/experiments/[/yellow]")
        print_json({"ok": False, "reason": "no_oof", "members": []})
        raise typer.Exit(code=1)

    strategy_norm = (method or strategy).strip().lower()
    strategy_norm = {"greedy": "greedy_forward", "ridge-oof": "ridge_oof"}.get(
        strategy_norm, strategy_norm
    )
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
    elif strategy_norm in {"ridge_oof", "non_negative_oof"}:
        if y_true is None or groups is None:
            console.print("[red]OOF stack requires aligned target and exped columns[/red]")
            raise typer.Exit(code=1)
        result = ridge_oof_stack(
            preds, y_true, groups, non_negative=strategy_norm == "non_negative_oof"
        )
        result["strategy"] = strategy_norm
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
            except Exception:  # noqa: BLE001, S112 -- corrupt manifests are excluded
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
