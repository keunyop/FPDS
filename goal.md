# Current work and unfinished ownership

## 반복 PF 적재용 데이터와 일본 수집 pre-flight

현재 승인 버전의 기관·상품·조건 정의·필드 근거를 반복 조회할 수 있게 하고 일본 승인 경로의 버전 불일치를 수정한다. 회귀 테스트와 DB 검증 후 두 은행의 16개 개발 수집 범위·공식 목록·상세 원문을 점검한다.

완료. 개발 DB에 0050을 적용하고 두 은행의 실제 조회 명령, 롤백한 DB 표본의 버전·근거 격리 및 69건의 관련 테스트를 검증했다. 히고 접근 거부, 가고시마 개인 26개 상세 링크·표본 PDF 6건·카드론 S의 8개 금리 구간 변환 결과를 [저장 분석](docs/03-design/일본_두_은행_상품팩토리_저장_분석.md)에 반영했다. 서비스 배포 및 실제 수집·외부 PF 전송은 후속 범위다.

## 일본 FPDS 수집 준비 재점검 — 2026-11-27

완료. PF 적재 대기 중 진행할 작업을 판단하기 위해 개발 DB의 범위·상세 출처·실행·정식 상품, 현재 은행 목록 및 PDF, 일본 수집 테스트를 대조했다. 은행별 활성 범위 8개, JP 실행 0건, 두 은행 정식 상품 0건이다. 가고시마 26개 문서 링크와 카드론 S 표본 체크섬 일치, 히고 원문 접근 거부 및 9건의 회귀 테스트 통과를 [저장 분석](docs/03-design/일본_두_은행_상품팩토리_저장_분석.md)에 기록했다.

## 상품팩토리 독립 기관 등록 — 2026-11-27

상품팩토리에 肥後銀行(Higo)와 鹿児島銀行(Kagoshima)를 각각 자기 기관을 모기관으로 하는 독립 기관으로 신규 등록한다. 기관 관리 목록에서 코드·기관명·모기관·모기관여부와 로그인 목록 표시를 검증한다.

완료. 肥後銀行(Higo)은 HIGO, 鹿児島銀行(Kagoshima)는 KAGO로 등록했다. 기관 관리 재조회에서 자기 코드를 모기관으로 사용하고 모기관여부가 Y임을 확인했다. 로그인 목록에서도 두 기관이 표시된다. 최초 저장의 AFE0008은 신규 행에 인증된 수정자를 지정해 해결했다.

## 상품팩토리 연계 분석 — 2026-11-27

일본 두 은행의 승인 데이터, 예상표의 코드와 상품팩토리 등록 구조를 읽기 전용으로 비교한다. 저장 단위·키·순서·변경 및 제외 처리와 미확인 사항을 구분해 제안한다. 외부 등록이나 배포는 분석 범위 밖이다.

분석 완료. STDA 인증 조회로 상품템플릿 3개와 연결 항목을 확인했다. 관리자 매뉴얼과 오퍼레이션가이드에서 독립 기관의 자기 모기관 지정, 8바이트 코드, 적용일자와 등록 경로를 대조했다. 두 은행의 공통 조건 정의와 기관별 코드 대응을 [저장 분석](docs/03-design/일본_두_은행_상품팩토리_저장_분석.md)에 기록했다.

## 일본 두 은행 상품조건 엑셀 — 2026-11-22

기존 수집대상과 공식 설명서를 대조해 수신·여신 공통 분류, 상품템플릿 및 L/R/I/F 조건과 값을 예상표에 연결한다. 기존 제외 판단을 보존하고, 은행 간 코드 공유, 동일 템플릿 조건 집합, 선택지·숫자 범위·구간·근거 링크를 저장 후 검증한다.

완료. 대상 73개·공통 템플릿 8개·조건 64개·근거가 있는 값 1,404개를 저장 후 확인했다. 금액 구간이 있는 금리 142행과 만기별 금리 99행의 숫자 필드를 확인했다. 기존 네 시트와 다른 작업의 소유권을 보존했다.

## Higo and Kagoshima collection readiness — 2026-11-21

Scope: both banks' own financial products for individuals and businesses,
including sole proprietors. Exclude distribution of third-party products.
Reconcile official Japanese listings with discovery, contracts and evidence.
Acceptance: inventory the source coverage and gaps, exercise real positive and
misleading inputs, and distinguish local readiness from deployed or collected data.
Verification: offline regressions with official examples, scope/isolation tests,
source-reference checks and final diff. Preserve other work below.

Status: Development registration and the local readiness assessment are complete.
Japan, both banks and 16 catalog scopes are active in the connected dev DB.
The full Kagoshima directory replay recovered 26 named PDFs across six types.
One credit line passed the normal offline extraction, normalization and routing
path. The live Higo acquisition block and uncovered financial contracts remain
open for full collection. No deployment or Japanese collection Run was started.
See the [readiness report](docs/00-governance/jp-higo-kagoshima-readiness-2026-11-21.md).

## Official bank documents and collection accuracy — 2026-11-21

Trace Admin acquisition and acceptance against the Floorplan and stored fixtures. Reproduce missed or misattributed official evidence, correct shared selection and verification paths, and write an operator-facing guide and rules. Verify separately what was reproduced locally and what needs a live collection to measure.

Status: Complete locally. Verified all 1,045 Worker tests in four groups, 594 API tests with disposable PostgreSQL and 56 Admin tests. Both historical fixture collections match their manifests. The current rules and Korean guide are linked from the development guide. Live collection success rates and rollout remain unmeasured.

## Admin-only repository

Scope: retire the consumer app, its endpoints, projection jobs and operating rules. Verify Admin collection, auth, canonical records, tests and build. Keep external environments and migration history under their existing ownership.

Status: Implemented locally. Existing data is preserved. Earlier plans for consumer delivery or publication are superseded. Verification and the four pre-existing Worker failures are recorded in the development journal.

## FPDS Admin Floorplan refresh — 2026-11-21

Rebuild the Korean interactive map for the current Admin collection path. Cover the bank and source entry points, scope selection, capture, evidence, validation, canonical records and Run outcomes. Check the map against local code and test readability at 390, 768 and 1440 pixels. Use offline analysis only.

Status: Complete. The interactive map describes 55 selected files, 19 routes and three guided flows. The Korean guide links to the source. Chrome exercised every guided step at 390, 768 and 1440 pixels. The review checked all mapped API routes for the shared session guard and all four mutations for role and CSRF guards.

## FPDS collection walkthrough - 2026-11-20

Status: Complete for the local source walkthrough and offline Floorplan.
Scope: Trace the local Admin bank-product collection path and present it in
plain Korean with a Floorplan map for the affected path. Keep all earlier work.
Acceptance: Explain collection modes, source ownership, field proof, automatic
exclusion and the distinction between Run completion and Public visibility.
Verification: Cross-check current code and contracts, verify the generated map
and inspect the workspace diff. Analysis uses local source and offline checks.
Outcome: The map covers 35 source files, 11 request routes and three guided
flows. Chrome rendered it at 1440, 768 and 390 pixels and opened the collection
walkthrough at 390 pixels. API tests passed 83/83. Worker tests passed 25/26.
The existing hash test failed again on retry. The bytes of all 19 mismatched
test captures matched their tracked Git versions. Live Runs and publication
were outside this analysis.

## Hosting cost reduction and clone handover cleanup - 2026-10-16

Status: Local code, DB cleanup and handover cleanup verified. Authorized
Production rollout awaits Vercel plugin installation/account connection.
Preserve all unrelated unfinished ownership.
Scope: Diagnose API/Public provisioned memory, Observability events and Supabase
egress; optimize proved expensive reads/requests/logging and retained operational
data. Clean safely disposable handover files; ask about ambiguous documents.
Acceptance:
- [x] Attribute expensive paths with bounded measurements and deployment evidence.
- [x] Reduce redundant reads/requests/logging, preserving financial/freshness/country/
      security/evidence/audit contracts; verify success/boundary/failure behavior.
- [x] Inspect retention/references; clean proven disposable data within authorized
      scope and report exact counts and limits.
- [x] Clean clone-facing files and resolve ambiguous documents with the owner.
- [x] Run affected checks, inspect diff/encoding/references, journal actual outcomes;
      distinguish local code, runtime deployment and database cleanup.
Limits: No paid collection, weaker gates, security/audit removal, unrelated release,
secret output or deletion of required evidence/history. Preserve all prior goals.
- [ ] Complete the authorized Production rollout of switchabank-api first, then
      switchabank-public; verify live CDN hits, fresh/private/error bypass, native
      product counts and usage attribution. Owner approved this on 2026-10-16;
      do not request the same deployment permission again after connection.

Outcome: API678/Public128/security11/browser60 pass (zero browser errors); lint,
typecheck, isolated build, tracked references/foundation/UTF-8/diff pass. Snapshot
lookup is one round trip with identical live CA/US/PH/missing-country data; local
32ms -> 16ms samples. Repeated BFF search sends one upstream fetch for two reads.
DB retention committed: 125330 chunks, 5962 diagnostic executions, 185 snapshots,
327 requests, 78 old login attempts and 74 expired/revoked sessions removed;
681 Run/3703 source metadata compacted. Ten permanent-table digests, 178012 protected
chunks, latest snapshots and CA120/US85/PH12 unchanged; zero orphan evidence links.
Owner approved deletion of 49 completed reports, 91 completed goal sections and
past journal. Nine cutover hashes, current contracts and open owners preserved.
Limits: Source changes remain local/uncommitted; no runtime deployment, billing
setting, paid collection, publication or new scheduler. Vercel plugin remains
uninstalled in the latest tool state. Next: complete connection, inspect the two
existing projects/source integration and release only the authorized projects.


## Actual National Admin parity failure investigation - 2026-10-06

Status: Complete for actual diagnosis and shared correction; fresh live approval/publication remains open.
Objective: Explain the demonstrated 1/17 live outcome using the exact Run
captures, evidence selection, extraction and normalization, and correct shared
code defects within the already authorized parity implementation where proven.
Ownership: preserve the previous import fix and all other goal history.
Scope: read-only live/private evidence diagnosis; current-input provider-disabled
reproduction; source-backed generic corrections with existing financial/security
limits; real runtime boundary regression tests; accurate report/journal.
Exclusions: fresh paid calls/recollection, deployment/restarts, canonical/Public
writes, weaker essentials, manual review and new permanent recovery features.
Acceptance:
- [x] Trace the failed four regular cards and Plus GIC against test inputs.
- [x] Identify the first actual evidence/field divergence, distinguishing observed
      defects from uncertain provider or bank nondisclosure claims.
- [x] Reproduce and test any generic corrective slice against exact retained
      inputs with no paid calls or financial-policy relaxation.
- [x] Record actual outcome, limits and next gate; verify diff/goal/docs.
Verification: read-only DB and private objects; captured SHA-256; production
loaders and provider-disabled proof/normalization; success/failure regressions.

Outcome: exact captured-PDF product association was missing; earlier fixtures
prefilled it. Five missing-parent failures reproduced before the shared fix.
Exact latest Run input replay with production current-origin, taxonomy and
routing SELECTs in a read-only database passes all six priorities, with no
pre-injected association/provider calls/data writes. API 632 pass; Worker
810 run has 809 pass and the known committed-fixture hash failure. Serving
health HTTP 200 already reports process v4; no fresh Run or extra Public
publication is claimed. Existing goals/evidence and one live National product
are preserved. Implementation report records reproducible evidence and limits.

## Authorized Admin collection parity implementation - 2026-10-06

Status: Complete for P1-P4 local implementation and P5/P6 preparation.
Paid evaluation, deployment and live acceptance remain separate open gates.
Ownership: preserve every preceding planning/data-operation goal and history.
Objective: Implement ordinary Admin acquisition and automatic fact handling with
shared services so source-proven facts can reach normal approval/publication.
Scope: P1-P4 source-backed reproductions, bounded same-page acquisition actions,
financial meaning/provenance preservation, actual ordinary artifact/validation
integration, run result diagnostics, and P5/P6 evaluation/release preparation.
Boundaries: unchanged financial essentials, optional omission, field units,
security/private evidence, registered countries/types, no manual product review.
Paid experiments, fresh live Runs, canonical/Public writes and deployment remain
separately scoped operations; do not claim them from a local code/test result.
Acceptance:
- [x] Add source-backed failure and success fixtures before extending patterns;
      reproduce National inputs and preserve independent expected facts.
- [x] Shared acquisition resolves owned dynamic evidence with safe fetch and
      per-detail/Run render and research limits, without optional-only work.
- [x] Shared proof/normalization preserves exact period roles, fee meaning,
      units, conditions and complete current-run field origins; negatives exclude.
- [x] Actual ordinary artifact/origin/routing integration accepts complete
      priority products, retains insufficient/conflicting exclusions, no Review.
- [x] Execution receipts distinguish field losses, acquisition stop/failure,
      approval and publication; cache/version boundaries prevent stale replay.
- [x] Relevant Worker/API regressions and full affected suites, documentation
      consistency checks and git diff --check pass; report real live limits.
Verification: existing safe services with fixture-backed network/DB/provider,
retained official inputs, regression and full affected Python boundary suites;
prepare scoped evaluation/release readback without stateful external actions.

Outcome: six independent National priorities pass ordinary artifact/origin,
normalization, routing and promotion checks; eleven incomplete targets exclude.
Full Worker 808/API 631 tests, CLI checks and changed-file harness checks passed.
Full repo-doctor retains one unrelated ignored tmp README link failure.
Implementation/release evidence: docs/00-governance/admin-collection-parity-implementation-2026-10-06.md.
Keep this file because the preceding independent goals/history remain owned.

## Active slice: 2026-09-30 accuracy-first autonomous collection

Latest Product Owner direction supersedes human review requirements for product
collection. Preserve all independently owned goals below and existing edits.
Objective: accept fewer, evidence-proven, consistently typed product facts with
automatic validation and exclusion, without any human review/approval step.
Scope: trace discovery through extraction, normalization, validation, canonical
promotion and Public; improve shared contracts/prompts, remove collection review
actions, audit and safely retract/correct existing unsafe data, update active rules.
Exclusions: new countries/types, personalized advice, private evidence exposure,
account/security changes, external deployment and unbounded paid recollection.
Acceptance:
- [x] Record concrete accuracy/type/review gaps and implement fail-closed fixes.
- [x] New collection: only exact official, product-scoped, contract-valid facts can be promoted;
      missing optional facts are omitted and unverifiable products excluded.
- [x] New collection completes automatically with accepted/excluded outcomes; human
      decisions cannot bypass the current product-fact gate.
- [x] Audit existing data, apply necessary scoped versioned correction/retraction
      with rehearsal/readback, and refresh affected public snapshots when needed.
- [x] Align Admin/Public workflow and EN/KO/JA copy where affected; preserve auth,
      CSRF, country boundaries, private evidence and historical change records.
- [x] Pass relevant behavior/runtime and responsive UI checks, update governing
      rules/journal, inspect final diff and run git diff --check.
- [ ] Activate the additional legacy review endpoint retirement in production
      after API redeployment; current CLI is logged out.
Verification: deterministic adversarial financial/type/evidence tests, API/worker
and affected frontend suites, bounded live read-only audit before any remediation,
transaction rehearsal and idempotent readback. Do not claim infallible AI accuracy.
Keep this file while unrelated earlier acceptance remains unresolved.

Current authorization and result (2026-09-30): Product Owner reports the prior
code was deployed and explicitly approved the concrete legacy cutover even if
Public becomes empty. Committed at 15:41:36Z: 355 history-preserving product
deactivations, 470 automatic review closures and atomic empty CA/US snapshots.
Rollback rehearsal, independent readback, preserved versions/evidence/decisions
and idempotency checks pass. Production API/BFF report zero products; normal
CA/US Home and catalogue HTML no longer contain historical product IDs after
cache refresh (15:50:23Z). No recollection or account/security changes.
All five legacy manual-review mutations return 410 in the tested code, retaining
auth/role/CSRF/country checks and read-only history. API 535 and cutover tool 4
tests pass. Additional API deployment remains required: Vercel CLI is logged out.
Do not rerun the data cutover or request the same approval again. Preserve the
private manifest/backup and unrelated goals below.

## Objective
Review FPDS Admin against descent/README.md, repair reproducible handover defects,
and leave an evidence-based readiness record for the Product Owner.

## Scope
Admin operator flows, auth/RBAC, country isolation, error/retry handling, related
API contracts, and handover documentation. Small reversible fixes for confirmed
defects. Assess screen purpose and missing essentials within approved scope.

## Exclusions
No production deployment, live collection/review/publication, canonical mutation,
migration execution, account changes, external transfer, release tag or UAT approval.
No Public redesign, new countries/products or restored standalone audit/usage.
Preserve existing edits in descent/README.md and the journal, deleted SEO documents,
and the deleted temporary log.

## Acceptance
- [x] Record findings and screen/feature disposition against the handover guide.
- [ ] Fix confirmed in-scope defects with success/boundary/failure regression checks.
- [x] Run Admin typecheck/build, API/Worker suites and foundation checks as available;
      record exact results and limitations without claiming client UAT.
- [x] Provide a readiness record and actionable remaining owner tasks.
- [x] Update the journal, inspect final diff and run git diff --check.

## Verification
Use repository commands and focused regressions. No live secrets or external
mutations. Layout changes require desktop/tablet/exact 390px checks.

## Current completion boundary
Authorized auth/UI/attention/header fixes and local verification are complete.
The account lifecycle CLI remains unwritten pending explicit approval after
automatic approval review rejection. Keep this goal until that scope is resolved.
No live account operation is authorized by a code implementation approval.

## Parallel bounded slice: 2026-09-07 Search Console diagnosis

Ownership: the Admin goal above remains open and is preserved. This independent
SEO investigation does not take over its acceptance or delete this goal file.

Objective: interpret the supplied Coverage ZIP and verify current public crawl
signals, recording confirmed defects and concrete Search Console follow-up.
Scope: report CSVs, existing Public SEO policy, read-only public HTTP checks,
and a dated diagnosis. No deployment, GSC mutation, data change, or UI redesign.
Acceptance: reconcile counts and dates; distinguish observed signals from unknown
reported URLs; verify representative live routes and sitemap using the existing
audit where available; record limitations and next steps; update journal.
Verification: public HTTP reads, existing SEO audit, document diff review and
git diff --check. Runtime fixes require a reproduced defect and relevant tests.

SEO diagnosis acceptance is complete: four CSVs reconciled, historical dates
identified, Production audit passed 225 sitemap URLs and 10 representative
routes, and diagnosis/journal record known limits and GSC follow-up. No runtime
fix was justified by the observed responses. Preserve this root goal for the
unresolved Admin scope above; SEO completion does not close that ownership.

## Active independent slice: 2026-09-29 Public-aligned collection and bounded repair

Ownership: preserve earlier Admin/data goals and their separate acceptance.
Objective: align CA/US collection and prompts with recent SwitchaBank financial
comparison, calculator and bank-handoff requirements, and repair existing data
where official evidence supports a proportionate correction.
Scope: inspect Public consumers and country profiles, extraction/normalization,
review/publication contracts; audit existing CA/US records; reuse stored evidence
first and perform bounded official-source checks for high-impact gaps/errors.
Cost boundary: no full-catalog recollection or optional marketing enrichment;
start with zero-model-call audit and at most 20 distinct official product checks,
with at most two supporting pages per selected product. Record unresolved gaps.
Exclusions: UI redesign, new countries/types, relaxed approval/comparison gates,
deployment, account changes, scheduler, inferred financial facts or freshness.
Acceptance:
- [x] Map recent Public requirements to confirmed collection/prompt gaps.
- [x] Implement bounded reusable fixes with success/boundary/failure regressions.
- [x] Audit both countries and apply evidence-backed targeted corrections via
      guarded version/change-history paths; verify unrelated data and readback.
- [x] Record actual work/cost limits, remaining gaps, tests and journal outcome;
      inspect final diff and run git diff --check.
Verification: relevant worker/API tests, official-source evidence review,
rollback rehearsal before live changes, idempotence and Public readback.
Keep this goal file while earlier independently owned acceptance remains open.

Completion: all acceptance items for this slice are satisfied. Worker 536, API
502, Public 74 and maintenance 6 tests pass; repo doctor and final diff checks
pass. Six corrections were rehearsed, applied and independently read back through
DB and live Public HTTP; idempotence, immutable prior payloads, 302 unrelated
canonical products, 293 unrelated projection rows and verification dates pass.
The dated report records eight inspected product identities, zero project model
calls, unresolved conditions and separately scoped code release. Preserve this
file for the earlier unresolved Admin and candidate-approval ownership.

## Evidence strengthening batch (2026-10-01)
- Objective: recover additional excluded products using shared official evidence with minimal model/token use.
- Scope: cached evidence triage, targeted current official support, one-off automatic validation and eligible data restoration; no new permanent feature or relaxed accuracy gates.
- Acceptance: exact product applicability and native financial types; uncertain facts omitted; unrelated data/history preserved; actual Public readback checked for any restoration.
- Verification: targeted accuracy tests, before/after database checks, evidence replay, git diff check.
- Status: complete for this bounded batch. Assessed 15 cards; strengthened 9 currency bindings; 0 eligible restorations. All 434 canonical rows unchanged, active 7/inactive manifest 348. One fresh source fetch, zero collection-model calls; development token usage not measured. Focused 31 tests passed. No deployment or human review needed.

## Product-specific disclosure follow-up
- Objective: fill remaining evidence gaps using linked official product disclosures; restore only automatically accepted products.
- Scope: bounded one-off evidence/data work, cached support reuse, no runtime or gate changes.
- Acceptance: preserve precise rate conditions and native types; no human review; publish only after current evidence passes; preserve unrelated data.
- Verification: automatic evidence replay, targeted tests, DB readback and Public checks if any promotion, final diff check.
- Status: completed bounded disclosure investigation. Two official documents checked; exact-context false exclusion reproduced. No eligible promotions under unchanged gate; active 7, original-manifest inactive 348. No data/runtime changes. Focused 31 tests passed; private report and journal record the prerequisite validator correction.

## Remove conclusively invalid excluded products
- Objective: delete excluded records proven not to be publishable products, as explicitly requested by the Product Owner.
- Scope: original cutover manifest only; preserve recoverable or uncertain products and active products; inspect dependencies, retain private rollback data and audit.
- Acceptance: evidence-bound exact deletion scope, no inference of retirement from missing evidence/inactive sources, no unrelated changes.
- Verification: transactional before/after checks, foreign-key integrity and active catalogue counts, diff check.
- Status: complete. Five verified non-product records deleted after rollback rehearsal; 429 survivors unchanged. Original manifest: 7 active, 343 inactive, 5 deleted. Public/API checks passed. Private recovery and audit artifacts retained; obsolete DB audit view is a no-op. No deployment required.

## Country currency defaults and lean required fields
- Objective: apply latest Product Owner policy: country currency when undisclosed, fewer publication-blocking fields.
- Scope: shared collection validation/profiles/prompts, grounding preflight, regression tests and authoritative docs. Product Owner now explicitly approves code changes and restoration of excluded products that pass the new policy. Verify serving-runtime compatibility before promotion.
- Acceptance: CA/CAD and US/USD defaults have explicit internal provenance; explicit or conflicting currencies never silently overwritten; optional unknown facts omitted; essential fee/rate/term meaning preserved; no human review.
- Verification: cached field coverage, focused and affected runtime regressions, existing receipt compatibility, diff checks.
- Status: complete. Deployed accuracy/profile versions verified; all 17 fresh candidates passed and were published across 9 completed runs, with no human reviews or collection-model calls. Independent DB/evidence replay passed for all 24 active receipts; unrelated 412 canonical rows, 150 historical candidates, registry and previous versions preserved. Aggregate refreshes and 24 actual Public URL checks passed: CA 17 / US 7; original manifest inactive 326 / deleted 5. Final operation report: docs/00-governance/collection-policy-recovery-2026-10-01.md.

## Restore essential cost, withdrawal and security information
- Objective: implement the Product Owner-approved conditional essentials across collection, automatic publication and SwitchaBank.
- Scope: CA/US checking transaction costs; GIC/CD withdrawal access and material consequences; line-of-credit security; shared prompts/types, Public API/display, regression tests and policy docs. Preserve country currency defaults and other optionality.
- Out of scope: live canonical mutations, paid recollection, deployment, new product types/countries or manual product review. Assess existing public data read-only and document deployment impact.
- Acceptance: unlimited transactions need no excess fee; finite allowances require excess costs; per-use pricing needs explicit per-transaction evidence. GICs with explicit no early access need no penalty; accessible GICs need complete withdrawal consequences. LOC requires explicit security evidence. Unknowns/conflicts exclude automatically; old receipts cannot bypass current gates. Display the verified terms in EN/KO/JA with no inferred zero/false.
- Verification: success/boundary/failure regressions across worker/API and Public; read-only current catalogue impact; responsive/localized display checks; final diff check.
- Status: implementation complete. Worker 584 / API 538 / maintenance 8 / Public 80 tests pass; Public lint, typecheck and build plus 47 responsive/localized browser checks complete. Read-only serving impact confirmed CA 4 / US 1 from existing 24, with 19 needing evidence. No live writes or deployment; historical goals and unrelated changes retained. Repository doctor and final diff checks passed; all acceptance criteria for this implementation slice are satisfied.


## Collect proven optional facts in the existing grounding pass
- Objective: fulfill the Product Owner request to collect required facts and reliably evidenced optional facts through Admin collection.
- Scope: bounded type/source field selection, extraction and normalization prompts, preservation through automatic validation, regression tests and current policy docs.
- Out of scope: changing publication prerequisites, new fields/countries/types, UI redesign, live collection/data mutations or deployment.
- Acceptance: profile and explicitly registered typed optional fields reach grounding and normalization; exact official evidence and native types remain mandatory. Missing/invalid optional facts are omitted without blocking otherwise complete products. Optional gaps cause no extra searches, repair calls or human review. Existing cache invalidates for changed request/code.
- Verification: mocked extraction-to-normalization/acceptance success and failure tests, country/type coverage, affected Worker/API tests and final diff check.
- Status: implemented; Worker 589 and API 538 tests passed. Optional facts survive normal mapping/automatic receipt checks; missing/invalid optional facts do not veto complete products, while missing required facts still exclude. No live data, deployment or paid collection. Repository doctor and final diff checks passed; all acceptance criteria for this slice are complete. Previous completed goal sections are retained.


## Align SwitchaBank surfaces with required and optional collection facts
- Objective: use required facts consistently in catalogue cards/lists, comparisons and Home Top 5; show verified optional facts in product detail with honest missing-data states.
- Scope: Public presentation and ranking/preset logic, detail information structure, related comparison/curated/finder surfaces where shared, EN/KO/JA copy, regression/UI checks and current rules.
- Out of scope: collection/publication gate changes, invented data, live canonical mutations, recollection, deployment, new country/type or recommendation scoring.
- Acceptance: all required decision facts remain visible in compact/mobile and card lists; optional omissions do not appear as zero/false or ranking penalties. Top 5 uses required fee/rate/term/security context with existing safe comparable-rate/currency boundaries. Detail separates core facts from evidenced extras, distinguishes opening deposits from balances, and avoids empty optional field grids. Existing loading/error/empty/accessibility and privacy boundaries remain.
- Verification: unit tests for all supported types, null/zero/false and ranking invariance; Public lint/typecheck/build; browser checks at 1440/768/390px in EN/KO/JA including empty/error/partial data; final diff and repository checks.
- Status: complete. Public 87 / API 539 tests, Public lint/typecheck/build and 135 browser checks passed (EN/KO/JA, 1440/768/390px, grid/list/detail/Home/comparison/curated/finder, optional empty/partial/zero/false, loading/error, keyboard and real published readback). Screenshots visually inspected; repository doctor and final diff checks passed. No deployment, collection or canonical writes. API-first then Public deployment remains external. Historical completed goals retained.

## Active: additional unpublished-product recovery - 2026-10-01
- Objective: discard conclusively unpublishable records and strengthen collection for currently unpublished products, then publish automatic passes economically, as requested by the Product Owner.
- Scope: bounded one-off data operation, retained evidence reuse, targeted official captures and normal validation/promotion. Preserve earlier goal ownership.
- Out of scope: Admin/runtime/UI changes, relaxed gates, new products/markets, permanent recovery tooling, unrelated active-product mutations, repeated unchanged paid calls.
- Acceptance: establish live Public/database scope; delete only proven non-products with backup/dependency checks; preserve uncertain records; require fresh exact-product evidence for promotion; verify unrelated records/history and actual Public results; record exclusions/usage.
- Verification: read-only inventory and serving-policy checks, evidence replay, bounded dry run/execution, independent DB/Public readback, relevant tests and git diff --check.
- Status: bounded operation complete. Four previously hidden products restored through normal automatic gates; one positively identified legal-document record deleted after backup/rollback rehearsal. Actual Public API/BFF/list/detail checks: 11 passed, CA 7 / US 2. Accuracy/recovery/cutover tests: 31 passed. Independent evidence/DB checks preserve 424 unrelated survivors, 1,536 historical candidates, source registry and target prior versions. Collection-model calls/provider tokens zero. Remaining 419 unpublished records are retained; current evidence and runtime limitations are documented in docs/00-governance/additional-product-recovery-2026-10-01.md. This completes the bounded data batch, not all remaining recovery. Prior independent goals remain owned by their existing sections.

## Active: preserve supporting-document origins and recover two Scotiabank products

- Objective: fix the reusable normalization defect that loses official supporting-document origins, then revalidate and publish the prepared Ultimate/Preferred Package products.
- Scope: trusted current-run evidence-origin loading, preservation through normalization inputs/expansion, regression coverage, affected documentation and a bounded two-product data operation. This improves future collection; retain all earlier changes and goal ownership.
- Out of scope: Admin/Public UI, weaker accuracy or applicability gates, unrelated rate/transaction parser fixes, new markets/products, mass recollection or new recovery features.
- Acceptance: actual captured supporting URL remains bound to the exact chunk/document/snapshot and current run, bank and country; missing/mismatched origins fail closed; model/artifact URLs cannot supply provenance. Existing native values and full evidence checks remain. Both target products publish only after normal automatic validation and current evidence verification; preserve unrelated data/history and verify actual Public results.
- Verification: reproduce the defect before implementation; positive/adversarial origin-loading and end-to-end tests; affected worker/API regressions; fresh two-product dry run, database/evidence/Public readback; git diff --check. Runtime deployment and live data results are reported separately.
- Status: complete for the approved code-and-two-product slice. Worker 596 / API 539 tests, repository doctor and final diff check pass. Two current official-evidence receipts replay successfully; other 426 products, 21 old target candidates, previous target versions and source registry unchanged. All 9 actual API/BFF/list/detail URL checks pass after normal cache refresh: CA 9 / US 2. Shared code is reflected locally; deployment remains required for future Admin collection and was not performed. No model calls, new reviews, UI changes or gate relaxation. Prior goal ownership remains; do not delete this shared goal file.


## Active: exact checking fee rows and bounded TD recovery

- Objective: correct shared interpretation of ordinary transaction limits versus transit-only unlimited benefits; recover the two prepared TD accounts with current evidence and no paid extraction.
- Scope: exact multiline ordinary account-fee rows, shared instructions, success/adversarial regressions, bounded two-product capture/normalization/promotion, private before-images and Public readback. Preserve all previous work.
- Out of scope: rate parser changes, relaxed comparison essentials, Admin/Public UI, mass recollection, permanent recovery tools, unrelated mutations.
- Acceptance: preserve native integer counts and excess money; reject channel-only unlimited, conditional/ambiguous/conflicting rows and excess-as-general fees. Keep full evidence. Publish only automatic passes under compatible serving policy; preserve unrelated canonical/history/registry. Report runtime deployment separately.
- Verification: reproduce failures first; shared Worker/API suites, current official preflight and dry run, independent DB/evidence/Public readback, diff check.
- Status: complete for this bounded two-product slice. Worker 601 / API 539 tests, focused 33 tests and repository doctor pass. Two current receipts replay; other 426 canonical rows, 26 historical target candidates, prior versions and registry unchanged. All 11 actual API/BFF/list/detail/card checks pass: CA 11 / US 2, total 13. Canonical remains 26 active / 402 inactive; 415 records remain unpublished. Zero collection-model calls/provider tokens or new reviews. Code is reflected locally; future Admin collection requires runtime deployment, which was not performed. Final diff/goal checks pass; preserve this shared file for older goal ownership.


## Active: current card rate context and bounded Platinum recovery

- Objective: fix the demonstrated false exclusion of an explicit current annual purchase rate caused by separately labelled offer-switch eligibility prose, then publish the prepared Platinum card if all current essentials pass.
- Scope: narrow shared card-rate evidence semantics and matching collection instructions; positive/adversarial regressions; retained-input diagnosis, bounded official source preflight and normal automatic data recovery. Preserve previous work and goal ownership.
- Out of scope: generic rate-section extraction, weaker rate/annual-basis/currency rules, UI/Admin changes, mass paid collection, historical amendment reactivation, new permanent recovery features or unrelated canonical mutations.
- Acceptance: only explicitly separated current rate declarations may distinguish unrelated switch-from eligibility; rate lower bounds, ranges, introductory/conditional/penalty values and incomplete conditions remain excluded. Keep full original evidence. Exact current product/currency/annual fee/rate and normal automatic gates precede promotion; preserve history/registry and verify actual Public results. Deployment remains separate.
- Verification: reproduce saved defect and adversarial failures first; affected Worker/API tests; fresh current preflight/dry run, before-images, independent DB/evidence/Public checks, final diff and goal review.
- Status: complete for this bounded card slice. Worker 605 / API 539 tests, focused 37, repository doctor and final diff checks pass. Replayed 15 retained cards without fetch/provider/database writes; exactly one current verified candidate was restored. Its complete evidence receipt replays; other 427 canonical products, four old target candidates, prior versions and registry are unchanged. All nine actual Public/API/BFF/list/card/detail checks pass after normal cache revalidation: CA 12 / US 2, total 14; 414 records remain unpublished. Zero collection-model calls/provider tokens or reviews. Shared code is local; future Admin collection requires collection-runtime/API deployment, which was not performed. Preserve previous goal ownership and this shared file.

## Active: bounded Scotiabank card bulk publication
- Objective: diagnose the remaining 14 saved cards together and publish all current automatic passes in one bounded batch, minimizing collection calls and repeated checks.
- Scope: saved-evidence diagnosis, at most 14 detail and shared essential-source preflights, demonstrated shared fixes with regressions if needed, normal automatic publication, before-images and independent readback.
- Out of scope: UI, weakened prerequisites, manual review, paid broad recollection, permanent recovery tooling, unrelated mutations or deployment.
- Acceptance: fresh exact-product identity/currency/annual fee/purchase annual rate; full conditions retained; preserve unrelated canonical/history/registry; record exclusions, usage and actual Public results.
- Verification: dry-run normal gates, regression tests for any code changes, independent DB/evidence/Public checks and diff check.
- Status: complete for this bounded 14-card batch. Two normal automatic publications, twelve retained exclusions, zero collection-model calls. Public API/BFF CA 14 / US 2; total 16, with 412 unpublished. Worker 608 / API 539 and seven focused tests, repository doctor, independent complete evidence replay and all 11 actual Public/API/BFF/list/detail checks pass. Other 426 canonical records, six saved target historical candidates, prior versions and registry unchanged. Shared code is local; future collection-runtime/API deployment remains separate. Preserve previous goal ownership.

## Active: remaining twelve Scotiabank cards
- Objective: continue the authorized unpublished-card recovery using saved diagnosis and bounded current official essential evidence, publishing normal automatic passes together.
- Scope: exact normalization-context defect diagnosis, bounded shared semantics/provenance fixes with regressions, one-off remaining-card operation and independent readback.
- Out of scope: UI, manual overrides, relaxed financial prerequisites, unrelated products/registry changes, permanent recovery tooling or deployment.
- Acceptance: current exact identity/currency/annual fee/annual purchase rate, complete conditions and trusted evidence, preservation of unrelated records/history; record exclusions and usage.
- Verification: reproduce each demonstrated fix before implementation; shared Worker/API tests, normal dry run, before-images, DB/evidence/Public readback and diff check.
- Status: complete for this bounded twelve-card continuation. Six normal automatic publications and six retained purchase-rate-context exclusions, zero model calls/tokens or new reviews. Public API/BFF CA 20 / US 2; total 22, with 406 unpublished. Worker 611 / API 539 and ten focused tests, repository doctor, independent complete evidence/DB replay and all 19 actual Public/API/BFF/list/detail checks pass. Other 422 canonical records, fifteen saved target historical candidates, prior versions, registry and existing Mastercard scope metadata/flag unchanged. One capture persistence conflict was resolved by reusing the existing document ID and resuming the same run once. Shared code is local; future collection-runtime/API deployment remains separate. Preserve prior goal ownership.

## Active: final six retained Scotiabank cards
- Objective: continue the authorized recovery of the six remaining saved cards; resolve demonstrated unrelated condition-word/declaration issues and publish only normal current passes together.
- Scope: bounded shared financial meaning fixes with success/adversarial regressions and matching prompts, saved-evidence diagnosis, fresh essential capture, one-off automatic publication and independent readback.
- Out of scope: generic source cropping, weaker financial prerequisites, UI, human review, new registrations, unrelated writes, recovery features or deployment.
- Acceptance: full original conditions, current exact identity/CAD/annual primary fee/preferred annual purchase rate, valid receipts and normal gates; preserve all other canonical/history/registry and verify actual Public.
- Verification: reproduce saved failures before implementation; affected Worker/API tests, bounded dry run and before-images, fresh capture/evidence/DB/Public readback and final diff/goal review.
- Status: superseded by Product Owner direction to prioritize the entire unpublished catalogue. Only read-only inspection occurred; no runtime or data changes.


## Active: fast publication across the unpublished catalogue
- Objective: find and publish the largest practical quick batch across all unpublished products, minimizing time and model costs.
- Scope: current whole-catalogue read-only diagnosis; reuse preserved evidence; prioritize common complete-essential groups; bounded official freshness checks and normal automatic batch publication with before-images.
- Out of scope: restricting work to six cards, lengthy individual parser work, relaxed essentials, manual overrides, UI, permanent recovery features or deployment.
- Acceptance: assess every unpublished product, select by verified yield and effort, publish current automatic passes only, preserve unrelated records/history/registry, report actual results and exclusions.
- Verification: current-gate evidence replay, source freshness and exact identity, normal dry run, independent DB/evidence/Public readback, journal and diff check.
- Status: complete for the bounded whole-catalogue quick batch. All 406 unpublished products diagnosed, saved captures replayed for 253, twelve current detail preflights and normal dry runs completed. Two automatic publications, zero model calls/reviews, no runtime code/deployment. Public API CA 20 / US 4, total 24; actual website list/details and independent current evidence/DB checks pass. Other 426 canonical rows, 1,430 historical candidates, prior version facts and registry preserved. US BFF initially retained its ordinary cached snapshot; report records this limitation. No large immediate group was proven. Preserve older goal ownership and this shared file.

## Independent slice: latest Alterna collection diagnosis
Objective: explain the latest Alterna collection and absence from Public.
Scope: read-only latest runs, candidates, evidence and live Public membership. Preserve prior goal ownership.
Exclusions: retries/model calls, data mutation, deployment, gate or UI changes.
Acceptance: identify run outcomes and exact blockers; distinguish exclusion from publication/cache failure; document evidence and next step.
Verification: read-only DB transaction, public API readback, scoped source inspection, journal and diff checks.

Completion: latest four Alterna runs completed, eleven source operations succeeded,
four candidates automatically excluded, zero accepted/reviews. Live Public has
zero Alterna products and all seven retained canonical records are inactive.
Exact field blockers and account grounding/context inconsistencies are recorded
in docs/00-governance/alterna-collection-diagnosis-2026-10-01.md. Read-only slice
acceptance is satisfied; preserve this goal for earlier unresolved ownership.

## Authorized slice: Alterna account validation fix
Objective: reproduce and correct proven checking/savings evidence failures.
Scope: saved current collection artifacts, shared meaning/quote validation, matching prompts and regression tests. Preserve earlier goal ownership.
Exclusions: live data writes, paid recollection, publication, deployment, GIC/loan work, relaxed financial prerequisites.
Acceptance: reproduce exact saved failures before extending patterns; correct only proven generic defects with positive/adversarial tests; replay saved evidence and document remaining blockers; run Worker/API checks and diff review.
Verification: private read-only evidence retrieval, deterministic offline replay, shared-contract regressions and affected runtime suites.

Completion: saved failures reproduced before changes; shared fee-condition and
ordinary day-to-day transaction meaning corrected with eight adversarial/positive
regressions and matching extraction/normalization instructions. Actual offline
replay retains savings fee zero but missing grounded rate, and excludes checking
whose saved extraction already discarded required official fields. Worker 632,
API 539, focused 31, repository doctor and final diff checks pass. No model calls,
canonical writes, publication or deployment. This slice acceptance is satisfied;
keep the shared goal for earlier unresolved ownership.


## Server interruption collection continuation - 2026-10-09

Status: Handoff verified; existing batch active, one-off retry waiting in background.
Actual Regions retry and collection outcome remain pending.
Scope: existing dev environment, current Santander queued Runs and the Regions
Bank savings Run proven failed by server connection termination. Preserve all
unrelated work and previous run evidence.
Acceptance:
- [x] Inspect actual DB, active processes, retained plans and server health.
- [x] Identify one outage failure and verify existing sequential pending batch.
- [x] Start and verify a bounded one-off handoff to standard retry after the queue.
- [x] Record actual execution state, limitations and diff checks.
- [ ] Confirm Regions replacement Run and final background collection outcome.
Limits: no server restart/deploy, schema/code changes, unrelated failed/partial
retries, permanent scheduler, historical fact filling or repeated paid retries.
Operational completion of the background collection remains distinct from handoff.


## Authorized slice: reversible Switchabank service suspension - 2026-10-19

Scope: inventory actual Switchabank/FPDS external services; pause verified dedicated
hosted services without deleting projects, data, domains or credentials; preserve
and verify local Admin/API/Public with the existing Supabase database retained.
User correction: Supabase must remain running; no pause/termination or DB mutation.
Separate local PostgreSQL setup is no longer required and was abandoned.
Preserve all earlier goal ownership and unrelated applications.
Acceptance:
- [x] Identify actual hosting, database, storage, providers and scheduled workloads.
- [x] Preserve recoverability and local configuration/data before pausing dependencies.
- [x] Execute supported reversible stops and independently verify results.
- [x] Verify local Admin/API/Public startup and data flow; document exact commands.
- [x] Record user actions, billing limits and restoration order; journal and diff check.
Verification: provider readback and external HTTP; local DB and API/BFF reads;
process/startup checks; secret-free inventory/runbook; git diff --check.
No termination, data purge, shared-service cancellation or paid collection.
Status: complete for accessible reversible suspension and local startup. Three
Vercel projects paused; five external URLs independently return DEPLOYMENT_PAUSED.
Supabase kept running per correction; existing financial data and S3 preserved.
Local health and CA/US/PH API/BFF reads pass; Public/Admin login browser checks at
1440/768/390px pass. Local servers remain running. Existing-account login and
write/collection flows were not run. Git auto-build/old Preview controls, billing,
subscriptions and broader AWS inventory remain documented owner actions because
original project controls are not exposed and AWS compute access is denied.
No DB migration, paid collection, publication, project deletion or deployment.
Preserve this shared goal and all earlier unfinished ownership.
