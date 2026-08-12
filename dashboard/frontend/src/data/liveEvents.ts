/** Bounded SSE client with poll fallback for Research Console live updates. */

export type LiveHandler = (eventType: string, payload: unknown) => void;

export function connectLiveEvents(
  onEvent: LiveHandler,
  opts?: { base?: string; pollMs?: number },
): () => void {
  const base = opts?.base ?? "";
  const pollMs = opts?.pollMs ?? 5000;
  let closed = false;
  let es: EventSource | null = null;
  let pollTimer: ReturnType<typeof setInterval> | null = null;

  const startPoll = () => {
    if (pollTimer || closed) return;
    pollTimer = setInterval(() => {
      if (!closed) onEvent("poll_tick", { at: new Date().toISOString() });
    }, pollMs);
  };

  try {
    es = new EventSource(`${base}/api/events`);
    es.onmessage = (ev) => {
      try {
        const data = JSON.parse(ev.data) as { type?: string; payload?: unknown };
        onEvent(data.type ?? "message", data.payload ?? data);
      } catch {
        onEvent("message", ev.data);
      }
    };
    es.onerror = () => {
      es?.close();
      es = null;
      startPoll();
    };
  } catch {
    startPoll();
  }

  return () => {
    closed = true;
    es?.close();
    if (pollTimer) clearInterval(pollTimer);
  };
}
