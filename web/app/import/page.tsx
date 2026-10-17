"use client";

import { useEffect, useRef, useState } from "react";
import { AppShell } from "@/components/app-shell";
import { endpoints } from "@/lib/api";

type Step = "upload" | "map" | "validate" | "commit" | "done";

const CANONICAL_FIELDS: { key: string; required: boolean; label: string }[] = [
  { key: "record_id",         required: true,  label: "record_id" },
  { key: "channel",           required: true,  label: "channel" },
  { key: "store_id",          required: true,  label: "store_id" },
  { key: "timestamp",         required: true,  label: "timestamp" },
  { key: "text_raw",          required: true,  label: "text_raw" },
  { key: "rating",            required: false, label: "rating" },
  { key: "language_hint",     required: false, label: "language_hint" },
  { key: "source_reference",  required: false, label: "source_reference" },
];

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
    if (!mappingOk) return;
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

  const usedSources = Object.values(mapping).filter(Boolean);
  const duplicateSource = usedSources.find(
    (s, i) => usedSources.indexOf(s) !== i
  );
  const missingRequired = CANONICAL_FIELDS.filter(
    (f) => f.required && !mapping[f.key]
  ).map((f) => f.key);
  const mappingOk = missingRequired.length === 0 && !duplicateSource;

  return (
    <AppShell active="/import" title="Import data">
      <div className="page-head">
        <div>
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
          <div
            className="row-between"
            style={{ padding: "16px 20px", borderBottom: "1px solid var(--line-soft)" }}
          >
            <div>
              <div className="t-heading">Map fields</div>
              <div className="t-caption">
                {upload?.filename} · {preview.format} · {preview.columns.length} source columns
                {" · "}
                {preview.columns.length - usedSources.length} unmapped
              </div>
            </div>
            <button className="btn btn-ghost btn-sm" onClick={reset}>
              Change file
            </button>
          </div>

          <div style={{ padding: 20 }}>
            <table className="table">
              <thead>
                <tr>
                  <th style={{ width: "38%" }}>Canonical field</th>
                  <th style={{ width: "50%" }}>Source column</th>
                  <th style={{ width: "12%", textAlign: "right" }}>Status</th>
                </tr>
              </thead>
              <tbody>
                {CANONICAL_FIELDS.map(({ key, required }) => {
                  const current = mapping[key] ?? "";
                  const isDup =
                    current &&
                    usedSources.filter((s) => s === current).length > 1;
                  const status = !current
                    ? required
                      ? "missing"
                      : "optional"
                    : isDup
                      ? "duplicate"
                      : "ok";
                  return (
                    <tr key={key}>
                      <td>
                        <span className="mono" style={{ fontWeight: 600 }}>
                          {key}
                        </span>
                        {required && (
                          <span
                            style={{ color: "var(--st-critical)", marginLeft: 6 }}
                            title="required"
                          >
                            *
                          </span>
                        )}
                      </td>
                      <td>
                        <select
                          className="select"
                          value={current}
                          onChange={(e) => {
                            const next = { ...mapping };
                            if (e.target.value) next[key] = e.target.value;
                            else delete next[key];
                            setMapping(next);
                          }}
                        >
                          <option value="">— not mapped —</option>
                          {preview.columns.map((col: string) => {
                            const takenBy = Object.entries(mapping).find(
                              ([k, v]) => v === col && k !== key
                            )?.[0];
                            return (
                              <option key={col} value={col}>
                                {col}
                                {takenBy ? `  ·  used by ${takenBy}` : ""}
                              </option>
                            );
                          })}
                        </select>
                      </td>
                      <td style={{ textAlign: "right" }}>
                        {status === "ok" && <span className="pill pill-ok">ok</span>}
                        {status === "missing" && (
                          <span className="pill pill-critical">missing</span>
                        )}
                        {status === "optional" && <span className="pill">optional</span>}
                        {status === "duplicate" && (
                          <span className="pill pill-high">dup</span>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>

            {duplicateSource && (
              <div
                className="card"
                style={{
                  marginTop: 16,
                  borderColor: "var(--st-high)",
                  color: "var(--st-high)",
                  fontSize: 13,
                }}
              >
                Source column <span className="mono">{duplicateSource}</span> is assigned
                to more than one canonical field. Each source column may feed only one
                canonical field.
              </div>
            )}

            {(() => {
              const used = new Set(usedSources);
              const dropped = (preview.columns as string[]).filter(
                (c) => !used.has(c)
              );
              if (dropped.length === 0) return null;
              return (
                <div
                  style={{
                    marginTop: 20,
                    padding: "14px 16px",
                    borderRadius: 10,
                    background:
                      "color-mix(in oklab, var(--fg) 3.5%, transparent)",
                    border: "1px solid var(--line-soft)",
                  }}
                >
                  <div
                    className="t-micro"
                    style={{ marginBottom: 8, marginTop: 0 }}
                  >
                    Unmapped source columns · {dropped.length} will be dropped
                  </div>
                  <div
                    style={{ display: "flex", flexWrap: "wrap", gap: 6 }}
                  >
                    {dropped.map((c) => (
                      <span
                        key={c}
                        className="pill mono"
                        style={{ fontSize: 11 }}
                      >
                        {c}
                      </span>
                    ))}
                  </div>
                  <div
                    className="t-caption"
                    style={{ marginTop: 8, color: "var(--fg-3)" }}
                  >
                    These columns have no canonical equivalent and will not be
                    imported. This is normal.
                  </div>
                </div>
              );
            })()}

            <div
              className="row"
              style={{ marginTop: 24, justifyContent: "space-between" }}
            >
              <button
                className="btn btn-ghost btn-sm"
                onClick={() => setMapping(preview.suggested_mapping ?? {})}
              >
                Reset to auto-mapping
              </button>
              <button
                className="btn btn-primary"
                onClick={onValidate}
                disabled={busy || !mappingOk}
                title={
                  !mappingOk
                    ? missingRequired.length
                      ? `Missing: ${missingRequired.join(", ")}`
                      : "Duplicate source column"
                    : undefined
                }
              >
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
