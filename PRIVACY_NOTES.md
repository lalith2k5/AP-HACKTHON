# Privacy Notes — StoreSignal AI

## Design principles

1. Data minimization — only needed fields ingested
2. Redaction by default — UI and logs show redacted text
3. No external calls — no LLM, translation, or analytics SDK
4. Local storage — no cloud backup by default
5. Audit trail — every mutation with actor + timestamp
6. Hidden-label isolation — eval labels unreachable from UI/API

## Threat model (informal)

| Threat | Mitigation | Gap |
|---|---|---|
| Malicious upload | size/type limits, safe parsers | no AV scan |
| Prompt injection | no LLM in MVP | n/a |
| PII leak in logs | redaction in normalization | manual logs not scanned |
| Hidden-label leak | env guard + module boundary | unit-tested |
| Unauthorized mutation | API key -> role map | key is static in demo |
| Lost audit event | SQLite WAL, append-only | no replication |

## Not this system

- Not a decision-maker. Feedback is unverified signal.
- Not a disciplinary tool. Routes to HR for human review.
- Not surveillance. No GPS, biometrics, live tracking.
- Not a public service. Local-first, single-tenant by default.

## Production next steps

1. TLS via scripts/serve-tls.sh (Caddy auto-cert for real domain)
2. Replace static API key with OIDC/OAuth2
3. Move SQLite -> PostgreSQL with row-level security
4. Ship audit log to SIEM
5. Retention cron (RETENTION_POLICY.md)
6. Penetration test before exposing non-localhost
