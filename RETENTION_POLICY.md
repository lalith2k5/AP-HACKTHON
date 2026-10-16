# Retention Policy — StoreSignal AI (TEMPLATE)

**Status:** template. Fill in with counsel and DPO before real data.

## Default windows

| Data class | Retention | Basis |
|---|---|---|
| Raw feedback | 90 days (proposed) | minimize PII |
| Normalized parquet | 365 days | analytics |
| Incidents / alerts | 730 days | operational history |
| Audit log | 7 years (proposed) | regulatory typical |
| Backups | 30 days rolling | DR |
| Eval reports | indefinite | model governance |

## Deletion procedure

    1. Stop ingestion for affected source
    2. Delete from data/raw/
    3. Re-run pipeline (regenerates without deleted rows)
    4. Delete SQLite rows for affected IDs
    5. Record event_type=deletion_request in audit log
    6. Spot-check verify

## SARs

Route to DPO. Search data/raw/ and data/processed/storesignal.db.
Provide raw text (if identifiable), incident references, actions taken.
Respond within statutory window (GDPR 30 days, etc.).

## Exceptions

- Legal hold: freeze deletion for specified incidents
- Safety: allergen/food-safety incidents retained for audit

## Sign-off

    DPO: ____________________  Date: __________
    Legal: __________________  Date: __________
