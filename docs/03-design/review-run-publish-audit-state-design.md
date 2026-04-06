# FPDS Review, Run, Publish, and Audit State Design

Version: 1.0  
Date: 2026-04-01  
Status: Approved Baseline for WBS 1.3.2 - 1.3.5  
Source Documents:
- `docs/02-requirements/FPDS_Requirements_Definition_v1_5.md`
- `docs/01-planning/plan.md`
- `docs/01-planning/WBS.md`
- `docs/03-design/domain-model-canonical-schema.md`
- `docs/03-design/workflow-state-ingestion-design.md`
- `docs/00-governance/decision-log.md`
- `docs/02-requirements/scope-baseline.md`
- `docs/00-governance/stage-gate-checklist.md`

---

## 1. Purpose

This document closes the detailed state and audit design left open after `WBS 1.3.1`.

Goals:
- define the persisted review task state machine for `WBS 1.3.2`
- define the persisted run lifecycle and retry boundary for `WBS 1.3.3`
- define the persisted BX-PF publish lifecycle for `WBS 1.3.4`
- define the audit trail scope, event taxonomy, and required metadata for `WBS 1.3.5`
- provide a stable baseline for ERD, admin API, runbook, and audit-log implementation work

This is still a design document. It does not authorize coding by itself and does not replace Gate A or Product Owner build-start approval.

---

## 2. Baseline Decisions Carried Forward

This document applies the already-approved baseline decisions below.

1. Review queue creation unit is `candidate`.
2. Prototype routes all candidates to review.
3. Phase 1 may auto-approve only through policy/config, not hard-coded logic.
4. Run retry is `source/stage scoped`, not always full-run restart.
5. Run partial completion is allowed.
6. Publish retry and reconciliation are tracked separately from ingestion run retry.
7. BX-PF publish remains `interface-first`; exact adapter-facing write contract and field mapping stay in `docs/03-design/api-interface-contracts.md` Section 7.
8. FPDS owns operational truth for run, review, audit, publish, and reconciliation metadata.

---

## 3. Review State Machine

### 3.1 Review State vs Product Lifecycle State

- This section defines `review_task` state, not end-user product lifecycle state.
- PRD product lifecycle labels such as `Draft`, `Auto-Validated`, `Pending Publish`, and `Published to BX-PF` belong to candidate/product/publish layers and must not be reused as review-task states.
- Review state answers "what is the current human decision status for this candidate?"
- Product lifecycle answers "what is the current product/canonical/publish status for this record?"

### 3.2 Review Unit and Boundary

- One persisted `review_task` is created per `candidate` when routing decides human review is required.
- A review task references exactly one `candidate_id`, one `run_id`, and zero or one resulting `product_id`.
- Review task state is separate from canonical product status and separate from publish status.
- Opening a task in the admin UI does not change persisted review status by itself.
- Temporary assignment, lock, or "being viewed" indicators are operational metadata, not review states.

### 3.3 Persisted Review States

| State | Meaning | Terminal |
|---|---|---|
| `queued` | waiting for reviewer action | No |
| `approved` | candidate accepted without field edits | Yes |
| `rejected` | candidate rejected and excluded from canonical upsert/publish | Yes |
| `edited` | reviewer changed candidate-derived values and approved the edited result | Yes |
| `deferred` | task intentionally parked for later review or missing context | No |

### 3.4 Review Transition Rules

| From | Action | To | Required Side Effects |
|---|---|---|---|
| routing result | create review task | `queued` | persist queue reason, issue summary, linked evidence refs |
| `queued` | approve | `approved` | persist decision reason, actor, timestamp; allow canonical upsert |
| `queued` | reject | `rejected` | persist decision reason, actor, timestamp; block canonical upsert |
| `queued` | edit & approve | `edited` | persist override diff, decision reason, actor, timestamp; allow canonical upsert |
| `queued` | defer | `deferred` | persist defer reason and expected follow-up context |
| `deferred` | resume/requeue | `queued` | persist requeue reason, actor, timestamp |
| `deferred` | reject | `rejected` | persist decision reason, actor, timestamp |
| `deferred` | approve | `approved` | persist decision reason, actor, timestamp |
| `deferred` | edit & approve | `edited` | persist override diff, actor, timestamp |

### 3.5 Review Action Semantics

#### `approved`

- reviewer accepts the candidate as normalized
- canonical upsert/change assessment may proceed
- if publish eligibility is met, publish preparation may proceed

#### `rejected`

- candidate is not promoted to canonical product
- rejection is final for that review task
- a later run may create a new candidate and new review task for the same source/product continuity

#### `edited`

- reviewer changes one or more canonical-target values before approval
- edited approval is treated as approved for downstream canonical upsert and publish preparation
- if edited values change canonical field output, `ManualOverride` change history and audit events must be emitted

#### `deferred`

- used when evidence is insufficient, conflicting, or awaiting later operational review
- task remains open but intentionally inactive
- no canonical upsert or publish preparation occurs while deferred

### 3.6 Review Reason Code Baseline

The review task should support at least these reason codes.

- `low_confidence`
- `required_field_missing`
- `conflicting_evidence`
- `ambiguous_mapping`
- `validation_error`
- `manual_sampling_review`
- `partial_source_failure`
- `insufficient_context`
- `needs_domain_review`
- `policy_hold`
- `manual_override`

### 3.7 Review Concurrency and Idempotency Rules

- Only one active review task may exist for a single `candidate_id`.
- `queued` and `deferred` are the only active states.
- Terminal states may not transition back except by creating a new review task from a later candidate.
- Review actions must record actor, timestamp, and decision reason.
- `edit & approve` must persist field-level diff between candidate-derived values and reviewer-approved values.
- If the same review action is submitted twice, the second submission must be treated idempotently and must not create duplicate change or publish events.

### 3.8 Prototype vs Phase 1 Rule

| Area | Prototype | Phase 1 |
|---|---|---|
| routing | all candidates create review tasks | policy/config may auto-approve |
| review states | same state machine | same state machine |
| reviewer burden | expected high | expected lower after stable policies |

---

## 4. Run Lifecycle

### 4.1 Run Boundary

- A `run` is the top-level execution record created at Stage 0 of ingestion flow.
- A run aggregates source-level and stage-level outcomes for one trigger scope.
- There is no separate persisted `queued` run state in this baseline; the run record is created in `started`.
- Retry creates a new run attempt and links it to a prior run; it does not mutate the retried attempt into a new execution.

### 4.2 Persisted Run States

| State | Meaning | Terminal |
|---|---|---|
| `started` | run initialized and still executing or awaiting remaining stage completion | No |
| `completed` | run reached terminal completion; may include warnings or partial source failures | Yes |
| `failed` | run could not continue due to run-level fatal condition | Yes |
| `retried` | earlier run attempt has been superseded by a later retry run | Yes |

### 4.3 Run Outcome Fields Required Alongside State

Because `completed` may still include partial source failure, run state must be interpreted together with summary fields.

Minimum required summary fields:
- `started_at`
- `completed_at`
- `trigger_type`
- `triggered_by`
- `source_scope_count`
- `source_success_count`
- `source_failure_count`
- `candidate_count`
- `review_queued_count`
- `error_summary`
- `partial_completion_flag`
- `retry_of_run_id`
- `retried_by_run_id`

### 4.4 Run Transition Rules

| From | Event | To | Required Side Effects |
|---|---|---|---|
| trigger received | initialize run | `started` | persist run header, trigger metadata, source scope |
| `started` | all required stages finish | `completed` | persist completion timestamp, summary counters, error summary |
| `started` | fatal run-level error | `failed` | persist failure timestamp and terminal reason |
| `failed` | new retry run created | `retried` | persist `retried_by_run_id`; keep original failure summary |
| `completed` | targeted retry run created for unresolved issues | `retried` | persist `retried_by_run_id`; keep original completion summary |

### 4.5 Meaning of `completed`

`completed` means the run finished processing its allowed scope and produced final summary output.

`completed` does not require zero source failures. Instead:
- `partial_completion_flag = false` means clean completion
- `partial_completion_flag = true` means run completed with source/stage-level failures or warnings

`failed` is reserved for cases where the run itself cannot produce a meaningful terminal summary, such as:
- invalid trigger or scope
- run initialization failure
- unrecoverable dependency failure at run boundary
- corruption/integrity failure that prevents trustworthy completion

### 4.6 Retry Rules

- Retry default unit is `source` or `stage`, not unconditional full rerun.
- A retry creates a new run record linked by `retry_of_run_id`.
- The earlier run becomes `retried` after the new run attempt is formally registered.
- Retried run history must remain queryable in admin surfaces.
- Publish retry is excluded from run retry and handled in publish lifecycle.

### 4.7 Run Stage Telemetry Expectations

Run lifecycle must support per-stage counters or summaries for:
- discovery
- snapshot fetch
- parse
- chunk/evidence registration
- extraction
- normalization
- validation
- review routing
- canonical upsert/change assessment
- publish preparation
- aggregate refresh

This telemetry is operational metadata, not separate lifecycle states.

---

## 5. Publish Lifecycle

### 5.1 Publish Boundary

- Publish lifecycle begins only after candidate approval or edited approval and successful canonical upsert eligibility.
- Publish lifecycle belongs to the `publish_item` or equivalent publish-tracking record, not to the review task and not to the run itself.
- Publish state must remain queryable even when BX-PF is not yet fully available.

### 5.2 Persisted Publish States

| State | Meaning | Terminal |
|---|---|---|
| `pending` | eligible or potentially eligible item is waiting because dependency, policy, or environment conditions are not yet satisfied | No |
| `published` | publish attempt succeeded and target/master linkage is recorded | Yes |
| `retry` | publish failed in a retryable way and another attempt is expected | No |
| `reconciliation` | publish outcome is ambiguous or target state requires manual/system reconciliation | No |

### 5.3 Publish Transition Rules

| From | Event | To | Required Side Effects |
|---|---|---|---|
| approved canonical record | create publish item | `pending` | persist pending reason, target environment metadata |
| `pending` | publish succeeds | `published` | persist published timestamp, target master id, response summary |
| `pending` | retryable failure | `retry` | persist attempt count, error code, next retry plan |
| `pending` | ambiguous or mismatched outcome | `reconciliation` | persist reconciliation reason and comparison metadata |
| `retry` | retry succeeds | `published` | persist latest attempt result, target linkage |
| `retry` | retry blocked by dependency/policy | `pending` | persist new pending reason |
| `retry` | ambiguous outcome | `reconciliation` | persist reconciliation reason |
| `reconciliation` | target state confirmed successful | `published` | persist reconciled timestamp and evidence |
| `reconciliation` | target state confirmed not applied but retryable | `retry` | persist next retry plan |
| `reconciliation` | dependency/policy hold reapplied | `pending` | persist pending reason |

### 5.4 Publish Reason Code Baseline

The publish tracker should support at least these reason codes.

- `environment_not_ready`
- `missing_contract_mapping`
- `awaiting_credentials`
- `policy_hold`
- `transient_transport_error`
- `rate_limited`
- `target_validation_error`
- `response_ambiguous`
- `target_state_mismatch`
- `manual_reconciliation_required`

### 5.5 Publish State Rules

- Rejected or deferred review tasks do not create publish items.
- `edited` review decisions are publish-eligible in the same way as `approved`.
- Publish failure must not roll back the already-approved canonical product state.
- Duplicate publish attempts for the same canonical version must be prevented by idempotency key or equivalent dedupe metadata.
- Reconciliation must preserve both FPDS view and last known BX-PF target response context.

---

## 6. Audit Trail Scope

### 6.1 Audit Objective

Audit trail exists to answer:
- who or what performed the action
- when it happened
- what entity was affected
- what state changed
- why it happened
- what evidence or request context supports it

### 6.2 Audit Scope Included in Phase 1 Baseline

Audit trail scope must include at least these categories.

| Category | Must Capture |
|---|---|
| review | review task creation, decision, defer/resume, edit diff, trace access relevant to decision |
| run | run start, terminal state change, retry creation, fatal stage summary |
| publish | publish item creation, publish attempts, retry scheduling, reconciliation entry/resolution, success |
| auth/security | login success/failure, logout, session revoke, privilege change, credential issuance/revocation when applicable |
| change governance | manual override, status reclassification, important configuration change affecting review/publish behavior |
| usage governance | LLM/model usage records linked to run/agent/model context |

### 6.3 Audit Scope Explicitly Out of Scope for This WBS Closure

- public anonymous page-view analytics
- product comparison clickstream analytics
- Phase 2 external API tenant audit separation detail
- exact retention duration by class

Exact retention periods remain a follow-up security policy item. This document closes event scope and required metadata, not long-term retention duration.

### 6.4 Mandatory Audit Event Fields

Every audit event must support at least the following fields.

| Field | Description |
|---|---|
| `audit_event_id` | unique event id |
| `event_category` | review, run, publish, auth, config, usage |
| `event_type` | concrete action name |
| `occurred_at` | event timestamp |
| `actor_type` | `system`, `user`, `service`, `scheduler` |
| `actor_id` | user id, service id, or nullable system actor reference |
| `actor_role_snapshot` | role at event time when available |
| `target_type` | run, candidate, review_task, product, publish_item, auth_session, config |
| `target_id` | affected entity id |
| `previous_state` | prior state when applicable |
| `new_state` | new state when applicable |
| `reason_code` | normalized reason code when applicable |
| `reason_text` | optional operator note or system detail |
| `run_id` | related run if available |
| `candidate_id` | related candidate if available |
| `review_task_id` | related review task if available |
| `product_id` | related product if available |
| `publish_item_id` | related publish tracker if available |
| `request_id` | request/correlation id when available |
| `diff_summary` | field diff summary for edits/config changes |
| `source_ref` | source URL/document/chunk reference when applicable |
| `ip_address` | auth/admin request origin when applicable |
| `user_agent` | auth/admin request agent when applicable |

### 6.5 Minimum Audit Event Taxonomy

| Event Type | Actor | Trigger Timing | Required Notes |
|---|---|---|---|
| `review_task_created` | system | review routing creates task | include queue reason and issue summary |
| `review_task_approved` | user | approve action | include reason code |
| `review_task_rejected` | user | reject action | include reason code |
| `review_task_edited` | user | edit & approve action | include diff summary |
| `review_task_deferred` | user | defer action | include defer reason |
| `review_task_requeued` | user/system | deferred task resumed | include requeue reason |
| `evidence_trace_viewed` | user | reviewer opens sensitive trace context | include review task/product context |
| `run_started` | system/user/scheduler | run initialization | include trigger metadata |
| `run_completed` | system | run terminal completion | include summary counters |
| `run_failed` | system | fatal run termination | include terminal reason |
| `run_retried` | system/user | retry run linked to prior run | include old/new run ids |
| `publish_item_created` | system | publish preparation produces tracker | include pending reason |
| `publish_attempted` | system | outbound publish attempt begins | include attempt number |
| `publish_succeeded` | system | publish confirmed | include target master id |
| `publish_retry_scheduled` | system | retry state entered | include error code/backoff plan |
| `publish_reconciliation_entered` | system | reconciliation state entered | include mismatch/ambiguity summary |
| `publish_reconciliation_resolved` | system/user | reconciliation closed | include resulting state |
| `auth_login_succeeded` | user/system | login success | include auth method |
| `auth_login_failed` | user/system | login failure | include failure reason |
| `auth_logout` | user/system | logout/session close | include session id if available |
| `privilege_changed` | user/system | role/permission change | include before/after role snapshot |
| `credential_issued_or_revoked` | user/system | secret/token/credential lifecycle event | include credential type only, never secret value |
| `config_changed` | user/system | review/publish policy changes | include diff summary |
| `manual_override_recorded` | user | canonical field override/change history event | include changed field list |
| `llm_usage_recorded` | system | model usage persisted | include run/agent/model context |

### 6.6 Audit Integrity Rules

- Audit events are append-only.
- Audit events must never store secret values or full credentials.
- State-changing actions in review, publish, and auth flows must emit audit events in the same logical transaction boundary as the business action or must fail visibly if audit persistence fails.
- `ManualOverride` must create both change history and audit trail records.
- Audit taxonomy must be stable enough for admin filtering by actor, date, category, target, and reason code.

### 6.7 Retention Handling Baseline

- Every audit event should carry a `retention_class` or equivalent classification hook.
- Exact retention period, archival rule, and purge rule will be closed in a later security/operations document.
- Lack of final retention duration must not block defining event schema, capture scope, or admin query surface.

---

## 7. Interfaces and Follow-On Work Unlocked

This document provides baseline input for:
- `WBS 1.4.2` ERD draft
- `WBS 1.5.2` admin API contract
- `WBS 1.5.3` internal orchestration interfaces
- `WBS 1.6.x` auth/RBAC/security design
- `WBS 4.2`, `4.5`, `4.7`, `6.2`, `6.3` implementation design later

This document does not close:
- exact BX-PF remote payload/response transport contract (`docs/03-design/api-interface-contracts.md` Section 7 closes the adapter-facing baseline)
- vector index implementation detail (`WBS 1.4.4`)
- exact audit retention duration policy

---

## 8. WBS Mapping

| WBS ID | Closure in This Document |
|---|---|
| 1.3.2 | Section 3 |
| 1.3.3 | Section 4 |
| 1.3.4 | Section 5 |
| 1.3.5 | Section 6 |

---

## 9. Change History

| Date | Change |
|---|---|
| 2026-04-01 | Initial state and audit design baseline created for WBS 1.3.2 - 1.3.5 |
