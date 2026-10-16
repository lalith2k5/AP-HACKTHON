"use client";

import { useEffect, useState } from "react";
import { AppShell } from "@/components/app-shell";
import { endpoints, ApiError } from "@/lib/api";

type Overview = {
  kpis?: { label: string; value: number | string; delta?: number }[];
  series?: { date: string; count: number }[];
  categories?: { category: string; count: number }[];
  urgent_queue?: { id: string; title: string; severity: string }[];
  freshness?: string;
};

type State =
  | { kind: "loading" }
  | { kind: "error"; message: string; status?: number }
  | { kind: "ok"; data: Overview };

export default function OverviewPage() {
  const [state, setState] = useState<State>({ kind: "loading" });

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const data = (await endpoints.overview()) as Overview;
        if (!cancelled) setState({ kind: "ok", data });
      } catch (e) {
        if (cancelled) return;
        const err = e as ApiError;
        setState({
          kind: "error",
          message: err.message ?? "Unknown error",
          status: err.status,
        });
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <AppShell active="/overview" title="Overview">
      {state.kind === "loading" && <LoadingState />}
      {state.kind === "error" && <ErrorState message={state.message} status={state.status} />}
      {state.kind === "ok" && <LoadedOverview data={state.data} />}
    </AppShell>
  );
}

function LoadingState() {
  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
      {Array.from({ length: 4 }).map((_, i) => (
        <div
          key={i}
          className="h-24 animate-pulse rounded-xl border border-border bg-muted/40"
        />
      ))}
    </div>
  );
}

function ErrorState({ message, status }: { message: string; status?: number }) {
  return (
    <div className="rounded-3xl border border-[var(--status-critical)]/30 bg-[color-mix(in_oklch,var(--status-critical),transparent_94%)] p-5">
      <div className="flex items-center gap-2 text-sm font-semibold text-[var(--status-critical)]">
        <span aria-hidden>●</span>
        Backend unreachable
        {status ? <span className="font-normal opacity-70">HTTP {status}</span> : null}
      </div>
      <p className="mt-2 text-sm text-muted-foreground">{message}</p>
      <p className="mt-3 text-xs text-muted-foreground">
        Start the API:{" "}
        <code className="rounded bg-muted px-1.5 py-0.5 font-mono text-[11px]">
          .venv/bin/uvicorn storesignal.api:app --port 8790
        </code>
      </p>
    </div>
  );
}

function LoadedOverview({ data }: { data: Overview }) {
  const kpis = data.kpis ?? [];
  return (
    <div className="space-y-10">
      <section>
        <div className="mb-3 flex items-baseline justify-between">
          <h2 className="text-[22px] font-semibold tracking-tight">Key metrics</h2>
          {data.freshness ? (
            <span className="text-xs text-muted-foreground">
              Last run: {data.freshness}
            </span>
          ) : null}
        </div>
        {kpis.length === 0 ? (
          <EmptyCard label="No KPI data returned" />
        ) : (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {kpis.map((k) => (
              <div key={k.label} className="glass p-5">
                <div className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
                  {k.label}
                </div>
                <div className="mt-2 text-2xl font-semibold tracking-tight">{k.value}</div>
              </div>
            ))}
          </div>
        )}
      </section>

      <section>
        <h2 className="mb-3 text-lg font-semibold tracking-tight">Urgent queue</h2>
        {!data.urgent_queue?.length ? (
          <EmptyCard label="No urgent items" />
        ) : (
          <ul className="divide-y divide-border glass">
            {data.urgent_queue.map((u) => (
              <li key={u.id} className="flex items-center justify-between px-4 py-3">
                <span className="text-sm">{u.title}</span>
                <span className="text-xs font-medium uppercase text-[var(--status-critical)]">
                  {u.severity}
                </span>
              </li>
            ))}
          </ul>
        )}
      </section>
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
