"""R0→R3 successive halving with integrity-only universal hard stops."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from qs_everesteer.api_schemas.pages import RaceDecision
from qs_everesteer.fsutil import read_json

STAGES = ("R0", "R1", "R2", "R3")


@dataclass(frozen=True)
class RaceOutcome:
    candidate_id: str
    stage: str
    decision: RaceDecision
    next_stage: str | None
    rationale: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "candidate_id": self.candidate_id, "stage": self.stage,
            "decision": self.decision.value, "next_stage": self.next_stage,
            "rationale": self.rationale,
        }


class RacingScheduler:
    def __init__(self, *, keep_fraction: float = 0.5, min_survivors: int = 1) -> None:
        self.keep_fraction = keep_fraction
        self.min_survivors = min_survivors

    def evaluate(self, records: list[dict[str, Any]], stage: str) -> list[RaceOutcome]:
        stage = stage.upper()
        if stage not in STAGES:
            raise ValueError(f"unknown race stage: {stage}")
        outcomes, eligible = [], []
        for record in records:
            cid = str(record.get("candidate_id") or record.get("run_id"))
            if record.get("integrity_ok", True) is False:
                outcomes.append(RaceOutcome(
                    cid, stage, RaceDecision.INVALID_INTEGRITY, None,
                    "hard integrity check failed",
                ))
            elif record.get("id_alignment_ok", True) is False:
                outcomes.append(RaceOutcome(
                    cid, stage, RaceDecision.INVALID_ID_ALIGNMENT, None,
                    "prediction IDs are misaligned",
                ))
            elif record.get("status") == "FAILED":
                outcomes.append(RaceOutcome(
                    cid, stage, RaceDecision.FAILED_TRAINING, None,
                    str(record.get("error") or "training failed"),
                ))
            else:
                eligible.append(record)
        eligible.sort(key=lambda r: float(r.get("score", float("-inf"))), reverse=True)
        keep = min(
            len(eligible),
            max(self.min_survivors, int(len(eligible) * self.keep_fraction + 0.999)),
        )
        next_stage = STAGES[STAGES.index(stage) + 1] if stage != "R3" else None
        for index, record in enumerate(eligible):
            cid = str(record.get("candidate_id") or record.get("run_id"))
            if index < keep:
                decision = (
                    RaceDecision.PROMOTE_TOP_SCORE if index == 0
                    else RaceDecision.PROMOTE_DIVERSITY
                    if float(record.get("diversity", 0)) > 0
                    else RaceDecision.PROMOTE_EXPLORATION
                )
                rationale = "survived soft-quality successive halving"
            else:
                decision, rationale = (
                    RaceDecision.RETIRE_DOMINATED,
                    "soft quality evidence ranked below current survivors",
                )
            outcomes.append(RaceOutcome(cid, stage, decision, next_stage if index < keep else None, rationale))
        return outcomes

    def next_actions(self, research_state: dict) -> list[dict]:
        stage = str(research_state.get("race_stage", "R0")).upper()
        records = list(research_state.get("candidates") or [])
        return [outcome.to_dict() for outcome in self.evaluate(records, stage)]

    @staticmethod
    def child_configs(
        outcomes: list[RaceOutcome], *, repo_root: str | Path, target_stage: str,
    ) -> list[dict[str, Any]]:
        """Build real retraining configs for promoted parents, preserving lineage."""
        root = Path(repo_root)
        configs = []
        for outcome in outcomes:
            if outcome.next_stage != target_stage:
                continue
            run_path = root / "runs" / "experiments" / outcome.candidate_id / "run.json"
            if not run_path.exists():
                continue
            parent = read_json(run_path)
            config = dict(parent.get("config") or {})
            if not config:
                continue
            config.update(
                run_id=f"{outcome.candidate_id}-{target_stage.lower()}",
                parent_run_id=outcome.candidate_id,
                profile=target_stage,
                promotion_decision=outcome.decision.value,
            )
            configs.append(config)
        return configs
