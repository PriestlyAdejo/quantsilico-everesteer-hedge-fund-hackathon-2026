"""Content and schema fingerprints for dataset integrity checks."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import pandas as pd


def file_sha256(path: str | Path, *, chunk_size: int = 1 << 20) -> str:
    """SHA-256 hex digest of file bytes."""
    h = hashlib.sha256()
    with Path(path).open("rb") as fh:
        while True:
            chunk = fh.read(chunk_size)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def schema_fingerprint(df: pd.DataFrame) -> str:
    """Stable SHA-256 over ordered column names and dtypes."""
    payload = [{"name": str(c), "dtype": str(df[c].dtype)} for c in df.columns]
    blob = json.dumps(payload, separators=(",", ":"), sort_keys=False).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


def schema_fingerprint_from_path(path: str | Path) -> str:
    """Read a Parquet/CSV file and return its schema fingerprint."""
    df = _read_frame(path)
    return schema_fingerprint(df)


def fingerprint_dataset(path: str | Path) -> dict[str, Any]:
    """Return content hash + schema fingerprint (+ column inventory)."""
    p = Path(path)
    df = _read_frame(p)
    return {
        "path": str(p.resolve()),
        "content_sha256": file_sha256(p),
        "schema_sha256": schema_fingerprint(df),
        "columns": [{"name": str(c), "dtype": str(df[c].dtype)} for c in df.columns],
        "rows": int(len(df)),
    }


def _read_frame(path: str | Path) -> pd.DataFrame:
    p = Path(path)
    suffix = p.suffix.lower()
    if suffix == ".parquet":
        return pd.read_parquet(p)
    if suffix in {".csv", ".tsv"}:
        sep = "\t" if suffix == ".tsv" else ","
        return pd.read_csv(p, sep=sep)
    raise ValueError(f"unsupported dataset format for fingerprint: {p}")
