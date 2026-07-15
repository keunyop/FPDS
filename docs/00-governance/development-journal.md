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

As of `2026-07-14`:
- `WBS 5` is the active stage
- public grid, dashboard, locale rollout, source registry admin MVP, and operator-managed product type onboarding are already implemented
- recent work has focused on source collection hardening, aggregate refresh health, and registry state behavior
- the latest slice hardened multi-bank Runs/Review Queue behavior after B2B duplicate/noisy candidates and Bridgewater domain-alias failures; active Queue is reduced to four genuinely reviewable B2B products and Bridgewater Savings now collects successfully
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

## 2026-07-14 - Review Detail Product-Style Candidate Presentation

- WBS: `4.2`, `4.3`, `4.4`, Admin review UX follow-on
- Status: done
- Goal: present each review candidate as a financial product detail without weakening evidence-led human decision controls.
- Outcome: the Review Detail now begins with a candidate product presentation aligned to Public detail hierarchy: product identity, source-derived description, three product-family-aware metrics, product facts, and key conditions. Lending prioritizes rate, rate type, term, amortization, payment, prepayment, amount/limit, and security; chequing prioritizes fee, balance, and transaction cues; deposit/term products prioritize rate, term, and entry amount. The overview uses the reviewer’s in-progress edits immediately, while the field list below remains the source of truth for agent value, effective value, inline evidence, correction, and approval decisions.
- Decisions: retain the explicit `Candidate product` state and the Admin-only source link; do not reuse Public disclosure copy or expose the evidence workflow as consumer content. Duplicate source-link action was removed from the decision-facts card to keep the screen concise.
- Key files: `app/admin/src/components/fpds/admin/review-detail-surface.tsx`, `app/admin/README.md`, `docs/03-design/admin-information-architecture.md`.
- Verification: `pnpm run typecheck` passed; `pnpm run build` passed and generated the protected Review Detail route; `git diff --check` passed.
- Next step: use the new summary during the next queued Mortgage review and confirm field values against the linked bank source before approval.

## 2026-07-14 - Public Loan Catalog Activation

- WBS: `5.6`, `5.7`, `5.9`, `5.16`
- Status: implemented; awaiting a required operator approval for the first public lending product
- Goal: make review-approved loans discoverable in FPDS Public with the same safe publish boundary as deposits.
- Why now: the Product Owner requested Loan discovery in Public and confirmed Mortgage, Personal Loan, and Line of Credit as the catalog scope. The registry was already active, but the public aggregate and navigation were deposit-only.
- Outcome: Public now has a localized `/loans` catalog, enabled navigation/footer links, lending-aware list/detail/compare cards, and loan-specific rate, term, payment, amount, and prepayment fields. Deposit-only purpose/fee/minimum-deposit controls are not shown for loans. Aggregate refresh now projects active canonical Mortgage, Personal Loan, and Line of Credit rows, and preserves a safe numeric lending display rate from grounded payload fields. Credit Card remains outside this catalog. Collection plans now carry the registered lending family, preventing a mortgage collection from falling back to `deposit`.
- Live verification: B2B Mortgage collection `collection_m5x_wgxkLzh42qgV` completed without failures. It created fresh `Mortgage renewal` (`cand-a5954efdbc6f297a`) and `Mortgage refinancing` (`cand-46a314440defa9cc`) candidates, both validation-pass and `in_review`; an older duplicate renewal candidate was superseded. No lending canonical product or public projection existed before this run, so no loan is publicly shown until an operator makes the required approval decision.
- Decisions: never auto-publish a collection candidate solely to populate the Loan catalog. The user-approved catalog covers Mortgage, Personal Loan, and Line of Credit only; Credit Card stays separate.
- Key files: `app/public/src/app/loans/page.tsx`, `product-grid-surface.tsx`, `product-detail-surface.tsx`, `public-query.ts`, `api/service/api_service/public_common.py`, `public_products.py`, `aggregate_refresh.py`, `worker/pipeline/fpds_aggregate_refresh/`, `source_catalog.py`.
- Verification: API full suite `187` passed; Worker full suite `127` passed; Public `pnpm run typecheck` passed; Public `pnpm run build` passed and generated `/loans`; `git diff --check` passed.
- Next step: review and approve or reject the two new B2B Mortgage candidates in Admin Review Queue. Once a candidate is approved and aggregate refresh completes, it will appear at `/loans` without any further code change.

## 2026-07-14 - Multi-Bank Runs and Problem-First Review Hardening

- WBS: `4.2`, `4.3`, `4.4`, `4.5`, `5.15`, `5.16`, collection QA hardening
- Status: `done`
- Goal: inspect the current Runs and active Review Queue, remove safely automatable duplicate/noise cases, improve future collection across banks and product types, and make unavoidable human decisions concise and field-editable.
- Why now: collection `collection_TncoSuZwjn6Mhd9X` completed 21 runs but left eight active B2B reviews. Four GIC tasks represented two products through locale/host aliases, four Mortgage tasks represented two products twice, candidate fields contained navigation text, and all seven Bridgewater runs had failed because a `www` homepage redirected to the apex host outside the literal allowlist. Several BMO/B2B runs also rejected strong named-detail candidates after whole-page navigation terms inflated negative scores.
- Outcome: homepage discovery now treats `www`/apex as one bounded bank host, permits high-confidence confirmed product identity to overcome navigation-wide negatives while retaining hard scope vetoes, collapses same-title/heading detail aliases, and deduplicates byte-identical target snapshots before normalization. Registered `product_family` is carried into collection plans. Final Runs summaries now represent the full source scope and preserve upstream failures instead of showing only the last stage. Normalization removes navigation and non-value rate copy, refuses corporate ownership percentages as deposit rates, prevents bank-name-only supporting evidence matches, and reduces broad withdrawal copy to an explicit limit. Newer exact logical-product review tasks supersede older active duplicates with system audit events.
- Review UX: Queue and detail use one `review_diagnosis` contract with category, concise headline, affected fields, and an actual review action. Detail uses the union of expected, collected, evidence-linked, and current fields; missing/suspect rows come first, values are editable inline, evidence expands in the row, recommendation controls CTA priority, and arbitrary raw-field editing is an advanced fallback. Re-edits persist the prior approved payload so a later correction does not restore old agent values.
- Live verification: first B2B GIC rerun `collection_tgiG0xYdX-gd15y_` reduced four detail candidates to two but exposed a corporate-form `25%` ownership value incorrectly merged as a rate. After the generic evidence-safety fix, `collection_Pme_NfK9hgLM2_7R` produced exactly two candidates with no `25%` rate and no navigation-contaminated description/application/deposit-insurance/post-maturity fields. Both remain review-required because the official detail pages do not publish required rate/minimum-deposit values. Its final Run correctly reports `3 of 19` sources not reaching the required terminal stage. Six older GIC duplicate/stale reviews and two same-run Mortgage duplicates were auditably superseded, leaving one task per logical product. Bridgewater Savings `collection_KWsPW9y_cgVSRZmj` passed the formerly failing apex redirect, captured `10/10` snapshots, produced one `2.70%` candidate, and created zero review tasks. Follow-up `collection_8enjijAejDwwJNjo` also produced one pass candidate and zero reviews; its final payload retains the grounded `2.70%` rate and CDIC evidence, removes `Home`/filler fields, and reduces withdrawal text to `One free withdrawal a month.`
- Active Queue after cleanup: four tasks: B2B Short-Term GIC and Long-Term GIC (`missing_fields`, edit/approve after sourcing the unavailable values), plus Mortgage refinancing and renewal (`suspect_fields`, inline correction of listed navigation/non-value fields). Mortgage is active in the Product Type Registry under `lending`, with 28 active bank-coverage rows and an active Canadian generic taxonomy fallback; it can be recollected when current lending terms need to replace the older source-time payloads.
- Key files: `api/service/api_service/source_catalog.py`, `source_collection_runner.py`, `review_diagnosis.py`, `review_queue.py`, `review_detail.py`, `worker/pipeline/fpds_normalization/service.py`, `supporting_merge.py`, `fpds_rate_safety.py`, `app/admin/src/components/fpds/admin/review-queue-results.tsx`, `review-detail-surface.tsx`, `app/admin/src/lib/admin-api.ts`, `docs/03-design/admin-information-architecture.md`, `homepage-discovery-scoring-enhancement.md`
- Decisions: duplicate review coalescing requires exact country/bank/family/type/product-name identity and detail-source roles; it never approves the proposal. Same-product page collapse requires confirmed page title and heading identity. Missing official values stay human-reviewable rather than being inferred. Domain aliases strip only a leading `www.` and do not widen the fetch allowlist to unrelated hosts.
- Verification:
  - API full suite: `186` passed.
  - Worker full suite: `126` passed.
  - Admin: `pnpm run typecheck` passed; `pnpm run build` passed with all `23` static pages generated.
  - Focused post-live rate/normalization suite: `51` passed.
  - `git diff --check` passed.
- Known issues: B2B GIC official pages still omit comparable rates and minimum deposits, so two operator decisions remain legitimate. Existing Mortgage candidates retain source-time noisy values but the new Review UI identifies and edits them directly; Mortgage coverage is active and can be recollected when a fresh lending run is required. Local collection logs and registries remain as dev evidence.
- Next step: review the four remaining B2B tasks through the normal UI; run Mortgage collection when a refreshed source payload is needed.

## 2026-07-13 - Runs and Review Queue Collection Accuracy Hardening

- WBS: `4.2`, `4.5`, `5.15`, `5.16`, collection QA hardening
- Status: `done`
- Goal: diagnose current Operations Runs and Queued Review Queue items, automate every safely resolvable case with bank/product-generic rules, and make any remaining human review faster and clearer.
- Why now: the active Alterna queue contained savings/GIC candidates with missing rates plus a linked PDF treated as a product, while earlier completed-partial lending runs lacked retry and two bad auto-promotions remained active publicly.
- Outcome: parser v2 preserves heading-only values and nested rate cards; parsed documents are now versioned per snapshot/parser; only `detail` sources produce candidates; generated supporting HTML is retained as evidence; retail discovery excludes clear business/commercial pages; rate safety suppresses redemption percentages; extraction fixes fee-waiver direction, registered/tax/navigation contamination, maturity-only redeemability, promotion boilerplate, and post-maturity noise. Generic supporting-rate merge now replaces invalid GIC zero placeholders and builds grounded term tables. Completed-partial collection runs are retryable. Review Queue rows now show source role, missing expected fields, and a suggested action. A newer approved same-detail-source candidate automatically supersedes older active reviews with audit history.
- Live verification: Alterna Savings collection `collection_Goosj-QQ2YmvpPfC` approved `cand-706062bfb55d3fe6` at `1.05%` with no review. Alterna GIC collection `collection_IgRmWSN6nXoHbAJc` completed cleanly, approved `cand-9a2156c937e5e906`, and created zero review tasks; DB values are standard/public/12-month `2.65%` with 1/2/3/4/5-year term rates `2.65/2.85/3.10/3.25/3.30%`, while false introductory, registered-plan, and post-maturity fields are absent.
- Database: applied `0023_versioned_parsed_documents.sql` to dev after the first parser-v2 run exposed the historical one-parsed-document-per-snapshot uniqueness constraint. The failed GIC attempt was retried through the supported run-retry path and completed.
- Outcome after Product Owner approval: retracted `cand-324e94861d70de31` (linked PDF-derived 20% GIC), `cand-c93e5b9d7e13cec0` (out-of-scope Small Business eChequing), and `cand-db25b724324d7925` (linked-PDF Queue task). Products `prod_Dy_L58___l1FzOcS` and `prod_K-MXTPAc9ZP3JYQn` are `inactive`. Superseded same-source review tasks for `cand-e19255488c3ee953`, `cand-bef2904f4e538da8`, and `cand-44a408a2dce7636b` now have candidate state `superseded` and review state `rejected` with system audit events. Aggregate request `aggreq_2GRzBwVK_9HSsP_b` completed as snapshot `agg_9J6Z09MBdCIdwK8Y`; active Queue is `0`; public API-equivalent active-only retrieval has `20` products and excludes both retracted product ids.
- Key files: `api/service/api_service/source_catalog.py`, `source_registry.py`, `source_catalog_collection_runner.py`, `candidate_auto_promotion.py`, `candidate_safety_remediation.py`, `review_queue.py`, `run_retry.py`, `worker/pipeline/fpds_parse_chunk/`, `fpds_extraction/service.py`, `fpds_normalization/supporting_merge.py`, `fpds_rate_safety.py`, `app/admin/src/components/fpds/admin/review-queue-results.tsx`, `db/migrations/0023_versioned_parsed_documents.sql`
- Decisions: supporting/linked sources are evidence-only; missing source role routes to review instead of publication; explicit non-detail role is rejected before canonical upsert; business/commercial pages do not enter retail product scope; exact same-detail-source success may close older queued/deferred tasks, but unrelated or genuinely ambiguous tasks remain human decisions.
- Verification:
  - API full suite: `179` passed.
  - Worker full suite: `123` passed.
  - Admin: `pnpm run typecheck` passed; `pnpm run build` passed with all `23` static pages generated.
  - Focused extraction/normalization/evidence/rate suite: `93` passed.
  - `git diff --check` passed.
- Known issues: local collection logs/registry artifacts are retained as run evidence and were not deleted. Raw snapshot history retains inactive projection rows by design, while the public API always filters to `status='active'`.
- Next step: resume normal multi-bank collection monitoring; new collection cases now use the generalized safety and review rules from this slice.

## 2026-07-13 - Medium Reasoning for Quality-Sensitive Product Collection

- WBS: `5.15`, `5.16`, AI-assisted discovery and worker-runtime hardening follow-on
- Status: `done`
- Goal: use GPT-5.6 Luna's default `medium` reasoning only for homepage product-detail classification and dynamic product extraction or normalization, while retaining `none` for the high-volume product-type keyword generator.
- Why now: the Product Owner chose higher default reasoning for the collection decisions where semantic judgment and evidence-grounded mapping most affect product data quality.
- Outcome: removed the explicit `reasoning.effort="none"` field from the homepage parallel scorer and the shared dynamic extraction/normalization Responses runtime. Omitting the field lets `gpt-5.6-luna` use its documented `medium` default. The product-type discovery-keyword generator remains explicitly at `none`; no prompt, JSON schema, parser, validation, or review-routing rule changed.
- Key files: `api/service/api_service/source_catalog.py`, `worker/pipeline/fpds_ai_runtime.py`, `api/service/tests/test_source_catalog.py`, `worker/pipeline/tests/test_ai_runtime.py`, `docs/03-design/dev-prod-environment-spec.md`
- Decisions: apply the higher effort only to the two quality-sensitive collection stages, not globally. This supersedes the prior all-path `none` compatibility baseline while preserving the keyword generator's low-latency behavior.
- Verification:
  - `uv run --directory api/service python -m unittest tests.test_source_catalog tests.test_product_types` -> `76` passed.
  - `uv run python -m unittest worker.pipeline.tests.test_ai_runtime worker.pipeline.tests.test_extraction worker.pipeline.tests.test_normalization` -> `81` passed.
  - Request-construction tests confirm the homepage scorer and dynamic runtime omit `reasoning`; the stage-specific static test confirms the keyword generator retains `reasoning.effort="none"`.
- Known issues: the first representative collection at `medium` has not yet been run, so its quality, latency, and cost effect is unmeasured in FPDS production-like data.
- Next step: compare a representative collection's structured-output validity, false-positive detail rate, latency, and cost with the prior `none` baseline before expanding `medium` to any other stage.

## 2026-07-13 - GPT-5.6 Luna Runtime Migration

- WBS: `5.15`, AI-assisted discovery and worker-runtime hardening follow-on
- Status: `done` for repository and configured dev environment
- Goal: replace the active FPDS GPT-5.4 mini runtime defaults with the requested GPT-5.6 Luna model while preserving the existing Responses API structured-output contracts and the prior low-latency operating behavior.
- Why now: the Product Owner requested that all current GPT-5.4 mini execution paths move to GPT-5.6 Luna.
- Outcome: changed the Worker shared OpenAI runtime, Admin homepage parallel scorer, Product Type keyword generator, tracked dev/prod environment examples, and the configured dev environment to `gpt-5.6-luna`. The model is available to the configured dev API project (`GET /v1/models/gpt-5.6-luna` returned `200`). All three Responses request builders now explicitly send `reasoning.effort="none"`, preserving GPT-5.4 mini's effective default instead of silently taking GPT-5.6's `medium` default. Existing prompts, JSON schemas, endpoint choice, error handling, and token/cost aggregation were intentionally retained.
- Not done: no optional GPT-5.6 Pro mode, persisted reasoning, prompt-cache change, Programmatic Tool Calling, multi-agent behavior, or prompt rewrite was added; there was no measured regression that required it.
- Key files: `.env.dev.example`, `.env.prod.example`, `worker/pipeline/fpds_ai_runtime.py`, `worker/pipeline/tests/test_ai_runtime.py`, `api/service/api_service/source_catalog.py`, `api/service/api_service/product_types.py`, `api/service/tests/test_source_catalog.py`, `worker/pipeline/tests/test_extraction.py`, `worker/pipeline/tests/test_normalization.py`, `docs/03-design/dev-prod-environment-spec.md`
- Decisions: `gpt-5.6-luna` is the exact API slug for the Product Owner's requested GPT-5.6 Luna tier; it fits FPDS's bounded extraction, classification, routing, and high-volume structured-output workloads. Keep `reasoning.effort=none` as the compatibility baseline and evaluate any higher effort separately with representative collection traces.
- Verification:
  - Official OpenAI model guidance confirmed the `gpt-5.6-luna` slug and Luna workload role.
  - Configured dev OpenAI project model lookup: `gpt-5.6-luna`, HTTP `200`.
  - `uv run --directory api/service python -m unittest tests.test_source_catalog tests.test_product_types` -> `75` passed.
  - `uv run python -m unittest worker.pipeline.tests.test_ai_runtime worker.pipeline.tests.test_extraction worker.pipeline.tests.test_normalization` -> `81` passed.
  - `git diff --check` -> passed.
- Known issues: a deployed production secret/configuration store is outside this workspace. Before production rollout, set `FPDS_LLM_MODEL=gpt-5.6-luna` there and verify model access with the production OpenAI project; the repository defaults and production example are already updated.
- Next step: on the next representative production-like collection, compare structured-output validity, latency, token usage, and estimated cost against the prior GPT-5.4 mini baseline before considering a different reasoning effort.

## 2026-07-13 - Unframed Bank Logos and Official Asset Refresh

- WBS: `5.9`, `5.15` UI and bank-registry hardening follow-on
- Status: `done`
- Goal: show bank logos directly, without an unnecessary logo card, in both FPDS Public and Admin; replace unreliable favicon-only defaults with verified official brand assets wherever public assets are available.
- Why now: the Public and Admin bank presentations used bordered white logo containers, while most recognized Canadian banks depended on a generic favicon URL that could be visually weak or fail to resolve.
- Outcome: Public `BankLogo`, Admin bank-list marks, and the Admin bank-detail preview now render unframed. Public failures degrade to a plain, accessible bank-code identifier instead of a bordered placeholder. A new `0022` migration replaces 22 recognized-bank favicon defaults with official logo assets, preserves operator-supplied custom logo URLs, and was applied to dev. The active Canadian registry now has logo metadata for all 28 banks, including 22 full official logo assets; the remaining six use official favicon fallback because a full asset was blocked, retired, or not safely discoverable.
- Not done: no inactive/retired institution was removed from the bank registry, and no unverified third-party logo asset was introduced.
- Key files: `app/public/src/components/fpds/public/bank-logo.tsx`, `app/admin/src/components/fpds/admin/bank-registry-surface.tsx`, `app/admin/src/components/fpds/admin/bank-detail-dialog-content.tsx`, `db/migrations/0022_bank_logo_asset_refresh.sql`, `db/README.md`, `app/public/README.md`, `docs/03-design/source-registry-refresh-and-approval-policy.md`, `api/service/tests/test_source_catalog.py`
- Decisions: official bank-hosted assets are preferred; an official favicon is permitted only as a resilience fallback; logo metadata migrations update only the seed favicon value (or a missing value) and never replace an operator custom URL.
- Verification:
  - Verified all 22 refreshed official logo URLs returned `200`; SVG/PNG assets were returned for each (Oaken returns its binary logo behind a generic content-type header).
  - Applied `db/migrations/0022_bank_logo_asset_refresh.sql` to the configured dev database: `UPDATE 22`, migration-history insert succeeded.
  - Dev DB read-back: 28 active Canadian banks have `logo_url`; 22 use full official-logo assets; migration history confirms `0022_bank_logo_asset_refresh.sql`.
  - `uv run --directory api/service python -m unittest tests.test_source_catalog` -> `57` passed.
  - `pnpm run typecheck` in `app/public` and `app/admin` -> passed.
  - `pnpm run build` in `app/public` and `app/admin` -> passed; Public generated 6 routes and Admin generated 23 routes.
- Known issues: a small number of brands remain on official favicon fallback because their full logo asset cannot presently be verified without using an untrusted third-party source; their display is still stable and unframed.
- Next step: re-check fallback brands only when their official sites publish stable public wordmark assets or when the Product Owner changes the recognized-bank registry scope.

## 2026-07-13 - Review Queue False-Positive Collection Hardening

- WBS: `4.2` to `4.4`, `5.15`, `5.16` hardening follow-on
- Status: `done`
- Goal: explain the four active queued tasks, prevent the same class of collection false positive across banks and Product Types, and make legitimate manual review faster and safer.
- Why now: one Alterna chequing collection created four validation-error review tasks from support/service/rates pages even though the AI discovery scorer had classified every page as supporting rather than product detail.
- Outcome: all four tasks came from `collection_xgYa5LlD31QA807u` / `run_20260705_045036_alterna_chequing_collect_ifLUf0ZH`: Wire Transfers (`0.5558`), Debit Cards (`0.5158`), External Account Transfers (`0.5919`), and Chequing & Savings Rates (`0.5968`). Each became `required_field_missing` because page evidence counted broad/repeated feature terms and `strong_page_evidence_detail_override` overruled the AI supporting/not-product classification. Discovery now separates product identity from attributes, counts distinct attribute terms, defines the AI score scale and constrained reasons, honors support/not-detail vetoes, and inactivates only explicitly rejected non-seed autogenerated detail rows after successful rediscovery. Review Detail now exposes discovery role/rationale and missing expected fields; Review Queue uses active bank registry options, keeps only safe bulk defer, and uses a Product Type-neutral field/evidence focus.
- Not done: the four historical review tasks were deliberately not auto-resolved; they remain auditable legacy tasks for an operator to reject or otherwise decide. No validation/confidence threshold was lowered, and generic/new Product Types remain review-first.
- Key files: `api/service/api_service/source_catalog.py`, `api/service/api_service/review_detail.py`, `api/service/tests/test_source_catalog.py`, `api/service/tests/test_review_detail.py`, `app/admin/src/app/admin/reviews/page.tsx`, `app/admin/src/components/fpds/admin/review-queue-surface.tsx`, `app/admin/src/components/fpds/admin/review-queue-results.tsx`, `app/admin/src/components/fpds/admin/review-detail-surface.tsx`, `app/admin/src/lib/admin-api.ts`, `app/admin/src/lib/admin-i18n.ts`, `README.md`, `app/admin/README.md`, `docs/03-design/homepage-discovery-scoring-enhancement.md`, `docs/03-design/source-registry-refresh-and-approval-policy.md`
- Decisions: valid ambiguity still routes to review; only explicit successful rejection can remove an autogenerated detail from active scope; transient fetch failures and seed sources are preserved; bulk approve/reject require task-level evidence inspection.
- Verification:
  - `api/service/.venv/Scripts/python.exe -m unittest tests.test_source_catalog tests.test_source_catalog_collection_runner tests.test_review_detail tests.test_review_detail_route tests.test_review_queue tests.test_candidate_auto_promotion` -> `81` passed.
  - Full API discovery -> `166/167` passed in one run; the sole config-fixture failure was caused by the host `FPDS_ALLOWED_PUBLIC_ORIGINS` override, and `tests.test_config` passed `2/2` when rerun with that override cleared for the test process.
  - `uv run python -m unittest worker.pipeline.tests.test_extraction worker.pipeline.tests.test_normalization worker.pipeline.tests.test_validation_routing` -> `92` passed.
  - `pnpm run typecheck` in `app/admin` passed.
  - `pnpm run build` in `app/admin` passed with all `23` static pages generated.
  - Live dev rerun `collection_M0Rg6AfUkQgqZtw6` / `run_20260713_125516_alterna_chequing_collect_3XPixi_W` completed with `2/2` sources successful, two validation-pass candidates auto-promoted, no partial failure, and `0` new review tasks. Wire Transfers, External Account Transfers, and Chequing & Savings Rates are inactive with `rejected_by_homepage_detail_validation`; Debit Cards is no longer a candidate-producing detail.
- Known issues: the active queue still includes the four historical tasks by design; their final rejection is an operator decision, not a collection repair side effect.
- Next step: use Review Detail to reject the four historical support-page tasks when the Product Owner wants the queue cleared; monitor future bank/Product Type collections for newly observed false-positive patterns rather than weakening the general review safeguards.

## 2026-07-05 - Canada Lending Product Type Baseline

- WBS: `5.16`, lending product type onboarding follow-on
- Status: `done`
- Goal: register Canadian retail lending Product Types before the Product Owner runs future FPDS Admin collection, and make the existing collection path preserve lending family metadata.
- Why now: the Product Owner requested Product Type registration for lending products while keeping actual product collection operator-triggered from FPDS Admin.
- Outcome: added migration `0019_canada_lending_product_types.sql`, registered `credit-card`, `mortgage`, `personal-loan`, and `line-of-credit` under `product_family=lending`, and added active generic `other` taxonomy fallback rows. Product Type list/map queries now include all product families, create/update can persist `product_family`, source collection plans carry product family into temporary registry payloads, and extraction artifacts derive `product_family` from source metadata instead of hard-coding `deposit`. Homepage discovery now has lending-specific profile, exclusion, supporting-source, and page-evidence terms.
- Not done: no lending product collection run was started; no lending-specific parser, public dashboard behavior, or auto-publish path was added.
- Key files: `db/migrations/0019_canada_lending_product_types.sql`, `api/service/api_service/product_types.py`, `api/service/api_service/source_catalog.py`, `api/service/api_service/source_registry.py`, `api/service/api_service/source_collection_runner.py`, `worker/pipeline/fpds_extraction/service.py`, `worker/pipeline/fpds_validation_routing/persistence.py`, `README.md`, `db/README.md`, `docs/03-design/source-registry-refresh-and-approval-policy.md`, `docs/03-design/homepage-discovery-scoring-enhancement.md`
- Decisions: FPDS canonical codes use hyphens (`credit-card`, `personal-loan`, `line-of-credit`) even when an operator enters underscores; lending remains generic AI extraction/manual review until specialized lending parsers and publish rules are separately approved.
- Verification:
  - `uv run --directory api/service python -m unittest tests.test_product_types tests.test_source_catalog tests.test_source_registry tests.test_source_collection_runner tests.test_source_catalog_collection_runner`
  - `uv run python -m unittest worker.pipeline.tests.test_extraction.ExtractionServiceTests.test_lending_source_metadata_sets_product_family_in_artifact`
  - Applied migration `db/migrations/0019_canada_lending_product_types.sql` to the configured dev database.
  - DB read-back confirmed four active lending Product Types with `fallback_policy=generic_ai_review` and four active `lending/*/other` taxonomy rows.
- Known issues: the Product Owner still needs to add bank coverage and run actual lending source collection from FPDS Admin.
- Next step: in FPDS Admin, attach the desired lending Product Types to banks, collect, then inspect generated sources and review-queued candidates before approving any canonical data.

## 2026-06-16 - Dev Product Collection Incremental Reset For Recollection

- WBS: `5.15`, `5.16`, admin collection retest preparation
- Status: `done`
- Goal: delete the newly accumulated product-information collection artifacts while preserving bank and product-type setup before another recollection test.
- Why now: the Product Owner requested deletion of all DB and S3-backed data produced by the product collection process, excluding bank and product-type information.
- Outcome: deleted the new dev DB collection/downstream artifacts: generated source rows, ingestion run, run-source links, source documents, snapshots, parsed documents, evidence chunks and embeddings, model and LLM usage records, normalized candidates, field evidence links, canonical products, product versions, change events, aggregate refresh rows, public projections, dashboard snapshots, and collection/review/run/product-targeted audit events. Deleted all S3 objects under `s3://fpds-dev-private/dev/`. Removed local collection tmp artifact directories under `tmp/source-catalog-collections/`, `tmp/source-collections/`, and `tmp/aggregate-refresh/`.
- Not done: no bank, product-type, taxonomy, source-catalog configuration, auth/config, or migration rows were changed; no new collection run was started.
- Key files: `tmp/fpds_collection_reset_common.py`, `tmp/fpds_collection_reset_counts.py`, `tmp/fpds_collection_reset_execute.py`, `tmp/fpds_admin_collection_goal_tool.py`, `docs/00-governance/development-journal.md`
- Decisions: preserved `bank`, `product_type_registry`, `taxonomy_registry`, `source_registry_catalog_item`, auth/session/signup, processing policy config, and migration history rows so the next admin recollection can start from the configured bank/product/source-catalog setup.
- Verification:
  - `.\api\service\.venv\Scripts\python.exe tmp\fpds_collection_reset_counts.py --env-file .env.dev`
  - `.\api\service\.venv\Scripts\python.exe tmp\fpds_collection_reset_execute.py --env-file .env.dev`
  - `.\api\service\.venv\Scripts\python.exe tmp\fpds_collection_reset_counts.py --env-file .env.dev`
  - `api\service\.venv\Scripts\python.exe tmp\fpds_admin_collection_goal_tool.py --env-file .env.dev state`
  - Pre-delete DB counts included `source_registry_item=10`, `ingestion_run=1`, `source_document=9`, `source_snapshot=9`, `run_source_item=9`, `parsed_document=9`, `evidence_chunk=354`, `evidence_chunk_embedding=354`, `model_execution=20`, `llm_usage_record=20`, `normalized_candidate=5`, `field_evidence_link=250`, `canonical_product=5`, `product_version=5`, `change_event=5`, `aggregate_refresh_request=1`, `aggregate_refresh_run=1`, `public_product_projection=5`, `dashboard_metric_snapshot=1`, `dashboard_ranking_snapshot=10`, and `dashboard_scatter_snapshot=5`.
  - Deleted `65` S3 objects under `s3://fpds-dev-private/dev/`; post-delete object storage summary is `object_count=0`, `total_bytes=0`.
  - Post-delete collection/output table counts are `0`, collection-related `audit_event` count is `0`, and preserved setup counts include `bank=5`, `product_type_registry=3`, `taxonomy_registry=14`, `source_registry_catalog_item=15`.
  - Admin collection state reports 5 active banks, 3 active product types, 15 active catalog items, all artifact counts `0`, and no latest collections.
  - Local collection tmp artifact directories under `tmp/source-catalog-collections/`, `tmp/source-collections/`, and `tmp/aggregate-refresh/` are absent.
- Known issues: no new collection run was started in this slice.
- Next step: rerun the FPDS admin collection flow from the preserved bank/product/source-catalog setup and inspect refreshed candidates before approval or aggregate refresh decisions.

## 2026-06-16 - Dev Product Collection Data Reset For Recollection

- WBS: `5.15`, `5.16`, admin collection retest preparation
- Status: `done`
- Goal: delete all product-information collection artifacts while preserving bank and product-type setup before a clean recollection test.
- Why now: the Product Owner requested deletion of all DB and S3-backed data produced by the product collection process, excluding bank and product-type information.
- Outcome: deleted dev DB collection/downstream artifacts: generated source rows, ingestion runs, run-source links, source documents, snapshots, parsed documents, evidence chunks and embeddings, model and LLM usage records, normalized candidates, field evidence links, canonical products, product versions, change events, aggregate refresh requests/runs, public projections, dashboard snapshots, and collection/review/run/product-targeted audit events. Deleted all S3 objects under `s3://fpds-dev-private/dev/`. Removed local collection tmp artifact directories under `tmp/source-catalog-collections/`, `tmp/source-collections/`, and `tmp/aggregate-refresh/`.
- Not done: no bank, product-type, taxonomy, source-catalog configuration, auth/config, or migration rows were changed; no new collection run was started.
- Key files: `tmp/fpds_collection_reset_common.py`, `tmp/fpds_collection_reset_counts.py`, `tmp/fpds_collection_reset_execute.py`, `tmp/fpds_admin_collection_goal_tool.py`, `docs/00-governance/development-journal.md`
- Decisions: preserved `bank`, `product_type_registry`, `taxonomy_registry`, `source_registry_catalog_item`, auth/session/signup, processing policy config, and migration history rows so the next admin recollection can start from the configured bank/product/source-catalog setup.
- Verification:
  - `.\api\service\.venv\Scripts\python.exe tmp\fpds_collection_reset_counts.py --env-file .env.dev`
  - `.\api\service\.venv\Scripts\python.exe tmp\fpds_collection_reset_execute.py --env-file .env.dev`
  - `.\api\service\.venv\Scripts\python.exe tmp\fpds_collection_reset_counts.py --env-file .env.dev`
  - `api\service\.venv\Scripts\python.exe tmp\fpds_admin_collection_goal_tool.py --env-file .env.dev state`
  - Pre-delete DB counts included `source_registry_item=38`, `ingestion_run=4`, `source_document=31`, `source_snapshot=31`, `run_source_item=34`, `parsed_document=31`, `evidence_chunk=950`, `evidence_chunk_embedding=950`, `model_execution=72`, `llm_usage_record=71`, `normalized_candidate=17`, `field_evidence_link=794`, `canonical_product=17`, `product_version=17`, `change_event=17`, `aggregate_refresh_request=4`, `aggregate_refresh_run=4`, `public_product_projection=43`, `dashboard_metric_snapshot=4`, `dashboard_ranking_snapshot=50`, and `dashboard_scatter_snapshot=5`.
  - Deleted `223` S3 objects under `s3://fpds-dev-private/dev/`; post-delete object storage summary is `object_count=0`, `total_bytes=0`.
  - Post-delete collection/output table counts are `0`, collection-related `audit_event` count is `0`, and preserved setup counts include `bank=5`, `product_type_registry=3`, `taxonomy_registry=14`, `source_registry_catalog_item=15`.
  - Admin collection state reports 5 active banks, 3 active product types, 15 active catalog items, all artifact counts `0`, and no latest collections.
  - Local collection tmp artifact directories under `tmp/source-catalog-collections/`, `tmp/source-collections/`, and `tmp/aggregate-refresh/` are absent.
- Known issues: no new collection run was started in this slice.
- Next step: rerun the FPDS admin collection flow from the preserved bank/product/source-catalog setup and inspect refreshed candidates before approval or aggregate refresh decisions.

## 2026-06-16 - Demo Architecture And Collection Process Rewrite

- WBS: `5.15`, `5.16`, customer demo documentation
- Status: `done`
- Goal: rewrite the customer demo architecture and collection-process explanation from the Product Owner-provided FPDS architecture and collection process diagrams.
- Why now: the Product Owner requested Section 6 of the demo scenario to explain architecture and collection flow based on the uploaded images.
- Outcome: replaced the short Section 6 explanation with a clearer architecture overview covering external systems, FPDS platform boundary, public/operator consumers, data stores, public evidence boundary, and public projection rules. Rewrote the collection process as a 10-step evidence-to-public-projection flow from admin scope selection through source discovery, snapshot, parse/chunk, retrieval, extraction, normalization, validation, canonical upsert, audit, and aggregate refresh.
- Not done: no implementation code, runtime behavior, database schema, or public/admin UI was changed.
- Key files: `docs/01-planning/fpds-customer-demo-scenario.md`, `docs/00-governance/development-journal.md`
- Decisions: kept BX-PF as interface-ready/future-facing in the demo explanation and kept public evidence trace explicitly admin-only.
- Verification: reviewed the updated Section 6 rendered text in-place and checked the git diff is limited to the requested documentation section plus this journal entry.
- Known issues: no runtime test was needed because this is a documentation-only update.
- Next step: use the revised Section 6 as the narration baseline for the FPDS customer demo architecture/process walkthrough.

## 2026-06-15 - Dev Product Collection Reset For Recollection Retest

- WBS: `5.15`, `5.16`, admin collection retest preparation
- Status: `done`
- Goal: delete all data produced by product information collection while preserving bank and product-type setup before another clean recollection test.
- Why now: the Product Owner requested removal of all product collection DB artifacts and S3-backed object storage artifacts, excluding bank and product-type information.
- Outcome: deleted dev DB collection/downstream output artifacts: generated source rows, ingestion runs, run-source links, source documents, snapshots, parsed documents, evidence chunks and embeddings, model and LLM usage records, normalized candidates, field evidence links, canonical products, product versions, change events, aggregate refresh requests/runs, public projections, dashboard snapshots, and collection/review/run/product-targeted audit events. Deleted all S3-compatible objects under `s3://fpds-dev-private/dev/`. Removed local collection tmp artifact directories under `tmp/source-catalog-collections/`, `tmp/source-collections/`, and `tmp/aggregate-refresh/`.
- Not done: no bank, product-type, taxonomy, source-catalog configuration, auth/config, or migration rows were changed; no new collection run was started.
- Key files: `tmp/fpds_collection_reset_common.py`, `tmp/fpds_collection_reset_counts.py`, `tmp/fpds_collection_reset_execute.py`, `tmp/fpds_admin_collection_goal_tool.py`, `docs/00-governance/development-journal.md`
- Decisions: preserved `bank`, `product_type_registry`, `taxonomy_registry`, `source_registry_catalog_item`, auth/session/signup, processing policy config, and migration history rows so the next admin recollection can start from the configured bank/product/source-catalog setup.
- Verification:
  - `.\api\service\.venv\Scripts\python.exe tmp\fpds_collection_reset_counts.py --env-file .env.dev`
  - `.\api\service\.venv\Scripts\python.exe tmp\fpds_collection_reset_execute.py --env-file .env.dev`
  - `.\api\service\.venv\Scripts\python.exe tmp\fpds_collection_reset_counts.py --env-file .env.dev`
  - `api\service\.venv\Scripts\python.exe tmp\fpds_admin_collection_goal_tool.py --env-file .env.dev state`
  - Pre-delete DB counts included `source_registry_item=38`, `ingestion_run=4`, `source_document=31`, `source_snapshot=31`, `run_source_item=34`, `parsed_document=31`, `evidence_chunk=950`, `evidence_chunk_embedding=950`, `model_execution=72`, `llm_usage_record=72`, `normalized_candidate=17`, `field_evidence_link=794`, `canonical_product=17`, `product_version=17`, `change_event=17`, `aggregate_refresh_request=4`, `aggregate_refresh_run=4`, `public_product_projection=45`, `dashboard_metric_snapshot=4`, `dashboard_ranking_snapshot=45`, and `dashboard_scatter_snapshot=10`.
  - Deleted `223` S3-compatible objects under `s3://fpds-dev-private/dev/`; post-delete object storage summary is `object_count=0`, `total_bytes=0`.
  - Post-delete collection/output table counts are `0`, collection-related `audit_event` count is `0`, and preserved setup counts include `bank=5`, `product_type_registry=3`, `taxonomy_registry=14`, `source_registry_catalog_item=15`.
  - Admin collection state reports 5 active banks, 3 active product types, 15 active catalog items, all artifact counts `0`, and no latest collections.
  - Local collection tmp artifact directories under `tmp/source-catalog-collections/`, `tmp/source-collections/`, and `tmp/aggregate-refresh/` are absent.
- Known issues: no new collection run was started in this slice.
- Next step: rerun the FPDS admin collection flow from the preserved bank/product/source-catalog setup and inspect refreshed candidates before approval or aggregate refresh decisions.

## 2026-06-15 - Dev Product Collection Data And Storage Reset Before Recollection

- WBS: `5.15`, `5.16`, admin collection retest preparation
- Status: `done`
- Goal: delete all data produced by product information collection while preserving bank and product-type setup before a clean recollection test.
- Why now: the Product Owner requested removal of all product collection DB artifacts and S3-backed object storage artifacts, excluding bank and product-type information.
- Outcome: deleted dev DB collection/downstream output artifacts: generated source rows, ingestion runs, run-source links, source documents, snapshots, parsed documents, evidence chunks and embeddings, model and LLM usage records, normalized candidates, field evidence links, review tasks/decisions, canonical products, product versions, change events, publish rows, aggregate refresh requests/runs, public projections, dashboard snapshots, and collection/review/run/product-targeted audit events. Deleted all S3-compatible objects under `s3://fpds-dev-private/dev/`. Removed local collection tmp artifact directories under `tmp/source-catalog-collections/`, `tmp/source-collections/`, and `tmp/aggregate-refresh/`.
- Not done: no bank, product-type, taxonomy, source-catalog configuration, auth/config, or migration rows were changed; no new collection run was started.
- Key files: `tmp/fpds_collection_reset_common.py`, `tmp/fpds_collection_reset_counts.py`, `tmp/fpds_collection_reset_execute.py`, `tmp/fpds_admin_collection_goal_tool.py`, `docs/00-governance/development-journal.md`
- Decisions: preserved `bank`, `product_type_registry`, `taxonomy_registry`, `source_registry_catalog_item`, auth/session/signup, processing policy config, and migration history rows so the next admin recollection can start from the configured bank/product/source-catalog setup.
- Verification:
  - `.\api\service\.venv\Scripts\python.exe tmp\fpds_collection_reset_counts.py --env-file .env.dev`
  - `.\api\service\.venv\Scripts\python.exe tmp\fpds_collection_reset_execute.py --env-file .env.dev`
  - `.\api\service\.venv\Scripts\python.exe tmp\fpds_collection_reset_counts.py --env-file .env.dev`
  - `api\service\.venv\Scripts\python.exe tmp\fpds_admin_collection_goal_tool.py --env-file .env.dev state`
  - Pre-delete DB counts included `source_registry_item=129`, `ingestion_run=15`, `source_document=105`, `source_snapshot=109`, `parsed_document=107`, `evidence_chunk=2883`, `evidence_chunk_embedding=2883`, `model_execution=327`, `llm_usage_record=327`, `normalized_candidate=98`, `field_evidence_link=4588`, `canonical_product=98`, `product_version=98`, `change_event=98`, `aggregate_refresh_request=15`, `aggregate_refresh_run=15`, `public_product_projection=762`, `dashboard_metric_snapshot=15`, `dashboard_ranking_snapshot=265`, and `dashboard_scatter_snapshot=132`.
  - Deleted `929` S3-compatible objects under `s3://fpds-dev-private/dev/`; post-delete object storage summary is `object_count=0`, `total_bytes=0`.
  - Post-delete collection/output table counts are `0`, collection-related `audit_event` count is `0`, and preserved setup counts include `bank=5`, `product_type_registry=3`, `taxonomy_registry=14`, `source_registry_catalog_item=15`.
  - Admin collection state reports 5 active banks, 3 active product types, 15 active catalog items, all artifact counts `0`, and no latest collections.
  - Local collection tmp artifact directories under `tmp/source-catalog-collections/`, `tmp/source-collections/`, and `tmp/aggregate-refresh/` are absent.
- Known issues: no new collection run was started in this slice.
- Next step: rerun the FPDS admin collection flow from the preserved bank/product/source-catalog setup and inspect refreshed candidates before approval or aggregate refresh decisions.

## 2026-06-11 - Public Main Screen Copy Simplification

- WBS: `5.10`, `5.13`, public UI copy simplification
- Status: `done`
- Goal: remove Product Owner-specified explanatory copy from the FPDS public main screen: `Public snapshot`, the purpose-entry explanatory subtitle, and the scope/snapshot/official-bank trust cue block.
- Why now: the Product Owner asked to simplify the public main screen by removing redundant snapshot/scope/process copy while keeping the comparison entry points.
- Outcome: removed the Home hero eyebrow, removed the shared purpose-entry subtitle and compact trust cue block from public surfaces, changed the filtered Home reset action to use the existing common `Clear` label, and removed the matching EN/KO/JA locale keys. The footer no longer lists a `Public snapshot` item or repeats the aggregate snapshot sentence, while retaining the evidence-boundary note.
- Not done: no public API, aggregate snapshot, product data, methodology route, collection pipeline, or product grid behavior contract was changed.
- Key files: `app/public/src/components/fpds/public/dashboard-surface.tsx`, `app/public/src/components/fpds/public/purpose-entry-points.tsx`, `app/public/src/components/fpds/public/product-grid-surface.tsx`, `app/public/src/components/fpds/public/public-footer.tsx`, `app/public/src/lib/public-locale.ts`, `app/public/README.md`, `docs/03-design/insight-dashboard-metric-definition.md`, `docs/03-design/product-grid-information-architecture.md`
- Decisions: removed the copy at the shared component/locale-resource level instead of hiding only one dashboard instance, so the same explanatory block cannot reappear on `/products` through the shared purpose-entry component.
- Verification:
  - searched `app/public/src`, `app/public/README.md`, and the updated active IA docs for the removed visible English copy and removed locale/component keys
  - in `app/public`: `pnpm run typecheck`
  - in `app/public`: `pnpm run build`
  - root `tests/regression` path is absent
  - `.venv\Scripts\python.exe -m unittest discover -s worker\pipeline\tests\regression -p "test_*.py"` (`2` tests)
  - `api\service\.venv\Scripts\python.exe -m unittest discover -s api\service\tests\regression -p "test_*.py"` (`9` tests)
- Known issues: no browser visual QA was run against a live public API snapshot in this slice; production build verifies renderability but not final visual density with live data.
- Next step: visually review `/dashboard` and `/products` with a live public API snapshot when available.

## 2026-06-11 - Canonical Rate Safety Guardrail For Market-Linked Returns

- WBS: `5.5`, `5.16`, collection quality hardening
- Status: `done`
- Goal: prevent market-linked return caps or full-term return percentages from being collected as canonical annual interest rates, after `Scotiabank Market Linked GICs` produced `60%` in `standard_rate` / `public_display_rate`.
- Why now: the Product Owner reported an impossible collected interest rate and requested a generic fix that helps other banks and product types rather than a narrow Scotiabank exception.
- Outcome: added a shared worker rate-safety guardrail that suppresses implausible annual deposit rates above 25% and percentage contexts that describe index return, full-term return, return caps, principal guarantee, or non-annual return semantics. Wired the guardrail into extraction percent fallback/direct extraction, normalization rate promotion, generic supporting-source rate merge, and validation routing. The specific Scotiabank `60% per year` limitation text no longer becomes `standard_rate` or `public_display_rate`; if such a value reaches validation from another path, it is routed as `invalid_numeric_range`.
- Not done: existing collected DB rows were not mutated in this slice; affected collection output should be regenerated rather than manually patched.
- Key files: `worker/pipeline/fpds_rate_safety.py`, `worker/pipeline/fpds_extraction/service.py`, `worker/pipeline/fpds_normalization/service.py`, `worker/pipeline/fpds_normalization/supporting_merge.py`, `worker/pipeline/fpds_validation_routing/service.py`, `worker/pipeline/tests/test_extraction.py`, `worker/pipeline/tests/test_normalization.py`, `worker/pipeline/tests/test_validation_routing.py`, `docs/03-design/domain-model-canonical-schema.md`
- Decisions: kept `highest_rate` in the Phase 1 golden/profile contract separate because market-linked and fund-linked products may publish maximum full-term return values such as `21%` or `35%`; those values must stay explicitly tagged/noted and must not be reused as annual canonical rate fields.
- Verification:
  - `.venv\Scripts\python.exe -m unittest worker.pipeline.tests.test_extraction.ExtractionServiceTests.test_rate_fallback_ignores_market_linked_return_cap_context worker.pipeline.tests.test_normalization.NormalizationServiceTests.test_suppresses_market_linked_return_cap_as_canonical_rate worker.pipeline.tests.test_normalization.SupportingMergeTests.test_generic_supporting_merge_ignores_market_linked_return_cap_context worker.pipeline.tests.test_validation_routing.ValidationRoutingServiceTests.test_implausible_deposit_rate_is_invalid_numeric_range`
  - `.venv\Scripts\python.exe -m unittest worker.pipeline.tests.test_extraction worker.pipeline.tests.test_normalization worker.pipeline.tests.test_validation_routing`
  - `.venv\Scripts\python.exe -m unittest discover -s worker\pipeline\tests -p "test_*.py"` (`109` tests)
  - root `tests/regression` path is absent
  - `.venv\Scripts\python.exe -m unittest discover -s worker\pipeline\tests\regression -p "test_*.py"` (`2` tests)
  - `api\service\.venv\Scripts\python.exe -m unittest discover -s api\service\tests\regression -p "test_*.py"` (`9` tests)
- Known issues: a clean recollection is still required for persisted candidates that were already collected before this guardrail.
- Next step: rerun the affected Scotiabank GIC collection and verify the Market Linked GIC candidate either omits annual canonical rate fields or uses only source-stated annual posted/guaranteed interest evidence.

## 2026-06-10 - Dev Product Collection Data And Storage Reset Before Recollection

- WBS: `5.15`, `5.16`, admin collection retest preparation
- Status: `done`
- Goal: delete all data produced by product information collection while preserving bank and product-type setup before a clean recollection test.
- Why now: the Product Owner requested removal of all product collection DB artifacts and S3-backed object storage artifacts, excluding bank and product-type information.
- Outcome: deleted dev DB collection/downstream output artifacts: generated source rows, ingestion runs, run-source links, source documents, snapshots, parsed documents, evidence chunks and embeddings, model and LLM usage records, normalized candidates, field evidence links, review tasks/decisions, canonical products, product versions, change events, publish rows, aggregate refresh requests/runs, public projections, dashboard snapshots, and collection/review/run/product-targeted audit events. Deleted all S3-compatible objects under `s3://fpds-dev-private/dev/`. Removed local collection tmp artifact directories under `tmp/source-catalog-collections/`, `tmp/source-collections/`, and `tmp/aggregate-refresh/`.
- Not done: no bank, product-type, taxonomy, source-catalog configuration, auth/config, or migration rows were changed; no new collection run was started.
- Key files: `tmp/fpds_collection_reset_common.py`, `tmp/fpds_collection_reset_counts.py`, `tmp/fpds_collection_reset_execute.py`, `docs/00-governance/development-journal.md`
- Decisions: preserved `bank`, `product_type_registry`, `taxonomy_registry`, `source_registry_catalog_item`, auth/session/signup, processing policy config, and migration history rows so the next admin recollection can start from the configured bank/product/source-catalog setup.
- Verification:
  - `.\api\service\.venv\Scripts\python.exe tmp\fpds_collection_reset_counts.py --env-file .env.dev`
  - `.\api\service\.venv\Scripts\python.exe tmp\fpds_collection_reset_execute.py --env-file .env.dev`
  - `.\api\service\.venv\Scripts\python.exe tmp\fpds_collection_reset_counts.py --env-file .env.dev`
  - `api\service\.venv\Scripts\python.exe tmp\fpds_admin_collection_goal_tool.py --env-file .env.dev state`
  - Pre-delete DB counts included `source_registry_item=39`, `ingestion_run=4`, `source_document=32`, `source_snapshot=32`, `parsed_document=32`, `evidence_chunk=989`, `evidence_chunk_embedding=989`, `model_execution=73`, `llm_usage_record=73`, `normalized_candidate=17`, `field_evidence_link=802`, `canonical_product=17`, `product_version=17`, `change_event=17`, `aggregate_refresh_run=4`, `public_product_projection=43`, `dashboard_metric_snapshot=4`, `dashboard_ranking_snapshot=50`, and `dashboard_scatter_snapshot=5`.
  - Post-delete collection/output table counts are `0`, collection-related `audit_event` count is `0`, and preserved setup counts include `bank=5`, `product_type_registry=3`, `taxonomy_registry=14`, `source_registry_catalog_item=15`.
  - S3-compatible storage prefix `s3://fpds-dev-private/dev/` changed from `object_count=228`, `total_bytes=43,158,843` to `object_count=0`, `total_bytes=0`.
  - Admin collection state reports 5 active banks, 3 active product types, 15 active catalog items, all artifact counts `0`, and no latest collections.
- Known issues: local process command-line inspection through `Get-CimInstance Win32_Process` was denied by OS permissions, so no process list was captured; DB/S3 post-delete counts remained clean.
- Next step: rerun the FPDS admin collection flow from the preserved bank/product/source-catalog setup and inspect refreshed candidates before approval or aggregate refresh decisions.

## 2026-06-09 - Public Purpose Entry And Compare Workspace

- WBS: `5.9`, `5.10`, `5.11`, `5.12`, `5.13`, public UI follow-on
- Status: `done`
- Goal: improve FPDS Public comparison usefulness using benchmark patterns for purpose-led entry, side-by-side comparison, and trust cues while staying inside the approved Canada Big 5 deposit scope.
- Why now: the Product Owner asked for a production-quality public financial-product comparison experience, with benchmark-inspired improvements and no shortcut/demo-grade implementation.
- Outcome: added shared purpose-first entry cards to `/dashboard` and `/products` for everyday banking cost, savings-rate, fixed-term return, and low-entry-amount paths. Added compact trust cues for scope, snapshot freshness, and official-bank confirmation. Added a client-side `/products` comparison workspace where users can select up to four currently rendered products and compare product, field-backed comparison reason, rate, monthly fee, entry amount, term, application method, and official bank page without changing public API contracts.
- Not done: no personalized recommendation, eligibility scoring, account-opening flow, public evidence trace, Admin data model change, or new API endpoint was added.
- Key files: `app/public/src/components/fpds/public/purpose-entry-points.tsx`, `app/public/src/components/fpds/public/product-compare-workspace.tsx`, `app/public/src/components/fpds/public/dashboard-surface.tsx`, `app/public/src/components/fpds/public/product-grid-surface.tsx`, `app/public/src/lib/public-locale.ts`, `app/public/README.md`, `docs/03-design/product-grid-information-architecture.md`, `docs/03-design/insight-dashboard-metric-definition.md`
- Decisions: kept the slice frontend-first because existing public product payloads already expose the needed rate, fee, balance/deposit, term, application, and official-page fields; used existing filters/sorts for purpose entry instead of adding a recommendation model.
- Verification:
  - In `app/public`: `pnpm run typecheck`
  - In `app/public`: `pnpm run build`
  - root `tests/regression` path is absent
  - `api\service\.venv\Scripts\python.exe -m unittest discover -s api/service/tests/regression -p "test_*.py"` (`9` tests)
  - `.venv\Scripts\python.exe -m unittest discover -s worker\pipeline\tests\regression -p "test_*.py"` (`2` tests)
  - Existing local public dev server on `http://localhost:3000`; `GET /dashboard`, `GET /products`, and `GET /methodology` returned HTTP `200`
- Known issues: final visual QA should still be done in a browser with a live public API snapshot to inspect real product density, mobile compare-table scrolling, and localized text wrapping.
- Next step: perform responsive browser QA for `/dashboard` and `/products`, especially compare selection and purpose-entry links, against current aggregate data.

## 2026-06-09 - Public Dashboard Future-Product Footer Polish

- WBS: `5.10`, `5.12`, `5.13`, `5.14` public UI follow-on
- Status: `done`
- Goal: adjust the FPDS Public Home surface so it no longer reads as deposit-only, simplify dashboard ranking/KPI presentation, and add a footer plus compact locale control pattern inspired by Revolut's footer structure.
- Why now: the Product Owner noted that the current public dashboard only shows deposit products today but should not lock the Home copy to deposits because loan products are planned later.
- Outcome: changed Home dashboard copy to product-neutral EN/KO/JA wording, removed the visible Methodology action from Home, moved the Banks KPI before Visible products, removed the visible Top Interest Rate KPI card, and simplified the Top 5 ranking numerals. Added a public footer with brand, route, coverage, data-boundary, and locale-control sections. Replaced the header language select with a compact globe/locale menu shared with the footer.
- Not done: no backend/API contract change, no new public route, no public evidence exposure, and no Revolut branding, copy, or legal content reuse.
- Key files: `app/public/src/components/fpds/public/dashboard-surface.tsx`, `app/public/src/components/fpds/public/public-header.tsx`, `app/public/src/components/fpds/public/public-locale-menu.tsx`, `app/public/src/components/fpds/public/public-footer.tsx`, `app/public/src/app/layout.tsx`, `app/public/src/lib/public-locale.ts`, `app/public/README.md`, `docs/03-design/insight-dashboard-metric-definition.md`
- Decisions: kept `/products` labeled as the current Deposit catalog while making `/dashboard` product-neutral; kept `/methodology` implemented as a direct route but removed it from visible Home actions; used a footer-level data-boundary note instead of adding another methodology card to the main screen.
- Verification:
  - In `app/public`: `pnpm run typecheck`
  - In `app/public`: `pnpm run build`
  - root `tests/regression` path is absent
  - `api\service\.venv\Scripts\python.exe -m unittest discover -s api/service/tests/regression -p "test_*.py"` (`9` tests)
  - `.venv\Scripts\python.exe -m unittest discover -s worker\pipeline\tests\regression -p "test_*.py"` (`2` tests)
  - Local public dev server started from `app/public`; `GET http://localhost:3000/dashboard` returned HTTP `200`
- Known issues: production build verifies renderability, but final visual QA should still be done against a running public API snapshot to inspect real product names, localized footer wrapping, and mobile menu placement.
- Next step: run browser/mobile visual QA for `/dashboard` with the public API service and current aggregate snapshot available.

## 2026-06-08 - Public Premium Fintech UI Simplification

- WBS: `5.9`, `5.10`, `5.11`, `5.13`, `5.14` public UI follow-on
- Status: `done`
- Goal: refresh the FPDS Public dashboard, deposit list, and product detail screens toward a more polished premium fintech experience while keeping public API contracts, locale behavior, and evidence boundaries unchanged.
- Why now: the Product Owner asked to remove low-value public information, simplify bank-logo presentation, add a sort-aware Top 5 list on the product catalog, remove the product-detail Decision Summary block, and raise the overall visual quality without copying Revolut branding.
- Outcome: redesigned the public dashboard hero with live KPI cards, ranking-card presentation, bank coverage, optional single-type scatter, and no visible Recently Changed KPI/ranking, Products by type card, or inline Data notes card. Added a sort-aware Top 5 list above `/products` cards using the existing products API with `page_size=5`. Simplified product cards and product detail to show bank logos without redundant visible bank-name chrome, and moved product-detail official/similar actions into the hero while removing the Decision Summary card. Added a restrained light canvas/header treatment and EN/KO/JA Top 5 labels.
- Not done: no backend/API contract change, no data mocking, no public evidence exposure, and no new UI/animation library.
- Key files: `app/public/src/app/products/page.tsx`, `app/public/src/components/fpds/public/dashboard-surface.tsx`, `app/public/src/components/fpds/public/product-grid-surface.tsx`, `app/public/src/components/fpds/public/product-detail-surface.tsx`, `app/public/src/components/fpds/public/bank-logo.tsx`, `app/public/src/components/fpds/public/public-header.tsx`, `app/public/src/app/globals.css`, `app/public/src/lib/public-locale.ts`, `app/public/README.md`, `docs/03-design/product-grid-information-architecture.md`, `docs/03-design/insight-dashboard-metric-definition.md`
- Decisions: kept the implementation frontend-only; treated the Top 5 list as a second read from the existing public products endpoint rather than a new API; preserved source-derived product text and the public/private evidence boundary; left methodology details on `/methodology` instead of repeating them on the public Home surface.
- Verification:
  - In `app/public`: `pnpm run typecheck`
  - In `app/public`: `pnpm run build`
  - `api\service\.venv\Scripts\python.exe -m unittest discover -s api/service/tests/regression -p "test_*.py"` (`9` tests)
  - `.venv\Scripts\python.exe -m unittest discover -s worker\pipeline\tests\regression -p "test_*.py"` (`2` tests)
  - Local public dev server started from `app/public`; `GET http://localhost:3000/dashboard` returned HTTP `200`
- Known issues: visual QA with real products still requires the public API service and a current aggregate snapshot running locally; without the API, the Next.js route correctly renders the existing API-unavailable state.
- Next step: run browser/mobile QA against `/dashboard`, `/products`, and representative `/products/:productId` pages with the API service and current public aggregate snapshot available.

## 2026-06-07 - Deposit List And Detail Benchmark UI Refresh

- WBS: `5.9`, `5.13`, `5.14` public UI follow-on
- Status: `done`
- Goal: improve `/products` and `/products/[productId]` so users can scan, compare, and inspect deposit products more comfortably using financial comparison-site interaction patterns.
- Why now: the Product Owner asked for the deposit product list and per-product detail screens to be upgraded for stronger usability, design, and UI/UX after reviewing benchmark sites.
- Outcome: added a result-summary strip to the product list with product count, snapshot freshness, active scope, reset action, and dashboard handoff. Reworked product cards into bank/product-type headers, official-bank action, highlight/customer signals, a stable three-metric comparison strip, and a clearer detail action. Reorganized product detail into an overview, decision summary, product-type-specific metric tiles, calculator, product facts, optional term rates, key conditions, and public disclosure sequence. Added EN/KO/JA interface labels for the new UI copy.
- Not done: no backend/API contract change, no source evidence exposure, no expansion beyond approved public deposit scope, and no scraping of benchmark sites.
- Key files: `app/public/src/components/fpds/public/product-grid-surface.tsx`, `app/public/src/components/fpds/public/product-detail-surface.tsx`, `app/public/src/lib/public-locale.ts`, `docs/00-governance/development-journal.md`
- Decisions: kept the slice frontend-only; preserved URL query state, locale fallback behavior, source-derived product text, and the public/private evidence boundary.
- Verification:
  - In `app/public`: `pnpm run typecheck`
  - In `app/public`: `pnpm run build`
  - `api\service\.venv\Scripts\python.exe -m unittest discover -s api/service/tests/regression -p "test_*.py"` (`9` tests)
  - `.venv\Scripts\python.exe -m unittest discover -s worker\pipeline\tests\regression -p "test_*.py"` (`2` tests)
- Known issues: production build verifies renderability, but final visual QA should still be done against a running public API snapshot so real product names, translated labels, and mobile wrapping can be inspected with current data.
- Next step: perform responsive browser QA for `/products` and representative `/products/:productId` records when the current aggregate snapshot is available.

## 2026-06-07 - Public Benchmark Comparison UI Refresh

- WBS: `5.9`, `5.10`, `5.11`, `5.14` public UI follow-on
- Status: `done`
- Goal: improve the FPDS Public Deposit catalog and dashboard against consumer financial-comparison benchmarks while preserving existing public API contracts, locale behavior, and evidence boundaries.
- Why now: the Product Owner asked for the public site to feel more usable and polished for comparing products across banks, using financial comparison-site patterns as the benchmark.
- Outcome: refreshed the dashboard into a stronger market overview with scope actions, active-scope chips, four KPI cards, bank/product-type composition charts, optional like-for-like scatter comparison, freshness/data-note panel, and scroll-safe ranking tables. Updated product cards with a stable three-signal comparison strip, clearer detail action, and safer long-text handling. Hardened the public navigation/header so localized labels can scroll instead of overlapping on narrow screens.
- Not done: no backend/API contract change, no new public evidence exposure, no expansion beyond the approved Canada deposit public scope, and no external benchmark-site scraping was added.
- Key files: `app/public/src/app/dashboard/page.tsx`, `app/public/src/components/fpds/public/dashboard-surface.tsx`, `app/public/src/components/fpds/public/product-grid-surface.tsx`, `app/public/src/components/fpds/public/public-nav.tsx`, `app/public/src/components/fpds/public/public-header.tsx`, `app/public/src/lib/public-locale.ts`
- Decisions: kept the slice frontend-only and reused existing dashboard summary/ranking/scatter API contracts; scatter is requested opportunistically only when a single product-type comparison has a supported axis preset, and scatter failure does not take down the dashboard.
- Verification:
  - In `app/public`: `pnpm run typecheck`
  - In `app/public`: `pnpm run build`
  - `api\service\.venv\Scripts\python.exe -m unittest discover -s api/service/tests/regression -p "test_*.py"` (`9` tests)
  - `.venv\Scripts\python.exe -m unittest discover -s worker\pipeline\tests\regression -p "test_*.py"` (`2` tests)
  - `git diff --check -- app/public/src/app/dashboard/page.tsx app/public/src/components/fpds/public/dashboard-surface.tsx app/public/src/components/fpds/public/product-grid-surface.tsx app/public/src/components/fpds/public/public-nav.tsx app/public/src/components/fpds/public/public-header.tsx app/public/src/lib/public-locale.ts goal.md`
- Known issues: build-time verification only confirmed renderability without a live public API; visual review should be done against a running API snapshot to inspect real product names, chart density, and localized long-label behavior.
- Next step: run responsive visual QA for `/dashboard`, `/products`, and representative `/products/:productId` states once the public API is running with the current aggregate snapshot.

## 2026-06-01 - Dev Product Collection Data And Storage Reset Before Recollection

- WBS: `5.15`, `5.16`, admin collection retest preparation
- Status: `done`
- Goal: delete all product information collection artifacts while preserving bank and product-type setup before a clean recollection test.
- Why now: the Product Owner requested removal of all data created by product information collection, including S3-backed object storage artifacts, except bank and product-type information.
- Outcome: deleted dev DB collection and downstream output artifacts: generated source rows, ingestion runs, run-source links, source documents, snapshots, parsed documents, evidence chunks and embeddings, model and LLM usage records, normalized candidates, field evidence links, review tasks/decisions, canonical products, product versions, change events, publish rows, aggregate refresh requests/runs, public projections, dashboard snapshots, and collection/review/run/product-targeted audit events. Preserved `bank`, `product_type_registry`, `taxonomy_registry`, `source_registry_catalog_item`, auth/session/signup, processing policy config, and migration history rows.
- Object storage: deleted every object under the dev prefix `s3://fpds-dev-private/dev/`; pre-delete summary was 929 objects / 89,009,097 bytes, and post-delete summary was 0 objects / 0 bytes.
- Local artifacts: removed the prior collection tmp artifact directories and report file under `tmp/source-catalog-collections/`, `tmp/source-collections/`, `tmp/aggregate-refresh/`, and `tmp/collection_7wJ2KRMYsDg9XEbn_golden_compare.json`.
- Not done: no bank, product-type, taxonomy, source-catalog configuration, auth/config, or migration rows were changed; no new collection run was started.
- Key files: `tmp/fpds_collection_reset_common.py`, `tmp/fpds_collection_reset_counts.py`, `tmp/fpds_collection_reset_execute.py`, `docs/00-governance/development-journal.md`
- Decisions: kept the 15 active source catalog coverage rows as setup data needed to launch the next admin recollection; deleted generated `source_registry_item` rows so source details will be regenerated.
- Verification:
  - `.\api\service\.venv\Scripts\python.exe tmp\fpds_collection_reset_counts.py --env-file .env.dev`
  - `.\api\service\.venv\Scripts\python.exe tmp\fpds_collection_reset_execute.py --env-file .env.dev`
  - `api\service\.venv\Scripts\python.exe tmp\fpds_admin_collection_goal_tool.py --env-file .env.dev state`
  - Post-delete DB counts: `bank=5`, `product_type_registry=3`, `taxonomy_registry=14`, `source_registry_catalog_item=15`; collection/output tables including `source_registry_item`, `ingestion_run`, `source_document`, `source_snapshot`, `parsed_document`, `evidence_chunk`, `evidence_chunk_embedding`, `model_execution`, `llm_usage_record`, `normalized_candidate`, `field_evidence_link`, `review_task`, `canonical_product`, `product_version`, `aggregate_refresh_request`, `aggregate_refresh_run`, `public_product_projection`, and dashboard snapshot tables are `0`.
  - `audit_event` retained 65 auth/config rows only: 35 auth rows and 30 config rows; collection-related audit count is `0`.
  - S3-compatible storage prefix `s3://fpds-dev-private/dev/` reports `object_count=0`, `total_bytes=0`.
- Known issues: public products and canonical products are intentionally empty until the next collection plus auto-promotion/review/aggregate flow repopulates them.
- Next step: rerun the FPDS admin collection flow from the preserved bank/product/source-catalog setup and inspect the new candidates before approval or publish decisions.

## 2026-06-01 - Customer Demo Scenario Code Alignment Correction

- WBS: customer demo planning, public surface communication support
- Status: `done`
- Goal: verify the customer demo scenario against the actual FPDS Public code after the Product Owner noted that `/methodology` is not a visible Public menu item.
- Why now: the demo document needed to distinguish implemented routes from visible navigation so the customer walkthrough does not instruct the presenter to click a non-existent menu.
- Outcome: confirmed `/methodology` is implemented as a direct Public route, while the Public top navigation only exposes Home(`/dashboard`), Deposit(`/products`), disabled Loan, and the language selector. Updated the demo scenario to describe Methodology as a direct URL/pre-opened tab and added a code-alignment note. Also confirmed the Product Grid bank and product type filters are checkbox-based and support multi-value BMO+TD and chequing+savings scope.
- Not done: no product/runtime code changes.
- Key files: `docs/01-planning/fpds-customer-demo-scenario.md`, `docs/00-governance/development-journal.md`
- Decisions: keep `/methodology` in the governance portion of the demo because it exists and explains the public data boundary, but do not present it as a top-level menu.
- Verification:
  - `rg -n "methodology|방법론|BMO와 TD|chequing과 savings|bank filter|product type filter|Public 화면|Public surfaces|메뉴|navigation|필터" docs/01-planning/fpds-customer-demo-scenario.md -S`
  - inspected `app/public/src/components/fpds/public/public-nav.tsx`
  - inspected `app/public/src/components/fpds/public/product-grid-surface.tsx`
  - inspected `app/public/src/app/methodology/page.tsx`
- Known issues: none for the corrected navigation wording.
- Next step: when preparing the live demo browser tabs, open `/dashboard`, `/products`, one product detail, and `/methodology` directly instead of relying on a Methodology menu item.

## 2026-06-01 - Customer Demo Scenario For Admin Collection To Public Results

- WBS: customer demo planning, `5.15`, `5.16`, public aggregate/admin observability communication support
- Status: `done`
- Goal: prepare a professional customer demo scenario for showing FPDS Admin collection of two banks' chequing and savings products, then FPDS Public product/grid dashboard results, with technical explanation of architecture, collection internals, AI-agent usage, and token usage.
- Why now: the Product Owner needs to demonstrate the current FPDS build to a technically interested customer and asked for a presentation scenario, detailed demo procedure, and ChatGPT prompts for process/architecture visuals.
- Outcome: added a customer demo scenario document covering BMO + TD chequing/savings scope, expected 17-product output, demo flow, environment/run preparation, UI procedure, AI-agent/token usage talking points, risk mitigations, customer Q&A, and separate ChatGPT image/prompts for architecture and collection-process diagrams.
- Not done: did not launch a new live collection or modify product/runtime behavior; the document recommends pre-running the narrowed demo scope before the customer session and using completed run tabs as backup.
- Key files: `docs/01-planning/fpds-customer-demo-scenario.md`, `docs/README.md`, `docs/00-governance/development-journal.md`
- Decisions: recommended `BMO` and `TD` because their chequing/savings coverage gives a compact 17-product story while staying inside already validated Big 5 deposit scope; separated live collection kickoff from public-results proof to avoid relying on external bank-site latency during the customer meeting.
- Verification:
  - `api\service\.venv\Scripts\python.exe tmp\fpds_admin_collection_goal_tool.py --env-file .env.dev state`
  - `git diff --check`
- Known issues: the helper `compare` command still validates against the full 98-product Big 5 golden dataset and should not be used directly for the 17-product demo subset without scope filtering.
- Next step: before the customer demo, run the 4-scope BMO/TD chequing/savings collection or confirm the latest aggregate snapshot already contains the desired filtered public output.

## 2026-05-30 - Admin Collection Golden Recollection Verification

- WBS: `5.15`, `5.16`, admin collection QA verification
- Status: `done`
- Goal: use only the FPDS admin product collection flow to recollect all active registered bank/product-type coverage and compare the result to `worker/pipeline/tests/fixtures/golden/canada_big5_deposit_products_golden_2026-05-23.json`.
- Why now: the Product Owner requested an end-to-end admin collection test after the dev product collection data reset, with the golden fixture as the acceptance target.
- Outcome: launched FPDS admin collection `collection_7wJ2KRMYsDg9XEbn` across the 15 active source catalog items for the 5 active banks (`BMO`, `CIBC`, `RBC`, `SCOTIA`, `TD`) and 3 active deposit product types (`chequing`, `gic`, `savings`). All 15 ingestion runs completed and produced 98 normalized candidates. Golden comparison passed with `actual_count=98`, `golden_count=98`, and zero missing, extra, duplicate, or field-mismatched products across bank name, product name, highest rate, 12-month base rate, tags, product URL, signup amount, eligibility, application method, post-maturity interest, tax benefits, deposit insurance, and term rates.
- Not done: no product pipeline behavior change was needed because the admin collection output already matched the golden fixture; no canonical approval or public publish step was run.
- Key files: `tmp/fpds_admin_collection_goal_tool.py`, `tmp/collection_7wJ2KRMYsDg9XEbn_golden_compare.json`, `docs/00-governance/development-journal.md`
- Decisions: kept verification on the admin source catalog collection path and did not seed, patch, or manually mutate collected product outputs.
- Verification:
  - `api\service\.venv\Scripts\python.exe tmp\fpds_admin_collection_goal_tool.py --env-file .env.dev poll --collection-id collection_7wJ2KRMYsDg9XEbn --brief`
  - `api\service\.venv\Scripts\python.exe tmp\fpds_admin_collection_goal_tool.py --env-file .env.dev compare --collection-id collection_7wJ2KRMYsDg9XEbn --report-path tmp\collection_7wJ2KRMYsDg9XEbn_golden_compare.json`
  - From `api/service`: `.venv\Scripts\python.exe -m unittest discover -s tests\regression -p "test_*.py"` (`9` tests)
  - From repo root: `.venv\Scripts\python.exe -m unittest discover -s worker\pipeline\tests\regression -p "test_*.py"` (`2` tests)
- Known issues: local `tmp/source-catalog-collections/`, `tmp/source-collections/`, and `tmp/aggregate-refresh/` artifacts remain as run evidence; no root-level `tests/regression` directory exists.
- Next step: if the Product Owner wants approval/publish validation, review the 98 candidates through the normal admin workflow rather than bypassing review state.

## 2026-05-29 - Dev Product Collection Data And Storage Reset

- WBS: `5.15`, `5.16`, admin collection retest preparation
- Status: `done`
- Goal: delete all data produced by the product information collection process before a clean recollection test, while preserving bank and product-type setup.
- Why now: the Product Owner requested removal of product collection DB artifacts and all S3 objects accumulated by product collection, excluding bank and product-type information.
- Outcome: deleted dev DB collection and downstream output artifacts: generated source rows, ingestion runs, run-source links, source documents, snapshots, parsed documents, evidence chunks and embeddings, model and LLM usage records, normalized candidates, field evidence links, review tasks/decisions, canonical products, product versions, change events, publish rows, aggregate refresh requests/runs, public projections, dashboard snapshots, and collection/review/run/product-targeted audit events. Preserved `bank`, `product_type_registry`, `taxonomy_registry`, `source_registry_catalog_item`, auth/session/signup, processing policy config, and migration history rows.
- Object storage: deleted every object under the dev prefix `s3://fpds-dev-private/dev/`; pre-delete summary was 1,305 objects / 115,383,901 bytes, and post-delete summary was 0 objects / 0 bytes.
- Not done: no bank, product-type, taxonomy, source-catalog configuration, auth/config, or migration rows were changed; no new collection run was started.
- Key files: `docs/00-governance/development-journal.md`
- Decisions: kept the 15 source catalog coverage rows as setup data needed to launch the next admin recollection; deleted generated `source_registry_item` rows so source details will be regenerated.
- Verification:
  - Post-delete DB counts: `bank=5`, `product_type_registry=3`, `taxonomy_registry=14`, `source_registry_catalog_item=15`; collection/output tables including `source_registry_item`, `ingestion_run`, `source_document`, `source_snapshot`, `parsed_document`, `evidence_chunk`, `evidence_chunk_embedding`, `model_execution`, `llm_usage_record`, `normalized_candidate`, `field_evidence_link`, `review_task`, `canonical_product`, `product_version`, `aggregate_refresh_request`, `aggregate_refresh_run`, `public_product_projection`, and dashboard snapshot tables are `0`.
  - `audit_event` retained 62 auth/config rows only: auth sessions, bank configuration, product-type registry configuration, and source-catalog item configuration.
  - S3-compatible storage prefix `s3://fpds-dev-private/dev/` reports `object_count=0`, `total_bytes=0`.
  - Local collection tmp artifact directories were absent; only non-collection `tmp/admin-dev.log` remains.
- Known issues: the next collection run will rebuild generated source registry details, evidence artifacts, candidates, review tasks, and aggregate outputs from scratch.
- Next step: rerun the FPDS admin collection flow from the preserved bank/product/source-catalog setup and inspect the new candidates before approval or publish decisions.

## 2026-05-29 - GIC Redeemability Flag Auto-Approval Hardening

- WBS: `5.15`, `5.16`, admin collection QA hardening
- Status: `done`
- Goal: diagnose why the active Review Queue had 16 queued GIC candidates and improve the pipeline generally so future bank/product collections do not carry broad page-level GIC redeemability noise into validation errors.
- Why now: the Product Owner reported 16 queued Review Queue items and asked whether GIC product types are inherently hard to auto-collect, with any improvement kept generic across banks and product types.
- Outcome: active dev DB diagnosis showed all 16 queued tasks were `product_type=gic`, `queue_reason_code=validation_error`, and `validation_issue_codes=["inconsistent_cross_field_logic"]`. The issue was not that GIC cannot be collected; profile-expanded candidates inherited both `redeemable_flag=true` and `non_redeemable_flag=true` from broad GIC family/comparison page snippets. Normalization now resolves conflicting GIC redeemability flags from product-level subtype, product name, source subtype label, and tags. Clear redeemable/cashable products keep `redeemable_flag=true`; clear non-redeemable/non-cashable products keep `non_redeemable_flag=true`; mixed or ambiguous products drop those optional flags instead of forcing a false conflict.
- Not done: did not mutate the existing 16 queued review tasks or approve current DB rows in place; a rerun or controlled revalidation is still needed if the current queue must reflect the new normalization behavior.
- Key files: `worker/pipeline/fpds_normalization/service.py`, `worker/pipeline/tests/test_normalization.py`, `docs/00-governance/development-journal.md`
- Decisions: kept true cross-field conflicts review-blocking; the new rule only disambiguates or removes optional GIC redeemability flags when product-level signals are clearer than broad page evidence.
- Verification:
  - DB diagnosis: active queue count `16`; product type `gic=16`; queue reason `validation_error=16`; issue code `inconsistent_cross_field_logic=16`.
  - `.venv\Scripts\python.exe -m unittest worker.pipeline.tests.test_normalization.NormalizationServiceTests.test_profile_gic_expansion_resolves_conflicting_redeemability_flags worker.pipeline.tests.test_normalization.NormalizationServiceTests.test_expands_gic_rate_source_into_multiple_product_candidates worker.pipeline.tests.test_validation_routing.ValidationRoutingServiceTests.test_gic_cross_field_issue_stays_error_and_queues_reason worker.pipeline.tests.test_validation_routing.ValidationRoutingServiceTests.test_big5_deposit_golden_fixture_rows_auto_validate_under_phase1_contract`
  - `.venv\Scripts\python.exe -m unittest worker.pipeline.tests.test_normalization worker.pipeline.tests.test_validation_routing`
  - `$env:PYTHONPATH='api/service'; .\api\service\.venv\Scripts\python.exe -m unittest discover -s api/service/tests/regression -p "test_*.py"`
  - `.venv\Scripts\python.exe -m unittest discover -s worker\pipeline\tests\regression -p "test_*.py"`
  - `git diff --check`
- Known issues: the current DB queue remains stale relative to this code change until rerun or revalidation; no root-level `tests/regression` directory exists.
- Next step: rerun the affected GIC collection or run a controlled revalidation/queue cleanup if the Product Owner wants the current dev DB queue to clear immediately.

## 2026-05-26 - Golden-Pass Validator Alignment

- WBS: `5.15`, `5.16`, admin collection QA hardening
- Status: `done`
- Goal: align validation and review routing with the Product Owner's Big 5 deposit golden fixture contract so golden-matching admin collection candidates can auto-validate instead of being forced into review by stricter canonical helper-field requirements.
- Why now: the final admin collection matched `worker/pipeline/tests/fixtures/golden/canada_big5_deposit_products_golden_2026-05-23.json`, but all 98 candidates were still queued because validation required fields outside the golden contract and treated profile expansion evidence conflicts as force-review issues.
- Outcome: validation now treats the approved Big 5 `chequing`, `savings`, and `gic` fixture fields as the Phase 1 pass contract. Golden-pass candidates may explicitly carry `null` or blank rate/signup/tax/maturity values when the official source does not publish a comparable value, and missing helper canonical fields such as `minimum_deposit`, `term_length_text`, `term_length_days`, `standard_rate`, or `public_display_rate` no longer create `required_field_missing` for those candidates. Profile expansion source-list conflicts no longer create `conflicting_evidence` when the final candidate satisfies the golden contract. Non-golden evidence conflicts still route to review.
- Not done: did not mutate existing queued final-collection review tasks in this slice.
- Key files: `worker/pipeline/fpds_validation_routing/service.py`, `worker/pipeline/fpds_normalization/service.py`, `worker/pipeline/tests/test_validation_routing.py`, `worker/pipeline/tests/test_normalization.py`, `docs/03-design/domain-model-canonical-schema.md`, `docs/03-design/workflow-state-ingestion-design.md`, `docs/03-design/review-run-publish-audit-state-design.md`, `docs/03-design/source-registry-refresh-and-approval-policy.md`
- Decisions: use field presence rather than non-null value for golden fields where the fixture intentionally records unavailable official-source values as `null`; keep dynamic product types and non-golden conflicts on the manual-review path.
- Verification:
  - `.venv\Scripts\python.exe -m unittest worker.pipeline.tests.test_validation_routing.ValidationRoutingServiceTests.test_big5_deposit_golden_fixture_rows_auto_validate_under_phase1_contract worker.pipeline.tests.test_validation_routing.ValidationRoutingServiceTests.test_golden_contract_deposit_candidate_auto_validates_despite_profile_source_conflict worker.pipeline.tests.test_validation_routing.ValidationRoutingServiceTests.test_non_golden_contract_evidence_conflict_still_routes_to_review worker.pipeline.tests.test_normalization.NormalizationServiceTests.test_expands_gic_rate_source_into_multiple_product_candidates`
  - `.venv\Scripts\python.exe -m unittest worker.pipeline.tests.test_normalization worker.pipeline.tests.test_validation_routing`
  - `$env:PYTHONPATH='api/service'; .\api\service\.venv\Scripts\python.exe -m unittest api.service.tests.test_candidate_auto_promotion api.service.tests.test_source_collection_runner api.service.tests.test_source_catalog_collection_runner`
  - `$env:PYTHONPATH='api/service'; .\api\service\.venv\Scripts\python.exe -m unittest discover -s api/service/tests/regression -p "test_*.py"`
  - `.venv\Scripts\python.exe -m unittest discover -s worker\pipeline\tests\regression -p "test_*.py"`
  - `git diff --check`
- Known issues: existing `collection_W8DiKS0ZtWJfRXKP` review tasks were created under the previous validator and remain queued until a rerun or explicit cleanup/revalidation path is applied.
- Next step: rerun admin collection or run a controlled revalidation/queue cleanup if the Product Owner wants the current dev DB queue to reflect the new validator immediately.

## 2026-05-26 - Stale Review Queue Cleanup And Auto-Approve Diagnosis

- WBS: admin collection QA support
- Status: `done`
- Goal: remove stale duplicate review queue load from the first Big 5 admin collection and explain why the golden-matching collection did not auto-approve into public products.
- Why now: the Product Owner reported zero visible public products and 196 admin review queue items after the admin collection golden-match test.
- Outcome: closed the stale first collection `collection_DpQMudY5RunBRjLH` through the review decision path as `rejected`, with reason code `stale_duplicate_collection`; its 98 linked candidates are now `candidate_state=rejected`. Active review queue now contains only the final golden-passing collection `collection_W8DiKS0ZtWJfRXKP` with 98 queued tasks. Public remains empty because `canonical_product`, `aggregate_refresh_run`, and `public_product_projection` are still empty; no final candidates have been approved or auto-promoted.
- Not done: did not force-approve or publish final collection candidates.
- Key files: `docs/00-governance/development-journal.md`
- Decisions: preserve stale run/review audit history instead of deleting rows; close stale tasks as rejected so active queue reflects only the latest collection.
- Verification:
  - Stale cleanup result: `collection_DpQMudY5RunBRjLH` has 98 `review_state=rejected` tasks and 98 `candidate_state=rejected` candidates.
  - Active queue result: 98 `queued` review tasks remain, all from `collection_W8DiKS0ZtWJfRXKP`.
  - Auto-approve diagnosis: final collection candidates all carry `conflicting_evidence`; 56 also carry `required_field_missing`, so force-review policy blocks auto-approve regardless of golden required-field equality.
- Known issues: validation is stricter than the golden comparison contract. It treats multiple evidence-linked values for the same field as conflict and still requires canonical GIC/rate fields such as `minimum_deposit`, `term_length_text`/`term_length_days`, and canonical rate fields even when the golden fixture intentionally uses `highest_rate`, `base_12_month_rate`, `signup_amount`, and `term_rates`.
- Next step: decide whether to harden validation/normalization so the final collection can auto-promote, or manually review/approve the final 98 candidates.
