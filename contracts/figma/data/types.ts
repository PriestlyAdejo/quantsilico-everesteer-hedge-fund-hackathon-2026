export type Provenance =
  | "OFFICIAL_EVENT_STATE"
  | "OFFICIAL_EVENT_DATA"
  | "OFFICIAL_PLATFORM_OBSERVATION"
  | "LOCAL_EXPERIMENT"
  | "SYNTHETIC_FIXTURE"
  | "MANUALLY_RECORDED";

export interface ProvenanceMeta {
  provenance: Provenance;
  generatedAt: string;
  sourceId?: string;
  eventSnapshotId?: string;
}

export interface DataEnvelope<T> {
  schemaVersion: number;
  kind: string;
  provenance: Provenance;
  generatedAt: string;
  stale: boolean;
  /** Human source line for the page header, e.g. "Everesteer API". */
  source: string;
  /** How this domain expects to refresh; drives cadence. */
  refreshMode?: "push" | "poll" | "manual";
  staleAfterSeconds?: number;
  sourceId?: string;
  eventSnapshotId?: string;
  data: T;
}

export interface ActionResult {
  ok: boolean;
  message: string;
  code?: string;
  timestamp: string;
}

// ─── Global live event status (top bar) ───────────────────────

export type ConnectionState = "LIVE" | "RECONNECTING" | "DISCONNECTED" | "NOT_CONNECTED";

export interface EventStatus {
  connection: ConnectionState;
  lastUpdateAt: string | null;
  eventId: string | null;
  eventPhase: string | null;
  round: { index: number | null; total: number | null; label: string | null };
  uploads: { used: number | null; total: number | null };
  champion: string | null;
  externalRank: number | null;
  autopilot: boolean;
  scope: string | null;
}

// ─── Shared job model with timing ─────────────────────────────

export type JobStatus = "RUNNING" | "QUEUED" | "PENDING" | "DONE" | "FAILED";

export interface Job {
  id: string;
  name: string;
  type: string; // TRAIN / INFER / VALIDATE / DATA_PULL / ENSEMBLE / SCORER_PARITY / SUBMIT / DOCS
  candidate?: string | null;
  status: JobStatus;
  startedAt: string | null;
  etaSeconds: number | null;
  totalSeconds: number | null;
  progress: number | null; // 0..1
  queuePosition: number | null;
  device: string; // "CPU" / "GPU" / "SERVER"
}

// ─── Domain types ─────────────────────────────────────────────

export interface MetricCardData extends ProvenanceMeta {
  label: string;
  value: string | number | null;
  unit?: string;
  delta?: string;
  trend?: "up" | "down" | "flat";
  warn?: boolean;
  critical?: boolean;
  /** glossary term key for a hover definition */
  term?: string;
}

export type FlowState = "waiting" | "ready" | "active" | "complete" | "attention" | "blocked";

export interface FlowNode {
  id: string;
  label: string;
  state: FlowState;
}

export interface OverviewData {
  metrics: MetricCardData[];
  researchMetrics: MetricCardData[];
  /** Backend-supplied operating flow; the frontend never guesses order. */
  flow: FlowNode[];
  currentStage: string; // id of the active flow node
  recommendation: {
    text: string;
    actions: { label: string; to: string }[];
  };
  scoreHistory: { round: string; score: number | null; rank: number | null }[];
  experiments: { runtimeSeconds: number; score: number; diversity: number; family: string; stage: string; name: string }[];
  foldEvidence: { fold: string; r0: number; r1: number; r2: number; r3: number }[];
  /** Upload budget breakdown — this is quota, not scoring weight. */
  uploadQuota: { label: string; value: number; fill: string }[];
  latestDecisions: { ts: string; text: string; level: "info" | "warn" | "error" }[];
}

export interface ScoringComponent {
  name: string; // CORR20 / AIMC / NCORR / …
  weight: number | null;
  value: number | null;
  provided: boolean; // false => "NOT PROVIDED BY EVENT"
}

export type CapabilityStatus = "available" | "unavailable" | "unknown";

export interface EventControlData {
  connection: {
    apiStatus: ConnectionState;
    sdkVersion: string; // everestapi pin
    scope: string;
    keyFingerprint: string;
    lastRequestAt: string | null;
  };
  eventState: {
    eventId: string | null;
    tournament: string | null;
    phase: string | null;
    currentRound: string | null;
    roundOpenedAt: string | null;
    timeRemaining: string | null;
  };
  scoring: {
    rankMetric: string | null;
    primaryTarget: string | null;
    components: ScoringComponent[];
    snapshotAt: string | null;
  };
  capabilities: { name: string; status: CapabilityStatus }[];
  autopilotActive: boolean;
  latestSnapshot: string | null;
  updatedAt: string;
  stale: boolean;
}

export interface RoundRoomData {
  roundId: string | null;
  roundStatus: "open" | "closed" | "scoring" | "unknown";
  countdown: string | null;
  splitFingerprint: string | null;
  liveRows: number | null;
  submissionsUsedRound: number | null;
  submissionsUsedEvent: number | null;
  submissionsTotalEvent: number | null;
  liveFeed: ConnectionState;
  inferenceQueue: Job[];
  submissionQueue: Job[];
  currentBoard: LeaderBoardEntry[];
  eventLog: { ts: string; msg: string; level: "info" | "warn" | "error" }[];
  emergency: {
    champion: string | null;
    ensemble: string | null;
    modelHash: string | null;
    splitVerified: boolean;
    submissionReady: boolean;
  };
  rankByRound: { round: string; rank: number | null }[];
  heatmapData: { model: string; round: string; score: number }[];
  updatedAt: string;
  stale: boolean;
}

export interface DataSetCard {
  split: string; // real event naming
  label: string; // human name e.g. "Train"
  hash: string;
  rows: number | null;
  cols: number | null;
  expeds: number | null;
  features: number | null;
  targets: number | null;
  targetAvailable: boolean;
  duplicates: number | null;
  missingnessPct: number | null;
  memoryMb: number | null;
  updatedAt: string;
  integrityStatus: "pass" | "warn" | "fail";
  integrityMessages: { level: "warn" | "error"; text: string }[];
}

export interface DataLabData {
  datasets: DataSetCard[];
  rowsPerExped: { exped: string; rows: number }[];
  missingness: { feature: string; pct: number }[];
  cardinality: { feature: string; unique: number }[];
  targetDist: { bucket: string; count: number }[];
  schemaDiff: { field: string; trainType: string; valType: string; match: boolean }[];
  drift: {
    schemaDrift: number | null;
    missingnessDrift: number | null;
    cardinalityDrift: number | null;
    idOverlapPct: number | null;
  };
}

export type RaceDecision =
  | "PROMOTE_TOP_SCORE"
  | "PROMOTE_DIVERSITY"
  | "PROMOTE_EXPLORATION"
  | "KEEP_ENSEMBLE"
  | "RETEST"
  | "RETIRE_DOMINATED"
  | "RETIRE_SATURATED"
  | "FAILED_OOM"
  | "FAILED_TRAINING"
  | "INVALID_INTEGRITY"
  | "INVALID_ID_ALIGNMENT"
  | "PENDING";

export interface ExperimentRow extends ProvenanceMeta {
  run: string;
  family: string;
  operator: string;
  parent: string;
  hypothesis: string;
  raceStage: "R0" | "R1" | "R2" | "R3" | "frontier";
  localScore: number | null;
  recentScore: number | null;
  lowerQuantile: number | null;
  stability: number | null;
  runtimeSeconds: number;
  diversity: number;
  practiceScore: number | null;
  liveScore: number | null;
  status: "active" | "retired" | "failed" | "invalid";
  raceDecision: RaceDecision;
  children: string[];
  oofPath: string;
  artefact: string;
  logs: string[];
}

export interface ValidationData {
  hardIntegrity: {
    check: string;
    status: "PASS" | "FAIL" | "UNKNOWN";
    detail: string;
  }[];
  softResearch: {
    metric: string;
    term?: string;
    interpretation: "STRONG" | "MIXED" | "WEAK" | "INSUFFICIENT";
    value: string;
    detail: string;
  }[];
  raceDecision: {
    decision: RaceDecision;
    rationale: string;
    stage: string;
  };
  foldHeatmap: { fold: string; round: string; score: number }[];
  scoreDist: { bucket: string; count: number }[];
  timeline: { ts: string; score: number }[];
  updatedAt: string;
}

export interface ModelRow extends ProvenanceMeta {
  privateAlias: string;
  publicAlias: string;
  family: string;
  params: string;
  parent: string;
  dataHash: string;
  pickleHash: string;
  pickleStatus: "verified" | "stale" | "missing";
  localScore: number | null;
  recentScore: number | null;
  icir: number | null;
  worstFold: number | null;
  inferenceP50Ms: number | null;
  inferenceP95Ms: number | null;
  modelSizeMb: number | null;
  exposure: number | null;
  corrToChampion: number | null;
  lifecycle: "active" | "frozen" | "retired";
  practiceScore: number | null;
  liveScore: number | null;
  foldPerformance: { fold: string; score: number }[];
  featureImportance: { feature: string; importance: number }[];
}

export interface FeatureLabData {
  summary: {
    featureCount: number | null;
    highMissingness: number | null;
    unstable: number | null;
    highExposure: number | null;
    selectedByFrontier: number | null;
  };
  features: {
    id: string;
    missingness: number;
    cardinality: number;
    importance: number;
    importanceStd: number;
    redundancy: number;
    exposure: number;
    selectionFreq: number;
    drift: number;
  }[];
  importanceSeries: { feature: string; importance: number }[];
  correlationMatrix: { a: string; b: string; corr: number }[];
}

export type EnsembleStrategy = "rank_average" | "weighted" | "greedy" | "diversity_aware" | "neutralised";

export interface EnsembleData {
  currentBlend: string;
  availableStrategies: EnsembleStrategy[];
  activeStrategy: EnsembleStrategy;
  candidatePool: { model: string; localScore: number | null; diversity: number }[];
  members: { model: string; weight: number; localScore: number | null; practiceScore: number | null; liveScore: number | null }[];
  metrics: {
    localUpliftVsBest: number | null;
    recentUplift: number | null;
    worstFoldChange: number | null;
    meanPairwiseCorr: number | null;
    effectiveModels: number | null;
    exposureChange: number | null;
    practiceUplift: number | null;
    liveUplift: number | null;
  };
  predCorrelation: { a: string; b: string; corr: number }[];
  marginalContrib: { model: string; contribution: number }[];
  scoreDiversityScatter: { model: string; score: number; diversity: number }[];
  foldScore: { fold: string; model: string; score: number }[];
}

export interface LeaderBoardEntry extends ProvenanceMeta {
  rank: number | null;
  alias: string;
  score: number | null;
  scoreChange: number | null;
  rankChange: number | null;
  round: string;
  isOurs: boolean;
}

export interface LeaderboardData {
  source: string;
  currentRound: LeaderBoardEntry[];
  cumulative: LeaderBoardEntry[];
  ourAliases: (LeaderBoardEntry & {
    localVsPracticeGap: number | null;
    practiceVsLiveGap: number | null;
  })[];
  history: { round: string; rank: number | null; score: number | null }[];
  rankTrajectory: { round: string; rank: number | null }[];
  scoreTrajectory: { round: string; score: number | null }[];
  roundModelMatrix: { model: string; round: string; score: number | null }[];
}

export type StepStatus = "NOT_STARTED" | "RUNNING" | "PASS" | "FAIL" | "BLOCKED" | "RETRYABLE";

export interface SubmissionData {
  quotaTotal: number | null;
  quotaUsed: number | null;
  quotaPractice: number | null;
  quotaLiveReserve: number | null;
  quotaEmergency: number | null;
  candidates: {
    id: string;
    model: string;
    lane: string;
    splitFingerprint: string;
    idCoverage: number | null;
    duplicates: number | null;
    boundsOk: boolean;
    pickleOk: boolean;
    predHash: string;
    modelHash: string;
    lineage: string;
    /** capability + integrity gating, with human blocking reasons */
    laneAllowed: boolean;
    quotaAllows: boolean;
    integrityOk: boolean;
    blockingReasons: string[];
  }[];
  /** stages reflect real backend job state, not manual advance */
  stepperSteps: { label: string; status: StepStatus; message?: string; startedAt?: string | null; etaSeconds?: number | null }[];
  selectedCandidate: string | null;
}

export interface StakingData {
  classification: "VIRTUAL_EVENT_BALANCE" | "REAL_USDC" | "NO_STAKING" | "UNKNOWN";
  /** Plain-language banner text driven by classification. */
  statement: string;
  virtualBalance: number | null;
  evidence: string;
  uncertainty: string;
  candidates: {
    model: string;
    localEvidence: number | null;
    liveEvidence: number | null;
    uncertainty: number | null;
    correlation: number | null;
    proposedAllocationPct: number | null;
  }[];
  concentration: number | null;
  riskProfile: string;
  requiresConfirmation: boolean;
  updatedAt: string;
}

export interface ComputeData {
  hardware: {
    os: string | null;
    cpu: { model: string | null; cores: number | null; usedPct: number | null };
    ram: { usedGb: number | null; totalGb: number | null };
    gpu: { name: string | null; vramUsedGb: number | null; vramTotalGb: number | null; cuda: string | null };
    disk: { usedGb: number | null; totalGb: number | null };
  };
  utilisation: {
    gpuUtilPct: number | null;
    vramUtilPct: number | null;
    ramPressurePct: number | null;
    queueLength: number | null;
    experimentsPerHour: number | null;
  };
  localQueue: Job[];
  serverQueue: Job[];
  eventWatcher: { active: boolean; lastPing: string; interval: string };
  runtimeHistory: { ts: string; durationMin: number; type: string }[];
  updatedAt: string;
}

export interface RepoData {
  servingBranch: string | null;
  servingSha: string | null;
  dirty: boolean;
  pythonVersion: string | null;
  everestApiPin: string | null;
  lockfileHash: string | null;
  frontendBuildSha: string | null;
  backendBuildSha: string | null;
  lastTests: { status: "passing" | "failing" | "unknown"; at: string | null; detail: string };
  lastRehearsal: { status: "passing" | "failing" | "unknown"; at: string | null; detail: string };
  lastScorerParity: { status: "passing" | "failing" | "unknown"; at: string | null; detail: string };
  envHealth: "healthy" | "degraded" | "unknown";
  latestCommits: { sha: string; msg: string; author: string; ts: string }[];
  updatedAt: string;
}

// ─── Documentation contract ───────────────────────────────────
// Curated MDX-style flow blocks plus generated-reference metadata.

export type DocBlock =
  | { kind: "intro"; text: string }
  | { kind: "heading"; text: string }
  | { kind: "paragraph"; text: string }
  | { kind: "flow"; nodes: { id: string; label: string }[] }
  | { kind: "callout"; tone: "info" | "warning" | "danger"; text: string }
  | { kind: "command"; command: string }
  | { kind: "metric"; name: string; text: string }
  | { kind: "related"; href: string; label: string };

export interface DocArticle {
  id: string;
  title: string;
  description: string;
  section: string; // nav group id
  order: number;
  source: "generated" | "curated";
  blocks: DocBlock[];
}

export interface DocSection {
  id: string;
  label: string;
}

export interface DocumentationData {
  generatedFromSha: string | null;
  generatedAt: string | null;
  sections: DocSection[];
  articles: DocArticle[];
}

export interface DataSource {
  getEventStatus(): Promise<DataEnvelope<EventStatus>>;
  getOverview(): Promise<DataEnvelope<OverviewData>>;
  getEventControl(): Promise<DataEnvelope<EventControlData>>;
  getRoundRoom(): Promise<DataEnvelope<RoundRoomData>>;
  getDataLab(): Promise<DataEnvelope<DataLabData>>;
  getExperiments(): Promise<DataEnvelope<ExperimentRow[]>>;
  getValidation(): Promise<DataEnvelope<ValidationData>>;
  getModels(): Promise<DataEnvelope<ModelRow[]>>;
  getFeatureLab(): Promise<DataEnvelope<FeatureLabData>>;
  getEnsembles(): Promise<DataEnvelope<EnsembleData>>;
  getLeaderboard(): Promise<DataEnvelope<LeaderboardData>>;
  getSubmission(): Promise<DataEnvelope<SubmissionData>>;
  getStaking(): Promise<DataEnvelope<StakingData>>;
  getComputeJobs(): Promise<DataEnvelope<ComputeData>>;
  getRepository(): Promise<DataEnvelope<RepoData>>;
  getDocumentation(): Promise<DataEnvelope<DocumentationData>>;

  refreshEvent(): Promise<ActionResult>;
  snapshotEvent(): Promise<ActionResult>;
  pullDatasets(): Promise<ActionResult>;
  runScorerParity(): Promise<ActionResult>;
  runOfficialBaseline(): Promise<ActionResult>;
  startAutopilot(): Promise<ActionResult>;
  stopAutopilot(): Promise<ActionResult>;
  startRace(profile: string): Promise<ActionResult>;
  buildEnsemble(strategy: string): Promise<ActionResult>;
  saveEnsembleCandidate(strategy: string): Promise<ActionResult>;
  promoteEnsemble(): Promise<ActionResult>;
  validateSubmission(candidateId: string): Promise<ActionResult>;
  submitPractice(candidateId: string): Promise<ActionResult>;
  submitLive(candidateId: string): Promise<ActionResult>;
  stopJob(jobId: string): Promise<ActionResult>;
}
