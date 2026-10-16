# Stakeholder Acceptance — Release Gates

Maps to spec section 21.3. Each gate is a binary pass/fail with an owner.

| Gate | Pass condition | Evidence | Owner | Accepted |
|---|---|---|---|---|
| Data correctness | Row counts reconcile; invalid rows accounted for | data/evaluation/reports/ | | |
| Safety | Every mandatory-risk fixture escalates independent of volume | tests/test_policy.py | | |
| Model reporting | Metrics reproducible, per-class support shown | evaluation_report.json | | |
| Trend reporting | Seeded lead time and false-alert burden measured | evaluation_report.json | | |
| Evidence traceability | Every alert links to source records and version IDs | API + UI verification | | |
| Workflow | Import, analysis, assignment, status, brief all work | E2E test suite | | |
| Security | No secrets or PII in logs; uploads bounded; hidden labels isolated | Pen test report | | |
| Reliability | Failures visible; safe retry; last-known-good preserved | Manual fail-injection | | |
| Honesty | No fabricated metrics or business outcomes | Review of all docs | | |
| Documentation | Setup, run, evaluate, limits, troubleshooting documented | DEPLOYMENT.md, OPERATIONS_RUNBOOK.md | | |

## Threshold and playbook acceptance (spec 20.5)

Config values in config/*.yaml are defaults. Every value must be approved
against permitted validation data. See 07_threshold_tuning_worksheet.md.

## Sign-off

- Business owner: ______________
- Risk owner: ______________
- Ops owner: ______________
- Date: ______________
- Overall: [ ] Accepted  [ ] Accepted with conditions  [ ] Rejected
