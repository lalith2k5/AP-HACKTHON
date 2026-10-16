"use client";

import { useEffect, useState, useCallback } from "react";
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
  status?: string;
  priority?: string;
  first_seen: string;
  last_seen: string;
  record_count: number;
  channels: string;
  sample_text: string;
  verification_status: string;
  evidence?: string[];
  notes?: { ts: string; actor: string; note: string }[];
  escalation_rule?: string | null;
  next_action?: string | null;
  sla_hours?: number | null;
};

type TimelineEvent = {
  ts: string;
  kind: string;
  label: string;
  actor?: string;
  reason?: string;
};

const TABS = ["Overview", "Evidence", "Timeline", "Actions"] as const;
type Tab = (typeof TABS)[number];

const SEV_COLOR: Record<string, string> = {
  critical: "var(--status-critical)",
  high: "var(--status-high)",
  medium: "var(--status-medium)",
  low: "var(--status-low)",
};

const STATUSES = ["new", "triaged", "assigned", "in_progress", "resolved", "verified_closed", "reopened", "needs_review"];
const OWNERS = ["Store Ops", "Supply Chain", "Merchandising", "HR", "Risk", "Food Safety", "Digital", "Maintenance", "Finance"];

export default function IncidentDetailClient() {
  const params = useParams();
  const id = (params && (params.id as string)) || "";
  const [data, setData] = useState<Incident | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [tab, setTab] = useState<Tab>("Overview");
  const [flash, setFlash] = useState<string | null>(null);

  const reload = useCallback(async () => {
    try {
      const d = (await endpoints.incident(id)) as Incident;
      setData(d);
    } catch (e) {
      setErr((e as ApiError).message);
    }
  }, [id]);

  useEffect(() => {
    if (!id) return;
    reload();
  }, [id, reload]);

  function notify(msg: string) {
    setFlash(msg);
    setTimeout(() => setFlash(null), 2500);
  }

  return (
    <AppShell active="/incidents" title={"Incident " + id}>
      <Link href="/incidents" className="mb-4 inline-block text-xs text-muted-foreground hover:text-foreground">
        ← All incidents
      </Link>

      {flash && (
        <div className="mb-4 rounded-lg border border-[var(--status-ok)]/30 bg-[color-mix(in_oklch,var(--status-ok),transparent_92%)] px-3 py-2 text-xs text-[var(--status-ok)]">
          {flash}
        </div>
      )}

      {err && (
        <div className="rounded-3xl border border-[var(--status-critical)]/30 bg-[color-mix(in_oklch,var(--status-critical),transparent_94%)] p-4 text-sm text-[var(--status-critical)]">
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
              <span className="rounded bg-muted px-1.5 py-0.5 font-medium uppercase">
                {data.status ?? "new"}
              </span>
              <span className="rounded bg-muted px-1.5 py-0.5">{data.verification_status}</span>
            </div>
          </header>

          {(data.escalation_rule || data.next_action) && (
            <div className="mb-5 card-soft p-5">
              <div className="grid gap-3 sm:grid-cols-3">
                <div>
                  <div className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
                    Escalation rule
                  </div>
                  <div className="mt-1 text-sm font-medium">
                    {data.escalation_rule
                      ? data.escalation_rule.split(":").join(" \u00b7 ")
                      : "\u2014"}
                  </div>
                  {data.escalation_rule?.startsWith("mandatory_policy") && (
                    <div className="mt-1 text-xs font-medium" style={{ color: "var(--status-critical)" }}>
                      Mandatory \u2014 bypasses trend volume
                    </div>
                  )}
                </div>
                <div className="sm:col-span-2">
                  <div className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
                    Next action
                  </div>
                  <div className="mt-1 text-sm">{data.next_action ?? "\u2014"}</div>
                </div>
              </div>
              {data.sla_hours != null && (
                <div className="mt-3 text-xs text-muted-foreground">
                  SLA: {data.sla_hours}h from first seen
                </div>
              )}
            </div>
          )}

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
          {tab === "Timeline" && <TabTimeline id={id} />}
          {tab === "Actions" && <TabActions id={id} d={data} onDone={reload} notify={notify} />}
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
    ["Status", d.status ?? "new"],
    ["Verification", d.verification_status],
    ["Channels", d.channels.split("|").join(", ")],
    ["First seen", d.first_seen],
    ["Last seen", d.last_seen],
  ];
  return (
    <dl className="grid gap-3 sm:grid-cols-2">
      {rows.map(([k, v]) => (
        <div key={k} className="card-soft p-4">
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
    <div className="space-y-6">
      <div className="card-soft p-5">
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

function TabTimeline({ id }: { id: string }) {
  const [events, setEvents] = useState<TimelineEvent[] | null>(null);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    (async () => {
      try {
        const d = (await endpoints.timeline(id)) as { events: TimelineEvent[] };
        setEvents(d.events);
      } catch (e) {
        setErr((e as ApiError).message);
      }
    })();
  }, [id]);

  if (err) return <EmptyCard label={err} />;
  if (!events) return <div className="text-sm text-muted-foreground">Loading timeline…</div>;
  if (events.length === 0) return <EmptyCard label="No timeline events" />;

  const KIND_COLOR: Record<string, string> = {
    first_seen: "var(--status-info)",
    last_seen: "var(--status-high)",
    override: "var(--status-medium)",
    note: "var(--status-ok)",
  };

  return (
    <ol className="relative space-y-4 border-l border-border pl-5">
      {events.map((e, i) => (
        <li key={i}>
          <div
            className="absolute -left-1.5 size-3 rounded-full"
            style={{ background: KIND_COLOR[e.kind] ?? "var(--muted-foreground)" }}
          />
          <div className="text-xs uppercase tracking-wide text-muted-foreground">
            {e.kind} · {e.ts}
          </div>
          <div className="mt-0.5 text-sm">{e.label}</div>
          {(e.actor || e.reason) && (
            <div className="mt-1 text-xs text-muted-foreground">
              {e.actor ? <span>by {e.actor}</span> : null}
              {e.reason ? <span> · {e.reason}</span> : null}
            </div>
          )}
        </li>
      ))}
    </ol>
  );
}

function TabActions({
  id,
  d,
  onDone,
  notify,
}: {
  id: string;
  d: Incident;
  onDone: () => Promise<void>;
  notify: (msg: string) => void;
}) {
  const [busy, setBusy] = useState(false);
  const [note, setNote] = useState("");
  const [owner, setOwner] = useState(d.owner_function);
  const [status, setStatus] = useState(d.status ?? "new");
  const [error, setError] = useState<string | null>(null);

  async function run(label: string, fn: () => Promise<unknown>) {
    setBusy(true);
    setError(null);
    try {
      await fn();
      await onDone();
      notify(label);
    } catch (e) {
      setError((e as ApiError).message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="space-y-6">
      {error && (
        <div className="rounded-2xl border border-[var(--status-critical)]/30 bg-[color-mix(in_oklch,var(--status-critical),transparent_94%)] p-3 text-xs text-[var(--status-critical)]">
          {error}
        </div>
      )}

      <div className="card-soft p-5">
        <h3 className="mb-3 text-sm font-semibold tracking-tight">Assign owner & status</h3>
        <div className="grid gap-3 sm:grid-cols-2">
          <label className="block">
            <span className="mb-1 block text-xs font-medium uppercase tracking-wide text-muted-foreground">Owner</span>
            <select
              value={owner}
              onChange={(e) => setOwner(e.target.value)}
              disabled={busy}
              className="w-full rounded-2xl border border-[var(--border)] bg-[var(--card)] px-4 py-3 text-sm"
            >
              {OWNERS.map((o) => <option key={o}>{o}</option>)}
            </select>
          </label>
          <label className="block">
            <span className="mb-1 block text-xs font-medium uppercase tracking-wide text-muted-foreground">Status</span>
            <select
              value={status}
              onChange={(e) => setStatus(e.target.value)}
              disabled={busy}
              className="w-full rounded-2xl border border-[var(--border)] bg-[var(--card)] px-4 py-3 text-sm"
            >
              {STATUSES.map((s) => <option key={s}>{s}</option>)}
            </select>
          </label>
        </div>
        <div className="mt-3 flex gap-2">
          <button
            disabled={busy}
            onClick={() => run("Incident updated", () =>
              endpoints.patchIncident(id, { actor: "demo-operator", owner_function: owner, status })
            )}
            className="rounded-2xl bg-primary px-3 py-1.5 text-sm font-medium text-primary-foreground disabled:opacity-50"
          >
            {busy ? "Saving…" : "Save changes"}
          </button>
          <button
            disabled={busy}
            onClick={() => run("Incident resolved", () =>
              endpoints.patchIncident(id, { actor: "demo-operator", status: "resolved", reason: "Resolved via UI" })
            )}
            className="rounded-2xl border border-border px-3 py-1.5 text-sm hover:bg-muted disabled:opacity-50"
          >
            Mark resolved
          </button>
        </div>
      </div>

      <div className="card-soft p-5">
        <h3 className="mb-3 text-sm font-semibold tracking-tight">Add note</h3>
        <textarea
          value={note}
          onChange={(e) => setNote(e.target.value)}
          disabled={busy}
          rows={3}
          placeholder="Investigation update, action taken, follow-up…"
          className="w-full rounded-2xl border border-[var(--border)] bg-[var(--card)] px-4 py-3 text-sm"
        />
        <button
          disabled={busy || !note.trim()}
          onClick={() => run("Note added", async () => {
            await endpoints.addNote(id, { actor: "demo-operator", note });
            setNote("");
          })}
          className="mt-3 rounded-lg bg-primary px-3 py-1.5 text-sm font-medium text-primary-foreground disabled:opacity-50"
        >
          {busy ? "Saving…" : "Add note"}
        </button>
      </div>

      {d.notes && d.notes.length > 0 && (
        <div className="card-soft p-5">
          <h3 className="mb-3 text-sm font-semibold tracking-tight">Notes ({d.notes.length})</h3>
          <ul className="space-y-2">
            {d.notes.map((n, i) => (
              <li key={i} className="border-l-2 border-border pl-3">
                <div className="text-xs text-muted-foreground">{n.ts} · {n.actor}</div>
                <div className="text-sm">{n.note}</div>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

function EmptyCard({ label }: { label: string }) {
  return (
    <div className="rounded-3xl border border-dashed border-border bg-muted/20 p-6 text-center text-sm text-muted-foreground">
      {label}
    </div>
  );
}
