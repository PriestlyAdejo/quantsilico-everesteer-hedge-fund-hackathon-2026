"""Deterministic, resumable competition workflow with no LLM dependency."""
from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import Any

from qs_everesteer.paths import find_repo_root
from qs_everesteer.state.research import SubmissionMode, load_research_state, update_research_state


class AutopilotStage(StrEnum):
    DISCOVER = "DISCOVER"
    PULL = "PULL"
    SCORER_PARITY = "SCORER_PARITY"
    BASELINE = "BASELINE"
    FAST_RACE = "FAST_RACE"
    STANDARD_RACE = "STANDARD_RACE"
    PROMOTION_RACE = "PROMOTION_RACE"
    FRONTIER = "FRONTIER"
    ENSEMBLE = "ENSEMBLE"
    PRACTICE_SUBMIT = "PRACTICE_SUBMIT"
    LIVE_SUBMIT = "LIVE_SUBMIT"
    OBSERVE = "OBSERVE"
    ADAPT = "ADAPT"
    COMPLETE = "COMPLETE"


STAGE_ORDER = tuple(AutopilotStage)


class CompetitionAutopilot:
    """Advance one persisted state at a time; handlers are plain callables."""

    def __init__(
        self, repo_root: str | Path | None = None,
        handlers: dict[str | AutopilotStage, Callable[[dict[str, Any]], Any]] | None = None,
    ) -> None:
        self.repo_root = Path(repo_root) if repo_root else find_repo_root()
        self.handlers = {str(key): value for key, value in (handlers or {}).items()}

    def step(self, profile: str = "competition_aggressive") -> dict[str, Any]:
        state = load_research_state(self.repo_root)
        raw = state.get("autopilot_stage", AutopilotStage.DISCOVER.value)
        stage = AutopilotStage(raw)
        if stage is AutopilotStage.COMPLETE:
            return state
        # Autopilot may use an already-ARMED mode, but never changes mode to ARMED.
        mode_before = state.get("submission_mode", SubmissionMode.DRY_RUN.value)
        handler = self.handlers.get(stage.value) or self.handlers.get(str(stage))
        result = handler(state) if handler else {"status": "SKIPPED", "reason": "no handler"}
        current_index = STAGE_ORDER.index(stage)
        next_stage = STAGE_ORDER[min(current_index + 1, len(STAGE_ORDER) - 1)]

        def mutate(current: dict[str, Any]) -> None:
            current["autopilot_active"] = next_stage is not AutopilotStage.COMPLETE
            current["autopilot_stage"] = next_stage.value
            current["submission_mode"] = mode_before
            history = current.setdefault("autopilot_history", [])
            history.append({
                "stage": stage.value, "next_stage": next_stage.value,
                "profile": profile, "result": result,
                "completed_at": datetime.now(UTC).replace(microsecond=0).isoformat(),
            })

        return update_research_state(mutate, repo_root=self.repo_root)

    def run(
        self, profile: str = "competition_aggressive", *, max_steps: int | None = None
    ) -> dict[str, Any]:
        state = load_research_state(self.repo_root)
        steps = 0
        while state.get("autopilot_stage", "DISCOVER") != AutopilotStage.COMPLETE.value:
            if max_steps is not None and steps >= max_steps:
                break
            state = self.step(profile)
            steps += 1
        return state
