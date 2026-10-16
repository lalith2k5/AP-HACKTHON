// StoreSignal — FastAPI client.
// Backend runs at http://localhost:8790 (HANDOFF section 8).
// Next 16 has cacheComponents:true, so fetches default to no-store.

// All requests go through the Next.js proxy route. The real API key
// lives only on the server (process.env.STORESIGNAL_API_KEY) and never
// reaches the browser bundle.
const API_BASE = "/api/proxy";

export class ApiError extends Error {
  status: number;
  code?: string;
  requestId?: string;
  constructor(status: number, message: string, code?: string, requestId?: string) {
    super(message);
    this.status = status;
    this.code = code;
    this.requestId = requestId;
  }
}

type FetchOpts = Omit<RequestInit, "body"> & { body?: unknown };

export async function api<T>(path: string, opts: FetchOpts = {}): Promise<T> {
  const url = `${API_BASE}${path.startsWith("/") ? path : `/${path}`}`;
  const headers = new Headers(opts.headers);
  headers.set("Accept", "application/json");
  let body: BodyInit | undefined;
  if (opts.body !== undefined) {
    headers.set("Content-Type", "application/json");
    body = JSON.stringify(opts.body);
  }

  const res = await fetch(url, {
    ...opts,
    headers,
    body,
    cache: "no-store",
  });

  if (!res.ok) {
    let code: string | undefined;
    let requestId: string | undefined;
    let message = res.statusText || `HTTP ${res.status}`;
    try {
      const env = await res.json();
      // Spec 14.1 error envelope
      if (env?.error) {
        code = env.error.code;
        requestId = env.error.request_id;
        message = env.error.message ?? message;
      }
    } catch {
      /* non-JSON error body */
    }
    throw new ApiError(res.status, message, code, requestId);
  }

  if (res.status === 204) return undefined as T;
  return (await res.json()) as T;
}

export const endpoints = {
  health: () => api<{ status: string; version?: string; ready?: boolean }>("/health"),
  overview: (params?: Record<string, string>) =>
    api(`/api/v1/overview${params ? `?${new URLSearchParams(params)}` : ""}`),
  incidents: (params?: Record<string, string>) =>
    api(`/api/v1/incidents${params ? `?${new URLSearchParams(params)}` : ""}`),
  incident: (id: string) => api(`/api/v1/incidents/${id}`),
  replay: (id: string) => api(`/api/v1/replay/${id}`),
  patchIncident: (id: string, body: Record<string, unknown>) =>
    api(`/api/v1/incidents/${id}`, { method: "PATCH", body }),
  addNote: (id: string, body: { actor: string; note: string }) =>
    api(`/api/v1/incidents/${id}/notes`, { method: "POST", body }),
  timeline: (id: string) =>
    api(`/api/v1/incidents/${id}/timeline`),
  alerts: (params?: Record<string, string>) =>
    api(`/api/v1/alerts${params ? `?${new URLSearchParams(params)}` : ""}`),
  ackAlert: (id: string, body: { actor: string; note?: string }) =>
    api(`/api/v1/alerts/${id}/acknowledge`, { method: "POST", body }),
  resolveAlert: (id: string, body: { actor: string; note?: string }) =>
    api(`/api/v1/alerts/${id}/resolve`, { method: "POST", body }),
  overrideAlert: (id: string, body: { actor: string; note: string; decision?: string }) =>
    api(`/api/v1/alerts/${id}/override`, { method: "POST", body }),
  briefWeekly: () => api("/api/v1/briefs/weekly"),
  stores: (params?: Record<string, string>) =>
    api(`/api/v1/stores${params ? `?${new URLSearchParams(params)}` : ""}`),
  store: (id: string) => api(`/api/v1/stores/${id}`),
  trends: (params?: Record<string, string>) =>
    api(`/api/v1/trends${params ? `?${new URLSearchParams(params)}` : ""}`),
  audit: (params?: Record<string, string>) =>
    api(`/api/v1/audit${params ? `?${new URLSearchParams(params)}` : ""}`),
  metrics: () => api("/api/v1/metrics"),
  jobs: (id: string) => api(`/api/v1/jobs/${id}`),
  pipelineRun: () => api("/api/v1/pipeline/run", { method: "POST", body: {} }),
  evaluationRun: () => api("/api/v1/evaluation/run", { method: "POST", body: {} }),
  ingest: (body: Record<string, unknown>) =>
    api("/api/v1/ingest", { method: "POST", body }),
  ingestStatus: (id: string) => api(`/api/v1/ingest/${id}`),
  pipelineStatus: (id: string) => api(`/api/v1/pipeline/${id}`),
  evaluationStatus: (id: string) => api(`/api/v1/evaluation/${id}`),
  demoReset: () => api("/api/v1/demo/reset", { method: "POST", body: {} }),
} as const;

export { API_BASE };
