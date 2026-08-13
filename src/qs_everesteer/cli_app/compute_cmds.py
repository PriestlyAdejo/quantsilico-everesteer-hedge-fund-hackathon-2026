"""Read-only compute capability, policy, and benchmark surfaces."""

from __future__ import annotations

from dataclasses import asdict

import typer

from qs_everesteer.cli_app.common import print_json
from qs_everesteer.execution.benchmark import autotune_from_latest, run_matched_benchmark
from qs_everesteer.execution.contracts import BudgetPolicy, DataEgressPolicy
from qs_everesteer.execution.probe import probe_backends
from qs_everesteer.jobs.queue import list_jobs

compute_app = typer.Typer(no_args_is_help=True, help="Probe compute without provisioning resources.")
policy_app = typer.Typer(no_args_is_help=True, help="Inspect fail-closed compute policies.")


@compute_app.command("probe")
def probe_cmd() -> None:
    """Capability-detect local lanes; remote lanes remain unavailable until verified."""
    print_json([asdict(item) for item in probe_backends()])


@policy_app.command("show")
def policy_show_cmd() -> None:
    """Show default funding and data-egress policy."""
    print_json({"data_egress": asdict(DataEgressPolicy()), "budget": asdict(BudgetPolicy())})


@compute_app.command("jobs")
def compute_jobs_cmd() -> None:
    """List local job records (legacy-compatible read surface)."""
    print_json([job.to_dict() for job in list_jobs()])


@compute_app.command("benchmark")
def benchmark_cmd(
    profile: str = typer.Option("matched", "--profile"),
) -> None:
    """Run a matched public-synthetic CPU/native-GPU canary."""
    if profile not in {"tiny", "matched"}:
        raise typer.BadParameter("profile must be tiny or matched")
    print_json(run_matched_benchmark(profile))


@compute_app.command("autotune")
def autotune_cmd() -> None:
    """Select the fastest passing lane from matched evidence."""
    result = autotune_from_latest()
    print_json(result)
    if result.get("status") == "BLOCKED":
        raise typer.Exit(code=1)


compute_app.add_typer(policy_app, name="policy")
