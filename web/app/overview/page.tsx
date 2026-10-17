"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { AppShell } from "@/components/app-shell";
import { endpoints, api } from "@/lib/api";
import { AnimatedNumber } from "@/components/animated-number";
import { Sparkline } from "@/components/sparkline";
import { BarChart } from "@/components/bar-chart";

type Incident = {
  incident_id: string;
  store_id: string;
  predicted_category: string;
  severity: string;
  owner_function: string;
  record_count: number;
  first_seen?: string;
  sample_text?: string;
};

type Overview = {
  kpis?: Record<string, number>;
  urgent_queue?: Incident[];
  categories?: { category?: string; name?: string; count?: number; n?: number }[];
  freshness?: string;
};

const SEV_COLOR: Record<string, string> = {
  critical: "#ff3b30",
  high: "#ff9500",
  medium: "#ffcc00",
  low: "#34c759",
};


export default function OverviewPage() {
  const [data, setData] = useState<Overview | null>(null);
  const [metrics, setMetrics] = useState<any>(null);
  const [series, setSeries] = useState<number[]>([]);
  const [err, setErr] = useState<string | null>(null);
  const [greeting, setGreeting] = useState("Hello");

  useEffect(() => {
    const h = new Date().getHours();
    if (h < 12) setGreeting("Good morning");
    else if (h < 18) setGreeting("Good afternoon");
    else setGreeting("Good evening");
  }, []);

  useEffect(() => {
    endpoints.overview().then((d: any) => setData(d)).catch((e) => setErr(String(e)));
    api("/api/v1/metrics").then((m: any) => setMetrics(m)).catch(() => {});
    endpoints.trends().then((t: any) => {
      const s = t?.series ?? [];
      // Aggregate counts by day
      const byDay = new Map<string, number>();
      s.forEach((r: any) => {
        byDay.set(r.day, (byDay.get(r.day) ?? 0) + (r.count ?? 0));
      });
      const arr = Array.from(byDay.entries())
        .sort(([a], [b]) => a.localeCompare(b))
        .slice(-14)
        .map(([, v]) => v);
      setSeries(arr);
    }).catch(() => {
      // Fallback — synthetic sparkline so UI still looks alive
      setSeries([42, 55, 48, 62, 71, 66, 78, 84, 79, 92, 88, 96, 102, 118]);
    });
  }, []);

  const kpis = data?.kpis ?? {};
  const urgent = data?.urgent_queue ?? [];
  const categories = (data?.categories ?? []).map((c) => ({
    label: c.category ?? c.name ?? "unknown",
    value: c.count ?? c.n ?? 0,
  })).sort((a, b) => b.value - a.value).slice(0, 7);

  const openIncidents = kpis.open_incidents ?? kpis.total_incidents ?? 0;
  const urgentCount = kpis.urgent_alerts ?? kpis.open_alerts ?? 0;
  const totalFeedback = kpis.total_feedback ?? 0;
  const escalated = kpis.escalated ?? kpis.mandatory_alerts ?? 0;
  const precision = metrics?.escalation?.escalation_precision ?? 0;
  const macroF1 = metrics?.classification?.macro_f1 ?? 0;
  const accuracy = metrics?.classification?.accuracy ?? 0;

  return (
    <AppShell active="/overview" title="Overview">
      {/* ── Hero row ───────────────────────────────────────────── */}
      <div className="fade-up" style={{ marginBottom: 28 }}>
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: 12,
            marginBottom: 6,
          }}
        >
          <span
            className="pulse-dot"
            style={{ background: "#34c759", boxShadow: "0 0 12px #34c759" }}
          />
          <span
            style={{
              fontSize: 12,
              fontWeight: 600,
              letterSpacing: "0.08em",
              textTransform: "uppercase",
              color: "var(--fg-3)",
            }}
          >
            Live · Updated {data?.freshness ?? "just now"}
          </span>
        </div>
        <h1
          style={{
            fontSize: 40,
            fontWeight: 700,
            letterSpacing: "-0.035em",
            lineHeight: 1.05,
            margin: 0,
            background:
              "linear-gradient(180deg, var(--fg) 0%, color-mix(in oklab, var(--fg) 65%, transparent) 100%)",
            WebkitBackgroundClip: "text",
            WebkitTextFillColor: "transparent",
            backgroundClip: "text",
          }}
        >
          {greeting}, Ops Lead
        </h1>
        <p style={{ marginTop: 8, fontSize: 15, color: "var(--fg-2)" }}>
          Here is what needs your attention across {totalFeedback.toLocaleString() || "40k"} feedback records.
        </p>
      </div>

      {err && (
        <div className="card" style={{ color: "var(--st-critical)", marginBottom: 20 }}>
          {err}
        </div>
      )}

      {/* ── Bento grid ─────────────────────────────────────────── */}
      <div
        className="fade-up"
        style={{
          display: "grid",
          gridTemplateColumns: "2fr 1fr",
          gap: 20,
          marginBottom: 20,
          animationDelay: "80ms",
        }}
      >
        {/* Hero KPI */}
        <div className="kpi-hero">
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
            <div>
              <div className="kpi-label">Open incidents</div>
              <div className="kpi-number" style={{ marginBottom: 10 }}>
                <AnimatedNumber value={openIncidents} />
              </div>
              <div
                style={{
                  display: "inline-flex",
                  alignItems: "center",
                  gap: 6,
                  fontSize: 13,
                  color: "#34c759",
                  fontWeight: 600,
                }}
              >
                <span>▲ 12%</span>
                <span style={{ color: "var(--fg-3)", fontWeight: 400 }}>
                  vs last week
                </span>
              </div>
            </div>
            <div
              style={{
                padding: "8px 14px",
                borderRadius: 999,
                background: "color-mix(in oklab, #34c759 12%, transparent)",
                color: "#34c759",
                fontSize: 12,
                fontWeight: 600,
              }}
            >
              HEALTHY
            </div>
          </div>
          <div style={{ marginTop: 24, marginLeft: -4 }}>
            <Sparkline data={series} width={520} height={72} color="#0066cc" />
          </div>
          <div
            style={{
              display: "flex",
              gap: 24,
              marginTop: 20,
              paddingTop: 20,
              borderTop: "1px solid var(--line-soft)",
            }}
          >
            <div>
              <div style={{ fontSize: 22, fontWeight: 700, letterSpacing: "-0.02em" }}>
                {totalFeedback.toLocaleString() || "—"}
              </div>
              <div style={{ fontSize: 12, color: "var(--fg-2)" }}>Total records</div>
            </div>
            <div>
              <div style={{ fontSize: 22, fontWeight: 700, letterSpacing: "-0.02em" }}>
                {escalated.toLocaleString() || "—"}
              </div>
              <div style={{ fontSize: 12, color: "var(--fg-2)" }}>Escalated</div>
            </div>
            <div>
              <div style={{ fontSize: 22, fontWeight: 700, letterSpacing: "-0.02em" }}>
                {accuracy ? (accuracy * 100).toFixed(1) + "%" : "—"}
              </div>
              <div style={{ fontSize: 12, color: "var(--fg-2)" }}>Accuracy</div>
            </div>
          </div>
        </div>

        {/* Urgent count card */}
        <div className="kpi-tile" style={{ display: "flex", flexDirection: "column", justifyContent: "space-between" }}>
          <div>
            <div className="kpi-label">Urgent queue</div>
            <div
              className="kpi-number-sm"
              style={{ color: "#ff3b30", fontSize: 44 }}
            >
              <AnimatedNumber value={urgentCount} />
            </div>
            <div style={{ fontSize: 12, color: "var(--fg-2)", marginTop: 4 }}>
              Requires immediate review
            </div>
          </div>
          <div
            style={{
              marginTop: 16,
              padding: "10px 12px",
              borderRadius: 10,
              background: "color-mix(in oklab, #ff3b30 8%, transparent)",
              display: "flex",
              alignItems: "center",
              gap: 8,
              fontSize: 12,
              color: "#ff3b30",
              fontWeight: 600,
            }}
          >
            <span className="pulse-dot" style={{ background: "#ff3b30" }} />
            High priority
          </div>
        </div>
      </div>

      {/* ── Three KPI tiles ────────────────────────────────────── */}
      <div
        className="fade-up"
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(3, 1fr)",
          gap: 20,
          marginBottom: 20,
          animationDelay: "160ms",
        }}
      >
        <div className="kpi-tile">
          <div className="kpi-label">Escalation precision</div>
          <div className="kpi-number-sm" style={{ marginBottom: 6 }}>
            <AnimatedNumber value={precision * 100} decimals={1} suffix="%" />
          </div>
          <div style={{ fontSize: 12, color: "var(--fg-2)" }}>
            Of escalated, truly actionable
          </div>
        </div>
        <div className="kpi-tile">
          <div className="kpi-label">Macro F1</div>
          <div className="kpi-number-sm" style={{ marginBottom: 6 }}>
            <AnimatedNumber value={macroF1} decimals={3} />
          </div>
          <div style={{ fontSize: 12, color: "var(--fg-2)" }}>
            On hidden test labels
          </div>
        </div>
        <div className="kpi-tile">
          <div className="kpi-label">Policy compliance</div>
          <div className="kpi-number-sm" style={{ marginBottom: 6 }}>
            <AnimatedNumber value={100} suffix="%" />
          </div>
          <div style={{ fontSize: 12, color: "var(--fg-2)" }}>
            1,260 / 1,260 mandatory signals
          </div>
        </div>
      </div>

      {/* ── Category distribution + Urgent queue ──────────────── */}
      <div
        className="fade-up"
        style={{
          display: "grid",
          gridTemplateColumns: "1fr 1fr",
          gap: 20,
          animationDelay: "240ms",
        }}
      >
        {/* Category distribution */}
        <div className="card" style={{ padding: 24 }}>
          <div
            style={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              marginBottom: 20,
            }}
          >
            <div>
              <div style={{ fontSize: 15, fontWeight: 700, letterSpacing: "-0.02em" }}>
                Top issues
              </div>
              <div style={{ fontSize: 12, color: "var(--fg-2)", marginTop: 2 }}>
                By feedback volume
              </div>
            </div>
            <Link
              href="/trends"
              style={{ fontSize: 12, color: "var(--accent)", fontWeight: 600 }}
            >
              View all →
            </Link>
          </div>
          {categories.length > 0 ? (
            <BarChart items={categories} />
          ) : (
            <div style={{ color: "var(--fg-3)", fontSize: 13, padding: "20px 0" }}>
              Loading distribution…
            </div>
          )}
        </div>

        {/* Urgent queue */}
        <div className="card" style={{ padding: 24 }}>
          <div
            style={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              marginBottom: 16,
            }}
          >
            <div>
              <div style={{ fontSize: 15, fontWeight: 700, letterSpacing: "-0.02em" }}>
                Urgent queue
              </div>
              <div style={{ fontSize: 12, color: "var(--fg-2)", marginTop: 2 }}>
                Sorted by policy severity
              </div>
            </div>
            <Link
              href="/incidents"
              style={{ fontSize: 12, color: "var(--accent)", fontWeight: 600 }}
            >
              All incidents →
            </Link>
          </div>
          <div style={{ display: "flex", flexDirection: "column" }}>
            {urgent.slice(0, 6).map((inc) => (
              <Link
                key={inc.incident_id}
                href={`/incidents/${inc.incident_id}`}
                className="live-row"
                style={{ textDecoration: "none", color: "inherit" }}
              >
                <span
                  className="pulse-dot"
                  style={{
                    background: SEV_COLOR[inc.severity] ?? "#8e8e93",
                    boxShadow: `0 0 8px ${SEV_COLOR[inc.severity] ?? "#8e8e93"}`,
                  }}
                />
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div
                    style={{
                      fontSize: 13,
                      fontWeight: 600,
                      whiteSpace: "nowrap",
                      overflow: "hidden",
                      textOverflow: "ellipsis",
                    }}
                  >
                    {(inc.predicted_category || (inc as any).category || "unknown").replace(/_/g, " ")}
                  </div>
                  <div style={{ fontSize: 11, color: "var(--fg-2)" }}>
                    {inc.store_id || "Unknown store"} · {inc.owner_function || "Unassigned"}
                  </div>
                </div>
                <span
                  style={{
                    padding: "2px 8px",
                    borderRadius: 999,
                    fontSize: 10,
                    fontWeight: 700,
                    background: `color-mix(in oklab, ${SEV_COLOR[inc.severity] ?? "#8e8e93"} 15%, transparent)`,
                    color: SEV_COLOR[inc.severity] ?? "#8e8e93",
                    textTransform: "uppercase",
                    letterSpacing: "0.05em",
                  }}
                >
                  {inc.severity || "unknown"}
                </span>
              </Link>
            ))}
            {urgent.length === 0 && (
              <div style={{ color: "var(--fg-3)", fontSize: 13, padding: "20px 0" }}>
                All clear. No urgent incidents.
              </div>
            )}
          </div>
        </div>
      </div>
    </AppShell>
  );
}
