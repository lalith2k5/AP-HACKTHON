# StoreSignal AI - Evaluation Report

## 1. Classification quality on hidden labels

- Matched records: **2000**
- Accuracy: **0.8910**
- Macro-F1: **0.9167**
- Weighted-F1: **0.9065**

## 2. Escalation quality

- Escalated (total): **1260**
- Escalated with hidden labels: **88**
- Truly actionable in hidden labels: **1255**
- **Escalation precision**: **0.9431818181818182**
- **Escalation recall**: **0.06613545816733067**

## 2b. Operational metrics

- False alerts per store-week: **5.695**
- Policy compliance: **1.0** (1260/1260 mandatory records escalated)
- Fusion quality: multi-record ratio **0.3146**, cross-channel ratio **0.2337**
- Human override rate: **0.0**
- Resolution outcome rate: **0.0**

## 3. Seeded-incident lead time

- Detected: **3/3**
- Mean lead time vs peak: **3.6666666666666665 days**

| Incident | Store | Category | First seen | First record | Peak | First flag | Lead vs peak (d) |
|---|---|---|---|---|---|---|---|
| SEED-1 | S-MUM-003 | equipment_or_refrigeration | 2026-09-25 | 2026-09-04 | 2026-09-26 | 2026-09-22 | 4 |
| SEED-2 | S-BLR-007 | allergen_or_labeling | 2026-09-26 | 2026-09-05 | 2026-10-01 | 2026-09-26 | 5 |
| SEED-3 | S-DEL-002 | staff_misconduct | 2026-09-28 | 2026-09-05 | 2026-09-30 | 2026-09-28 | 2 |