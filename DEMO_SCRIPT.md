# StoreSignal AI — 3-Minute Demo Script

Setup: `make serve` (Terminal 1) and `make ui` (Terminal 2).

## 0:00 — The problem
> Head office is drowning in unstructured feedback. Real operational
> problems — a broken freezer, a mislabelled allergen, a rude billing
> counter — surface weeks late. StoreSignal AI turns chatter into action.

## 0:20 — Command Center
Show: 40,000 records, 32 categories, 1,260 escalations, 1,320 alerts.
Line: "Reproducible pipeline — this is not a snapshot."

## 0:45 — Early-Warning Radar (killer feature)
Show: flag table with robust z-scores.
Line: "Three incidents were planted. We never look at hidden labels during
detection. The radar found all three, 3.67 days before each peak."

## 1:25 — Incident Explorer + fusion
Show: cross-channel incident with pipes in `channels` column.
Line: "Same allergen concern across call + app + review becomes one
incident — not three counts. Every source record is preserved."

## 1:55 — Regional Action Brief
Show: North region markdown brief.
Line: "Top 5 issues, evidence quotes, affected stores, trend arrows,
owner, next action. Every claim traces back to source data."

## 2:30 — Model & Trust
Show: evaluation report.
Line: "Macro-F1 0.9167 on hidden labels. Escalation precision 0.9432.
3/3 seeded detected. 3.67 days mean lead time. Precision over recall,
because that is what the spec asked for."

## 2:50 — Close
Line: "make clean && make pipeline regenerates every number on this screen."

## Backup answers

Q: Why TF-IDF, not transformers?
A: Baseline first. Char n-grams handle code-mixed noise; 0.92 macro-F1.
   The spec says evaluate embeddings only if the baseline shows limits.

Q: How is the mandatory-escalation invariant enforced?
A: Separate module (risk_policy.py). Fires on category OR weak-category OR
   severity. Tests enforce zero mandatory records dropped, even below 0.4
   confidence.

Q: Is this production-ready?
A: Production-shaped. Containerization, transactional state, CI/CD are
   listed as future work per the spec.
