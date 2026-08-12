"""Dataset pull / audit / fingerprint commands."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer

from qs_everesteer.cli_app.common import (
    console,
    print_json,
    print_mutation_context,
    repo_root,
    wants_synthetic,
)
from qs_everesteer.data.audit import audit_dataset
from qs_everesteer.data.fingerprint import fingerprint_dataset
from qs_everesteer.data.synthetic import generate_synthetic_event_data
from qs_everesteer.event.adapter import EveresteerAdapter
from qs_everesteer.jobs.model import JobKind
from qs_everesteer.jobs.queue import enqueue
from qs_everesteer.paths import data_dir, synthetic_data_dir

data_app = typer.Typer(help="Dataset pull, audit, and fingerprinting.", no_args_is_help=True)


def _ensure_synthetic() -> dict[str, Path]:
    syn = synthetic_data_dir(repo_root())
    train = syn / "train.parquet"
    if not train.exists():
        console.print("[dim]generating synthetic fixtures…[/dim]")
        return generate_synthetic_event_data(syn)
    return {
        "train": syn / "train.parquet",
        "validation": syn / "validation.parquet",
        "live": syn / "live.parquet",
    }


@data_app.command("pull")
def data_pull(
    split: str = typer.Option(
        ...,
        "--split",
        help="Dataset split: train | validation | live",
    ),
    dest: Optional[Path] = typer.Option(
        None,
        "--dest",
        help="Destination file or directory (default: data/<split>.parquet).",
    ),
) -> None:
    """Pull a split; uses synthetic fixtures when creds missing or QSEH_SYNTHETIC=1."""
    split_norm = split.strip().lower()
    if split_norm not in {"train", "validation", "live", "val", "valid"}:
        console.print("[red]split must be train|validation|live[/red]")
        raise typer.Exit(code=1)
    if split_norm in {"val", "valid"}:
        split_norm = "validation"

    root = repo_root()
    synthetic = wants_synthetic()
    print_mutation_context(lane=split_norm, extra={"synthetic": synthetic})

    out = dest or (data_dir(root) / f"{split_norm}.parquet")
    adapter = EveresteerAdapter(synthetic=synthetic)
    try:
        path = adapter.pull_split(split_norm, out, repo_root=root)
    except RuntimeError as exc:
        if not synthetic:
            console.print(f"[yellow]{exc}[/yellow]")
            console.print("[dim]falling back to synthetic fixtures[/dim]")
            adapter = EveresteerAdapter(synthetic=True)
            path = adapter.pull_split(split_norm, out, repo_root=root)
        else:
            raise
    fp = fingerprint_dataset(path)
    job_id = enqueue(
        JobKind.DATA_PULL,
        {
            "split": split_norm,
            "path": str(path),
            "content_sha256": fp["content_sha256"],
            "synthetic": adapter.synthetic,
        },
        repo_root=root,
        name=f"data_pull:{split_norm}",
    )
    print_json(
        {
            "path": str(path),
            "split": split_norm,
            "synthetic": adapter.synthetic,
            "content_sha256": fp["content_sha256"],
            "schema_sha256": fp["schema_sha256"],
            "rows": fp["rows"],
            "job_id": job_id,
        }
    )


@data_app.command("audit")
def data_audit(
    path: Optional[Path] = typer.Argument(
        None,
        help="Dataset path (default: synthetic train.parquet).",
    ),
) -> None:
    """Run structural integrity audit on a Parquet/CSV dataset."""
    if path is None:
        paths = _ensure_synthetic()
        path = paths["train"]
    target = Path(path)
    if not target.exists():
        console.print(f"[red]dataset not found:[/red] {target}")
        raise typer.Exit(code=1)
    audit = audit_dataset(target)
    print_json(audit.to_dict())
    if audit.hard_failures:
        raise typer.Exit(code=1)


@data_app.command("fingerprint")
def data_fingerprint(
    path: Optional[Path] = typer.Argument(
        None,
        help="Dataset path (default: synthetic train.parquet).",
    ),
) -> None:
    """Content + schema fingerprint for a dataset file."""
    if path is None:
        paths = _ensure_synthetic()
        path = paths["train"]
    target = Path(path)
    if not target.exists():
        console.print(f"[red]dataset not found:[/red] {target}")
        raise typer.Exit(code=1)
    print_mutation_context(hashes={"content": "(computing)"})
    result = fingerprint_dataset(target)
    print_json(result)
