"""Filesystem-backed DTO builder for the local Research Console."""

from __future__ import annotations

import json
import platform
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import psutil

from qs_everesteer.api_schemas import (
    ComputeData,
    ConnectionState,
    DataEnvelope,
    DataLabData,
    DocumentationData,
    EnsembleData,
    EnsembleStrategy,
    EventControlData,
    EventStatus,
    ExperimentRow,
    FeatureLabData,
    FlowNode,
    FlowState,
    LeaderboardData,
    OverviewData,
    Provenance,
    RaceDecision,
    RepoData,
    RoundRoomData,
    StakingData,
    SubmissionData,
    ValidationData,
)
from qs_everesteer.api_schemas.pages import (
    ComputeCpu,
    ComputeDisk,
    ComputeEventWatcher,
    ComputeGpu,
    ComputeHardware,
    ComputeRam,
    ComputeUtilisation,
    DataLabDrift,
    DataSetCard,
    DataSetIntegrityMessage,
    DocArticle,
    DocCalloutBlock,
    DocCommandBlock,
    DocFlowBlock,
    DocFlowNode,
    DocHeadingBlock,
    DocIntroBlock,
    DocMetricBlock,
    DocParagraphBlock,
    DocRelatedBlock,
    DocSection,
    EnsembleMetrics,
    EventControlConnection,
    EventControlEventState,
    EventControlScoring,
    EventRoundInfo,
    EventUploadsInfo,
    FeatureLabSummary,
    LeaderboardModelMatrixCell,
    ModelRow,
    OverviewAction,
    OverviewRecommendation,
    RepoCheckResult,
    RoundEmergency,
    RoundEventLogEntry,
    RoundHeatmapCell,
    StakingClassification,
    StepStatus,
    SubmissionStepperStep,
    ValidationRaceDecision,
)
from qs_everesteer.docs_build import collect_curated_articles, curated_sections
from qs_everesteer.jobs.queue import list_jobs
from qs_everesteer.staking.classify import classify_staking
from qs_everesteer.state.research import load_research_state


def utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


class ConsoleService:
    """Build contract DTOs only from persisted local or official observations."""

    def __init__(self, repo_root: str | Path) -> None:
        self.repo_root = Path(repo_root).resolve()

    def state(self) -> dict[str, Any]:
        return load_research_state(self.repo_root)

    def envelope(
        self,
        kind: str,
        data: Any,
        *,
        provenance: Provenance,
        source: str,
        stale: bool = False,
        refresh_mode: str = "poll",
    ) -> DataEnvelope[Any]:
        state = self.state()
        return DataEnvelope(
            kind=kind,
            provenance=provenance,
            generated_at=utc_now(),
            stale=stale,
            source=source,
            refresh_mode=refresh_mode,
            source_id=state.get("meta", {}).get("source"),
            event_snapshot_id=state.get("event_snapshot_id"),
            data=data,
        )

    @staticmethod
    def _connection(state: dict[str, Any]) -> ConnectionState:
        try:
            return ConnectionState(state.get("connection", "NOT_CONNECTED"))
        except ValueError:
            return ConnectionState.NOT_CONNECTED

    @staticmethod
    def _submission_mode(state: dict[str, Any]) -> str:
        mode = str(state.get("submission_mode", "DRY_RUN"))
        return mode if mode in {"DISABLED", "DRY_RUN", "ARMED"} else "DRY_RUN"

    @staticmethod
    def _jobs(repo_root: Path) -> list[dict[str, Any]]:
        return [
            {
                "id": job.id,
                "name": job.name,
                "type": job.type,
                "status": job.status.value,
                "device": job.device,
                "candidate": job.candidate,
                "started_at": job.started_at,
                "eta_seconds": job.eta_seconds,
                "total_seconds": job.total_seconds,
                "progress": job.progress,
                "queue_position": job.queue_position,
            }
            for job in list_jobs(repo_root)
        ]

    @staticmethod
    def _model_ids(state: dict[str, Any]) -> list[str]:
        models = state.get("models")
        ids: list[str] = []
        if isinstance(models, list):
            for item in models:
                if isinstance(item, str) and item:
                    ids.append(item)
                elif isinstance(item, dict):
                    alias = (
                        item.get("id")
                        or item.get("private_alias")
                        or item.get("alias")
                        or item.get("public_alias")
                    )
                    if alias:
                        ids.append(str(alias))
        if ids:
            return ids
        for item in state.get("frontier") or []:
            if isinstance(item, str) and item:
                ids.append(item)
            elif isinstance(item, dict):
                alias = item.get("id") or item.get("candidate_id") or item.get("alias")
                if alias:
                    ids.append(str(alias))
        return ids

    @staticmethod
    def _round_ids(state: dict[str, Any]) -> list[str]:
        rounds = state.get("rounds")
        if isinstance(rounds, list) and rounds:
            return [str(item) for item in rounds if item is not None and str(item)]
        labels: list[str] = []
        for key in (state.get("live_evidence") or {}):
            labels.append(str(key))
        if state.get("round"):
            rid = str(state["round"])
            if rid not in labels:
                labels.append(rid)
        return labels

    @classmethod
    def _heatmap_cells(cls, state: dict[str, Any]) -> list[RoundHeatmapCell]:
        explicit = state.get("heatmap") or state.get("heatmap_data")
        if isinstance(explicit, list) and explicit:
            cells: list[RoundHeatmapCell] = []
            for item in explicit:
                if not isinstance(item, dict):
                    continue
                try:
                    cells.append(
                        RoundHeatmapCell(
                            model=str(item["model"]),
                            round=str(item["round"]),
                            score=float(item.get("score") or 0.0),
                        )
                    )
                except (KeyError, TypeError, ValueError):
                    continue
            if cells:
                return cells
        models = cls._model_ids(state)
        rounds = cls._round_ids(state)
        scores = state.get("score_matrix") if isinstance(state.get("score_matrix"), dict) else {}
        out: list[RoundHeatmapCell] = []
        for model in models:
            row = scores.get(model) if isinstance(scores.get(model), dict) else {}
            for round_id in rounds:
                raw = row.get(round_id, 0.0)
                try:
                    score = float(raw)
                except (TypeError, ValueError):
                    score = 0.0
                out.append(RoundHeatmapCell(model=model, round=round_id, score=score))
        return out

    @classmethod
    def _round_model_matrix(cls, state: dict[str, Any]) -> list[LeaderboardModelMatrixCell]:
        cells = cls._heatmap_cells(state)
        return [
            LeaderboardModelMatrixCell(model=cell.model, round=cell.round, score=cell.score)
            for cell in cells
        ]

    @staticmethod
    def _doc_blocks(raw_blocks: list[Any]) -> list[Any]:
        blocks: list[Any] = []
        for item in raw_blocks:
            if not isinstance(item, dict):
                continue
            kind = item.get("kind")
            try:
                if kind == "intro":
                    blocks.append(DocIntroBlock(kind="intro", text=str(item.get("text") or "")))
                elif kind == "heading":
                    blocks.append(DocHeadingBlock(kind="heading", text=str(item.get("text") or "")))
                elif kind == "paragraph":
                    blocks.append(
                        DocParagraphBlock(kind="paragraph", text=str(item.get("text") or ""))
                    )
                elif kind == "flow":
                    nodes = [
                        DocFlowNode(id=str(node.get("id")), label=str(node.get("label")))
                        for node in item.get("nodes") or []
                        if isinstance(node, dict)
                    ]
                    blocks.append(DocFlowBlock(kind="flow", nodes=nodes))
                elif kind == "callout":
                    tone = str(item.get("tone") or "info")
                    if tone not in {"info", "warning", "danger"}:
                        tone = "info"
                    blocks.append(
                        DocCalloutBlock(kind="callout", tone=tone, text=str(item.get("text") or ""))
                    )
                elif kind == "command":
                    blocks.append(
                        DocCommandBlock(kind="command", command=str(item.get("command") or ""))
                    )
                elif kind == "metric":
                    blocks.append(
                        DocMetricBlock(
                            kind="metric",
                            name=str(item.get("name") or "metric"),
                            text=str(item.get("text") or ""),
                        )
                    )
                elif kind == "related":
                    blocks.append(
                        DocRelatedBlock(
                            kind="related",
                            href=str(item.get("href") or "/"),
                            label=str(item.get("label") or item.get("href") or "/"),
                        )
                    )
            except (TypeError, ValueError):
                continue
        return blocks

    def event_status(self) -> DataEnvelope[EventStatus]:
        state = self.state()
        budget = state.get("upload_budget", {})
        cap = budget.get("cap")
        remaining = budget.get("practice_remaining")
        used = cap - remaining if isinstance(cap, int) and isinstance(remaining, int) else None
        data = EventStatus(
            connection=self._connection(state),
            last_update_at=state.get("meta", {}).get("updated_at"),
            event_id=state.get("event_id"),
            event_phase=state.get("event_phase"),
            round=EventRoundInfo(
                index=state.get("round_index"),
                total=state.get("round_total"),
                label=state.get("round"),
            ),
            uploads=EventUploadsInfo(used=used, total=cap),
            champion=state.get("champion"),
            external_rank=state.get("external_rank"),
            autopilot=bool(state.get("autopilot_active")),
            scope=state.get("scope"),
        )
        return self.envelope(
            "event_status",
            data,
            provenance=Provenance.OFFICIAL_EVENT_STATE,
            source="Research state; official event adapter not connected"
            if data.connection is ConnectionState.NOT_CONNECTED
            else "Everesteer event adapter",
            stale=data.connection is not ConnectionState.LIVE,
        )

    def overview(self) -> DataEnvelope[OverviewData]:
        state = self.state()
        connected = self._connection(state) is ConnectionState.LIVE
        has_data = bool(state.get("data_fingerprint"))
        has_runs = bool(state.get("frontier"))
        has_ensemble = bool(state.get("ensemble", {}).get("blend_id"))
        stages = [
            ("connect", "Connect event", connected),
            ("data", "Audit data", has_data),
            ("research", "Run experiments", has_runs),
            ("ensemble", "Build ensemble", has_ensemble),
            ("submit", "Validate submission", False),
        ]
        first_incomplete = next((item[0] for item in stages if not item[2]), "submit")
        flow = [
            FlowNode(
                id=stage_id,
                label=label,
                state=FlowState.COMPLETE
                if complete
                else FlowState.ACTIVE
                if stage_id == first_incomplete
                else FlowState.WAITING,
            )
            for stage_id, label, complete in stages
        ]
        mode = self._submission_mode(state)
        recommendation = state.get("recommendation")
        text = (
            str(recommendation)
            if recommendation
            else "Connect the official event adapter to begin."
        )
        if mode == "ARMED":
            text = f"SUBMISSIONS ARMED — {text}"
        data = OverviewData(
            metrics=[],
            research_metrics=[],
            flow=flow,
            current_stage=first_incomplete,
            recommendation=OverviewRecommendation(
                text=text,
                actions=[OverviewAction(label="Open event control", to="/event")],
            ),
            score_history=[],
            experiments=[],
            fold_evidence=[],
            upload_quota=[],
            latest_decisions=[],
        )
        return self.envelope(
            "overview",
            data,
            provenance=Provenance.LOCAL_EXPERIMENT,
            source="Local research state",
        )

    def event_control(self) -> DataEnvelope[EventControlData]:
        state = self.state()
        observed = utc_now()
        opened = state.get("round_opened_at")
        deadline = state.get("round_deadline_at")
        snapshot_at = state.get("snapshot_at")
        mode = self._submission_mode(state)
        data = EventControlData(
            connection=EventControlConnection(
                api_status=self._connection(state),
                sdk_version="everestapi 0.3.22",
                scope=str(state.get("scope") or "UNKNOWN"),
                key_fingerprint="NOT EXPOSED",
                last_request_at=state.get("last_request_at"),
            ),
            event_state=EventControlEventState(
                event_id=state.get("event_id"),
                tournament=state.get("tournament"),
                phase=state.get("event_phase"),
                current_round=state.get("round"),
                round_opened_at=opened,
                time_remaining=self._format_countdown(state.get("time_remaining_seconds")),
            ),
            scoring=EventControlScoring(
                rank_metric=state.get("rank_metric"),
                primary_target=state.get("primary_target"),
                components=[],
                snapshot_at=snapshot_at,
            ),
            capabilities=[],
            autopilot_active=bool(state.get("autopilot_active")),
            submission_mode=mode,
            latest_snapshot=state.get("event_snapshot_id"),
            updated_at=observed,
            stale=self._connection(state) is not ConnectionState.LIVE,
            server_observed_at=observed,
            round_opened_at=opened,
            round_deadline_at=deadline,
            snapshot_at=snapshot_at,
        )
        return self.envelope(
            "event_control",
            data,
            provenance=Provenance.OFFICIAL_EVENT_STATE,
            source="Research state; unavailable fields remain null/UNKNOWN",
            stale=data.stale,
        )

    def round_room(self) -> DataEnvelope[RoundRoomData]:
        state = self.state()
        observed = utc_now()
        mode = self._submission_mode(state)
        jobs = self._jobs(self.repo_root)
        event_log = []
        if mode == "ARMED":
            event_log.append(
                RoundEventLogEntry(ts=observed, msg="SUBMISSIONS ARMED", level="warn")
            )
        data = RoundRoomData(
            round_id=state.get("round"),
            round_status=str(state.get("round_status") or "unknown").lower(),
            countdown=self._format_countdown(state.get("time_remaining_seconds")),
            split_fingerprint=state.get("split_fingerprint"),
            live_rows=state.get("live_rows"),
            submissions_used_round=state.get("submissions_used_round"),
            submissions_used_event=state.get("submissions_used_event"),
            submissions_total_event=state.get("upload_budget", {}).get("cap"),
            live_feed=self._connection(state),
            inference_queue=[job for job in jobs if job["type"] == "INFER"],
            submission_queue=[job for job in jobs if job["type"] == "SUBMIT"],
            current_board=[],
            event_log=event_log,
            emergency=RoundEmergency(
                champion=state.get("champion"),
                ensemble=state.get("ensemble", {}).get("blend_id"),
                model_hash=state.get("model_hash"),
                split_verified=bool(state.get("split_verified", False)),
                submission_ready=bool(state.get("submission_ready", False)),
            ),
            rank_by_round=[],
            heatmap_data=self._heatmap_cells(state),
            submission_mode=mode,
            updated_at=observed,
            stale=self._connection(state) is not ConnectionState.LIVE,
            server_observed_at=observed,
            round_opened_at=state.get("round_opened_at"),
            round_deadline_at=state.get("round_deadline_at"),
            snapshot_at=state.get("snapshot_at"),
        )
        return self.envelope(
            "round_room",
            data,
            provenance=Provenance.OFFICIAL_EVENT_STATE,
            source="Official round data unavailable"
            if not state.get("event_snapshot_id")
            else "Everesteer event snapshot",
            stale=data.stale,
        )

    def data_lab(self) -> DataEnvelope[DataLabData]:
        datasets: list[DataSetCard] = []
        synthetic = False
        audit_paths = sorted((self.repo_root / "data").rglob("*audit*.json"))
        for audit_path in audit_paths:
            try:
                payload = json.loads(audit_path.read_text(encoding="utf-8"))
            except (OSError, ValueError, TypeError):
                continue
            records: list[tuple[str, dict[str, Any]]] = []
            if isinstance(payload, dict) and "rows" in payload:
                records.append((audit_path.stem, payload))
            elif isinstance(payload, dict):
                records.extend(
                    (str(name), value)
                    for name, value in payload.items()
                    if isinstance(value, dict) and "rows" in value
                )
            for split, audit in records:
                is_synthetic = "synthetic" in {
                    part.lower() for part in audit_path.relative_to(self.repo_root).parts
                }
                synthetic = synthetic or is_synthetic
                missingness = audit.get("missingness") or {}
                messages = [
                    DataSetIntegrityMessage(level="warn", text=str(message))
                    for message in audit.get("warnings", [])
                ]
                messages.extend(
                    DataSetIntegrityMessage(level="error", text=str(message))
                    for message in audit.get("hard_failures", [])
                )
                integrity = str(audit.get("integrity") or "warn").lower()
                if integrity not in {"pass", "warn", "fail"}:
                    integrity = "warn"
                datasets.append(
                    DataSetCard(
                        split=split,
                        label=f"{split} (SYNTHETIC)" if is_synthetic else split,
                        hash=str(audit.get("schema_sha256") or ""),
                        rows=audit.get("rows"),
                        cols=audit.get("columns"),
                        expeds=audit.get("exped_count"),
                        features=len(audit.get("feature_columns") or []),
                        targets=len(audit.get("target_columns") or []),
                        target_available=bool(audit.get("target_available", False)),
                        duplicates=audit.get("duplicate_ids"),
                        missingness_pct=(
                            max(float(value) for value in missingness.values()) * 100
                            if missingness
                            else None
                        ),
                        memory_mb=(
                            float(audit["memory_bytes_estimate"]) / 2**20
                            if audit.get("memory_bytes_estimate") is not None
                            else None
                        ),
                        updated_at=datetime.fromtimestamp(
                            audit_path.stat().st_mtime, UTC
                        ).replace(microsecond=0).isoformat(),
                        integrity_status=integrity,
                        integrity_messages=messages,
                    )
                )
        data = DataLabData(
            datasets=datasets,
            rows_per_exped=[],
            missingness=[],
            cardinality=[],
            target_dist=[],
            schema_diff=[],
            drift=DataLabDrift(
                schema_drift=None,
                missingness_drift=None,
                cardinality_drift=None,
                id_overlap_pct=None,
            ),
        )
        return self.envelope(
            "data_lab",
            data,
            provenance=(
                Provenance.SYNTHETIC_FIXTURE if synthetic else Provenance.LOCAL_EXPERIMENT
            ),
            source=(
                "Local synthetic dataset audit (SYNTHETIC_FIXTURE)"
                if synthetic
                else "Local dataset audits"
                if datasets
                else "No audited dataset manifests available"
            ),
        )

    def experiments(self) -> DataEnvelope[list[Any]]:
        rows: list[ExperimentRow] = []
        experiments_root = self.repo_root / "runs" / "experiments"
        for manifest_path in sorted(experiments_root.glob("*/run.json")):
            try:
                manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
                run_dir = manifest_path.parent
                metrics_path = run_dir / "metrics.json"
                decision_path = run_dir / "decision.json"
                metrics = (
                    json.loads(metrics_path.read_text(encoding="utf-8"))
                    if metrics_path.is_file()
                    else {}
                )
                decision_data = (
                    json.loads(decision_path.read_text(encoding="utf-8"))
                    if decision_path.is_file()
                    else {}
                )
                config = manifest.get("config") if isinstance(manifest.get("config"), dict) else {}
                raw_status = str(manifest.get("status") or "").upper()
                status = (
                    "failed"
                    if raw_status == "FAILED"
                    else "active"
                    if raw_status in {"RUNNING", "COMPLETED"}
                    else "invalid"
                )
                decision_raw = str(decision_data.get("decision") or RaceDecision.PENDING.value)
                try:
                    decision = RaceDecision(decision_raw)
                except ValueError:
                    decision = RaceDecision.PENDING
                profile = str(config.get("profile") or "R1").upper()
                stage = profile if profile in {"R0", "R1", "R2", "R3"} else "frontier"
                score = metrics.get("score") if isinstance(metrics, dict) else None
                rows.append(
                    ExperimentRow(
                        run=str(manifest.get("run_id") or run_dir.name),
                        family=str(config.get("model") or "UNKNOWN"),
                        operator=str(config.get("operator") or "UNKNOWN"),
                        parent=str(config.get("parent") or ""),
                        hypothesis=str(config.get("hypothesis") or ""),
                        race_stage=stage,
                        local_score=score if isinstance(score, (int, float)) else None,
                        recent_score=None,
                        lower_quantile=None,
                        stability=None,
                        runtime_seconds=float(manifest.get("runtime_seconds") or 0),
                        diversity=float(metrics.get("diversity") or 0),
                        practice_score=None,
                        live_score=None,
                        status=status,
                        race_decision=decision,
                        children=[],
                        oof_path=str(run_dir / "oof.parquet")
                        if (run_dir / "oof.parquet").is_file()
                        else "",
                        artefact=str(manifest.get("model_id") or ""),
                        logs=[str(manifest.get("error"))] if manifest.get("error") else [],
                        provenance=Provenance.LOCAL_EXPERIMENT,
                        generated_at=str(
                            manifest.get("completed_at")
                            or manifest.get("started_at")
                            or utc_now()
                        ),
                    )
                )
            except (OSError, ValueError, TypeError):
                continue
        return self.envelope(
            "experiments",
            rows,
            provenance=Provenance.LOCAL_EXPERIMENT,
            source="Local experiment manifests",
        )

    def validation(self) -> DataEnvelope[ValidationData]:
        data = ValidationData(
            hard_integrity=[],
            soft_research=[],
            race_decision=ValidationRaceDecision(
                decision=RaceDecision.PENDING,
                rationale="No validated experiment evidence is available.",
                stage="UNKNOWN",
            ),
            fold_heatmap=[],
            score_dist=[],
            timeline=[],
            updated_at=utc_now(),
        )
        return self.envelope(
            "validation",
            data,
            provenance=Provenance.LOCAL_EXPERIMENT,
            source="Local validation evidence unavailable",
        )

    def models(self) -> DataEnvelope[list[Any]]:
        state = self.state()
        now = utc_now()
        rows: list[ModelRow] = []
        for alias in self._model_ids(state):
            rows.append(
                ModelRow(
                    private_alias=alias,
                    public_alias=f"pub-{alias}",
                    family="UNKNOWN",
                    params="",
                    parent="",
                    data_hash="",
                    pickle_hash="",
                    pickle_status="missing",
                    local_score=None,
                    recent_score=None,
                    icir=None,
                    worst_fold=None,
                    inference_p50_ms=None,
                    inference_p95_ms=None,
                    model_size_mb=None,
                    exposure=None,
                    corr_to_champion=None,
                    lifecycle="active",
                    practice_score=None,
                    live_score=None,
                    fold_performance=[],
                    feature_importance=[],
                    provenance=Provenance.LOCAL_EXPERIMENT,
                    generated_at=now,
                )
            )
        return self.envelope(
            "models",
            rows,
            provenance=Provenance.LOCAL_EXPERIMENT,
            source="Local model registry / research frontier",
        )

    def feature_lab(self) -> DataEnvelope[FeatureLabData]:
        data = FeatureLabData(
            summary=FeatureLabSummary(
                feature_count=None,
                high_missingness=None,
                unstable=None,
                high_exposure=None,
                selected_by_frontier=None,
            ),
            features=[],
            importance_series=[],
            correlation_matrix=[],
        )
        return self.envelope(
            "feature_lab",
            data,
            provenance=Provenance.LOCAL_EXPERIMENT,
            source="Feature evidence unavailable",
        )

    def ensembles(self) -> DataEnvelope[EnsembleData]:
        state = self.state()
        data = EnsembleData(
            current_blend=str(state.get("ensemble", {}).get("blend_id") or "NONE"),
            available_strategies=list(EnsembleStrategy),
            active_strategy=EnsembleStrategy.RANK_AVERAGE,
            candidate_pool=[],
            members=[],
            metrics=EnsembleMetrics(
                local_uplift_vs_best=None,
                recent_uplift=None,
                worst_fold_change=None,
                mean_pairwise_corr=None,
                effective_models=None,
                exposure_change=None,
                practice_uplift=None,
                live_uplift=None,
            ),
            pred_correlation=[],
            marginal_contrib=[],
            score_diversity_scatter=[],
            fold_score=[],
        )
        return self.envelope(
            "ensembles",
            data,
            provenance=Provenance.LOCAL_EXPERIMENT,
            source="Local ensemble state",
        )

    def leaderboard(self) -> DataEnvelope[LeaderboardData]:
        state = self.state()
        connected = self._connection(state) is ConnectionState.LIVE
        matrix = self._round_model_matrix(state)
        source = (
            "Everesteer platform observation"
            if connected
            else "NOT CONNECTED / official leaderboard unavailable"
        )
        data = LeaderboardData(
            source=source,
            current_round=[],
            cumulative=[],
            our_aliases=[],
            history=[],
            rank_trajectory=[],
            score_trajectory=[],
            round_model_matrix=matrix,
        )
        return self.envelope(
            "leaderboard",
            data,
            provenance=Provenance.OFFICIAL_PLATFORM_OBSERVATION,
            source=data.source,
            stale=not connected,
        )

    def submission(self) -> DataEnvelope[SubmissionData]:
        state = self.state()
        mode = self._submission_mode(state)
        message = "SUBMISSIONS ARMED" if mode == "ARMED" else f"Submission mode: {mode}"
        data = SubmissionData(
            quota_total=state.get("upload_budget", {}).get("cap"),
            quota_used=state.get("submissions_used_event"),
            quota_practice=state.get("upload_budget", {}).get("practice_remaining"),
            quota_live_reserve=state.get("upload_budget", {}).get("live_remaining"),
            quota_emergency=None,
            candidates=[],
            stepper_steps=[
                SubmissionStepperStep(
                    label="Submission mode",
                    status=StepStatus.PASS if mode == "ARMED" else StepStatus.BLOCKED,
                    message=message,
                )
            ],
            selected_candidate=None,
            submission_mode=mode,
        )
        return self.envelope(
            "submission",
            data,
            provenance=Provenance.LOCAL_EXPERIMENT,
            source="Local submission state",
        )

    def staking(self) -> DataEnvelope[StakingData]:
        state = self.state()
        classification = classify_staking(state.get("staking"))
        mapped = classification.to_dict()["figma_stake_mode"]
        data = StakingData(
            classification=StakingClassification(mapped),
            statement=(
                "Stake mode UNKNOWN; no allocation or transaction is permitted."
                if mapped == "UNKNOWN"
                else f"Stake mode classified as {mapped}; this console never sends wallet transactions."
            ),
            virtual_balance=classification.raw_signals.get("virtual_balance")
            or classification.raw_signals.get("event_balance"),
            evidence="; ".join(classification.reasons),
            uncertainty=classification.confidence,
            candidates=[],
            concentration=None,
            risk_profile="UNKNOWN",
            requires_confirmation=classification.human_only,
            updated_at=utc_now(),
        )
        return self.envelope(
            "staking",
            data,
            provenance=Provenance.OFFICIAL_EVENT_STATE,
            source="Explicit event staking signals only",
            stale=mapped == "UNKNOWN",
        )

    def compute(self) -> DataEnvelope[ComputeData]:
        vm = psutil.virtual_memory()
        disk = psutil.disk_usage(str(self.repo_root))
        jobs = self._jobs(self.repo_root)
        data = ComputeData(
            hardware=ComputeHardware(
                os=platform.platform(),
                cpu=ComputeCpu(
                    model=platform.processor() or None,
                    cores=psutil.cpu_count(),
                    used_pct=psutil.cpu_percent(interval=None),
                ),
                ram=ComputeRam(
                    used_gb=round(vm.used / 2**30, 2),
                    total_gb=round(vm.total / 2**30, 2),
                ),
                gpu=ComputeGpu(
                    name=None, vram_used_gb=None, vram_total_gb=None, cuda=None
                ),
                disk=ComputeDisk(
                    used_gb=round(disk.used / 2**30, 2),
                    total_gb=round(disk.total / 2**30, 2),
                ),
            ),
            utilisation=ComputeUtilisation(
                gpu_util_pct=None,
                vram_util_pct=None,
                ram_pressure_pct=vm.percent,
                queue_length=sum(job["status"] == "QUEUED" for job in jobs),
                experiments_per_hour=None,
            ),
            local_queue=jobs,
            server_queue=[],
            event_watcher=ComputeEventWatcher(
                active=False, last_ping=utc_now(), interval="not running"
            ),
            runtime_history=[],
            updated_at=utc_now(),
        )
        return self.envelope(
            "compute",
            data,
            provenance=Provenance.LOCAL_EXPERIMENT,
            source="Local host and filesystem job queue",
        )

    def repository(self) -> DataEnvelope[RepoData]:
        unknown = RepoCheckResult(status="unknown", at=None, detail="No persisted result")
        data = RepoData(
            serving_branch=None,
            serving_sha=None,
            dirty=False,
            python_version=platform.python_version(),
            everest_api_pin="everestapi==0.3.22",
            lockfile_hash=None,
            frontend_build_sha=None,
            backend_build_sha=None,
            last_tests=unknown,
            last_rehearsal=unknown,
            last_scorer_parity=unknown,
            env_health="unknown",
            latest_commits=[],
            updated_at=utc_now(),
        )
        return self.envelope(
            "repository",
            data,
            provenance=Provenance.MANUALLY_RECORDED,
            source="Repository metadata unavailable without invoking git",
        )

    def documentation(self) -> DataEnvelope[DocumentationData]:
        articles: list[DocArticle] = []
        generated_at = None
        sections: list[DocSection] = []

        curated = collect_curated_articles(self.repo_root)
        for item in curated:
            articles.append(
                DocArticle(
                    id=str(item["id"]),
                    title=str(item["title"]),
                    description=str(item.get("description") or ""),
                    section=str(item.get("section") or "flows"),
                    order=int(item.get("order") or 100),
                    source="curated",
                    blocks=self._doc_blocks(list(item.get("blocks") or [])),
                )
            )
        for section in curated_sections(curated):
            sections.append(DocSection(id=section["id"], label=section["label"]))

        manifest_path = self.repo_root / "dashboard/frontend/src/generated/docs-manifest.json"
        curated_path = self.repo_root / "docs/generated/curated-articles.json"
        for path in (curated_path, manifest_path):
            if path.is_file():
                try:
                    payload = json.loads(path.read_text(encoding="utf-8"))
                    generated_at = payload.get("generated_at") or generated_at
                except (OSError, ValueError, TypeError):
                    pass

        if manifest_path.is_file():
            try:
                manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
                generated_at = manifest.get("generated_at") or generated_at
                existing_ids = {article.id for article in articles}
                for index, item in enumerate(manifest.get("articles", [])):
                    article_id = str(item.get("id"))
                    if article_id in existing_ids:
                        continue
                    source = str(item.get("source") or "generated")
                    if source not in {"generated", "curated"}:
                        source = "generated"
                    raw_blocks = item.get("blocks")
                    blocks = (
                        self._doc_blocks(list(raw_blocks))
                        if isinstance(raw_blocks, list) and raw_blocks
                        else [
                            DocIntroBlock(
                                kind="intro",
                                text=f"Generated reference: {item.get('path', 'UNKNOWN')}",
                            )
                        ]
                    )
                    articles.append(
                        DocArticle(
                            id=article_id,
                            title=str(item.get("title")),
                            description=str(item.get("description") or item.get("path") or ""),
                            section=str(item.get("section") or "generated"),
                            order=int(item.get("order") if item.get("order") is not None else 1000 + index),
                            source=source,  # type: ignore[arg-type]
                            blocks=blocks,
                        )
                    )
                if not sections:
                    for section in manifest.get("sections") or []:
                        if isinstance(section, dict) and section.get("id"):
                            sections.append(
                                DocSection(
                                    id=str(section["id"]),
                                    label=str(section.get("label") or section["id"]),
                                )
                            )
            except (OSError, ValueError, TypeError):
                pass

        if articles and not any(section.id == "generated" for section in sections):
            if any(article.source == "generated" for article in articles):
                sections.append(DocSection(id="generated", label="Generated reference"))

        data = DocumentationData(
            generated_from_sha=None,
            generated_at=generated_at,
            sections=sections,
            articles=articles,
        )
        return self.envelope(
            "documentation",
            data,
            provenance=Provenance.MANUALLY_RECORDED,
            source="Curated MDX flows/runbooks + generated documentation manifest",
            refresh_mode="manual",
        )

    @staticmethod
    def _format_countdown(seconds: Any) -> str | None:
        if not isinstance(seconds, (int, float)) or seconds < 0:
            return None
        total = int(seconds)
        hours, remainder = divmod(total, 3600)
        minutes, secs = divmod(remainder, 60)
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
