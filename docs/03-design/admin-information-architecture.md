# FPDS Admin Information Architecture

Version: 1.1
Date: 2026-04-15
Status: Approved Baseline for WBS 1.7.4 plus source-registry follow-on
Source Documents:
- `docs/02-requirements/FPDS_Requirements_Definition_v1_5.md`
- `docs/01-planning/WBS.md`
- `docs/02-requirements/scope-baseline.md`
- `docs/03-design/api-interface-contracts.md`
- `docs/03-design/security-access-control-design.md`
- `docs/03-design/review-run-publish-audit-state-design.md`
- `docs/03-design/workflow-state-ingestion-design.md`
- `docs/03-design/source-registry-refresh-and-approval-policy.md`
- `docs/03-design/erd-draft.md`
- `docs/00-governance/decision-log.md`

---

## 1. Purpose

This document defines the admin console information architecture baseline.

Goals:
- keep admin navigation aligned to operator jobs instead of data-model internals
- separate triage, diagnosis, and mutation surfaces
- define where source registry management fits once the DB-backed registry slice starts

This is an IA and operator-workflow baseline, not a UI implementation approval by itself.

---

## 2. Baseline Decisions Carried Forward

1. The admin console is a browser-based operator surface protected by server-side session auth.
2. Review, runs, change history, audit, publish, usage, and dashboard health remain separate operator surfaces.
3. Source registry management is an operations surface, not a hidden settings page.
4. The first source-registry slice is intentionally minimal: bank setup plus bank-owned coverage management, while generated source rows are inspectable and may only be operator-removed through an audit-visible `removed` status transition.
5. Bulk collection may start from the bank list as long as the collect action still resolves down to the existing bank-plus-product coverage items.
6. Dynamic operator-defined product-type onboarding is a later slice because it needs explicit AI-assisted discovery, parser, and fallback contracts beyond the current canonical product set.
5. Collection launched from the source registry means candidate-producing ingestion through `normalized_candidate`, not raw fetch only.
6. `detail` sources are the default candidate-producing scope. Supporting sources may be included for evidence support, but should not create standalone primary candidates unless explicitly configured.
7. UI-owned labels and navigation support `en`, `ko`, and `ja`, while source-derived product text stays in source language.

---

## 3. Scope of This Baseline

Included:
- admin shell and primary navigation
- contextual route ownership
- overview, review, runs, change history, audit, publish, usage, dashboard health, bank registry, source catalog compatibility, source registry, and later product-type-management surfaces
- cross-surface drilldown rules
- role-visibility baseline
- responsive and localization baseline

Not included:
- exact component library implementation
- visual styling or motion details
- scheduler management UX
- registry diff-review workflow
- exact chart library, table virtualization, or pagination implementation

---

## 4. Information Architecture Principles

### 4.1 Triage First, Diagnosis Second, Mutation Last

- overview and list surfaces should help operators decide what needs attention
- detail surfaces should explain why something happened
- state-changing actions should live on the detail surface that owns the decision

### 4.2 One Primary Home Per Operational Entity

- `review_task` lives primarily in Review
- `run` lives primarily in Runs
- canonical change continuity lives primarily in Change History and Product Record
- publish tracking lives primarily in Publish Monitor
- usage and aggregate freshness live primarily in Observability
- source registry ownership lives primarily in Source Registry

### 4.3 Preserve Context on Drilldown

- list filters and search context should survive drilldown when practical
- detail surfaces should expose a clear path back to the owning list
- cross-links should move by stable ids, not only by display labels

### 4.4 Separate Current State from History

- current queue vs historical decisions
- current run summary vs failure history
- current approved product vs change chronology
- current active source row vs historical edit context

---

## 5. Admin Shell Baseline

### 5.1 Global Chrome

All admin surfaces should share:

1. collapsible primary sidebar
2. environment badge
3. top-bar route-group navigation on desktop with an active-route title on smaller screens
4. locale toggle
5. user/session menu anchored in the sidebar footer

### 5.2 Navigation Groups

| Group | Surface | Route Baseline | Purpose |
|---|---|---|---|
| Overview | Admin Overview Dashboard | `/admin` | operator triage |
| Review | Review Queue | `/admin/reviews` | review intake and decision workload |
| Operations | Banks | `/admin/banks` | bank profile setup, initial and ongoing product coverage management, and single-bank or multi-bank collection kickoff |
| Operations | Source Registry | `/admin/sources` | generated source inspection |
| Operations | Runs | `/admin/runs` | ingestion diagnostics |
| Operations | Change History | `/admin/changes` | canonical change chronology |
| Operations | Audit Log | `/admin/audit` | append-only actor/request trail |
| Operations | Publish Monitor | `/admin/publish` | BX-PF publish tracking |
| Observability | LLM Usage | `/admin/usage` | model/agent/run usage visibility |
| Observability | Dashboard Health | `/admin/health/dashboard` | public aggregate freshness and health |

### 5.3 Contextual Routes

| Surface | Route Baseline | Entry Path |
|---|---|---|
| Signup Request | `/admin/signup` | login screen, anonymous access-request flow |
| Review Detail / Trace Viewer | `/admin/reviews/:reviewTaskId` | review queue, run detail, search |
| Bank Detail | `/admin/banks/:bankCode` | bank list |
| Source Catalog Detail | `/admin/source-catalog/:catalogItemId` | compatibility redirect into bank detail |
| Source Registry Detail | `/admin/sources/:sourceId` | source registry list, source catalog detail, run detail, search |
| Product Type Management | `/admin/product-types` | operator-managed product type registry, bank coverage search, and dynamic onboarding controls |
| Run Detail | `/admin/runs/:runId` | runs list, review detail, usage drilldown, source collection history, search |
| Product Record | `/admin/products/:productId` | change history, publish monitor, review result context, search |

### 5.4 Reserved Follow-On Navigation

- `Localization Health` remains a possible future admin health surface
- broader scheduler or refresh governance remains a later source-operations slice
- `Product Type Management` is now the operator-owned registry surface for product type definitions used by bank coverage selection and homepage-first discovery

---

## 6. Global Search and Cross-Surface Drilldown

### 6.1 Search Baseline

Global search should support at least:

- `bank`
- `product name`
- `run id`
- `candidate id`
- `source id`
- `source URL`

Recommended result grouping:
- review task
- run
- product
- source

### 6.2 Search Routing Rules

- `run id` opens Run Detail
- `candidate id` opens Review Detail / Trace Viewer
- `source id` or source URL opens Source Registry Detail
- `product name` should prefer an active review task when one exists, otherwise the Product Record

### 6.3 Cross-Link Rules

| From | To | Why |
|---|---|---|
| Review Queue | Review Detail | decision and evidence inspection |
| Review Detail | Run Detail | producing run diagnostics |
| Review Detail | Product Record | approved continuity check |
| Source Registry | Run Detail | inspect collection result |
| Source Registry | Review Queue | inspect candidate/review outcome after collection |
| Run Detail | Related Review Tasks | inspect run-created review workload |
| Run Detail | LLM Usage | same-run cost drilldown |
| Change History | Product Record | inspect current truth vs chronology |
| Change History | Audit Log | inspect broader actor/request context |
| Publish Monitor | Product Record | inspect publish target context |

---

## 7. Surface Definitions

### 7.1 Admin Overview Dashboard

Purpose:
- first-stop triage surface after login
- for `admin`, also the first-stop approval surface for pending signup requests

Minimum widgets:
- total products
- products by bank
- products by type
- pending signup requests
- runs today/this week
- queued review count
- approval rate
- recent failures
- recently changed products
- dashboard refresh status
- metric aggregation health

### 7.2 Review Queue

Purpose:
- primary reviewer intake surface

Minimum filters:
- review state
- bank
- product type
- validation status
- created date range

Minimum columns:
- task id
- bank
- country
- product type
- product name
- issue summary
- confidence
- validation status
- created at
- status

### 7.3 Review Detail / Trace Viewer

Purpose:
- diagnosis and decision surface for one review task

Minimum panels:
- candidate summary
- normalized fields
- validation issues
- source evidence / trace
- decision form
- override diff preview
- action history

### 7.4 Source Registry Management

Purpose:
- own active source scope
- let operators manage banks and product coverage with minimal controlled inputs
- let operators inspect generated source rows after collection
- let operators start collection from bank-owned coverage items
- let operators start bulk collection from the bank list across multiple banks' attached coverage items
- reserve a later operator-managed product type surface for searchable product-type definitions that AI-assisted discovery can use

`/admin/sources` minimum list behavior:
- filter by bank, country, product type, status, role
- search by source id, source name, URL, product key
- expose drill-in for generated source rows, with admin-only removal for bad generated source details

Minimum row fields:
- source id
- bank
- product type
- source name
- source type
- discovery role
- status
- normalized URL
- last verified at
- updated at

`/admin/sources/:sourceId` minimum detail behavior:
- source metadata inspection
- role/status visibility
- admin-only remove action that marks the source `removed`
- recent collection history summary
- linked run drilldown

Rules:
- `/admin/banks` owns visible bank profile editing
- `/admin/banks` also owns bank/product-type coverage editing and collection launch
- `/admin/source-catalog` remains only as a compatibility redirect into the bank-owned workflow
- `/admin/product-types` owns all product-type definitions as operator-managed DB rows and is the source of truth for bank coverage option search
- product types without specialized parser support use the generic AI extraction/normalization fallback path and remain review-first rather than auto-publish
- `/admin/sources` and `/admin/sources/:sourceId` are generated-source inspection surfaces; destructive cleanup is limited to an admin-only soft remove that preserves audit and historical run context
- collection means full candidate-producing ingestion through `normalized_candidate`
- `detail` sources are candidate-producing by default
- supporting sources may be included for evidence support, but should not create standalone primary candidates unless explicitly configured

### 7.5 Runs Surface

Purpose:
- primary ingestion diagnostic surface

`/admin/runs` minimum list:
- run id
- run state
- started at
- completed at
- source count
- candidate count
- review queued count
- success/failure count
- partial completion flag
- error summary

`/admin/runs/:runId` minimum detail:
- run summary
- stage summary
- source processing summary
- failure section
- related review tasks
- usage summary

### 7.6 Change History and Product Record

Purpose:
- explain canonical change continuity

`/admin/changes` minimum list:
- change type
- summary
- changed fields
- detected at
- related review/run context

`/admin/products/:productId` minimum detail:
- product summary
- current approved version summary
- finalized evidence links
- change events
- publish summary

### 7.7 Audit Log

Purpose:
- append-only actor/request context trail

`/admin/audit` minimum list:
- event category
- event type
- occurred at
- actor
- target
- state transition
- reason
- request context

### 7.8 Publish Monitor

Purpose:
- BX-PF publish tracking surface

Minimum list information:
- publish item id
- canonical product id or product name
- product version id
- publish state
- pending/failure reason
- last attempted at
- attempt count
- target master id

### 7.9 LLM Usage Dashboard

Purpose:
- usage and cost observability

Minimum capabilities:
- model breakdown
- agent breakdown
- run breakdown
- time-range trend
- anomaly drilldown

### 7.10 Dashboard Health

Purpose:
- public aggregate freshness and health visibility

Minimum domain rows:
- `public_product_projection`
- `dashboard_metric_snapshot`
- `dashboard_ranking_snapshot`
- `dashboard_scatter_snapshot`

Minimum information:
- latest successful refresh time
- latest attempted refresh time
- refresh status
- stale flag
- missing-data ratio or equivalent completeness note
- cache TTL
- last error summary

---

## 8. Role Visibility Baseline

| Surface / Action | `admin` | `reviewer` | `read_only` | Notes |
|---|---:|---:|---:|---|
| Overview dashboard | O | O | O | read-only triage |
| Review queue list/detail read | O | O | O | trace read allowed |
| Review decision actions | O | O | X | approve/reject/edit/defer |
| Source registry list/detail read | O | O | O | source scope visibility and run drilldown |
| Source registry edit and collection start | O | X | X | direct registry mutation and collection kickoff |
| Runs and run detail | O | O | O | diagnostic read |
| Change history and product record | O | O | O | diagnostic read |
| Publish monitor read | O | O | O | operational visibility |
| Usage dashboard read | O | O | O | cost visibility |
| Dashboard health read | O | O | O | aggregate health visibility |

---

## 9. Responsive and Localization Baseline

### 9.1 Responsive Rules

- desktop-first layout
- review detail and source detail may use split-pane layouts on desktop
- tablet/mobile may collapse heavy diagnostic panes into tabs or stacked sections
- state badges, confidence, validation status, and role/status controls must remain visible on smaller screens

### 9.2 Localization Rules

- navigation, widget titles, status labels, filter labels, and help text use `en`, `ko`, and `ja`
- `product_name`, `description_short`, `eligibility_text`, `fee_waiver_condition`, evidence excerpts, and source names derived from source content may remain in source language

---

## 10. Follow-On Items

| Area | Follow-Up |
|---|---|
| i18n ownership / fallback | `docs/03-design/localization-governance-and-fallback-policy.md` |
| Admin login and route protection | `4.1` |
| Review queue / decision flow | `4.2`, `4.3` |
| Trace viewer implementation | `4.4` |
| Run status screen | `4.5` |
| Change history screen | `4.6` |
| Audit log implementation | `4.7` |
| Usage dashboard implementation | `4.8`, `4.9` |
| Publish monitor implementation | `6.4` |

---

## 11. Follow-On Work Unlocked

- `4.1`: admin login implementation
- `4.2`: review queue implementation
- `4.4`: evidence trace viewer implementation
- `4.5`: run status screen implementation
- `4.6`: change history implementation
- `4.7`: audit log implementation
- `4.9`: usage dashboard v1 implementation
- `5.12`: EN/KO/JA admin locale rollout
- `6.4`: publish monitor UI implementation

---

## 12. WBS Mapping

| WBS ID | Closure in This Document |
|---|---|
| 1.7.4 | Sections 2-11 |
| 5.15 | Sections 2, 5, 6, 7.4, 8, 10, 11 |

---

## 13. Change History

| Date | Change |
|---|---|
| 2026-04-06 | Initial admin information architecture baseline created for WBS 1.7.4 |
| 2026-04-13 | Added Audit Log as an operations surface with drilldown rules distinct from canonical change history |
| 2026-04-15 | Added Source Registry Management as an operations surface for DB-backed source editing and multi-select candidate collection kickoff |
| 2026-04-15 | Marked Source Registry Management as implemented in the live admin runtime and removed it from follow-on-only lists |
| 2026-04-22 | Added the anonymous signup-request route and admin-overview approval panel to the active operator IA |
