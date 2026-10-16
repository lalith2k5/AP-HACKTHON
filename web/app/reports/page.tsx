"use client";

import { useEffect, useState } from "react";
import { AppShell } from "@/components/app-shell";
import { endpoints, ApiError } from "@/lib/api";

type Brief = {
  region_id?: string;
  generated_at?: string;
  period?: { from: string; to: string };
  executive_summary?: string;
  top_issues?: { category: string; count: number; severity?: string; stores?: string[] }[];
  mandatory_risk?: { category: string; count: number; reason?: string }[];
  evidence?: string[];
};

export default function ReportsPage() {
  const [data, setData] = useState<Brief | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [raw, setRaw] = useState<string | null>(null);

  useEffect(() => {
    (async () => {
      try {
        const d = (await endpoints.brief("HYD")) as Brief;
        setData(d);
      } catch (e) {
        const err2 = e as ApiError;
        setErr(err2.message);
        // The brief endpoint may return non-JSON / different shape; grab raw as fallback
        try {
          const r = await fetch("http://localhost:8790/api/v1/briefs/weekly");
          const t = await r.text();
          setRaw(t.slice(0, 2000));
        } catch {
          /* ignore */
        }
      }
    })();
  }, []);

  return (
    <AppShell active="/reports" title="Weekly Report">
      <div className="mb-4">
        <h2 className="text-lg font-semibold tracking-tight">Weekly regional brief</h2>
        <p className="mt-1 text-xs text-muted-foreground">
          Evidence-backed summary. Unverified feedback — not a determination of fact.
        </p>
      </div>

      {err && (
        <div className="space-y-3">
          <div className="rounded-xl border border-[var(--status-medium)]/30 bg-[color-mix(in_oklch,var(--status-medium),transparent_94%)] p-4 text-sm">
            Brief endpoint returned: {err}
          </div>
          {raw && (
            <div className="rounded-xl border border-border bg-card p-4">
              <div className="mb-2 text-xs font-medium uppercase tracking-wide text-muted-foreground">
                Raw /api/v1/briefs/weekly (first 2000 chars)
              </div>
              <pre className="overflow-auto text-[11px] leading-relaxed">{raw}</pre>
            </div>
          )}
        </div>
      )}

      {data && (
        <div className="space-y-5">
          <div className="flex flex-wrap gap-x-4 gap-y-1 text-xs text-muted-foreground">
            {data.region_id && <span>Region {data.region_id}</span>}
            {data.generated_at && <span>Generated {data.generated_at}</span>}
            {data.period && (
              <span>
                Period {data.period.from} to {data.period.to}
              </span>
            )}
          </div>

          {data.executive_summary && (
            <section className="rounded-xl border border-border bg-card p-4">
              <h3 className="mb-2 text-sm font-semibold tracking-tight">Executive summary</h3>
              <p className="text-sm leading-relaxed text-muted-foreground">{data.executive_summary}</p>
            </section>
          )}

          {data.top_issues && data.top_issues.length > 0 && (
            <section>
              <h3 className="mb-2 text-sm font-semibold tracking-tight">Top issues</h3>
              <ul className="divide-y divide-border rounded-xl border border-border bg-card">
                {data.top_issues.map((t) => (
                  <li key={t.category} className="flex items-center justify-between px-4 py-3">
                    <span className="text-sm">{t.category.split("_").join(" ")}</span>
                    <span className="text-xs text-muted-foreground">{t.count}</span>
                  </li>
                ))}
              </ul>
            </section>
          )}

          {data.mandatory_risk && data.mandatory_risk.length > 0 && (
            <section>
              <h3 className="mb-2 text-sm font-semibold tracking-tight text-[var(--status-critical)]">
                Mandatory-risk section
              </h3>
              <ul className="divide-y divide-border rounded-xl border border-[var(--status-critical)]/30 bg-card">
                {data.mandatory_risk.map((m) => (
                  <li key={m.category} className="flex items-center justify-between px-4 py-3">
                    <span className="text-sm">{m.category.split("_").join(" ")}</span>
                    <span className="text-xs text-muted-foreground">{m.count}</span>
                  </li>
                ))}
              </ul>
            </section>
          )}
        </div>
      )}
    </AppShell>
  );
}
