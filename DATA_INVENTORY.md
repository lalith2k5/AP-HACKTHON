# Data Inventory — StoreSignal AI

**Status:** draft for legal review. Not a compliance certification.

## What data is processed

| Source | Fields | Sensitivity | Storage |
|---|---|---|---|
| Customer reviews | text, rating, timestamp, store_id | Low (public) | data/raw/, data/processed/ |
| App feedback | text, app version, timestamp | Low | same |
| Staff shift notes | text, shift_id, timestamp | Medium — may identify staff | same |
| Call transcripts | text, timestamp, agent_id | Medium — may contain PII | same |
| Store reference | store_id, region, city | Low | data/reference/ |

## Automatic redaction

src/storesignal/normalization.py detects and redacts: emails, phone numbers,
long digit strings, address-like patterns. Applied to text_display_redacted.
Raw text remains in restricted artifacts for authorized workflows.

## Not stored

- Passwords, API keys, session tokens
- Account numbers
- Any data transmitted to third-party LLMs or cloud APIs

## Access (post-SSO)

admin (all) · analyst (read+evaluate) · regional_ops_lead (read+write) ·
store_manager (own store) · hr_sensitive (misconduct only, logged) ·
food_safety_risk (mandatory-risk) · reviewer (read+write) · supply_chain (relevant)

## Data flow

    raw --> ingest --> normalize(redact) --> parquet
                                            |
                                       predictions
                                            |
                                       risk policy
                                            |
                              incidents / alerts / briefs
                                            |
                                     Next.js UI

No external network calls except UI <-> API on localhost.

## Before processing real data

- [ ] Legal review of retention period
- [ ] DPO sign-off
- [ ] Consent path documented for staff data
- [ ] Encryption at rest for data/raw/
- [ ] Access log review cadence
