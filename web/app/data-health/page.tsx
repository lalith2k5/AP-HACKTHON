"use client";
import { useEffect, useState } from "react";
import { AppShell } from "@/components/app-shell";
import { endpoints } from "@/lib/api";

export default function DataHealthPage() {
  const [metrics, setMetrics] = useState<any>(null);
  const [busy, setBusy] = useState<string | null>(null);
  const [job, setJob] = useState<any>(null);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => { endpoints.metrics().then(setMetrics).catch((e) => setErr(String(e))); }, []);

  async function runPipeline() {
    setBusy("pipeline"); setErr(null);
    try {
      const r: any = await endpoints.pipelineRun();
      const id = r.run_id;
      const poll = setInterval(async () => {
        try {
          const j: any = await endpoints.pipelineStatus(id);
          setJob(j);
          if (j.status === "succeeded" || j.status === "failed") clearInterval(poll);
        } catch {}
      }, 1500);
    } catch (e) { setErr(String(e)); setBusy(null); }
  }
  async function runEvaluation() {
    setBusy("evaluation"); setErr(null);
    try {
      const r: any = await endpoints.evaluationRun();
      const id = r.evaluation_run_id;
      const poll = setInterval(async () => {
        try {
          const j: any = await endpoints.evaluationStatus(id);
          setJob(j);
          if (j.status === "succeeded" || j.status === "failed") clearInterval(poll);
        } catch {}
      }, 1500);
    } catch (e) { setErr(String(e)); setBusy(null); }
  }
  async function resetDemo() {
    if (!confirm("Reset demo state? Overrides and notes will be cleared.")) return;
    setBusy("reset");
    try { await endpoints.demoReset(); window.location.reload(); }
    catch (e) { setErr(String(e)); setBusy(null); }
  }

  return (
    <AppShell active="/data-health" title="Data health">
      <div className="space-y-6">
        <div className="flex flex-wrap gap-2">
          <button onClick={runPipeline} disabled={!!busy}
            className="rounded-lg bg-[var(--primary)] px-3 py-2 text-sm font-medium text-white disabled:opacity-50">
            {busy === "pipeline" ? "Running..." : "Re-run pipeline"}
          </button>
          <button onClick={runEvaluation} disabled={!!busy}
            className="rounded-lg border border-border px-3 py-2 text-sm font-medium disabled:opacity-50">
            {busy === "evaluation" ? "Running..." : "Re-run evaluation"}
          </button>
          <button onClick={resetDemo} disabled={!!busy}
            className="rounded-lg border border-red-300 text-red-700 px-3 py-2 text-sm font-medium disabled:opacity-50">
            Reset demo state
          </button>
        </div>

        {err && <div className="rounded-lg border border-red-300 bg-red-50 px-4 py-3 text-sm text-red-700">{err}</div>}
        {job && (
          <div className="rounded-xl border border-border bg-card p-5">
            <h2 className="text-sm font-semibold">Job {job.job_id ?? job.evaluation_run_id}</h2>
            <p className="mt-1 text-xs text-muted-foreground">status: {job.status} · stage: {job.stage}</p>
            {job.error && <p className="mt-2 text-xs text-red-600">{job.error}</p>}
          </div>
        )}

        <div className="rounded-xl border border-border bg-card p-5">
          <h2 className="text-sm font-semibold">Current metrics</h2>
          <pre className="mt-3 overflow-auto rounded-lg bg-muted/40 p-3 text-[11px]">
            {metrics ? JSON.stringify(metrics, null, 2) : "Loading..."}
          </pre>
        </div>
      </div>
    </AppShell>
  );
}
