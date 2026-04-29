# FPDS Development Journal

Version: 1.2
Date: 2026-04-22
Status: Active
Source Documents:
- `docs/00-governance/working-agreement.md`
- `docs/01-planning/WBS.md`
- `docs/02-requirements/scope-baseline.md`

---

## 1. Purpose

This document is the short implementation memory for active work.

Rules:
- keep only recent slices that matter for safe resume
- move older historical context to stable status docs or archive
- record only the minimum needed to continue safely

Historical gate and prototype material now lives under `docs/archive/`.

---

## 2. Current Resume Context

As of `2026-04-22`:
- `WBS 5` is the active stage
- public grid, dashboard, locale rollout, source registry admin MVP, and operator-managed product type onboarding are already implemented
- recent work has focused on source collection hardening, aggregate refresh health, and registry state behavior
- `docs/archive/` now holds old gate notes, prototype planning docs, and prototype evidence artifacts

Read before coding:
1. `README.md`
2. `docs/README.md`
3. this journal
4. `docs/01-planning/WBS.md`
5. the relevant active design doc for the slice

---

## 3. Entry Template

```md
## YYYY-MM-DD - Slice Title

- WBS:
- Status:
- Goal:
- Why now:
- Outcome:
- Not done:
- Key files:
- Decisions:
- Verification:
- Known issues:
- Next step:
```

---

## 4. Recent Entries

## 2026-04-29 - Product Type Code Rename and Semantic Discovery Profile

- WBS: `5.15`, `5.16`, source collection quality hardening
- Status: `done`
- Goal: let operators correct a product type code such as `saving` to `savings` from the Product Types detail modal and prevent homepage discovery from depending only on the literal short code
- Why now: the Product Owner confirmed `Savings` is the correct product type name and reported that saving the Product Types detail modal still returned `Product type was not found`; the previous BMO collection also showed that singular `saving` was too weak for BMO savings discovery
- Outcome: Product Types detail and create modals now expose the product type code, update routes keep the modal on the renamed code after save, backend updates can rename `product_type_registry.product_type_code`, and the rename cascades existing source catalog, generated source, candidate, canonical product, public projection, and taxonomy references. Homepage discovery now derives a bounded semantic discovery profile from the stored display name, description, discovery keywords, and code terms, so a registered `saving` row whose definition clearly describes savings accounts can use `savings` discovery signals and a `gic-term-deposit` row can use `gic` seed discovery while generated rows still preserve the registered code. Follow-up runtime failures were fixed by accepting and recording the semantic discovery profile in `_score_candidate_links_with_ai`, preventing AI `irrelevant` scores from hard-vetoing curated seed detail sources before page evidence or seed fetch fallback can validate them, allowing curated seed detail sources to remain eligible when page evidence is low but not strongly negative, adding no-detail run summaries that include the first discovery note for easier diagnosis, and fixing HTML parse/chunk fallback so pages with empty `<main>` elements can still parse body/app content.
- Not done: no live BMO collection rerun was launched from this slice.
- Key files: `api/service/api_service/product_types.py`, `api/service/api_service/source_catalog.py`, `api/service/tests/test_product_types.py`, `api/service/tests/test_source_catalog.py`, `app/admin/src/components/fpds/admin/product-type-create-dialog-content.tsx`, `app/admin/src/components/fpds/admin/product-type-detail-dialog-content.tsx`, `app/admin/src/components/fpds/admin/product-type-registry-surface.tsx`, `app/admin/src/lib/admin-api.ts`
- Decisions: missing product type codes still fail clearly; FPDS does not silently alias an unregistered `savings` request to a `saving` row. The AI/semantic improvement applies after a registered product type row is found, keeping DB identity operator-owned and auditable.
- Verification:
  - `$env:PYTHONPATH='api/service'; api\service\.venv\Scripts\python.exe -m unittest api.service.tests.test_product_types api.service.tests.test_source_catalog api.service.tests.test_source_catalog_collection_runner api.service.tests.test_source_registry api.service.tests.test_source_collection_runner`
  - `$env:PYTHONPATH='api/service'; api\service\.venv\Scripts\python.exe -m unittest api.service.tests.test_source_catalog api.service.tests.test_source_catalog_collection_runner api.service.tests.test_product_types`
  - `python -m unittest worker.pipeline.tests.test_parse_chunk`
  - `$env:PYTHONPATH='api/service'; api\service\.venv\Scripts\python.exe -m compileall api/service/api_service`
  - `$env:PYTHONPATH='api/service'; api\service\.venv\Scripts\python.exe -m compileall worker/pipeline/fpds_parse_chunk`
  - `$env:PYTHONPATH='api/service'; api\service\.venv\Scripts\python.exe -m unittest discover -s api/service/tests/regression -p "test_*.py"`
  - `pnpm run typecheck` from `app/admin`
- Known issues: existing live data still needs the operator action or migration execution; update the Product Types row to code `savings` before launching a `savings` run, or launch collection against the registered `saving` row to exercise semantic discovery while preserving that code.
- Next step: restart the running API/worker process, then rerun BMO savings and BMO GIC-term-deposit source catalog collection.

## 2026-04-29 - Operator-Managed Product Type Registry Cleanup

- WBS: `5.15`, `5.16`, source collection quality hardening
- Status: `done`
- Goal: remove the remaining product-type alias/default behavior so chequing, savings, GIC, and later product types are all DB-registered operator-managed rows
- Why now: BMO savings collection first produced zero sources with `product_type=saving`, then failed with `Product type was not found`; the Product Owner clarified that silently treating `chequing`, `saving`, or `gic` as predefined runtime product types is the wrong product direction
- Outcome: removed runtime `saving -> savings` aliasing, removed in-memory product-type fallback rows, removed product-type legacy classification fields from API/admin DTOs, made collection plans and runners preserve the exact registered product type code, and changed product-type DB migration state so current fresh DBs no longer auto-insert chequing/savings/GIC rows
- Not done: no live DB migration or live BMO collection rerun was launched from this slice
- Key files: `api/service/api_service/product_types.py`, `api/service/api_service/source_catalog.py`, `api/service/api_service/source_registry.py`, `api/service/api_service/source_collection_runner.py`, `db/migrations/0007_dynamic_product_type_onboarding.sql`, `db/migrations/0013_operator_managed_product_types.sql`, `app/admin/src/lib/admin-api.ts`, `app/admin/src/lib/admin-product-types.ts`, `app/admin/src/app/admin/reviews/page.tsx`, `app/admin/src/app/admin/changes/page.tsx`, `app/admin/src/components/fpds/admin/review-queue-surface.tsx`, `app/admin/src/components/fpds/admin/change-history-surface.tsx`
- Decisions: superseded by the later code-rename entry above for operator correction flow; product type identity still comes from the DB row, not from aliases or runtime fallback.
- Verification:
  - `$env:PYTHONPATH='api/service'; api\service\.venv\Scripts\python.exe -m unittest api.service.tests.test_product_types api.service.tests.test_source_catalog api.service.tests.test_source_catalog_collection_runner api.service.tests.test_source_registry api.service.tests.test_source_collection_runner`
  - `$env:PYTHONPATH='api/service'; api\service\.venv\Scripts\python.exe -m compileall api/service/api_service`
  - `$env:PYTHONPATH='api/service'; api\service\.venv\Scripts\python.exe -m unittest discover -s api/service/tests/regression -p "test_*.py"`
  - `pnpm run typecheck` from `app/admin`
  - `git diff --check` passed with existing CRLF conversion warnings only
- Known issues: existing environments that already applied old `0007` may still have chequing/savings/GIC rows as normal data; apply `0013_operator_managed_product_types.sql` to remove the legacy classification column, then manage those rows from `/admin/product-types`
- Next step: apply the new DB migration, confirm the intended BMO product type code exists and is active in `/admin/product-types`, then rerun BMO savings source catalog collection

## 2026-04-29 - BMO Savings Product-Type Registry Diagnosis

- WBS: `5.15`, `5.16`, source collection quality hardening
- Status: `done`
- Goal: fix BMO savings source-catalog runs that completed with zero source items and the warning `Homepage discovery produced no detail sources eligible for collection`
- Why now: the Product Owner reported a BMO savings run where source catalog collection used `product_type=saving`, produced no source rows, and matched the earlier BMO chequing zero-source failure pattern
- Outcome: confirmed the failed run plan originally used singular `saving`; after API restart, the next run used `savings` but failed because the live DB had no matching `product_type_registry` row. A short-lived alias/fallback approach was rejected by the Product Owner and superseded by the operator-managed cleanup above.
- Not done: no live BMO savings collection rerun was launched from this slice; existing DB catalog rows that already display `saving` are not force-migrated.
- Key files: `api/service/api_service/source_catalog.py`, `api/service/api_service/source_catalog_collection_runner.py`, `api/service/api_service/product_types.py`, `api/service/tests/test_source_catalog.py`, `api/service/tests/test_source_catalog_collection_runner.py`, `api/service/tests/test_product_types.py`
- Decisions: superseded by the later cleanup entry; product type identity now comes from the DB row, not from aliases or runtime fallback.
- Verification:
  - `$env:PYTHONPATH='api/service'; api\service\.venv\Scripts\python.exe -m unittest api.service.tests.test_source_catalog api.service.tests.test_source_catalog_collection_runner`
  - `$env:PYTHONPATH='api/service'; api\service\.venv\Scripts\python.exe -m unittest api.service.tests.test_source_catalog api.service.tests.test_source_catalog_collection_runner api.service.tests.test_source_registry api.service.tests.test_product_types api.service.tests.test_source_collection_runner`
  - `$env:PYTHONPATH='api/service'; api\service\.venv\Scripts\python.exe -m unittest api.service.tests.test_product_types api.service.tests.test_source_catalog api.service.tests.test_source_catalog_collection_runner`
  - `$env:PYTHONPATH='api/service'; api\service\.venv\Scripts\python.exe -m unittest api.service.tests.test_source_catalog api.service.tests.test_source_catalog_collection_runner api.service.tests.test_source_registry api.service.tests.test_product_types api.service.tests.test_source_collection_runner`
  - `$env:PYTHONPATH='api/service'; api\service\.venv\Scripts\python.exe -m compileall api/service/api_service`
  - `$env:PYTHONPATH='api/service'; api\service\.venv\Scripts\python.exe -m unittest discover -s api/service/tests/regression -p "test_*.py"`
  - `git diff --check` passed with existing CRLF conversion warnings only
- Known issues: operator-visible catalog records created with `saving` must match an active `saving` DB row or be edited to the intended active product type code.
- Next step: use the cleanup entry above as the current implementation state.

## 2026-04-29 - Source Catalog AI Usage Persistence

- WBS: `4.5`, `4.8`, `5.15`
- Status: `done`
- Goal: make Run Detail token and cost totals include the OpenAI homepage parallel scorer used during source catalog collection
- Why now: the Product Owner reported a BMO chequing source-catalog run where usage records and model executions were counted, but token and cost totals stayed at zero even though homepage discovery used AI scoring
- Outcome: source catalog materialization now carries the run context into homepage generation, captures OpenAI Responses API usage from the bounded homepage scorer, persists a `source_catalog_collection` `model_execution` row and linked `llm_usage_record`, and lets the existing Run Detail usage aggregation include those tokens and estimated cost. Heuristic extraction, normalization, and validation rows remain zero-token records because they do not make paid model calls.
- Not done: already-completed historical runs are not backfilled because the stored discovery metadata does not include provider response usage; rerun collection to produce nonzero scorer usage on new runs.
- Key files: `api/service/api_service/source_catalog.py`, `api/service/api_service/source_catalog_collection_runner.py`, `api/service/tests/test_source_catalog.py`, `api/service/tests/test_source_catalog_collection_runner.py`
- Decisions: kept Run Detail aggregation unchanged because it was summing stored rows correctly; fixed the missing source-catalog AI usage writer instead of estimating tokens from saved discovery notes.
- Verification:
  - `$env:PYTHONPATH='api/service'; api\service\.venv\Scripts\python.exe -m unittest api.service.tests.test_source_catalog api.service.tests.test_source_catalog_collection_runner api.service.tests.test_run_status api.service.tests.test_llm_usage`
  - `python -m unittest worker.pipeline.tests.test_extraction worker.pipeline.tests.test_normalization worker.pipeline.tests.test_validation_routing`
  - `$env:PYTHONPATH='api/service'; api\service\.venv\Scripts\python.exe -m compileall api/service/api_service`
  - `$env:PYTHONPATH='api/service'; api\service\.venv\Scripts\python.exe -m unittest api.service.tests.test_ops_scenario_qa api.service.tests.test_source_collection_runner api.service.tests.test_review_detail`
  - `$env:PYTHONPATH='api/service'; api\service\.venv\Scripts\python.exe -m unittest discover -s api/service/tests/regression -p "test_*.py"`
  - `$env:PYTHONPATH='api/service'; api\service\.venv\Scripts\python.exe -m unittest discover -s api/service/tests -p "test_*.py"`
- Known issues: local source-catalog AI usage will still be zero when the OpenAI provider or API key is not configured; in that case the discovery note continues to explain that the scorer was unavailable.
- Next step: rerun the BMO chequing source catalog collection and confirm Run Detail shows an added `Source Catalog Collection` usage stage with nonzero tokens/cost when the AI scorer runs.

## 2026-04-29 - Admin Operator Focus and Overflow Polish

- WBS: `4.2`, `4.3`, `4.6`, `4.7`, `4.9`, `5.14`, admin responsive polish
- Status: `done`
- Goal: reduce Audit Log, Review Queue, Review Detail, Usage, and Dashboard Health to operator-relevant primary information; keep Audit Log, Review Queue, and Usage bodies inside the application shell; remove extra outer snapshot cards on Audit Log, Change History, Review Queue, and Usage
- Why now: the Product Owner reported several admin pages were noisy for admin users, table-heavy bodies could exceed the shell width, and snapshot sections had an unnecessary wrapper card around their stat cards
- Outcome: `Stats5` now supports a frameless mode used by the requested snapshot sections. Audit Log, Review Queue, and Usage now add route-level `min-w-0` containment and internal table scroll boundaries. Audit Log hides lower-level request, retention, role-snapshot, and target-id details from the main table. Review Queue hides country, updated, candidate-state, and action-helper noise from the list. Review Detail hides snapshot and parsed-document ids plus verbose section descriptions. Usage removes the top coverage/density helper panel, trims model/anomaly tables, and keeps cost/token concentration plus review/run drilldowns. Dashboard Health hides snapshot/request identifiers and the explanatory definition block while keeping freshness, queue, latest attempt, and retry controls.
- Not done: no browser screenshot QA was run; use the running admin dev server to visually confirm the density and horizontal-scroll behavior with live data.
- Key files: `app/admin/src/components/stats5.tsx`, `app/admin/src/components/fpds/admin/audit-log-surface.tsx`, `app/admin/src/components/fpds/admin/review-queue-surface.tsx`, `app/admin/src/components/fpds/admin/review-detail-surface.tsx`, `app/admin/src/components/fpds/admin/llm-usage-surface.tsx`, `app/admin/src/components/fpds/admin/health-dashboard-surface.tsx`, `app/admin/src/components/fpds/admin/change-history-surface.tsx`, `app/admin/README.md`, `docs/03-design/ui-override-register.md`
- Decisions: kept API payloads unchanged and treated this as presentation-only operator focus; advanced diagnostic fields can return later through a dedicated advanced drawer instead of occupying the primary table/body.
- Verification:
  - `pnpm run typecheck` in `app/admin`
  - `pnpm run build` in `app/admin`
  - `.venv\Scripts\python.exe -m unittest discover -s tests/regression -p "test_*.py"` in `api/service`
  - `git diff --check`
  - existing admin dev server listener confirmed on port `3001`
- Known issues: the worktree already contained unrelated prior source-catalog/API, admin auto-refresh, timestamp, public UI, and local `tmp/` run-artifact changes; this slice did not revert them.
- Next step: browser-check `/admin/audit`, `/admin/reviews`, `/admin/reviews/:reviewTaskId`, `/admin/usage`, `/admin/changes`, and `/admin/health/dashboard` at desktop and mobile widths with live data.

## 2026-04-29 - Runs Operator Focus and Fixed Timestamp Format

- WBS: `4.5`, admin operations polish
- Status: `done`
- Goal: reduce Runs and Run Detail to operator-relevant information and make admin-owned date/time rendering deterministic
- Why now: the Product Owner asked for Runs surfaces to show only information an admin user needs and for dates/times across screens to use fixed `yyyy-mm-dd`, `hh:mm`, and `hh:mm:ss` formats when seconds are shown
- Outcome: `/admin/runs` now omits lower-value list columns for correlation, actor, and retry chain while keeping run id, type/trigger, state, time window, source counts, candidate/review counts, error summary, and detail drilldown. `/admin/runs/:runId` now keeps the main diagnostic sections but hides lower-level source document, snapshot, parsed-document, safe metadata, runtime-note, request-id, and source-id details from the primary view. Admin and public date/timestamp rendering now emits fixed `yyyy-mm-dd` or `yyyy-mm-dd hh:mm`, with explicit second precision for source-registry timestamps.
- Not done: no browser screenshot QA was run; verify the resulting density with live run data during the next admin dev-server pass.
- Key files: `app/admin/src/lib/admin-i18n.ts`, `app/admin/src/components/fpds/admin/run-status-surface.tsx`, `app/admin/src/components/fpds/admin/run-detail-surface.tsx`, admin date/timestamp surface components, `app/public/src/components/fpds/public/product-grid-surface.tsx`, `app/public/src/components/fpds/public/dashboard-surface.tsx`, `app/admin/README.md`, `app/public/README.md`, `docs/03-design/ui-override-register.md`
- Decisions: kept API payloads unchanged and reduced only UI presentation so advanced diagnostics remain available for future route-specific drilldowns if needed.
- Verification:
  - `pnpm run typecheck` in `app/admin`
  - `pnpm run build` in `app/admin`
  - `pnpm run typecheck` in `app/public`
  - `pnpm run build` in `app/public`
  - `.venv\Scripts\python.exe -m unittest discover -s tests/regression -p "test_*.py"` in `api/service`
- Known issues: the worktree already contained unrelated prior source-catalog/API and admin auto-refresh modifications plus local `tmp/` run artifacts; this slice did not revert them.
- Next step: browser-check `/admin/runs`, `/admin/runs/:runId`, and timestamp-heavy admin routes against live data at desktop and mobile widths.

## 2026-04-29 - Runs Shell Width and Snapshot Polish

- WBS: `4.5`, `5.14`, admin responsive polish
- Status: `done`
- Goal: keep the Runs body inside the application shell width and simplify the Run Snapshot visual structure
- Why now: the Product Owner observed that `/admin/runs` could push past the shell width and that the Run Snapshot did not need an extra outer card around its metric cards
- Outcome: added `min-w-0` containment to the admin shell content lane, constrained the Runs surface/table card so wide diagnostics scroll inside the card, and replaced the Runs `Stats5` snapshot wrapper with direct white stat cards matching the registry summary-card pattern.
- Not done: no route-specific column hiding or mobile card variant was added; the current fix keeps the table as an internally scrollable diagnostic table.
- Key files: `app/admin/src/components/application-shell5.tsx`, `app/admin/src/components/fpds/admin/run-status-surface.tsx`, `app/admin/README.md`, `docs/03-design/ui-override-register.md`
- Decisions: used shell-level containment for all admin pages plus a Runs-specific table boundary instead of narrowing diagnostic columns or changing shared table primitives.
- Verification:
  - `pnpm run typecheck` in `app/admin`
  - `pnpm run build` in `app/admin`
  - `.venv\Scripts\python.exe -m unittest discover -s tests/regression -p "test_*.py"` in `api/service`
- Known issues: browser responsive QA was not run in this slice; verify `/admin/runs` with live data at desktop and mobile widths during the next admin dev-server pass.
- Next step: continue responsive QA on other table-heavy admin routes if any still show horizontal page overflow after the shell containment change.

## 2026-04-28 - Admin Table Auto Refresh

- WBS: `4.5`, `5.15`, admin operations polish
- Status: `done`
- Goal: let Runs and other admin table/list screens reflect server-side status changes without requiring operators to press `Search`
- Why now: the Product Owner observed that `/admin/runs` only showed run status changes after a manual Search action
- Outcome: added a small FPDS-owned `AdminTableAutoRefresh` client wrapper that periodically calls `router.refresh()` only while the page is visible and no form control is being edited. Mounted it on the admin table/list surfaces for reviews, runs, changes, audit, usage, health, banks, product types, source catalog, and generated sources.
- Not done: no resource-specific polling endpoint, websocket, or row-level live update system was added; route-level refresh is intentionally the simple implementation
- Key files: `app/admin/src/components/fpds/admin/admin-table-auto-refresh.tsx`, `app/admin/src/components/fpds/admin/*-surface.tsx`, `app/admin/README.md`, `docs/03-design/ui-override-register.md`
- Decisions: kept the interval refresh as a client-only wrapper because existing server data fetches already use `cache: "no-store"` and `router.refresh()` can reuse the current route/search params safely
- Verification:
  - `pnpm run typecheck` in `app/admin`
  - `.venv\Scripts\python.exe -m unittest discover -s tests/regression -p "test_*.py"` in `api/service`
  - `pnpm run build` in `app/admin`
- Known issues: browser QA was not part of the implementation pass; responsive/live-data confirmation should happen during the next admin dev-server pass
- Next step: verify `/admin/runs` during an active collection run and confirm the table status changes without pressing `Search`

## 2026-04-28 - BMO Seed Detail Ordering Fix

- WBS: `5.15`, source collection quality hardening
- Status: `done`
- Goal: fix the repeated BMO chequing source-catalog run outcome where no source rows were materialized after source cleanup
- Why now: the Product Owner reran BMO chequing collection and still saw `Homepage discovery produced no detail sources eligible for collection`
- Outcome: confirmed BMO chequing seed detail hints load from the committed registry, but homepage candidates could displace seed details from the page-evidence evaluation window and BMO detail pages were rejected because broad page text triggered negative terms. Seed detail hints now evaluate ahead of non-seed homepage candidates, curated seed detail can promote when page evidence meets the minimum score even if broad page text has negative terms, and non-seed detail promotion is suppressed when seed detail hints are present.
- Not done: no live BMO collection run was launched from this slice
- Key files: `api/service/api_service/source_catalog.py`, `api/service/tests/test_source_catalog.py`
- Decisions: treated curated seed detail rows as the authoritative recovery path for BMO chequing; homepage-discovered non-seed detail candidates remain available only when there are no seed detail hints
- Verification:
  - `.venv\Scripts\python.exe -m unittest tests.test_source_catalog` in `api/service`
  - local `_generate_sources_from_homepage` check now returns 5 BMO chequing detail source ids: `BMO-CHQ-002`, `BMO-CHQ-003`, `BMO-CHQ-004`, `BMO-CHQ-005`, `BMO-CHQ-008`
  - `.venv\Scripts\python.exe -m unittest discover -s tests/regression -p "test_*.py"` in `api/service`
  - `git diff --check`
- Known issues: the generated entry row can still point at the best discovered hub URL rather than the committed entry URL, but it is not candidate-producing; revisit only if source list operator clarity requires exact seed entry retention
- Next step: rerun BMO chequing source catalog collection after this patch is on the running API/worker code path

## 2026-04-28 - BMO Seed Detail Fetch Fallback

- WBS: `5.15`, source collection quality hardening
- Status: `done`
- Goal: restore BMO chequing source materialization after deleting collected source rows and rerunning source catalog collection
- Why now: the latest BMO chequing run completed with partial completion and no source items because homepage discovery had no existing active detail scope and dropped seed detail hints when page-evidence fetch was unavailable
- Outcome: seed-backed detail sources now remain eligible for materialization when page evidence fetch is unavailable. The generated source row records `selection_path=seed_hint_fetch_unavailable`, keeps the fetch error in discovery metadata, and proceeds to downstream source collection where snapshot capture can succeed or fail with source-level diagnostics.
- Not done: no live rerun was launched after this code fix
- Key files: `api/service/api_service/source_catalog.py`, `api/service/tests/test_source_catalog.py`
- Decisions: allowed this fallback only for curated seed detail hints; non-seed homepage candidates still require evidence validation or AI/detail signals before promotion
- Verification:
  - `.venv\Scripts\python.exe -m unittest tests.test_source_catalog` in `api/service`
  - `cmd /c npm run typecheck` in `app/admin`
  - `.venv\Scripts\python.exe -m unittest discover -s tests/regression -p "test_*.py"` in `api/service`
  - `git diff --check`
- Known issues: the run log under `tmp/source-catalog-collections/` is local evidence from the failed live run and was not removed
- Next step: rerun BMO chequing source catalog collection; if snapshot fetch fails later, Run Detail should show per-source failures instead of zero source scope

## 2026-04-28 - Source Detail Soft Remove

- WBS: `5.15`, source registry admin operations
- Status: `done`
- Goal: add an operator-safe way to delete bad generated Source Detail rows before rerunning collection
- Why now: the BMO chequing source audit found unrelated generated source details, and the Product Owner needs cleanup without manually editing the database
- Outcome: added admin-only `DELETE /api/admin/sources/{source_id}` that marks a source row `removed` and writes a `source_registry_item_removed` audit event. Source Detail now shows a shared destructive confirmation action for admins, proxies the delete through Next.js with CSRF, and returns to the Sources list after success. Homepage source materialization now avoids inactivating `removed` rows and preserves `removed` status on upsert so a recollect does not silently reactivate an operator-suppressed URL.
- Not done: no live BMO source rows were removed and no live BMO recollection was launched in this slice
- Key files: `api/service/api_service/source_registry.py`, `api/service/api_service/main.py`, `api/service/api_service/source_catalog.py`, `app/admin/src/components/fpds/admin/source-detail-surface.tsx`, `app/admin/src/app/admin/sources/[sourceId]/delete/route.ts`
- Decisions: implemented delete as a soft remove because source evidence and collection history must remain auditable; kept bulk deletion out of scope until there is a stronger review flow and reason capture
- Verification:
  - `.venv\Scripts\python.exe -m unittest tests.test_source_registry tests.test_source_catalog` in `api/service`
  - `cmd /c npm run typecheck` in `app/admin`
  - `cmd /c npm run build` in `app/admin`
  - `.venv\Scripts\python.exe -m unittest discover -s tests/regression -p "test_*.py"` in `api/service`
  - `git diff --check`
- Known issues: Source Detail currently uses the English fallback copy for all locales after replacing a corrupted local copy block; broader KO/JA copy restoration should be handled as a focused localization slice
- Next step: remove the bad BMO chequing generated rows from `/admin/sources`, then rerun BMO chequing collection from the source catalog or bank coverage action

## 2026-04-28 - BMO Chequing Source Discovery Hardening

- WBS: `5.15`, `5.16`, source collection quality hardening
- Status: `done`
- Goal: verify the BMO chequing generated source set, remove unrelated generated sources, and restore complete current chequing product detail coverage
- Why now: the Product Owner found a BMO chequing generated-source set containing savings pages, a corporate Modern Slavery PDF, a numeric footnote source name, and no actual chequing detail pages
- Outcome: verified BMO's current public chequing lineup as Practical, Plus, Performance, Premium, and AIR MILES. Updated the BMO chequing seed registry to current `/en-ca/` detail URLs and added the missing AIR MILES detail source. Homepage discovery now preserves seeded supporting sources only after detail sources are promoted, filters unrelated product-family links such as savings pages from chequing support, rejects corporate/legal PDFs such as Modern Slavery statements, and prevents supporting links from being promoted to detail without AI detail confirmation or seed alignment.
- Not done: no live admin rerun was launched in this slice; existing DB rows generated before this change still need a fresh BMO chequing collection run or operator cleanup to disappear from `/admin/sources`
- Key files: `api/service/api_service/source_catalog.py`, `api/service/tests/test_source_catalog.py`, `worker/discovery/data/bmo_chequing_source_registry.json`, `worker/discovery/tests/test_registry_catalog.py`
- Decisions: treated student, senior, newcomer, kids/teens, Indigenous, family, and defence pages as audience/program support rather than standalone chequing products because BMO's chequing navigation and product lineup list the five account plans above as the current product set
- Verification:
  - `.venv\Scripts\python.exe -m unittest tests.test_source_catalog tests.test_source_catalog_collection_runner tests.test_source_collection_runner` in `api/service`
  - `python -m unittest worker.discovery.tests.test_registry_catalog`
  - `.venv\Scripts\python.exe -m unittest discover -s tests/regression -p "test_*.py"` in `api/service`
  - `git diff --check`
- Known issues: the local worktree already contains unrelated admin/readme/i18n-style modifications from prior slices; this slice did not touch or normalize them
- Next step: rerun BMO chequing source catalog collection from the admin workflow and confirm generated rows now include the five detail sources plus seeded support, with previous unrelated rows deprecated or regenerated away

## 2026-04-28 - Sources Search and Detail Density Polish

- WBS: `5.15`, `5.16`, admin UI polish
- Status: `done`
- Goal: remove the unnecessary Sources page `Manage banks` header action, rename admin search/filter submit buttons to `Search`, format generated-source Updated timestamps as `yyyy-mm-dd hh:mm:ss`, and reduce Source Detail to operator-relevant information
- Why now: the Product Owner asked for lower-friction Sources navigation, clearer search action wording, deterministic source-list timestamp display, and a less noisy Source Detail screen
- Outcome: Sources no longer shows the header bank-management shortcut. Admin search/filter submit actions on reviews, runs, changes, audit, usage, banks, product types, source catalog, and generated sources now read `Search`. Generated source list Updated values use a fixed datetime format. Source Detail now emphasizes source identity, URL, role/status, verification/update timestamps, a compact discovery summary, and linked recent collection runs instead of exposing lower-level registry and scoring internals.
- Not done: no browser/responsive QA was run in this slice; verification covered TypeScript/build and API regression tests
- Key files: `app/admin/src/components/fpds/admin/source-registry-surface.tsx`, `app/admin/src/components/fpds/admin/source-detail-surface.tsx`, admin list/filter surface components, `app/admin/README.md`, `docs/03-design/ui-override-register.md`
- Decisions: kept generated source inspection read-only and did not reintroduce bank-management actions on the Sources route; retained a compact discovery explanation rather than removing discovery context entirely because operators still need to understand why a source was promoted
- Verification:
  - `pnpm run typecheck` in `app/admin`
  - `pnpm run build` in `app/admin`
  - `.venv\Scripts\python.exe -m unittest discover -s tests/regression -p "test_*.py"` in `api/service`
  - `git diff --check`
- Known issues: browser QA is still needed to confirm Source Detail density and button wording across EN/KO/JA locales with live data
- Next step: browser-check `/admin/sources`, `/admin/sources/:sourceId`, and the main admin search/filter routes after the next local dev-server pass

## 2026-04-28 - Bank Coverage Copy and Sources Overflow Polish

- WBS: `5.15`, `5.16`, admin UI polish
- Status: `done`
- Goal: simplify the Bank detail coverage copy, shorten the single product-type collection queued message, and stop the generated Sources table from pushing wider than the application shell
- Why now: the Product Owner identified one unnecessary Bank detail helper paragraph, overly long queued feedback after product-type collection, and a Sources page overflow issue
- Outcome: Bank detail coverage no longer renders the explanatory paragraph about product-family selection and homepage-generated URLs. Single coverage queued feedback now returns only the concise queued sentence. The generated Sources route now adds `min-w-0` containment, table-card overflow clipping, URL/name wrapping, and an internal horizontal scroll boundary so wide rows stay inside the shell.
- Not done: no browser visual QA was run in this slice; verification covered TypeScript/build and API regression tests
- Key files: `app/admin/src/components/fpds/admin/bank-coverage-section.tsx`, `app/admin/src/components/fpds/admin/source-registry-surface.tsx`, `app/admin/README.md`, `docs/03-design/ui-override-register.md`
- Decisions: kept the change in FPDS-owned wrapper components rather than altering shared shell or table primitives; did not remove the underlying locale copy keys that may be cleaned up during a later locale-file pass
- Verification:
  - `pnpm run typecheck` in `app/admin`
  - `pnpm run build` in `app/admin`
  - `.venv\Scripts\python.exe -m unittest discover -s tests/regression -p "test_*.py"` in `api/service`
- Known issues: browser/responsive QA is still needed to confirm the Sources table behavior against real long URLs at desktop and mobile widths
- Next step: browser-check `/admin/banks` and `/admin/sources` with live generated-source data

## 2026-04-28 - Registry Summary Card White Background

- WBS: `5.15`, `5.16`, admin UI polish
- Status: `done`
- Goal: make the Banks summary cards use white backgrounds and apply the same treatment to similar Product Types and Sources summary cards
- Why now: the Product Owner wanted the top registry metric cards to read as white cards instead of blending into the admin canvas
- Outcome: Banks, Product Types, generated Sources, and Source Catalog summary `StatCard` components now use explicit `bg-white` card surfaces while preserving existing borders, typography, and layout density.
- Not done: no browser visual QA was run in this slice; verification covered TypeScript/build and API regression tests
- Key files: `app/admin/src/components/fpds/admin/bank-registry-surface.tsx`, `app/admin/src/components/fpds/admin/product-type-registry-surface.tsx`, `app/admin/src/components/fpds/admin/source-registry-surface.tsx`, `app/admin/src/components/fpds/admin/source-catalog-surface.tsx`, `app/admin/README.md`, `docs/03-design/ui-override-register.md`
- Decisions: kept the change local to existing registry `StatCard` wrappers instead of introducing a shared metric-card abstraction for a four-line visual adjustment
- Verification:
  - `cmd /c npm run typecheck` in `app/admin`
  - `cmd /c npm run build` in `app/admin`
  - `.venv\Scripts\python.exe -m unittest discover -s tests/regression -p "test_*.py"` in `api/service`
- Known issues: none observed in the final diff; an initial unrelated `app/admin/next-env.d.ts` modification was not touched by this slice and is no longer present in final status
- Next step: browser-check `/admin/banks`, `/admin/product-types`, `/admin/sources`, and `/admin/source-catalog` to confirm the white summary cards against live admin data

## 2026-04-26 - Bank Detail Modal Simplification

- WBS: `5.15`, admin UI polish
- Status: `done`
- Goal: remove unnecessary Bank detail information, make coverage counts read as product types, and remove the visible Bank profile Change reason field
- Why now: the Product Owner wanted the Bank detail modal to be simpler and corrected the coverage unit from generic items to product types
- Outcome: the Bank detail summary now shows only Bank code and Coverage, with coverage rendered as product type counts in EN/KO/JA. The Bank profile card no longer shows the explanatory homepage/discovery paragraph, and the profile form no longer renders a Change reason input while preserving the existing hidden `change_reason` payload default for API compatibility.
- Not done: no browser visual QA was run in this slice; verification covered TypeScript/build and API regression tests
- Key files: `app/admin/src/components/fpds/admin/bank-detail-dialog-content.tsx`, `app/admin/README.md`, `docs/03-design/ui-override-register.md`
- Decisions: kept this as an FPDS wrapper/content simplification instead of changing shared modal primitives or backend update contracts
- Verification:
  - `cmd /c npm run typecheck` in `app/admin`
  - `cmd /c npm run build` in `app/admin`
  - `.venv\Scripts\python.exe -m unittest discover -s tests/regression -p "test_*.py"` in `api/service`
- Known issues: the worktree already contained unrelated modified admin/API/i18n files before this slice; this slice did not normalize those broader changes
- Next step: browser-check `/admin/banks` to confirm the reduced Bank detail summary and profile form density against live data

## 2026-04-26 - Bank and Product Type Registry Density Follow-up

- WBS: `5.15`, `5.16`, admin UI polish
- Status: `done`
- Goal: reduce duplicated top-level add actions, make bank add/detail modals slightly narrower, and remove the visible Change reason field from Add bank
- Why now: the Product Owner wanted the Banks and Product Types screens to rely on list-local add actions and asked for a simpler Add bank modal
- Outcome: Banks and Product Types no longer pass add buttons into the shared page header; their add buttons remain in the list toolbar. `offer-modal4` now has a `width="medium"` option, and Bank add/detail modals use it while Product Type modals keep `width="narrow"` and source-catalog modals keep the default width. Add bank no longer renders a Change reason input, while the create payload still sends the existing empty `change_reason` default.
- Not done: no browser visual QA was run in this slice; verification covered TypeScript/build and API regression tests
- Key files: `app/admin/src/components/offer-modal4.tsx`, `app/admin/src/components/fpds/admin/bank-registry-surface.tsx`, `app/admin/src/components/fpds/admin/bank-create-dialog-content.tsx`, `app/admin/src/components/fpds/admin/product-type-registry-surface.tsx`, `app/admin/README.md`, `docs/03-design/shadcnblocks-adoption-log.md`, `docs/03-design/ui-override-register.md`
- Decisions: kept Add bank's `change_reason` form state as an empty backend-compatible field instead of changing the API contract; kept source-catalog modals at the wider default because their detail views remain denser
- Verification:
  - `cmd /c npm run typecheck` in `app/admin`
  - `cmd /c npm run build` in `app/admin`
  - `.venv\Scripts\python.exe -m unittest discover -s tests/regression -p "test_*.py"` in `api/service`
- Known issues: the worktree already contained unrelated modified admin/API/i18n files before this slice; this slice did not normalize those broader changes
- Next step: browser-check `/admin/banks` and `/admin/product-types` for modal width, toolbar action placement, and mobile wrapping

## 2026-04-26 - Product Type Modal Delete Polish

- WBS: `5.16`, admin UI polish
- Status: `done`
- Goal: simplify the Product Type delete confirmation, close the Product Type detail modal automatically after successful delete, and make Product Type add/detail dialogs slightly narrower
- Why now: the Product Owner reported that the delete prompt felt too complex, deletion left the detail modal open, and the Product Type modals had more horizontal space than needed
- Outcome: the shared destructive confirmation dialog now renders a compact title, description, and action row; Product Type delete success now clears the parent detail modal state before refreshing the list; `offer-modal4` has a scoped `width="narrow"` option used by Product Type add/detail only, leaving bank and source-catalog dialog widths unchanged
- Not done: no browser visual QA was run in this slice; verification covered TypeScript/build and API regression tests
- Key files: `app/admin/src/components/offer-modal4.tsx`, `app/admin/src/components/fpds/admin/destructive-confirm-dialog.tsx`, `app/admin/src/components/fpds/admin/product-type-registry-surface.tsx`, `app/admin/src/components/fpds/admin/product-type-detail-dialog-content.tsx`, `app/admin/src/components/fpds/admin/bank-detail-dialog-content.tsx`, `app/admin/README.md`, `docs/03-design/shadcnblocks-adoption-log.md`, `docs/03-design/ui-override-register.md`
- Decisions: kept the modal-width change scoped through an explicit prop instead of shrinking all registry modals; kept delete failure behavior inside the detail modal so blocked deletes can still show the API error near the action
- Verification:
  - `cmd /c npm run typecheck` in `app/admin`
  - `cmd /c npm run build` in `app/admin`
  - `.venv\Scripts\python.exe -m unittest discover -s tests/regression -p "test_*.py"` in `api/service`
- Known issues: the worktree already contained unrelated modified admin/API/i18n files before this slice; this slice did not normalize those broader changes
- Next step: run browser QA for `/admin/product-types` to confirm the narrower dialog width and post-delete close behavior against a live admin API

## 2026-04-26 - Product Type Discovery Keyword AI Generation

- WBS: `5.16`
- Status: `done`
- Goal: improve operator-created Product Type `Discovery keywords` so they are generated for source discovery quality instead of raw description-token extraction
- Why now: the Product Owner showed a chequing-style description producing low-value keywords such as `designed`, `for`, `such`, and `and`
- Outcome: Product Type create now regenerates discovery keywords through the configured OpenAI provider when available, using display name, full description, and the discovery purpose; persisted keywords are sanitized to short useful discovery terms or phrases. Product Type update regenerates keywords when the display name or description is supplied, while status-only API updates preserve existing keywords. If AI is unavailable, creation still succeeds with a conservative finance-domain fallback that filters filler words.
- Not done: no live OpenAI request was executed in verification; unit tests mock the AI generator. LLM usage rows are not emitted for this admin configuration helper, matching the current homepage-discovery scorer behavior.
- Key files: `api/service/api_service/product_types.py`, `api/service/tests/test_product_types.py`, `docs/03-design/homepage-discovery-scoring-enhancement.md`, `app/admin/README.md`
- Decisions: used the existing `FPDS_LLM_PROVIDER`, `FPDS_LLM_API_KEY`, and `FPDS_LLM_MODEL` environment contract instead of adding a new provider setting; kept AI failures fail-open so missing credentials do not block registry administration
- Verification:
  - `.venv\Scripts\python.exe -m unittest tests.test_product_types` in `api/service`
  - `.venv\Scripts\python.exe -m compileall api_service` in `api/service`
  - `.venv\Scripts\python.exe -m unittest tests.test_product_types tests.test_source_catalog` in `api/service`
  - `.venv\Scripts\python.exe -m unittest discover -s tests/regression -p "test_*.py"` in `api/service`
  - `git diff --check`
- Known issues: actual AI generation requires `FPDS_LLM_PROVIDER=openai` and `FPDS_LLM_API_KEY`; without those settings the deterministic fallback is used
- Next step: verify one live Product Type creation against a configured dev API key and inspect the generated keywords before launching coverage collection

## 2026-04-26 - Admin Locale Copy Polish

- WBS: `5.12`, admin UI polish
- Status: `done`
- Goal: improve EN/KO/JA admin locale wording without translating source-derived or user-entered data
- Why now: the Product Owner asked for a broad admin locale pass while allowing English to remain where it is clearer for operators
- Outcome: tightened protected admin shell navigation copy for banks/product types/sources and account menu labels, localized the overview dashboard metrics and API-unavailable fallback, added KO/JA copy for the pending signup approval panel, made review queue and run status list controls/table/status/date labels locale-aware, localized Product Types list/create/detail/delete chrome, expanded the same locale-copy pattern to Banks, bank coverage, generated Sources, Source Catalog list/create/detail, Change History, Audit Log, Dashboard Health, and Run Detail, and added missing shared KO/JA `admin_operations.audit` resource entries
- Not done: the very large `/admin/usage` and `/admin/reviews/:reviewTaskId` diagnostic-detail bodies still contain English operator copy and should be handled as a separate focused copy pass; source-derived product names, URLs, evidence excerpts, issue codes, ids, and user-entered registry values remain untranslated by design
- Key files: `app/admin/src/components/application-shell5.tsx`, `app/admin/src/app/admin/page.tsx`, `app/admin/src/components/fpds/admin/signup-request-review-panel.tsx`, `app/admin/src/components/fpds/admin/review-queue-surface.tsx`, `app/admin/src/components/fpds/admin/run-status-surface.tsx`, `app/admin/src/components/fpds/admin/run-detail-surface.tsx`, `app/admin/src/components/fpds/admin/product-type-registry-surface.tsx`, `app/admin/src/components/fpds/admin/product-type-create-dialog-content.tsx`, `app/admin/src/components/fpds/admin/product-type-detail-dialog-content.tsx`, `app/admin/src/components/fpds/admin/bank-registry-surface.tsx`, `app/admin/src/components/fpds/admin/bank-create-dialog-content.tsx`, `app/admin/src/components/fpds/admin/bank-detail-dialog-content.tsx`, `app/admin/src/components/fpds/admin/bank-coverage-section.tsx`, `app/admin/src/components/fpds/admin/source-registry-surface.tsx`, `app/admin/src/components/fpds/admin/source-detail-surface.tsx`, `app/admin/src/components/fpds/admin/source-catalog-surface.tsx`, `app/admin/src/components/fpds/admin/source-catalog-create-dialog-content.tsx`, `app/admin/src/components/fpds/admin/source-catalog-detail-dialog-content.tsx`, `app/admin/src/components/fpds/admin/change-history-surface.tsx`, `app/admin/src/components/fpds/admin/audit-log-surface.tsx`, `app/admin/src/components/fpds/admin/health-dashboard-surface.tsx`, `shared/i18n/locales/ko.json`, `shared/i18n/locales/ja.json`, `app/admin/README.md`
- Decisions: kept terms such as `Dashboard`, `Admin API`, `FastAPI`, `source detail`, `trace`, `fallback`, `Discovery keywords`, `coverage`, `collection`, ids, URLs, source values, and operator-entered registry values in English/source form where that preserves operator clarity; treated Usage and Review Detail as follow-on detail-copy inventory rather than rushing a high-risk large edit into this slice
- Verification:
  - `cmd /c npm run typecheck` in `app/admin`
  - `cmd /c npm run build` in `app/admin`
  - `.venv\Scripts\python.exe -m unittest discover -s tests/regression -p "test_*.py"` in `api/service`
- Known issues: `/admin/usage` and `/admin/reviews/:reviewTaskId` still need a dedicated EN/KO/JA diagnostic-detail copy pass; this slice intentionally avoids translating source-derived data and user-entered values
- Next step: perform browser QA for `/admin?locale=ko`, `/admin/product-types?locale=ko|ja`, `/admin/banks?locale=ko|ja`, `/admin/sources?locale=ko|ja`, `/admin/source-catalog?locale=ko|ja`, `/admin/changes?locale=ko|ja`, `/admin/audit?locale=ko|ja`, `/admin/runs/:runId?locale=ko|ja`, and `/admin/health/dashboard?locale=ko|ja` to catch wrapping or readability issues

## 2026-04-25 - Admin Route Body Simplification

- WBS: `4.x`, `5.12`, `5.14`
- Status: `done`
- Goal: apply the compact overview-dashboard body pattern across protected admin menu surfaces
- Why now: the Product Owner reported that Application Shell menu bodies still used oversized card regions and too much explanatory copy outside the simplified overview dashboard
- Outcome: added a shared breadcrumb-led `AdminPageHeader`, added a compact `AdminApiUnavailable` fallback, replaced large route-introduction cards across review, run, change, audit, usage, health, bank, product type, source catalog, source, and detail surfaces, removed production `Slice boundary`/`Live route` explainer banners from those surfaces, and tightened the edited `stats5` metric block into a smaller operational summary
- Not done: this slice did not redesign every inner detail record into definition lists; cards remain where they group metrics, filters, tables, forms, or trace/detail records
- Key files: `app/admin/src/components/fpds/admin/admin-page-header.tsx`, `app/admin/src/components/fpds/admin/admin-api-unavailable.tsx`, `app/admin/src/components/stats5.tsx`, `app/admin/src/components/fpds/admin/*-surface.tsx`, protected admin route pages under `app/admin/src/app/admin/`, `app/admin/README.md`, `docs/03-design/shadcnblocks-adoption-log.md`, `docs/03-design/ui-override-register.md`
- Decisions: used one small FPDS-owned header helper instead of importing another vendor block; kept cards for real data groupings and actions, but removed cards whose only job was route explanation
- Verification:
  - `cmd /c npm run typecheck` in `app/admin`
  - `cmd /c npm run build` in `app/admin`
  - `.venv\Scripts\python.exe -m unittest discover -s tests/regression -p "test_*.py"` in `api/service`
- Known issues: `app/admin/next-env.d.ts` was already modified before this slice and was not touched; broader admin KO/JA mojibake remains outside this layout cleanup
- Next step: run browser/responsive QA against the compact admin menu bodies and adjust only concrete overflow or scanability issues

## 2026-04-24 - Vector-Assisted Evidence Retrieval Bootstrap

- WBS: `3.4`, `5.17`
- Status: `done`
- Goal: document and implement the recommended narrow vector DB adoption path for evidence retrieval without widening into public semantic search or recommendations
- Why now: the Product Owner asked whether vector DB would help and then approved the recommended pgvector-first evidence retrieval implementation
- Outcome: added a pgvector `evidence_chunk_embedding` side table migration, deterministic local 64-dimensional evidence chunk embeddings for dev/test, parse/chunk-side embedding row preparation, vector-assisted retrieval loading with metadata filters pushed into SQL, blended vector/lexical scoring, and metadata-only fallback when vector infrastructure or rows are unavailable
- Not done: no external semantic embedding provider was wired in; production embedding model, dimensions, refresh policy, and score thresholds remain explicit follow-up decisions
- Key files: `db/migrations/0012_evidence_chunk_embeddings.sql`, `worker/pipeline/fpds_vector_embedding.py`, `worker/pipeline/fpds_parse_chunk/persistence.py`, `worker/pipeline/fpds_evidence_retrieval/persistence.py`, `worker/pipeline/fpds_evidence_retrieval/service.py`, `worker/pipeline/tests/test_evidence_retrieval.py`, `worker/pipeline/tests/regression/test_vector_assisted_retrieval.py`, `docs/02-requirements/FPDS_Requirements_Definition_v1_5.md`, `docs/03-design/retrieval-vector-starting-point.md`
- Decisions: kept vector scope limited to `evidence_chunk`; used a side table rather than changing the canonical evidence row; kept metadata filtering before vector ranking; used a deterministic bootstrap embedding so dev/test do not require network calls or live embedding credentials
- Verification:
  - `python -m compileall worker/pipeline/fpds_evidence_retrieval worker/pipeline/fpds_parse_chunk worker/pipeline/fpds_vector_embedding.py`
  - `python -m unittest worker.pipeline.tests.test_evidence_retrieval worker.pipeline.tests.regression.test_vector_assisted_retrieval`
  - `python -m unittest discover -s worker/pipeline/tests -p "test_*.py"`
  - `python -m unittest discover -s worker -t .`
  - `.venv\Scripts\python.exe -m unittest discover -s tests/regression -p "test_*.py"` in `api/service`
  - `python -m unittest discover -s worker/pipeline/tests/regression -p "test_*.py"`
  - `powershell -NoLogo -NoProfile -ExecutionPolicy Bypass -File scripts/harness/invoke-foundation-checks.ps1`
- Known issues: `0012` requires a Postgres target with the `vector` extension available; existing parsed chunks need a parse/chunk rerun or equivalent backfill to create embedding rows
- Next step: apply `0012` in dev, rerun parse/chunk for representative Big 5 sources to populate `evidence_chunk_embedding`, then compare vector-assisted retrieval against metadata-only on evidence recall and review noise

## 2026-04-24 - Admin Dashboard Follow-up Cleanup

- WBS: `4.x`, `5.12`, `5.14`
- Status: `done`
- Goal: apply the Product Owner follow-up on the admin dashboard by renaming the sidebar `/admin` item to `Dashboard` and removing nonessential dashboard body sections
- Why now: after the overview body simplification, the Product Owner wanted the sidebar wording and first-screen content tightened one more step
- Outcome: changed the Application Shell sidebar item label for `/admin` from `Overview` to `Dashboard`, kept the breadcrumb path as `Overview > Dashboard`, removed the `Quick links` and `Session` sections from the dashboard body, and left only the compact attention metrics plus the pending signup approval panel when there are pending requests
- Not done: no new dashboard metric was added because the currently available review, run, dashboard-health, and signup signals already cover the useful live triage data without adding speculative or duplicated widgets
- Key files: `app/admin/src/components/application-shell5.tsx`, `app/admin/src/app/admin/page.tsx`, `app/admin/README.md`, `docs/03-design/shadcnblocks-adoption-log.md`, `docs/03-design/ui-override-register.md`
- Decisions: kept this as a narrow UI cleanup rather than adding another data call or expanding dashboard scope; retained `Overview > Dashboard` in the page breadcrumb because that was the previously requested path structure
- Verification:
  - `cmd /c npm run typecheck`
  - `cmd /c npm run build`
  - `.venv\Scripts\python.exe -m unittest discover -s tests/regression -p "test_*.py"`
- Known issues: the broader admin shell locale resources still contain pre-existing corrupted KO/JA strings outside this cleanup slice
- Next step: include this final compact dashboard body in the next responsive/browser QA pass

## 2026-04-24 - Admin Overview Body Simplification

- WBS: `4.x`, `5.12`, `5.14`
- Status: `done`
- Goal: simplify the protected admin overview body so the first screen starts with an `Overview > Dashboard` breadcrumb, a direct operator greeting, and only the operational information needed for triage
- Why now: the Product Owner called out that the Application Shell body had become dominated by large card regions and explanatory copy instead of a compact dashboard surface
- Outcome: removed the long overview hero, slice-boundary banner, route-design explainer cards, and implementation timeline from `/admin`; added a breadcrumb-led header, greeting, compact metrics backed by review queue/run/dashboard-health/signup APIs, quick links, and a small session summary; kept the signup approval panel only when pending requests exist
- Not done: this slice did not redesign the deeper review, runs, health, bank, or source surfaces; it only simplified the overview entry body
- Key files: `app/admin/src/app/admin/page.tsx`, `app/admin/README.md`
- Decisions: kept the existing `application-shell5` shell and route navigation intact, avoided importing another vendor block, and treated KPI tiles plus the pending signup form as the only card-like elements worth keeping on the overview
- Verification:
  - `cmd /c npm run typecheck`
  - `cmd /c npm run build`
  - `.venv\Scripts\python.exe -m unittest discover -s tests/regression -p "test_*.py"`
- Known issues: the broader admin locale resources still contain pre-existing corrupted KO/JA strings outside this overview body slice
- Next step: include `/admin` in the next responsive/browser QA pass to confirm the new compact body scans well on desktop and mobile

## 2026-04-24 - Admin Shell Navbar and Sidebar Polish

- WBS: `4.x`, `5.12`, `5.14`
- Status: `done`
- Goal: tighten the FPDS Admin shell chrome so the brand and section headings read more clearly, the desktop collapse control sits in the sidebar instead of the navbar, and the footer user menu matches the requested `application-shell5` behavior more closely
- Why now: the Product Owner asked for a small visual polish pass on the live admin shell rather than a wider route redesign
- Outcome: increased the navbar `FPDS Admin` title emphasis, increased sidebar group-label emphasis, moved the desktop collapse trigger into the sidebar header while keeping the navbar trigger on mobile only, removed persistent sidebar-button fills so highlight color appears only on hover/open/active states, removed the footer chevron, added a placeholder `Account` menu row, and added a logout icon to the existing sign-out action
- Not done: no account-management route or interaction was added; the new `Account` row is intentionally disabled until that scope is approved
- Key files: `app/admin/src/components/application-shell5.tsx`, `app/admin/src/app/admin/LogoutButton.tsx`, `app/admin/README.md`, `docs/03-design/ui-override-register.md`, `docs/03-design/shadcnblocks-adoption-log.md`
- Decisions: kept the current `application-shell5` base and adjusted only shell-local composition and menu behavior instead of importing another vendor block or adding a new route; kept the mobile navbar trigger because the off-canvas sidebar still needs an entrypoint on small screens
- Verification:
  - `cmd /c npm run typecheck`
  - `cmd /c npm run build`
  - `.venv\Scripts\python.exe -m unittest discover -s tests/regression -p "test_*.py"`
- Known issues: the shell locale copy file still contains pre-existing corrupted KO/JA strings outside this narrow polish slice
- Next step: include this updated shell behavior in the next responsive QA browser pass so desktop collapsed state and mobile drawer entry remain aligned

## 2026-04-24 - Admin Shell Header Row and Footer Menu Cleanup

- WBS: `4.x`, `5.12`, `5.14`
- Status: `done`
- Goal: finish the requested follow-up shell cleanup by moving the active sidebar section title into the sidebar header row, removing the visible footer env/role line, and tightening menu highlight behavior plus footer action alignment
- Why now: the Product Owner reviewed the previous shell polish and called out remaining layout and background-state mismatches
- Outcome: moved the active section heading into the same sidebar-header row as the desktop collapse trigger, removed the visible divider-under-header treatment, hid the footer env/role row from the user dropdown, left-aligned both `Account` and `Sign out`, and made the shared sidebar menu button explicitly transparent until hover or active state so the highlight fill only appears when intended
- Not done: the `Account` row is still placeholder-only and the shell file still carries older corrupted KO/JA copy outside this narrow interaction pass
- Key files: `app/admin/src/components/application-shell5.tsx`, `app/admin/src/components/ui/sidebar.tsx`, `app/admin/README.md`, `docs/03-design/ui-override-register.md`, `docs/03-design/shadcnblocks-adoption-log.md`
- Decisions: kept the fix inside the existing shell and shared sidebar primitive instead of importing another vendor block or widening the scope into a broader locale-copy cleanup
- Verification:
  - `cmd /c npm run typecheck`
  - `cmd /c npm run build`
  - `.venv\Scripts\python.exe -m unittest discover -s tests/regression -p "test_*.py"`
- Known issues: this slice removes the visible footer env/role line, but it does not add any new account-management route or profile flow
- Next step: include the refined shell in the next responsive/browser QA pass and only reopen the shell if another concrete mismatch appears

## 2026-04-22 - Admin Shell Simplification and Collapse Alignment

- WBS: `4.x`, `5.12`
- Status: `done`
- Goal: align the protected admin shell to the requested `application-shell5` behavior by removing extra chrome, restoring explicit collapse or expand behavior, and moving sign-out into the footer user menu
- Why now: the Product Owner asked to remove the navbar `Operations shell` subtitle and search, drop sidebar promo copy/status pills/card styling, and make the sidebar/footer behave more like the intended Shadcnblocks shell
- Outcome: switched the shared admin shell away from the floating card-style sidebar, removed sidebar header copy plus menu descriptions/status tags, kept the module tabs while simplifying the top bar, added a footer avatar dropdown that shows display name plus `login_id`, and moved sign-out into that menu while the protected route pages now pass `logoutApiOrigin` and `loginId`
- Not done: no broader admin copy cleanup or route-level search redesign outside the shared shell was included in this slice
- Key files: `app/admin/src/components/application-shell5.tsx`, `app/admin/src/app/admin/LogoutButton.tsx`, `app/admin/src/app/admin/page.tsx`, `app/admin/src/app/admin/banks/page.tsx`, `app/admin/src/app/admin/reviews/page.tsx`, `app/admin/src/app/admin/runs/page.tsx`, `app/admin/README.md`, `docs/03-design/admin-information-architecture.md`
- Decisions: kept the existing installed `application-shell5` foundation instead of importing another shell; removed shell-level global search because the Product Owner asked for lighter chrome and the active route surfaces already own their own search/filter UX where needed
- Verification:
  - `cmd /c npm run typecheck`
  - passed in `app/admin`
  - `cmd /c npm run build`
  - passed in `app/admin`
  - `.venv\Scripts\python.exe -m unittest discover -s tests/regression -p "test_*.py"`
  - passed in `api/service`
- Known issues: the shell locale copy map still contains older unused strings, but those strings no longer render in the simplified header/sidebar path
- Next step: do a browser pass on collapsed and expanded desktop behavior plus the mobile sheet after the next protected admin slice that touches shell chrome

## 2026-04-22 - Archive Reference Repair for Pre-Commit Integrity

- WBS: documentation hygiene
- Status: `done`
- Goal: fix staged archive-doc path references so the markdown reference check stops blocking commits after the `docs/archive/` split
- Why now: the pre-commit hook was failing on archived gate and prototype docs that still pointed at the old active-path locations after the archive move
- Outcome: updated staged archive governance and prototype docs to reference `docs/archive/...` consistently, corrected the archived evidence pack viewer links to repo-root `/app/prototype/...`, and restored hook-valid link integrity for the staged archive bundle
- Not done: this slice only repaired staged archive-link breakage and did not attempt broader content cleanup in the older archived docs
- Key files: `docs/archive/00-governance/gate-a-build-start-review-note.md`, `docs/archive/00-governance/gate-b-prototype-review-note.md`, `docs/archive/00-governance/gate-c-admin-ops-review-note.md`, `docs/archive/01-planning/evidence/2026-04-11-first-successful-run/evidence-pack.md`, `docs/archive/01-planning/prototype-backlog.md`, `docs/archive/01-planning/prototype-findings-memo.md`, `docs/archive/01-planning/prototype-spike-scope.md`, `docs/archive/01-planning/sprint-0-board.md`, `docs/archive/01-planning/td-savings-source-inventory.md`
- Decisions: kept archive references root-anchored as `docs/archive/...` for consistency with the repo's other document citations; used repo-root `/app/prototype/...` links for viewer artifacts so deep archive docs do not depend on fragile relative traversal
- Verification:
  - `powershell -NoLogo -NoProfile -ExecutionPolicy Bypass -File scripts/harness/pre-commit.ps1`
  - pending after staging the repaired docs
- Known issues: archived prototype docs still contain older mojibake in their body text, but that was pre-existing and outside this commit-unblock slice
- Next step: rerun the pre-commit hook on the repaired staged set and commit once the reference check passes

## 2026-04-22 - Admin Shell Correction Back to Application Shell 5 Floating

- WBS: `4.x`, `5.12`, documentation hygiene
- Status: `done`
- Goal: correct the mistaken Sidebar 8 change by restoring the admin shell to Shadcnblocks `application-shell5` and switching that shell to the floating sidebar variant
- Why now: the Product Owner clarified that the requested target was `application-shell5` floating sidebar shell, not `sidebar8`, so the just-made shell change had to be backed out before it became the recorded baseline
- Outcome: reinstalled `@shadcnblocks/application-shell5`, restored the live admin shell to the FPDS-tailored Application Shell 5 structure, switched its sidebar to the floating variant, removed the mistaken `sidebar8` and `breadcrumb` additions, and corrected the runtime/docs tracking files back to the Application Shell 5 baseline
- Not done: no broader cleanup of older mojibake in unrelated admin copy files was included in this slice, and the reserved publish route remains planned rather than implemented
- Key files: `app/admin/src/components/application-shell5.tsx`, `app/admin/README.md`, `docs/03-design/shadcnblocks-adoption-log.md`, `docs/03-design/shadcnblocks-block-inventory.md`, `docs/03-design/ui-override-register.md`, `docs/00-governance/development-journal.md`
- Decisions: used the existing FPDS-tailored Application Shell 5 structure as the safer baseline and changed only the sidebar variant to floating instead of inventing another shell rewrite; removed the mistaken Sidebar 8 artifacts so the repo records match the actual live shell again
- Verification:
  - `pnpm run typecheck`
  - passed in `app/admin`
  - `pnpm run build`
  - passed in `app/admin`
  - `api/service/.venv/Scripts/python.exe -m unittest discover -s tests/regression -p "test_*.py"`
  - passed
- Known issues: the admin app still contains some pre-existing broken KO/JA strings outside the new shell file, so locale switching is preserved structurally but not every older label in the wider admin surface was normalized here
- Next step: do a quick browser pass on the protected admin routes to confirm the new shell layout feels right on desktop and mobile

## 2026-04-22 - Signup Validation Alignment for Local Dev Auth

- WBS: `4.1`
- Status: `done`
- Goal: fix the signup-request 422 error for short local-dev credentials and capture the rule in regression coverage
- Why now: the Product Owner hit `Invalid request payload` on `/api/admin/auth/signup-requests` with a short local-dev password because signup validation still required 8 characters while the recently relaxed login flow no longer did
- Outcome: introduced a shared auth password minimum in the request models, aligned both login and signup request validation to the same 4-character local-dev threshold, and extended the auth regression suite to cover both acceptance and rejection around that boundary
- Not done: the bootstrap-admin CLI still keeps its stronger standalone password minimum and was not changed in this slice
- Key files: `api/service/api_service/models.py`, `api/service/tests/regression/auth/test_login_transition_regression.py`, `docs/00-governance/development-journal.md`
- Decisions: fixed the inconsistency at the API request-model boundary instead of layering special-case frontend handling on top of a mismatched backend rule; kept the bootstrap CLI untouched because this slice was about the live signup/login path only
- Verification:
  - `.venv\Scripts\python.exe -m unittest discover -s tests/regression -p "test_*.py"`
  - passed
  - `.venv\Scripts\python.exe -m unittest tests.test_auth`
  - passed
- Known issues: signup/login now allow very short local-dev passwords, which is acceptable for the current requested workflow but still weaker than the bootstrap path
- Next step: if auth policy needs to diverge by environment later, decide explicitly whether to keep one shared minimum or introduce a settings-driven dev-vs-prod validation rule

## 2026-04-22 - Auth Regression Coverage Extension for Password Hash Integrity

- WBS: `4.1`
- Status: `done`
- Goal: add regression coverage for the latest local admin login recovery where a mangled password hash caused repeated `Invalid ID or password`
- Why now: the Product Owner asked to keep regression-testable fixes under `tests/regression/<domain>/test_*.py`, and the latest auth issue highlighted the need to preserve hash-format expectations in the regression suite
- Outcome: extended `tests/regression/auth/test_login_transition_regression.py` with coverage that the dev admin credential still produces a valid `scrypt$...` hash and that the previously observed shell-mangled hash shape does not verify
- Not done: the operational act of repairing a live DB row is still not directly test-covered because it is an environment-specific manual recovery step
- Key files: `api/service/tests/regression/auth/test_login_transition_regression.py`, `docs/00-governance/development-journal.md`
- Decisions: kept the new cases in the existing auth regression file instead of splitting another micro-module because they belong to the same login-transition failure family
- Verification:
  - `.venv\Scripts\python.exe -m unittest discover -s tests/regression -p "test_*.py"`
  - passed
- Known issues: this coverage protects app-level hash invariants, but it cannot stop unsafe ad-hoc shell SQL from corrupting values outside the application path
- Next step: if credential admin tooling is touched again, prefer adding a repo-owned reset path so future credential changes stay inside testable code paths

## 2026-04-22 - Local Admin Password Hash Repair

- WBS: `4.1`
- Status: `done`
- Goal: fix the remaining local admin login failure after the login-id switch
- Why now: the admin account still returned `Invalid ID or password` even after changing the local login to `admin`
- Outcome: confirmed the stored `user_account.password_hash` had been corrupted during a direct shell-based SQL update because the shell expanded `$...` segments inside the scrypt hash; repaired the row using the project Python environment with a parameterized DB update, reset login-failure counters, and verified that the stored hash now matches `admin`
- Not done: no broader admin password reset tooling or safer operator credential command was added in this slice
- Key files: `docs/00-governance/development-journal.md`
- Decisions: used the project Python environment plus parameterized SQL instead of another direct shell SQL literal so the password hash could not be mangled by shell interpolation
- Verification:
  - inspected the live `user_account` row for `login_id=admin`
  - verified the repaired stored hash with `verify_password('admin', password_hash)`
  - passed
- Known issues: direct shell SQL updates remain risky for password hashes and any other values containing `$` unless they are parameterized or safely quoted
- Next step: if operator credential changes are needed again, use the project Python path or add an explicit reset command rather than embedding password hashes in shell SQL

## 2026-04-22 - API Auth Regression Test Split

- WBS: `4.1`, documentation hygiene
- Status: `done`
- Goal: move the just-added admin auth regression coverage into a dedicated folder so it can be reused later as a recursive regression suite
- Why now: the Product Owner asked for separate management of the new auth-fix test cases rather than leaving them mixed into the main unit-test module
- Outcome: moved the login transition regression coverage into `api/service/tests/regression/auth/`, added a regression test README with recursive `unittest discover` commands, and documented the standalone regression-suite command in `api/service/README.md`
- Not done: no broader repo-wide regression runner or CI split was added in this slice
- Key files: `api/service/tests/regression/auth/test_login_transition_regression.py`, `api/service/tests/regression/README.md`, `api/service/tests/test_auth.py`, `api/service/README.md`
- Decisions: kept the existing `tests/` layout intact for general unit tests and introduced `tests/regression/` as a parallel subtree for bug-fix coverage that should remain easy to discover recursively
- Verification:
  - `.venv\Scripts\python.exe -m unittest discover -s tests/regression -p "test_*.py"`
  - passed
  - `.venv\Scripts\python.exe -m unittest tests.test_auth`
  - passed
- Known issues: regression discovery currently depends on the service virtualenv Python and manual command invocation; no dedicated CI job targets `tests/regression/` yet
- Next step: if more bug-fix suites accumulate, group them by domain under `tests/regression/` and add a harness or CI entrypoint only when the suite becomes large enough to justify separate automation

## 2026-04-22 - Admin Login Attempt Backward-Compatibility Fix

- WBS: `4.1`
- Status: `done`
- Goal: fix the 500 error raised during admin login after the login-id migration
- Why now: live login attempts were failing with `psycopg.errors.NotNullViolation` because `auth_login_attempt.email` was still `NOT NULL` in the legacy auth table while the new login-id flow was inserting `NULL`
- Outcome: updated login-attempt persistence to always write a non-null legacy `email` value for backward compatibility, preferring the real user email when available and otherwise falling back to the submitted `login_id`; added unit coverage for both cases
- Not done: the DB schema itself was not cleaned up in this slice, so the runtime compatibility path still carries the legacy `email` column requirement
- Key files: `api/service/api_service/auth.py`, `api/service/tests/test_auth.py`, `docs/00-governance/development-journal.md`
- Decisions: fixed the runtime write path instead of mutating the live auth schema during an active login issue; kept the patch narrow so existing login telemetry and indexes continue to work
- Verification:
  - `python -m compileall api/service/api_service`
  - passed
  - `.venv\Scripts\python.exe -m unittest tests.test_auth`
  - passed
- Known issues: the auth schema still reflects a mixed `email` plus `login_id` transition state and may deserve a later cleanup migration
- Next step: if more auth cleanup is needed later, decide whether to keep the legacy `email` column for audit/search compatibility or formally relax/drop its `NOT NULL` requirement

## 2026-04-22 - Admin Login-ID Regression Recovery for Local Dev

- WBS: `4.1`
- Status: `done`
- Goal: explain why the old email-shaped admin login stopped working and restore a working local admin credential
- Why now: the Product Owner could no longer log in with the old Hotmail-shaped admin credential and asked to switch the local admin account to `admin / admin`
- Outcome: confirmed that auth now signs in by `login_id` instead of email, and that the current login-id validator rejects `@` even though older accounts were backfilled from email during the signup-request migration; updated the live local admin account to `login_id=admin`, reset lock counters, and changed the login request model so the requested 5-character local dev password is accepted at the API boundary
- Not done: broader legacy-account migration or transitional email-login compatibility was not added in this slice
- Key files: `api/service/api_service/models.py`, `docs/00-governance/development-journal.md`
- Decisions: kept the fix narrow to the active local admin account and the login endpoint validation instead of reopening the broader auth design; left signup/bootstrap password rules unchanged so only the direct local-login path was relaxed
- Verification:
  - `python -m compileall api/service/api_service`
  - passed
  - verified current DB row after update
  - `login_id=admin`, `account_status=active`, `failed_login_count=0`
- Known issues: any other legacy account that still stores an email-shaped `login_id` may hit the same validator mismatch until it is renamed or a separate compatibility strategy is implemented
- Next step: if more legacy accounts must keep email-style login temporarily, choose between a one-time DB rename pass and an explicit transitional auth compatibility rule

## 2026-04-22 - Admin Auth Surface Copy and Header Alignment

- WBS: `4.1`, `5.12`
- Status: `done`
- Goal: remove unnecessary auth-screen eyebrow copy, tighten the `FPDS ADMIN` wordmark spacing, align the auth title with the locale switcher on one row, and make login/signup labels actually react to EN/KO/JA locale changes
- Why now: the Product Owner called out redundant copy on `/admin/login` and `/admin/signup`, overly wide brand tracking, and broken locale-aware labeling on the auth surfaces
- Outcome: removed the `Secure access` and `Request access` eyebrow text, reduced the `FPDS ADMIN` tracking, moved `Login` or `Sign up` and the locale switcher into a single header row inside each card, and filled in Korean/Japanese auth-surface copy so labels, placeholders, button text, success text, and error text now change with locale
- Not done: broader admin locale-resource cleanup outside the login/signup surfaces was not included in this slice
- Key files: `app/admin/src/components/login2.tsx`, `app/admin/src/components/signup-request-form.tsx`
- Decisions: kept the fix local to the two auth-surface components instead of opening a wider admin i18n refactor; preserved the existing route/query-param locale flow and corrected the missing translations where the UI was still using English base copy for every locale
- Verification:
  - `pnpm run typecheck`
  - passed in `app/admin`
- Known issues: other admin surfaces still rely on older locale-label implementations and may need a later cleanup pass
- Next step: verify the auth surfaces in-browser at `en`, `ko`, and `ja`, then continue the broader responsive/admin locale QA backlog only if additional issues appear

## 2026-04-20 - Scotia Savings Seed Scope Refresh and Money Master Follow-up

- WBS: `3.6`, `5.15`
- Status: `done`
- Goal: close the remaining Scotia savings follow-ups by fixing the stale preserved-scope `404` and the Money Master savings validation gap
- Why now: Scotia savings reruns were still reusing an old dead source URL, and `SCOTIA-SAV-004` still landed in review with `validation_error`
- Outcome: refreshed active seed-backed source rows from the current seed baseline before preserved detail reuse, removed the stale `SCOTIA-SAV-005` dead URL from live runs, and added a supporting merge so `SCOTIA-SAV-004` can borrow missing rate fields from `SCOTIA-SAV-006`
- Not done: `SCOTIA-SAV-005` still reaches review with `required_field_missing`; that is now a separate real parser or content gap
- Key files: `api/service/api_service/source_catalog_collection_runner.py`, `api/service/tests/test_source_catalog_collection_runner.py`, `worker/discovery/data/scotia_savings_source_registry.json`, `worker/discovery/tests/test_registry_catalog.py`, `worker/pipeline/fpds_normalization/supporting_merge.py`, `worker/pipeline/tests/test_normalization.py`
- Decisions: kept the preserved-scope fix narrow to active seed-backed rows for the current bank and product type; used the existing supporting-merge pattern instead of adding a Scotia-only extraction special case
- Verification:
  - `api/service/.venv/Scripts/python.exe -m unittest api.service.tests.test_source_catalog_collection_runner api.service.tests.test_source_catalog`
  - passed
  - `python -m unittest worker.discovery.tests.test_registry_catalog worker.pipeline.tests.test_normalization`
  - passed
  - `api/service/.venv/Scripts/python.exe -m api_service.source_catalog_collection_runner --plan-path tmp/source-catalog-collections/run_20260420_222518_scotia_savings_collect_b1zEZ9d_.json`
  - completed successfully
- Known issues: `SCOTIA-SAV-005` still has a candidate-level `required_field_missing` validation error after the stale URL fix
- Next step: inspect the normalized and validated artifacts for `SCOTIA-SAV-005` and decide whether the next fix belongs in extraction heuristics or supporting merge logic

## 2026-04-21 - Aggregate Refresh Auto Queue and Dashboard Health

- WBS: `5.6`, `5.7`, `5.8`, `5.13`
- Status: `done`
- Goal: make approved canonical changes propagate to public aggregate snapshots automatically, preserve latest-successful serving on failure, and expose refresh state on a real admin health route with manual retry
- Why now: public `/products` could drift from canonical truth because review approval did not yet enqueue the aggregate refresh step
- Outcome: added an aggregate refresh queue table and runner, queued refresh requests on review approval or edit-approve, kept public serving on the latest successful snapshot when newer refreshes fail, and added `GET/POST /api/admin/dashboard-health` plus `/admin/health/dashboard`
- Not done: no broader scheduler, lease-expiry governance, or second publish approval gate was added
- Key files: `db/migrations/0010_aggregate_refresh_queue.sql`, `api/service/api_service/aggregate_refresh.py`, `api/service/api_service/aggregate_refresh_runner.py`, `api/service/api_service/main.py`, `api/service/tests/test_aggregate_refresh.py`, `app/admin/src/app/admin/health/dashboard/page.tsx`, `app/admin/src/app/admin/health/dashboard/retry/route.ts`, `app/admin/src/components/fpds/admin/health-dashboard-surface.tsx`
- Decisions: kept `aggregate_refresh_run` as execution history and introduced a separate queue table instead of overloading run rows with queued semantics; kept refresh asynchronous and post-commit
- Verification:
  - `python -m unittest tests.test_aggregate_refresh tests.test_run_retry tests.test_public_products tests.test_review_detail`
  - passed in `api/service`
  - `python -m compileall api_service`
  - passed in `api/service`
  - `pnpm run typecheck`
  - passed in `app/admin`
- Known issues: the queue still assumes one active Canada public aggregate scope and relies on the current single-runner guard
- Next step: apply `0010_aggregate_refresh_queue.sql` to the target DB, restart the admin API, then verify the dashboard health state changes after a review approval

## 2026-04-21 - Customer Reports Cleanup

- WBS: documentation hygiene
- Status: `done`
- Goal: remove the retired external reporting docs and scrub related references
- Why now: the Product Owner asked to delete the retired reporting folder and remove related references from remaining docs
- Outcome: deleted the retired reporting docs, removed the old report-specific journal entry, and tightened the Phase 1 QA checklist so evidence stays under governance docs instead of pointing to a separate reporting area
- Not done: no replacement reporting workflow was introduced
- Key files: `docs/00-governance/phase-1-no-bxpf-test-checklist.md`
- Decisions: treated the retired reporting area as intentionally removed rather than relocated
- Verification:
  - `Get-ChildItem -Name docs`
  - governance, planning, requirements, design, and docs map remained
  - `git diff --check`
  - passed
- Known issues: generic uses of the word `customer` still remain elsewhere because they are unrelated to the deleted reporting area
- Next step: if external reporting is needed again later, define a new approved location before reintroducing shareable reporting artifacts

## 2026-04-21 - Runtime Reseed Removal for Resettable Registry State

- WBS: `5.15`, `5.16`
- Status: `done`
- Goal: stop bank, product type, source catalog, and generated source rows from silently repopulating after an operator reset
- Why now: operator resets were being undermined by runtime reseeding from committed JSON baselines and active seed scope refresh behavior
- Outcome: removed runtime reseeding from product types, source catalog, source registry, and source collection runner logic so empty-state replay testing is possible without dropping the whole DB
- Not done: historical SQL migrations that seed a fresh database were not rewritten
- Key files: `api/service/api_service/product_types.py`, `api/service/api_service/source_catalog.py`, `api/service/api_service/source_registry.py`, `api/service/api_service/source_catalog_collection_runner.py`, `api/service/tests/test_product_types.py`, `api/service/tests/test_source_catalog.py`, `api/service/tests/test_source_registry.py`, `api/service/tests/test_source_catalog_collection_runner.py`, `docs/03-design/source-registry-refresh-and-approval-policy.md`
- Decisions: fixed runtime behavior only and did not mutate already-applied historical SQL migrations
- Verification:
  - runtime code search no longer returns `ensure_product_type_registry_seeded`, `_ensure_bank_and_catalog_seeded`, `_ensure_source_registry_seeded`, or `_refresh_active_seed_scope_rows` inside `api/service/api_service`
  - remaining automatic bootstrap is limited to historical fresh-DB migration inserts
- Known issues: a fully fresh DB rebuilt from the current migration chain still receives the historical bank and product type baseline rows
- Next step: if fresh databases should also start empty, choose an explicit migration strategy before changing historical migrations

## 2026-04-22 - Docs Active Path Cleanup

- WBS: documentation hygiene
- Status: `done`
- Goal: reduce startup reading cost for Codex by separating archival docs from active docs and rewriting weak navigation entrypoints
- Why now: `docs/` had become too large and too noisy, and the development journal and frontend benchmark doc were no longer efficient resume references
- Outcome: moved closed gate notes, prototype planning docs, and prototype evidence artifacts under `docs/archive/`; rewrote `docs/README.md` as the active navigation hub; added `docs/archive/README.md` and `docs/03-design/README.md`; rewrote `docs/03-design/fpds_design_system_stripe_benchmark.md` as a short current baseline; and reduced this journal to recent entries only
- Not done: long-standing mojibake inside some older governance docs such as `decision-log.md`, `raid-log.md`, `roadmap.md`, and `milestone-tracker.md` was not fully normalized in this slice
- Key files: `README.md`, `docs/README.md`, `docs/archive/README.md`, `docs/03-design/README.md`, `docs/03-design/fpds_design_system_stripe_benchmark.md`, `docs/00-governance/development-journal.md`
- Decisions: archive material stays inside the repository for traceability, but Codex should skip it by default; the benchmark doc remains the stronger frontend direction doc when it conflicts with the broader design-system baseline
- Verification:
  - `rg --files docs`
  - confirmed active docs and archive split
  - `git diff --check`
  - pending after final link updates
- Known issues: some active docs still carry older path references or legacy wording and may need later cleanup
- Next step: keep future active docs short, and move closed-stage planning or gate evidence into `docs/archive/` as soon as it stops shaping current implementation

## 2026-04-22 - Governance Docs Current-Baseline Rewrite

- WBS: documentation hygiene
- Status: `done`
- Goal: replace the four noisy governance docs with short current-baseline documents that are readable from the shell and useful for active implementation decisions
- Why now: `decision-log.md`, `raid-log.md`, `roadmap.md`, and `milestone-tracker.md` still carried stale stage-by-stage detail and encoding-noisy content even after the archive split
- Outcome: rewrote the four docs as compact current-baseline references. The decision log now keeps only active decisions that still shape implementation. The RAID log now keeps only active risks, assumptions, issues, and dependencies. The roadmap now shows only current stage direction. The milestone tracker now keeps a short live milestone board instead of a schedule-heavy historical narrative
- Not done: `WBS.md` and some other older active docs still contain legacy wording and may need later readability cleanup
- Key files: `docs/00-governance/decision-log.md`, `docs/00-governance/raid-log.md`, `docs/00-governance/roadmap.md`, `docs/00-governance/milestone-tracker.md`, `docs/00-governance/development-journal.md`
- Decisions: treated these four docs as current operating documents, not historical archives; removed stale detailed history from the default path instead of trying to preserve every old item inline
- Verification:
  - `rg --line-number --glob '!docs/archive/**' "D-0[0-9]{2}|R-[0-9]{3}|A-[0-9]{3}|I-[0-9]{3}" README.md docs app shared api db storage worker`
  - no active docs outside the rewritten governance files depended on the old decision or RAID numbering
  - `git diff --check`
  - passed except for expected line-ending warnings only
- Known issues: the rewritten docs are intentionally concise, so very old design-stage decision history now lives only indirectly through archive records, requirements, WBS, and implementation artifacts
- Next step: if docs hygiene continues, clean remaining legacy readability issues in `WBS.md` and any active design docs that still render poorly in the shell

## 2026-04-22 - Admin Login Simplification and Shared Copy Rule

- WBS: `4.1`, `5.12`, documentation hygiene
- Status: `done`
- Goal: simplify the admin login screen by removing the left-side operator explainer panel and record a shared design-system rule against overly verbose UI copy
- Why now: the Product Owner asked for a simpler admin login surface, removal of the left `Operator sign-in` region, retention of locale switching, and a reusable design rule that keeps future screens from adding unnecessary explanatory text
- Outcome: reduced `/admin/login` to a single centered sign-in card, moved the locale switcher above the card, removed the verbose eligibility/bootstrap/session/footer copy from the visible UI, and added a design-system copy-discipline rule that now applies across surfaces
- Not done: no broader admin shell or locale-resource wording pass was included in this slice
- Key files: `app/admin/src/components/login2.tsx`, `docs/03-design/fpds-design-system.md`, `docs/03-design/fpds_design_system_stripe_benchmark.md`
- Decisions: kept the locale switcher visible on the login page while removing the secondary explanatory panel; recorded the simplicity rule in both the baseline design-system doc and the current benchmark doc so future UI work follows the same constraint
- Verification:
  - `pnpm run typecheck`
  - passed in `app/admin`
- Known issues: some existing admin locale strings still need later wording cleanup, but the simplification rule now prevents new verbose helper copy from being added by default
- Next step: apply the same minimal-copy rule opportunistically when other admin or public screens are touched

## 2026-04-22 - Admin Signup Request Flow and Login-ID Auth

- WBS: `4.1`, `5.12`
- Status: `done`
- Goal: convert admin auth from email-shaped login copy to `login_id`-first auth, add a simple `Sign up` request flow, and keep account activation gated by an existing admin
- Why now: the Product Owner asked for a simpler login card, `Id` instead of work email, a visible sign-up path, and an approval-based onboarding flow instead of direct self-service account creation
- Outcome: the admin login UI now shows `FPDS ADMIN` above the card, keeps locale switching inside the card, logs in with `login_id`, and links to a new `/admin/signup` access-request page; the API now accepts pending signup requests, exposes admin-only list and approve or reject routes, stores `user_account.login_id`, and the protected `/admin` overview now includes an admin-only pending-request approval panel
- Not done: no broader user-management surface, password reset flow, or self-service profile editing was added
- Key files: `db/migrations/0011_admin_signup_requests.sql`, `api/service/api_service/auth.py`, `api/service/api_service/main.py`, `api/service/api_service/models.py`, `api/service/api_service/bootstrap_admin_user.py`, `api/service/tests/test_auth.py`, `app/admin/src/components/login2.tsx`, `app/admin/src/components/signup-request-form.tsx`, `app/admin/src/components/fpds/admin/signup-request-review-panel.tsx`, `app/admin/src/app/admin/signup/page.tsx`, `app/admin/src/app/admin/page.tsx`
- Decisions: kept self-sign-up narrow by treating it as a pending request only; placed approval on the existing overview surface instead of creating a separate account-admin module; defaulted approval role selection in the UI to `reviewer` to avoid unnecessary admin grants
- Verification:
  - `python -m unittest tests.test_auth tests.test_security`
  - pending
  - `python -m compileall api_service`
  - pending
  - `pnpm run typecheck`
  - pending
- Known issues: older admin locale resources outside the new signup flow still carry some legacy wording and encoding noise
- Next step: apply migration `0011_admin_signup_requests.sql`, create the first bootstrap admin with `--login-id`, then verify signup request creation and approval against a live local database

## 2026-04-24 - Admin Shell Active-State Fix Follow-up

- WBS: `5.12`
- Status: `done`
- Goal: reduce the shell brand weight slightly and remove the always-highlighted sidebar and footer-avatar fills so only hover or the current route shows emphasis
- Why now: the Product Owner reported that the navbar title still felt too bold and the sidebar menu plus avatar trigger continued to look active even when idle
- Outcome: reduced the `FPDS Admin` navbar title from `font-bold` to `font-semibold`, and fixed the sidebar primitives so active styling now applies only when `data-active=true` instead of whenever a `data-active` attribute exists
- Not done: no new account-management route or footer-menu behavior change was added in this slice
- Key files: `app/admin/src/components/application-shell5.tsx`, `app/admin/src/components/ui/sidebar.tsx`
- Decisions: corrected the root cause in the shared sidebar primitive instead of stacking more local `bg-transparent` overrides onto each shell row
- Verification:
  - `cmd /c npm run typecheck`
  - `cmd /c npm run build`
  - `.venv\Scripts\python.exe -m unittest discover -s tests/regression -p "test_*.py"`
- Known issues: the dropdown still contains a hidden env/role placeholder block from the earlier shell edit, but it is not visible and does not affect interaction state
- Next step: if the Product Owner wants, clean the hidden footer-menu residue in a separate low-risk markup pass after the visible behavior is confirmed

## 2026-04-25 - Admin Registry Modal Responsiveness

- WBS: `5.13`, admin UI polish
- Status: `done`
- Goal: make bank, source-catalog, and product-type registry modals feel immediate, remove redundant modal branding/copy, and keep the close affordance clear inside rounded dialog corners
- Why now: the Product Owner reported slow modal open/close behavior, redundant `FPDS Admin` modal labels, unnecessary explanatory modal copy, and a clipped close icon
- Outcome: modal open/close now uses local component state plus native history URL sync instead of forcing `router.push` or `router.replace` for routine toggles; product-type detail opens from already-loaded list data; bank and source-catalog detail open immediately from list preview data and hydrate richer detail through narrow JSON proxy routes. The shared `offer-modal4` removed redundant `FPDS Admin` pills and moved the close button inward.
- Not done: no new modal design system abstraction was introduced; this stays scoped to the current Shadcnblocks-derived modal and the three affected registry surfaces
- Key files: `app/admin/src/components/offer-modal4.tsx`, `app/admin/src/components/fpds/admin/bank-registry-surface.tsx`, `app/admin/src/components/fpds/admin/source-catalog-surface.tsx`, `app/admin/src/components/fpds/admin/product-type-registry-surface.tsx`, `app/admin/src/app/admin/banks/[bankCode]/detail/route.ts`, `app/admin/src/app/admin/source-catalog/[catalogItemId]/detail/route.ts`
- Decisions: kept URL sharing for modal state, but stopped using App Router navigation as the default modal state mechanism because it was causing unnecessary route refresh and backend refetch work on open and close
- Verification:
  - `cmd /c npm run typecheck`
  - `cmd /c npm run build`
  - `.venv\Scripts\python.exe -m unittest discover -s tests/regression -p "test_*.py"`
- Known issues: delete actions inside detail modals still intentionally use router navigation because they change the underlying resource and route state
- Next step: if more modal-heavy admin surfaces are added, extract the native-history modal URL sync into a small shared helper instead of copying it across surfaces

---

## 5. Change History

| Date | Change |
|---|---|
| 2026-04-22 | Reduced the journal to recent resume context and pointed historical material to `docs/archive/` |
| 2026-04-22 | Rewrote the decision log, RAID log, roadmap, and milestone tracker as short current-baseline governance docs |
