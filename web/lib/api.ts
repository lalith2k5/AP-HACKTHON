// StoreSignal — FastAPI client.
// Backend runs at http://localhost:8790 (HANDOFF section 8).
// Next 16 has cacheComponents:true, so fetches default to no-store.

const API_BASE =
  process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, "") ?? "http://localhost:8790";

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
  alerts: (params?: Record<string, string>) =>
    api(`/api/v1/alerts${params ? `?${new URLSearchParams(params)}` : ""}`),
  brief: (regionId: string, params?: Record<string, string>) =>
    api(`/api/v1/briefs/${regionId}${params ? `?${new URLSearchParams(params)}` : ""}`),
  briefWeekly: () => api("/api/v1/briefs/weekly"),
} as const;

export { API_BASE };
