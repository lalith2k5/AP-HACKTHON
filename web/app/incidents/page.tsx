"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { AppShell } from "@/components/app-shell";
import { endpoints, ApiError } from "@/lib/api";

type Incident = {
  incident_id: string;
  store_id: string;
  predicted_category: string;
  owner_function: string;
  severity: string;
  first_seen: string;
  last_seen: string;
  record_count: number;
  channels: string;
  sample_text: string;
  verification_status: string;
};

const SEV_COLOR: Record<string, string> = {
  critical: "var(--status-critical)",
  high:     "var(--status-high)",
  medium:   "var(--status-medium)",
  low:      "var(--status-low)",
};

export default function IncidentsPage() {
  const [items, setItems] = useState<Incident[] | null>(null);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    (async () => {
      try {
        const data = (await endpoints.incidents({ limit: "50" })) as Incident[];
        setItems(data);
      } catch (e) {
        setErr((e as ApiError).message);
      }
    })();
  }, []);

  return (
    <AppShell active="/incidents" title="Incidents">
      <div className="mb-4 flex items-baseline justify-between">
        <h2 className="text-[22px] font-semibold tracking-tight">Incidents</h2>
        <span className="text-xs text-muted-foreground">
          {items ? `${items.length} shown` : "loading..."}
        </span>
      </div>
      {err && (
        <div className="rounded-3xl border border-[var(--status-critical)]/30 bg-[color-mix(in_oklch,var(--status-critical),transparent_94%)] p-4 text-sm text-[var(--status-critical)]">
          {err}
        </div>
      )}
      {items && (
        <ul className="divide-y divide-border card-soft">
          {items.map((it) => (
            <li key={it.incident_id}>
              <Link
                href={`/incidents/${it.incident_id}`}
                className="flex items-center justify-between gap-4 px-4 py-3 transition-colors hover:bg-muted/40"
              >
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-2">
                    <span
                      aria-hidden
                      className="inline-block size-2 rounded-full"
                      style={{ background: SEV_COLOR[it.severity] ?? "var(--muted-foreground)" }}
                    />
                    <span className="text-sm font-medium truncate">
                      {it.predicted_category.replaceAll("_", " ")}
                    </span>
                    <span className="text-xs text-muted-foreground">· {it.store_id}</span>
                  </div>
                  <p className="mt-1 truncate text-xs text-muted-foreground">{it.sample_text}</p>
                </div>
                <div className="shrink-0 text-right">
                  <div className="text-xs font-medium uppercase text-muted-foreground">{it.severity}</div>
                  <div className="text-xs text-muted-foreground">{it.record_count} rec</div>
                </div>
              </Link>
            </li>
          ))}
        </ul>
      )}
    </AppShell>
  );
}
