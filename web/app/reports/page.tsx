"use client";

import { useEffect, useState } from "react";
import { AppShell } from "@/components/app-shell";
import { endpoints, ApiError } from "@/lib/api";

type TopIssue = {
  category: string;
  current_count: number;
  previous_count: number;
  trend: string;
  severity: string;
  owner_function: string;
  next_action: string;
  escalation_rule?: string;
};

type Brief = {
  region_id: string;
  region_name: string;
  week_start: string;
  week_end: string;
  total_feedback: number;
  total_feedback_previous_week: number;
  top_issues: TopIssue[];
};

type Metrics = {
  escalation?: {
    escalated_total?: number;
    escalation_precision?: number;
    escalation_recall?: number;
  };
};

const SEV_COLOR: Record<string, string> = {
  critical: "var(--status-critical)",
  high: "var(--status-high)",
  medium: "var(--status-medium)",
  low: "var(--status-low)",
};

const TREND_COLOR: Record<string, string> = {
  UP: "var(--status-critical)",
  DOWN: "var(--status-ok)",
  FLAT: "var(--muted-foreground)",
  NEW: "var(--status-high)",
};

const TREND_GLYPH: Record<string, string> = {
  UP: "\u2191",
  DOWN: "\u2193",
  FLAT: "\u2192",
  NEW: "\u2726",
};

export default function ReportsPage() {
  const [data, setData] = useState<Brief | null>(null);
  const [metrics, setMetrics] = useState<Metrics | null>(null);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    (async () => {
      try {
        const d = (await endpoints.briefWeekly()) as Brief;
        setData(d);
      } catch (e) {
        setErr((e as ApiError).message);
      }
      try {
        const m = (await endpoints.metrics()) as Metrics;
        setMetrics(m);
      } catch {
        // metrics optional
      }
    })();
  }, []);

  const mandatory = data?.top_issues.filter((t) =>
    (t.escalation_rule ?? "").startsWith("mandatory")
  ) ?? [];

  const delta = data
    ? data.total_feedback - data.total_feedback_previous_week
    : 0;

  return (
    <AppShell active="/reports" title="Weekly Report">
      <div className="fade-up" style={{ animationDelay: "0ms" }}>
      <div className="mb-4">
        <h2 className="text-[22px] font-semibold tracking-tight">Weekly regional brief</h2>
        <p className="mt-1 text-xs text-muted-foreground">
          Evidence-backed summary. Unverified feedback — not a determination of fact.
        </p>
      </div>

      {err && (
        <div className="rounded-3xl border border-[var(--status-medium)]/30 bg-[color-mix(in_oklch,var(--status-medium),transparent_94%)] p-4 text-sm">
          {err}
        </div>
      )}

      {data && (
        <div className="space-y-8">
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4 fade-up" style={{ animationDelay: "80ms" }}>
            <div className="glass p-5">
              <div className="text-xs font-medium uppercase tracking-wide text-muted-foreground">Region</div>
              <div className="mt-1 text-lg font-semibold">{data.region_name}</div>
              <div className="text-xs text-muted-foreground">{data.region_id}</div>
            </div>
            <div className="glass p-5">
              <div className="text-xs font-medium uppercase tracking-wide text-muted-foreground">Week</div>
              <div className="mt-1 text-sm font-medium">
                {data.week_start} → {data.week_end}
              </div>
            </div>
            <div className="glass p-5">
              <div className="text-xs font-medium uppercase tracking-wide text-muted-foreground">Feedback</div>
              <div className="mt-1 text-lg font-semibold">{data.total_feedback.toLocaleString()}</div>
              <div
                className="text-xs"
                style={{ color: delta > 0 ? "var(--status-critical)" : delta < 0 ? "var(--status-ok)" : "var(--muted-foreground)" }}
              >
                {delta >= 0 ? "+" : ""}
                {delta} vs previous week
              </div>
            </div>
            <div className="glass p-5">
              <div className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
                Escalation precision
              </div>
              <div className="mt-1 text-lg font-semibold">
                {metrics?.escalation?.escalation_precision != null
                  ? (metrics.escalation.escalation_precision * 100).toFixed(1) + "%"
                  : "\u2014"}
              </div>
              <div className="text-xs text-muted-foreground">
                {metrics?.escalation?.escalated_total != null
                  ? metrics.escalation.escalated_total.toLocaleString() + " escalated"
                  : "of escalated, truly actionable"}
              </div>
            </div>
          </div>

          <div className="row" style={{ gap: 8, flexWrap: "wrap" }}>
            <a className="btn btn-secondary btn-sm" href="/api/proxy/api/v1/export/brief/ALL.pdf" download>
              Download PDF
            </a>
            <a className="btn btn-secondary btn-sm" href="/api/proxy/api/v1/export/incidents.csv" download>
              Incidents CSV
            </a>
            <a className="btn btn-secondary btn-sm" href="/api/proxy/api/v1/export/audit.csv" download>
              Audit CSV
            </a>
          </div>

          <section>
            <h3 className="mb-2 text-sm font-semibold tracking-tight">Top issues</h3>
            <ul className="divide-y divide-border glass">
              {data.top_issues.map((t) => (
                <li key={t.category} className="p-4 hover-scale">
                  <div className="flex items-start justify-between gap-4">
                    <div className="min-w-0 flex-1">
                      <div className="flex flex-wrap items-center gap-2">
                        <span className="text-sm font-medium">{t.category.split("_").join(" ")}</span>
                        <span
                          className="text-xs font-medium uppercase"
                          style={{ color: SEV_COLOR[t.severity] ?? "var(--muted-foreground)" }}
                        >
                          {t.severity}
                        </span>
                        <span
                          className="rounded bg-muted px-1.5 py-0.5 text-[10px] font-semibold"
                          style={{ color: TREND_COLOR[t.trend] }}
                          title={"Trend vs previous week: " + t.trend}
                        >
                          {(TREND_GLYPH[t.trend] ?? "?") + " " + t.trend}
                        </span>
                      </div>
                      {t.next_action && (
                        <p className="mt-1.5 text-xs text-muted-foreground">{t.next_action}</p>
                      )}
                    </div>
                    <div className="shrink-0 text-right text-xs">
                      <div className="font-semibold">{t.current_count}</div>
                      <div className="text-muted-foreground">prev {t.previous_count}</div>
                    </div>
                  </div>
                </li>
              ))}
            </ul>
          </section>

          {mandatory.length > 0 && (
            <section>
              <h3 className="mb-2 text-sm font-semibold tracking-tight text-[var(--status-critical)]">
                Mandatory-risk section ({mandatory.length})
              </h3>
              <ul className="divide-y divide-border rounded-xl border border-[var(--status-critical)]/30 bg-card">
                {mandatory.map((m) => (
                  <li key={m.category} className="flex items-center justify-between px-4 py-3">
                    <div>
                      <span className="text-sm">{m.category.split("_").join(" ")}</span>
                      <span className="ml-2 text-xs text-muted-foreground">{m.owner_function}</span>
                    </div>
                    <span className="text-xs text-muted-foreground">{m.current_count}</span>
                  </li>
                ))}
              </ul>
            </section>
          )}
        </div>
      )}
    </div>
    </AppShell>
  );
}
