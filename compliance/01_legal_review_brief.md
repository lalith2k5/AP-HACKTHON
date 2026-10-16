# Legal Review Brief — StoreSignal AI

Prepared for counsel review. Not legal advice.

## What the system does

StoreSignal AI ingests multilingual retail feedback from four channels
(customer reviews, app comments, staff shift notes, call-centre excerpts),
classifies it into a versioned taxonomy of operational categories, applies a
mandatory high-risk policy engine, detects emerging trends, groups related
signals into incidents, routes them to an owning team with an SLA, and
produces evidence-linked weekly regional briefs.

## What the system does NOT do

- No automated disciplinary decisions
- No determination that any allegation is true
- No cloud LLM, machine translation, or external data transmission
- No access to real customer or staff systems
- No scraping
- No raw PII in normal UI or logs (redacted at the normalization stage)

These exclusions are architectural, not policy: they are enforced by code
boundaries (see spec section 4.2 module contracts).

## Data classes touched

See DATA_INVENTORY.md. Summary:
- Feedback text (customer/staff authored, may contain PII in free text)
- Ratings, channel, timestamp, store ID (pseudonymous)
- Derived labels, scores, severity, policy flags
- Audit events (actor, action, timestamp, object ID)

## Specific questions for counsel

1. Under DPDP Act 2023, what is the lawful basis for processing feedback
   collected via reviews and call centres? Does existing consent at the
   collection point extend to this secondary processing?
2. Retention: RETENTION_POLICY.md proposes 24 months for raw, 36 months for
   derived. Does that comply with the DPDP retention limitation principle?
3. Right to erasure: the system is append-only by design (source IDs are
   preserved). What is the compliant mechanism to honour an erasure request
   without destroying audit integrity?
4. Food safety signals: is a single credible signal sufficient to escalate
   internally, or does FSSAI reporting duty trigger before internal review?
5. Staff misconduct: what access restrictions must apply before HR review?
   POSH Act 2013 implications?
6. Cross-border: everything runs local. If we later host on cloud, what
   additional obligations attach?
7. Breach notification: what is the reporting timeline under DPDP rules?

## Sign-off

- Reviewed by (counsel name): ______________
- Date: ______________
- Outcome: [ ] Approved  [ ] Approved with conditions  [ ] Rejected
- Conditions / notes:
