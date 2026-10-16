# Meeting - Stakeholder Acceptance
Duration: 45 minutes
Attendees: You, Business owner, Risk owner, Ops owner
Goal: 06_stakeholder_acceptance.md gates signed + 07_threshold_tuning_worksheet.md reviewed

## Agenda

0:00-0:05  Recap (5 min)
  - Demo of 3 screens: /overview, /incidents/[id], /reports
  - Reminder: 10 release gates from spec 21.3

0:05-0:25  Walk the 10 gates (20 min)
  For each gate: state the pass condition, show the evidence, ask for
  acceptance. Use 06_stakeholder_acceptance.md as the checklist.
  - Data correctness
  - Safety
  - Model reporting
  - Trend reporting
  - Evidence traceability
  - Workflow
  - Security (note: pen test pending)
  - Reliability
  - Honesty
  - Documentation

0:25-0:40  Threshold tuning (15 min)
  Open 07_threshold_tuning_worksheet.md
  For each config value: state the current, the rationale, ask for
  approval or adjustment. Any change requires re-validation.
  - Ops lead owns thresholds.yaml
  - Risk lead owns risk_policy.yaml
  - Owner teams confirm routing.yaml rows

0:40-0:45  Sign and next steps (5 min)
  - Collect signatures on 06
  - Note any conditions
  - Agree date for re-review if anything is conditional

## What to bring
- 06_stakeholder_acceptance.md (printed, one per attendee)
- 07_threshold_tuning_worksheet.md (printed, one per attendee)
- Laptop with the running app
- DEPLOYMENT.md as backup reference

## Do NOT
- Do not claim more than the system does. Read section 20.5 aloud if
  anyone pushes: "not approved for multi-user deployment until..."
- Do not skip the pen-test caveat on the Security gate.
- Do not commit to thresholds you have not validated on data.
