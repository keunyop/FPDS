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

As of 2026-08-31 (Public product report and site feedback, complete):

- migration 0046 defines a 400-day-bounded anonymous product-error and site-
  feedback store. Product reports copy country, snapshot, bank, product name,
  Product Type, and product ID from the latest active Public projection; no
  visitor, contact, IP, cookie, query, profile, account, or browser identity is
  retained
- credential-bound POST /api/public/feedback enforces fixed type/category
  pairs, active country/product context, locale and length bounds, and a
  process rate limit. Authenticated GET /api/admin/public-feedback derives its
  country exclusively from the Admin session
- Public product-detail Important note and footer now open accessible EN/KO/JA
  dialogs with Other, optional 2,000-character detail, anonymous/no-reply copy,
  submitting/error state, and a confirmation that restates the current
  submission without exposing an inbox
- authenticated Admin /admin/feedback shows country-scoped totals, product and
  site submissions, search/type/category filters, product/bank/snapshot
  context, stable IDs, locale, detail, time, and pagination; it is read-only
  and does not mutate canonical data or create Review decisions
- verification: feedback tests 9/9 and security tests 2/2; Public and Admin
  typechecks and production builds pass; hydrated browser checks at 1440px,
  768px, and exact 390px confirm dialog containment, zero document overflow,
  initial close-button focus, Escape closure, footer feedback, and EN/KO/JA
  category/copy; route manifests parse and git diff --check passes
- migration 0046 was not applied to shared dev or Production and no deployment
  was performed. Next: apply 0046 through an approved database release before
  enabling the deployed submit/inbox routes

As of `2026-08-30` (US partial-run recurrence and Public finder analytics,
complete and verified in Production):

- latest US Partial RCA: Wells Fargo Savings run
  `run_20260829_202848_wfbn_savings_collect_nZQsjzvy` rejected three valid
  Savings details under `/savings-cds/...` because the shared path classifier
  detected `cds` but did not recognize Savings in a hyphenated family segment.
  The only unavailable page was a deterministic non-HTML account-close PDF,
  yet the no-detail classifier treated the generic unavailable wording as
  transient, so the exact scope remained eligible to fail again
- generic recurrence fix: path-token matching now recognizes Savings and
  Chequing/Checking inside mixed hyphenated route segments for every bank and
  Product Type. Deterministic non-HTML mismatches are structural; true
  timeout/408/425/429/5xx evidence remains transient. A conclusive zero-detail
  run can therefore use the existing reversible quarantine/no-repeat path
- Public finder: Bank and Product Type are optional, product-name-only API
  filtering works without them, and an empty focused field browses the complete
  active scope alphabetically in 40-row pages with list-contained scroll
  loading. Per the Product Owner follow-up, the labels no longer display an
  optional qualifier and the blank-field browse hint is omitted. EN/KO/JA still
  explain that the input is a held product, use Find a better product and My
  product, and omit the requested standing caveat
- Public analytics: migration `0045` defines 400-day daily product/event
  aggregates only. The first-party BFF records internal detail clicks,
  official-bank clicks, and finder selections after active-snapshot validation.
  `/admin` uses server-only password/shared credentials, a signed eight-hour
  HttpOnly SameSite=Strict cookie, best-effort login/write throttling, noindex,
  and no GA initialization. It shows totals, product/bank rows, most-selected
  My products, a 30-day series, and explicit selection/retention limitations
- shared-dev migration `0045` was applied with the CA and US published
  aggregate IDs/counts unchanged; the migration-history row, event table,
  400-day retention trigger, and empty initial analytics state were read back.
  Matching API/Public app credentials and the Product Owner password were set
  for Vercel Production and Preview; an initially invalid generated secret was
  immediately replaced with independently checked cryptographic values
- final verification completed in this slice: focused API/runner tests 23/23,
  post-integration engagement tests 8/8, final full API unit suite 442/442,
  Public TypeScript typecheck, Public production build, and local production
  functional QA for blank alphabetical browse, name-only search, EN/KO/JA
  copy, secure password session, aggregate analytics, rejected events, GA
  exclusion, and robots exclusion. Responsive renders passed at 1440px, 768px,
  and exact 390px without layout breakage
- Product Owner-authorized Production deployments completed for
  `switchabank-api` (`dpl_EAn4tN5uhfjEfgyncDBSszLDUViK`) and
  `switchabank-public` (`dpl_591MtMXQCHL32PCoPYbhXWbjToKK`). Public deployment
  used a temporary package that preserved the configured `app/public` Root
  Directory because the root API `.vercelignore` correctly excludes `app/`;
  the two preceding failed Public builds never received the Production alias
- Production read-back confirmed `https://www.switchabank.com/admin` returns
  the configured login, password `1112` opens the aggregate dashboard, the
  signed session cookie is Secure and HttpOnly, API-backed Product engagement
  renders without the unavailable state, and the requested optional labels and
  blank-field hint are absent. The pre-existing
  `tmp/aggregate-refresh/aggregate-refresh-runner.log` change is preserved and
  was not edited

As of `2026-08-29` (Public finder simplification and Methodology map move,
complete):

- the Home finder now follows one compact path: published bank, available
  Product Type, case-insensitive literal product-name filter, exact current
  product, then comparison; selection is still local and persists no consumer
  or financial value
- the eyebrow, explanatory body, initial-state panel, and standing long caveat
  are removed. Results retain one concise localized one-metric/non-advice line,
  while loading, no-match, empty, unavailable-metric, no-improvement, error,
  retry, reset, detail, and official-link states remain available
- `FR-PUB-021` ranking behavior is unchanged: lower Chequing monthly fee,
  higher Savings/GIC rate, lower Credit Card annual fee, and lower governed
  Loan rate; ties, missing values, unsupported types, and the selected product
  do not become candidates, and display remains capped at three
- Home no longer renders or requests country coverage. Methodology now owns the
  unchanged local Equal Earth map, published product/bank counts, fallback,
  localization, freshness, and privacy behavior
- requirements, WBS `5.55`, decision `D-070`, Public/design/runtime baselines,
  and the UI override register reflect the explicit type/name flow and the new
  map owner; profile-based, multi-factor, cross-type, suitability, eligibility,
  and application recommendation remain out of scope
- Public `pnpm run typecheck`, `pnpm run build`, and `git diff --check` passed.
  Production-build Chrome QA passed EN `1440px`, KO `768px`, and JA exact
  `390px`: localized no-match states appeared, `Aeroplan` returned four literal
  matches, exact selection enabled Compare, and the CIBC Aeroplan Visa Infinite
  Privilege Card returned three lower-annual-fee same-type candidates. All
  viewports had no browser console error or document overflow and kept `44px`
  minimum visible controls. Home had no coverage map; Methodology rendered it
  at `1024px`, `705px`, and `358px` respectively. Exact-`390px` KO keyboard QA
  confirmed visible Tab focus in order across Product Type, product search,
  matching option, and Compare.

As of `2026-08-21` (TD Credit Card precision publication proof, active):

- final precision collection `collection_VU39TiCQ5NYprOMG` completed one TD
  Credit Card run with 7/7 selected sources successful, no failed/partial run,
  six English named-card candidates, and all six automatically approved
- four candidates passed direct validation; Review AI v19 examined the two
  validation-routed candidates and approved both, leaving zero active Review
  candidate in this collection
- the approved inventory includes TD Cash Back Visa Infinite, TD Cash Back
  Visa, TD First Class Travel Visa Infinite, TD Rewards Visa, TD U.S. Dollar
  Visa, and TD Aeroplan Visa Infinite; each has exact annual fee and purchase
  rate evidence sufficient for the comparison contract
- discovery excluded 22 conflicting-language detail candidates before bounded
  selection, promoted six exact details, and retained no Chinese detail source;
  the prior payment-protection insurance detail was hard-scope deactivated
- the reusable final fixes additionally reserve bounded capacity for exact AEM
  product attributes, permit `View offer` only for a singular card-detail URL,
  exclude credit-card payment-protection insurance from product scope, and
  recover TD's exact colon-formatted card rates when AI omits them
- current focused verification is 168 API source-catalog tests, 36 worker
  discovery tests, and 170 worker normalization tests; next refresh/read back
  CA Public and audit the historical Chinese duplicate before full suites
- CA Public snapshot `agg_i_hp6XF3yY8faniY` is fresh after explicit refresh.
  All six final English cards and U.S. Daily Interest Chequing were read back
  active with the expected comparison fields; the four featured cards expose
  exact official annual fee and purchase rate values
- historical Chinese candidate `cand-b293fb02a76bbf68` was retracted through
  candidate-safety remediation, inactivating `prod_xTv0e57FN_qQ3LT1` with
  audit/change events. The new Public snapshot returns no item for that product
  while English Aeroplan `prod_45xFdESnoR7j5i1w` remains active
- final full verification passed: 425 API tests and 522 worker tests. Tracked
  test fixtures, aggregate-runner log lines, and bytecode noise were restored;
  `git diff --check` passes and the automatic scheduler remains disabled

As of `2026-08-21` (TD targeted precision diagnosis and hardening, active):

- targeted precision collection `collection_cBlvixf9appwQxZh` is terminal with
  both Chequing and Credit Card runs completed and no failed/partial run
- Chequing produced six comparison-complete candidates and auto-approved all
  six, including U.S. Daily Interest Chequing; Credit Card still produced only
  TD U.S. Dollar Visa and retained it in Review for a missing normalized
  `purchase_interest_rate`
- the remaining card failure had three independent, reproducible causes: an
  unselected primary category URL was incorrectly marked already visited before
  secondary-hub expansion; TD's exact AEM card routes are stored in
  `data-cardDescriptionUrl`; and normalization did not accept the official
  `Interest: Purchases 21.99%` label even when AI extraction and official
  grounding matched
- discovery now expands only actually visited primary hubs, extracts TD's
  bounded card-description attribute while canonicalizing the public route,
  and keeps the existing application/offer exclusions; normalization accepts
  exact purchase labels but still rejects cash-advance/balance-transfer labels
- focused module verification passed: 166 API source-catalog tests, 35 worker
  discovery tests, and 169 worker normalization tests
- next run one fresh TD Credit Card precision recollection, poll through Review
  AI and aggregate refresh, verify the named English card inventory and CA
  Public readback, then continue the append-only historical duplicate audit;
  keep the automatic scheduler disabled

As of `2026-08-21` (TD precision recollection continuation, paused again):

- resume-next step 1 is now complete:
  `collection_EfMGx23KF2114R3C` reached terminal with seven completed runs,
  33/33 selected sources successful, zero failed/partial runs, 23 candidates,
  8 approvals, 13 active Review candidates, and 2 superseded candidates
- Personal Loan retained two candidates in Review because the official
  evidence still lacked a complete rate/amount/term contract; Savings
  auto-promoted TD ePremium and TD Growth while TD Every Day remained Review
  only for missing minimum-balance evidence. All three Review AI attempts
  completed and did not invent unavailable facts
- the next active step is the already scoped targeted precision recollection
  for TD Chequing and Credit Card after confirming no runner is active
- this block supersedes the older TD pause block below; `goal.md` contains the
  authoritative detailed handoff and exact next commands/IDs
- standard collection `collection_FsuYnsK5WtBDwyzw` is terminal across seven
  types with 29 candidates: 7 approved, 20 in Review, and 2 superseded
- reusable fixes now include active/reused-scope locale enforcement,
  pre-cap English seed filtering, hard locale deactivation, best-effort runner
  failure persistence after transient DB/DNS errors, and Review AI v19
  requirement-level alternative selection
- live precision collection `collection_EfMGx23KF2114R3C` was intentionally
  left running: last poll was 5 completed / 2 started, 18 candidates, and 14
  Review tasks; Personal Loan was extracting and Savings was still pending
- precision Chequing excluded 22 locale-conflicting candidates and produced 5
  approvals plus U.S. Daily Interest Chequing in Review; its official
  `Transaction Fee 1 $1.25 U.S. each` layout is now parsed by a tested fix,
  but requires a fresh targeted run
- precision Credit Card excluded 56 locale-conflicting candidates and
  auto-approved TD U.S. Dollar Visa, but an AI `irrelevant` preemption lost
  three strong English named-card details; strong singular title/H1 plus
  pricing evidence can now safely override that scorer error while category
  pages remain blocked, also requiring a fresh targeted run
- focused continuation verification passed: 180 API source-catalog/runner tests
  and 191 worker extraction/approval tests
- resume by polling the live collection to terminal, then run targeted precision
  Chequing + Credit Card, verify CA Public, audit the historical Chinese
  duplicate append-only, run full suites/diff checks, and delete `goal.md`
  only when its acceptance criteria are complete; keep the automatic scheduler
  disabled

As of `2026-08-21` (TD Canada detailed-recollection hardening, paused):
- Product Owner requested a pause after the reusable implementation and tests;
  `goal.md` contains the full active handoff and must remain until final TD
  precision recollection/Public readback is complete
- prior TD collection `collection_VebpXs07e6atGGls` completed all seven
  Product Types but produced 29 candidates with only 7 approved and 22 in
  Review; AI did run, so the failure was traced to bounded discovery polluted
  by `zh.td.com`/`zt.td.com`, scalar-first lending/security repair,
  conversion-fee percentage confusion, and genuine inaccessible/ambiguous
  official facts
- discovery now removes conflicting source-language hosts/paths before its
  bounded cap and retains a named official Credit Application Guide only as
  supporting evidence; Review AI v18 applies candidate country/language to
  consulted URLs and requests evidence-preserving lending/security alternatives
- Canada Chequing now accepts exact non-balance fee waivers and product-wide
  transaction fees; savings merge rejects unlabeled fee percentages, pairs a
  tiered Public rate with its first qualifying balance, and keeps TD Growth's
  ongoing Boosted Rate out of promotional fields
- verification completed before pause: 586 focused tests, 418 full API tests,
  and 516 full worker tests passed
- explicit TD collection `collection_FsuYnsK5WtBDwyzw` is continuing in the
  background with the database scheduler still disabled; last poll showed 1
  completed and 6 started runs, 6 persisted candidates, 1 Review task, and no
  reported errors
- that launch used standard/reused-detail scope, so resume by auditing it to
  terminal and then execute the actual Admin `Rediscover completed` precision
  path for CA/TD Chequing, Savings, GIC, Credit Card, Line of Credit, Mortgage,
  and Personal Loan; finish candidate/Public comparison and append-only audit
  of historical Chinese duplicate `prod_xTv0e57FN_qQ3LT1`

As of `2026-08-12` (US pricing-evidence follow-up):
- official US bank UI review confirmed that required pricing is commonly split
  across a product hero or accordion, ZIP/state-specific tables, directly
  linked fee/rate disclosures, query-addressed offer documents, and
  product-named agreements rather than one static product page
- exact-product detail discovery now follows at most two compatible pricing,
  fee, rate-table, account-guide, or agreement companions per product; source
  identity retains bounded offer/document/location query keys, US dynamic
  pages can use browser capture, and structured payload parsing includes
  APY/APR/fee keys
- Review AI v17 invalidates a cached result when candidate approval fields
  change and permits only bounded exact-quote repair from the exact product
  route or a separately named exact-product agreement/disclosure
- US cards require annual fee plus a qualified Purchase APR summary; Public
  shows the entire intro/range/variable-rate qualification rather than a
  synthetic lower-bound rate, and approved-origin fallback keeps an official
  product link available without exposing private evidence
- shared-dev migrations `0036` through `0039` are applied. Bank of America
  Travel Rewards, Travel Rewards for Students, and Marcus High-Yield CDs were
  automatically promoted from exact official evidence. Latest Public is
  `77/77` essential-complete (`63` CA, `14` US), with zero incomplete rows and
  zero US missing official product links; `108` incomplete canonical rows stay
  private

As of `2026-08-12`:
- the CA/US Admin-to-Public gap investigation found no recurring product
  scheduler, no global recovery sweep for pre-policy or interrupted candidates,
  and a Public aggregate allowlist that omits credit cards
- shared-dev started this slice with 171 active canonical products, only 60
  satisfying the current essential comparison contract, and Public snapshots
  containing 47 CA plus 11 US products
- migration `0035_collection_publication_automation.sql` and the API runtime now
  define a single-leader, policy-controlled loop for weekly active-catalog
  collection, 24-hour failed/partial retry, stale-run recovery, orphan
  auto-promotion, bounded current-v7 Review AI recovery, and pending aggregate
  restart; automated runs and audit events retain the `scheduler` actor type
- credit cards now use the existing D-034 completeness gate across aggregate,
  Public API, `/cards`, comparison, and detail instead of being silently
  filtered out
- shared-dev migration, recovery, and aggregate refresh are complete: all 66
  active canonical products that currently satisfy the essential contract are
  in Public (`55` CA, including `7` cards; `11` US), with zero incomplete Public
  rows; 111 incomplete active canonical rows remain private
- the first scheduled six-scope US collection is progressing independently in
  the background, and the scheduler continues bounded reconciliation of legacy
  Review candidates without operator action

As of `2026-08-09`:
- `WBS 5` is the active stage
- US collection-failure hardening is complete, fully regression tested, and
  verified through audited shared-dev Bank of America recollection after
  migration `0028`
- `WBS 5.23` AI bank-registry onboarding is complete, locally verified, and
  activated in shared dev through migration
  `0027_standalone_ai_operations.sql`
- AI onboarding now separates readable bank display names from legal entity
  names and exact ranking labels; the five affected US shared-dev bank names
  were corrected through audited updates
- the client-handoff simplification is complete: Admin now exposes Overview, Review, Runs, and Banks as direct daily work, secondary tools remain in one labeled group, core list/detail density is reduced through progressive disclosure, and stale/generated/unreachable repository scaffolding has been removed without changing routes or backend contracts
- public grid, dashboard, locale rollout, source registry admin MVP, and operator-managed product type onboarding are already implemented
- country is now a first-class bank/canonical/aggregate/Public dimension; the
  Public header selects active published countries, the footer owns language,
  and current governed collection scope includes Canada and the United States;
  later countries fail closed until their country-product profiles are added
- Admin now requires an enabled working country at login, stores it in the
  server session, lets authenticated operators change it from the shell header,
  and scopes country-owned bank/source/collection/run/review/change/usage work
  to that session country
- Admin language selection now uses one EN/KO/JA dropdown pattern: authenticated
  routes place it inside the sidebar Account menu, while Login and Signup show
  the standalone dropdown and the global Header remains focused on country and
  environment context
- Public Home, Deposit, Loan, comparison, detail, and Methodology now use the verified-record visual system and were production-verified against the live aggregate snapshot in EN, KO, and JA at desktop, tablet, and exact `390px`; `WBS 5.14` remains complete
- recent work has focused on source collection hardening, aggregate refresh health, and registry state behavior
- current Deposit and Lending collection is narrowed to identity plus explicit
  type-specific comparison essentials; complete evidence-grounded candidates
  follow the audited automatic canonical/aggregate path, while incomplete
  active canonical rows are excluded from Public projection
- existing CA/US Public data has been recollected and repaired: the live Public
  API now returns `48/48` essential-complete products with no `Unavailable`
  values; `53` unresolved newly collected candidates remain private in Review
- qualified APR ranges, formulas, and representative examples remain
  source-language `interest_rate_summary` values with assumptions rather than
  being flattened to misleading scalar rates
- the latest slice hardened multi-bank Runs/Review Queue behavior after B2B duplicate/noisy candidates and Bridgewater domain-alias failures; active Queue is reduced to four genuinely reviewable B2B products and Bridgewater Savings now collects successfully
- the current collection-QA slice inspected CIBC, EQ Bank, Fairstone, and Canadian Tire runs and reviews; dynamic candidates now stay inside registered field contracts, false percentage/rate mappings and page-copy fields are suppressed, non-product editorial/service sources are rejected, and Review opens only concrete problem fields with concise decision controls
- cross-bank field-contract hardening now keeps rates, money, booleans, and term schedules typed consistently, renders field-level notes in Admin review, reconstructs product-scoped official rate tables, and keeps unavailable official values in review instead of filling them from static fixtures or nearby products
- the FPDS Admin accuracy audit has retracted confirmed unsafe legacy/live candidates through audited remediation and added exact percentage evidence, promotion/standard-rate, fee, currency, source-role, and product-boundary guards; its representative recollection checkpoints remain documented in the recent entries
- Review Detail supports CSRF-protected, role-gated AI verification against country-scoped registered official bank domains with cited comparisons, contract-safe correction staging, usage persistence, and append-only audit events; interactive verification remains advisory, while collection and existing-queue remediation require verified identity plus 100% of the smaller essential-field set and ignore optional omissions
- configured detail-product collection now uses the same required official-domain live-search discipline across standard and dynamic Product Types, while accepting a field only when a provider-consulted official URL and an exact quote from the fresh evidence chunk both support it
- latest source/review hardening blocks multi-product family composites, fixes rate-first schedule pairing and `www`/apex redirects, excludes service/advice and cross-product sources, verified named Haventree mortgage discovery, and completed the approved audited retraction of two unsafe historical candidates
- the latest official-source accuracy slice replaced Oaken's expired 2023 6% Savings publication with the current 2.80% rate, reconstructed the current Oaken GIC schedule from a column-header rate table, removed National card-family and Oaken commercial false candidates, and kept unresolved family/dynamic-card facts in Review rather than inferring them
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

## 2026-08-12 - US Pricing Evidence And Automatic Publication

- WBS: `5.26`, US pricing/fee evidence collection and Public publication
- Status: complete in implementation, targeted shared-dev remediation, live
  aggregate/API readback, and regression verification; the independent broad
  catalog runner remains observable through normal automation
- Goal: align FPDS collection with how US banks actually expose mandatory rate
  and fee information, then publish every repaired candidate that meets the
  unchanged official-evidence gate without operator approval.
- Why now: registered banks and candidate counts were high, but exact rates and
  fees often lived outside the originally selected detail page. Query stripping,
  static-only fetches, deposit-centric labels, range flattening, and stale AI
  verification kept otherwise valid US products private.
- Outcome:
  - analyzed official Chase, Bank of America, Capital One, Wells Fargo, TD Bank,
    U.S. Bank, and Marcus page/disclosure patterns and implemented bounded
    detail-linked pricing companions, query-aware source identity, browser
    fallback, structured pricing payload extraction, and cross-Product-Type
    supporting-source exclusion
  - added Purchase APR labels and `purchase_interest_rate_summary` across
    extraction, normalization, validation, aggregate, API, and Public list,
    comparison, and detail; migration `0039` makes the qualified summary the
    preferred US card essential rather than treating a range lower bound as the
    offer
  - upgraded Review AI to v17 with current-field cache matching and an exact
    US-card fallback limited to `$0`/no-annual-fee statements and named
    exact-product Purchase APR disclosure quotes
  - fixed nested US CD identity so an exact `*-cd`/`*-cds` product slug under a
    bank's `/savings/` information architecture outranks the parent route
  - added a safe Public product-link fallback from the approved candidate's
    official origin when projection metadata and product-version evidence links
    do not themselves contain a link
  - applied shared-dev migrations `0036`-`0039`, re-ran the cleanup after broad
    collection materialization, and confirmed all `93` active US card sources
    request the v2 APR-summary contract
  - automatically approved and published Bank of America Travel Rewards,
    Travel Rewards for Students, and Marcus High-Yield CDs. The cards retain
    `$0` annual fees and full disclosed APR text; Marcus retains `3.90%`,
    `$500`, `6 months to 6 years`, and its early-withdrawal disclosure
  - rechecked seven other complete-looking private US candidates through the
    current official-domain/exact-quote workflow. All seven remained private
    because one or more required fields could not be verified at 100%; six
    additional complete-looking candidates retain explicit cross-field
    inconsistency blockers
  - latest Public audit is exact: canonical `185 = 77 complete + 108
    incomplete`; Public `77 = 77 complete + 0 incomplete`. US Public has `14`
    products (`5` checking, `2` cards, `1` CD, `1` mortgage, `5` personal/
    vehicle loans), no `Unavailable` values, and no missing official links
- Not done: did not bulk-approve the `78` incomplete active US canonical rows
  or the `135` private active candidates. Their current missing field and
  cross-field reasons remain available to Admin and the recurring recovery
  loop; no source fact was inferred from a sibling product.
- Key files: discovery URL/fetch/parser modules, source catalog and runner,
  Review AI verification/correction, market profile and field contract,
  aggregate/Public API/UI modules, migrations `0036`-`0039`, active design and
  requirements docs, and `tmp/fpds_admin_collection_goal_tool.py`
- Decisions: updated D-043; retained exact product identity, source-language
  financial qualifications, 100% essential grounding, private raw evidence,
  and fail-closed publication.
- Verification:
  - API full suite: `391` tests
  - worker full suite: `471` tests
  - Public: `pnpm run typecheck`; `pnpm run build` including `/cards`
  - shared-dev targeted collections: two Bank of America cards and Marcus CD
    approved with zero Review task for the CD
  - live anonymous Public API: US `14`, zero unavailable values, zero missing
    product links; exact card APR summaries and Marcus CD facts read back
- Known issues: current official search still cannot fully verify seven
  otherwise complete-looking legacy candidates; they remain Review-bound. The
  older broad runner discovered 49 Chase card sources before the current
  bounded process was loaded and continues through the guarded downstream
  stages; future scheduled runs use the new selection rules.
- Next step: no routine operator action is required. Keep the API runtime
  deployed so the elected scheduler continues weekly collection, bounded
  re-verification, and aggregate recovery.



## 2026-08-26 - Public Home Equal Earth Coverage Map and Bank Counts

- WBS: `5.52` (`Completed`).
- Status: web reference and license review, Public Home map replacement,
  country bank-count contract extension, localization, responsive rendering,
  regression coverage, and documentation are complete.
- Research and design:
  - reviewed polished editorial/global-coverage map treatments and reusable map
    sources rather than retaining the approximate seven-path illustration
  - selected Natural Earth 1:110m public-domain land geometry, distributed
    through `world-atlas`, and generated a compact Equal Earth projection;
    source tooling was temporary and added no Public runtime dependency
  - kept the map as a local static SVG with restrained graticules, accurate
    geography, and country markers aligned to the existing SwitchaBank visual
    tokens; no external map request, account, cookie, or tracking surface was
    introduced
- Outcome:
  - `GET /api/public/countries` now returns active product `count` and
    distinct active `bank_count` from the same latest completed
    `phase1_public` snapshot
  - the Public response type keeps `bank_count` optional so an older
    five-minute cached response continues to render product counts safely
  - Home country rows now show localized product and bank counts in EN, KO,
    and JA while preserving unavailable, empty, current-country, and
    assistive-label behavior
  - the former hand-drawn continent paths were replaced by the local
    `world-map-equal-earth.svg` asset and accurate marker coordinates
- Verification:
  - focused Public countries API module: 12 tests passed
  - full API suite: 435 tests passed
  - Public TypeScript typecheck passed
  - Public Production build passed
  - live local API readback returned product and distinct-bank counts for
    Canada and the United States
  - rendered Home inspection passed at 1440px EN, 768px JA, and exact 390px
    KO; DOM measurement confirmed no document-level horizontal overflow and
    both localized counts in every country row
- Boundaries: no canonical product, aggregate eligibility, country scope,
  Production deployment, analytics, external runtime map service, or unrelated
  dirty-worktree state was changed.

## 2026-08-26 - Public Home Map Fill and Bank-Count Compatibility

- WBS: `5.53` (`Completed`).
- Status: screenshot-led follow-up diagnosis, centered map enlargement,
  bank-count rollout compatibility, old-response verification, responsive
  rendering, and documentation are complete.
- Root cause:
  - the accurate Equal Earth asset was centered, but the full `0 0 1000 500`
    projection viewport retained enough outer ocean margin that the land mass
    read smaller than intended inside the compact Home card
  - the screenshot used the new Public UI against a deployed/cached
    `GET /api/public/countries` response that still returned only `code` and
    product `count`; the intentionally optional `bank_count` compatibility
    field therefore caused the bank label to be omitted
- Outcome:
  - the map now uses a symmetric centered `55 27.5 890 445` viewport,
    enlarging the geometry by about 12% while keeping markers, graticules, and
    the local SVG aligned
  - Home still prefers `bank_count` from the country endpoint; only a country
    missing that field receives an unfiltered dashboard-summary compatibility
    lookup, using the established `banks_in_scope` metric
  - compatibility failures are caught per country, so they cannot turn an
    otherwise healthy Home or product count into an unavailable page; once
    the country response includes `bank_count`, no extra summary lookup is
    issued for that country
- Verification:
  - focused Public countries API module: 12 tests passed
  - Public TypeScript typecheck passed after a corrupted generated
    `.next/dev/types/routes.d.ts` was regenerated by Next dev
  - Public Production build passed
  - the existing local API was used as an exact old-response fixture:
    `/api/public/countries` omitted `bank_count`, while Home still rendered
    Canada with 16 banks and the United States with 10 banks
  - visual and DOM checks passed at 1440px EN, 768px JA, and exact 390px KO;
    every country row included its localized bank count and no document-level
    horizontal overflow was present
- Boundaries: no Public API formula, canonical product, aggregate eligibility,
  country scope, Production deployment, external map service, or unrelated
  dirty-worktree state was changed.

## 2026-08-27 - FPDS Admin Minimum Handover Playbook

- WBS: documentation-only Admin handover baseline; no WBS status changed.
- Status: the follow-in-order execution playbook and primary handoff routing are
  complete.
- Outcome:
  - reduced daily execution to nine gated steps: signed scope, code/assets,
    client-owned environments, full dev rehearsal, five minimum manuals,
    role-based training, client-led UAT, Production cutover, and ten-business-
    day hypercare
  - gave the Product Owner concrete checkboxes, expected evidence filenames,
    pass criteria, and stop conditions instead of requiring them to interpret
    a separate project-management plan
  - retained non-negotiable Public exclusion, private-evidence/secrets handling,
    dev-only stateful rehearsal, restore/rollback proof, independent operator
    performance, client ownership, and final access revocation
  - added a one-page final GO/NO-GO checklist and linked the playbook as the
    primary Admin handover entrypoint from the root README and docs map
- Key files:
  - `docs/01-planning/fpds-admin-handover-minimum-playbook.md`
  - `README.md`
  - `docs/README.md`
- Verification:
  - the new cross-document Markdown links resolved locally
  - changed-document whitespace and final-newline checks passed
  - `git diff --check` passed after closeout
  - no application build/test was run because this follow-up changes only
    documentation and no runtime behavior
- Boundaries: no credential, account, data, runtime, deployment, scheduler,
  external service, Public surface, canonical fact, or WBS state changed.
- Next step: fill the owner/date table at the top of the playbook, complete Step
  1 signatures, and do not start code transfer until its stop gate is clear.

## 2026-08-27 - FPDS Admin Graphical Mark Removal

- WBS: small Product Owner-directed Admin UI refinement; no WBS status changed.
- Status: complete.
- Outcome:
  - removed the graphical `F`/record-dot mark from Login and Signup, the
    authenticated Admin header, and Admin modal context panels
  - retained the localized `FPDS Admin` text identity and left all bank logos,
    navigation, country, locale, authentication, and modal behavior unchanged
  - removed the now-unused `admin-mark.tsx` component and recorded the identity
    presentation override
- Key files:
  - `app/admin/src/components/fpds/admin/admin-auth-frame.tsx`
  - `app/admin/src/components/fpds/admin/admin-shell.tsx`
  - `app/admin/src/components/fpds/admin/admin-modal.tsx`
  - `docs/03-design/ui-override-register.md`
- Verification:
  - Admin `pnpm run typecheck`: passed
  - Admin `pnpm run build`: passed
  - Login visual checks passed at 1440px and 768px; an exact 390x844 CSS
    viewport check confirmed `scrollWidth=390`, no Admin mark, and retained
    text identity
  - repository `git diff --check`: passed
- Boundaries: no bank logo, Public identity, auth/session behavior, data,
  external service, deployment, or Product scope changed.

## 2026-08-27 - Review Queue Result-Only Search and Context Return

- WBS: Product Owner-directed Admin Review Queue refinement; no WBS status
  changed.
- Status: complete.
- Outcome:
  - Search, reset, page-size selection, pagination, bulk-action refresh, and
    visible auto-refresh now use an authenticated same-origin Queue proxy and
    replace only the results region
  - operators can select `20`, `50`, or `100` rows; missing or invalid input
    resolves to `20` and the selected value is passed to the existing API
  - active search, filters, sort, page, page size, and locale stay in the
    browser URL; Queue detail links carry a same-origin allowlisted
    `return_to` context
  - Review Detail Back, Reject, and Defer return to that preserved Queue
    context, while direct or invalid return paths fall back to the localized
    Queue root
  - added concise Korean handover scope at `00-Scope/scope.md`
- Key files:
  - `app/admin/src/lib/review-queue-query.ts`
  - `app/admin/src/app/admin/reviews/data/route.ts`
  - `app/admin/src/components/fpds/admin/review-queue-surface.tsx`
  - `app/admin/src/components/fpds/admin/review-queue-results.tsx`
  - `app/admin/src/app/admin/reviews/[reviewTaskId]/page.tsx`
  - `app/admin/src/components/fpds/admin/review-detail-surface.tsx`
  - `00-Scope/scope.md`
- Verification:
  - focused query assertions passed for default/invalid `page_size`, the
    `20/50/100` allowlist, date conversion, filter normalization, and rejection
    of external or non-Queue return paths
  - Admin `pnpm run typecheck`: passed
  - Admin `pnpm run build`: passed; `/admin/reviews/data` was included in the
    generated route table
  - synthetic-data browser verification recorded no additional Document
    request during Search and seven results-only requests across search,
    reset, page size, pagination, failure, and delayed-loading scenarios
  - loading, retained-results error, empty, default 20-row, 50-row, second-page,
    and detail return-link states passed
  - EN/KO/JA checks passed at 1440px, 768px, and exact 390x844; no
    document-level horizontal overflow was present, and the 390px result was
    visually inspected
- Boundaries: no API schema, DB/canonical data, review-decision semantics,
  RBAC, CSRF, session-country authority, Public surface, external service, or
  deployment state changed. Live Reject was not submitted against the shared
  database; its navigation path was verified without mutating review data.

## 2026-08-28 - FPDS Admin Manual-Only Collection Boundary

- WBS: `5.54` (`Completed`); decision `D-069` supersedes the recurring
  execution portion of `D-042`.
- Status: repository implementation and active-document alignment complete.
  Migration `0044` is committed for the next approved DB deployment but was
  not applied to the shared database in this slice.
- Outcome:
  - removed the API lifespan collection loop, leader lock, cadence policy
    loader, runtime flags, scheduler module, and its dedicated tests
  - fixed source-catalog collection and runner lineage to authenticated Admin
    trigger values and removed the scheduler actor from current write contracts
  - changed registry refresh discovery to explicit manual mode while retaining
    candidate-diff generation and approval-first registry protection
  - added migration `0044_remove_admin_collection_scheduler.sql` to delete the
    former recurring collection/recovery policy rows
  - aligned requirements, workflow/interface/state design, environment,
    retention, runtime, DB, worker, RAID, WBS, handover, and `00-Scope` docs
    with operator-initiated collection and retry
  - retained historical migration, decision, actor/run, and journal records for
    traceability; financial rate/fee schedules and Admin table auto-refresh are
    unrelated and remain unchanged
- Key files:
  - `api/service/api_service/main.py`
  - `api/service/api_service/config.py`
  - `api/service/api_service/source_catalog.py`
  - `worker/discovery/fpds_registry_refresh/service.py`
  - `db/migrations/0044_remove_admin_collection_scheduler.sql`
  - `docs/00-governance/decision-log.md`
  - `docs/02-requirements/FPDS_Requirements_Definition_v1_5.md`
  - `00-Scope/scope.md`
- Verification:
  - full API unit suite: 431 tests passed
  - full discovery-worker suite: 63 tests passed
  - Admin `pnpm run typecheck`: passed
  - Admin `pnpm run build`: passed
  - root Vercel/FastAPI entrypoint import: passed (`FPDS Admin API`)
  - active-code/document search found no recurring execution reference outside
    the removal migration and the regression fixture for ignored legacy flags
  - `git diff --check`: passed with line-ending conversion warnings only
- Boundaries: no collection, retry, Review, approval-triggered aggregate
  refresh, watchdog, financial-field schedule semantics, Public behavior,
  canonical data, shared DB state, external service, or deployment was changed
  beyond removal of the unattended Admin execution path.
- Next step: apply migration `0044` through the approved deployment process and
  verify the six former collection-automation policy keys are absent in each
  target database.

## 2026-08-28 - Repository Artifact Cleanup with Public Preservation

- Status: non-Public cleanup complete. FPDS Public is excluded only from the
  Admin handover and remains fully present in the repository.
- Outcome:
  - removed 219 tracked `tmp` logs, collection registry outputs, and test
    persistence artifacts
  - preserved four one-off `tmp` helpers because they include Public audit,
    refresh, API-check, or projection-reset behavior, even though one helper's
    retired scheduler import means it is not a current Admin runtime dependency
  - removed the historical static prototype viewer, its worker exporter and
    dedicated test after Admin Review Detail and Run Detail superseded it
  - removed seven accidentally tracked Python bytecode files and local
    regenerable root build/cache/package metadata
  - retained `app/public`, anonymous Public API modules/tests, Vercel settings,
    Public design/product documents, Public QA artifacts, all DB migrations,
    aggregate refresh/health, and archive evidence
  - replaced stale archive links to the retired static viewer with preserved
    archived output/evidence references
- Key files:
  - `app/README.md`
  - `worker/README.md`
  - `worker/pipeline/README.md`
  - `docs/01-planning/WBS.md`
  - `docs/archive/00-governance/gate-b-prototype-review-note.md`
  - `docs/archive/01-planning/evidence/2026-04-11-first-successful-run/evidence-pack.md`
- Verification:
  - exact Public path diff guard: passed; no Public code, API, test, deployment,
    or Public-only document diff remains
  - Admin and Public `pnpm run typecheck`: passed
  - Admin and Public `pnpm run build`: passed
  - full API suite: 431 tests passed
  - full worker suite: 521 tests passed after removing the obsolete viewer test
  - foundation baseline validation: passed
  - repository project checks: passed for Admin and Public typecheck/build
  - tracked-source checks: 83 Markdown references, 8 PowerShell syntax files,
    and 56 JSON syntax files passed; active deleted-path references: zero
  - `git diff --check`: passed with line-ending conversion warnings only
  - full foundation entrypoint was run but repo-doctor stopped on ignored Public
    Chromium QA profile data stored with a `.json` suffix but newline-delimited
    contents; the Public artifact and harness policy were intentionally left
    unchanged
- Boundaries: no Public runtime/content deletion, Admin product behavior,
  canonical/DB/object-storage data, cloud deployment, account, secret, or
  external service changed. Existing user edits to Admin scope and handover
  documents were preserved.

## 2026-08-29 - FPDS Admin External-Service and Database Handover Inventory

- WBS: documentation-only Admin handover completion; no WBS status changed.
- Status: repository handover inventories and scope checklist complete; actual
  account transfer, environment provisioning, migration reconciliation, and
  Cutover remain client-executed gates.
- Outcome:
  - added a separate current-state inventory for GitHub, Admin compute,
    Supabase PostgreSQL, AWS S3, Admin domain/DNS/TLS, OpenAI, monitoring,
    secret management, official source sites, DB-backed auth, UI asset tooling,
    and BX-PF, with safe account/ownership/security/recovery templates
  - clearly marked Admin web/API/worker production hosting, Admin
    domain/DNS/TLS, production monitoring, and a dedicated secret manager as
    not ready; retained Vercel switchabank-api as a Public-read exception
    rather than an Admin production deployment
  - documented all 44 committed migrations through 0044 and read shared dev
    through a read-only PostgreSQL transaction: latest history is 0044, with
    31 base tables and two discard-only compatibility views
  - recorded the shared-dev 0013 application-effect drift and the distinct
    history limitations of 0009, 0014, and 0015 instead of silently declaring
    a clean schema
  - added the live physical schema dictionary, four bounded Mermaid ERDs,
    reconciliation/restore checklist, and required restricted evidence paths
  - expanded 00-Scope/scope.md into a final handover checklist and connected
    the new files from the root README, docs map, DB README, and minimum
    handover playbook
- Key files:
  - 00-Scope/external-services-and-accounts.md
  - 00-Scope/database-migrations-schema-erd.md
  - 00-Scope/scope.md
  - docs/01-planning/fpds-admin-handover-minimum-playbook.md
  - README.md
  - docs/README.md
  - db/README.md
- Verification:
  - repository migration filenames and document rows matched 44/44 with no
    difference
  - read-only shared-dev information_schema/pg_constraint checks found 33
    public relations and every relation name is covered by the schema document
  - migration_history, policy v2, Canada deposit taxonomy, columns, PKs, and
    FKs were inspected read-only; no DB mutation or migration application ran
  - changed local Markdown links resolved; credential-pattern scan returned no
    finding; UTF-8, final newline, and all seven fenced blocks passed
  - foundation baseline validation passed
  - git diff --check passed with line-ending conversion warnings only
- Known issue:
  - a Mermaid CLI was not installed, so the four diagrams received structural
    fence/entity review but not renderer execution
  - shared dev needs an approved 0013 reconciliation and fresh-replay/schema
    comparison before the handover checklist can be signed
- Boundaries: no external account, credential, deployment, domain, DNS, TLS,
  cloud resource, DB row/schema, object, canonical fact, Public behavior, or
  runtime code changed.
- Next step: the client owner fills the restricted ownership matrix, provisions
  separated Admin production services, resolves the DB drift through the
  approved DBA process, and completes rehearsal/restore/UAT before Cutover.

## 2026-08-31 - AI Bank Onboarding Transport and DB Failure Hardening

- Status: reported `Add banks with AI` failure reproduced from the supplied
  traceback, corrected in the API runtime, and covered by regression tests.
- Root cause:
  - the OpenAI Responses web-search request ended with Windows transport reset
    `10054`
  - the request held the initial PostgreSQL transaction open throughout the
    provider wait; that connection was then unavailable when the failure path
    tried to complete `model_execution`, replacing the intended bounded 502
    response with an unhandled ASGI 500 traceback
- Outcome:
  - commits the started model execution before the external provider wait so
    the database session is not left idle in a transaction
  - retries exactly once for a transport reset, timeout, or URL transport
    failure, while provider HTTP errors retain their existing single-attempt
    status handling
  - starts a new outer transaction before the atomic bank/coverage savepoint,
    preserving all-or-nothing registry creation and final model metadata
  - treats failure metadata/compatibility-ledger writes as best effort; if the
    provider and database both disconnect, the route still returns the existing
    `502 bank_ai_onboarding_failed` result and never enters the bank write batch
- Key files:
  - `api/service/api_service/bank_ai_onboarding.py`
  - `api/service/tests/test_bank_ai_onboarding.py`
  - `api/service/README.md`
- Verification:
  - focused bank AI onboarding suite: 14 tests passed
  - full API unit suite: 453 tests passed
  - regressions cover commit-before-provider ordering, one successful retry
    after `ConnectionResetError(10054)`, bounded failure when model-execution
    completion also loses the DB connection, existing success, and batch
    rollback behavior
  - `git diff --check` passed before documentation closeout
- Boundaries: no live provider request, bank/coverage creation, shared database
  mutation, collection, Review decision, canonical fact, Public snapshot,
  deployment, credential, or external configuration changed.
- Next step: restart the local Admin API so it loads the fix, then retry `Add
  banks with AI`; deploy through the approved Admin release process before
  expecting the same behavior in another environment.

## 2026-08-31 - AI Bank Onboarding Official-Source Budget Hardening

- Status: the follow-up `bank_ai_results_insufficient` failure was diagnosed
  from the latest shared-dev execution and corrected without weakening bank,
  duplicate, official-source, Product Type, or atomic-write validation.
- Root cause:
  - read-only inspection of model execution `modelexec_HNa8UD8d37Arq1jy`
    found 32 consulted URLs, all from FDIC/FFIEC ranking, data, help, PDF, or
    derivative search results; no candidate official bank homepage or current
    product page was consulted
  - the shared model runtime allowed at most four web-search tool calls while
    the five-bank request asked for up to 13 fully sourced candidates, so the
    model exhausted its search budget on ranking discovery and every candidate
    correctly failed official-source validation
- Outcome:
  - the shared AI runtime retains its four-call default and accepts only an
    explicit bounded caller override from 1 through 20
  - bank onboarding now uses a requested-count-based search ceiling: 8 calls
    for one through three banks, 10 for four, 12 for five, up to 20 for nine or
    ten; the selected limit and candidate limit are persisted in execution
    metadata under contract v4
  - extra-candidate research is reduced from `count + 8` to at most
    `count + min(3, count)`, making a five-bank request target at most eight
    candidates instead of thirteen
  - the prompt permits at most two ranking searches, then requires official
    homepage, legal-identity, and current product evidence for the requested
    count before any extra candidate; strict consulted-URL validation and
    all-or-nothing creation remain unchanged
- Key files:
  - `worker/pipeline/fpds_ai_runtime.py`
  - `worker/pipeline/tests/test_ai_runtime.py`
  - `api/service/api_service/bank_ai_onboarding.py`
  - `api/service/tests/test_bank_ai_onboarding.py`
  - `api/service/README.md`
  - `worker/pipeline/README.md`
- Verification:
  - focused shared AI runtime suite: 6 tests passed
  - focused bank AI onboarding suite: 15 tests passed
  - full API unit suite: 454 tests passed
  - full worker unit suite: 522 tests passed
  - regressions cover the unchanged default, a 12-call onboarding override,
    the 1..20 policy bound, five-bank candidate bounding, sourcing-first prompt
    ordering, persisted v4 limits, and existing atomic/provider failure paths
  - `git diff --check` passed with line-ending conversion warnings only
- Boundaries: diagnostics were read-only. No live provider request, bank or
  coverage write, shared database mutation, collection, Review decision,
  canonical fact, Public snapshot, deployment, credential, or external
  configuration changed.
- Next step: restart the local Admin API and retry `Add banks with AI`; a
  five-bank request will then use the v4 candidate/search budget.

## 2026-08-31 - AI Bank Onboarding Two-Stage Evidence Isolation

- Status: the Product Owner reported the same insufficiency after v4. The new
  execution was inspected read-only and the reusable orchestration defect was
  replaced with a two-stage v5 contract.
- Root cause:
  - execution `modelexec_ATMzCeEr3OSGXZs9` confirms the running API loaded v4:
    requested count 5, candidate limit 8, and web-search ceiling 12
  - despite the prompt ordering, all 38 consulted URLs were again regulator,
    ranking/statistical, aggregator, Wikipedia, filing, or news sources; zero
    candidate official bank homepage or product domain was consulted
  - a single model request could treat prompt ordering as guidance, so merely
    increasing the shared tool budget could not reserve searches for official
    evidence
- Outcome:
  - contract v5 performs a ranking-only call with its own strict schema and
    four-call search ceiling; it cannot emit homepage, legal, logo, or Product
    Type fields
  - the ranking result is passed to a second strict-schema call that cannot add
    candidates or repeat ranking research and may search only official
    homepage, legal-identity, and current product evidence, using the existing
    requested-count-based 8-to-20-call ceiling
  - provider request IDs, sources, prompt/completion tokens, and per-stage
    counts are combined into the one bounded operation record; if the official
    evidence stage fails, completed ranking usage and sources are still retained
  - insufficient-result metadata now records raw/accepted candidate counts and
    how many candidates supplied consulted homepage, legal-name, ranking,
    coverage, and relationship URLs. Official-source, duplicate, active Product
    Type, relationship, and atomic-write validation remain unchanged
- Key files:
  - `api/service/api_service/bank_ai_onboarding.py`
  - `api/service/tests/test_bank_ai_onboarding.py`
  - `api/service/README.md`
- Verification:
  - focused bank AI onboarding suite: 16 tests passed
  - full API unit suite: 455 tests passed
  - full worker unit suite: 522 tests passed
  - regression coverage proves isolated ranking/evidence calls, combined
    source validation, v5 persisted limits/request IDs, strict source
    diagnostics, one transport retry per stage, partial ranking-usage retention,
    and existing all-or-nothing bank creation
  - `git diff --check` passed with line-ending conversion warnings only
- Boundaries: the reported v4 execution and current country context were read
  only. No v5 live provider request, bank/coverage write, shared database
  mutation, collection, Review decision, canonical fact, Public snapshot,
  deployment, credential, or external configuration change was performed.
- Remaining verification: a model-only v5 dry run would send the existing bank
  and active Product Type payload to the configured OpenAI account and incur
  provider usage, so it requires explicit Product Owner approval. It performs
  no DB write.

## 2026-08-31 - AI Bank Onboarding Per-Candidate Evidence Isolation

- Status: the Product Owner approved the model-only v5 dry run. It proved that
  separating ranking from one batch evidence prompt was still insufficient;
  contract v6 now isolates official research per ranked bank.
- Live v5 evidence:
  - the first approved attempt completed ranking, then the official-evidence
    stage exhausted its transport retry on a DNS disconnect; no DB write ran
  - after network reconnection, ranking request
    `resp_0f7bb224ba1a1617016a95ea36639487d0a0b0033e994cd83c` completed with 33
    FDIC/FFIEC sources
  - batch evidence request
    `resp_02ac5b28a7b5c280016a95ea82a62087d099a10684b2db0b23` returned zero
    consulted sources and one placeholder candidate, `No verified candidate
    returned`; the unchanged sanitizer accepted zero of five
  - source diagnostics confirmed one raw candidate, one consulted ranking
    source, and zero candidates with consulted homepage, legal-name, coverage,
    or relationship sources
- Outcome:
  - v6 keeps the ranking-only call, server-filters/deduplicates its bounded
    candidates, and sends exactly one immutable ranked candidate to each
    official-evidence call
  - each candidate receives at most four official searches; an unsourceable
    candidate returns an empty array and the server advances to the next rank
  - evidence must identity-match the pinned ranking candidate, and the server
    overwrites all rank/metric/source fields with the ranking-stage values
    before applying the unchanged full sanitizer
  - the operation stops as soon as the requested number of banks passes the
    sanitizer; otherwise it remains an atomic `bank_ai_results_insufficient`
    failure with no registry write
  - per-candidate provider stages, request IDs, tokens, sources, failure rank,
    and partial completed-stage usage remain auditable
- Key files:
  - `api/service/api_service/bank_ai_onboarding.py`
  - `api/service/tests/test_bank_ai_onboarding.py`
  - `api/service/README.md`
- Verification:
  - focused bank AI onboarding suite: 17 tests passed
  - full API unit suite: 456 tests passed
  - full worker unit suite: 522 tests passed
  - regressions cover candidate pinning, rank/identity preservation, an empty
    first candidate advancing to the next rank, sanitizer-based early stop,
    partial usage retention, and existing atomic/provider failure behavior
  - `git diff --check` passed with line-ending conversion warnings only
- Boundaries: the approved v5 calls incurred provider usage but performed no
  bank, coverage, audit, usage-ledger, or other DB write. The v6 live call did
  not run because its potential one-ranking-plus-eight-evidence request scope
  requires fresh explicit Product Owner approval.

## 2026-08-31 - AI Bank Onboarding Exact Ranking and Homepage Evidence

- Status: the Product Owner explicitly approved the expanded v6 model-only dry
  run. It identified one ranking-shape defect and one equivalent official-URL
  mismatch; contract v7 corrects both without relaxing legal/product evidence.
- Live v6 evidence:
  - ranking request `resp_056d3ddfcfe4c45d016a95ecf5f5d487d09ceb745817cbe58a`
    returned only one entry instead of the eight-candidate limit and used the
    report title `U.S. Domestically Chartered Commercial Banks, Ranked by
    Consolidated Assets` as `ranking_name`
  - the retained rank/alias still resolved to Fifth Third Bank; evidence request
    `resp_082ce26440b17bb2016a95ed1155c487d0ac85d134dc93d99b` consulted 43
    sources, including 32 on `53.com` or its subdomains, and returned one bank
  - legal-name, ranking, coverage, and relationship URLs were consulted, but the
    proposed homepage root did not exactly match any returned source path, so
    the unchanged exact-URL check accepted zero candidates
- Outcome:
  - v7 creates the ranking JSON schema per request and requires exactly
    `candidate_limit` entries rather than permitting one through twenty
  - ranking instructions require an institution-row label, and the server
    rejects common report/table heading shapes before spending evidence calls
  - if the proposed homepage source path was not returned, the server selects a
    URL that was actually consulted on the exact same normalized homepage host;
    subdomain-only, off-domain, or unconsulted legal/ranking/product/relationship
    evidence is not substituted
  - source diagnostics now distinguish exact homepage-source consultation from
    same-homepage-host consultation
- Key files:
  - `api/service/api_service/bank_ai_onboarding.py`
  - `api/service/tests/test_bank_ai_onboarding.py`
  - `api/service/README.md`
- Verification:
  - focused bank AI onboarding suite: 19 tests passed
  - full API unit suite: 458 tests passed
  - full worker unit suite: 522 tests passed
  - regressions cover exact dynamic ranking cardinality, report-title rejection,
    same-host consulted homepage recovery, off-domain rejection, per-candidate
    fallback, and the existing full sanitizer/atomic-write boundaries
  - `git diff --check` passed with line-ending conversion warnings only
- Boundaries: the approved v6 calls incurred provider usage but performed no
  DB write. A v7 live run has not executed because it changes the external
  ranking schema and homepage evidence payload and therefore requires fresh
  explicit Product Owner approval despite retaining the same maximum call count.

## 2026-08-31 - AI Bank Onboarding Relevant-Source Retention

- Status: the Product Owner explicitly approved the v7 model-only run. It
  validated exact ranking cardinality and per-candidate search, then exposed a
  server-side source aggregation cap; contract v8 corrects that loss. The
  subsequently approved retry-expanded v8 model-only run passed the unchanged
  five-bank sanitizer.
- Live v7 evidence:
  - ranking request `resp_07b0d39bb48089ab016a95ee5028e087d0afbe4772f3948b75`
    returned exactly eight candidates and 51 ranking sources
  - eight candidate-specific evidence requests returned 19 through 48 sources
    each, including Fifth Third, Huntington, BMO, and First Citizens official
    domains; one Huntington transport timeout retried successfully
  - the merge path truncated combined sources at 100 before the final sanitizer,
    so later candidate official URLs were absent even though their individual
    provider responses had consulted them
  - the final bounded diagnostics showed eight raw candidates but only one
    accepted, two with exact retained coverage/relationship sources, and four
    with retained homepage-host evidence
- Live v8 evidence:
  - the explicitly approved v8 run returned exactly ten ranked candidates after
    one ranking timeout retry, then completed six candidate-specific evidence
    responses with 22 through 52 consulted sources each
  - the seventh candidate stopped on an OpenAI `503 Service Unavailable`; the
    prior transport classifier deliberately treated every HTTP error as
    non-retryable, so the already-completed stages could not continue to the
    remaining consumer-bank candidates
  - after explicit approval of the bounded gateway retry, ranking request
    `resp_03ff33023b8a792a016a95f44b61a887d0b8101e3e444442f7` returned exactly
    ten candidates and 23 total sources; six evidence requests then completed
    without a retry and the sanitizer stopped early after accepting five banks
  - the successful run retained 35 relevant consulted sources across official
    domains and accepted Huntington Bank, BMO, First Citizens Bank, American
    Express, and M&T Bank from six raw evidence candidates; the accepted
    coverage included mortgage, savings, GIC, line of credit, credit card,
    personal loan, and chequing product types
  - the successful provider request chain was the ranking request above plus
    `resp_016deb67507bc864016a95f4607b5887d0b6660494f028d7e4`,
    `resp_0fd288b3dc3a9670016a95f47c634887d09e46cd16288d5b68`,
    `resp_0fa3fcf2b95c86fc016a95f496a6f487d0aa9e949a09377821`,
    `resp_00f7acf04bc04bb6016a95f4b5a8d887d0acb731026c13b046`,
    `resp_0755d3daba589bf4016a95f4d5311087d09e13634c2b96a88a`, and
    `resp_024af6777d56c7b3016a95f4edc03c87d09b3a4f796155e2fa`
- Outcome:
  - v8 filters every completed model stage before aggregation, retaining only
    URLs referenced by ranking, legal, homepage, logo, coverage, or relationship
    fields plus one actually consulted exact-host homepage URL when needed
  - total provider source counts and retained relevant counts remain distinct in
    model-stage metadata; combined relevant sources have a bounded 250-item cap
    instead of allowing early discovery noise to consume a 100-item global cap
  - the five-bank candidate limit increases from eight to ten to get past large
    custody/investment-only institutions; per-candidate processing still stops
    immediately once five banks pass the unchanged sanitizer
  - bounded provider retry now includes gateway `502`, `503`, and `504` in
    addition to connection reset/timeout/URL transport failures; HTTP `4xx` and
    other provider contract errors remain single-attempt
- Key files:
  - `api/service/api_service/bank_ai_onboarding.py`
  - `api/service/tests/test_bank_ai_onboarding.py`
  - `api/service/README.md`
- Verification:
  - focused bank AI onboarding suite: 21 tests passed
  - full API unit suite: 460 tests passed
  - full worker unit suite: 522 tests passed
  - regression coverage proves that 120 preceding irrelevant sources cannot
    displace late exact official evidence and that retained/total source counts,
    candidate fallback, source safety, `503` versus `400` retry classification,
    and atomic creation remain bounded
  - `git diff --check` passed with line-ending conversion warnings only
- Boundaries: the approved v7 and both v8 calls incurred provider usage but
  performed no DB write. The final approved v8 validation was a model-only dry
  run: it exercised the production sanitizer but did not invoke the Admin bank
  creation transaction, audit write, or usage-ledger write.

## 2026-08-31 - Interrupted Admin Collection Recovery

- Status: recovered the zero-progress remainder of source-catalog collection
  `collection_uQka60tuZBPa68YR` after a local server/database interruption.
- Diagnosis:
  - six of the original 23 US runs had completed
  - 17 runs remained `started` with no source scope, source item, model
    execution, candidate, or Review progress
  - the original runner log ended after Supabase DNS/network failures and could
    not persist terminal failure state; no original runner process remained
- Recovery:
  - retained the six completed runs unchanged
  - transitioned the exact 17 stale runs to `retried` with the interruption
    reason, completion time, and replacement-run metadata
  - created replacement collection `collection_RafvZX3T4bAgOdcC` with exactly
    the same 17 country/bank/Product Type/catalog scopes
  - stored 17 bidirectional old/new retry links and launched one sequential
    source-catalog runner using precision discovery
- Verification:
  - read-only dry run passed exact-count, zero-progress, active-catalog, and
    no-competing-run guards
  - post-write SQL returned `completed=6` and `retried=17` for the original
    collection, with 17/17 retry links, identity matches, and recovery reasons
  - the replacement runner remained alive and its log advanced from run start
    to `fpds_snapshot` for the first BMO line-of-credit run
  - the first replacement run persisted five collection sources and two target
    detail sources before snapshot processing
- Key evidence:
  - `tmp/source-catalog-collections/collection_uQka60tuZBPa68YR.log`
  - `tmp/source-catalog-collections/collection_RafvZX3T4bAgOdcC.json`
  - `tmp/source-catalog-collections/collection_RafvZX3T4bAgOdcC.log`
- Boundaries: no completed run was recollected, and no schema, runtime code,
  canonical fact, Review decision, or collection policy was changed manually.
  The normal replacement collection remains in progress and may perform its
  existing guarded source, candidate, Review, promotion, and aggregate effects.
- Next step: monitor `collection_RafvZX3T4bAgOdcC` in Runs until its 17 groups
  reach terminal states; investigate only if the runner disappears or its log
  and DB progress both stop advancing.

## 2026-08-31 - Server-Restart Replacement Collection Recovery

- Status: recovered the interrupted remainder of replacement collection
  `collection_RafvZX3T4bAgOdcC` after another local server restart.
- Diagnosis:
  - six of its 17 runs had completed and were retained unchanged
  - the source-catalog runner and worker-stage processes were absent
  - one FCB mortgage run had reached normalization and stopped immediately
    after launching validation routing; ten later runs had never started work
- Recovery:
  - transitioned exactly the 11 stale `started` runs to `retried` with an
    interruption reason, completion time, and recovery metadata
  - created replacement collection `collection_XQchKyN0HiK603Yy` with only
    the same 11 country/bank/Product Type/catalog scopes
  - stored 11 bidirectional old/new retry links and launched one sequential
    source-catalog runner
- Verification:
  - the guarded dry run passed exact-count, inactivity, active-catalog,
    one-to-one catalog, and no-competing-run checks
  - post-write SQL returned `completed=6` and `retried=11` for the interrupted
    collection and 11 new runs, with 11/11 valid retry and identity links
  - the replacement runner and its child snapshot worker remained alive
  - the first FCB mortgage run entered `fpds_snapshot`, materialized ten source
    scopes and ten source items, and recorded a fresh model execution
- Key evidence:
  - `tmp/source-catalog-collections/collection_RafvZX3T4bAgOdcC.log`
  - `tmp/source-catalog-collections/collection_XQchKyN0HiK603Yy.json`
  - `tmp/source-catalog-collections/collection_XQchKyN0HiK603Yy.log`
- Boundaries: no completed run was recollected and no schema, runtime code,
  canonical fact, Review decision, or collection policy was manually changed.
  The database's bounded operational-storage policy discards `audit_event`
  writes, so the durable recovery evidence is the bidirectional run linkage,
  recovery metadata, interruption reason, plan, and runner log. The normal
  replacement collection remains in progress and retains its existing guarded
  downstream effects.
- Next step: monitor `collection_XQchKyN0HiK603Yy` in Runs until all 11 groups
  reach terminal states; investigate only if its process disappears or both
  log and database activity stop advancing.

## 2026-09-02 - Minimal Admin Handover Execution Guide

- Status: documentation-only handover execution guide complete; no WBS or
  runtime status changed.
- Outcome:
  - added `descent/README.md` as a single follow-in-order checklist for the
    Product Owner and handover participants
  - compressed the existing baseline into eight gated steps: signed scope,
    release readiness, client-owned environment, dev migration/recovery
    rehearsal, consolidated operations handbook and training, client-led UAT,
    Production cutover, and ten-business-day Hypercare closure
  - limited the working pack to eight evidence documents beyond the guide by
    consolidating the former minimum manual subjects into one operations
    handbook without removing deployment, operator, recovery, security, or
    known-limitation content
  - retained the Admin-only boundary, client ownership, secret/private-evidence
    exclusion, real restore/rollback proof, zero Critical/High defects,
    independent client operation, final secret rotation, access revocation,
    and signed closure
- Key file: `descent/README.md`.
- Verification:
  - UTF-8 text and the complete heading/step structure were inspected
  - no malformed replacement characters or placeholder corruption were found
  - new Markdown references resolve to existing repository documents
  - documentation whitespace validation passed
- Boundaries: no source cleanup, test execution, account or secret transfer,
  database/storage operation, deployment, UAT, Cutover, Public behavior,
  canonical data, or external service changed. The eight listed evidence files
  are execution outputs to create during the handover, not claims of completed
  transfer work.

## 2026-09-02 - Regions Savings HTTP-200 Challenge Recovery

- Status: latest US Admin partial-run RCA, generic recurrence hardening, and
  targeted clean recollection complete.
- Diagnosis:
  - run `run_20260902_035832_rb_savings_collect_9qU3ddp5` received an Imperva
    `Pardon Our Interruption` / `Security check: JavaScript disabled` shell
    with HTTP 200 from the official Regions Savings route
  - the prior fetch boundary handled HTTP 403 generically but treated this
    successful-status shell as product-page HTML, so discovery produced no
    eligible detail source and completed Partial
  - the first bounded recovery run exposed a second generic edge: concurrent
    fresh browser sessions could be re-challenged, and a declared PDF route
    could return an empty HTML viewer that failed only during parsing
- Outcome:
  - added high-confidence HTTP-200 access-challenge detection for any already
    SSRF-validated official domain and one bounded browser DOM recovery
  - serialized browser recoveries within one worker, retained transient
    browser/runtime failures as retryable, and rejected still-challenged pages
    before seed fallback or product extraction
  - required declared PDF sources to return PDF bytes before snapshot storage
  - made standard collection dynamically omit sources whose latest terminal
    result is a persisted post-browser challenge or PDF/content-type mismatch;
    registry status is not mutated and precision rediscovery remains the
    explicit revalidation path
- Live verification:
  - recovery run `run_20260903_022412_rb_savings_collect_PWQtQTl8` recovered
    real product pages and produced two candidates, while its remaining 3/5
    terminal source failures confirmed the concurrency/PDF edge
  - follow-up standard run `run_20260903_023940_rb_savings_collect_9iXR2zSU`
    skipped those three latest-terminal sources and completed with 2/2 source
    successes, zero failures, two candidates, and `partial_completion_flag=false`
  - Regions LifeGreen Savings passed and was auto-promoted through the normal
    guarded workflow; Regions Savings for Minors remained queued in Review
    after validation error; no manual candidate approval was applied
  - the earlier Regions GIC challenge-shell candidate remains private in
    Review with validation error and has no canonical product; it was not
    manually decided as part of this Savings-only recollection
- Verification:
  - focused API/runner tests: 33 passed
  - focused Worker discovery/snapshot tests: 44 passed
  - full API suite: 464 passed
  - full Worker suite: 525 passed
  - live official-page fetch returned 218 KB of rendered product HTML with
    `browser_html_fallback` / `html_access_challenge` provenance
- Key files:
  - `worker/discovery/fpds_discovery/fetch.py`
  - `worker/discovery/fpds_snapshot/capture.py`
  - `api/service/api_service/source_catalog.py`
  - `api/service/api_service/source_catalog_collection_runner.py`
  - `worker/discovery/tests/test_discovery.py`
  - `worker/discovery/tests/test_snapshot_capture.py`
  - `api/service/tests/test_source_catalog.py`
  - `api/service/tests/test_source_catalog_collection_runner.py`
- Boundaries: no unrelated bank or Product Type was recollected; no official
  domain, SSRF, evidence, Review, canonical, or publication gate was relaxed.

## 2026-09-02 - US Failed-Run Generic Transport Recovery

- Status: recent US Admin Failed-run RCA, generic recurrence hardening, and
  exact-scope replacement collection complete.
- Diagnosis:
  - the six latest Failed runs were the KeyBank Chequing, Credit Card, GIC,
    Mortgage, Personal Loan, and Savings groups from batch `20260902_035832`
  - all six failed in `source_collection` because every selected official
    `key.com` snapshot failed: 21 sources ended in `The read operation timed
    out` and eight ended in `Remote end closed connection without response`
  - the 29 sources made 87 attempts. Timeout and connection-close fallback was
    restricted to preconfigured rendering domains, and KeyBank was not one, so
    the worker never tried the browser path even though live browser DOM capture
    returned valid product HTML
  - the older US Failed rows are immutable history: 19 pre-current-schema
    extraction failures, 13 abandoned-run retention recoveries, and one DB
    connection termination. The 102 later completed US runs show those causes
    are no longer current recurrence paths
- Outcome:
  - any timeout, socket timeout, connection reset, or remote close from an
    already SSRF-validated official HTML source now receives one serialized
    browser DOM attempt, independent of bank and Product Type
  - successful recovery persists `browser_html_fallback` and
    `direct_transport_failure`; returned HTML still passes access-challenge,
    Product-Type, evidence, Review, and publication gates, and PDF content
    remains fail-closed
  - actual `RemoteDisconnected` behavior is covered directly in regression
    tests instead of relying only on its base connection-error type
  - companion discovery and later standard-scope reuse now exclude global user
    agreements and deposit-scope wealth/investment disclosures that contain no
    product context, while retaining product-specific agreements and pricing
    disclosures
- Live verification:
  - targeted collection `collection_Koc2vRat1GYm4pDY` completed all six groups
    with `partial_completion_flag=false`, zero source failures, and no error:
    Chequing 3/3 sources and three candidates; Credit Card 2/2 and two; GIC 2/2
    and two; Mortgage 13/13 and 13; Personal Loan 3/3 and three; Savings 7/7
    and five
  - all 30 stored snapshots record `browser_html_fallback` with
    `direct_transport_failure`; the six runs produced 28 candidates, of which
    seven passed the guarded approval path and 21 remain private in Review
  - the next KeyBank Savings standard scope resolves to the five product
    details only; the global KIS disclosure and site user agreement are omitted
    without mutating registry history
  - no US ingestion run remained `started` after the collection runner exited
- Verification:
  - focused Worker discovery/snapshot tests: 46 passed
  - focused API catalog/runner tests: 197 passed
  - full API suite: 466 passed
  - full Worker suite: 527 passed
  - live official KeyBank fetch returned valid 338 KB product HTML through the
    generic browser path with no challenge signature
- Key files:
  - `worker/discovery/fpds_discovery/fetch.py`
  - `api/service/api_service/source_catalog.py`
  - `api/service/api_service/source_catalog_collection_runner.py`
  - `worker/discovery/tests/test_discovery.py`
  - `api/service/tests/test_source_catalog.py`
  - `api/service/tests/test_source_catalog_collection_runner.py`
  - `worker/README.md`
  - `api/service/README.md`
  - `docs/03-design/source-registry-refresh-and-approval-policy.md`
  - `docs/00-governance/decision-log.md`
  - `docs/01-planning/WBS.md`
- Boundaries: no unrelated bank or Product Type was recollected, no manual
  Review decision was applied, and no official-domain, SSRF, evidence,
  canonical, or publication gate was relaxed. Historical Failed rows were not
  rewritten or deleted.

## 2026-09-03 - Admin Handover Scope And Owners

- Status: documentation-only handover scope record complete.
- Outcome:
  - added `descent/01-scope-and-owners.md` with the Admin-only scope, known
    contacts, target schedule, final client ownership, and approval fields
  - left unknown owner, date, and evidence-store details explicitly pending
    instead of inventing assignments
  - retained the stop condition that source and data transfer cannot begin
    until scope and ownership are approved
- Verification: UTF-8 content, Markdown structure, and repository whitespace
  checks passed.
- Boundaries: no runtime, external account, secret, data, access, deployment,
  or handover state was changed.

## 2026-09-03 - GSC SEO Canonical and Product-Content Hardening

- Status: repository implementation and production-like verification complete;
  production deployment and GSC follow-up remain Product Owner operations.
- Diagnosis:
  - parsed every CSV in the two `2026-09-03` GSC ZIP exports; the available
    performance window held 1 click / 79 impressions, while coverage reported
    17 indexed and 193 non-indexed pages on `2026-08-27`
  - catalog state was copied into product links, and every product locale was
    self-canonical/indexable/hreflang-listed even though product facts remain
    source language; the Japanese BMO URL therefore carried contradictory
    locale and English-intent discovery signals
  - product metadata fallback reused a Deposit category title, category crawl
    discovery after the first batch depended on client loading, and product
    pages had too little concise product-specific explanatory context
  - the full generated-sitemap audit found two active CA BMO Performance
    Chequing Account records competing with identical metadata
- Outcome:
  - added one product URL policy used by links, proxy redirects, metadata,
    structured data, and sitemap; irrelevant listing/tracking state now returns
    one 308 to a clean active product route, while invalid IDs remain 404
  - retained static-page EN/KO/JA indexing, but made incomplete KO/JA product
    variants usable `noindex,follow` with an English canonical and no product
    sitemap/hreflang membership; `<html lang>` now renders on the server
  - added unique type-specific metadata, verified-fact descriptions, truthful
    FinancialProduct/LoanOrCredit and collection graphs, visible breadcrumbs,
    server product overviews, related same-bank/type links, and crawlable
    no-script catalog paging without changing financial facts
  - resolved `prod_OOVZNobikI65DAAF` as Scotiabank The Long and Short Mortgage;
    preserved its clean route and visibility
  - consolidated older duplicate `prod_LuH-Kei2S8uFFOyY` by 308 to the newer
    verified `prod_SNcPg2yBYt4rgyAt`, without mutating canonical data
  - corrected the 390px product-detail intrinsic-width overflow found during
    browser QA; exact DevTools measurements now show 390px client/scroll width,
    one H1 within x=374, and zero overflow offenders
- Verification:
  - Public lint passed with zero warnings
  - Public TypeScript check passed
  - Public URL policy tests: 5 passed
  - Next.js 16.2.3 Webpack production build passed against the deployed Public
    API origin
  - production-like SEO audit passed all 225 sitemap URLs and 10 required
    representative routes, plus localized/noindex, polluted redirect, duplicate
    alias, deposit/card sample, and invalid-product cases
  - responsive QA passed at exact 390px, 768px, and 1440px with no document
    width overflow; final repository `git diff --check` is recorded at handoff
- Key files:
  - `app/public/src/lib/public-url-policy.ts`
  - `app/public/src/lib/public-seo.ts`
  - `app/public/src/proxy.ts`
  - `app/public/src/app/sitemap.xml/route.ts`
  - `app/public/src/app/products/[productId]/page.tsx`
  - `app/public/src/components/fpds/public/product-detail-surface.tsx`
  - `app/public/src/components/fpds/public/public-structured-data.tsx`
  - `app/public/scripts/seo-audit.mjs`
  - `docs/seo/gsc-2026-09-03-action-plan.md`
- Decisions: D-075 and WBS 5.60 record the source-language product indexing,
  clean canonical, and duplicate-alias baseline.
- Known issues: indexing/ranking remain controlled by Google; the upstream API
  remains a dynamic-render dependency, and the hosting layer still gives the
  HTTP apex a two-hop HTTPS/www redirect chain.
- Next step: deploy Public, execute the documented live checklist, resubmit the
  sitemap, request indexing only for the priority clean URLs, and capture 7-day
  and 28-day GSC comparisons.
- Boundaries: no database row, financial fact, Review/publish gate, secret,
  production deployment, GSC property, or raw export was modified.

## 2026-09-03 - Public PageSpeed Performance and Accessibility Hardening

- Status: repository implementation and production-like verification complete;
  production deployment and post-deployment PageSpeed reruns remain Product
  Owner operations.
- Diagnosis:
  - the supplied mobile runs scored 88-92 Performance, 93 Accessibility,
    96-100 Best Practices, and 100 SEO; the H1 was LCP at 3.3-3.5 seconds
    with about 2.4 seconds of element render delay
  - Home awaited summary and two ranking responses before emitting its hero,
    and its initial client graph included the Recharts runtime plus the Radix
    umbrella package; Lighthouse estimated 183-186 KiB of unused JavaScript
  - the 13.7 KB stylesheet was render-blocking, and runtime logo requests
    included oversized favicon images and short-cache third-party assets
  - logo wrappers used prohibited ARIA, logo images had no intrinsic size,
    and the footer locale trigger combined a mismatched accessible name with
    1.08:1 visible-text contrast
- Outcome:
  - split the server-rendered hero/finder and ranking data into independent
    Suspense boundaries while starting all upstream reads concurrently
  - replaced the client Recharts scatter with accessible server SVG plus an
    assistive table, removed Recharts, and replaced the Radix umbrella with
    direct Dialog, Dropdown Menu, and Slot packages
  - enabled Next inline CSS, removed the duplicate root locale synchronizer,
    and retained the Header-owned client-navigation locale update
  - restricted bank-logo browser images to five verified local assets, added
    explicit dimensions, and used an accessible bank-code mark for all other
    institutions
  - matched locale/country trigger accessible names to their visible labels
    and added a dark-footer locale style with readable contrast
- Verification:
  - Public lint, TypeScript, eight unit tests, and Next.js 16.2.3 Webpack
    production build passed
  - the Home client reference graph fell from 11 chunks / about 750 KiB raw
    to 9 chunks / 223.8 KiB raw; no Recharts reference remains
  - initial HTML has zero stylesheet links, zero third-party image sources,
    zero images without dimensions, and the H1 is present in the server
    document
  - local Lighthouse 13.4.1 mobile scored 88/100/100/100 with LCP 3.0 seconds,
    zero CLS, no console error, and 47 KiB estimated unused JavaScript;
    desktop scored 99/100/100/100 with LCP 0.8 seconds and zero CLS
  - the prior render-blocking, image-delivery, cache, ARIA, name-mismatch,
    contrast, and console-error audits all passed locally
  - exact 390px, 768px, and 1440px browser checks found zero horizontal
    overflow, zero third-party images, and zero missing image dimensions;
    the 390px mobile menu opened with six links and the footer locale menu
    opened with all three locale choices;
    EN/KO/JA plus a filtered Home route returned 200 with the expected
    document language and H1
- Verification limitation: Lighthouse wrote complete reports but its Windows
  CLI process returned exit 1 during post-report temporary-directory cleanup
  with `EPERM`; both JSON reports parsed normally and contain complete audits.
- Key files:
  - `app/public/src/app/dashboard/page.tsx`
  - `app/public/src/components/fpds/public/dashboard-hero.tsx`
  - `app/public/src/components/fpds/public/dashboard-surface.tsx`
  - `app/public/src/components/fpds/public/public-dashboard-charts.tsx`
  - `app/public/src/components/fpds/public/bank-logo.tsx`
  - `app/public/src/lib/public-bank-logo.ts`
  - `app/public/next.config.ts`
  - `app/public/package.json`
  - `app/public/README.md`
- Decisions: D-076 and WBS 5.61 record the first-paint, runtime, logo, and
  stylesheet baseline.
- Next step: deploy Public, rerun both supplied PageSpeed profiles against
  production, and compare mobile LCP, unused JavaScript, Accessibility, and
  Best Practices after CDN caches stabilize.
- Boundaries: no financial fact, ranking, finder rule, canonical data,
  publication gate, analytics policy, Admin behavior, secret, deployment, or
  external system was changed.
