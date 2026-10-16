"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
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
  evidence?: string[];
};

const TABS = ["Overview", "Evidence", "Timeline", "Actions"] as const;
type Tab = (typeof TABS)[number];

const SEV_COLOR: Record<string, string> = {
  critical: "var(--status-critical)",
  high: "var(--status-high)",
  medium: "var(--status-medium)",
  low: "var(--status-low)",
};

export default function IncidentDetailClient() {
  const params = useParams();
  const id = (params && (params.id as string)) || "";
  const [data, setData] = useState<Incident | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [tab, setTab] = useState<Tab>("Overview");

  useEffect(() => {
    if (!id) return;
    (async () => {
      try {
        const d = (await endpoints.incident(id)) as Incident;
        setData(d);
      } catch (e) {
        setErr((e as ApiError).message);
      }
    })();
  }, [id]);

  return (
    <AppShell active="/incidents" title={"Incident " + id}>
      <Link href="/incidents" className="mb-4 inline-block text-xs text-muted-foreground hover:text-foreground">
        ← All incidents
      </Link>

      {err && (
        <div className="rounded-xl border border-[var(--status-critical)]/30 bg-[color-mix(in_oklch,var(--status-critical),transparent_94%)] p-4 text-sm text-[var(--status-critical)]">
          {err}
        </div>
      )}

      {data && (
        <>
          <header className="mb-5">
            <h2 className="text-xl font-semibold tracking-tight">
              {data.predicted_category.split("_").join(" ")}
            </h2>
            <div className="mt-1 flex flex-wrap gap-x-4 gap-y-1 text-xs text-muted-foreground">
              <span>Store {data.store_id}</span>
              <span>Owner {data.owner_function}</span>
              <span>{data.record_count} records</span>
              <span className="font-medium uppercase" style={{ color: SEV_COLOR[data.severity] }}>
                {data.severity}
              </span>
              <span className="rounded bg-muted px-1.5 py-0.5">{data.verification_status}</span>
            </div>
          </header>

          <div role="tablist" className="mb-4 flex gap-1 border-b border-border">
            {TABS.map((t) => (
              <button
                key={t}
                role="tab"
                aria-selected={tab === t}
                onClick={() => setTab(t)}
                className={
                  "relative -mb-px border-b-2 px-3 py-2 text-sm font-medium transition-colors " +
                  (tab === t
                    ? "border-[var(--primary)] text-foreground"
                    : "border-transparent text-muted-foreground hover:text-foreground")
                }
              >
                {t}
              </button>
            ))}
          </div>

          {tab === "Overview" && <TabOverview d={data} />}
          {tab === "Evidence" && <TabEvidence d={data} />}
          {tab === "Timeline" && <TabTimeline d={data} />}
          {tab === "Actions" && <TabActions />}
        </>
      )}
    </AppShell>
  );
}

function TabOverview({ d }: { d: Incident }) {
  const rows: [string, string][] = [
    ["Category", d.predicted_category.split("_").join(" ")],
    ["Store", d.store_id],
    ["Owner", d.owner_function],
    ["Severity", d.severity],
    ["Verification", d.verification_status],
    ["Channels", d.channels.split("|").join(", ")],
    ["First seen", d.first_seen],
    ["Last seen", d.last_seen],
  ];
  return (
    <dl className="grid gap-3 sm:grid-cols-2">
      {rows.map(([k, v]) => (
        <div key={k} className="rounded-lg border border-border bg-card p-3">
          <dt className="text-xs font-medium uppercase tracking-wide text-muted-foreground">{k}</dt>
          <dd className="mt-1 text-sm">{v}</dd>
        </div>
      ))}
    </dl>
  );
}

function TabEvidence({ d }: { d: Incident }) {
  if (!d.evidence || d.evidence.length === 0) {
    return <EmptyCard label="No evidence IDs attached" />;
  }
  return (
    <div className="space-y-4">
      <div className="rounded-xl border border-border bg-card p-4">
        <div className="text-xs font-medium uppercase tracking-wide text-muted-foreground">Sample</div>
        <p className="mt-2 text-sm italic">&ldquo;{d.sample_text}&rdquo;</p>
      </div>
      <div>
        <div className="mb-2 text-xs font-medium uppercase tracking-wide text-muted-foreground">
          Source record IDs ({d.evidence.length})
        </div>
        <ul className="grid gap-1 sm:grid-cols-2 lg:grid-cols-3">
          {d.evidence.map((rid) => (
            <li key={rid} className="rounded bg-muted px-2 py-1 font-mono text-[11px]">{rid}</li>
          ))}
        </ul>
      </div>
    </div>
  );
}

function TabTimeline({ d }: { d: Incident }) {
  return (
    <ol className="relative space-y-4 border-l border-border pl-5">
      <li>
        <div className="absolute -left-1.5 size-3 rounded-full bg-[var(--status-info)]" />
        <div className="text-xs text-muted-foreground">First seen</div>
        <div className="text-sm font-medium">{d.first_seen}</div>
      </li>
      <li>
        <div className="absolute -left-1.5 size-3 rounded-full bg-[var(--status-high)]" />
        <div className="text-xs text-muted-foreground">Last seen</div>
        <div className="text-sm font-medium">{d.last_seen}</div>
      </li>
      <li className="text-xs text-muted-foreground">
        Full transition history requires a backend audit endpoint — not implemented yet.
      </li>
    </ol>
  );
}

function TabActions() {
  return (
    <div className="space-y-3">
      <div className="rounded-xl border border-dashed border-border bg-muted/20 p-4 text-sm text-muted-foreground">
        Action mutations require backend endpoints that do not exist yet:
        <ul className="mt-2 ml-4 list-disc space-y-0.5 text-xs">
          <li><code className="font-mono">PATCH /api/v1/incidents/{"{id}"}</code></li>
          <li><code className="font-mono">POST /api/v1/incidents/{"{id}"}/notes</code></li>
        </ul>
        Both are in spec section 14.2 but not implemented. Tab shell ready; buttons ship once endpoints land.
      </div>
      <div className="flex gap-2">
        <button disabled className="cursor-not-allowed rounded-lg bg-primary px-3 py-1.5 text-sm text-primary-foreground opacity-40">
          Assign owner
        </button>
        <button disabled className="cursor-not-allowed rounded-lg border border-border px-3 py-1.5 text-sm opacity-40">
          Add note
        </button>
        <button disabled className="cursor-not-allowed rounded-lg border border-border px-3 py-1.5 text-sm opacity-40">
          Resolve
        </button>
      </div>
    </div>
  );
}

function EmptyCard({ label }: { label: string }) {
  return (
    <div className="rounded-xl border border-dashed border-border bg-muted/20 p-6 text-center text-sm text-muted-foreground">
      {label}
    </div>
  );
}
