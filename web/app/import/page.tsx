"use client";

import { useEffect, useRef, useState } from "react";
import { AppShell } from "@/components/app-shell";
import { endpoints } from "@/lib/api";

type Step = "upload" | "map" | "validate" | "commit" | "done";

export default function ImportPage() {
  const fileRef = useRef<HTMLInputElement>(null);
  const [step, setStep] = useState<Step>("upload");
  const [upload, setUpload] = useState<any>(null);
  const [preview, setPreview] = useState<any>(null);
  const [mapping, setMapping] = useState<Record<string, string>>({});
  const [validation, setValidation] = useState<any>(null);
  const [batchId, setBatchId] = useState<string | null>(null);
  const [batches, setBatches] = useState<any[]>([]);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    endpoints.importBatches().then((d: any) => setBatches(d.batches ?? [])).catch(() => {});
  }, [batchId]);

  async function onFile(file: File) {
    setErr(null); setBusy(true);
    try {
      const up: any = await endpoints.importUpload(file);
      setUpload(up);
      const pv: any = await endpoints.importPreview(up.upload_id);
      setPreview(pv);
      setMapping(pv.suggested_mapping ?? {});
      setStep("map");
    } catch (e: any) { setErr(String(e?.message ?? e)); }
    finally { setBusy(false); }
  }

  async function onValidate() {
    setErr(null); setBusy(true);
    try {
      const v: any = await endpoints.importValidate({
        columns: preview?.columns ?? [],
        mapping,
      });
      setValidation(v);
      setStep("validate");
    } catch (e: any) { setErr(String(e?.message ?? e)); }
    finally { setBusy(false); }
  }

  async function onCommit() {
    setErr(null); setBusy(true);
    try {
      const r: any = await endpoints.importCommit({
        upload_id: upload.upload_id,
        mapping,
      });
      setBatchId(r.batch_id);
      setStep("done");
    } catch (e: any) { setErr(String(e?.message ?? e)); }
    finally { setBusy(false); }
  }

  function reset() {
    setStep("upload"); setUpload(null); setPreview(null);
    setMapping({}); setValidation(null); setBatchId(null); setErr(null);
    if (fileRef.current) fileRef.current.value = "";
  }

  const stepNum = { upload: 1, map: 2, validate: 3, commit: 4, done: 4 }[step];

  return (
    <AppShell active="/import" title="Import data">
      <div className="page-head">
        <div>
          <h2 className="page-head-title">Import data</h2>
          <p>CSV, JSONL, or Parquet. Column mapping is required for CSV and JSONL.</p>
        </div>
      </div>

      {/* Stepper */}
      <div className="card" style={{ marginBottom: 20, padding: "12px 20px" }}>
        <div className="row" style={{ gap: 20 }}>
          {["Upload", "Map", "Validate", "Commit"].map((label, i) => {
            const n = i + 1;
            const active = n === stepNum;
            const done = n < stepNum;
            return (
              <div key={label} className="row" style={{ gap: 8 }}>
                <span
                  style={{
                    display: "inline-flex", alignItems: "center", justifyContent: "center",
                    width: 22, height: 22, borderRadius: "50%",
                    background: done ? "var(--st-ok)" : active ? "var(--accent)" : "var(--bg-inset)",
                    color: done || active ? "#fff" : "var(--fg-2)",
                    fontSize: 11, fontWeight: 700,
                  }}
                >
                  {done ? "✓" : n}
                </span>
                <span style={{ fontSize: 13, fontWeight: active ? 600 : 500, color: active ? "var(--fg)" : "var(--fg-2)" }}>
                  {label}
                </span>
                {n < 4 && <span style={{ color: "var(--fg-3)" }}>—</span>}
              </div>
            );
          })}
        </div>
      </div>

      {err && (
        <div className="card" style={{ marginBottom: 20, borderColor: "var(--st-critical)", color: "var(--st-critical)" }}>
          {err}
        </div>
      )}

      {step === "upload" && (
        <div className="card" style={{ padding: 40, textAlign: "center" }}>
          <input
            ref={fileRef}
            type="file"
            accept=".csv,.jsonl,.ndjson,.parquet,.pq"
            onChange={(e) => e.target.files?.[0] && onFile(e.target.files[0])}
            style={{ display: "none" }}
          />
          <div style={{ fontSize: 44, color: "var(--fg-3)" }}>⇧</div>
          <h3 className="t-heading" style={{ marginTop: 12 }}>Drop a file or choose one</h3>
          <p className="t-caption" style={{ marginTop: 6 }}>CSV · JSONL · Parquet · max 100MB</p>
          <button
            className="btn btn-primary"
            style={{ marginTop: 20 }}
            disabled={busy}
            onClick={() => fileRef.current?.click()}
          >
            {busy ? "Uploading…" : "Choose file"}
          </button>
        </div>
      )}

      {step === "map" && preview && (
        <div className="card" style={{ padding: 0 }}>
          <div className="row-between" style={{ padding: "16px 20px", borderBottom: "1px solid var(--line-soft)" }}>
            <div>
              <div className="t-heading">Map columns</div>
              <div className="t-caption">{upload?.filename} · {preview.format} · {preview.columns.length} columns</div>
            </div>
            <button className="btn btn-ghost btn-sm" onClick={reset}>Change file</button>
          </div>
          <div style={{ padding: 20 }}>
            <table className="table">
              <thead>
                <tr><th>Source column</th><th>Canonical field</th></tr>
              </thead>
              <tbody>
                {preview.columns.map((col: string) => (
                  <tr key={col}>
                    <td className="mono">{col}</td>
                    <td>
                      <select
                        className="select"
                        value={Object.entries(mapping).find(([, v]) => v === col)?.[0] ?? ""}
                        onChange={(e) => {
                          const next = { ...mapping };
                          for (const k of Object.keys(next)) if (next[k] === col) delete next[k];
                          if (e.target.value) next[e.target.value] = col;
                          setMapping(next);
                        }}
                      >
                        <option value="">— skip —</option>
                        {["record_id","channel","store_id","timestamp","text_raw","rating","language_hint","source_reference"].map((k) => (
                          <option key={k} value={k}>{k}</option>
                        ))}
                      </select>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            <div className="row" style={{ marginTop: 20, justifyContent: "flex-end" }}>
              <button className="btn btn-primary" onClick={onValidate} disabled={busy}>
                {busy ? "Validating…" : "Validate mapping →"}
              </button>
            </div>
          </div>
        </div>
      )}

      {step === "validate" && validation && (
        <div className="card" style={{ padding: 24 }}>
          <div className="t-heading" style={{ fontSize: 18 }}>{validation.ok ? "Ready to import" : "Fix the issues below"}</div>
          <div style={{ marginTop: 16 }} className="stack-sm">
            <div className="row-between">
              <span className="t-caption">Required columns present</span>
              <span className={validation.missing_required.length === 0 ? "pill pill-ok" : "pill pill-critical"}>
                {validation.missing_required.length === 0 ? "All present" : `${validation.missing_required.length} missing`}
              </span>
            </div>
            {validation.missing_required.length > 0 && (
              <div className="t-caption" style={{ color: "var(--st-critical)" }}>
                Missing: {validation.missing_required.join(", ")}
              </div>
            )}
            {validation.errors.length > 0 && (
              <ul className="t-caption" style={{ color: "var(--st-critical)", paddingLeft: 18 }}>
                {validation.errors.map((e: string, i: number) => <li key={i}>{e}</li>)}
              </ul>
            )}
          </div>
          <div className="row" style={{ marginTop: 24, justifyContent: "flex-end", gap: 8 }}>
            <button className="btn btn-secondary" onClick={() => setStep("map")}>Back</button>
            <button className="btn btn-primary" onClick={onCommit} disabled={!validation.ok || busy}>
              {busy ? "Committing…" : "Commit import"}
            </button>
          </div>
        </div>
      )}

      {step === "done" && (
        <div className="card" style={{ padding: 28, textAlign: "center" }}>
          <div style={{ fontSize: 40, color: "var(--st-ok)" }}>✓</div>
          <div className="t-heading" style={{ marginTop: 12, fontSize: 18 }}>Import committed</div>
          <div className="t-caption" style={{ marginTop: 6 }}>Batch {batchId}</div>
          <div className="row" style={{ marginTop: 20, justifyContent: "center", gap: 8 }}>
            <button className="btn btn-secondary" onClick={reset}>Import another</button>
            <button className="btn btn-primary" onClick={() => location.assign("/data-health")}>
              Run pipeline →
            </button>
          </div>
        </div>
      )}

      {/* Batch history */}
      {batches.length > 0 && (
        <section style={{ marginTop: 32 }}>
          <h2 className="t-heading" style={{ marginBottom: 12 }}>Import history</h2>
          <div className="card card-flat">
            <table className="table">
              <thead>
                <tr><th>Batch</th><th>Rows</th><th>Channel</th><th>When</th></tr>
              </thead>
              <tbody>
                {batches.slice(-8).reverse().map((b: any, i: number) => (
                  <tr key={i}>
                    <td className="mono">{b.batch_id ?? b.id ?? "—"}</td>
                    <td>{b.rows ?? b.row_count ?? "—"}</td>
                    <td>{b.channel ?? "—"}</td>
                    <td className="tiny muted">{b.ts ?? b.created_at ?? "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      )}
    </AppShell>
  );
}
