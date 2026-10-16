"use client";
import { useEffect, useState } from "react";
import { AppShell } from "@/components/app-shell";
import { api, endpoints } from "@/lib/api";

type Trend = { series: {day:string;predicted_category:string;count:number}[]; anomalies: any[] };

export default function TrendsPage() {
  const [region, setRegion] = useState("");
  const [data, setData] = useState<Trend | null>(null);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    const params: Record<string,string> = {};
    if (region) params.region_id = region;
    api<Trend>("/api/v1/trends" + (Object.keys(params).length ? "?" + new URLSearchParams(params) : ""))
      .then(setData)
      .catch((e) => setErr(String(e)));
  }, [region]);

  const byCat: Record<string, number> = {};
  data?.series.forEach((r) => { byCat[r.predicted_category] = (byCat[r.predicted_category] ?? 0) + r.count; });
  const top = Object.entries(byCat).sort((a,b) => b[1]-a[1]).slice(0, 12);

  return (
    <AppShell active="/trends" title="Trends">
      <div className="space-y-10">
        <div className="flex items-center gap-3">
          <label className="text-sm font-medium">Region</label>
          <select value={region} onChange={(e) => setRegion(e.target.value)}
            className="rounded-2xl border border-border bg-background px-3 py-1.5 text-sm">
            <option value="">All</option>
            <option value="DEL">DEL</option>
            <option value="MUM">MUM</option>
            <option value="BLR">BLR</option>
            <option value="HYD">HYD</option>
            <option value="CHN">CHN</option>
          </select>
        </div>

        {err && <div className="rounded-2xl border border-red-300 bg-red-50 px-4 py-3 text-sm text-red-700">{err}</div>}

        <section className="card-soft p-6">
          <h2 className="text-[15px] font-semibold tracking-tight">Category totals</h2>
          {top.length === 0 ? (
            <p className="mt-2 text-sm text-muted-foreground">No data for this filter.</p>
          ) : (
            <ul className="mt-3 space-y-2">
              {top.map(([cat, n]) => (
                <li key={cat} className="flex items-center gap-3">
                  <span className="w-56 truncate text-sm">{cat}</span>
                  <div className="h-2 flex-1 rounded-full bg-muted">
                    <div className="h-2 rounded-full bg-[var(--primary)]" style={{ width: `${Math.min(100, n / top[0][1] * 100)}%` }} />
                  </div>
                  <span className="w-16 text-right text-xs text-muted-foreground">{n}</span>
                </li>
              ))}
            </ul>
          )}
        </section>

        <section className="card-soft p-6">
          <h2 className="text-[15px] font-semibold tracking-tight">Anomalies flagged ({data?.anomalies.length ?? 0})</h2>
          {data?.anomalies.length ? (
            <table className="mt-3 w-full text-sm">
              <thead className="text-left text-xs uppercase tracking-wide text-muted-foreground">
                <tr><th className="py-2">Store</th><th>Category</th><th>Days flagged</th><th>Max z</th><th>Last flag</th></tr>
              </thead>
              <tbody>
                {data.anomalies.slice(0, 25).map((a, i) => (
                  <tr key={i} className="border-t border-[var(--border)]">
                    <td className="py-2">{a.store_id}</td>
                    <td>{a.predicted_category}</td>
                    <td>{a.num_flag_days}</td>
                    <td>{typeof a.max_robust_z === "number" ? a.max_robust_z.toFixed(2) : a.max_robust_z}</td>
                    <td>{a.last_flag_day}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <p className="mt-2 text-sm text-muted-foreground">No anomalies in this window.</p>
          )}
        </section>
      </div>
    </AppShell>
  );
}
