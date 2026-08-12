"""Page DTOs mirroring contracts/figma/data/types.ts."""

from __future__ import annotations

from enum import StrEnum
from typing import Annotated, Literal

from pydantic import Field

from qs_everesteer.api_schemas.common import (
    CapabilityStatus,
    ConnectionState,
    FlowNode,
    Job,
    MetricCardData,
    ScoringComponent,
)
from qs_everesteer.api_schemas.envelope import ApiModel, ProvenanceMeta

# ─── Event status ───────────────────────────────────────────────


class EventRoundInfo(ApiModel):
    index: int | None
    total: int | None
    label: str | None


class EventUploadsInfo(ApiModel):
    used: int | None
    total: int | None


class EventStatus(ApiModel):
    connection: ConnectionState
    last_update_at: str | None
    event_id: str | None
    event_phase: str | None
    round: EventRoundInfo
    uploads: EventUploadsInfo
    champion: str | None
    external_rank: int | None
    autopilot: bool
    scope: str | None


# ─── Overview ───────────────────────────────────────────────────


class OverviewAction(ApiModel):
    label: str
    to: str


class OverviewRecommendation(ApiModel):
    text: str
    actions: list[OverviewAction]


class OverviewScorePoint(ApiModel):
    round: str
    score: float | None
    rank: int | None


class OverviewExperimentPoint(ApiModel):
    runtime_seconds: float
    score: float
    diversity: float
    family: str
    stage: str
    name: str


class OverviewFoldEvidence(ApiModel):
    fold: str
    r0: float
    r1: float
    r2: float
    r3: float


class OverviewQuotaSlice(ApiModel):
    label: str
    value: float
    fill: str


class OverviewDecision(ApiModel):
    ts: str
    text: str
    level: Literal["info", "warn", "error"]


class OverviewData(ApiModel):
    metrics: list[MetricCardData]
    research_metrics: list[MetricCardData]
    flow: list[FlowNode]
    current_stage: str
    recommendation: OverviewRecommendation
    score_history: list[OverviewScorePoint]
    experiments: list[OverviewExperimentPoint]
    fold_evidence: list[OverviewFoldEvidence]
    upload_quota: list[OverviewQuotaSlice]
    latest_decisions: list[OverviewDecision]


# ─── Event control ──────────────────────────────────────────────


class EventControlConnection(ApiModel):
    api_status: ConnectionState
    sdk_version: str
    scope: str
    key_fingerprint: str
    last_request_at: str | None


class EventControlEventState(ApiModel):
    event_id: str | None
    tournament: str | None
    phase: str | None
    current_round: str | None
    round_opened_at: str | None
    time_remaining: str | None


class EventControlScoring(ApiModel):
    rank_metric: str | None
    primary_target: str | None
    components: list[ScoringComponent]
    snapshot_at: str | None


class EventControlCapability(ApiModel):
    name: str
    status: CapabilityStatus


class EventControlData(ApiModel):
    connection: EventControlConnection
    event_state: EventControlEventState
    scoring: EventControlScoring
    capabilities: list[EventControlCapability]
    autopilot_active: bool
    submission_mode: Literal["DISABLED", "DRY_RUN", "ARMED"] = "DRY_RUN"
    latest_snapshot: str | None
    updated_at: str
    stale: bool
    # Optional authoritative timestamps (frontend may ignore until wired)
    server_observed_at: str | None = None
    round_opened_at: str | None = None
    round_deadline_at: str | None = None
    snapshot_at: str | None = None


# ─── Leaderboard entry (shared with Round Room) ─────────────────


class LeaderBoardEntry(ProvenanceMeta):
    rank: int | None
    alias: str
    score: float | None
    score_change: float | None
    rank_change: int | None
    round: str
    is_ours: bool


# ─── Round room ─────────────────────────────────────────────────


class RoundEventLogEntry(ApiModel):
    ts: str
    msg: str
    level: Literal["info", "warn", "error"]


class RoundEmergency(ApiModel):
    champion: str | None
    ensemble: str | None
    model_hash: str | None
    split_verified: bool
    submission_ready: bool


class RoundRankPoint(ApiModel):
    round: str
    rank: int | None


class RoundHeatmapCell(ApiModel):
    model: str
    round: str
    score: float


class RoundRoomData(ApiModel):
    round_id: str | None
    round_status: Literal["open", "closed", "scoring", "unknown"]
    countdown: str | None
    split_fingerprint: str | None
    live_rows: int | None
    submissions_used_round: int | None
    submissions_used_event: int | None
    submissions_total_event: int | None
    live_feed: ConnectionState
    inference_queue: list[Job]
    submission_queue: list[Job]
    current_board: list[LeaderBoardEntry]
    event_log: list[RoundEventLogEntry]
    emergency: RoundEmergency
    rank_by_round: list[RoundRankPoint]
    heatmap_data: list[RoundHeatmapCell]
    submission_mode: Literal["DISABLED", "DRY_RUN", "ARMED"] = "DRY_RUN"
    updated_at: str
    stale: bool
    # Optional authoritative timestamps (frontend may ignore until wired)
    server_observed_at: str | None = None
    round_opened_at: str | None = None
    round_deadline_at: str | None = None
    snapshot_at: str | None = None


# ─── Data lab ───────────────────────────────────────────────────


class DataSetIntegrityMessage(ApiModel):
    level: Literal["warn", "error"]
    text: str


class DataSetCard(ApiModel):
    split: str
    label: str
    hash: str
    rows: int | None
    cols: int | None
    expeds: int | None
    features: int | None
    targets: int | None
    target_available: bool
    duplicates: int | None
    missingness_pct: float | None
    memory_mb: float | None
    updated_at: str
    integrity_status: Literal["pass", "warn", "fail"]
    integrity_messages: list[DataSetIntegrityMessage]


class DataLabRowsPerExped(ApiModel):
    exped: str
    rows: int


class DataLabMissingness(ApiModel):
    feature: str
    pct: float


class DataLabCardinality(ApiModel):
    feature: str
    unique: int


class DataLabTargetBucket(ApiModel):
    bucket: str
    count: int


class DataLabSchemaDiff(ApiModel):
    field: str
    train_type: str
    val_type: str
    match: bool


class DataLabDrift(ApiModel):
    schema_drift: float | None
    missingness_drift: float | None
    cardinality_drift: float | None
    id_overlap_pct: float | None


class DataLabData(ApiModel):
    datasets: list[DataSetCard]
    rows_per_exped: list[DataLabRowsPerExped]
    missingness: list[DataLabMissingness]
    cardinality: list[DataLabCardinality]
    target_dist: list[DataLabTargetBucket]
    schema_diff: list[DataLabSchemaDiff]
    drift: DataLabDrift


# ─── Experiments / race ─────────────────────────────────────────


class RaceDecision(StrEnum):
    PROMOTE_TOP_SCORE = "PROMOTE_TOP_SCORE"
    PROMOTE_DIVERSITY = "PROMOTE_DIVERSITY"
    PROMOTE_EXPLORATION = "PROMOTE_EXPLORATION"
    KEEP_ENSEMBLE = "KEEP_ENSEMBLE"
    RETEST = "RETEST"
    RETIRE_DOMINATED = "RETIRE_DOMINATED"
    RETIRE_SATURATED = "RETIRE_SATURATED"
    FAILED_OOM = "FAILED_OOM"
    FAILED_TRAINING = "FAILED_TRAINING"
    INVALID_INTEGRITY = "INVALID_INTEGRITY"
    INVALID_ID_ALIGNMENT = "INVALID_ID_ALIGNMENT"
    PENDING = "PENDING"


class ExperimentRow(ProvenanceMeta):
    run: str
    family: str
    operator: str
    parent: str
    hypothesis: str
    race_stage: Literal["R0", "R1", "R2", "R3", "frontier"]
    local_score: float | None
    recent_score: float | None
    lower_quantile: float | None
    stability: float | None
    runtime_seconds: float
    diversity: float
    practice_score: float | None
    live_score: float | None
    status: Literal["active", "retired", "failed", "invalid"]
    race_decision: RaceDecision
    children: list[str]
    oof_path: str
    artefact: str
    logs: list[str]


# ─── Validation ─────────────────────────────────────────────────


class HardIntegrityCheck(ApiModel):
    check: str
    status: Literal["PASS", "FAIL", "UNKNOWN"]
    detail: str


class SoftResearchMetric(ApiModel):
    metric: str
    interpretation: Literal["STRONG", "MIXED", "WEAK", "INSUFFICIENT"]
    value: str
    detail: str
    term: str | None = None


class ValidationRaceDecision(ApiModel):
    decision: RaceDecision
    rationale: str
    stage: str


class ValidationFoldCell(ApiModel):
    fold: str
    round: str
    score: float


class ValidationScoreBucket(ApiModel):
    bucket: str
    count: int


class ValidationTimelinePoint(ApiModel):
    ts: str
    score: float


class ValidationData(ApiModel):
    hard_integrity: list[HardIntegrityCheck]
    soft_research: list[SoftResearchMetric]
    race_decision: ValidationRaceDecision
    fold_heatmap: list[ValidationFoldCell]
    score_dist: list[ValidationScoreBucket]
    timeline: list[ValidationTimelinePoint]
    updated_at: str


# ─── Models ─────────────────────────────────────────────────────


class ModelFoldPerformance(ApiModel):
    fold: str
    score: float


class ModelFeatureImportance(ApiModel):
    feature: str
    importance: float


class ModelRow(ProvenanceMeta):
    private_alias: str
    public_alias: str
    family: str
    params: str
    parent: str
    data_hash: str
    pickle_hash: str
    pickle_status: Literal["verified", "stale", "missing"]
    local_score: float | None
    recent_score: float | None
    icir: float | None
    worst_fold: float | None
    inference_p50_ms: float | None
    inference_p95_ms: float | None
    model_size_mb: float | None
    exposure: float | None
    corr_to_champion: float | None
    lifecycle: Literal["active", "frozen", "retired"]
    practice_score: float | None
    live_score: float | None
    fold_performance: list[ModelFoldPerformance]
    feature_importance: list[ModelFeatureImportance]


# ─── Feature lab ────────────────────────────────────────────────


class FeatureLabSummary(ApiModel):
    feature_count: int | None
    high_missingness: int | None
    unstable: int | None
    high_exposure: int | None
    selected_by_frontier: int | None


class FeatureLabFeature(ApiModel):
    id: str
    missingness: float
    cardinality: float
    importance: float
    importance_std: float
    redundancy: float
    exposure: float
    selection_freq: float
    drift: float


class FeatureImportancePoint(ApiModel):
    feature: str
    importance: float


class FeatureCorrelationCell(ApiModel):
    a: str
    b: str
    corr: float


class FeatureLabData(ApiModel):
    summary: FeatureLabSummary
    features: list[FeatureLabFeature]
    importance_series: list[FeatureImportancePoint]
    correlation_matrix: list[FeatureCorrelationCell]


# ─── Ensembles ──────────────────────────────────────────────────


class EnsembleStrategy(StrEnum):
    RANK_AVERAGE = "rank_average"
    WEIGHTED = "weighted"
    GREEDY = "greedy"
    DIVERSITY_AWARE = "diversity_aware"
    NEUTRALISED = "neutralised"


class EnsembleCandidate(ApiModel):
    model: str
    local_score: float | None
    diversity: float


class EnsembleMember(ApiModel):
    model: str
    weight: float
    local_score: float | None
    practice_score: float | None
    live_score: float | None


class EnsembleMetrics(ApiModel):
    local_uplift_vs_best: float | None
    recent_uplift: float | None
    worst_fold_change: float | None
    mean_pairwise_corr: float | None
    effective_models: float | None
    exposure_change: float | None
    practice_uplift: float | None
    live_uplift: float | None


class EnsemblePredCorr(ApiModel):
    a: str
    b: str
    corr: float


class EnsembleMarginalContrib(ApiModel):
    model: str
    contribution: float


class EnsembleScoreDiversity(ApiModel):
    model: str
    score: float
    diversity: float


class EnsembleFoldScore(ApiModel):
    fold: str
    model: str
    score: float


class EnsembleData(ApiModel):
    current_blend: str
    available_strategies: list[EnsembleStrategy]
    active_strategy: EnsembleStrategy
    candidate_pool: list[EnsembleCandidate]
    members: list[EnsembleMember]
    metrics: EnsembleMetrics
    pred_correlation: list[EnsemblePredCorr]
    marginal_contrib: list[EnsembleMarginalContrib]
    score_diversity_scatter: list[EnsembleScoreDiversity]
    fold_score: list[EnsembleFoldScore]


# ─── Leaderboard ────────────────────────────────────────────────


class OurAliasEntry(LeaderBoardEntry):
    local_vs_practice_gap: float | None
    practice_vs_live_gap: float | None


class LeaderboardHistoryPoint(ApiModel):
    round: str
    rank: int | None
    score: float | None


class LeaderboardRankPoint(ApiModel):
    round: str
    rank: int | None


class LeaderboardScorePoint(ApiModel):
    round: str
    score: float | None


class LeaderboardModelMatrixCell(ApiModel):
    model: str
    round: str
    score: float | None


class LeaderboardData(ApiModel):
    source: str
    current_round: list[LeaderBoardEntry]
    cumulative: list[LeaderBoardEntry]
    our_aliases: list[OurAliasEntry]
    history: list[LeaderboardHistoryPoint]
    rank_trajectory: list[LeaderboardRankPoint]
    score_trajectory: list[LeaderboardScorePoint]
    round_model_matrix: list[LeaderboardModelMatrixCell]


# ─── Submission ─────────────────────────────────────────────────


class StepStatus(StrEnum):
    NOT_STARTED = "NOT_STARTED"
    RUNNING = "RUNNING"
    PASS = "PASS"
    FAIL = "FAIL"
    BLOCKED = "BLOCKED"
    RETRYABLE = "RETRYABLE"


class SubmissionCandidate(ApiModel):
    id: str
    model: str
    lane: str
    split_fingerprint: str
    id_coverage: float | None
    duplicates: int | None
    bounds_ok: bool
    pickle_ok: bool
    pred_hash: str
    model_hash: str
    lineage: str
    lane_allowed: bool
    quota_allows: bool
    integrity_ok: bool
    blocking_reasons: list[str]


class SubmissionStepperStep(ApiModel):
    label: str
    status: StepStatus
    message: str | None = None
    started_at: str | None = None
    eta_seconds: int | None = None


class SubmissionData(ApiModel):
    quota_total: int | None
    quota_used: int | None
    quota_practice: int | None
    quota_live_reserve: int | None
    quota_emergency: int | None
    candidates: list[SubmissionCandidate]
    stepper_steps: list[SubmissionStepperStep]
    selected_candidate: str | None
    submission_mode: Literal["DISABLED", "DRY_RUN", "ARMED"] = "DRY_RUN"


# ─── Staking ────────────────────────────────────────────────────


class StakingClassification(StrEnum):
    VIRTUAL_EVENT_BALANCE = "VIRTUAL_EVENT_BALANCE"
    REAL_USDC = "REAL_USDC"
    NO_STAKING = "NO_STAKING"
    UNKNOWN = "UNKNOWN"


class StakingCandidate(ApiModel):
    model: str
    local_evidence: float | None
    live_evidence: float | None
    uncertainty: float | None
    correlation: float | None
    proposed_allocation_pct: float | None


class StakingData(ApiModel):
    classification: StakingClassification
    statement: str
    virtual_balance: float | None
    evidence: str
    uncertainty: str
    candidates: list[StakingCandidate]
    concentration: float | None
    risk_profile: str
    requires_confirmation: bool
    updated_at: str


# ─── Compute ────────────────────────────────────────────────────


class ComputeCpu(ApiModel):
    model: str | None
    cores: int | None
    used_pct: float | None


class ComputeRam(ApiModel):
    used_gb: float | None
    total_gb: float | None


class ComputeGpu(ApiModel):
    name: str | None
    vram_used_gb: float | None
    vram_total_gb: float | None
    cuda: str | None


class ComputeDisk(ApiModel):
    used_gb: float | None
    total_gb: float | None


class ComputeHardware(ApiModel):
    os: str | None
    cpu: ComputeCpu
    ram: ComputeRam
    gpu: ComputeGpu
    disk: ComputeDisk


class ComputeUtilisation(ApiModel):
    gpu_util_pct: float | None
    vram_util_pct: float | None
    ram_pressure_pct: float | None
    queue_length: int | None
    experiments_per_hour: float | None


class ComputeEventWatcher(ApiModel):
    active: bool
    last_ping: str
    interval: str


class ComputeRuntimePoint(ApiModel):
    ts: str
    duration_min: float
    type: str


class ComputeData(ApiModel):
    hardware: ComputeHardware
    utilisation: ComputeUtilisation
    local_queue: list[Job]
    server_queue: list[Job]
    event_watcher: ComputeEventWatcher
    runtime_history: list[ComputeRuntimePoint]
    updated_at: str


# ─── Repository ─────────────────────────────────────────────────


class RepoCheckResult(ApiModel):
    status: Literal["passing", "failing", "unknown"]
    at: str | None
    detail: str


class RepoCommit(ApiModel):
    sha: str
    msg: str
    author: str
    ts: str


class RepoData(ApiModel):
    serving_branch: str | None
    serving_sha: str | None
    dirty: bool
    python_version: str | None
    everest_api_pin: str | None
    lockfile_hash: str | None
    frontend_build_sha: str | None
    backend_build_sha: str | None
    last_tests: RepoCheckResult
    last_rehearsal: RepoCheckResult
    last_scorer_parity: RepoCheckResult
    env_health: Literal["healthy", "degraded", "unknown"]
    latest_commits: list[RepoCommit]
    updated_at: str


# ─── Documentation ──────────────────────────────────────────────


class DocIntroBlock(ApiModel):
    kind: Literal["intro"]
    text: str


class DocHeadingBlock(ApiModel):
    kind: Literal["heading"]
    text: str


class DocParagraphBlock(ApiModel):
    kind: Literal["paragraph"]
    text: str


class DocFlowNode(ApiModel):
    id: str
    label: str


class DocFlowBlock(ApiModel):
    kind: Literal["flow"]
    nodes: list[DocFlowNode]


class DocCalloutBlock(ApiModel):
    kind: Literal["callout"]
    tone: Literal["info", "warning", "danger"]
    text: str


class DocCommandBlock(ApiModel):
    kind: Literal["command"]
    command: str


class DocMetricBlock(ApiModel):
    kind: Literal["metric"]
    name: str
    text: str


class DocRelatedBlock(ApiModel):
    kind: Literal["related"]
    href: str
    label: str


DocBlock = Annotated[
    DocIntroBlock
    | DocHeadingBlock
    | DocParagraphBlock
    | DocFlowBlock
    | DocCalloutBlock
    | DocCommandBlock
    | DocMetricBlock
    | DocRelatedBlock,
    Field(discriminator="kind"),
]


class DocArticle(ApiModel):
    id: str
    title: str
    description: str
    section: str
    order: int
    source: Literal["generated", "curated"]
    blocks: list[DocBlock]


class DocSection(ApiModel):
    id: str
    label: str


class DocumentationData(ApiModel):
    generated_from_sha: str | None
    generated_at: str | None
    sections: list[DocSection]
    articles: list[DocArticle]
