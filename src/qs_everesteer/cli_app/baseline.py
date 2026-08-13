"""Baseline scorer-parity and reproduce commands."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import numpy as np
import pandas as pd
import typer

from qs_everesteer.cli_app.common import (
    console,
    print_json,
    print_mutation_context,
    repo_root,
    wants_synthetic,
)
from qs_everesteer.data.synthetic import TARGET_COL, generate_synthetic_event_data
from qs_everesteer.models import create_model
from qs_everesteer.models.baseline import ORGANISER_BASELINE_PROVENANCE
from qs_everesteer.paths import ensure_dir, synthetic_data_dir
from qs_everesteer.validation.scoring import official_scorers, scorer_parity

baseline_app = typer.Typer(help="Baseline / scorer tooling.", no_args_is_help=True)


@baseline_app.command("scorer-parity")
def baseline_scorer_parity(
    expected: Annotated[
        Path | None, typer.Option("--expected", help="Expected prediction file.")
    ] = None,
    observed: Annotated[
        Path | None, typer.Option("--observed", help="Observed prediction file.")
    ] = None,
    column: Annotated[str, typer.Option("--column")] = "prediction",
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
        frame = pd.read_parquet(path) if path.suffix.lower() == ".parquet" else pd.read_csv(path)
        if column in frame.columns:
            return frame[column].to_numpy(dtype=float), frame.get("id")
        return frame.iloc[:, 0].to_numpy(dtype=float), frame.get("id")

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
    data_path: Annotated[
        Path | None,
        typer.Option("--data", help="Training parquet (required unless synthetic mode is explicit)."),
    ] = None,
    official: Annotated[
        bool,
        typer.Option(
            "--official/--reference",
            help="Use the attributable organiser recipe or legacy reference recipe.",
        ),
    ] = False,
) -> None:
    """Fit the organiser or independent reference LightGBM baseline."""
    model_name = "organiser_lgbm" if official else "reference_lgbm"
    print_mutation_context(candidate=model_name, lane="practice")
    root = repo_root()
    path = data_path
    if path is None:
        if not wants_synthetic():
            console.print("[red]--data is required unless QSEH_SYNTHETIC=1 was set[/red]")
            raise typer.Exit(code=1)
        syn = synthetic_data_dir(root)
        path = syn / "train.parquet"
        if not path.exists():
            generate_synthetic_event_data(syn)
    if not Path(path).exists():
        console.print(f"[red]data not found:[/red] {path}")
        raise typer.Exit(code=1)

    df = pd.read_parquet(path)
    features = sorted(c for c in df.columns if str(c).startswith("feature_"))
    if TARGET_COL not in df.columns or not features:
        console.print("[red]dataset missing target/features[/red]")
        raise typer.Exit(code=1)

    fit_df = df
    score_df = df
    if official:
        if "exped" not in df.columns:
            console.print("[red]official reproduction requires an exped column[/red]")
            raise typer.Exit(code=1)

        def _exped_num(value: object) -> int:
            return int(str(value).split("_")[-1])

        expeds = sorted(df["exped"].dropna().unique(), key=_exped_num)
        if len(expeds) <= 120:
            console.print("[red]official reproduction requires more than 120 expeds[/red]")
            raise typer.Exit(code=1)
        fit_df = df[df["exped"].isin(set(expeds[:-120]))].copy()
        score_df = df[df["exped"].isin(set(expeds[-100:]))].copy()

    fit_df = fit_df[fit_df[TARGET_COL].notna()].copy()
    score_df = score_df[score_df[TARGET_COL].notna()].copy()
    x_fit = fit_df[features].astype("float32")
    x_score = score_df[features].astype("float32")
    if official:
        x_fit = x_fit.where(x_fit >= 0)
        x_score = x_score.where(x_score >= 0)

    model = create_model(model_name)
    model.fit(x_fit, fit_df[TARGET_COL])
    out_dir = ensure_dir(root / "artifacts" / "models" / model_name)
    pred = np.asarray(model.predict(x_score), dtype=float)
    pred_path = out_dir / ("holdout_predictions.npy" if official else "train_predictions.npy")
    np.save(pred_path, pred)

    mean_spearman = None
    if official and len(score_df):
        from scipy.stats import spearmanr

        corrs: list[float] = []
        for _, group in score_df.assign(prediction=pred).groupby("exped", sort=False):
            if len(group) < 5:
                continue
            rho = spearmanr(group["prediction"], group[TARGET_COL]).statistic
            if np.isfinite(rho):
                corrs.append(float(rho))
        mean_spearman = float(np.mean(corrs)) if corrs else None

    print_json(
        {
            "model": model_name,
            "organiser_parity": ORGANISER_BASELINE_PROVENANCE,
            "rows": len(fit_df),
            "holdout_rows": len(score_df) if official else None,
            "n_features": len(features),
            "predictions_path": str(pred_path),
            "mean_holdout_spearman": mean_spearman,
            "synthetic": wants_synthetic(),
            "note": "Attributable organiser recipe" if official else "Independent reference",
        }
    )
