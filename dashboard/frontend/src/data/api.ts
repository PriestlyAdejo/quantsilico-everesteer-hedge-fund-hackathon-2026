import type {
  DataSource, DataEnvelope, ActionResult, EventStatus,
  OverviewData, EventControlData, RoundRoomData, DataLabData,
  ExperimentRow, ValidationData, ModelRow, FeatureLabData,
  EnsembleData, LeaderboardData, SubmissionData, StakingData,
  ComputeData, RepoData, DocumentationData,
} from "./types";

const UNAVAILABLE = "BACKEND UNAVAILABLE";

function unavailableEnvelope<T>(kind: string): DataEnvelope<T> {
  return {
    schemaVersion: 2,
    kind,
    provenance: "OFFICIAL_EVENT_STATE",
    generatedAt: new Date().toISOString(),
    stale: true,
    source: "Everesteer API",
    data: null as unknown as T,
  };
}

function unavailableAction(): ActionResult {
  return {
    ok: false,
    message: UNAVAILABLE,
    code: "BACKEND_UNAVAILABLE",
    timestamp: new Date().toISOString(),
  };
}

export class ApiDataSource implements DataSource {
  private base: string;
  constructor(base = "") { this.base = base; }

  private async get<T>(path: string, kind: string): Promise<DataEnvelope<T>> {
    try {
      const res = await fetch(`${this.base}${path}`);
      if (!res.ok) return unavailableEnvelope<T>(kind);
      return res.json();
    } catch {
      return unavailableEnvelope<T>(kind);
    }
  }

  private async post(path: string): Promise<ActionResult> {
    try {
      const res = await fetch(`${this.base}${path}`, { method: "POST" });
      if (!res.ok) return unavailableAction();
      return res.json();
    } catch {
      return unavailableAction();
    }
  }

  getEventStatus() { return this.get<EventStatus>("/api/event-status", "event_status"); }
  getOverview() { return this.get<OverviewData>("/api/overview", "overview"); }
  getEventControl() { return this.get<EventControlData>("/api/event-control", "event_control"); }
  getRoundRoom() { return this.get<RoundRoomData>("/api/round-room", "round_room"); }
  getDataLab() { return this.get<DataLabData>("/api/data-lab", "data_lab"); }
  getExperiments() { return this.get<ExperimentRow[]>("/api/experiments", "experiments"); }
  getValidation() { return this.get<ValidationData>("/api/validation", "validation"); }
  getModels() { return this.get<ModelRow[]>("/api/models", "models"); }
  getFeatureLab() { return this.get<FeatureLabData>("/api/feature-lab", "feature_lab"); }
  getEnsembles() { return this.get<EnsembleData>("/api/ensembles", "ensembles"); }
  getLeaderboard() { return this.get<LeaderboardData>("/api/leaderboard", "leaderboard"); }
  getSubmission() { return this.get<SubmissionData>("/api/submission", "submission"); }
  getStaking() { return this.get<StakingData>("/api/staking", "staking"); }
  getComputeJobs() { return this.get<ComputeData>("/api/compute", "compute"); }
  getRepository() { return this.get<RepoData>("/api/repository", "repository"); }
  getDocumentation() { return this.get<DocumentationData>("/api/docs", "documentation"); }

  refreshEvent() { return this.post("/api/actions/refresh-event"); }
  snapshotEvent() { return this.post("/api/actions/snapshot-event"); }
  pullDatasets() { return this.post("/api/actions/pull-datasets"); }
  runScorerParity() { return this.post("/api/actions/scorer-parity"); }
  runOfficialBaseline() { return this.post("/api/actions/official-baseline"); }
  startAutopilot() { return this.post("/api/actions/autopilot/start"); }
  stopAutopilot() { return this.post("/api/actions/autopilot/stop"); }
  startRace(profile: string) { return this.post(`/api/actions/race/start?profile=${profile}`); }
  buildEnsemble(strategy: string) { return this.post(`/api/actions/build-ensemble?strategy=${strategy}`); }
  saveEnsembleCandidate(strategy: string) { return this.post(`/api/actions/save-ensemble?strategy=${strategy}`); }
  promoteEnsemble() { return this.post("/api/actions/promote-ensemble"); }
  validateSubmission(id: string) { return this.post(`/api/actions/validate/${id}`); }
  submitPractice(id: string) { return this.post(`/api/actions/submit-practice/${id}`); }
  submitLive(id: string) { return this.post(`/api/actions/submit-live/${id}`); }
  stopJob(id: string) { return this.post(`/api/actions/jobs/${id}/stop`); }
}
