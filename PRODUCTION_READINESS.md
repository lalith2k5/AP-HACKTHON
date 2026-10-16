# Production Readiness Checklist

StoreSignal AI v2.0 is a local-first MVP. Per spec section 20.5, the
following items must be completed before any public or multi-user
deployment. Nothing in this file is implemented in this build.

## 1. Identity and access
- [ ] SSO / OIDC integration with an approved identity provider
- [ ] Real RBAC bound to identity, not demo API keys
- [ ] Sensitive-case access restrictions enforced at the storage layer
- [ ] Least-privilege service accounts and secret rotation

## 2. Storage
- [ ] Transactional database (Postgres or equivalent) replacing Parquet
- [ ] Migration strategy and schema versioning
- [ ] Encryption at rest and in transit
- [ ] Backup + restore drills

## 3. Transport
- [ ] TLS termination
- [ ] Secure cookie / session management
- [ ] CSRF protection where applicable

## 4. Operations
- [ ] Structured logging to a central sink
- [ ] Monitoring + alerting on pipeline failures and latency
- [ ] Runbooks for on-call
- [ ] Incident response process

## 5. Privacy
- [ ] Retention and deletion schedule approved by data owner
- [ ] PII impact assessment
- [ ] Approved export policy
- [ ] Redaction audit trail

## 6. Model governance
- [ ] Model card describing intended use and limitations
- [ ] Validation by language and channel
- [ ] Drift detection and rollback process
- [ ] Approval workflow for model promotion

## 7. Workflow
- [ ] Owner teams and SLAs formally agreed
- [ ] Approved playbooks replacing the current recommendation stubs
- [ ] Escalation rota for mandatory-risk alerts

## 8. Scale
- [ ] Background workers / queue for long jobs
- [ ] Idempotent job execution under concurrency
- [ ] Load testing at projected volume

## 9. Security
- [ ] Dependency scanning in CI
- [ ] Threat model review
- [ ] Penetration testing as appropriate

## 10. Compliance
- [ ] Legal, labour, consumer, food-safety review by qualified stakeholders

## What IS already done in this build

- Local-first binding (uvicorn + Streamlit default to localhost)
- Env-var configuration for all paths and secrets
- Hidden-label isolation enforced by env guard
- 7-role permission model defined and enforced server-side
- Append-only audit log for workflow and API mutations
- Import pipeline with schema validation, column mapping, PII-aware storage
- Deterministic pipeline (seed 20260214)
- Error envelope with request IDs on the API
