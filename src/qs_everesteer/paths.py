"""Repo-root discovery and standard filesystem layout helpers."""

from __future__ import annotations

from pathlib import Path

_MARKER_NAMES = ("pyproject.toml", ".git")


def find_repo_root(start: str | Path | None = None) -> Path:
    """Walk upward from *start* (or this file) until a repo marker is found."""
    cur = Path(start).resolve() if start is not None else Path(__file__).resolve().parent
    if cur.is_file():
        cur = cur.parent
    for candidate in (cur, *cur.parents):
        if any((candidate / marker).exists() for marker in _MARKER_NAMES):
            return candidate
    raise FileNotFoundError(
        f"Could not locate repo root from {cur} (looking for {_MARKER_NAMES})"
    )


def ensure_dir(path: str | Path) -> Path:
    """Create *path* (and parents) if needed; return resolved Path."""
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p.resolve()


def data_dir(repo_root: str | Path | None = None) -> Path:
    root = Path(repo_root) if repo_root is not None else find_repo_root()
    return (Path(root) / "data").resolve()


def runs_dir(repo_root: str | Path | None = None) -> Path:
    root = Path(repo_root) if repo_root is not None else find_repo_root()
    return (Path(root) / "runs").resolve()


def artifacts_dir(repo_root: str | Path | None = None) -> Path:
    root = Path(repo_root) if repo_root is not None else find_repo_root()
    return (Path(root) / "artifacts").resolve()


def synthetic_data_dir(repo_root: str | Path | None = None) -> Path:
    return data_dir(repo_root) / "synthetic"


def state_dir(repo_root: str | Path | None = None) -> Path:
    return runs_dir(repo_root) / "state"


def jobs_dir(repo_root: str | Path | None = None) -> Path:
    return runs_dir(repo_root) / "jobs"


def ensure_standard_dirs(repo_root: str | Path | None = None) -> dict[str, Path]:
    """Ensure the core data/runs/artifacts layout exists; return key paths."""
    root = Path(repo_root) if repo_root is not None else find_repo_root()
    root = Path(root).resolve()
    paths = {
        "repo_root": root,
        "data": ensure_dir(root / "data"),
        "data_synthetic": ensure_dir(root / "data" / "synthetic"),
        "runs": ensure_dir(root / "runs"),
        "runs_state": ensure_dir(root / "runs" / "state"),
        "runs_jobs": ensure_dir(root / "runs" / "jobs"),
        "runs_experiments": ensure_dir(root / "runs" / "experiments"),
        "artifacts": ensure_dir(root / "artifacts"),
        "artifacts_models": ensure_dir(root / "artifacts" / "models"),
        "artifacts_predictions": ensure_dir(root / "artifacts" / "predictions"),
        "artifacts_submissions": ensure_dir(root / "artifacts" / "submissions"),
    }
    return paths
