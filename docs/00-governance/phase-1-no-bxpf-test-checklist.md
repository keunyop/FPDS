# Phase 1 No-BXPF Test Checklist

Version: 1.0
Date: 2026-04-15
Status: Active Interim QA Baseline
Source Documents:
- `docs/02-requirements/scope-baseline.md`
- `docs/01-planning/WBS.md`
- `docs/01-planning/plan.md`
- `docs/03-design/domain-model-canonical-schema.md`
- `docs/03-design/review-run-publish-audit-state-design.md`
- `api/service/README.md`
- `README.md`

---

## 1. Purpose

This checklist defines what the team can test now when BX-PF environment readiness is still blocked.

Goals:
- keep Phase 1 schedule moving without pretending BX-PF publish is already testable
- verify all FPDS-owned behavior that does not require live BX-PF write-back
- make the temporary test boundary explicit so acceptance language does not drift
- produce concrete evidence that the approved product data is already stored and reviewable inside FPDS before external publish is enabled

This checklist is an interim QA/verification tool. It does not change Phase 1 scope, and it does not mark BX-PF publish work as done.

---

## 2. Baseline Decision

Use this checklist only under the following condition:

- BX-PF interface, credentials, environment, or operating rules are not ready enough to execute live publish work

Under that condition:

- FPDS-owned ingestion, review, approval, canonical persistence, public read surfaces, and operator visibility should still be tested
- BX-PF connector, publish execution, retry/reconciliation workflow, and publish monitor should remain explicitly untested and blocked

This interpretation is aligned with the approved requirement that FPDS must still manage approved copy and publish/reconciliation metadata even when BX-PF write-back is not immediately available.

---

## 3. What FPDS Already Stores Internally

Before using this checklist, keep the internal record boundary clear:

- `normalized_candidate` stores the extracted and normalized review-target draft
- `review_task` stores the persisted human-review queue item
- `canonical_product` stores the approved internal canonical product record
- `product_version` stores the approved immutable version snapshot
- `field_evidence_link` stores field-to-evidence traceability
- `change_event` and `audit_event` store continuity and operator/audit history

This means BX-PF publish can be blocked while FPDS internal approval, continuity, traceability, and public read behavior are still fully testable.

---

## 4. Explicitly Out of Scope for This Checklist

Do not mark the following items as passed from this checklist alone:

- live BX-PF connector execution
- approved product write-back into BX-PF
- publish pending/retry/reconciliation runtime behavior
- publish monitor UI behavior
- target master id linkage returned from BX-PF
- release hardening sign-off that depends on the publish path

These items remain separate follow-on work under `WBS 6.x`.

---

## 5. Preconditions

Check these before starting:

- [v] DB migrations are applied through `0003_aggregate_refresh.sql`
- [v] API service can run locally
- [v] public app can run or build locally
- [v] admin app can run or build locally
- [v] at least one reviewable dataset exists in the DB, or a rerunnable ingestion path is available
- [v] a test operator account exists for admin login
- [v] BX-PF mode stays `disabled`, `mock`, or otherwise non-live during this checklist

Suggested local verification commands:

```powershell
cd api/service
uv run python -m unittest discover -s tests

cd ../../app/public
cmd /c npm run typecheck
cmd /c npm run build

cd ../admin
cmd /c npm run typecheck
cmd /c npm run build
```

---

## 6. Checklist

## 6.1 Ingestion and Internal Persistence

- [v] Big 5 source-backed records are available for the approved product types: `chequing`, `savings`, `gic`
- [v] ingestion run data is queryable from FPDS run history
- [v] source-derived candidate drafts are persisted as `normalized_candidate`
- [v] candidate records preserve core identity fields such as `bank_code`, `product_type`, `product_name`, `currency`, and `source_language`
- [v] evidence links are persisted for reviewable fields
- [v] validation status and issue codes are persisted on the candidate
- [v] no step in this flow depends on BX-PF availability

Recommended evidence:
- run id
- candidate ids
- sample candidate payload
- sample field evidence links

## 6.2 Review Queue and Decision Flow

- [v] review queue loads protected `queued` and `deferred` tasks
- [v] review detail shows candidate payload, evidence trace, and decision context
- [v] `approve` updates the review task to a terminal approved state
- [v] `edit_approve` records override diff and approved result
- [v] `reject` keeps the candidate from being promoted to canonical product
- [v] `defer` keeps the task open without promoting the record
- [v] review actions require valid session and CSRF protection

Recommended evidence:
- review task id
- before/after review state
- decision payload or screenshot
- audit event id if available

## 6.3 Canonical Product and Version Persistence

- [v] approved or edited-approved review actions create or update `canonical_product`
- [v] approved records create a `product_version` snapshot
- [v] repeated approvals update continuity/versioning without duplicating the same product identity incorrectly
- [v] `last_verified_at`, `current_version_no`, and snapshot payload update as expected
- [v] change history reflects `New`, `Updated`, `Reclassified`, or `ManualOverride` when applicable
- [v] FPDS retains the approved internal copy even though BX-PF publish is blocked

Recommended evidence:
- product id
- product version id
- version number change
- change event ids and event types

## 6.4 Evidence Traceability and Auditability

- [v] field-level evidence remains visible from the admin review detail route
- [v] evidence trace access is auditable where implemented
- [v] review decision audit events are queryable
- [v] manual override audit context appears when edited approval changes persisted values
- [v] run, review, product, and audit drilldowns stay linked to the same product continuity story

Recommended evidence:
- sample field trace
- audit log rows for review action
- linked run/review/product references

## 6.5 Public Product Grid

- [v] `/products` loads against the latest successful aggregate snapshot
- [ ] filter vocabulary loads and applies correctly
- [ ] product cards render the approved product types with the expected primary metrics
- [ ] pagination and sorting work for the current aggregate scope
- [ ] freshness and methodology notes render
- [ ] EN/KO/JA locale switching works for UI-owned copy
- [ ] empty state and API-unavailable fallback remain understandable

Recommended evidence:
- screenshots for default scope and one filtered scope
- locale switch screenshots
- one empty-state or unavailable-state screenshot if exercised

## 6.6 Public Insight Dashboard

- [ ] `/dashboard` loads summary, ranking, and scatter-backed content from FPDS internal aggregate data
- [ ] dashboard scope follows the shared public filter vocabulary
- [ ] dashboard drill-in links return to the Product Grid with meaningful narrowed scope
- [ ] methodology and freshness messaging render
- [ ] EN/KO/JA locale switching works for UI-owned copy
- [ ] single-type and mixed-scope behavior remains consistent with the approved dashboard rules

Recommended evidence:
- default dashboard screenshot
- single-product-type screenshot
- one drill-in example with preserved query scope

## 6.7 Admin and Ops Continuity

- [ ] admin login works with DB-backed operator/session data
- [ ] `/admin/reviews` and `/admin/reviews/:reviewTaskId` remain usable
- [ ] `/admin/runs` and `/admin/runs/:runId` expose run diagnostics
- [ ] `/admin/changes` shows canonical chronology tied to review/run context
- [ ] `/admin/audit` shows append-only review/auth/run context
- [ ] `/admin/usage` remains queryable for model/token/cost visibility
- [ ] current admin shell keeps publish/health as route-oriented follow-on surfaces without breaking the implemented routes

Recommended evidence:
- login success evidence
- one review task walk-through
- one run detail screenshot
- one change history screenshot
- one audit log screenshot
- one usage screen screenshot

## 6.8 Responsive and Cross-Surface QA

- [ ] Product Grid is usable on desktop width
- [ ] Product Grid is usable on tablet width
- [ ] Product Grid is usable on mobile width
- [ ] Insight Dashboard is usable on desktop width
- [ ] Insight Dashboard is usable on tablet width
- [ ] Insight Dashboard is usable on mobile width
- [ ] locale switch, sibling nav, and filter-summary visibility remain usable at smaller widths
- [ ] no blocker-level layout break prevents operator or public QA for the implemented routes

Note:
- this section can close the currently open `WBS 5.14` responsive QA slice without claiming anything about BX-PF publish readiness

---

## 7. Pass / Hold Rule

### 7.1 Interim Pass Meaning

This checklist can be marked `Pass` when:

- all FPDS-internal ingestion, review, approval, canonical persistence, public read, and admin visibility checks pass
- failures, if any, are limited to the known BX-PF-blocked surfaces that are already out of scope for this checklist

### 7.2 Hold Meaning

Mark this checklist `Hold` if:

- approved records do not persist correctly inside FPDS
- review decisions do not produce canonical product/version continuity
- public Product Grid or Insight Dashboard fail on FPDS-owned data
- audit, run, or change drilldowns break operator traceability
- responsive or locale behavior introduces blocker-level issues in the implemented Phase 1 surfaces

---

## 8. Evidence Pack for This Checklist

When this checklist is executed, capture at least:

- execution date
- environment name
- BX-PF mode/value used during testing
- commands actually run
- pass/fail result per section
- blocking issues
- representative screenshots
- sample ids for run, review task, product, product version, and audit event

Store the resulting evidence as a dated QA note under `docs/00-governance/` unless the Product Owner prefers a customer-facing summary artifact.

---

## 9. Next Step After This Checklist

Once BX-PF becomes ready, run a separate publish-focused checklist covering:

- connector execution
- publish item creation
- publish attempts
- retry scheduling
- reconciliation handling
- publish monitor UI
- release hardening and acceptance pack completion

This checklist is intentionally not a substitute for that later work.

---

## 10. Change History

| Date | Change |
|---|---|
| 2026-04-15 | Created the interim Phase 1 test checklist for use while BX-PF publish work is externally blocked |
