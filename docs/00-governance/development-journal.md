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
- public grid, dashboard, locale rollout, source registry admin MVP, and dynamic product type onboarding are already implemented
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

---

## 5. Change History

| Date | Change |
|---|---|
| 2026-04-22 | Reduced the journal to recent resume context and pointed historical material to `docs/archive/` |
| 2026-04-22 | Rewrote the decision log, RAID log, roadmap, and milestone tracker as short current-baseline governance docs |
