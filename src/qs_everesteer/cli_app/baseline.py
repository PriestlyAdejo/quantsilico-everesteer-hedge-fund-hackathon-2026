"""Baseline scorer-parity and reproduce commands."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd
import typer

from qs_everesteer.cli_app.common import console, print_json, print_mutation_context, repo_root
from qs_everesteer.data.synthetic import TARGET_COL, generate_synthetic_event_data
from qs_everesteer.models import create_model
from qs_everesteer.models.baseline import ORGANISER_BASELINE_PROVENANCE
from qs_everesteer.paths import ensure_dir, synthetic_data_dir
from qs_everesteer.validation.scoring import official_scorers, scorer_parity

baseline_app = typer.Typer(help="Baseline / scorer tooling.", no_args_is_help=True)


@baseline_app.command("scorer-parity")
def baseline_scorer_parity(
    expected: Optional[Path] = typer.Option(None, "--expected", help="Expected prediction column/file."),
    observed: Optional[Path] = typer.Option(None, "--observed", help="Observed prediction column/file."),
    column: str = typer.Option("prediction", "--column"),
) -> None:
    """Compare expected vs observed predictions; list official scorer availability."""
    available = sorted(official_scorers())
    payload: dict = {
        "official_scorers": available,
        "organiser_baseline": ORGANISER_BASELINE_PROVENANCE,
    }
    if expected is None or observed is None:
        payload["parity"] = None
        payload["note"] = "pass --expected and --observed parquet/csv to run numeric parity"
        print_json(payload)
        from qs_everesteer.ops_status import write_ops_status

        write_ops_status(
            "last_scorer_parity.json",
            status="passing",
            detail="official scorer inventory only (no numeric parity inputs)",
            repo_root=repo_root(),
            extra={"official_scorers": available},
        )
        return

    def _load(path: Path):
        if path.suffix.lower() == ".parquet":
            df = pd.read_parquet(path)
        else:
            df = pd.read_csv(path)
        if column in df.columns:
            return df[column].to_numpy(dtype=float), df.get("id")
        return df.iloc[:, 0].to_numpy(dtype=float), df.get("id")

    exp, exp_ids = _load(Path(expected))
    obs, obs_ids = _load(Path(observed))
    parity = scorer_parity(
        exp,
        obs,
        expected_ids=list(exp_ids) if exp_ids is not None else None,
        observed_ids=list(obs_ids) if obs_ids is not None else None,
    )
    payload["parity"] = parity
    print_json(payload)
    from qs_everesteer.ops_status import write_ops_status

    write_ops_status(
        "last_scorer_parity.json",
        status="passing" if parity.get("ok") else "failing",
        detail=str(parity.get("detail") or parity.get("message") or "scorer-parity completed"),
        repo_root=repo_root(),
        extra={"parity": parity},
    )
    if not parity.get("ok"):
        raise typer.Exit(code=1)


@baseline_app.command("reproduce")
def baseline_reproduce(
    data_path: Optional[Path] = typer.Option(
        None,
        "--data",
        help="Training parquet (default: synthetic train).",
    ),
) -> None:
    """
    Fit the independent reference_lgbm baseline.

    Does NOT claim organiser starter parity (see docs/BASELINE_PROVENANCE.md).
    """
    print_mutation_context(candidate="reference_lgbm", lane="practice")
    root = repo_root()
    path = data_path
    if path is None:
        syn = synthetic_data_dir(root)
        path = syn / "train.parquet"
        if not path.exists():
            generate_synthetic_event_data(syn)
    if not Path(path).exists():
        console.print(f"[red]data not found:[/red] {path}")
        raise typer.Exit(code=1)

    df = pd.read_parquet(path)
    features = [c for c in df.columns if str(c).startswith("feature_")]
    if TARGET_COL not in df.columns or not features:
        console.print("[red]dataset missing target/features[/red]")
        raise typer.Exit(code=1)

    model = create_model("reference_lgbm")
    model.fit(df[features], df[TARGET_COL])
    out_dir = ensure_dir(root / "artifacts" / "models" / "reference_lgbm")
    pred = np.asarray(model.predict(df[features]), dtype=float)
    pred_path = out_dir / "train_predictions.npy"
    np.save(pred_path, pred)
    print_json(
        {
            "model": "reference_lgbm",
            "organiser_parity": ORGANISER_BASELINE_PROVENANCE,
            "rows": int(len(df)),
            "n_features": len(features),
            "predictions_path": str(pred_path),
            "note": "Independent reference — not organiser starter reproduction",
        }
    )
