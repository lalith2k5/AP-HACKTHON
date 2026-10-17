"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { AppShell } from "@/components/app-shell";
import { endpoints } from "@/lib/api";
import { AnimatedNumber } from "@/components/animated-number";

type Incident = {
  incident_id: string;
  store_id: string;
  predicted_category: string;
  severity: string;
  owner_function: string;
  record_count: number;
};

const SEV_COLOR: Record<string, string> = {
  critical: "#ff3b30", high: "#ff9500", medium: "#ffcc00", low: "#34c759",
};

export default function IncidentsPage() {
  const [rows, setRows] = useState<Incident[] | null>(null);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    endpoints.incidents()
      .then((d: any) => setRows(d.items ?? d.incidents ?? d))
      .catch((e) => setErr(String(e)));
  }, []);

  const total = rows?.length ?? 0;
  const critical = rows?.filter((r) => r.severity === "critical").length ?? 0;
  const high = rows?.filter((r) => r.severity === "high").length ?? 0;

  return (
    <AppShell active="/incidents" title="Incidents">
      <div className="fade-up" style={{ marginBottom: 28 }}>
        <h1 style={{ fontSize: 32, fontWeight: 700, letterSpacing: "-0.03em", margin: 0 }}>
          Incidents
        </h1>
        <p style={{ marginTop: 8, fontSize: 15, color: "var(--fg-2)" }}>
          Traceable issues grouped by evidence and routed to owning teams.
        </p>
      </div>

      {err && <div className="card" style={{ color: "var(--st-critical)" }}>{err}</div>}

      {/* Summary strip */}
      <div className="fade-up" style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 16, marginBottom: 28, animationDelay: "80ms" }}>
        <div className="kpi-tile">
          <div className="kpi-label">Total incidents</div>
          <div className="kpi-number-sm">
            <AnimatedNumber value={total} />
          </div>
        </div>
        <div className="kpi-tile">
          <div className="kpi-label">Critical</div>
          <div className="kpi-number-sm" style={{ color: "#ff3b30" }}>
            <AnimatedNumber value={critical} />
          </div>
        </div>
        <div className="kpi-tile">
          <div className="kpi-label">High</div>
          <div className="kpi-number-sm" style={{ color: "#ff9500" }}>
            <AnimatedNumber value={high} />
          </div>
        </div>
      </div>

      {/* Incident list */}
      {rows && (
        <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
          {rows.slice(0, 50).map((r, i) => (
            <Link
              key={r.incident_id || `inc-${i}`}
              href={`/incidents/${r.incident_id}`}
              className="kpi-tile fade-up"
              style={{
                display: "flex",
                alignItems: "center",
                gap: 20,
                textDecoration: "none",
                color: "inherit",
                animationDelay: `${Math.min(i * 30, 300)}ms`,
                padding: "18px 24px",
              }}
            >
              <span
                className="pulse-dot"
                style={{
                  background: SEV_COLOR[r.severity] ?? "#8e8e93",
                  boxShadow: `0 0 8px ${SEV_COLOR[r.severity] ?? "#8e8e93"}`,
                }}
              />
              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ fontSize: 16, fontWeight: 600, letterSpacing: "-0.01em", color: "var(--fg)" }}>
                  {(r.predicted_category || "unknown").replace(/_/g, " ")}
                </div>
                <div style={{ fontSize: 13, color: "var(--fg-2)", marginTop: 2 }}>
                  {r.incident_id} · {r.store_id} · {r.owner_function}
                </div>
              </div>
              <div style={{ textAlign: "right" }}>
                <div style={{ fontSize: 14, fontWeight: 600 }}>{r.record_count} rec</div>
                <div style={{ fontSize: 11, color: "var(--fg-3)", textTransform: "uppercase", fontWeight: 600 }}>
                  {r.severity}
                </div>
              </div>
            </Link>
          ))}
        </div>
      )}
    </AppShell>
  );
}
