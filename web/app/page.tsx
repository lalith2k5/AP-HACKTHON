import Link from "next/link";
import { Reveal } from "@/components/reveal";

export default function WelcomePage() {
  return (
    <main style={{ minHeight: "100dvh", overflow: "hidden" }}>
      {/* Top nav */}
      <nav
        style={{
          position: "sticky",
          top: 0,
          zIndex: 50,
          height: 52,
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          padding: "0 32px",
          background: "color-mix(in oklab, var(--background) 78%, transparent)",
          backdropFilter: "blur(40px) saturate(180%)",
          WebkitBackdropFilter: "blur(40px) saturate(180%)",
          borderBottom: "1px solid var(--border)",
          fontSize: 13,
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          <span
            aria-hidden
            style={{
              width: 8,
              height: 8,
              borderRadius: "50%",
              background: "var(--apple-blue)",
              boxShadow: "0 0 12px var(--apple-blue)",
            }}
          />
          <span style={{ fontWeight: 600, letterSpacing: "-0.02em", fontSize: 14 }}>
            StoreSignal AI
          </span>
        </div>
        <div style={{ display: "flex", gap: 24, color: "var(--fg-secondary)" }}>
          <span style={{ fontWeight: 500 }}>Voice-of-Store Engine</span>
          <span
            style={{
              padding: "3px 10px",
              borderRadius: 999,
              background: "var(--separator-soft)",
              fontWeight: 600,
              fontSize: 11,
            }}
          >
            SIMULATED DATA
          </span>
        </div>
      </nav>

      {/* HERO */}
      <section
        className="glow-blue"
        style={{
          padding: "120px 24px 100px",
          textAlign: "center",
          maxWidth: 980,
          margin: "0 auto",
        }}
      >
        <Reveal>
          <span className="tag" style={{ marginBottom: 24 }}>
            Talent AP Mega Hackathon · Track R5
          </span>
        </Reveal>

        <Reveal delay={1}>
          <h1 className="display-xl" style={{ marginTop: 24 }}>
            Turning store chatter
            <br />
            into action.
          </h1>
        </Reveal>

        <Reveal delay={2}>
          <p
            className="lede"
            style={{ maxWidth: 640, margin: "28px auto 0" }}
          >
            40,000 multilingual feedback records. Four channels. One early-warning
            system that surfaces safety issues at low volume and hands every
            incident to the right owner — with evidence.
          </p>
        </Reveal>

        <Reveal delay={3}>
          <div
            style={{
              display: "flex",
              gap: 12,
              justifyContent: "center",
              marginTop: 40,
              flexWrap: "wrap",
            }}
          >
            <Link href="/overview" className="btn btn-primary btn-lg">
              Open sample workspace
            </Link>
            <Link href="/import" className="btn btn-secondary btn-lg">
              Import my data
            </Link>
          </div>
        </Reveal>

        <Reveal delay={4}>
          <p style={{ marginTop: 24 }}>
            <Link
              href="/reports"
              className="btn btn-ghost btn-sm"
              style={{ fontSize: 13 }}
            >
              See a live weekly brief →
            </Link>
          </p>
        </Reveal>

        <Reveal delay={5}>
          <p className="tiny muted" style={{ marginTop: 12 }}>
            Early-warning and incident-resolution, not a sentiment dashboard.
          </p>
        </Reveal>
      </section>

      {/* KEY NUMBERS */}
      <section className="section" style={{ maxWidth: 1200, margin: "0 auto", padding: "80px 32px" }}>
        <Reveal>
          <div style={{ textAlign: "center", marginBottom: 64 }}>
            <span className="eyebrow">Measured on hidden labels</span>
            <h2 className="display-md" style={{ marginTop: 16 }}>
              Numbers, not opinions.
            </h2>
          </div>
        </Reveal>

        <div className="bento">
          <Reveal delay={1} className="bento-2-1">
            <div className="card card-tall card-hover-lift">
              <div className="card-title">Classification accuracy</div>
              <div>
                <div className="stat">
                  89.1<span className="stat-unit">%</span>
                </div>
                <div className="stat-label">On 2,000 hidden-label records</div>
              </div>
            </div>
          </Reveal>

          <Reveal delay={2} className="bento-2-1">
            <div className="card card-tall card-hover-lift">
              <div className="card-title">Escalation precision</div>
              <div>
                <div className="stat">
                  94.3<span className="stat-unit">%</span>
                </div>
                <div className="stat-label">Of escalated, truly actionable</div>
              </div>
            </div>
          </Reveal>

          <Reveal delay={3} className="bento-2-1">
            <div className="card card-tall card-hover-lift">
              <div className="card-title">Policy compliance</div>
              <div>
                <div className="stat">
                  100<span className="stat-unit">%</span>
                </div>
                <div className="stat-label">1,260 / 1,260 mandatory-risk signals</div>
              </div>
            </div>
          </Reveal>
        </div>
      </section>

      {/* THREE PILLARS */}
      <section
        className="section-lg"
        style={{ maxWidth: 1200, margin: "0 auto", padding: "80px 32px" }}
      >
        <Reveal>
          <div style={{ textAlign: "center", marginBottom: 80 }}>
            <span className="eyebrow">What makes this different</span>
            <h2 className="display-md" style={{ marginTop: 16, maxWidth: 720, margin: "16px auto 0" }}>
              Three rules we don&rsquo;t break.
            </h2>
          </div>
        </Reveal>

        <div className="feature-row" style={{ marginBottom: 96 }}>
          <Reveal delay={1}>
            <span className="eyebrow">01 — Safety over volume</span>
            <h3 className="display-md" style={{ marginTop: 16, marginBottom: 20 }}>
              One signal is enough.
            </h3>
            <p className="lede" style={{ fontSize: 17 }}>
              Food safety, allergens, hygiene, and staff misconduct escalate on a
              single credible signal. The policy engine runs independently of the
              classifier and of trend volume. Volume cannot suppress it.
            </p>
          </Reveal>
          <Reveal delay={2}>
            <div className="card" style={{ padding: 28 }}>
              <div className="card-title">Escalation rule</div>
              <div style={{ marginTop: 16, fontSize: 15, fontWeight: 600, letterSpacing: "-0.01em" }}>
                mandatory_policy · high_risk_category
              </div>
              <div
                className="pill pill-critical"
                style={{ marginTop: 14, padding: "5px 12px", fontSize: 12 }}
              >
                Bypasses trend volume
              </div>
              <hr className="hr" style={{ margin: "24px 0" }} />
              <div className="card-sub" style={{ marginTop: 0 }}>
                Applied to every usable record. Independently unit-tested.
              </div>
            </div>
          </Reveal>
        </div>

        <div className="feature-row" style={{ marginBottom: 96 }}>
          <Reveal delay={2}>
            <div className="card" style={{ padding: 28 }}>
              <div className="card-title">Trend detection</div>
              <div style={{ marginTop: 16, fontSize: 15, fontWeight: 600, letterSpacing: "-0.01em" }}>
                Robust z-score (MAD) · 28d baseline · 72h window
              </div>
              <div
                className="pill pill-info"
                style={{ marginTop: 14, padding: "5px 12px", fontSize: 12 }}
              >
                3 / 3 seeded incidents detected
              </div>
              <hr className="hr" style={{ margin: "24px 0" }} />
              <div className="card-sub" style={{ marginTop: 0 }}>
                Mean lead time: 3.67 days before peak. Normalized by footfall
                where available.
              </div>
            </div>
          </Reveal>
          <Reveal delay={1}>
            <span className="eyebrow">02 — Emerging signals</span>
            <h3 className="display-md" style={{ marginTop: 16, marginBottom: 20 }}>
              Small, but rising sharply.
            </h3>
            <p className="lede" style={{ fontSize: 17 }}>
              A robust anomaly score flags a store-level increase before it
              becomes a national problem. Rate lift and coverage are disclosed;
              when the denominator is missing, we say so.
            </p>
          </Reveal>
        </div>

        <div className="feature-row">
          <Reveal delay={1}>
            <span className="eyebrow">03 — Every claim has evidence</span>
            <h3 className="display-md" style={{ marginTop: 16, marginBottom: 20 }}>
              Trace it back to a record.
            </h3>
            <p className="lede" style={{ fontSize: 17 }}>
              Every alert links to source record IDs, channel, timestamp, and
              store. Every mutation writes an append-only audit event. No
              fabricated metrics; no invented causal language.
            </p>
          </Reveal>
          <Reveal delay={2}>
            <div className="card" style={{ padding: 28 }}>
              <div className="card-title">Audit trail</div>
              <div style={{ marginTop: 16, fontFamily: "var(--font-mono)", fontSize: 12, lineHeight: 1.7 }}>
                <div>incident.status_changed · actor=ops-lead</div>
                <div>alert.overridden · reason &ldquo;dup of INC-4A58...&rdquo;</div>
                <div>note.added · actor=store-mgr</div>
              </div>
              <hr className="hr" style={{ margin: "24px 0" }} />
              <div className="card-sub" style={{ marginTop: 0 }}>
                SQLite WAL. Survives restart. No UI to edit or delete.
              </div>
            </div>
          </Reveal>
        </div>
      </section>

      {/* FINAL CTA */}
      <section
        className="section-lg"
        style={{
          textAlign: "center",
          padding: "120px 32px",
          background:
            "radial-gradient(60% 100% at 50% 0%, color-mix(in oklab, var(--apple-blue) 12%, transparent), transparent 70%)",
        }}
      >
        <Reveal>
          <h2 className="display-lg" style={{ maxWidth: 720, margin: "0 auto" }}>
            See it in 7 minutes.
          </h2>
          <p className="lede" style={{ maxWidth: 540, margin: "20px auto 0" }}>
            The full walkthrough is in the demo script. The workspace runs
            locally, on simulated data, without any cloud dependency.
          </p>
          <div style={{ display: "flex", gap: 12, justifyContent: "center", marginTop: 40 }}>
            <Link href="/overview" className="btn btn-primary btn-lg">
              Enter the workspace
            </Link>
            <Link href="/reports" className="btn btn-ghost btn-lg">
              Read a brief →
            </Link>
          </div>
          <p className="tiny muted" style={{ marginTop: 40 }}>
            Local · Demo mode · Simulated demo data · No real customer or staff data
          </p>
        </Reveal>
      </section>
    </main>
  );
}
