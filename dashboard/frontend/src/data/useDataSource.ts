import { DemoDataSource } from "./demo";
import { ApiDataSource } from "./api";
import type { DataSource } from "./types";

const mode = import.meta.env.VITE_DATA_MODE ?? "demo";

let _source: DataSource | null = null;

export function getDataSource(): DataSource {
  if (_source) return _source;
  if (mode === "api") {
    _source = new ApiDataSource(import.meta.env.VITE_API_BASE ?? "");
  } else {
    _source = new DemoDataSource();
  }
  return _source;
}

export function useDataSource(): DataSource {
  return getDataSource();
}

export function isDemo(): boolean {
  return mode !== "api";
}
