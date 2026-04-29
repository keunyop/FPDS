# FPDS Source Registry Operations Policy

Version: 1.2
Date: 2026-04-21
Status: Active Operating Baseline
Source Documents:
- `docs/02-requirements/FPDS_Requirements_Definition_v1_5.md`
- `docs/02-requirements/scope-baseline.md`
- `docs/01-planning/WBS.md`
- `docs/03-design/admin-information-architecture.md`
- `docs/03-design/workflow-state-ingestion-design.md`
- `docs/03-design/source-snapshot-evidence-storage-strategy.md`
- `docs/00-governance/decision-log.md`

---

## 1. Purpose

This document defines the Phase 1 operating policy for source registry management.

Goals:
- make source registry ownership explicit before implementation starts
- let operators manage bank and product coverage from the admin UI without editing repo JSON files
- keep collection runs reproducible even when registry entries are edited over time
- keep the first implementation intentionally small: bank management, source catalog management, and source-selected product collection

This is an operating-policy baseline, not an implementation approval by itself.

---

## 2. Baseline Decisions

1. The operational source of truth for the active source registry will be the FPDS database.
2. Admin operators will manage banks and source catalog coverage directly in the admin UI, while generated source rows remain system-managed except for admin-only removal that marks a bad row `removed`.
3. After the DB-backed source registry is introduced, `source_registry_catalog.json` and per-bank registry JSON files will no longer be the ongoing operational control surface.
4. The admin `collect` action means full product collection through candidate creation, not raw fetch only.
5. The first collection target is `normalized_candidate` plus normal validation/routing side effects such as `review_task` creation when rules require it.
6. Candidate-producing scope is controlled by registry role. `detail` sources are candidate-producing by default. Supporting sources may be included for evidence support, but they should not create standalone product candidates unless their registry role explicitly allows it.
7. Registry edits are direct operational changes, so they must be audit-visible.
8. The MVP stays intentionally narrow: no diff-heavy refresh approval workflow is required for the first admin-managed registry slice.

Short form:

`source registry is DB-backed, admin-managed, and collect means candidate-producing ingestion`

---

## 3. Why This Policy Was Chosen

### 3.1 Why Not Keep JSON as the Live Registry

Repo JSON files were useful to bootstrap the Big 5 registry baseline, but they are not a good long-term operator control surface.

Problems with JSON-as-operations:
- non-developers cannot safely manage it from the admin runtime
- edit history is tied to git workflow instead of operator workflow
- runtime state and operator action history drift apart
- launching collection from a selected source list becomes awkward if the true registry still lives in files

### 3.2 Why Bank and Catalog Editing Is Acceptable for MVP

The Product Owner explicitly prefers a minimal management flow over a heavier approval system.

That makes sense for the next slice because:
- the team needs a practical operator surface now, not a full registry governance product
- bank/profile editing plus catalog coverage management is simpler than candidate-diff plus promotion workflow
- it keeps focus on the immediate business value: maintain source scope and collect product candidates

### 3.3 Why Collect Should Produce Candidates

FPDS is not building a crawl archive for its own sake. The useful operator outcome is a reviewable product candidate.

Benefits:
- operators see whether a selected source actually leads to product candidates
- source management and operational outcome stay connected
- the admin console can link registry, run, candidate, and review flows directly

Tradeoff:
- the collection action is heavier than raw fetch-only collection
- quality guardrails matter more because supporting pages should not become noisy standalone candidates

That is why candidate-producing scope must stay registry-role-aware.

---

## 4. Minimum Registry Data Model

The DB-backed source registry should retain at least the following fields for generated or materialized source rows:

- `source_id`
- `bank_code`
- `country_code`
- `product_type`
- `product_key` or equivalent stable logical grouping key
- `source_name`
- `normalized_url`
- `source_type`
- `discovery_role`
- `status`
- `priority`
- `source_language`
- `last_verified_at`
- `last_seen_at`
- `change_reason`
- `redirect_target_url` when applicable
- `alias_urls` when applicable
- `created_at`
- `updated_at`

Minimum status vocabulary for the MVP:

| Status | Meaning | Default Collection Eligible |
|---|---|---|
| `active` | current approved source row | Yes |
| `inactive` | stored but not part of default collection scope | No |
| `deprecated` | historical row kept for traceability | No |
| `removed` | no longer operationally used | No |

Minimum role vocabulary for the MVP:

| Role | Meaning | Candidate-Producing |
|---|---|---|
| `detail` | primary product truth source | Yes |
| `supporting_html` | supporting page for fees/rates/terms | No by default |
| `supporting_pdf` | supporting governing/rates PDF | No by default |
| `entry` | listing/discovery page | No by default |

---

## 5. Minimal Admin Functions

The first admin-managed source registry slice should support only the following functions:

1. List and filter banks.
2. Create and edit bank profiles with auto-generated bank codes.
3. List and filter source catalog items by bank, product type, and status.
4. Create and edit source catalog items using controlled bank and product-type inputs.
5. Select one or more source catalog items and start collection.
6. See the resulting run id and success/failure summary.
7. Inspect generated source rows in the source registry surface.
8. Remove a bad generated source row by marking it `removed`, preserving audit and historical run context.

Current live workflow note:
- `/admin/banks` is now the primary operator-owned surface for bank setup, bank-owned coverage management, and collection launch.
- `/admin/source-catalog` may still exist as a compatibility route, but it is no longer the preferred primary workflow.
- bank list bulk collect is allowed as long as the action resolves to the underlying bank-plus-product coverage items.

Still deferred from the MVP:
- crawler-driven registry auto-promotion
- candidate-diff review UI for registry changes
- scheduler-level refresh governance UI
- visual diffing between historical registry versions

Current live product-type onboarding note:
- `/admin/product-types` now lets operators manage product type definitions with searchable name and description fields.
- Bank coverage creation validates against that registry instead of a hard-coded canonical list.
- Chequing, savings, GIC, and every later product type are all ordinary operator-managed DB rows. Collection must fail clearly when the requested product type row is missing or inactive.
- Product type code is an operator-managed identity field. When a code is corrected from the Product Types detail modal, the backend renames the registry row and cascades source catalog, generated source, candidate, canonical product, public projection, and taxonomy references instead of relying on aliases.
- Homepage-first discovery now carries the stored product type definition into AI-assisted detail-source resolution.
- Homepage-first discovery may infer a bounded discovery profile from the stored display name, description, and discovery keywords. For example, a registered `saving` row whose definition clearly describes savings accounts can use `savings` discovery signals, while generated source rows still preserve the registered product type code.
- the approved follow-on design now upgrades discovery quality through bounded AI parallel scoring, stronger product-type-description grounding, and page-level evidence scoring before `detail` promotion. See `docs/03-design/homepage-discovery-scoring-enhancement.md`.
- generated source rows now persist structured `discovery_metadata`, and `/admin/sources/:sourceId` exposes that explainability block for operator inspection.
- Operator-managed product types without specialized parser support continue through generic AI extraction/normalization fallback and are forced into manual review rather than public publish.

---

## 6. Collection Semantics

For this policy, `collect` means:

1. use the selected source rows as run scope
2. fetch and persist snapshots as needed
3. parse and chunk the fetched content
4. run extraction and normalization
5. persist `normalized_candidate`
6. run normal validation/routing behavior
7. create `review_task` rows when the candidate is not auto-clear

Important rules:
- the run must persist which source rows were selected so the collection scope is reproducible later
- `detail` sources are the default candidate-producing scope
- supporting sources may still be fetched and parsed during the same run if the registry metadata says they support a selected detail source
- supporting sources should not create primary standalone candidates unless the registry explicitly marks them as candidate-producing

---

## 7. JSON Retirement Rule

Current repo JSON registry files remain useful as historical baseline artifacts and migration input.

However, once the DB-backed admin-managed registry is introduced:
- operators do not manage live registry state through JSON anymore
- runtime collection must read the DB-backed registry state
- JSON files stop being the operational source of truth

This is an operations-policy change, not a requirement to immediately delete the historical files from the repository.

---

## 8. Current Repository State

Current repository state:
- the repo contains `source_registry_catalog.json` and per-bank registry JSON baselines
- the live admin runtime now includes `/admin/banks`, `/admin/source-catalog`, and `/admin/sources` with generated-source inspection plus admin-only soft remove
- operator-managed registry ownership now lives in `bank` and `source_registry_catalog_item`
- generated source detail lives in `source_registry_item`
- the live DB tables are now respected as-is at runtime, including intentionally empty reset states; committed JSON baselines remain import/reference material rather than an automatic runtime bootstrap path
- collection can now be started from the admin source catalog list and produces generated source rows, `normalized_candidate` rows, and normal review-routing side effects
- the worker execution path is still file/catalog oriented under the hood, so the API-side runner currently materializes temporary grouped registry files for the selected source scope
- candidate-producing scope is still role-aware, with selected `detail` sources as the primary scope and only the existing TD savings supporting-source merge path auto-included today
- operator-managed product type onboarding is now live, and its next discovery-quality improvements are documented in `docs/03-design/homepage-discovery-scoring-enhancement.md`

---

## 9. Non-Goals

The following are intentionally out of scope for the first source-registry admin slice:

- automatic source discovery that silently edits the active registry
- complex candidate-diff review UX for registry promotion
- generalized multi-bank supporting-source inference engine beyond what the existing pipeline already needs
- replacing run diagnostics, review queue, or change history with a source-centric workflow
- bulk destructive actions without audit visibility

---

## 10. Follow-On Work Remaining

- explicit DB import/export tooling for source-registry administration beyond first-boot seeding
- broader supporting-source auto-inclusion rules beyond the existing TD savings path
- dedicated collection-progress UX on the source surfaces instead of relying on the run views for deeper execution visibility
- optional scheduler or approval governance follow-ons if source-registry operations later need tighter release controls
- operator-managed product type registry with searchable `name` and `description`
- hybrid homepage discovery scoring that uses deterministic candidate generation, AI parallel scoring, and page-level evidence validation
- parser, normalization, validation, and vocabulary fallback rules for newly added product types

---

## 11. Change History

| Date | Change |
|---|---|
| 2026-04-10 | Initial source registry refresh and approval policy added |
| 2026-04-15 | Replaced the JSON-first approval baseline with a DB-backed admin-managed source registry baseline and defined `collect` as candidate-producing ingestion |
| 2026-04-15 | Refined the MVP so operators manage banks and source catalog coverage while generated source rows remain read-only |
| 2026-04-15 | Updated the policy after the `WBS 5.15` implementation so current-state notes now reflect the live DB-backed `/admin/sources` runtime |
| 2026-04-18 | Linked the approved homepage-discovery quality follow-on design and corrected the current-state note for live operator-managed product-type onboarding |
| 2026-04-18 | Recorded the first homepage-discovery explainability implementation slice on generated source rows and source-detail inspection |
| 2026-04-28 | Added admin-only generated source soft removal using `removed` status so bad collected source details can be excluded from future collection without losing audit history |
