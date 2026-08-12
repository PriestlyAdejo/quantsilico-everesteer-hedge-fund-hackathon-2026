"""Experiment run / race / compare / frontier / champion commands."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

import typer
import yaml

from qs_everesteer.cli_app.common import (
    console,
    print_json,
    print_mutation_context,
    repo_root,
)
from qs_everesteer.data.synthetic import generate_synthetic_event_data
from qs_everesteer.experiments.racing import RacingScheduler
from qs_everesteer.experiments.runner import ExperimentRunner
from qs_everesteer.fsutil import read_json
from qs_everesteer.jobs.model import JobKind
from qs_everesteer.jobs.queue import enqueue
from qs_everesteer.jobs.worker import run_job_sync
from qs_everesteer.paths import synthetic_data_dir
from qs_everesteer.selection.frontier import pareto_frontier
from qs_everesteer.state.research import load_research_state, update_research_state
from qs_everesteer.validation.temporal import FOLD_PROFILES


def _load_experiment_records(root: Path) -> list[dict[str, Any]]:
    exp_root = root / "runs" / "experiments"
    records: list[dict[str, Any]] = []
    if not exp_root.is_dir():
        return records
    for run_dir in sorted(exp_root.iterdir()):
        if not run_dir.is_dir():
            continue
        run_path = run_dir / "run.json"
        metrics_path = run_dir / "metrics.json"
        if not run_path.exists():
            continue
        try:
            run = read_json(run_path)
            metrics = read_json(metrics_path) if metrics_path.exists() else {}
        except Exception:  # noqa: BLE001
            continue
        if not isinstance(run, dict):
            continue
        score = None
        if isinstance(metrics, dict):
            score = metrics.get("score") or metrics.get("mean_score") or metrics.get("CORR20")
            if score is None and isinstance(metrics.get("fold_scores"), list):
                vals = [float(x) for x in metrics["fold_scores"] if x is not None]
                score = sum(vals) / len(vals) if vals else None
        records.append(
            {
                "candidate_id": run.get("run_id") or run_dir.name,
                "run_id": run.get("run_id") or run_dir.name,
                "status": run.get("status"),
                "score": float(score) if score is not None else None,
                "diversity": float((metrics or {}).get("diversity", 0) or 0)
                if isinstance(metrics, dict)
                else 0.0,
                "runtime_seconds": run.get("runtime_seconds"),
                "integrity_ok": run.get("status") != "FAILED",
                "error": run.get("error"),
                "path": str(run_dir),
            }
        )
    return records


def register_research_commands(app: typer.Typer) -> None:
    """Attach top-level research commands to *app*."""

    @app.command("run")
    def run_experiment(
        config: Path = typer.Argument(..., help="YAML experiment config path."),
        sync: bool = typer.Option(
            True,
            "--sync/--async",
            help="Run via in-process job worker (default) or enqueue only.",
        ),
    ) -> None:
        """Run a persisted temporal experiment from a YAML config."""
        root = repo_root()
        cfg_path = Path(config)
        if not cfg_path.exists():
            console.print(f"[red]config not found:[/red] {cfg_path}")
            raise typer.Exit(code=1)
        print_mutation_context(run_id=cfg_path.stem, lane="practice")
        job_id = enqueue(
            JobKind.TRAIN,
            {"config_path": str(cfg_path.resolve())},
            repo_root=root,
            name=f"train:{cfg_path.stem}",
            candidate=cfg_path.stem,
        )
        if not sync:
            print_json({"job_id": job_id, "status": "QUEUED", "config": str(cfg_path)})
            return

        def _train_handler(job: Any, repo: Path) -> dict[str, Any]:
            path = Path((job.payload or {}).get("config_path") or cfg_path)
            return ExperimentRunner(repo).run(path)

        job = run_job_sync(
            job_id,
            root,
            handlers={JobKind.TRAIN.value: _train_handler},
        )
        manifest = (job.payload or {}).get("result") or {}
        print_json(
            {
                "job_id": job.id,
                "job_status": job.status.value,
                "run_id": manifest.get("run_id"),
                "status": manifest.get("status") or job.status.value,
                "error": manifest.get("error") or job.error,
                "runtime_seconds": manifest.get("runtime_seconds") or job.total_seconds,
            }
        )
        if (manifest.get("status") == "FAILED") or job.status.value == "FAILED":
            raise typer.Exit(code=1)

    @app.command("race")
    def race(
        profile: str = typer.Option(
            "fast",
            "--profile",
            help="Race profile: fast | standard",
        ),
        stage: str = typer.Option("R0", "--stage", help="Racing stage R0–R3."),
    ) -> None:
        """Successive-halving race over known experiment candidates."""
        profile_norm = profile.strip().lower()
        if profile_norm not in {"fast", "standard"}:
            console.print("[red]profile must be fast|standard[/red]")
            raise typer.Exit(code=1)
        stage_norm = stage.strip().upper()
        fold = FOLD_PROFILES.get(stage_norm)
        if fold is None:
            console.print(
                f"[red]stage must be one of[/red] {', '.join(sorted(FOLD_PROFILES))}"
            )
            raise typer.Exit(code=1)
        root = repo_root()
        print_mutation_context(
            lane="practice",
            extra={
                "profile": profile_norm,
                "stage": stage_norm,
                "fold_n_splits": fold.n_splits,
            },
        )
        records = _load_experiment_records(root)
        state = load_research_state(root)
        if not records:
            records = list(state.get("candidates") or [])
        keep = 0.4 if profile_norm == "fast" else 0.5
        outcomes = RacingScheduler(keep_fraction=keep).evaluate(records, stage_norm)
        payload = [o.to_dict() for o in outcomes]

        def _mutate(current: dict) -> None:
            current["race_stage"] = stage_norm
            current["candidates"] = records
            current["race_outcomes"] = payload
            current["meta"]["source"] = "race"
            current["meta"]["fold_profile"] = {
                "name": fold.name,
                "n_splits": fold.n_splits,
                "min_train_expeds": fold.min_train_expeds,
                "test_expeds": fold.test_expeds,
                "embargo": fold.embargo,
            }

        update_research_state(_mutate, repo_root=root)
        print_json(
            {
                "profile": profile_norm,
                "stage": stage_norm,
                "fold_profile": fold.name,
                "outcomes": payload,
            }
        )

    @app.command("compare")
    def compare() -> None:
        """Compare experiment run metrics under runs/experiments/."""
        records = _load_experiment_records(repo_root())
        ranked = sorted(
            [r for r in records if r.get("score") is not None],
            key=lambda r: float(r["score"]),
            reverse=True,
        )
        print_json({"n": len(records), "ranked": ranked[:20], "unscored": len(records) - len(ranked)})

    @app.command("frontier")
    def frontier_cmd(
        score_key: str = typer.Option("score", "--score-key"),
        runtime_key: str = typer.Option("runtime_seconds", "--runtime-key"),
    ) -> None:
        """Compute Pareto frontier (max score, min runtime)."""
        root = repo_root()
        print_mutation_context(lane="practice")
        records = _load_experiment_records(root)
        usable = [r for r in records if r.get(score_key) is not None]
        front = pareto_frontier(
            usable,
            [(score_key, "max"), (runtime_key, "min")],
        )

        def _mutate(current: dict) -> None:
            current["frontier"] = front
            current["meta"]["source"] = "frontier"

        update_research_state(_mutate, repo_root=root)
        print_json({"n_candidates": len(usable), "frontier": front})

    @app.command("champion")
    def champion(
        candidate: Optional[str] = typer.Option(
            None,
            "--set",
            help="Promote a candidate id to champion (omit to show current).",
        ),
    ) -> None:
        """Show or set the research champion candidate."""
        root = repo_root()
        if candidate is None:
            state = load_research_state(root)
            print_json({"champion": state.get("champion")})
            return
        print_mutation_context(candidate=candidate, lane="practice")

        def _mutate(current: dict) -> None:
            current["champion"] = {"id": candidate, "source": "cli"}
            current["meta"]["source"] = "champion"

        update_research_state(_mutate, repo_root=root)
        console.print(f"[green]champion[/green] → {candidate}")


def write_default_race_config(root: Path, *, profile: str = "R0") -> Path:
    """Helper used by rehearsal: tiny ridge config on synthetic train."""
    syn = synthetic_data_dir(root)
    train = syn / "train.parquet"
    if not train.exists():
        generate_synthetic_event_data(syn)
    cfg = {
        "model": "ridge",
        "params": {"alpha": 10.0},
        "data_path": str(train),
        "profile": profile,
        "target": "target_everest_20",
    }
    out = root / "runs" / "experiments" / "_cli_rehearsal_config.yaml"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(yaml.safe_dump(cfg, sort_keys=True), encoding="utf-8")
    return out
