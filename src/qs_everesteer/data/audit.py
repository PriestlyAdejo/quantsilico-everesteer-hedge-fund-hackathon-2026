from dataclasses import dataclass
from pathlib import Path


@dataclass
class DatasetAudit:
    path: Path
    rows: int
    columns: int
    id_column: str | None
    time_group: str | None
    target_columns: list[str]
    feature_columns: list[str]
    duplicate_ids: int
    warnings: list[str]
    hard_failures: list[str]


def audit_dataset(path: str | Path) -> DatasetAudit:
    raise NotImplementedError
