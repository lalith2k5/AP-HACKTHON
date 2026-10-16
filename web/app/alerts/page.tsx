"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { AppShell } from "@/components/app-shell";
import { endpoints, ApiError } from "@/lib/api";

type Alert = {
  alert_id: string;
  trigger_type: string;
  incident_id: string;
  store_id: string;
  predicted_category: string;
  owner_function: string;
  severity: string;
  priority: number;
  reason: string;
  record_count: number;
  escalated_count: number;
  evidence: string;
  first_seen: string;
  last_seen: string;
  uncertainty: number;
};

const SEV_COLOR: Record<string, string> = {
  critical: "var(--status-critical)",
  high: "var(--status-high)",
  medium: "var(--status-medium)",
  low: "var(--status-low)",
};

export default function AlertsPage() {
  const [items, setItems] = useState<Alert[] | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [filter, setFilter] = useState<"all" | "critical" | "high">("all");

  useEffect(() => {
    (async () => {
      try {
        const data = (await endpoints.alerts({ limit: "100" })) as Alert[];
        setItems(data);
      } catch (e) {
        setErr((e as ApiError).message);
      }
    })();
  }, []);

  const filtered = items
    ? filter === "all"
      ? items
      : items.filter((a) => a.severity === filter)
    : null;

  return (
    <AppShell active="/alerts" title="Alerts">
      <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
        <h2 className="text-lg font-semibold tracking-tight">Alerts</h2>
        <div className="flex gap-1 rounded-lg border border-border bg-card p-0.5 text-xs">
          {(["all", "critical", "high"] as const).map((f) => (
            <button
              key={f}
              onClick={() => setFilter(f)}
              className={
                "rounded-md px-2.5 py-1 font-medium capitalize transition-colors " +
                (filter === f ? "bg-muted text-foreground" : "text-muted-foreground hover:text-foreground")
              }
            >
              {f}
            </button>
          ))}
        </div>
      </div>

      {err && (
        <div className="rounded-xl border border-[var(--status-critical)]/30 bg-[color-mix(in_oklch,var(--status-critical),transparent_94%)] p-4 text-sm text-[var(--status-critical)]">
          {err}
        </div>
      )}

      {filtered && (
        <ul className="space-y-2">
          {filtered.map((a) => (
            <li key={a.alert_id} className="rounded-xl border border-border bg-card p-4">
              <div className="flex items-start justify-between gap-4">
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-2">
                    <span
                      aria-hidden
                      className="inline-block size-2.5 rounded-full"
                      style={{ background: SEV_COLOR[a.severity] ?? "var(--muted-foreground)" }}
                    />
                    <span
                      className="text-xs font-semibold uppercase tracking-wide"
                      style={{ color: SEV_COLOR[a.severity] }}
                    >
                      {a.severity}
                    </span>
                    <span className="rounded bg-muted px-1.5 py-0.5 text-[10px] font-medium uppercase text-muted-foreground">
                      {a.trigger_type}
                    </span>
                  </div>
                  <p className="mt-2 text-sm">{a.reason}</p>
                  <div className="mt-2 flex flex-wrap gap-x-3 gap-y-1 text-xs text-muted-foreground">
                    <span>Store {a.store_id}</span>
                    <span>Owner {a.owner_function}</span>
                    <span>{a.record_count} records</span>
                    <span>uncertainty {a.uncertainty.toFixed(3)}</span>
                  </div>
                  {a.evidence && (
                    <p className="mt-2 line-clamp-1 text-xs italic text-muted-foreground">
                      {a.evidence}
                    </p>
                  )}
                </div>
                <Link
                  href={"/incidents/" + a.incident_id}
                  className="shrink-0 rounded-lg border border-border px-2.5 py-1 text-xs font-medium hover:bg-muted"
                >
                  Open
                </Link>
              </div>
            </li>
          ))}
        </ul>
      )}
    </AppShell>
  );
}
