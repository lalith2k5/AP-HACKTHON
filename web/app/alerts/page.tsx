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
  status?: string;
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
  const [busyId, setBusyId] = useState<string | null>(null);
  const [flash, setFlash] = useState<string | null>(null);
  const [overrideId, setOverrideId] = useState<string | null>(null);

  async function load() {
    try {
      const data = (await endpoints.alerts({ limit: "100" })) as Alert[];
      setItems(data);
    } catch (e) {
      setErr((e as ApiError).message);
    }
  }

  useEffect(() => { load(); }, []);

  function notify(msg: string) {
    setFlash(msg);
    setTimeout(() => setFlash(null), 2500);
  }

  async function doAction(id: string, label: string, fn: () => Promise<unknown>) {
    setBusyId(id);
    try {
      await fn();
      await load();
      notify(label);
    } catch (e) {
      setErr((e as ApiError).message);
    } finally {
      setBusyId(null);
    }
  }

  async function submitOverride(reason: string) {
    if (!overrideId || !reason.trim()) return;
    const id = overrideId;
    setOverrideId(null);
    await doAction(id, "Alert overridden", () =>
      endpoints.overrideAlert(id, { actor: "demo-operator", note: reason, decision: "suppressed" })
    );
  }

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

      {flash && (
        <div className="mb-4 rounded-lg border border-[var(--status-ok)]/30 bg-[color-mix(in_oklch,var(--status-ok),transparent_92%)] px-3 py-2 text-xs text-[var(--status-ok)]">
          {flash}
        </div>
      )}

      {err && (
        <div className="mb-4 rounded-xl border border-[var(--status-critical)]/30 bg-[color-mix(in_oklch,var(--status-critical),transparent_94%)] p-4 text-sm text-[var(--status-critical)]">
          {err}
        </div>
      )}

      {filtered && (
        <ul className="space-y-2">
          {filtered.map((a) => {
            const busy = busyId === a.alert_id;
            const status = a.status ?? "open";
            return (
              <li key={a.alert_id} className="rounded-xl border border-border bg-card p-4">
                <div className="flex items-start justify-between gap-4">
                  <div className="min-w-0 flex-1">
                    <div className="flex flex-wrap items-center gap-2">
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
                      <span className="rounded bg-muted px-1.5 py-0.5 text-[10px] font-medium uppercase text-muted-foreground">
                        {status}
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
                  <div className="flex shrink-0 flex-col gap-1.5">
                    <Link
                      href={"/incidents/" + a.incident_id}
                      className="rounded-lg border border-border px-2.5 py-1 text-center text-xs font-medium hover:bg-muted"
                    >
                      Open
                    </Link>
                    {status === "open" && (
                      <button
                        disabled={busy}
                        onClick={() => doAction(a.alert_id, "Alert acknowledged", () =>
                          endpoints.ackAlert(a.alert_id, { actor: "demo-operator" })
                        )}
                        className="rounded-lg border border-border px-2.5 py-1 text-xs font-medium hover:bg-muted disabled:opacity-50"
                      >
                        Ack
                      </button>
                    )}
                    {(status === "open" || status === "acknowledged") && (
                      <>
                        <button
                          disabled={busy}
                          onClick={() => doAction(a.alert_id, "Alert resolved", () =>
                            endpoints.resolveAlert(a.alert_id, { actor: "demo-operator" })
                          )}
                          className="rounded-lg border border-border px-2.5 py-1 text-xs font-medium hover:bg-muted disabled:opacity-50"
                        >
                          Resolve
                        </button>
                        <button
                          disabled={busy}
                          onClick={() => setOverrideId(a.alert_id)}
                          className="rounded-lg border border-border px-2.5 py-1 text-xs font-medium text-[var(--status-medium)] hover:bg-muted disabled:opacity-50"
                        >
                          Override
                        </button>
                      </>
                    )}
                  </div>
                </div>
              </li>
            );
          })}
        </ul>
      )}

      {overrideId && (
        <OverrideModal
          onCancel={() => setOverrideId(null)}
          onSubmit={submitOverride}
        />
      )}
    </AppShell>
  );
}

function OverrideModal({
  onCancel,
  onSubmit,
}: {
  onCancel: () => void;
  onSubmit: (reason: string) => void;
}) {
  const [reason, setReason] = useState("");
  return (
    <div
      role="dialog"
      aria-modal="true"
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm"
      onClick={onCancel}
    >
      <div
        className="w-full max-w-md rounded-2xl border border-border bg-card p-5 shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        <h3 className="text-base font-semibold tracking-tight">Override alert</h3>
        <p className="mt-1 text-xs text-muted-foreground">
          Overriding suppresses this alert. A written reason is required and will be
          stored in the audit log.
        </p>
        <textarea
          autoFocus
          value={reason}
          onChange={(e) => setReason(e.target.value)}
          rows={3}
          placeholder="Why is this alert being overridden?"
          className="mt-3 w-full rounded-lg border border-border bg-background px-3 py-2 text-sm"
        />
        <div className="mt-4 flex justify-end gap-2">
          <button
            onClick={onCancel}
            className="rounded-lg border border-border px-3 py-1.5 text-sm hover:bg-muted"
          >
            Cancel
          </button>
          <button
            disabled={!reason.trim()}
            onClick={() => onSubmit(reason)}
            className="rounded-lg bg-primary px-3 py-1.5 text-sm font-medium text-primary-foreground disabled:opacity-50"
          >
            Override
          </button>
        </div>
      </div>
    </div>
  );
}
