"use client";

import { useEffect, useState } from "react";
import { AppShell } from "@/components/app-shell";
import { endpoints } from "@/lib/api";
import { AnimatedNumber } from "@/components/animated-number";
import { BarChart } from "@/components/bar-chart";

export default function TrendsPage() {
  const [data, setData] = useState<any>(null);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    endpoints.trends()
      .then(setData)
      .catch((e) => setErr(String(e)));
  }, []);

  const byCat: Record<string, number> = {};
  data?.series?.forEach((r: any) => {
    byCat[r.predicted_category] = (byCat[r.predicted_category] ?? 0) + r.count;
  });
  const topCats = Object.entries(byCat)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 8)
    .map(([label, value]) => ({ label, value }));

  const anomalies = data?.anomalies ?? [];

  return (
    <AppShell active="/trends" title="Trends">
      <div className="fade-up" style={{ marginBottom: 28 }}>
        <h1 style={{ fontSize: 32, fontWeight: 700, letterSpacing: "-0.03em", margin: 0 }}>
          Emerging trends
        </h1>
        <p style={{ marginTop: 8, fontSize: 15, color: "var(--fg-2)" }}>
          Baseline vs current window. Robust z-score highlights anomalies.
        </p>
      </div>

      {err && <div className="card" style={{ color: "var(--st-critical)" }}>{err}</div>}

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 20 }}>
        {/* Categories */}
        <div className="glass-panel fade-up" style={{ padding: 24, animationDelay: "80ms" }}>
          <div className="kpi-label" style={{ marginBottom: 20 }}>Volume by category</div>
          {topCats.length > 0 ? <BarChart items={topCats} /> : <p className="muted">Loading…</p>}
        </div>

        {/* Anomalies */}
        <div className="glass-panel fade-up" style={{ padding: 24, animationDelay: "160ms" }}>
          <div className="kpi-label" style={{ marginBottom: 20 }}>
            Flagged anomalies (<AnimatedNumber value={anomalies.length} />)
          </div>
          <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
            {anomalies.slice(0, 8).map((a: any, i: number) => (
              <div key={i} className="hover-scale" style={{ padding: "12px 16px", borderRadius: 12, background: "var(--bg-inset)", border: "1px solid var(--line-soft)" }}>
                <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 4 }}>
                  <span style={{ fontWeight: 600, fontSize: 14 }}>{a.predicted_category?.replace(/_/g, " ")}</span>
                  <span style={{ color: "#ff3b30", fontWeight: 700, fontSize: 12 }}>z = {a.max_robust_z?.toFixed(2)}</span>
                </div>
                <div style={{ fontSize: 12, color: "var(--fg-2)" }}>{a.store_id} · {a.num_flag_days} days flagged</div>
              </div>
            ))}
            {anomalies.length === 0 && <p className="muted">No anomalies detected.</p>}
          </div>
        </div>
      </div>
    </AppShell>
  );
}
