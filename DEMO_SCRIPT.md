# StoreSignal AI — Demo Script for Judges

Maps to spec section 22. Target runtime: 7 minutes live, 3 minutes Q&A.

## Pre-flight (do this 15 minutes before)

Run the checklist at the bottom of this file. Do not skip step 6.

## The story in one sentence

StoreSignal turns scattered store chatter into traceable incidents, escalates
safety issues regardless of volume, and shows the evidence behind every claim.

## Beat 1 — Frame (30 seconds)

"StoreSignal is not a sentiment dashboard. It is an early-warning and
incident-resolution layer. The output is not a score — it is an incident with
an owner and an audit trail."

Point at the sidebar: "This workspace is simulated data, clearly labelled."

## Beat 2 — Overview (60 seconds)

Open http://localhost:3300/overview

- "Four channels: reviews, app comments, staff notes, call centre."
- Point at KPIs: "40,053 records classified. Accuracy 0.891 on the hidden
  test set. Macro-F1 0.917."
- Point at the urgent queue: "This is not sorted by volume. It is sorted by
  policy severity."
- Change the region filter to DEL. "Filter is real. It re-queries the
  backend."

Do not linger. The overview is the map, not the territory.

## Beat 3 — The safety boundary (90 seconds) ← THE MOMENT

Open the alerts page: http://localhost:3300/alerts

- Filter to `mandatory_policy`.
- Pick any allergen or food-safety alert. Open it.
- "One record. One signal. It escalates anyway."
- Point at the reason field: "This is not the classifier's opinion. This is a
  mandatory policy rule that fires independently of confidence and volume."

Open the incident. Show the Evidence tab.

- "Here is the quote, the channel, the timestamp, the store, the record ID."
- "Every alert links back to source records. This is the traceability
  guarantee."

If asked about false positives, the honest answer is: "Escalation recall is
0.066 by design — we fire on the safety boundary, not on precision. False
positives are cheaper than missed food-safety signals."

## Beat 4 — Emerging trend (60 seconds)

Open http://localhost:3300/trends

- "This is the baseline-versus-current view. The robust z-score uses MAD, not
  standard deviation, so a single spike does not create an alert."
- Point at the anomalies table: "Three seeded incidents, all detected. Mean
  lead time 3.67 days before peak."
- "The denominator is weekly footfall where available. When it is not, the
  rate lift is marked not-calculable. We do not invent numbers."

## Beat 5 — Assignment and audit (60 seconds)

Open any incident, Actions tab.

- Change owner to `supply_chain`.
- Add a note: "Demo note — rehearse."
- Click Save.
- Show the Timeline tab: "The note and the status change are in the timeline.
  Every mutation writes an audit event."

Open http://localhost:3300/audit

- "Append-only. No UI to edit or delete. Timestamp, actor, object, reason."

## Beat 6 — Regional brief (60 seconds)

Open http://localhost:3300/reports

- Point at the structure: "Executive summary, top five issues, mandatory-risk
  section, evidence links, owner, next action."
- "Every sentence derives from a query. No LLM. No invented causal language."
- "Note the mandatory-risk section sits separately from the top five. Risk
  does not compete with volume."

## Beat 7 — Evaluation honesty (45 seconds)

Open http://localhost:3300/data-health

- "Metrics come from a hidden-label evaluator that normal pipeline code
  cannot read. Environment guard enforces it."
- Show the job controls: "The pipeline can be re-run from the UI. It takes
  about 27 seconds. We do not re-run it during the demo because it overwrites
  artifacts."

## Beat 8 — Close (30 seconds)

"Three things make this different:

1. Safety overrides volume. Always.
2. Every claim has an evidence trail back to a source record.
3. It runs locally, end to end. No cloud, no external AI, no data leaves
   the machine.

What we have not done is listed honestly in DEPLOYMENT.md — legal review,
pen test, real IdP swap, data-owner sign-off. Those are process items, not
engineering gaps."

## Rehearsal checklist

- [ ] Backend running: `./scripts/run-api.sh` (NOT bare uvicorn)
- [ ] Frontend running: `cd web && npm run dev -- --port 3300`
- [ ] Browser open at http://localhost:3300, clean profile, no other tabs
- [ ] Font size bumped to 125% for projection
- [ ] Do not show terminal tabs during the demo
- [ ] Demo reset done in advance: `POST /api/v1/demo/reset` — then re-run
      pipeline (27s) so state is fresh but artifacts are populated
- [ ] One dry run end to end, stopwatch on, under 7:30

## The one slide

If a slide is required:

    StoreSignal AI
    Voice-of-Store Engine

    Safety-first escalation
    Evidence-backed incidents
    Local, auditable, deterministic

    github.com/lalith2k5/AP-HACKTHON

## Three questions you will be asked

**Q: What stops a false accusation from ruining someone's career?**
A: No automated disciplinary action. The system flags risk for human review.
Staff-misconduct incidents are restricted to HR/risk roles, and every access
is audit-logged. We do not infer truth from feedback.

**Q: What if the model is wrong?**
A: Multi-label classification produces scores and uncertainty. Low-confidence
cases route to human review. And the mandatory policy engine runs
independently of the model — a safety signal does not depend on the
classifier being right.

**Q: How does this scale?**
A: The baseline is deterministic and local. For scale, the honest answer is
in section 24 of the spec: background workers, transactional DB (we have
SQLite), managed secrets, real IdP, monitoring. We have the architecture;
what is missing is the operational hardening, listed line by line.

## Numbers you should have memorised

- 40,053 records
- 0.8910 accuracy, 0.9167 macro-F1
- 0.9432 escalation precision
- 3/3 seeded incidents, 3.67 mean lead days
- 1.0000 policy compliance (1260/1260)
- 39 API endpoints, 17 frontend pages, 31 tests passing
