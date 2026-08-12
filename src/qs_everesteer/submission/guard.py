"""Pre-submit integrity checks with structured pass/fail reasons."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import Any

import pandas as pd

from qs_everesteer.data.fingerprint import file_sha256
from qs_everesteer.state.research import SubmissionMode, load_research_state
from qs_everesteer.submission.mode import get_mode


class GuardVerdict(StrEnum):
    PASS = "PASS"
    FAIL = "FAIL"


@dataclass
class GuardCheck:
    name: str
    ok: bool
    detail: str | None = None


@dataclass
class GuardResult:
    ok: bool
    verdict: GuardVerdict
    checks: list[GuardCheck] = field(default_factory=list)
    blocking_reasons: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "verdict": self.verdict.value,
            "checks": [asdict(c) for c in self.checks],
            "blocking_reasons": list(self.blocking_reasons),
        }


@dataclass
class SubmissionContext:
    """Inputs required for a pre-submit guard evaluation."""

    event_id: str | None = None
    event_snapshot_id: str | None = None
    round_id: str | None = None
    lane: str | None = None
    split_fingerprint: str | None = None
    expected_split_fingerprint: str | None = None
    candidate_id: str | None = None
    predictions_path: str | Path | None = None
    expected_ids: list[str] | set[str] | None = None
    prediction_bounds: tuple[float, float] = (0.0, 1.0)
    artefact_path: str | Path | None = None
    quota_remaining: int | None = None
    quota_known: bool = False
    capabilities: dict[str, Any] | None = None
    mode: SubmissionMode | str | None = None
    require_armed_for_live: bool = True
    allow_unknown_quota_in_dry_run: bool = True


class SubmissionGuard:
    """Hard integrity checks: event, round, lane, fingerprint, IDs, quota, mode."""

    def validate(self, ctx: SubmissionContext | None = None, **kwargs: Any) -> GuardResult:
        if ctx is None:
            ctx = SubmissionContext(**kwargs)
        checks: list[GuardCheck] = []
        blocking: list[str] = []

        def add(name: str, ok: bool, detail: str | None = None) -> None:
            checks.append(GuardCheck(name=name, ok=ok, detail=detail))
            if not ok:
                blocking.append(detail or name)

        # Mode
        mode = ctx.mode
        if mode is None:
            mode = get_mode()
        mode = SubmissionMode(mode) if not isinstance(mode, SubmissionMode) else mode
        if mode is SubmissionMode.DISABLED:
            add("mode", False, "submission mode is DISABLED")
        else:
            add("mode", True, mode.value)

        # Event identity
        if not ctx.event_id and not ctx.event_snapshot_id:
            add("event", False, "missing event_id and event_snapshot_id")
        else:
            add(
                "event",
                True,
                f"event_id={ctx.event_id!r} snapshot={ctx.event_snapshot_id!r}",
            )

        # Round
        if not ctx.round_id:
            add("round", False, "missing round_id")
        else:
            add("round", True, str(ctx.round_id))

        # Lane
        lane = (ctx.lane or "").strip().lower()
        if lane not in {"practice", "validation", "diagnostics", "live", "event"}:
            add("lane", False, f"invalid or missing lane: {ctx.lane!r}")
        else:
            add("lane", True, lane)
            caps = ctx.capabilities or {}
            if lane in {"practice", "validation", "diagnostics"}:
                avail = caps.get("validation_available")
                if avail is False:
                    add("capability", False, "practice/validation lane unavailable")
                elif avail is None and "validation_available" in caps:
                    add("capability", False, "practice/validation capability UNKNOWN")
                else:
                    add("capability", True, "practice lane")
            if lane in {"live", "event"}:
                avail = caps.get("live_available")
                if avail is False:
                    add("capability", False, "live/event lane unavailable")
                elif avail is None and "live_available" in caps:
                    add("capability", False, "live/event capability UNKNOWN")
                else:
                    add("capability", True, "live lane")
                if ctx.require_armed_for_live and mode is not SubmissionMode.ARMED:
                    add(
                        "armed_for_live",
                        False,
                        "live lane requires ARMED submission mode",
                    )

        # Split fingerprint
        if not ctx.split_fingerprint:
            add("split_fingerprint", False, "missing split_fingerprint")
        elif (
            ctx.expected_split_fingerprint
            and ctx.split_fingerprint != ctx.expected_split_fingerprint
        ):
            add(
                "split_fingerprint",
                False,
                "split fingerprint mismatch "
                f"(got {ctx.split_fingerprint[:12]}… "
                f"expected {ctx.expected_split_fingerprint[:12]}…)",
            )
        else:
            add("split_fingerprint", True, ctx.split_fingerprint[:16])

        # Artefact / predictions load
        pred_path = Path(ctx.predictions_path) if ctx.predictions_path else None
        if pred_path is None or not pred_path.exists():
            add("artefact", False, f"predictions artefact missing: {ctx.predictions_path!r}")
            df = None
        else:
            try:
                df = _read_predictions(pred_path)
                add(
                    "artefact",
                    True,
                    f"loaded {pred_path.name} sha256={file_sha256(pred_path)[:12]}",
                )
            except Exception as exc:  # noqa: BLE001
                add("artefact", False, f"failed to load predictions: {exc}")
                df = None

        if ctx.artefact_path:
            art = Path(ctx.artefact_path)
            if not art.exists():
                add("model_artefact", False, f"model artefact missing: {art}")
            else:
                add("model_artefact", True, art.name)

        # ID coverage + duplicates + bounds
        if df is not None:
            id_col = "id" if "id" in df.columns else None
            pred_col = "prediction" if "prediction" in df.columns else None
            if id_col is None or pred_col is None:
                add(
                    "id_coverage",
                    False,
                    "predictions must include 'id' and 'prediction' columns",
                )
            else:
                ids = df[id_col].astype(str)
                dup = int(ids.duplicated().sum())
                if dup:
                    add("duplicates", False, f"duplicate prediction ids: {dup}")
                else:
                    add("duplicates", True, "no duplicate ids")

                if ctx.expected_ids is not None:
                    expected = {str(x) for x in ctx.expected_ids}
                    got = set(ids.tolist())
                    missing = sorted(expected - got)
                    extra = sorted(got - expected)
                    if missing or extra:
                        add(
                            "id_coverage",
                            False,
                            f"id coverage fail missing={len(missing)} extra={len(extra)}",
                        )
                    else:
                        add("id_coverage", True, f"coverage {len(got)}/{len(expected)}")
                else:
                    add("id_coverage", True, f"ids={len(ids)} (no expected set provided)")

                lo, hi = ctx.prediction_bounds
                series = pd.to_numeric(df[pred_col], errors="coerce")
                if series.isna().any():
                    add("bounds", False, "non-numeric or null predictions present")
                elif bool((series < lo).any() or (series > hi).any()):
                    add(
                        "bounds",
                        False,
                        f"predictions outside bounds [{lo}, {hi}]",
                    )
                else:
                    add("bounds", True, f"within [{lo}, {hi}]")

        # Quota — UNKNOWN is not zero; block ARMED when unknown; allow DRY_RUN optionally
        if not ctx.quota_known or ctx.quota_remaining is None:
            if mode is SubmissionMode.ARMED:
                add("quota", False, "upload quota UNKNOWN — refusing ARMED submit")
            elif mode is SubmissionMode.DRY_RUN and ctx.allow_unknown_quota_in_dry_run:
                add("quota", True, "quota UNKNOWN (permitted in DRY_RUN)")
            else:
                add("quota", False, "upload quota UNKNOWN")
        else:
            if ctx.quota_remaining <= 0:
                add("quota", False, f"no quota remaining ({ctx.quota_remaining})")
            else:
                add("quota", True, f"remaining={ctx.quota_remaining}")

        # Candidate
        if not ctx.candidate_id:
            add("candidate", False, "missing candidate_id")
        else:
            add("candidate", True, str(ctx.candidate_id))

        ok = not blocking
        return GuardResult(
            ok=ok,
            verdict=GuardVerdict.PASS if ok else GuardVerdict.FAIL,
            checks=checks,
            blocking_reasons=blocking,
        )

    def validate_from_research_state(
        self,
        ctx: SubmissionContext,
        repo_root: str | Path | None = None,
    ) -> GuardResult:
        """Fill mode / snapshot defaults from research state then validate."""
        state = load_research_state(repo_root)
        if ctx.mode is None:
            ctx.mode = state.get("submission_mode")
        if ctx.event_snapshot_id is None:
            ctx.event_snapshot_id = state.get("event_snapshot_id")
        if ctx.round_id is None:
            ctx.round_id = state.get("round")
        budget = state.get("upload_budget") or {}
        if not ctx.quota_known:
            rem = budget.get("live_remaining")
            if ctx.lane and str(ctx.lane).lower() in {"practice", "validation", "diagnostics"}:
                rem = budget.get("practice_remaining", rem)
            if rem is not None:
                ctx.quota_remaining = int(rem)
                ctx.quota_known = True
        return self.validate(ctx)


def _read_predictions(path: Path) -> pd.DataFrame:
    suffix = path.suffix.lower()
    if suffix == ".parquet":
        return pd.read_parquet(path)
    if suffix in {".csv", ".tsv"}:
        sep = "\t" if suffix == ".tsv" else ","
        return pd.read_csv(path, sep=sep)
    if suffix == ".json":
        return pd.read_json(path)
    raise ValueError(f"unsupported predictions format: {path}")
