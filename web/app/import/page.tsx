"use client";
import { useState } from "react";
import { AppShell } from "@/components/app-shell";
import { endpoints } from "@/lib/api";

export default function ImportPage() {
  const [path, setPath] = useState("data/raw/sample.csv");
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [err, setErr] = useState<string | null>(null);

  async function submit() {
    setBusy(true); setErr(null); setResult(null);
    try {
      const r = await endpoints.ingest({ path, mapping: {} });
      setResult(r);
    } catch (e) { setErr(String(e)); }
    finally { setBusy(false); }
  }

  return (
    <AppShell active="/import" title="Import data">
      <div className="max-w-2xl space-y-4">
        <div className="card-soft p-6">
          <label htmlFor="import-source-path" className="text-sm font-medium">Source file (server path)</label>
          <input id="import-source-path" value={path} onChange={(e) => setPath(e.target.value)}
            className="mt-2 w-full rounded-2xl border border-[var(--border)] bg-[var(--card)] px-4 py-3 text-sm font-mono" />
          <p className="mt-2 text-xs text-muted-foreground">
            CSV / JSONL / Parquet. Column mapping defaults will be applied if omitted.
          </p>
          <button onClick={submit} disabled={busy}
            className="mt-4 rounded-lg bg-[var(--primary)] px-4 py-2 text-sm font-medium text-white disabled:opacity-50">
            {busy ? "Importing..." : "Start import"}
          </button>
        </div>
        {err && <div className="rounded-2xl border border-red-300 bg-red-50 px-4 py-3 text-sm text-red-700">{err}</div>}
        {result && (
          <div className="card-soft p-6">
            <p className="text-sm">Job accepted: <span className="font-mono">{result.import_id}</span></p>
            <p className="mt-1 text-xs text-muted-foreground">Poll status below.</p>
            <Poll id={result.import_id} />
          </div>
        )}
      </div>
    </AppShell>
  );
}

function Poll({ id }: { id: string }) {
  const [job, setJob] = useState<any>(null);
  useState(() => {});
  // naive poll via setInterval
  if (typeof window !== "undefined") {
    setTimeout(async () => {
      try { setJob(await endpoints.ingestStatus(id)); } catch {}
    }, 600);
  }
  if (!job) return <p className="mt-3 text-xs text-muted-foreground">Polling...</p>;
  return (
    <pre className="mt-3 overflow-auto rounded-lg bg-muted/40 p-3 text-[11px]">{JSON.stringify(job, null, 2)}</pre>
  );
}
