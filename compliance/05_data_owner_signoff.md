# Data Owner Sign-Off

One page. Sign or return with gaps noted.

## System

StoreSignal AI — voice-of-store operational intelligence layer.

## Data classes and purposes

| Data class | Source | Purpose | Retention |
|---|---|---|---|
| Raw feedback text | Reviews, app comments, staff notes, call-centre transcripts | Operational incident detection | 24 months |
| Redacted display text | Derived from raw | UI display, evidence snippets | Same as raw |
| Classified labels and scores | Derived | Routing, trend detection, briefs | 36 months |
| Incident records | Derived | Workflow and reporting | 36 months |
| Overrides, notes, audit events | Operator actions | Accountability and traceability | 36 months |
| PII (if present in raw) | Feedback free text | Never displayed raw; redacted downstream | Same as raw |

## Access

| Role | Read | Write |
|---|---|---|
| Regional Operations Lead | Region scope | Assign, acknowledge, resolve |
| Store Manager | Assigned store | Acknowledge, note, resolve |
| Food Safety / Risk | Risk scope | Escalate, document |
| Supply Chain | Category scope | Assign, note |
| HR / Sensitive Reviewer | Staff-conduct only (access logged) | Restricted workflow |
| Analyst | Data-quality + eval | Run permitted pipeline |
| Administrator | All | Config, demo, rollback |

## Declarations

- [ ] Data owner confirms lawful basis for each processing purpose above
- [ ] Data owner confirms the retention schedule is acceptable
- [ ] Data owner confirms the access matrix is appropriate
- [ ] Data owner confirms any on-premise or in-country storage requirement
- [ ] Data owner confirms the SAR (Subject Access Request) procedure in
      RETENTION_POLICY.md is adequate
- [ ] Data owner confirms no real customer or staff data will be loaded
      without a fresh sign-off

## Signature

- Data owner name: ______________
- Title: ______________
- Date: ______________
- Outcome: [ ] Approved  [ ] Approved with conditions  [ ] Rejected
- Conditions:
