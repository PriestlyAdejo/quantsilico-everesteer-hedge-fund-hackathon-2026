import type {
  DataSource, DataEnvelope, ActionResult, Provenance,
  EventStatus, Job, OverviewData, EventControlData, RoundRoomData, DataLabData,
  ExperimentRow, ValidationData, ModelRow, FeatureLabData,
  EnsembleData, LeaderboardData, SubmissionData, StakingData,
  ComputeData, RepoData, DocumentationData,
} from "./types";

const SYN: Provenance = "SYNTHETIC_FIXTURE";
const NOW = () => new Date().toISOString();
const AGO = (secs: number) => new Date(Date.now() - secs * 1000).toISOString();
const SOURCE = "Local research store (preview)";

function env<T>(kind: string, data: T, source = SOURCE): DataEnvelope<T> {
  return {
    schemaVersion: 2,
    kind,
    provenance: SYN,
    generatedAt: NOW(),
    stale: false,
    source,
    refreshMode: "poll",
    data,
  };
}

function ok(msg: string): ActionResult {
  return { ok: true, message: msg, code: "OK", timestamp: NOW() };
}

const MODELS = ["organiser-lgbm", "ridge-01", "extra-trees-01", "blend-01"];
const ROUNDS = ["R1", "R2", "R3", "R4", "R5"];

function job(partial: Partial<Job> & Pick<Job, "id" | "name" | "type" | "status">): Job {
  return {
    candidate: null,
    startedAt: partial.status === "RUNNING" ? AGO(192) : null,
    etaSeconds: null,
    totalSeconds: null,
    progress: null,
    queuePosition: null,
    device: "CPU",
    ...partial,
  };
}

export class DemoDataSource implements DataSource {
  async getEventStatus(): Promise<DataEnvelope<EventStatus>> {
    return env<EventStatus>("event_status", {
      connection: "LIVE",
      lastUpdateAt: AGO(4),
      eventId: "EVERESTEER-2026-HF-HACK",
      eventPhase: "QUALIFYING",
      round: { index: 3, total: 8, label: "R3" },
      uploads: { used: 12, total: 20 },
      champion: "blend-01",
      externalRank: 2,
      autopilot: false,
      scope: "research:read+submit",
    });
  }

  async getOverview(): Promise<DataEnvelope<OverviewData>> {
    return env("overview", {
      metrics: [
        { label: "Event phase", value: "Qualifying", provenance: "OFFICIAL_EVENT_STATE", generatedAt: NOW() },
        { label: "Round", value: "R3 / 8", provenance: "OFFICIAL_EVENT_STATE", generatedAt: NOW() },
        { label: "Upload budget", value: "12 / 20", provenance: "OFFICIAL_EVENT_STATE", generatedAt: NOW() },
        { label: "Champion", value: "blend-01", provenance: SYN, generatedAt: NOW() },
        { label: "External rank", value: 2, provenance: "OFFICIAL_PLATFORM_OBSERVATION", generatedAt: NOW() },
        { label: "Local best", value: "0.7234", provenance: "LOCAL_EXPERIMENT", generatedAt: NOW() },
        { label: "Practice score", value: "0.7198", provenance: "OFFICIAL_PLATFORM_OBSERVATION", generatedAt: NOW() },
        { label: "Live score", value: null, provenance: "OFFICIAL_PLATFORM_OBSERVATION", generatedAt: NOW() },
        { label: "Active jobs", value: 3, provenance: "LOCAL_EXPERIMENT", generatedAt: NOW() },
      ],
      researchMetrics: [
        { label: "CORR20", value: "0.0421", term: "CORR20", provenance: "LOCAL_EXPERIMENT", generatedAt: NOW() },
        { label: "ICIR", value: "1.34", term: "ICIR", provenance: "LOCAL_EXPERIMENT", generatedAt: NOW() },
        { label: "Positive expeds", value: "68%", provenance: "LOCAL_EXPERIMENT", generatedAt: NOW() },
        { label: "Recent vs history", value: "-0.4%", trend: "down", provenance: "LOCAL_EXPERIMENT", generatedAt: NOW() },
        { label: "Worst fold", value: "0.6810", term: "worst fold", provenance: "LOCAL_EXPERIMENT", generatedAt: NOW() },
        { label: "Local→external gap", value: "-0.0036", provenance: "LOCAL_EXPERIMENT", generatedAt: NOW() },
      ],
      flow: [
        { id: "connect", label: "Connect event", state: "complete" },
        { id: "data", label: "Data ready", state: "complete" },
        { id: "baseline", label: "Baseline proven", state: "active" },
        { id: "research", label: "Research", state: "ready" },
        { id: "validate", label: "Validate", state: "waiting" },
        { id: "ensemble", label: "Ensemble", state: "waiting" },
        { id: "submit", label: "Submit", state: "waiting" },
        { id: "live", label: "Live round", state: "waiting" },
        { id: "stake", label: "Stake / finalise", state: "waiting" },
      ],
      currentStage: "baseline",
      recommendation: {
        text: "Train data is verified. Reproduce the organiser baseline before starting the research race so every later result has a reference point.",
        actions: [
          { label: "Run baseline", to: "/event" },
          { label: "Open Data Lab", to: "/data" },
        ],
      },
      scoreHistory: ROUNDS.map((r, i) => ({ round: r, score: 0.68 + i * 0.011 + Math.random() * 0.005, rank: 8 - i })),
      experiments: Array.from({ length: 24 }, (_, i) => ({
        runtimeSeconds: 10 + Math.random() * 280,
        score: 0.65 + Math.random() * 0.08,
        diversity: Math.random(),
        family: ["lgbm", "ridge", "extra-trees", "blend"][i % 4],
        stage: ["R0", "R1", "R2", "R3", "frontier"][i % 5],
        name: `run-${String(i + 1).padStart(3, "0")}`,
      })),
      foldEvidence: ["F0", "F1", "F2", "F3", "F4"].map((f) => ({
        fold: f,
        r0: 0.64 + Math.random() * 0.04,
        r1: 0.67 + Math.random() * 0.04,
        r2: 0.70 + Math.random() * 0.03,
        r3: 0.72 + Math.random() * 0.03,
      })),
      uploadQuota: [
        { label: "Used", value: 12, fill: "#38BDF8" },
        { label: "Practice allocation", value: 3, fill: "#3B82F6" },
        { label: "Live reserve", value: 3, fill: "#A78BFA" },
        { label: "Emergency reserve", value: 1, fill: "#4B5563" },
        { label: "Remaining", value: 1, fill: "#22C55E" },
      ],
      latestDecisions: [
        { ts: AGO(120), text: "blend-01 advanced to R3 — best local score so far", level: "info" },
        { ts: AGO(360), text: "extra-trees-01 retest — evidence not yet conclusive on fold F2", level: "warn" },
        { ts: AGO(900), text: "ridge-v7 stopped — another candidate is better on the same trade-offs", level: "info" },
      ],
    });
  }

  async getEventControl(): Promise<DataEnvelope<EventControlData>> {
    return env("event_control", {
      connection: {
        apiStatus: "LIVE",
        sdkVersion: "everestapi 0.3.22",
        scope: "research:read+submit",
        keyFingerprint: "ek_live_••••_••••_1A2B",
        lastRequestAt: AGO(4),
      },
      eventState: {
        eventId: "EVERESTEER-2026-HF-HACK",
        tournament: "Everesteer Hedge Fund Hackathon 2026",
        phase: "Qualifying",
        currentRound: "R3",
        roundOpenedAt: AGO(3200),
        timeRemaining: "02:14:33",
      },
      scoring: {
        rankMetric: "CORR20",
        primaryTarget: "target_20d",
        components: [
          { name: "CORR20", weight: 0.6, value: 0.0421, provided: true },
          { name: "AIMC", weight: 0.25, value: 0.0188, provided: true },
          { name: "NCORR", weight: 0.15, value: null, provided: false },
        ],
        snapshotAt: AGO(60),
      },
      capabilities: [
        { name: "Practice submissions", status: "available" },
        { name: "Live submissions", status: "available" },
        { name: "Leaderboard", status: "available" },
        { name: "Cumulative standings", status: "available" },
        { name: "Server compute", status: "unavailable" },
        { name: "Event staking", status: "unavailable" },
      ],
      autopilotActive: false,
      latestSnapshot: "snap-2026-08-12T09:41:00Z",
      updatedAt: NOW(),
      stale: false,
    });
  }

  async getRoundRoom(): Promise<DataEnvelope<RoundRoomData>> {
    return env("round_room", {
      roundId: "R3-2026-08-12",
      roundStatus: "open",
      countdown: "02:14:33",
      splitFingerprint: "fp-a3b9c1",
      liveRows: 4820,
      submissionsUsedRound: 1,
      submissionsUsedEvent: 12,
      submissionsTotalEvent: 20,
      liveFeed: "LIVE",
      inferenceQueue: [
        job({ id: "infer-0", name: "blend-01", type: "INFER", candidate: "blend-01", status: "RUNNING", startedAt: AGO(192), etaSeconds: 120, totalSeconds: 312, progress: 0.62, device: "GPU" }),
        job({ id: "infer-1", name: "ridge-01", type: "INFER", candidate: "ridge-01", status: "QUEUED", queuePosition: 1, etaSeconds: 130 }),
        job({ id: "infer-2", name: "extra-trees-01", type: "INFER", candidate: "extra-trees-01", status: "QUEUED", queuePosition: 2, etaSeconds: 260 }),
      ],
      submissionQueue: [
        job({ id: "sub-0", name: "blend-01 → live", type: "SUBMIT", candidate: "blend-01", status: "DONE", startedAt: AGO(600), totalSeconds: 22 }),
      ],
      currentBoard: [
        { rank: 1, alias: "anon-alpha", score: 0.7401, scoreChange: 0.003, rankChange: 0, round: "R3", isOurs: false, provenance: "OFFICIAL_PLATFORM_OBSERVATION", generatedAt: NOW() },
        { rank: 2, alias: "blend-01", score: 0.7390, scoreChange: 0.011, rankChange: 1, round: "R3", isOurs: true, provenance: "OFFICIAL_PLATFORM_OBSERVATION", generatedAt: NOW() },
        { rank: 3, alias: "anon-beta", score: 0.7310, scoreChange: -0.002, rankChange: -1, round: "R3", isOurs: false, provenance: "OFFICIAL_PLATFORM_OBSERVATION", generatedAt: NOW() },
      ],
      eventLog: [
        { ts: AGO(3200), msg: "Round R3 opened — live split loaded", level: "info" },
        { ts: AGO(600), msg: "blend-01 submitted to live lane", level: "info" },
        { ts: AGO(200), msg: "split fingerprint verified against live data", level: "info" },
      ],
      emergency: {
        champion: "blend-01",
        ensemble: "blend-01 (rank-avg of 4)",
        modelHash: "sha256:9f3a…c17d",
        splitVerified: true,
        submissionReady: true,
      },
      rankByRound: ROUNDS.map((r, i) => ({ round: r, rank: 8 - i })),
      heatmapData: MODELS.flatMap((m, mi) =>
        ROUNDS.map((r, ri) => ({
          model: m,
          round: r,
          score: 0.65 + mi * 0.01 + ri * 0.008 + Math.random() * 0.01,
        }))
      ),
      updatedAt: NOW(),
      stale: false,
    });
  }

  async getDataLab(): Promise<DataEnvelope<DataLabData>> {
    return env("data_lab", {
      datasets: [
        {
          split: "train", label: "Train", hash: "sha256:abc123", rows: 480000, cols: 312, expeds: 240,
          features: 308, targets: 1, targetAvailable: true, duplicates: 0, missingnessPct: 1.2, memoryMb: 1420,
          updatedAt: NOW(), integrityStatus: "pass", integrityMessages: [],
        },
        {
          split: "practice", label: "Practice / Validation", hash: "sha256:def456", rows: 120000, cols: 312, expeds: 60,
          features: 308, targets: 1, targetAvailable: true, duplicates: 0, missingnessPct: 2.8, memoryMb: 360,
          updatedAt: NOW(), integrityStatus: "warn",
          integrityMessages: [{ level: "warn", text: "3 features have >5% missingness vs train" }],
        },
        {
          split: "live", label: "Live", hash: "sha256:ghi789", rows: 4820, cols: 311, expeds: null,
          features: 308, targets: 0, targetAvailable: false, duplicates: 0, missingnessPct: 0.4, memoryMb: 14,
          updatedAt: NOW(), integrityStatus: "pass", integrityMessages: [],
        },
      ],
      rowsPerExped: Array.from({ length: 12 }, (_, i) => ({
        exped: `E${String(i + 1).padStart(3, "0")}`,
        rows: 1800 + Math.floor(Math.random() * 400),
      })),
      missingness: Array.from({ length: 15 }, (_, i) => ({ feature: `f_anon_${String(i + 1).padStart(3, "0")}`, pct: Math.random() * 8 })),
      cardinality: Array.from({ length: 12 }, (_, i) => ({ feature: `f_anon_${String(i + 1).padStart(3, "0")}`, unique: Math.floor(10 + Math.random() * 5000) })),
      targetDist: Array.from({ length: 10 }, (_, i) => ({ bucket: `${(i * 0.1).toFixed(1)}–${((i + 1) * 0.1).toFixed(1)}`, count: Math.floor(40000 + Math.random() * 10000) })),
      schemaDiff: [
        { field: "f_anon_001", trainType: "float32", valType: "float32", match: true },
        { field: "f_anon_042", trainType: "float32", valType: "float64", match: false },
        { field: "f_anon_100", trainType: "int32", valType: "int32", match: true },
      ],
      drift: { schemaDrift: 1, missingnessDrift: 0.031, cardinalityDrift: 0.008, idOverlapPct: 0 },
    });
  }

  async getExperiments(): Promise<DataEnvelope<ExperimentRow[]>> {
    const families = ["lgbm", "ridge", "extra-trees", "blend"];
    const operators = ["tune", "prune", "ensemble", "explore", "baseline"];
    const decisions = [
      "PROMOTE_TOP_SCORE", "PROMOTE_DIVERSITY", "PROMOTE_EXPLORATION",
      "KEEP_ENSEMBLE", "RETEST", "RETIRE_DOMINATED", "RETIRE_SATURATED",
      "FAILED_OOM", "INVALID_INTEGRITY", "PENDING",
    ] as const;
    const stages = ["R0", "R1", "R2", "R3", "frontier"] as const;

    const rows: ExperimentRow[] = Array.from({ length: 40 }, (_, i) => ({
      run: `run-${String(i + 1).padStart(3, "0")}`,
      family: families[i % 4],
      operator: operators[i % 5],
      parent: i < 4 ? "—" : `run-${String(Math.floor(i / 2)).padStart(3, "0")}`,
      hypothesis: `Vary ${operators[i % 5]} on ${families[i % 4]} to lift CORR20 without raising exposure.`,
      raceStage: stages[i % 5],
      localScore: 0.64 + Math.random() * 0.09,
      recentScore: 0.63 + Math.random() * 0.09,
      lowerQuantile: 0.60 + Math.random() * 0.08,
      stability: Math.round((0.5 + Math.random() * 0.5) * 100) / 100,
      runtimeSeconds: Math.round(10 + Math.random() * 280),
      diversity: Math.round(Math.random() * 100) / 100,
      practiceScore: i < 8 ? 0.70 + Math.random() * 0.04 : null,
      liveScore: i < 3 ? 0.72 + Math.random() * 0.03 : null,
      status: i > 35 ? "failed" : i > 30 ? "retired" : "active",
      raceDecision: decisions[i % decisions.length],
      children: i < 4 ? [`run-${String(i * 2 + 5).padStart(3, "0")}`] : [],
      oofPath: `oof/run-${String(i + 1).padStart(3, "0")}.parquet`,
      artefact: `artefacts/run-${String(i + 1).padStart(3, "0")}.pkl`,
      logs: ["train start", "fold 0..4 complete", "oof written", "scored"],
      provenance: SYN,
      generatedAt: NOW(),
    }));
    return env("experiments", rows);
  }

  async getValidation(): Promise<DataEnvelope<ValidationData>> {
    return env("validation", {
      hardIntegrity: [
        { check: "Schema", status: "PASS", detail: "All 308 features present and typed correctly" },
        { check: "Leakage", status: "PASS", detail: "No target leakage detected" },
        { check: "ID alignment", status: "PASS", detail: "100% ID coverage against live split" },
        { check: "Submission lane", status: "PASS", detail: "Submission lane matches current round" },
        { check: "Scorer parity", status: "PASS", detail: "Local scorer matches official within 0.0001" },
        { check: "Model artefact", status: "PASS", detail: "Pickle loads cleanly, hash verified" },
      ],
      softResearch: [
        { metric: "Rank metric (CORR20)", term: "CORR20", interpretation: "STRONG", value: "0.0421", detail: "Above baseline by 0.0032" },
        { metric: "Mean IC", term: "IC", interpretation: "STRONG", value: "0.038", detail: "Consistent positive signal" },
        { metric: "ICIR", term: "ICIR", interpretation: "STRONG", value: "1.34", detail: "Stable across expeditions" },
        { metric: "Positive exped %", term: "exped", interpretation: "MIXED", value: "68%", detail: "Slight drift in last 3 expeditions" },
        { metric: "Recent-window IC", interpretation: "MIXED", value: "0.031", detail: "Below full-history mean" },
        { metric: "Worst fold", term: "worst fold", interpretation: "WEAK", value: "0.681", detail: "Fold F2 lags the others" },
        { metric: "Prediction diversity", term: "diversity", interpretation: "STRONG", value: "0.74", detail: "Low correlation with champion" },
        { metric: "Trial count", interpretation: "INSUFFICIENT", value: "n=6", detail: "Recommend ≥10 trials before promotion" },
      ],
      raceDecision: {
        decision: "PROMOTE_DIVERSITY",
        rationale: "Integrity is clear. Research evidence is mixed but diversity value is strong, so the candidate advances as a diversity slot.",
        stage: "R1 → R2",
      },
      foldHeatmap: ["F0", "F1", "F2", "F3", "F4"].flatMap((f) =>
        ["R0", "R1", "R2", "R3"].map((r) => ({ fold: f, round: r, score: 0.68 + Math.random() * 0.06 }))
      ),
      scoreDist: Array.from({ length: 10 }, (_, i) => ({ bucket: `${(0.60 + i * 0.02).toFixed(2)}`, count: Math.floor(5 + Math.random() * 25) })),
      timeline: Array.from({ length: 20 }, (_, i) => ({ ts: AGO((20 - i) * 60), score: 0.68 + i * 0.002 + (Math.random() - 0.5) * 0.01 })),
      updatedAt: NOW(),
    });
  }

  async getModels(): Promise<DataEnvelope<ModelRow[]>> {
    const rows: ModelRow[] = MODELS.map((m, i) => ({
      privateAlias: m,
      publicAlias: `alias-${String(i + 1).padStart(4, "0")}`,
      family: ["lgbm", "ridge", "extra-trees", "blend"][i],
      params: ["n_est=800,lr=0.05", "alpha=0.1", "n_est=500", "w=[0.4,0.3,0.2,0.1]"][i],
      parent: i === 0 ? "—" : MODELS[i - 1],
      dataHash: `sha256:${i}abc123`,
      pickleHash: `sha256:p${i}def456`,
      pickleStatus: i === 2 ? "stale" : "verified",
      localScore: 0.70 + i * 0.006 + Math.random() * 0.003,
      recentScore: 0.69 + i * 0.006 + Math.random() * 0.003,
      icir: 1.1 + i * 0.1,
      worstFold: 0.66 + i * 0.006,
      inferenceP50Ms: 800 + i * 300,
      inferenceP95Ms: 1400 + i * 380,
      modelSizeMb: 12 + i * 30,
      exposure: Math.round((0.6 + Math.random() * 0.3) * 100) / 100,
      corrToChampion: i === 3 ? 1 : Math.round((0.4 + Math.random() * 0.4) * 100) / 100,
      lifecycle: i === 2 ? "frozen" : "active",
      practiceScore: 0.70 + i * 0.006 + Math.random() * 0.003,
      liveScore: i < 2 ? 0.72 + Math.random() * 0.004 : null,
      foldPerformance: ["F0", "F1", "F2", "F3", "F4"].map((f) => ({ fold: f, score: 0.66 + i * 0.006 + Math.random() * 0.03 })),
      featureImportance: Array.from({ length: 10 }, (_, k) => ({ feature: `f_anon_${String(k + 1).padStart(3, "0")}`, importance: Math.round(Math.random() * 100) / 100 })),
      provenance: SYN,
      generatedAt: NOW(),
    }));
    return env("models", rows);
  }

  async getFeatureLab(): Promise<DataEnvelope<FeatureLabData>> {
    const features = Array.from({ length: 30 }, (_, i) => ({
      id: `f_anon_${String(i + 1).padStart(3, "0")}`,
      missingness: Math.round(Math.random() * 8 * 100) / 100,
      cardinality: Math.floor(10 + Math.random() * 5000),
      importance: Math.round(Math.random() * 100) / 100,
      importanceStd: Math.round(Math.random() * 20) / 100,
      redundancy: Math.round(Math.random() * 80) / 100,
      exposure: Math.round(50 + Math.random() * 50),
      selectionFreq: Math.round(Math.random() * 100),
      drift: Math.round(Math.random() * 30) / 100,
    }));

    return env("feature_lab", {
      summary: {
        featureCount: features.length,
        highMissingness: features.filter((f) => f.missingness > 5).length,
        unstable: features.filter((f) => f.importanceStd > 0.15).length,
        highExposure: features.filter((f) => f.exposure > 85).length,
        selectedByFrontier: features.filter((f) => f.selectionFreq > 60).length,
      },
      features,
      importanceSeries: features.slice(0, 15).map((f) => ({ feature: f.id, importance: f.importance })),
      correlationMatrix: features.slice(0, 8).flatMap((a) =>
        features.slice(0, 8).map((b) => ({ a: a.id, b: b.id, corr: a.id === b.id ? 1 : Math.round((Math.random() * 2 - 1) * 100) / 100 }))
      ),
    });
  }

  async getEnsembles(): Promise<DataEnvelope<EnsembleData>> {
    return env("ensembles", {
      currentBlend: "blend-01",
      availableStrategies: ["rank_average", "weighted", "greedy", "diversity_aware"],
      activeStrategy: "weighted",
      candidatePool: MODELS.map((m, i) => ({ model: m, localScore: 0.70 + i * 0.006, diversity: [0.74, 0.62, 0.55, 0.41][i] })),
      members: MODELS.map((m, i) => ({
        model: m,
        weight: [0.4, 0.3, 0.2, 0.1][i],
        localScore: 0.70 + i * 0.006 + Math.random() * 0.003,
        practiceScore: 0.71 + i * 0.004,
        liveScore: i < 2 ? 0.718 + Math.random() * 0.004 : null,
      })),
      metrics: {
        localUpliftVsBest: 0.0042,
        recentUplift: 0.0019,
        worstFoldChange: 0.003,
        meanPairwiseCorr: 0.58,
        effectiveModels: 3.1,
        exposureChange: -0.04,
        practiceUplift: 0.0026,
        liveUplift: null,
      },
      predCorrelation: MODELS.flatMap((a, ai) =>
        MODELS.map((b, bi) => ({ a, b, corr: ai === bi ? 1 : Math.round((0.3 + Math.random() * 0.6) * 100) / 100 }))
      ),
      marginalContrib: MODELS.map((m, i) => ({ model: m, contribution: [0.018, 0.009, 0.006, 0.003][i] })),
      scoreDiversityScatter: MODELS.map((m, i) => ({ model: m, score: 0.70 + i * 0.006, diversity: [0.74, 0.62, 0.55, 0.41][i] })),
      foldScore: ["F0", "F1", "F2", "F3", "F4"].flatMap((f) =>
        MODELS.map((m, i) => ({ fold: f, model: m, score: 0.68 + i * 0.008 + Math.random() * 0.02 }))
      ),
    });
  }

  async getLeaderboard(): Promise<DataEnvelope<LeaderboardData>> {
    const entries = Array.from({ length: 20 }, (_, i) => ({
      rank: i + 1,
      alias: i === 1 ? "blend-01" : `anon-${String(i + 1).padStart(3, "0")}`,
      score: 0.76 - i * 0.004 + (Math.random() - 0.5) * 0.001,
      scoreChange: (Math.random() - 0.5) * 0.01,
      rankChange: Math.round((Math.random() - 0.5) * 4),
      round: "R3",
      isOurs: i === 1,
      provenance: "OFFICIAL_PLATFORM_OBSERVATION" as Provenance,
      generatedAt: NOW(),
    }));

    return env("leaderboard", {
      source: "Everesteer",
      currentRound: entries,
      cumulative: entries.map((e) => ({ ...e, rank: e.rank ? e.rank + 1 : null })),
      ourAliases: entries.filter((e) => e.isOurs).map((e) => ({ ...e, localVsPracticeGap: 0.0036, practiceVsLiveGap: null })),
      history: ROUNDS.map((r, i) => ({ round: r, rank: 8 - i, score: 0.695 + i * 0.009 })),
      rankTrajectory: ROUNDS.map((r, i) => ({ round: r, rank: 8 - i })),
      scoreTrajectory: ROUNDS.map((r, i) => ({ round: r, score: 0.695 + i * 0.009 })),
      roundModelMatrix: MODELS.flatMap((m) =>
        ROUNDS.map((r, ri) => ({ model: m, round: r, score: 0.69 + ri * 0.008 + Math.random() * 0.005 }))
      ),
    }, "Everesteer");
  }

  async getSubmission(): Promise<DataEnvelope<SubmissionData>> {
    return env("submission", {
      quotaTotal: 20,
      quotaUsed: 12,
      quotaPractice: 3,
      quotaLiveReserve: 3,
      quotaEmergency: 1,
      candidates: MODELS.map((m, i) => {
        const pickleOk = i !== 2;
        const integrityOk = pickleOk;
        const blockingReasons: string[] = [];
        if (!pickleOk) blockingReasons.push("Model artefact is stale — re-train or re-pickle before submitting");
        return {
          id: `cand-${i + 1}`,
          model: m,
          lane: "live",
          splitFingerprint: "fp-a3b9c1",
          idCoverage: 100,
          duplicates: 0,
          boundsOk: true,
          pickleOk,
          predHash: `sha256:pred-${i}`,
          modelHash: `sha256:model-${i}`,
          lineage: `${m} ← ${i === 0 ? "baseline" : MODELS[i - 1]}`,
          laneAllowed: true,
          quotaAllows: true,
          integrityOk,
          blockingReasons,
        };
      }),
      stepperSteps: [
        { label: "Select", status: "PASS", message: "blend-01 selected" },
        { label: "Infer", status: "RUNNING", message: "4,820 rows", startedAt: AGO(192), etaSeconds: 120 },
        { label: "Validate", status: "NOT_STARTED" },
        { label: "Package", status: "NOT_STARTED" },
        { label: "Dry run", status: "NOT_STARTED" },
        { label: "Submit", status: "NOT_STARTED" },
        { label: "Record", status: "NOT_STARTED" },
      ],
      selectedCandidate: "cand-1",
    });
  }

  async getStaking(): Promise<DataEnvelope<StakingData>> {
    return env("staking", {
      classification: "VIRTUAL_EVENT_BALANCE",
      statement: "This event uses a virtual competition balance. No real wallet is involved.",
      virtualBalance: 10000,
      evidence: "Event configuration specifies virtual credits only. No wallet connected.",
      uncertainty: "None — event type confirmed as virtual hackathon.",
      candidates: MODELS.map((m, i) => ({
        model: m,
        localEvidence: 0.70 + i * 0.006,
        liveEvidence: i < 2 ? 0.718 + Math.random() * 0.004 : null,
        uncertainty: Math.round((0.1 + Math.random() * 0.2) * 100) / 100,
        correlation: i === 3 ? 1 : Math.round((0.4 + Math.random() * 0.4) * 100) / 100,
        proposedAllocationPct: [40, 30, 20, 10][i],
      })),
      concentration: 0.42,
      riskProfile: "Moderate — virtual credits, no real exposure.",
      requiresConfirmation: false,
      updatedAt: NOW(),
    });
  }

  async getComputeJobs(): Promise<DataEnvelope<ComputeData>> {
    return env("compute", {
      hardware: {
        os: "Ubuntu 22.04 (WSL2)",
        cpu: { model: "Intel Core i7-10750H", cores: 12, usedPct: 62 },
        ram: { usedGb: 9.8, totalGb: 16 },
        gpu: { name: "NVIDIA GeForce RTX 3070", vramUsedGb: 5.2, vramTotalGb: 8, cuda: "12.4" },
        disk: { usedGb: 214, totalGb: 512 },
      },
      utilisation: {
        gpuUtilPct: 74,
        vramUtilPct: 65,
        ramPressurePct: 61,
        queueLength: 3,
        experimentsPerHour: 4.2,
      },
      localQueue: [
        job({ id: "job-001", name: "LightGBM R2", type: "TRAIN", candidate: "lgbm-r2", status: "RUNNING", startedAt: AGO(192), etaSeconds: 120, totalSeconds: 312, progress: 0.62, device: "GPU" }),
        job({ id: "job-002", name: "blend-01 inference", type: "INFER", candidate: "blend-01", status: "QUEUED", queuePosition: 1, etaSeconds: 720, device: "GPU" }),
        job({ id: "job-003", name: "R2 validation", type: "VALIDATE", candidate: "lgbm-r2", status: "QUEUED", queuePosition: 2, etaSeconds: 900, device: "CPU" }),
      ],
      serverQueue: [],
      eventWatcher: { active: true, lastPing: AGO(4), interval: "30s" },
      runtimeHistory: Array.from({ length: 12 }, (_, i) => ({
        ts: AGO((12 - i) * 900),
        durationMin: 5 + Math.random() * 25,
        type: ["TRAIN", "INFER", "VALIDATE"][i % 3],
      })),
      updatedAt: NOW(),
    });
  }

  async getRepository(): Promise<DataEnvelope<RepoData>> {
    return env("repository", {
      servingBranch: "main",
      servingSha: "a1b2c3d",
      dirty: false,
      pythonVersion: "3.11.9",
      everestApiPin: "everestapi==0.3.22",
      lockfileHash: "sha256:lock-7f21",
      frontendBuildSha: "fe-9c2e1a",
      backendBuildSha: "be-3d81f4",
      lastTests: { status: "passing", at: AGO(1800), detail: "142 passed, 0 failed" },
      lastRehearsal: { status: "passing", at: AGO(5400), detail: "Full submission rehearsal clean" },
      lastScorerParity: { status: "passing", at: AGO(600), detail: "Δ=0.0001 vs official scorer" },
      envHealth: "healthy",
      latestCommits: [
        { sha: "a1b2c3d", msg: "feat: add diversity-aware ensemble builder", author: "researcher", ts: AGO(1200) },
        { sha: "b2c3d4e", msg: "fix: id alignment check edge case", author: "researcher", ts: AGO(4800) },
        { sha: "c3d4e5f", msg: "chore: pin everestapi to 0.3.22", author: "researcher", ts: AGO(9600) },
      ],
      updatedAt: NOW(),
    });
  }

  async getDocumentation(): Promise<DataEnvelope<DocumentationData>> {
    return env("documentation", {
      generatedFromSha: "a1b2c3d",
      generatedAt: AGO(1800),
      sections: [
        { id: "start", label: "Start Here" },
        { id: "flows", label: "Workflows" },
        { id: "reference", label: "Reference" },
        { id: "runbooks", label: "Runbooks" },
        { id: "glossary", label: "Glossary" },
      ],
      articles: [
        {
          id: "start-here", title: "Start Here", description: "What this console is and how to use it during the event.",
          section: "start", order: 10, source: "curated",
          blocks: [
            { kind: "intro", text: "This console is your operating surface for the Everesteer hackathon: connect the event, prove a baseline, race experiments, validate, ensemble, submit, and operate live rounds." },
            { kind: "heading", text: "The shape of the day" },
            { kind: "paragraph", text: "Work flows left-to-right through the stages shown on Overview. You rarely need every page at once — the recommended next action tells you where to go." },
            { kind: "related", href: "/", label: "Open Overview" },
          ],
        },
        {
          id: "competition-workflow", title: "Competition Workflow", description: "End-to-end from connect to finalise.",
          section: "flows", order: 20, source: "curated",
          blocks: [
            { kind: "intro", text: "The full competition loop, from first connection to a recorded, finalised result." },
            { kind: "flow", nodes: [
              { id: "connect", label: "Connect event" },
              { id: "data", label: "Data ready" },
              { id: "baseline", label: "Baseline proven" },
              { id: "research", label: "Research" },
              { id: "validate", label: "Validate" },
              { id: "ensemble", label: "Ensemble" },
              { id: "submit", label: "Submit" },
              { id: "live", label: "Live round" },
              { id: "stake", label: "Stake / finalise" },
            ]},
            { kind: "callout", tone: "info", text: "Never skip baseline. Every later result is judged relative to the organiser baseline." },
          ],
        },
        {
          id: "research-loop", title: "Research Loop", description: "How a hypothesis becomes a candidate, frontier member or retired branch.",
          section: "flows", order: 30, source: "curated",
          blocks: [
            { kind: "intro", text: "How a hypothesis becomes a candidate, a frontier member, or a retired branch." },
            { kind: "flow", nodes: [
              { id: "hypothesis", label: "Hypothesis" },
              { id: "r0", label: "Smoke test" },
              { id: "r1", label: "Fast race" },
              { id: "r2", label: "Standard evidence" },
              { id: "frontier", label: "Frontier" },
              { id: "ensemble", label: "Ensemble candidate" },
            ]},
            { kind: "related", href: "/experiments", label: "Open Experiments" },
          ],
        },
        {
          id: "live-round-flow", title: "Live Round Flow", description: "What happens from round open to recorded result.",
          section: "flows", order: 40, source: "curated",
          blocks: [
            { kind: "intro", text: "Use this flow when Everesteer opens a live round. The objective is to move from a verified live split to a recorded submission without rebuilding the research system." },
            { kind: "flow", nodes: [
              { id: "detect", label: "Detect round" },
              { id: "snapshot", label: "Snapshot event" },
              { id: "pull", label: "Pull live data" },
              { id: "verify", label: "Verify split and IDs" },
              { id: "infer", label: "Run inference" },
              { id: "guard", label: "Submission checks" },
              { id: "submit", label: "Submit" },
              { id: "observe", label: "Record score and standing" },
            ]},
            { kind: "heading", text: "What to watch" },
            { kind: "metric", name: "Time remaining", text: "How long the current round remains open." },
            { kind: "metric", name: "Upload budget", text: "How many external submissions remain available." },
            { kind: "callout", tone: "warning", text: "Do not retrain automatically because a submission failed. First check lane, IDs, event state and the model artefact." },
            { kind: "related", href: "/round", label: "Open Round Room" },
          ],
        },
        {
          id: "submission-flow", title: "Submission Flow", description: "The controlled path from candidate to valid upload.",
          section: "flows", order: 50, source: "curated",
          blocks: [
            { kind: "intro", text: "Every submission is checked before it leaves the machine." },
            { kind: "flow", nodes: [
              { id: "select", label: "Select" },
              { id: "infer", label: "Infer" },
              { id: "validate", label: "Validate" },
              { id: "package", label: "Package" },
              { id: "dryrun", label: "Dry run" },
              { id: "submit", label: "Submit" },
              { id: "record", label: "Record" },
            ]},
            { kind: "related", href: "/submission", label: "Open Submission" },
          ],
        },
        {
          id: "cli-reference", title: "CLI Reference", description: "Generated from the Typer CLI.",
          section: "reference", order: 60, source: "generated",
          blocks: [
            { kind: "intro", text: "Generated from the project's Typer command definitions. Do not hand-edit." },
            { kind: "command", command: "qseh event connect --key $EVEREST_KEY" },
            { kind: "command", command: "qseh data pull --split live" },
            { kind: "command", command: "qseh baseline run" },
            { kind: "command", command: "qseh submit live --candidate blend-01" },
            { kind: "command", command: "qseh docs build" },
          ],
        },
        {
          id: "python-api", title: "Python API", description: "Generated from docstrings.",
          section: "reference", order: 70, source: "generated",
          blocks: [
            { kind: "intro", text: "Reference generated from Python module, class and function docstrings." },
            { kind: "paragraph", text: "DataSource, RaceEngine, EnsembleBuilder and SubmissionGuard are the primary entry points. Signatures are generated at docs build time from the pinned everestapi 0.3.22 environment." },
          ],
        },
        {
          id: "backend-api", title: "Backend API", description: "Generated from the FastAPI OpenAPI schema.",
          section: "reference", order: 80, source: "generated",
          blocks: [
            { kind: "intro", text: "Every DataSource method maps to a FastAPI route. Reference is generated from the OpenAPI schema." },
            { kind: "command", command: "GET /api/overview" },
            { kind: "command", command: "GET /api/round" },
            { kind: "command", command: "POST /api/submit/live" },
          ],
        },
        {
          id: "config-reference", title: "Configuration Reference", description: "Generated from Pydantic config models.",
          section: "reference", order: 90, source: "generated",
          blocks: [
            { kind: "intro", text: "Configuration keys and defaults, generated from the Pydantic settings models." },
          ],
        },
        {
          id: "runbook-reconnect", title: "Runbook: Reconnect mid-round", description: "Recover the console during a live round.",
          section: "runbooks", order: 100, source: "curated",
          blocks: [
            { kind: "intro", text: "If the event connection drops during an open round, recover without retraining." },
            { kind: "callout", tone: "danger", text: "Do not submit until the split fingerprint re-verifies against the live data." },
            { kind: "command", command: "qseh event reconnect && qseh data verify --split live" },
            { kind: "related", href: "/round", label: "Open Round Room" },
          ],
        },
        {
          id: "glossary", title: "Glossary", description: "Domain terms used across the console.",
          section: "glossary", order: 110, source: "curated",
          blocks: [
            { kind: "intro", text: "Definitions for the domain terminology used throughout the console." },
            { kind: "metric", name: "CORR20", text: "Rank correlation of predictions against the target over a 20-period window — a core competition scoring component." },
            { kind: "metric", name: "AIMC", text: "Adjusted information-metric component reported by the event scorer." },
            { kind: "metric", name: "NCORR", text: "Neutralised correlation — correlation after feature exposure is removed." },
            { kind: "metric", name: "IC / ICIR", text: "Information coefficient and its consistency ratio (mean IC over its standard deviation)." },
            { kind: "metric", name: "exped", text: "Expedition — the event's cross-sectional scoring unit." },
            { kind: "metric", name: "OOF", text: "Out-of-fold predictions produced on data the model did not train on." },
            { kind: "metric", name: "frontier", text: "Candidates not dominated on the score / diversity / runtime trade-off." },
          ],
        },
      ],
    });
  }

  // Actions
  async refreshEvent(): Promise<ActionResult> { return ok("Event refreshed"); }
  async snapshotEvent(): Promise<ActionResult> { return ok("Snapshot created: snap-2026-08-12T10:03Z"); }
  async pullDatasets(): Promise<ActionResult> { return ok("Datasets pulled — no changes detected"); }
  async runScorerParity(): Promise<ActionResult> { return ok("Scorer parity: local ≈ official (Δ=0.0001)"); }
  async runOfficialBaseline(): Promise<ActionResult> { return ok("Official baseline run: 0.6834"); }
  async startAutopilot(): Promise<ActionResult> { return ok("Autopilot started (profile: fast-race)"); }
  async stopAutopilot(): Promise<ActionResult> { return ok("Autopilot stopped"); }
  async startRace(profile: string): Promise<ActionResult> { return ok(`Race started (${profile})`); }
  async buildEnsemble(strategy: string): Promise<ActionResult> { return ok(`Ensemble preview built (${strategy})`); }
  async saveEnsembleCandidate(strategy: string): Promise<ActionResult> { return ok(`Ensemble candidate saved (${strategy})`); }
  async promoteEnsemble(): Promise<ActionResult> { return ok("Blend promoted to champion candidate"); }
  async validateSubmission(id: string): Promise<ActionResult> { return ok(`Validation passed for ${id}`); }
  async submitPractice(id: string): Promise<ActionResult> { return ok(`Practice submitted: ${id}`); }
  async submitLive(id: string): Promise<ActionResult> { return ok(`Live submitted: ${id}`); }
  async stopJob(id: string): Promise<ActionResult> { return ok(`Job ${id} stopped`); }
}
