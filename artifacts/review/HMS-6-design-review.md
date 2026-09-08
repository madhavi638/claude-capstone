# Design Review Report — HMS-6 (Appointment Management)

**Reviewed:** artifacts/architecture/HMS-6-design-spec.md, artifacts/architecture/adr/HMS-6-ADR-001.md, and (for consistency) artifacts/database/HMS-6-database-design.md.
**Role:** Principal Architecture Reviewer (adversarial review — challenging assumptions, not rubber-stamping)

## Executive Summary

The core architecture — layered API/service/repository, database-enforced slot exclusivity
(ADR-001), and an append-only status-history audit trail — is sound and directly traceable to
the epic's business rules and NFRs. Two gaps are serious enough to require resolution before
Implementation Planning locks in tasks: **(1)** the auth/identity integration is asserted but not
contracted, and **(2)** "async, best-effort" notification dispatch does not actually guarantee the
BR-013 notification requirement it claims to satisfy. Neither is a redesign — both are
tightenings of what's already proposed.

## Architecture Strengths

- **ADR-001's DB-level `EXCLUDE USING gist` constraint** is the correct fix for the
  double-booking race condition — an app-level check-then-insert would not have been safe under
  concurrency (NFR-014). This is now also implemented in the database phase, not just proposed.
- **Append-only `appointment_status_history`** with mandatory `actor_id` + `changed_at` cleanly
  satisfies NFR-018 without overloading the `appointments` row itself with audit concerns.
- **Layering (router → service → repository)** keeps the state machine and conflict-check logic
  out of the API layer, which is exactly where business-rule enforcement (BR-009, BR-011, BR-012)
  needs to live to be testable and reusable.
- **Scoping the exclusion constraint to active statuses** was the right call — an unscoped
  constraint would have permanently locked a slot after cancellation, which is a subtle
  correctness bug the design spec explicitly avoided.

## Security Review

- **Gap (High):** The design states role-based access control and auth are "delegated to the
  existing HMS identity/user module," but no such module exists in this workspace and no
  contract is defined for what the Appointment service actually receives (a user ID? a role
  claim? both?). Without this, Implementation Planning cannot scope authorization tasks
  concretely — it will guess.
- `actor_id` on `appointment_status_history` is not a foreign key (acknowledged in the database
  design as a known gap) — this is acceptable for now, but the API layer **must** derive
  `actor_id` from the authenticated principal server-side, never accept it as client input, or
  the audit trail becomes forgeable. This constraint should be stated explicitly, not just
  implied by "auth is delegated elsewhere."
- No mention of patient health data protection/compliance handling (e.g. access logging beyond
  status-history, data-at-rest considerations). Likely out of this epic's scope per the problem
  spec, but should be explicitly confirmed rather than silently assumed away, given the domain.

## Scalability Review

- GiST exclusion indexes have higher write-side maintenance cost than a plain btree unique
  index. For expected hospital-appointment volumes this is very likely fine, but it's worth a
  load-test checkpoint rather than an unexamined assumption, since it's on the hot booking path.
- **Gap (Medium):** No pagination or result-size limit is defined for the appointment listing
  endpoint (FR-020). An unbounded `GET /appointments` for a busy provider will eventually become
  an NFR-001 problem. This needs a default page size / cursor strategy before implementation.
- Indexes on `(patient_id, start_time)` and `(provider_id, start_time)` correctly match the two
  stated visibility access patterns — no over- or under-indexing observed.

## Reliability Review

- **Gap (High):** The design describes notification dispatch as "async... failures are logged,
  not fatal." That protects the booking transaction (NFR-002) but does **not** protect the
  BR-013 guarantee that stakeholders are notified — a logged-and-dropped failure is silent data
  loss from the business rule's perspective. As written, this satisfies "don't block booking on
  notification failure" while quietly *not* satisfying "must notify." These are two different
  requirements and the current design only addresses one.
  - **Recommendation:** introduce a durable outbox (event row written in the same transaction as
    the appointment change, dispatched by a separate worker with retry/backoff, marked
    delivered/failed) rather than a purely in-process best-effort call. This keeps the "don't
    block booking" property while actually making delivery durable and retryable.
- No behavior is specified for what happens if the exclusion-constraint violation is raised —
  the design says "translate to `409 Conflict`" (good), but doesn't say whether the client is
  expected to retry with a different slot automatically or whether that's a UI concern. Minor,
  but worth a one-line clarification for the API contract.

## Maintainability Review

- Clear separation of concerns; no objection.
- The status **state machine itself is referenced (BR-012) but never enumerated** — the design
  spec says "follow the defined lifecycle state machine" without stating which transitions are
  legal. Two different implementers could reasonably disagree on whether `NO_SHOW` is reachable
  from `CONFIRMED` only or also from `SCHEDULED`. This ambiguity should be resolved with an
  explicit transition table before Implementation Planning decomposes tasks, or BR-012
  enforcement will be inconsistent across code paths.
- Placeholder `patients`/`providers` stub tables are well-flagged in the database design, which
  is good practice — but there is no tracked follow-up item to reconcile them with the real
  modules. Recommend this becomes an explicit backlog item, not just a comment in a doc.

## Backward Compatibility Review

- Greenfield module — no existing appointment system to be compatible with inside this
  workspace, so direct compatibility risk is low.
- **Open concern:** HMS-6's Jira labels include `hms-backlog-import`, suggesting this epic was
  imported from a pre-existing backlog/system rather than authored fresh. If there is legacy
  appointment data anywhere that this module is expected to inherit or migrate, that is
  unaddressed by the current design and should be confirmed, not assumed absent.

## Risk Assessment

### High Risks
- Auth/identity integration contract is undefined — blocks concrete authorization task scoping.
- Notification "best-effort" dispatch does not actually guarantee BR-013; risk of silent,
  unrecoverable notification loss.

### Medium Risks
- No enumerated state-transition table for BR-012 — risk of inconsistent enforcement.
- No pagination/limits defined for appointment listing — risk under load (NFR-001).
- GiST exclusion constraint write-cost under high concurrent booking volume is unverified.

### Low Risks
- Placeholder `patients`/`providers` schemas may need rework when real modules are built.
- Legacy/backlog-import data migration need is unconfirmed.
- Scope assumptions (no recurring/multi-party appointments) are inferred, not business-confirmed.

## Recommendations

1. Before Implementation Planning: define the concrete auth contract the Appointment service
   will consume (claims/fields available on the authenticated principal), even as a stub
   interface if the real identity module isn't built yet.
2. Replace "log-and-drop" notification dispatch with a durable outbox + retry/backoff pattern so
   BR-013 is actually guaranteed, not just attempted.
3. Enumerate the full appointment status transition table explicitly as an implementation
   planning artifact.
4. Define pagination defaults (e.g. page size, max) for the appointment listing endpoint.
5. Open a tracked follow-up for reconciling placeholder `patients`/`providers` tables with the
   real HMS patient/provider modules once they exist.
6. Confirm with a business/compliance stakeholder whether legacy appointment data migration or
   additional data-protection handling is in scope.

## Open Concerns

- Data protection/compliance requirements for patient health information (not addressed; likely
  out of this epic's scope, needs explicit confirmation rather than silent omission).
- Whether `hms-backlog-import` implies pre-existing appointment data requiring migration.

## Final Assessment

**APPROVED WITH CONCERNS** — architecture is sound and may proceed to Implementation Planning,
provided recommendations 1–4 above are captured as explicit tasks (not silently dropped) in the
implementation manifest. Recommendations 5–6 are tracked follow-ups, not blockers.
