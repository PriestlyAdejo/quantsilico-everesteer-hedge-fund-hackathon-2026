"""Deterministic SYNTHETIC_FIXTURE envelopes for golden contract tests."""

from __future__ import annotations

from typing import TypeVar

from qs_everesteer.api_schemas.common import (
    CapabilityStatus,
    ConnectionState,
    FlowNode,
    FlowState,
    Job,
    JobStatus,
    MetricCardData,
    ScoringComponent,
)
from qs_everesteer.api_schemas.envelope import (
    SCHEMA_VERSION,
    ActionResult,
    DataEnvelope,
    Provenance,
)
from qs_everesteer.api_schemas.pages import (
    ComputeCpu,
    ComputeData,
    ComputeDisk,
    ComputeEventWatcher,
    ComputeGpu,
    ComputeHardware,
    ComputeRam,
    ComputeRuntimePoint,
    ComputeUtilisation,
    DataLabCardinality,
    DataLabData,
    DataLabDrift,
    DataLabMissingness,
    DataLabRowsPerExped,
    DataLabSchemaDiff,
    DataLabTargetBucket,
    DataSetCard,
    DataSetIntegrityMessage,
    DocArticle,
    DocIntroBlock,
    DocSection,
    DocumentationData,
    EnsembleCandidate,
    EnsembleData,
    EnsembleMarginalContrib,
    EnsembleMember,
    EnsembleMetrics,
    EnsemblePredCorr,
    EnsembleScoreDiversity,
    EnsembleStrategy,
    EventControlCapability,
    EventControlConnection,
    EventControlData,
    EventControlEventState,
    EventControlScoring,
    EventRoundInfo,
    EventStatus,
    EventUploadsInfo,
    ExperimentRow,
    FeatureCorrelationCell,
    FeatureImportancePoint,
    FeatureLabData,
    FeatureLabFeature,
    FeatureLabSummary,
    HardIntegrityCheck,
    LeaderBoardEntry,
    LeaderboardData,
    LeaderboardHistoryPoint,
    LeaderboardModelMatrixCell,
    LeaderboardRankPoint,
    LeaderboardScorePoint,
    ModelFeatureImportance,
    ModelFoldPerformance,
    ModelRow,
    OurAliasEntry,
    OverviewAction,
    OverviewData,
    OverviewDecision,
    OverviewExperimentPoint,
    OverviewFoldEvidence,
    OverviewQuotaSlice,
    OverviewRecommendation,
    OverviewScorePoint,
    RaceDecision,
    RepoCheckResult,
    RepoCommit,
    RepoData,
    RoundEmergency,
    RoundEventLogEntry,
    RoundHeatmapCell,
    RoundRankPoint,
    RoundRoomData,
    SoftResearchMetric,
    StakingCandidate,
    StakingClassification,
    StakingData,
    StepStatus,
    SubmissionCandidate,
    SubmissionData,
    SubmissionStepperStep,
    ValidationData,
    ValidationFoldCell,
    ValidationRaceDecision,
    ValidationScoreBucket,
    ValidationTimelinePoint,
)

_NOW = "2026-08-12T10:00:00Z"
_AGO = "2026-08-12T09:56:00Z"
_SOURCE = "Local research store (SYNTHETIC_FIXTURE)"

T = TypeVar("T")


def _env(kind: str, data: T, *, source: str = _SOURCE) -> DataEnvelope[T]:
    return DataEnvelope(
        schema_version=SCHEMA_VERSION,
        kind=kind,
        provenance=Provenance.SYNTHETIC_FIXTURE,
        generated_at=_NOW,
        stale=False,
        source=source,
        refresh_mode="poll",
        data=data,
    )


def _job(**kwargs: object) -> Job:
    base = {
        "candidate": None,
        "started_at": None,
        "eta_seconds": None,
        "total_seconds": None,
        "progress": None,
        "queue_position": None,
        "device": "CPU",
    }
    base.update(kwargs)
    return Job.model_validate(base)


def example_action_result() -> ActionResult:
    return ActionResult(
        ok=True,
        message="Event refreshed",
        code="OK",
        timestamp=_NOW,
    )


def example_event_status() -> DataEnvelope[EventStatus]:
    return _env(
        "event_status",
        EventStatus(
            connection=ConnectionState.LIVE,
            last_update_at=_AGO,
            event_id="SYNTHETIC-EVENT-2026",
            event_phase="QUALIFYING",
            round=EventRoundInfo(index=3, total=8, label="R3"),
            uploads=EventUploadsInfo(used=12, total=20),
            champion="blend-01",
            external_rank=2,
            autopilot=False,
            scope="research:read+submit",
        ),
    )


def example_overview() -> DataEnvelope[OverviewData]:
    meta = dict(provenance=Provenance.SYNTHETIC_FIXTURE, generated_at=_NOW)
    return _env(
        "overview",
        OverviewData(
            metrics=[
                MetricCardData(label="Event phase", value="Qualifying", **meta),
                MetricCardData(label="Champion", value="blend-01", **meta),
            ],
            research_metrics=[
                MetricCardData(label="CORR20", value="0.0421", term="CORR20", **meta),
            ],
            flow=[
                FlowNode(id="connect", label="Connect event", state=FlowState.COMPLETE),
                FlowNode(id="baseline", label="Baseline proven", state=FlowState.ACTIVE),
            ],
            current_stage="baseline",
            recommendation=OverviewRecommendation(
                text="Reproduce the organiser baseline before starting the research race.",
                actions=[OverviewAction(label="Run baseline", to="/event")],
            ),
            score_history=[OverviewScorePoint(round="R1", score=0.69, rank=8)],
            experiments=[
                OverviewExperimentPoint(
                    runtime_seconds=42,
                    score=0.71,
                    diversity=0.55,
                    family="lgbm",
                    stage="R1",
                    name="run-001",
                )
            ],
            fold_evidence=[
                OverviewFoldEvidence(fold="F0", r0=0.64, r1=0.67, r2=0.70, r3=0.72)
            ],
            upload_quota=[OverviewQuotaSlice(label="Used", value=12, fill="#38BDF8")],
            latest_decisions=[
                OverviewDecision(ts=_AGO, text="blend-01 advanced to R3", level="info")
            ],
        ),
    )


def example_event_control() -> DataEnvelope[EventControlData]:
    return _env(
        "event_control",
        EventControlData(
            connection=EventControlConnection(
                api_status=ConnectionState.LIVE,
                sdk_version="everestapi 0.3.22",
                scope="research:read+submit",
                key_fingerprint="ek_live_••••_1A2B",
                last_request_at=_AGO,
            ),
            event_state=EventControlEventState(
                event_id="SYNTHETIC-EVENT-2026",
                tournament="Synthetic Everesteer Fixture",
                phase="Qualifying",
                current_round="R3",
                round_opened_at=_AGO,
                time_remaining="02:14:33",
            ),
            scoring=EventControlScoring(
                rank_metric="CORR20",
                primary_target="target_20d",
                components=[
                    ScoringComponent(name="CORR20", weight=0.6, value=0.0421, provided=True),
                    ScoringComponent(name="NCORR", weight=0.15, value=None, provided=False),
                ],
                snapshot_at=_AGO,
            ),
            capabilities=[
                EventControlCapability(name="Practice submissions", status=CapabilityStatus.AVAILABLE),
                EventControlCapability(name="Event staking", status=CapabilityStatus.UNAVAILABLE),
            ],
            autopilot_active=False,
            latest_snapshot="snap-synthetic-001",
            updated_at=_NOW,
            stale=False,
            server_observed_at=_NOW,
            round_opened_at=_AGO,
            round_deadline_at="2026-08-12T12:14:33Z",
            snapshot_at=_AGO,
        ),
    )


def example_round_room() -> DataEnvelope[RoundRoomData]:
    board = [
        LeaderBoardEntry(
            rank=1,
            alias="blend-01",
            score=0.739,
            score_change=0.011,
            rank_change=1,
            round="R3",
            is_ours=True,
            provenance=Provenance.SYNTHETIC_FIXTURE,
            generated_at=_NOW,
        )
    ]
    return _env(
        "round_room",
        RoundRoomData(
            round_id="R3-SYNTHETIC",
            round_status="open",
            countdown="02:14:33",
            split_fingerprint="fp-synthetic",
            live_rows=4820,
            submissions_used_round=1,
            submissions_used_event=12,
            submissions_total_event=20,
            live_feed=ConnectionState.LIVE,
            inference_queue=[
                _job(
                    id="infer-0",
                    name="blend-01",
                    type="INFER",
                    candidate="blend-01",
                    status=JobStatus.RUNNING,
                    started_at=_AGO,
                    eta_seconds=120,
                    progress=0.62,
                    device="GPU",
                )
            ],
            submission_queue=[
                _job(
                    id="sub-0",
                    name="blend-01 → live",
                    type="SUBMIT",
                    candidate="blend-01",
                    status=JobStatus.DONE,
                    started_at=_AGO,
                    total_seconds=22,
                )
            ],
            current_board=board,
            event_log=[
                RoundEventLogEntry(ts=_AGO, msg="Round R3 opened", level="info")
            ],
            emergency=RoundEmergency(
                champion="blend-01",
                ensemble="blend-01",
                model_hash="sha256:synthetic",
                split_verified=True,
                submission_ready=True,
            ),
            rank_by_round=[RoundRankPoint(round="R3", rank=2)],
            heatmap_data=[RoundHeatmapCell(model="blend-01", round="R3", score=0.739)],
            updated_at=_NOW,
            stale=False,
            server_observed_at=_NOW,
            round_opened_at=_AGO,
            round_deadline_at="2026-08-12T12:14:33Z",
            snapshot_at=_AGO,
        ),
    )


def example_data_lab() -> DataEnvelope[DataLabData]:
    return _env(
        "data_lab",
        DataLabData(
            datasets=[
                DataSetCard(
                    split="train",
                    label="Train",
                    hash="sha256:synthetic-train",
                    rows=480000,
                    cols=312,
                    expeds=240,
                    features=308,
                    targets=1,
                    target_available=True,
                    duplicates=0,
                    missingness_pct=1.2,
                    memory_mb=1420,
                    updated_at=_NOW,
                    integrity_status="pass",
                    integrity_messages=[],
                ),
                DataSetCard(
                    split="practice",
                    label="Practice",
                    hash="sha256:synthetic-practice",
                    rows=120000,
                    cols=312,
                    expeds=60,
                    features=308,
                    targets=1,
                    target_available=True,
                    duplicates=0,
                    missingness_pct=2.8,
                    memory_mb=360,
                    updated_at=_NOW,
                    integrity_status="warn",
                    integrity_messages=[
                        DataSetIntegrityMessage(
                            level="warn",
                            text="SYNTHETIC: 3 features have elevated missingness",
                        )
                    ],
                ),
            ],
            rows_per_exped=[DataLabRowsPerExped(exped="E001", rows=2000)],
            missingness=[DataLabMissingness(feature="f_anon_001", pct=1.5)],
            cardinality=[DataLabCardinality(feature="f_anon_001", unique=120)],
            target_dist=[DataLabTargetBucket(bucket="0.0–0.1", count=40000)],
            schema_diff=[
                DataLabSchemaDiff(
                    field="f_anon_001",
                    train_type="float32",
                    val_type="float32",
                    match=True,
                )
            ],
            drift=DataLabDrift(
                schema_drift=1,
                missingness_drift=0.031,
                cardinality_drift=0.008,
                id_overlap_pct=0,
            ),
        ),
    )


def example_experiments() -> DataEnvelope[list[ExperimentRow]]:
    rows = [
        ExperimentRow(
            run="run-001",
            family="lgbm",
            operator="tune",
            parent="—",
            hypothesis="SYNTHETIC: vary learning rate to lift CORR20.",
            race_stage="R1",
            local_score=0.71,
            recent_score=0.70,
            lower_quantile=0.68,
            stability=0.82,
            runtime_seconds=120,
            diversity=0.55,
            practice_score=0.705,
            live_score=None,
            status="active",
            race_decision=RaceDecision.PROMOTE_TOP_SCORE,
            children=["run-002"],
            oof_path="oof/run-001.parquet",
            artefact="artefacts/run-001.pkl",
            logs=["train start", "scored"],
            provenance=Provenance.SYNTHETIC_FIXTURE,
            generated_at=_NOW,
        )
    ]
    return _env("experiments", rows)


def example_validation() -> DataEnvelope[ValidationData]:
    return _env(
        "validation",
        ValidationData(
            hard_integrity=[
                HardIntegrityCheck(check="Schema", status="PASS", detail="All features present")
            ],
            soft_research=[
                SoftResearchMetric(
                    metric="Rank metric (CORR20)",
                    term="CORR20",
                    interpretation="STRONG",
                    value="0.0421",
                    detail="Above baseline",
                )
            ],
            race_decision=ValidationRaceDecision(
                decision=RaceDecision.PROMOTE_DIVERSITY,
                rationale="SYNTHETIC: diversity value is strong.",
                stage="R1 → R2",
            ),
            fold_heatmap=[ValidationFoldCell(fold="F0", round="R1", score=0.70)],
            score_dist=[ValidationScoreBucket(bucket="0.70", count=5)],
            timeline=[ValidationTimelinePoint(ts=_AGO, score=0.70)],
            updated_at=_NOW,
        ),
    )


def example_models() -> DataEnvelope[list[ModelRow]]:
    rows = [
        ModelRow(
            private_alias="blend-01",
            public_alias="alias-0001",
            family="blend",
            params="w=[0.4,0.3,0.2,0.1]",
            parent="organiser-lgbm",
            data_hash="sha256:data",
            pickle_hash="sha256:pickle",
            pickle_status="verified",
            local_score=0.72,
            recent_score=0.71,
            icir=1.3,
            worst_fold=0.68,
            inference_p50_ms=900,
            inference_p95_ms=1400,
            model_size_mb=42,
            exposure=0.7,
            corr_to_champion=1.0,
            lifecycle="active",
            practice_score=0.715,
            live_score=0.718,
            fold_performance=[ModelFoldPerformance(fold="F0", score=0.71)],
            feature_importance=[
                ModelFeatureImportance(feature="f_anon_001", importance=0.2)
            ],
            provenance=Provenance.SYNTHETIC_FIXTURE,
            generated_at=_NOW,
        )
    ]
    return _env("models", rows)


def example_feature_lab() -> DataEnvelope[FeatureLabData]:
    features = [
        FeatureLabFeature(
            id="f_anon_001",
            missingness=1.2,
            cardinality=100,
            importance=0.4,
            importance_std=0.05,
            redundancy=0.2,
            exposure=60,
            selection_freq=80,
            drift=0.1,
        )
    ]
    return _env(
        "feature_lab",
        FeatureLabData(
            summary=FeatureLabSummary(
                feature_count=1,
                high_missingness=0,
                unstable=0,
                high_exposure=0,
                selected_by_frontier=1,
            ),
            features=features,
            importance_series=[
                FeatureImportancePoint(feature="f_anon_001", importance=0.4)
            ],
            correlation_matrix=[
                FeatureCorrelationCell(a="f_anon_001", b="f_anon_001", corr=1.0)
            ],
        ),
    )


def example_ensembles() -> DataEnvelope[EnsembleData]:
    return _env(
        "ensembles",
        EnsembleData(
            current_blend="blend-01",
            available_strategies=[
                EnsembleStrategy.RANK_AVERAGE,
                EnsembleStrategy.WEIGHTED,
            ],
            active_strategy=EnsembleStrategy.WEIGHTED,
            candidate_pool=[
                EnsembleCandidate(model="blend-01", local_score=0.72, diversity=0.41)
            ],
            members=[
                EnsembleMember(
                    model="blend-01",
                    weight=1.0,
                    local_score=0.72,
                    practice_score=0.715,
                    live_score=0.718,
                )
            ],
            metrics=EnsembleMetrics(
                local_uplift_vs_best=0.0042,
                recent_uplift=0.0019,
                worst_fold_change=0.003,
                mean_pairwise_corr=0.58,
                effective_models=3.1,
                exposure_change=-0.04,
                practice_uplift=0.0026,
                live_uplift=None,
            ),
            pred_correlation=[EnsemblePredCorr(a="blend-01", b="blend-01", corr=1.0)],
            marginal_contrib=[EnsembleMarginalContrib(model="blend-01", contribution=0.01)],
            score_diversity_scatter=[
                EnsembleScoreDiversity(model="blend-01", score=0.72, diversity=0.41)
            ],
            fold_score=[],
        ),
    )


def example_leaderboard() -> DataEnvelope[LeaderboardData]:
    entry = LeaderBoardEntry(
        rank=2,
        alias="blend-01",
        score=0.739,
        score_change=0.011,
        rank_change=1,
        round="R3",
        is_ours=True,
        provenance=Provenance.SYNTHETIC_FIXTURE,
        generated_at=_NOW,
    )
    return _env(
        "leaderboard",
        LeaderboardData(
            source="Everesteer (SYNTHETIC)",
            current_round=[entry],
            cumulative=[entry],
            our_aliases=[
                OurAliasEntry(
                    **entry.model_dump(),
                    local_vs_practice_gap=0.0036,
                    practice_vs_live_gap=None,
                )
            ],
            history=[LeaderboardHistoryPoint(round="R3", rank=2, score=0.739)],
            rank_trajectory=[LeaderboardRankPoint(round="R3", rank=2)],
            score_trajectory=[LeaderboardScorePoint(round="R3", score=0.739)],
            round_model_matrix=[
                LeaderboardModelMatrixCell(model="blend-01", round="R3", score=0.739)
            ],
        ),
        source="Everesteer (SYNTHETIC)",
    )


def example_submission() -> DataEnvelope[SubmissionData]:
    return _env(
        "submission",
        SubmissionData(
            quota_total=20,
            quota_used=12,
            quota_practice=3,
            quota_live_reserve=3,
            quota_emergency=1,
            candidates=[
                SubmissionCandidate(
                    id="cand-1",
                    model="blend-01",
                    lane="live",
                    split_fingerprint="fp-synthetic",
                    id_coverage=100,
                    duplicates=0,
                    bounds_ok=True,
                    pickle_ok=True,
                    pred_hash="sha256:pred",
                    model_hash="sha256:model",
                    lineage="blend-01 ← baseline",
                    lane_allowed=True,
                    quota_allows=True,
                    integrity_ok=True,
                    blocking_reasons=[],
                )
            ],
            stepper_steps=[
                SubmissionStepperStep(label="Select", status=StepStatus.PASS, message="selected"),
                SubmissionStepperStep(
                    label="Infer",
                    status=StepStatus.RUNNING,
                    started_at=_AGO,
                    eta_seconds=120,
                ),
            ],
            selected_candidate="cand-1",
        ),
    )


def example_staking() -> DataEnvelope[StakingData]:
    return _env(
        "staking",
        StakingData(
            classification=StakingClassification.VIRTUAL_EVENT_BALANCE,
            statement="SYNTHETIC: This event uses a virtual competition balance. No real wallet is involved.",
            virtual_balance=10000,
            evidence="SYNTHETIC fixture — virtual credits only.",
            uncertainty="None — synthetic classification.",
            candidates=[
                StakingCandidate(
                    model="blend-01",
                    local_evidence=0.72,
                    live_evidence=0.718,
                    uncertainty=0.12,
                    correlation=1.0,
                    proposed_allocation_pct=100,
                )
            ],
            concentration=0.42,
            risk_profile="Moderate — virtual credits, no real exposure.",
            requires_confirmation=False,
            updated_at=_NOW,
        ),
    )


def example_compute() -> DataEnvelope[ComputeData]:
    return _env(
        "compute",
        ComputeData(
            hardware=ComputeHardware(
                os="Ubuntu 22.04 (SYNTHETIC)",
                cpu=ComputeCpu(model="Synthetic CPU", cores=8, used_pct=40),
                ram=ComputeRam(used_gb=8.0, total_gb=16.0),
                gpu=ComputeGpu(
                    name="Synthetic GPU",
                    vram_used_gb=4.0,
                    vram_total_gb=8.0,
                    cuda="12.4",
                ),
                disk=ComputeDisk(used_gb=100, total_gb=512),
            ),
            utilisation=ComputeUtilisation(
                gpu_util_pct=50,
                vram_util_pct=50,
                ram_pressure_pct=50,
                queue_length=1,
                experiments_per_hour=3.0,
            ),
            local_queue=[
                _job(
                    id="job-001",
                    name="LightGBM R2",
                    type="TRAIN",
                    candidate="lgbm-r2",
                    status=JobStatus.RUNNING,
                    started_at=_AGO,
                    eta_seconds=120,
                    progress=0.5,
                    device="GPU",
                )
            ],
            server_queue=[],
            event_watcher=ComputeEventWatcher(active=True, last_ping=_AGO, interval="30s"),
            runtime_history=[
                ComputeRuntimePoint(ts=_AGO, duration_min=12.0, type="TRAIN")
            ],
            updated_at=_NOW,
        ),
    )


def example_repository() -> DataEnvelope[RepoData]:
    return _env(
        "repository",
        RepoData(
            serving_branch="main",
            serving_sha="a1b2c3d",
            dirty=False,
            python_version="3.11.9",
            everest_api_pin="everestapi==0.3.22",
            lockfile_hash="sha256:lock-synthetic",
            frontend_build_sha="fe-synthetic",
            backend_build_sha="be-synthetic",
            last_tests=RepoCheckResult(status="passing", at=_AGO, detail="SYNTHETIC: tests ok"),
            last_rehearsal=RepoCheckResult(
                status="passing", at=_AGO, detail="SYNTHETIC: rehearsal ok"
            ),
            last_scorer_parity=RepoCheckResult(
                status="passing", at=_AGO, detail="SYNTHETIC: parity ok"
            ),
            env_health="healthy",
            latest_commits=[
                RepoCommit(
                    sha="a1b2c3d",
                    msg="SYNTHETIC: chore fixture commit",
                    author="researcher",
                    ts=_AGO,
                )
            ],
            updated_at=_NOW,
        ),
    )


def example_documentation() -> DataEnvelope[DocumentationData]:
    return _env(
        "documentation",
        DocumentationData(
            generated_from_sha="a1b2c3d",
            generated_at=_AGO,
            sections=[DocSection(id="start", label="Start Here")],
            articles=[
                DocArticle(
                    id="start-here",
                    title="Start Here",
                    description="SYNTHETIC docs intro.",
                    section="start",
                    order=10,
                    source="curated",
                    blocks=[
                        DocIntroBlock(
                            kind="intro",
                            text="SYNTHETIC: This console is your operating surface.",
                        )
                    ],
                )
            ],
        ),
    )


def all_example_envelopes() -> list[DataEnvelope]:
    """Every page-kind envelope used by golden tests."""
    return [
        example_event_status(),
        example_overview(),
        example_event_control(),
        example_round_room(),
        example_data_lab(),
        example_experiments(),
        example_validation(),
        example_models(),
        example_feature_lab(),
        example_ensembles(),
        example_leaderboard(),
        example_submission(),
        example_staking(),
        example_compute(),
        example_repository(),
        example_documentation(),
    ]
