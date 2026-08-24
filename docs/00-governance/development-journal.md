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

## 2026-08-12 - Continuous Collection-To-Public Recovery And Public Cards

- WBS: `5.25`, Admin collection automation, existing-candidate reconciliation,
  Public credit-card activation
- Status: complete in implementation, shared-dev migration/recovery, Public
  readback, full API/worker regression, and Public production build
- Goal: explain why registered and collected CA/US products were not reaching
  Public, publish every currently complete product, and remove routine operator
  dependency from collection through aggregate refresh.
- Why now: the Product Owner reported many Admin banks and collection results
  but few Public products and explicitly authorized a process redesign plus
  publication of the currently collected safe data.
- Outcome:
  - confirmed that registration and collection counts were not publication
    counts: the latest five collections included rejected/superseded and Review
    candidates, while only 60 of 171 active canonical rows met the current
    country/Product Type essential contract at the start
  - found three lifecycle defects: no recurring product-collection scheduler,
    no global recovery after an interrupted/pre-policy promotion or Review
    step, and an aggregate/Public allowlist that omitted credit cards despite
    D-034 already defining their publication contract
  - added migration `0035` and one advisory-lock-elected API scheduler leader
    for weekly six-scope active-catalog collection, 24-hour failed/partial
    retry, 12-hour abandoned-run closure, orphan auto-promotion, ten-task
    current-v7 Review recovery, and pending aggregate restart
  - preserved scheduler actor/trigger lineage and the existing 100% essential
    official-evidence, canonical, audit, and country projection gates; failed
    AI attempts can retry, while incomplete, ambiguous, and non-product rows
    stay private
  - enabled credit cards in aggregate loading and anonymous Public APIs; added
    `/cards`, annual-fee sorting, purchase-rate list/compare/detail facts,
    navigation, and EN/KO/JA copy
  - applied migration `0035` to shared dev, recovered six abandoned runs,
    promoted the orphan eligible candidate, processed bounded legacy Review
    batches, and refreshed Public snapshots
  - final essential audit is exact: active canonical `177 = 66 complete + 111
    incomplete`; Public `66 = 66 complete + 0 incomplete`, with no affected
    complete scope. Public grew from `58` to `66`: CA `55` (`16` chequing, `7`
    credit card, `8` GIC, `3` line of credit, `4` mortgage, `17` savings) and US
    `11` (`5` chequing, `1` mortgage, `5` personal loan)
  - launched scheduled collection `collection_Z4Vbo8MwicqtqKgE` for six due US
    bank/Product Type scopes; the final checkpoint was `3 completed / 3
    started`, with the independent runner still progressing
- Not done: did not force-publish the 111 incomplete canonical rows or legacy
  candidates whose identity, required financial fact, exact official evidence,
  or cross-field consistency is unresolved. No publication gate was weakened.
- Key files: `db/migrations/0035_collection_publication_automation.sql`,
  `api/service/api_service/collection_automation.py`,
  `api/service/api_service/main.py`, aggregate/Public API modules,
  `worker/pipeline/fpds_aggregate_refresh/*`, `app/public/src/app/cards/`,
  shared Public catalog components, and this journal
- Decisions: recorded D-042; kept normal collection weekly, failed/partial
  retry at 24 hours, recovery work at ten candidates per 15-minute poll, and
  cards on the already-approved annual-fee plus purchase-rate contract
- Verification:
  - API: `.venv\Scripts\python.exe -B -m unittest discover -s tests -p
    "test_*.py"` (`383` tests)
  - worker: `uv run python -B -m unittest discover -s worker -p "test_*.py"`
    (`463` tests)
  - Public: `pnpm run typecheck`; `pnpm run build` (includes `/cards`)
  - live `/cards`: HTTP `200`, `7 products`, annual-fee and purchase-rate copy
  - exact mobile emulation: `innerWidth=390`, `clientWidth=390`, document and
    body `scrollWidth=390`; current title and seven-product snapshot rendered
  - shared-dev `essential-audit --brief`: canonical `66/177` complete, Public
    `66/66` complete, zero incomplete Public rows
  - `git diff --check`
- Known issues: the 50 legacy active US card rows are incomplete under the
  current profile and correctly remain non-public; fresh scheduled recollection
  and bounded Review recovery continue automatically rather than bulk-approving
  them from stale data.
- Next step: no routine Product Owner action is required. Keep the API runtime
  deployed so the elected scheduler can finish the active US collection and
  continue weekly collection/recovery; use Admin Review only for candidates
  that remain genuinely ambiguous after automatic verification.

## 2026-08-09 - Country-Specific Collection And Publication Profiles

- WBS: `5.24`, country-product collection/publication profiles, existing US
  Public remediation
- Status: complete in implementation, shared-dev migration/recollection,
  aggregate refresh, Public readback, and regression verification
- Goal: make Banks collection reach Public automatically when the smaller set
  of country/product-specific comparison essentials has exact official
  evidence, while routing only missing, contradictory, or unsafe essentials to
  Review.
- Outcome:
  - introduced the versioned declarative `(country_code, product_type)` market
    profile registry, preserved Canada behavior, added explicit US Checking,
    Savings, CD, Mortgage, Personal Loan, Credit Card, and Line of Credit
    profiles, and made future explicit countries fail closed until registered
  - carried the profile through collection, validation, grounding, Review,
    approval, aggregate eligibility, and essential-only Public projection;
    added US CD early-withdrawal-penalty support
  - added country-route isolation, exact-product supporting bundles,
    non-product and masked-value rejection, US pricing-assumption completeness,
    and canonical identity continuity across trademark/punctuation and a
    trailing generic `account`
  - bounded automatic supporting sources to selected-product companions,
    compatible rate/APR pages, and relevant essential-fact disclosures/FAQs;
    live TD runs used six sources instead of the earlier broad same-bank plans,
    while unrelated Checking/application evidence no longer supplied Savings
    facts
  - upgraded Review AI to `review-ai-verification-v7` and collection grounding
    to `collection-official-grounding-v2`: ellipsized/composite quotes,
    Product-Type-conflicting routes, numeric values absent from the quote, and
    decision-critical prose extending beyond the exact quote are rejected
  - applied shared-dev migration `0034` and retracted confirmed unsafe US
    Public rows with append-only remediation/audit history, including false or
    incomplete rates/conditions, cross-country contamination, invalid product
    taxonomy, scenario-truncated lending facts, and duplicate product variants
  - terminal collection `collection_BOxLexnlgTi2sNhQ` finished `7/7` with no
    partial/failure: `21` candidates, `20` private Review, `1` rejected, and
    `0` active promoted product. The rejected Truist approval appended an
    unsupported graduation-date expiry to a genuine student-waiver quote.
  - proof collection `collection_2VG5tbk2eNbTvjR7` finished `5/5` with `35/35`
    source successes, no partial/failure, `11` candidates, all `11` private in
    Review, and `0` promoted products. No unsafe approval required remediation;
    TD Savings remained Review-bound and the former false `0.02%` correction
    from a Checking application route did not recur
  - the final US cross-country source audit found `0` active route conflicts
  - audited manual refresh request `aggreq_W82b0caQSGoB1FsY` completed as fresh
    US snapshot `agg_ejocbYJer7SZD04R` with `11` active products and `31`
    incomplete canonical rows excluded. Latest Public is `58/58`
    essential-complete: US `11` and CA `47`, with `0` `Unavailable` values,
    `0` duplicate groups, and `0` numeric type violations
  - final US Public products are Capital One `MONEY Teen Checking Account with
    Debit Card`; Citi `Citi Personal Loans`; TD `TD Beyond Checking: Premium
    Banking`; Truist `Auto Refinance Loan Options & Competitive Rates`,
    `Marine & Yacht Loans`, `New car loans`, and `Used Car Loans`; U.S. Bank
    `Bank Smartly Checking for teens`, `Young adult & student checking`, and
    `U.S. Bank Access Home Loan`; and Wells Fargo `Prime Checking`
- Key files: `worker/pipeline/fpds_market_profile.py`,
  `worker/pipeline/fpds_extraction/service.py`,
  `worker/pipeline/fpds_validation_routing/service.py`,
  `api/service/api_service/source_catalog.py`,
  `api/service/api_service/ai_verification.py`,
  `api/service/api_service/review_ai_correction.py`,
  `api/service/api_service/public_products.py`, migrations `0032`-`0034`,
  Public comparison/detail surfaces, active requirements/design/decision docs,
  and `tmp/fpds_admin_collection_goal_tool.py`
- Decisions: keep the `100%` essential-field and official-evidence gate; reduce
  fields and source scope rather than weakening truth requirements. Country
  differences belong in versioned profiles, not scattered conditionals.
  Incomplete candidates remain private; no operator approval is fabricated.
- Verification: focused exact-quote/Review suites `81` API tests and `342`
  worker tests; full API `378/378`; full worker `462/462`; Public typecheck and
  production build; shared-dev collection, source-isolation, aggregate,
  essential-contract, Public API, duplicate, numeric-type, and audit-event
  readbacks; helper `py_compile`; and `git diff --check`.
- Known issues: genuinely incomplete US candidates remain private in Review;
  no incomplete active Public projection is known.
- Next step: continue ordinary source-quality operations from the evidence-first
  Review queue; do not weaken the country profile or exact-evidence gates to
  increase Public catalog size.

## 2026-08-09 - Existing Public Catalog Recollection And Quality Repair

- WBS: `5.15`, `5.16`, existing-data remediation, audited Banks recollection,
  Public aggregate repair
- Status: complete in shared-dev operations, runtime safety, regression tests,
  and Public readback
- Goal: repair the already-published weak catalog without requiring the Product
  Owner to review every product, while retaining only evidence-grounded
  comparison essentials in Public.
- Starting state:
  - latest CA/US Public snapshots contained `86` active products; only `35`
    satisfied the new essential contract and `51` were incomplete
  - active governed canonical data contained `102` products; `67` were
    incomplete
- Operational outcome:
  - generated immediate safety snapshots that removed all `51` incomplete
    Public rows before recollection
  - retracted the unsupported Capital One Kids Savings `10%` candidate and a
    WealthONE GIC candidate whose product identity was actually a High Interest
    Savings Account; their products were inactivated with append-only
    remediation audit events rather than deleting source evidence or history
  - ran audited Banks collection `collection_gfmLJxN54Uo2H43M` across `32`
    affected bank/product scopes: all `32` runs completed with no partial or
    failed run; `78` candidates resulted in `27` approved, `50` in Review, and
    `1` superseded candidate
  - the `27` approved candidates included `21` contract-pass candidates and
    `6` older AI-verification approvals that still lacked a new essential; the
    aggregate contract correctly kept those six outside Public
  - ran targeted semantic recollection
    `collection_4sMFw9d8XWPA-fP8` for Capital One savings and WealthONE GIC;
    the collection completed `2/2` runs and produced four candidates. Capital
    One `360 Performance Savings` initially auto-promoted, while Kids Savings,
    a duplicate feature page, and the unresolved WealthONE GIC stayed in Review
  - direct official-page verification showed the Capital One APY rendered as
    unavailable in captured HTML and the extracted `10` came from unrelated
    `top 10%` mobile-app copy. The promoted candidate was therefore retracted
    and its canonical product inactivated
  - final snapshots are `agg_repair_final_20260809_ca` and
    `agg_repair_verified_20260809_us`; the Public API now returns `47` CA plus
    `1` US product, all `48/48` essential-complete, with zero `Unavailable`
    values and zero numeric type violations. The remaining `64` incomplete
    active canonical rows stay outside Public
- Runtime hardening:
  - annual Deposit rates at or above `10%` now require review instead of being
    treated as a plausible context-free canonical rate; semantic non-rate
    contexts still receive their more specific suppression reason
  - candidate safety remediation now queues aggregate refresh separately for
    every affected product country instead of silently defaulting US
    retractions to CA
  - the tracked admin collection helper now provides essential/Public audits,
    collection outcome summaries, long-run activity diagnosis, and Public API
    readback used for this repair
- Review state: `53` newly collected unresolved candidates remain in Review
  because an essential field could not be grounded; they are not visible in
  Public. No operator approval was fabricated to increase catalog size.
- Verification: API `365/365`; worker `439/439`; Public typecheck and production
  build remained passed from the essential-field slice; live Public API
  readback confirmed CA `47`, US `1`, fresh snapshots, and `0` unavailable
  values; final essential audit confirmed Public `48/48` complete and `0`
  incomplete; duplicate and numeric-type audit found `0` violations.
- Known limitation: the official Capital One page renders its APY dynamically
  as `NaN` to the server-side capture, so that savings product correctly remains
  unavailable to Public until direct current APY evidence can be collected.
- Next step: work Review only for the `53` candidates whose missing essential
  can be resolved from an official source; ordinary complete Banks collections
  require no operator action.

## 2026-08-08 - Essential-Field Low-Touch Publication

- WBS: `5.15`, `5.16`, collection automation, Review routing, Public product
  quality
- Status: complete in code, tests, active documentation, and shared-dev policy
  migration
- Goal: let a Banks collection reach FPDS Public without operator intervention
  whenever the official source supports the minimum facts customers need to
  compare that product type, and send only unresolved essentials to Review.
- Why now: months of runs showed that broad collection contracts created many
  empty or strange Public fields and unnecessary Review work without improving
  the few facts customers actually compare.
- Outcome:
  - introduced one executable essential contract shared by source generation,
    validation, collection/Review AI, automatic and manual approval, aggregate
    projection, Public API, and Public UI
  - Chequing now requires fee, minimum balance, and included/unlimited
    transactions; Savings requires ongoing rate, fee, and minimum balance; GIC
    requires rate, term, minimum deposit, and redeemability; Mortgage requires
    rate/qualified summary, rate type, and term; Personal Loan requires rate/APR
    summary, amount, and term; Line of Credit requires rate/formula summary,
    limit, and security. Credit Card retains annual fee and purchase rate while
    remaining outside current Public scope
  - optional marketing/operational fields are no longer requested by default or
    included in Review AI. Identity and every selected essential require direct
    evidence and full official grounding; partial-source and legacy confidence
    warnings alone no longer block a complete candidate
  - aggregate refresh excludes incomplete active canonical rows for both
    Deposit and Lending, derives Deposit display rates from standard/base/highest
    rates or GIC schedules, and carries transaction, redeemability, and security
    facts into the Public projection
  - Public cards, comparison, and detail surfaces now use product-type-specific
    essentials and no longer add optional application/entry rows or irrelevant
    loan rate-type/term placeholders
  - migration `0033_essential_field_low_touch_publication.sql` updated seven
    Product Type contracts, `1,106` active source rows, the two AI thresholds to
    `1.0`, and force-review policy to remove partial-source/confidence-only work
- Not done: no existing candidate, canonical, Review, or Public projection data
  was manually repaired, deleted, or recollected. Existing records improve when
  the new runtime is deployed and the relevant collection/aggregate refresh runs.
- Key files: `worker/pipeline/fpds_approval_policy.py`,
  `worker/pipeline/fpds_validation_routing/service.py`,
  `api/service/api_service/candidate_auto_promotion.py`,
  `api/service/api_service/ai_verification.py`,
  `worker/pipeline/fpds_aggregate_refresh/service.py`,
  `app/public/src/components/fpds/public/product-compare-workspace.tsx`,
  `app/public/src/components/fpds/public/product-detail-surface.tsx`, migration
  `0033`, requirements, field contract, workflow, and decision D-034
- Decisions: D-034 supersedes the broad populated-field and 80% current
  contracts for governed types. The smaller field set must pass at 100%; zero
  money values and explicit boolean states are valid only with evidence.
- Verification: Worker `438/438`; API `365/365`; Public `pnpm run typecheck`;
  Public production build with eight routes; shared-dev readback confirmed
  migrations `0032` and `0033`, the seven narrowed registry contracts, v4
  `1.0` AI policy rows, and force-review v2; `git diff --check` passed.
- Known issues: official banks may still omit a true essential or split it
  across unsupported source patterns; those products correctly remain in
  Review. Existing Public data is not retroactively recollected by this slice.
- Next step: deploy the runtime, then trigger representative Deposit and Loan
  Banks collections and inspect automatic canonical/aggregate outcomes before
  deciding whether a separately authorized legacy-data cleanup is needed.

## 2026-08-08 - Cross-Country Comparison-Grade Product Collection

- WBS: `5.15`, `5.16`, collection quality, review automation, Public aggregate
  safety
- Status: done in code, shared-dev migration, documentation, and representative
  live recollection
- Goal: explain and fix why US loan products could be approved without rate,
  amount, or term facts, then make the same quality boundary reusable across
  countries and operator-managed Product Types.
- Why now: live Chase Mortgage and Citi Personal Loan candidates had official
  rate disclosures in their evidence, but the populated-only approval policy
  scored only fields that happened to be present. A product with an empty rate
  could therefore receive a `100%` grounding ratio and become canonical.
- Outcome:
  - added a country-neutral comparison contract: credit card requires annual
    fee + purchase rate; mortgage requires a numeric rate or percentage-bearing
    qualified summary + rate type + term; personal loan requires a rate/APR
    summary + amount + term; line of credit requires a rate/formula summary +
    limit; unknown dynamic types fail closed without a percentage field and a
    second decision field
  - missing mandatory fields now enter validation and Review AI v4 assessment,
    block automatic and human approval independently of the `80%` score, and
    cannot be hidden as empty optional omissions
  - extraction actively requests official rate/pricing/disclosure facts,
    preserves rate ranges/formulas/examples with their conditions, carries
    exact-product officially grounded lending rate summaries from supporting
    sources, and may reuse a fresh high-confidence official detail snapshot
    only for co-located qualified lending comparison facts
  - Public serialization and lending cards/details/comparison now expose
    `interest_rate_summary`; aggregate refresh excludes incomplete active
    lending canonical rows and records the exclusion count
  - migration `0032_comparison_grade_collection_quality.sql` was applied to
    shared dev, updating lending registry contracts and activating v3
    comparison policy rows while retaining the four bounded retail lending
    types because type count was not the failure cause
- Live verification:
  - Chase collection `collection_C9cfG4mm6S1goKwj` completed with 14/14 source
    successes. Five incomplete mortgage candidates received
    `required_field_missing` and stayed in Review. `FHA Loan` alone passed with
    fixed-rate, 30-year, and a qualified representative disclosure preserving
    `5.75% / 6.5756% APR`, down payment, loan amount, payment, geography, lock,
    LTV, and FICO assumptions
  - first Citi control collection `collection_v4PelMBPUVv9wLb4` produced an
    empty-core candidate that correctly failed with three missing comparison
    fields instead of false approval
  - after exact-origin recovery, Citi collection
    `collection_XgfA274n6TUxXnEi` completed with a validation-pass candidate
    containing `9.99% APR` with automatic-payment discount, `$2,000-$30,000`
    amount context, and an up-to-60-month term. Review AI retained it rather
    than auto-approving because the broader official search described a
    `9.99%-17.49%` APR and `12-60` month range that was not fully backed by the
    captured detail-page field quotes
  - latest US Public snapshot `agg_KswzrzB8aXlmkDVS` is completed and non-stale;
    it records `excluded_incomplete_comparison_rows=16`. The only projected
    Chase/Citi lending item in the audited scope is the comparison-complete FHA
    Loan with its qualified rate summary
- Not done: did not force-approve Citi, invent its missing upper APR/term bound,
  retract historical canonical rows, deactivate lending Product Types, or
  expose private evidence. One intermediate Citi retry
  `collection_B19cSuJ0t8s2ezMO` failed before candidate creation due a transient
  shared-dev database connection termination and remains preserved as run
  history.
- Key files: `worker/pipeline/fpds_approval_policy.py`,
  `worker/pipeline/fpds_extraction/service.py`,
  `worker/pipeline/fpds_normalization/supporting_merge.py`,
  `worker/pipeline/fpds_validation_routing/service.py`,
  `worker/pipeline/fpds_aggregate_refresh/service.py`,
  `api/service/api_service/ai_verification.py`,
  `api/service/api_service/candidate_auto_promotion.py`,
  `api/service/api_service/review_detail.py`,
  `api/service/api_service/public_products.py`, Public product surfaces,
  migration `0032`, requirements/design/decision/runbook documents, and focused
  regression tests
- Decisions: recorded D-033. Keep the four current lending types; reduce
  published facts, not supported types. A qualified advertised floor or
  representative example may be collected as labeled source-language text,
  but conflicting or incomplete official disclosures remain review-bound.
- Verification:
  - Worker affected suites: `338` tests passed
  - API affected suites: `89` tests passed
  - Public `pnpm run typecheck` passed
  - Public `pnpm run build` passed
  - shared-dev migration `0032` committed successfully
  - `git diff --check` passed
- Known issues: Citi's current detail snapshot publishes an advertised floor
  and maximum term, while Review AI found a broader range on other official
  pages without field-level persisted quotes. The candidate is intentionally
  retained in Review until those exact source facts are captured or an operator
  accepts only the narrower disclosure.
- Next step: when adding a new Product Type, define its percentage and second
  decision field up front; use the same live audit to confirm either a complete
  approved product or an explicit review-blocking source limitation.

## 2026-08-06 - JCBN Interrupted Collection Recovery And Rerun

- WBS: `5.15`, `5.16`, Admin collection operations
- Status: recovery complete; replacement collection running
- Goal: recover an orphaned JPMorgan Chase Bank collection and rerun the same
  six US Product Type scopes without losing run history.
- Why now: `collection_9QPRjT2ksDHtn9Lo` had one completed Chequing run and
  five runs left in `started` after its background runner terminated during
  Credit Card extraction.
- Outcome: the five nonterminal runs were closed with an explicit
  `background_runner_terminated` failure record, linked as `retried`, and
  preserved with their original run IDs. Replacement collection
  `collection_XbLwUNvRZiBfN1SC` was launched for the same JCBN `chequing`,
  `credit-card`, `gic`, `line-of-credit`, `mortgage`, and `savings` catalog
  items. Its background runner progressed the first Chequing scope through 15
  successful snapshot sources and into `parse_chunk` at handoff.
- Not done: did not approve or publish any candidate and did not change
  collection pipeline behavior. The replacement collection was still running
  at the end of this operational slice.
- Key files: `docs/00-governance/development-journal.md`, runtime collection
  plans/logs under `tmp/source-catalog-collections/`
- Decisions: reran all six originally selected scopes, including the previously
  completed Chequing scope, while linking only the five interrupted runs to
  their matching replacement run IDs.
- Verification:
  - original collection poll: terminal with `completed=1`, `retried=5`, and no
    `started` run
  - replacement collection poll: six new `started` run IDs under
    `collection_XbLwUNvRZiBfN1SC`
  - replacement log: source-catalog runner completed Chequing snapshot capture
    with `15/15` successful sources and launched `fpds_parse_chunk`
  - process inspection: replacement source-catalog runner remained alive after
    launch
- Known issues: a parent background-runner termination is not automatically
  reconciled on API/runtime restart, so a future recurrence can again leave
  persisted `started` rows until an operator recovery action is taken.
- Next step: monitor `collection_XbLwUNvRZiBfN1SC` to terminal state and inspect
  any failed or partial scope through Admin Runs.

## 2026-08-06 - Goldman Sachs Coverage Repair and Zero-Review Recollection

- WBS: `5.15`, `5.16`, low-touch source coverage, normalization, and automatic
  approval reliability
- Status: done in code, shared-dev data, documentation, migration, and running
  API process
- Goal: diagnose Goldman Sachs Bank USA runs that all ended Partial and make an
  ordinary Admin collection complete through audited automatic approval unless
  current official evidence is genuinely unavailable or ambiguous.
- RCA: the three catalog rows came from a July 31 v1 bank-onboarding execution
  with null coverage routes. The registered `goldmansachs.com` homepage is a
  corporate site, while current US consumer deposits are served by Marcus on
  `marcus.com`; the old same-domain-only policy made Savings/CD discovery
  structurally impossible. The onboarding result also retained legacy Personal
  Loan coverage even though official evidence says the portfolio was sold or
  wound down. The runner was a fresh subprocess and already loaded current disk
  code, so the API not being restarted did not cause the observed run failures.
- Coverage-flow outcome: migration `0031_catalog_coverage_route_evidence.sql`
  adds private relationship/current-offering evidence metadata. AI onboarding
  v3 and one-shot no-detail repair may now accept a product-specific official
  consumer-brand domain only with exact bank-relationship evidence. The same
  repair deactivates coverage and clean-closes a run only on explicit official
  sale/transfer/wind-down/discontinuation evidence; absence remains fail-closed.
  Corporate transaction-banking routes and narrative contamination from a
  rejected prior route are excluded, and Markdown heading citations are
  normalized before exact-quote validation.
- Extraction/routing outcome: a review candidate is superseded when an exact
  identity in the same run is already approved. Savings normalization now uses
  the run country's domestic currency for subtype, recognizes ongoing APY
  product headers separately from referral offers, omits an incremental rate
  boost when no total promotional APY is stated, and rejects comparison-
  calculator balances/assumptions as product terms.
- Controlled shared-dev results:
  - Personal Loan run
    `run_20260806_035200_gsbu_personal-loan_collect_5i4KWU1_` completed with
    `partial=false`, `product_not_currently_offered`, no candidate/review, and
    inactive catalog coverage backed by official retirement evidence.
  - CD run `run_20260806_035804_gsbu_gic_collect_f1ChdoZJ` completed with
    `partial=false`; `High-Yield Certificates of Deposit` passed validation and
    auto-approved with the official 6-month through 6-year rate table and `$500`
    minimum deposit. Its catalog route is the verified Marcus CD page.
  - Savings run `run_20260806_041005_gsbu_savings_collect_uHvIHQ21` completed
    with `partial=false`; `Online Savings Account` passed and auto-approved as
    US `standard`, `standard_rate=3.40`, `public_display_rate=3.40`, and
    `minimum_deposit=0`. The false `$2,500` calculator balance, calculator
    method, and uncombined referral boost are absent.
  - Goldman active Review Queue is `0`. Canonical state is one active Savings
    product and one active CD family; the earlier wrong `foreign_currency`
    Savings version is superseded rather than duplicated.
- Restart finding and action: the prior API/uvicorn process had been running
  since August 2, before this slice. This stale process did not explain the old
  runner failures, but it did require restart so future Admin launch plans carry
  `coverage_source_metadata`. Only the verified localhost port-4000 FPDS API
  process tree was restarted; the replacement listener returned `/healthz = ok`.
- Key files: source catalog/onboarding/collection runner services and tests,
  normalization service/tests, migration `0031`, API/Worker/DB runbooks,
  requirements, source/workflow/field/review design, decision D-031, and R-001.
- Verification:
  - migration `0031` applied to shared dev and catalog metadata queried
  - focused source catalog/runner/onboarding/collection modules: `180/180`
  - normalization module after Goldman safeguards: `148/148`
  - full API suite: `356/356`
  - full Worker suite: `416/416`
  - controlled DB reconciliation for run, candidate, review, catalog, canonical,
    and product-version state
- Known issues: provider search latency can make a single external-source run
  exceed the helper's first 240-second wait window even while the persisted run
  is healthy; the second bounded poll observed normal completion. Uncertain or
  inaccessible official evidence intentionally remains Partial/Review.
- Next step: monitor later bank expansions for new legal-bank/consumer-brand
  relationships and add evidence-bound regressions rather than broadening the
  allowed-domain set globally.

## 2026-08-05 - Citibank Review Queue v2 Remediation and Recollection

- WBS: `5.15`, `5.16`, low-touch collection and audited queue remediation
- Status: done
- Authorized operation: the Product Owner approved normal processing of the
  current Citibank Review Queue. The operation was restricted to US bank code
  `CN`; the 74 active non-Citibank reviews were unchanged.
- Policy rollout: migration `0030_collection_approval_field_policy.sql` applied
  successfully. V1 approval policy rows are inactive and both v2 `80%` policy
  rows are active.
- Existing queue remediation: batch `citibank-review-v2-20260805` processed all
  19 original tasks, applied six cited contract-safe corrections, approved two
  products, retained 17 below-threshold/hard-blocked tasks, and completed both
  aggregate requests. Exact batch reconciliation records 19 v2 assessments,
  two eligible decisions, and `$0.119946` estimated usage.
- Controlled recollection: collection `collection_xqNNmn5f82L6Eeu6` completed
  all five authorized scopes. Chequing safely produced no detail candidate;
  Credit Card captured `27/27` sources, reduced them to 18 candidates, and
  auto-validated 10; GIC produced one review; Personal Loan reduced 12 sources
  to two candidates with one auto-validation; Savings produced two reviews.
  The collection persisted 23 candidates and 12 review tasks in total. Two
  residual card reviews were approved by collection autopilot.
- Additional reusable fixes: Review AI may now accept an exact persisted
  official detail-page H1 as product identity only when discovery recorded an
  identity match, AI returned `unverified` rather than `mismatch`, and the page
  is not a checking/savings composite. Stale-review coalescing also accepts an
  exact normalized source URL only when the new run produced one review
  candidate for that URL. Dry-run projected four additional safe approvals;
  the live reassessment approved those same four and completed one US aggregate
  snapshot. Six older same-URL duplicates were auditably superseded without
  approving their proposals.
- Final state: Citibank active Review fell from 19 to 8. The remaining set is
  one combined chequing boundary, four cards without a separately verified
  material fact or exact identity evidence, one location/rate-dependent CD,
  and two savings candidates with unresolved rate or product-boundary facts.
  Citibank canonical state has 16 active credit cards and two active personal
  loans. Credit cards remain outside the approved Public projection scope;
  the approved personal loan is present in snapshot `agg_QU6E1uDNx_66wUkc`.
- Audit and verification:
  - migration history and active v2 policy rows verified
  - 19 original tasks received v2 assessments; no execution errors
  - four authoritative-identity approvals and six stale-review supersessions
    have normal review/audit lineage
  - all six aggregate requests created by the two explicit remediation approval
    passes completed; collection-time promotions used their normal refresh path
  - full API suite: `348/348`
  - focused identity, approval and supersession modules after the final safety
    change: `38/38`
- Next step: the remaining eight items need genuinely new official facts or a
  corrected single-product source. Re-running AI against unchanged evidence is
  intentionally not treated as progress.

## 2026-08-05 - Citibank Collection Auto-Approval Flow Repair

- WBS: `5.15`, `5.16`, collection quality and low-touch review automation
- Status: done in code and documentation; production/shared-dev rollout is
  intentionally pending Product Owner deployment and data-operation approval
- Goal: make normal operator-triggered collection reach audited automatic
  approval unless product identity/boundary or a material financial fact is
  genuinely unsafe.
- RCA: shared-dev has 19 active Citibank reviews. Seventeen include missing
  required fields, two deposit pages are true multi-product boundaries, and
  two personal-loan candidates have cross-field/evidence failures. Dynamic
  extraction expanded an 11-field credit-card contract to roughly 50 generic
  fields; lending H1/title terms were not eligible as authoritative product
  identities, so feature labels could reach official grounding first; and
  residual Review AI counted optional and operational fields in a typical
  15-field approval denominator.
- Outcome: added a shared decision-field policy, scoped dynamic
  extraction/grounding to the registered contract, made card/loan/mortgage
  discovery titles eligible as authoritative identity, omitted ungrounded
  lending attributes, and introduced Review AI v2 with an identity plus
  populated/blocking decision-field denominator and explicit hard blockers.
  Migration `0030_collection_approval_field_policy.sql` records the new policy;
  v1 Review AI executions are not reused after rollout.
- Key files: `worker/pipeline/fpds_approval_policy.py`, extraction,
  normalization and validation services, Review AI/autopilot services,
  regression tests, migration `0030`, and the aligned requirements, design,
  runbook, decision and risk records.
- Verification:
  - full Worker suite: `413/413`
  - full API suite: `346/346`
  - explicit API and Worker regressions: `11/11` and `2/2`
  - final focused normalization suite after grounding-order repair: `145/145`
  - final `git diff --check`: passed; generated fixture diffs were removed
  - read-only v2 field-set projection across all 19 Citibank reviews: card
    approval sets reduced from 15 fields to 2–6 without removing identity or
    populated material facts
- Known issues: the current 19 Citibank reviews still reflect the pre-v2
  contract because migration `0030`, deployment and recollection/remediation
  were not applied. True combined checking/savings pages, inaccessible CD
  rates/locations, and absent official product identity remain legitimate
  human-review cases.
- Data safety: diagnosis and the v2 projection were read-only. No shared-dev
  review, canonical, aggregate or Public state was mutated.
- Next step: after deployment approval, apply migration `0030`, deploy Worker
  and API together, then run a controlled Citibank recollection or an explicitly
  authorized v2 remediation of the existing queue.

## 2026-08-04 - Retried Partial Run Evidence-Scoring Fix

- WBS: `5.15`, `5.16`, cross-bank collection reliability hardening
- Status: done
- Goal: re-analyze the newly retried Partial runs after JSON route discovery
  was repaired, correct the remaining shared discovery defects, and preserve a
  genuine no-product Partial outcome.
- RCA: the retry proved JSON link recovery itself was working: Citi
  credit-card completed cleanly with `27/27` sources and `18` candidates, and
  Capital One savings completed `3/3` with one candidate. Six product routes
  were then rejected by shared page-evidence rules: Citi checking/savings/CD
  app shells were penalized by global navigation words, Citi mortgage had an
  official title/path but an unrendered body, Citi `PERSONAL LOANS` use-case
  sections were mistaken for distinct loan products, and Capital One's US
  `Auto Loan Refinancing` identity was present in localized discovery
  vocabulary but absent from canonical identity matching. Citi line-of-credit
  had no named official product among `32` scored links and is a genuine
  no-detail Partial rather than a code defect.
- Outcome: page evidence now recognizes bounded official route identity,
  limits weak negative words to prominent route/title/H1 context, merges
  country-local identity nouns, and distinguishes personal-loan use cases from
  distinct subtypes. High-confidence structured official product routes can
  survive an unrendered body without bypassing hard business/editorial/service
  vetoes. Deposit family fallback remains collection-capable but both
  validation and API promotion/autopilot force AI-identified hubs to Review.
  No-detail run summaries now prefer decisive rejection diagnostics over an
  incidental earlier `503` hub fetch.
- Read-only live verification: replaying the persisted AI roles/scores against
  the current official pages promoted all six previously false-negative URLs.
  Page scores changed from `1→4` for Citi savings/checking, `2→7` for Citi CD,
  `3→4` for Citi mortgage, and `0→6` for Capital One auto refinance; Citi
  personal-loan reached `10` without the false family marker.
- Not done: no shared-dev collection was launched and no historical run,
  source, candidate, review, canonical, aggregate, or Public state was mutated.
- Key files: `api_service/source_catalog.py`, the source-catalog runner,
  candidate promotion/review autopilot, worker validation routing, their tests,
  runtime READMEs, and the source-registry policy.
- Verification:
  - focused source-catalog/runner/promotion/autopilot modules: `162/162`
  - focused validation-routing module: `31/31`
  - full API suite: `342/342`
  - full worker suite: `409/409`
  - API regression suite: `11/11`
  - worker regression suite: `2/2`
  - current official-page plus persisted-AI promotion matrix: `6/6`
- Known issues: Citi line-of-credit should remain Partial until an official
  named consumer line-of-credit product or an approved coverage URL exists.
  Family fallback candidates are deliberately Review-bound rather than
  silently published.
- Next step: after the updated API/runner code is active, retry only the six
  fixable Partial scopes through the normal Admin path; do not retry the Citi
  line-of-credit scope merely to force a green run.

## 2026-08-04 - Dynamic Homepage JSON Discovery Partial-Run Fix

- WBS: `5.15`, `5.16`, cross-bank collection reliability hardening
- Status: done
- Goal: diagnose the latest Admin product-collection runs that completed
  Partial and prevent the same discovery failure across other banks and
  Product Types.
- RCA: all seven Citibank US runs in
  `collection_3vEVaRVKq1F58QBx` completed with zero source scope and
  `no_detail_sources_discovered`. The direct homepage fetch was successful and
  returned `232,663` characters, but Citi exposes its product routes inside an
  `application/ld+json` graph and an `application/json` SSR-state payload
  rather than ordinary anchors or `data-*` JSON. The shared discovery parser
  therefore returned zero links even though the payload contained checking,
  savings, CD, credit-card, mortgage, and personal-loan routes. All seven
  catalog rows also had null coverage URLs and no preserved generated detail
  source, so the runner had no fallback scope.
- Outcome: shared HTML discovery now reads recognized `href`, `url`, and
  `targetUrl` values plus bounded product copy from non-executable JSON/JSON-LD
  scripts. Payload size, script count, node count, template rejection, and
  total link/text limits remain enforced. Recovered URLs still pass the same
  HTTPS/official-domain, scope-exclusion, product-role, page-evidence, review,
  and publication gates. The repaired parser recovered `22` allowed links and
  `12` product-related links from the current Citi response. Cross-bank tests
  cover both savings and mortgage; executable scripts and unresolved template
  URLs remain ignored, while genuine no-detail collection results still remain
  Partial.
- Not done: the seven historical Partial run rows were not mutated or retried;
  no candidate, review, canonical product, aggregate, or Public state changed.
- Key files: `worker/discovery/fpds_discovery/discovery.py`, worker discovery
  tests, API source-catalog tests, worker/API READMEs, root README, and the
  source-registry operating policy.
- Verification:
  - focused JSON component/script and cross-bank source-generation tests: `5/5`
  - worker discovery suite: `50/50`
  - worker pipeline suite: `358/358`
  - worker regression suite: `2/2`
  - API suite: `335/335`
  - API regression suite: `11/11`
  - current Citi read-only reproduction: `22` allowed links, including
    checking, savings, CD, credit-card, mortgage, and personal-loan routes
- Known issues: an active catalog row for a Product Type the bank does not
  actually offer may still correctly end as no-detail Partial; the fix does not
  invent a product or treat a family/service page as a named lending product.
- Next step: retry the affected Citi Partial runs through the normal Admin retry
  path when the Product Owner wants shared-dev run/candidate state refreshed.

## 2026-08-02 - Review Detail AI Verification Country-Query Fix

- WBS: `4.11`, Review Detail reliability
- Status: done
- Goal: diagnose and fix the `500 Internal Server Error` returned by Review
  Detail `Verify with AI`.
- RCA: `load_registered_bank_domains` used the optional country placeholder in
  `%(country_code)s IS NULL` without a PostgreSQL type. Psycopg sent it as an
  untyped prepared parameter, so PostgreSQL raised `AmbiguousParameter` before
  the model execution row or OpenAI request could start. The supplied traceback
  for `review-0c21d130b42857a0` and rollback-only runtime reproduction matched
  the same line and exception.
- Outcome: both bank-homepage and active-source country predicates now cast the
  placeholder to `text`. The regression asserts all four placeholder uses stay
  typed. A real-DB diagnostic with a local model stub passed for the affected
  review and five newly queued US reviews; every transaction was rolled back.
- Not done: no live provider retry, candidate correction, review decision, or
  canonical/Public mutation was performed.
- Key files: `api_service/ai_verification.py`, its focused tests, and the API
  runtime README.
- Verification: API full suite `334/334`, API regression `11/11`, focused
  AI/review tests `39/39`, real-DB stub reproduction `6/6` with rollback, and
  restarted dev API `/healthz` returned `ok` on port `4000`.
- Known issues: the failed HTTP request predates model-execution persistence,
  so it correctly has no AI execution or usage record.
- Next step: retry `Verify with AI` from the existing Review Detail session;
  normal provider latency and the existing `110s` Admin proxy timeout still
  apply.

## 2026-08-02 - BOAN Mortgage Run RCA and Failure Diagnostics

- WBS: `5.15`, `5.16`, collection reliability hardening
- Status: done
- Goal: explain why
  `run_20260731_041753_boan_mortgage_collect_7lD8qbPY` failed and prevent the
  same worker/schema mismatch from recurring opaquely in other runs.
- RCA: the run selected `30` BOAN mortgage sources but `fpds_snapshot` exited
  before writing any `run_source_item`. Migration `0025` had already made
  `ingestion_run.country_code` non-null, while the then-running snapshot and
  downstream worker upserts still omitted that column. The source-catalog
  wrapper retained only `fpds_snapshot failed with exit code 1`, which hid the
  database constraint detail.
- Existing prevention verified: snapshot, parse/chunk, extraction,
  normalization, and validation now require one valid country and include it
  in every ingestion-run insert/update. The focused cross-stage regression
  passes for `US`; later BOAN mortgage runs completed, including the clean
  `17/17` run `run_20260731_061006_boan_mortgage_collect_8Uig924q`.
- Additional outcome: non-zero worker exits and unrecoverable timeouts now
  raise a structured stage error. Direct and source-catalog runners persist
  `failed_stage`, failure kind, return code or timeout, and a bounded worker
  diagnostic. Credential URLs and common secret assignments are redacted from
  both console output and stored metadata.
- Not done: the historical failed run was not retried or mutated; later BOAN
  runs already provide recovery evidence, and no candidate or canonical data
  changed in this slice.
- Key files: source collection runners, focused API tests, API runtime README,
  and source-registry operating policy.
- Verification: API full suite `334/334`, API regression `11/11`, worker full
  suite `406/406`, focused single-country contract tests `2/2`, and
  `git diff --check`.
- Known issues: the historical row cannot recover the original stderr because
  the old runner never persisted it; the RCA is corroborated by DB timing,
  zero source items, migration state, code history, the earlier hardening
  record, and successful later reruns.
- Next step: no Product Owner action is required unless the historical run
  should be explicitly retried for audit continuity.

## 2026-08-01 - Low-Touch Collection AI Autopilot

- WBS: `3.5`, `3.7`, `4.3`, `4.11`, `5.15`, `5.16`
- Status: done
- Goal: increase AI judgment in Admin product collection and leave as little
  safe post-collection work as possible for operators.
- Outcome: dynamic and lending candidates are no longer unconditionally forced
  into Review. Validation now persists a collection AI assessment over product
  identity, known decision-priority fields, and populated typed contract
  fields. Verified identity, at least two verified fields, the configured
  `80%` assessed-field ratio, normal confidence, clean validation, and every
  force-review guard are all required before normal auto-promotion.
- Residual Review automation: after normal promotion, the collection runner
  AI-verifies a policy-bounded set of active detail reviews, applies only cited
  contract-safe mismatches, scores every requested field, and system-approves
  only `>=80%` results with verified identity, an official source, and no
  unapplied correction. Completed attempts are reused after restart; provider
  failure, sub-threshold results, and ambiguous/non-product boundaries remain
  in Review without failing the collection run.
- Accuracy and isolation: lending percentage values now have a bounded `<100%`
  AI/review/validation contract, and Review AI official-domain lookup is
  constrained by both bank and candidate country.
- Policy/docs: migration `0029_collection_ai_autopilot_policy.sql` records the
  enabled default, `80%` grounding and full-field thresholds, and `200`-candidate
  per-run cap. Requirements, WBS, decision/RAID, workflow, field contract,
  review/audit, API, source policy, demo, DB, and runtime docs now replace the
  old blanket manual-review rule. Decision `D-028` records the new baseline.
- Not done: migration `0029` was not applied to shared dev, no live provider
  call or Admin collection was launched, and existing DB candidates were not
  mutated in this implementation slice.
- Key files: worker extraction/normalization/validation services,
  `api_service/collection_ai_autopilot.py`, Review AI correction/decision and
  source collection runner services, migration `0029`, tests, and active
  requirements/design/runtime/governance docs.
- Verification:
  - worker pipeline full suite: `358/358`
  - API full suite: `331/331`
  - worker regression: `2/2`
  - API regression: `11/11`
  - focused official-grounding, validation, auto-promotion, Review AI,
    collection-runner, and review-contract tests
  - `git diff --check`
- Known issues: live latency, usage cost, and bank-by-bank pass-rate impact need
  a targeted Admin recollection after migration `0029`; lower-confidence or
  officially incomplete products intentionally remain operator work.
- Next step: apply `0029` in the intended environment, run one representative
  weak lending/deposit collection, and compare autopilot approvals, retained
  Review reasons, Usage, and Public aggregate output before widening the live
  run scope.

## 2026-08-01 - Existing Review Queue AI Correction and 80% Approval

- WBS: `4.3`, `4.11`, Review/canonical data-quality remediation
- Status: done
- Goal: AI-verify every active existing Review Queue candidate, correct cited
  contract-safe mismatches, auto-approve products with at least 80% verified
  field coverage, and leave lower scores for operator approval.
- Scope before mutation: shared dev contained `94` active queued tasks (`CA 75`,
  `US 19`), no completed Review AI attempts for those tasks, `143` canonical
  products, and `14,801` Public projection rows.
- Outcome: all `94/94` candidates completed official-domain AI verification
  with no provider failure. `73` candidates received one or more safe field
  corrections. The score used every requested field as its denominator;
  official matches and applied safe mismatches passed, while omitted and
  unverified fields failed. Verified product identity, official sources, and no
  remaining correction were mandatory. Two candidates scored `87.5%` and were
  auto-approved; `92` candidates remain in Review.
- Approved products: `CIBC Aeroplan Visa Card for Students` and `Scotiabank
  American Express Card (for students)` entered canonical through the existing
  review decision path. Both country aggregate refresh requests completed.
- Final shared-dev state: `94` verification audits, `73` correction audits,
  `94` persisted threshold assessments, `2` system approvals, `145` canonical
  products, `92` active review tasks (`CA 73`, `US 19`), and `14,941` Public
  projection rows.
- Key files: `api_service/ai_verification.py`,
  `api_service/review_ai_correction.py`, `api_service/review_detail.py`, the
  resumable `tmp/fpds_review_ai_backfill.py` operator tool, API tests, runtime
  docs, requirements, API/state contracts, decision log, and RAID.
- Decisions: recorded `D-027`. Interactive Verify with AI remains advisory;
  only an explicitly authorized remediation batch may apply corrections and
  threshold approval. Exact `80%` passes; partial model response cannot shrink
  the denominator.
- Verification: focused AI verification/correction/review tests passed before
  execution; the final API suite passed `325/325` and API regression passed
  `11/11`. Post-run DB reconciliation confirmed all counts, both completed
  aggregate refresh requests, and the final canonical/Review/Public boundary.
- Usage: `94` usage records captured `2,090,387` prompt tokens and `284,209`
  completion tokens with an estimated total cost of `$0.968161`.
- Known issues: `92` lower-scoring candidates still require operator review;
  many are family, service, calculator, or incomplete product pages and should
  not be approved solely because some fields were corrected.
- Next step: review the remaining Queue in descending AI pass rate, starting
  with candidates just below 80%, and reject clear non-product identities.

## 2026-08-01 - Collection Official-Domain AI Grounding

- WBS: `3.5`, `5.15`, `5.16` collection-quality hardening
- Status: done
- Goal: explain and close the quality gap between normal Admin product
  collection and Review Detail `Verify with AI` without weakening evidence,
  review, approval, or publication boundaries.
- Why now: executable-path comparison showed that Review verification forced a
  current official-domain web search over a named product and all review fields,
  then sanitized citations and field-contract values. Standard Product Type
  collection instead remained heuristic-only; AI extraction/normalization was
  limited to dynamic Product Types and used stored chunks without live search.
- Outcome: every configured candidate-producing `detail` source now receives
  one required official-domain web grounding pass. The request includes exact
  product context, collected values, the complete resolved Product Type field
  contract, and up to 24 prioritized fresh evidence chunks. A match or
  correction is retained only when its URL is both allowlisted and present in
  provider consulted-source metadata, its exact quote exists in the selected
  chunk, and its JSON value passes canonical type and numeric safe-range
  validation aligned with review edits. The resulting
  evidence chunk link, official sources, quote, rationale, model execution, and
  usage remain traceable through extraction/normalization metadata.
- Fail-safe behavior: supporting and entry sources remain evidence-only. An
  unconfigured, failed, off-domain, unconsulted, unquoted, malformed, ambiguous,
  or unverified AI result leaves deterministic extraction or omission intact
  and continues through existing validation and review routing.
- Not done: no shared-dev collection, provider call, candidate mutation,
  canonical approval, or Public publication was run in this slice. Existing
  collected candidates are unchanged until an operator starts a new collection
  or retry.
- Key files: `worker/pipeline/fpds_extraction/service.py`, extraction registry
  context, normalization trace metadata, source collection runner, focused API
  and worker tests, requirements, runtime/design docs, decision log, and RAID.
- Decisions: recorded `D-026`; one AI request is bounded to each
  candidate-producing detail source, while deterministic extraction remains the
  provider-independent fallback and the human/canonical gates stay unchanged.
- Verification:
  - Worker pipeline full suite: `357` tests
  - API full suite: `317` tests
  - Worker regression suite: `2` tests
  - API regression suite: `11` tests
  - focused extraction/normalization/AI-runtime/source-runner tests passed
- Known issues: a real OpenAI/web collection was not launched, so live bank
  response quality, latency, and cost still require the next targeted Admin
  recollection check. Usage is persisted under
  `openai-official-product-grounding` for that review.
- Next step: run a targeted recollection for one previously weak product,
  compare its collected candidate to `Verify with AI`, and inspect Usage before
  deciding whether to widen the live rerun scope.

## 2026-07-30 - US Product Collection Failure Hardening

- WBS: `5.15`, `5.16`, `5.23`
- Status: done
- Goal: diagnose the all-failed US Admin product collection and fix the common
  pipeline classes so the next US bank/site does not need a one-off bypass.
- Why now: Bank of America collection exposed both a hard worker persistence
  failure and US/dynamic-site discovery gaps.
- Outcome: the hard failure was traced to migration `0025` making
  `ingestion_run.country_code` non-null while all five worker persistence
  stages still omitted it. Snapshot, parse/chunk, extraction, normalization,
  and validation now persist a validated single-country scope and reject
  invalid/mixed-country runs before DB work. Discovery also keeps canonical
  codes while using US `checking` and CD vocabulary, reads bounded links and
  product copy from JSON-valued `data-*` components, resolves relative links
  against the fetched URL, and preserves location-gated component copy in
  parser v3. Migration `0028` adds the verified coverage evidence URL to
  source-catalog rows so later collection starts from the page AI already
  cited instead of rediscovering it from the homepage.
- Follow-on hardening: the queued runner now forwards the verified coverage
  URL into materialization; exact coverage pages can safely survive a ZIP or
  county gate without relaxing ordinary candidate pages. Page-validation
  fetch failures and source-language conflicts cannot be reintroduced as
  supporting HTML. US currency defaults to USD, and legal documents, SEO
  actions, enrollment CTAs, calculators, and other non-product headings are
  excluded from product identity.
- Shared dev: Product Owner approval was received. Migration `0028` was
  applied, all five Bank of America coverage rows were backfilled with exact
  same-domain URLs through five
  `source_catalog_coverage_evidence_backfilled` audit events, and 46 generated
  sources were soft-inactivated for clean regeneration through one
  `generated_source_scope_reset` event. Request ID:
  `req-us-collection-repair-20260730`.
- Runtime evidence: `collection_kPrqgtYCIyAEXz9y` completed all five product
  types with no partial run, `30/30` sources successful, `12` review
  candidates, and USD on every candidate. After the final title-quality
  guard, `collection_wN63XHwPQbEPgnTP` produced
  `Bank of America Advantage Banking`, `Certificate of Deposit`, and
  `Bank of America Advantage Savings Account`, all in USD. CD and savings were
  full successes; checking isolated one official supporting-page HTTP 500
  after discovery and still completed with `13/14` sources and the correct
  candidate.
- Publication boundary: every new candidate remains review-routed; none was
  approved or published.
- Key files: worker run-scope and five persistence entry points, discovery
  link extraction, parse/chunk parser v3, source catalog and AI onboarding,
  `0028_source_catalog_coverage_evidence.sql`, API/worker regression tests,
  runtime READMEs, API contract, and source-registry policy.
- Decisions: coverage citations remain official-domain private operational
  evidence; local vocabulary never renames canonical Product Type codes;
  structured component parsing is bounded and remains subject to existing
  HTTPS, domain, role, evidence, review, and publication gates. A genuine
  post-discovery source outage is reported as an isolated partial-source
  failure rather than being hidden or escalating to an all-run failure.
- Verification:
  - API full suite: `317` tests
  - worker discovery full suite: `48` tests
  - worker pipeline full suite: `354` tests
  - focused US coverage/location/title/supporting-source regressions
  - shared-dev terminal, source-status, candidate-name/currency, migration,
    coverage, and audit queries
  - `git diff --check`
- Known issues: Bank of America currently withholds some required financial
  fields behind location-dependent interactions, so the corrected candidates
  remain in review with `required_field_missing`; this is a data-review state,
  not a collection-run failure. Diagnostic-run candidates were not approved
  or published.
- Next step: operator review of the corrected Bank of America candidates;
  publication remains outside this hardening slice.

## 2026-08-13 - Bounded Operational Storage and Dev Database Cleanup

- WBS: `5.27`
- Status: done
- Goal: stop unbounded operational/audit/evidence growth and reclaim clearly
  redundant shared-development data without changing Admin review quality,
  canonical truth, or the latest Public datasets.
- Outcome: migration `0040_bounded_operational_storage.sql` removes the
  physical `audit_event`, `llm_usage_record`, `evidence_chunk_embedding`, and
  three redundant dashboard snapshot tables. Empty discard-only compatibility
  views temporarily preserve the two legacy relation shapes while storing zero
  rows. Audit/Usage APIs and Admin routes are removed; Review/Run no longer show
  token/cost data. Public dashboard responses continue to derive from the
  latest successful `public_product_projection`.
- Retention: the scheduler now runs `fpds_apply_data_retention()` before each
  cycle. It protects field-linked/latest-source/active-run evidence, bounds
  unreferenced model diagnostics and aggregate work to 14 days, keeps two
  completed aggregate runs per country/scope, recovers runs abandoned for 12
  hours, bounds login/session residue, and compacts old run/source JSON to the
  fields used by Admin diagnosis and retry.
- Shared dev cleanup: after a transactional dry run and explicit `dev`
  environment/precondition checks, evidence chunks fell from `161,296` to
  `62,944`, model executions from `9,913` to `5,039`, Public projection rows
  from `19,978` to `576`, aggregate snapshots from `278` to `8`, and stale
  started runs from `4` to `0`. Scoped `VACUUM FULL/ANALYZE` reclaimed roughly
  `329 MB` including dropped relations. No synthetic bank, product, run, or
  candidate marker was present; two URL substring matches were legitimate
  CIBC/Manulife pages and were preserved.
- Quality reconciliation: orphan field-evidence links remain `0`; Audit and
  Usage compatibility views each contain `0` rows. Latest snapshot IDs and
  counts are unchanged: all-active CA `107`, all-active US `2`, phase1-public
  CA `140`, and phase1-public US `41`. Public CA/US catalog/dashboard reads and
  the Admin queue/review-detail reads returned normally after cleanup.
- Key files: migration `0040`, `api_service/data_retention.py`, collection
  automation, parse and aggregate persistence, Admin route/API cleanup,
  retention regression tests, `bounded-data-retention-policy.md`, requirements,
  WBS, decision log, database/runtime READMEs, and affected design contracts.
- Decisions: `D044` makes review decisions and canonical change events the
  durable business chronology. Generic request/read audit events, standalone
  token/cost usage, evidence embeddings, and dashboard materializations are not
  product truth and are not retained. Metadata-only evidence retrieval is the
  active path. Pre-`0040` writers using usage `ON CONFLICT` must be drained;
  current writers use discard-compatible inserts.
- Verification:
  - API full suite: `395` tests
  - worker full suite: `471` tests
  - Admin typecheck and production build passed; the generated route list has
    no Audit or Usage page
  - rollback DB compatibility-write smoke passed with `0` stored rows
  - migration/readback, relation-kind, row-count, orphan-link, latest-Public,
    Admin/Public functional reads, and scoped post-vacuum size checks passed
- Known issues: compatibility views remain temporarily because some retained
  Review/AI code still performs optional legacy joins or discard-only inserts;
  they consume no row storage and can be removed in a later coordinated schema
  cleanup after those compatibility references are retired.
- Next step: monitor the next scheduled collection cycle's retention summary
  and relation growth; do not widen deletion into canonical/review history or
  private object-storage lifecycle without a separate Product Owner decision.

## 2026-08-13 - Numeric Interest Rates on Public Product Cards

- WBS: `5.28`
- Status: done
- Goal: render one numeric, customer-favorable interest rate on Public catalog
  cards from the current approved projection while retaining complete qualified
  pricing text on comparison and product detail and avoiding recollection.
- Outcome: the Public products API now adds `card_display_rate`. Deposit rows
  keep their approved display-rate behavior; lending/card rows derive the
  lowest explicit absolute scalar, range endpoint, or introductory APR.
  `display_rate` sorting uses that same derivative. Catalog cards use only the
  numeric value or the existing unavailable state, while comparison and detail
  continue to use `interest_rate_summary` or
  `purchase_interest_rate_summary`.
- Safety: rate parsing excludes discounts, down payments, finance/origination
  fees, LTV/CLTV, caps, and unresolved Prime/SOFR/reference/index spreads. For
  Credit Cards, an explicit purchase-rate field/summary takes precedence over
  a generic display-rate value so reward percentages cannot appear as interest.
  No canonical row, evidence, Review state, or collection input was changed.
- Shared-dev readback: the requested Truist `5.15%-18.00% APR` products return
  `card_display_rate=5.15`; Citi's `9.99%` rate plus `0.5%` autopay discount
  returns `9.99`; US card APR ranges return their absolute lower endpoints and
  intro offers return `0`; the U.S. Bank representative mortgage returns
  `6.625`; CIBC Costco returns its `21.75` purchase rate rather than `3%`
  rewards; and the Manulife representative examples return `4.45`. The full
  stored summaries were unchanged in every readback.
- Key files: `api_service/public_products.py`, Public API type and catalog/detail
  components, Public product API regressions, requirements, API/field/UI
  contracts, Public README, WBS, and decision `D-045`.
- Verification:
  - focused Public products API suite: `11` tests
  - API full suite: `397` tests
  - Public typecheck and production build passed
  - read-only CA/US shared-dev Public API readback passed
  - final `git diff --check`
- Known issues: a reference-rate-only formula intentionally remains unavailable
  on the card until approved data contains an explicit resulting absolute rate.
- Next step: no data recollection is required; monitor future summary wording
  through the regression suite when new markets or rate formats are added.

## 2026-08-14 - BankingFacts Public Launch Polish and Review Recovery Guard

- WBS: `5.29`
- Status: done
- Goal: simplify the anonymous Public experience for launch, establish a clear
  customer brand and favicon, replace Home bank composition with Loan Top 5,
  route catalog-card users to the official bank page, and stop Review recovery
  from attempting approval after a correction creates a new conditional
  essential field.
- Outcome: customer-facing Public metadata, header, footer, EN/KO/JA copy, and
  the shared code-native mark now use `BankingFacts`. Home is reduced to a
  concise thesis, direct Deposit/Credit Card/Loan actions, current product/bank
  freshness, and up to five Loan products ordered by the lowest disclosed
  numeric rate. Products by bank, the provenance ledger, repeated coverage,
  decorative page gradients, and legacy ranking cards were removed.
- Catalog action: product names still open the internal detail route and Compare
  remains available. `Compare details` is replaced by `View at bank` (localized)
  only when the approved projection has `product_url`; the external link uses a
  new tab with `noopener noreferrer` and no URL fallback is invented.
- Recovery fix: after AI corrections and an otherwise eligible verification,
  collection automation reloads the current Review detail and applies the same
  market-profile comparison contract used by manual approval. If a positive US
  monthly fee now requires a missing `fee_waiver_condition`, the assessment is
  persisted as ineligible with the missing fields and the task remains in
  Review. The approval function is not called, so the scheduler no longer emits
  the reported unhandled `essential_fields_missing` traceback for this path.
- Safety: no canonical product, Review decision, collection run, aggregate
  snapshot, or shared-dev data was mutated. Existing anonymous, country-scoped,
  evidence-private, source-language, and non-recommendatory boundaries remain.
- Key files: Public layout/locale/shell/Home/catalog components and app icon,
  collection AI autopilot plus focused regression, Public README, requirements,
  IA/metric baseline, WBS, and decision `D-046`.
- Verification:
  - collection autopilot plus approval-policy focused suites: `24` tests
  - API full suite: `398` tests
  - Public typecheck passed
  - Public production build passed, including `/icon.svg`
  - EN/KO/JA static copy/metadata and official-link safety inspection passed
  - production-rendered Home passed at `1440px` EN, `768px` KO, and exact
    `390px` JA; Deposit `390px` KO and Loan `390px` EN also passed with no
    document overflow, correct localized title/lang/H1, no Products by bank or
    Compare details text, and safe official-bank links
- Known issues: `BankingFacts` is a `.com`-compatible label, but domain
  registration and trademark clearance are external launch decisions and were
  not performed by this code slice.
- Next step: confirm the chosen domain before DNS/production cutover and repeat
  the same smoke against the deployment candidate.

## 2026-08-14 - BankTable Identity and Dual Home Top 5

- WBS: `5.30`
- Status: done
- Goal: simplify the Public logo further, replace the customer-facing title,
  and balance Home with Deposit Top 5 on the left and Loan Top 5 on the right.
- Outcome: the customer-facing title is now `BankTable`. The shell and favicon
  share one flat 2-by-2 table mark with no check badge, second color, or shadow.
  EN/KO/JA metadata, comparison boundaries, and methodology copy use the new
  name while FPDS remains the internal platform/runtime identity.
- Home: Deposit and Loan now use independent product requests and equal desktop
  columns, stacking below `lg`. Deposit requests the approved Chequing,
  Savings, and GIC scope with `display_rate desc`; Loan requests Mortgage,
  Personal Loan, and Line of Credit with `display_rate asc`. Both cap at five,
  omit missing numeric rates, keep internal detail and safe official-bank
  links, and distinguish request failure from a genuinely empty eligible set.
- Copy and safety: Deposit explicitly means highest disclosed numeric rates and
  Loan lowest disclosed numeric rates. Localized caveats direct users to
  compare fees, terms, eligibility, and full conditions; no suitability score,
  application flow, canonical mutation, or public evidence exposure was added.
- Key files: Public Home route/surface, locale resources, layout metadata,
  code-native mark/favicon, Public README, requirements, Home IA/metric
  baseline, decision `D-047`, and WBS `5.30`.
- Verification:
  - Public typecheck passed
  - Public production build passed, including `/icon.svg`
  - production-rendered Home passed at `1440px` EN, `768px` KO, and exact
    `390px` JA with no document overflow, browser exception, or interactive
    target below 44px
  - all three widths rendered five Deposit rates in descending order
    (`5`, `5`, `5`, `5`, `4.65`) and five Loan rates in ascending order
    (`3.45`, `4.45`, `4.45`, `4.59`, `4.59`)
  - desktop rendered equal left/right columns; tablet/mobile rendered the
    intended stacked order; all ten official-bank links retained
    `noopener noreferrer`
  - `/icon.svg` returned `200 image/svg+xml` with the matching table geometry
- Known issues: `banktable.com` is currently offered as a premium aftermarket
  domain, not reserved by this code change. Purchase and formal trademark
  clearance remain Product Owner launch decisions.
- Next step: decide whether to acquire `banktable.com` before production DNS
  cutover, or select another customer name before external brand investment.

## 2026-08-14 - Home Top 5 Group and Action Refinement

- WBS: `5.31`
- Status: done
- Goal: distinguish the parallel Deposit and Loan rankings more clearly,
  reduce header button weight, and make Home official-bank actions consistent
  with Product Grid cards.
- Outcome: each ranking region now has a family-specific semantic top rail and
  quiet header tint plus an explicit label and Deposit/Loan icon. Header View
  all buttons are removed; localized text-style more links now follow each
  list. Home official-bank actions use the same label, external-link icon,
  classes, new-tab target, and `noopener noreferrer` protection as Product
  Grid cards.
- Scope: rate eligibility, Deposit descending order, Loan ascending order,
  five-item caps, independent unavailable states, internal detail links, API
  contracts, canonical data, and evidence boundaries are unchanged. Additional
  title candidates were reviewed, but the runtime identity remains `BankTable`
  pending a separate Product Owner choice and domain/trademark clearance.
- Key files: Public Home surface and locale resources, Public README,
  requirements, Product Grid/Home IA, metric baseline, decision `D-048`, and
  WBS `5.31`.
- Verification:
  - Public typecheck and production build passed
  - rendered Home passed at `1440px` EN, `768px` KO, and exact `390px` JA with
    no document overflow, browser error, or interaction target below `44px`
  - every viewport rendered five Deposit rates in descending order
    (`5`, `5`, `5`, `5`, `4.65`) and five Loan rates in ascending order
    (`3.45`, `4.45`, `4.45`, `4.59`, `4.59`)
  - no header View all button remained; EN/KO/JA bottom more links rendered as
    links, not buttons
  - all ten official-bank actions matched the Product Grid card text-link
    composition and were not wrapped by buttons
- Known issue: title and `.com` availability are not changed or reserved by
  this presentation slice; formal domain and trademark checks remain external
  launch decisions.
- Next step: choose the final customer-facing title before production DNS and
  brand investment.

## 2026-08-15 - Bankoom Public Identity

- WBS: `5.32`
- Status: done
- Goal: replace the temporary Public title with `Bankoom` and make the paired
  `oo` the defining logo idea as two eyes comparing bank products.
- Outcome: Public metadata, EN/KO/JA customer copy, header, footer, and
  methodology boundaries now use `Bankoom`. The shared code-native mark uses
  two overlapping circular eyes with outward pupils; the wordmark emphasizes
  its `oo`, and the favicon repeats the same eye geometry on evergreen.
- Scope: FPDS remains the internal platform/runtime identity. Home rankings,
  catalog actions, comparison semantics, APIs, canonical data, Review state,
  and publication behavior are unchanged.
- Key files: Public layout, locale resources, shared mark/wordmark, header,
  footer, app icon, Public README, requirements, Product Grid/Home IA,
  decision `D-049`, and WBS `5.32`.
- Verification:
  - Public typecheck passed
  - Public production build passed, including static `/icon.svg`
  - `/dashboard` returned `200` with `Bankoom` metadata and `/icon.svg`
    returned `200 image/svg+xml`
  - production-rendered header passed at `1440px` EN and exact `390x844` KO;
    the mobile document stayed within the CSS viewport, the title resolved to
    `홈 — Bankoom`, and the Home brand link retained its accessible name
  - desktop and mobile unavailable states were inspected because the isolated
    Public render had no API process; data-bearing Home content was unchanged
    by this identity-only slice
  - final stale-brand search and `git diff --check` passed
- Known issue: domain registration and formal trademark clearance remain
  external launch actions and are not performed by this code slice.
- Next step: confirm the production domain/DNS and repeat the same brand smoke
  against the deployment candidate.

## 2026-08-15 - Bankoom Public Experience Refinement

- WBS: `5.33`
- Status: done
- Goal: audit and improve the Public experience across design, UI/UX, source
  structure, rendering performance, brand scale, logo geometry, trilingual
  wrapping, and the information density of Home and product catalogs.
- Outcome: the paired-eye mark is larger and both pupils are centered; the
  desktop/tablet Bankoom wordmark uses a stronger title scale. Home now has a
  shorter thesis, a compact snapshot, less repeated family/evidence copy, more
  deliberate section spacing, and lighter one-line desktop ranking rows.
  Catalog cards remove optional customer/highlight labels and keep one primary
  plus at most two essential supporting metrics. The comparison selection bar
  now communicates count directly without decorative capacity indicators.
- Localization and accessibility: Korean and Japanese use language-aware line
  breaking, while compact navigation, controls, rates, freshness, and external
  actions stay intact. Exact `390px` retains a mark-only header so primary
  navigation and country selection fit. Existing focus, reduced-motion,
  semantic heading, bounded internal-scroll, and minimum-target behavior remain.
- Structure and performance: product metric/label/formatting logic is
  centralized in `public-product-presentation.ts`, removing nearly 500 lines
  of local comparison/detail formatting and label code. Public
  product/filter/detail reads now
  revalidate at five minutes and dashboard aggregate reads at fifteen minutes,
  while the eight-second unavailable-state timeout remains.
- Scope: no API contract, canonical product, Review state, publication rule,
  financial calculation, raw evidence boundary, or personalized recommendation
  behavior changed.
- Key files: Public shared mark/favicon/header/footer/navigation, Home and
  catalog/comparison/detail surfaces, locale/global styles, Public API client,
  shared presentation module, Public README, requirements, IA/metric baseline,
  decision `D-050`, and WBS `5.33`.
- Verification:
  - Public `pnpm run typecheck` passed
  - Public `pnpm run build` passed, including all static/dynamic routes and
    `/icon.svg`
  - production-rendered Home passed at `1440px` EN, `768px` KO, and exact
    `390px` JA; Deposit, Credit Card, Loan, selected comparison, Deposit detail,
    Loan detail, and Methodology were also checked across representative
    EN/KO/JA desktop/tablet/mobile states
  - all checked documents matched their viewport widths; intentional mobile
    sort rails and term-rate tables remained bounded internal scrollers
  - final exact-390px Japanese Home had no overflow, undersized target, browser
    exception, long motion, or awkward snapshot-label split
- Known issue: domain registration and formal trademark clearance remain
  external launch actions. The mark-only exact-390px header is intentional;
  the full wordmark appears from the existing tablet-capable breakpoint.
- Next step: repeat the responsive/browser smoke against the deployment
  candidate after production domain and API-origin configuration are finalized.

## 2026-08-15 - Vancity Collection Failure Recovery

- WBS: `5.34`
- Status: done
- Goal: account for the failed/partial Vancity Admin collection history,
  correct each reusable cause without weakening source or publication safety,
  and recollect only Vancity's active Canadian Product Type coverage.
- Root cause:
  - the seven `failed` runs from 2026-07-23 were persisted operator
    cancellations, not bank transport failures
  - later 2026-07-24, 2026-07-28, and initial 2026-08-15 attempts completed
    with `partial_completion_flag=true` and zero selected sources because
    Vancity returned HTTP `429` to direct HTTPS clients; the existing browser
    path produced PDF only and could not serve HTML homepage discovery
  - Admin homepage/companion discovery constructed fetch policies directly,
    so it bypassed environment browser settings even after Vancity was added
  - once discovery recovered, extraction exposed a separate post-migration
    issue: migration `0040` replaced `llm_usage_record` with a discard-only
    compatibility view, while AI-stage schema discovery inspected physical
    tables only and therefore rejected the valid `public` schema
  - a retired `Vancity-2024-Climate-Report.pdf` had also been admitted as
    generic supporting evidence for three lending scopes; its `404` made those
    otherwise healthy runs partial even though it contained no product facts
- Outcome: fetch policy now requests browser DOM for HTML-only discovery and
  browser PDF for stored snapshots, loads environment browser settings while
  retaining the exact current bank allowlist, and closes direct HTTP error
  responses. Vancity is in the default browser-enabled domain set. Extraction,
  normalization, and validation/routing schema checks use
  `information_schema.tables` so base tables and `0040` compatibility views
  are both valid relations. Annual/climate disclosures are excluded from
  product-supporting discovery.
- Vancity-only execution:
  - every launch and targeted retry was constrained to `country_code=CA` and
    `bank_code=VANCITY`; no other bank was included
  - the effective latest runs cover `chequing`, `credit-card`, `gic`,
    `line-of-credit`, `mortgage`, `personal-loan`, and `savings`
  - all seven runs are `completed` with no error or partial flag; `36/36`
    selected sources succeeded, using 29 `browser_pdf_fallback` snapshots and
    seven direct HTTPS snapshots
  - 42 generated Vancity sources remain active; the three climate-report rows
    are inactive with `superseded_by_homepage_catalog_generation` lineage
- Downstream audit: the effective runs produced 23 candidates. Existing policy
  approved four and left 19 in Review; 22 candidates have validation errors
  and one passed. Three Review tasks were approved by normal automation, one
  pass candidate was promoted without a Review task, and 19 tasks remain
  queued. No manual canonical or Review decision was made. The four promoted
  products (two credit cards and two mortgages) are active in canonical data
  and visible in the fresh Canadian Public snapshot
  `agg_Z5YXEFgOh6KyVHq0`; the latest Public projection contains no incomplete
  comparison product.
- Key files: format-aware discovery fetch policy and tests, Admin source
  catalog generation and exclusions, AI-stage persistence schema resolution,
  example environments, discovery/API/pipeline READMEs, source-registry and
  bounded-retention policies, decision `D-051`, RAID, and WBS `5.34`.
- Verification:
  - Discovery full suite: 56 tests passed
  - source-catalog and collection-runner API suites: 182 tests passed
  - extraction, normalization, validation/routing, and country-scope pipeline
    suites: 348 tests passed
  - live exact-bank Admin fetch returned browser-rendered Vancity DOM while
    preserving `allowed_domains=(vancity.com)`
  - shared-dev final audit confirmed seven terminal runs, `36/36` successful
    sources, zero source failures, zero partial flags, and four promoted
    product IDs present in the latest Public API response
- Known issue: direct non-browser Vancity requests still receive `429`, so
  collection depends on the bounded local browser and has higher capture cost.
  The 19 queued candidates are expected evidence/essential-field review work,
  not failed collection runs, and remain non-public.
- Next step: monitor Vancity under RAID `D-002` and process the 19 Review tasks
  only through the existing evidence-led operator workflow.

## 2026-08-16 - Vancity Coverage Recovery Pause Checkpoint

- WBS: `5.35`
- Status: in progress; intentionally paused by the Product Owner
- Outcome to date: mapped Vancity's current official product hubs and detail
  routes across all seven active Product Types, expanded the curated registry
  to 60 rows including the official insured-mortgage route, and implemented
  evidence-bounded discovery, extraction, grounding, and validation fixes for
  Vancity's structured CMS, multi-product pages, comparison tables, stale rate
  support, deposit-only ceilings, and mortgage qualification rates.
- Data safety: no Review item was manually approved and no canonical/Public
  fact was directly edited. Every collection launch remained constrained to
  `country_code=CA` and `bank_code=VANCITY`.
- Latest completed comparison baseline:
  `collection_xQrVsioO6c2IcvcX` / `corr_LHaKVlpvuPzAxNF1`; seven completed,
  zero failed/partial, 46 candidates, 17 approved, 29 in Review, 32 Review
  tasks, and validation 14 pass / 32 error.
- Active background collection at pause:
  `collection_pC4G-nfcCpkakYrE` / `corr_syRk20gX8Sf7uoUd`. Its five requested
  Vancity runs were last observed as `started` with no error/partial result;
  chequing had reached extraction and the serial runner had not yet produced
  candidates. It was deliberately not terminated because forced termination
  can leave run state stuck at `started`. Audit this exact collection before
  considering any relaunch.
- Verification completed before the pause:
  - discovery full suite: 60 tests passed
  - API source-catalog full suite: 160 tests passed
  - worker pipeline full suite: 435 tests passed
- Resume entrypoint: read root startup docs and `goal.md`, then perform a
  one-second status check of `collection_pC4G-nfcCpkakYrE` using
  `tmp/fpds_admin_collection_goal_tool.py wait`. When terminal, inspect the
  detailed per-Product-Type summary, canonical promotion, Review reasons, and
  latest Public aggregate before making another code or collection decision.
- Remaining completion work: terminal collection audit; targeted follow-up
  only if grounded blockers remain; Public aggregate verification; final
  affected test rerun; `git diff --check`; tracked test-artifact restoration;
  ignored research-helper cleanup; final documentation/WBS update; and removal
  of `goal.md` only after all acceptance criteria pass.

## 2026-08-16 - Vancity Coverage Recovery Continuation Pause

- WBS: 5.35
- Status: in progress; intentionally paused by the Product Owner
- Completed execution: Vancity-only collection
  collection_bkk5K_e2ZD5Lh1ij completed five runs with zero failure/partial
  state and produced 35 candidates: 22 approved and 13 in Review. Chequing
  approved 9/9, cards 5/8, GICs 6/7, line of credit 0/3 before the final
  sibling-boundary fix, and personal loans 2/8.
- Quality outcome:
  - exact card H1s and student variants are retained; deterministic purchase
    rates survive AI merge and Review-AI fallback
  - Vancity calculator copy can no longer turn $123 rewards value into a
    no-fee card's annual fee
  - the official ILTD terms PDF supplies the exact $1,000 minimum, ISO dates
    no longer create a 14-year GIC row, and decisive non-redeemable evidence
    wins over noisy subtype inference
  - Creditline and Personaline bind separately to their official rate, limit,
    and security columns; the final validator exception requires all
    comparison fields, one evidence chunk, official sources, and the
    deterministic sibling-table contract
  - the EV loan is approved with Prime + 1%, amount from $1,500, and maximum
    10-year term; its rate link now prefers the Electric Vehicle section
  - products lacking exact public comparison facts remain in Review; no
    Review task was manually approved and no canonical/Public fact was
    directly edited
- Key files: Vancity GIC registry, extraction service, supporting merge and
  normalization, validation routing, API AI verification, and focused tests.
- Verification:
  - latest extraction + normalization + validation/routing suites: 370 passed
  - earlier continuation worker pipeline full suite: 442 passed
  - API source catalog, collection runner, and AI suites: 208 passed
  - first post-fix collection: five completed, zero failed/partial
- Active background recollection at pause:
  collection_g6Bdzbm3utaEA8s2 / corr_VOQHNiY7-kdwn8HA, limited to Vancity
  credit card, GIC, line of credit, and personal loan. Exact run IDs and resume
  checks are in root goal.md. Last observed state was four started runs at
  serial source-catalog collection, zero candidates, zero Review tasks, and no
  errors. It was not force-terminated because that can strand run state.
- Next step: poll and audit that exact collection before any new launch,
  compare per-type approval/Review outcomes, verify canonical and Public
  projections, then complete final tests, artifact cleanup, diff check,
  WBS/journal closure, and goal.md removal only if all criteria pass.

## 2026-08-20 - Vancity Coverage Recovery Final Audit Checkpoint

- WBS: 5.35
- Status: in progress; collection-quality recovery is verified, while two
  exact canonical/Public deactivations await explicit Product Owner authority.
- Collection outcome:
  - final Vancity card run
    collection_c2bKGp1SUqpSI2r0 / corr_oYsFXoYX6iZN8zQJ completed without
    failure or partial state and approved all eight exact cards
  - latest safe coverage is chequing 9/9, cards 8/8, GICs 6/7, lines of
    credit 2/3, and personal loans 3/8
  - the remaining Review items lack an exact current public comparison fact or
    contain an intentionally non-scalar condition; no Review item was manually
    approved and every launch remained limited to Vancity in Canada
- Quality fixes:
  - retained exact detail/sibling product identities and exact deterministic
    values through AI merge and normalization
  - separated card purchase rates from adjacent rewards, cash-advance,
    balance-transfer, and deposit-rate numeric context
  - bound the Planet-Wise EV amount and rate evidence to the exact EV section
  - suppressed Escalating GIC redeemability when cash-out and conversion rights
    differ by account scope, including a Review-AI restoration guard
  - retained source continuity in Review/canonical lookup, allowed only fully
    grounded one-chunk Creditline/Personaline sibling-table promotion, and
    allowed newer approved exact-name candidates to supersede older Review
    tasks
- Review audit: 16 Vancity tasks remain queued/deferred. Fourteen are genuine
  safe gaps: one Escalating GIC, one HELOC, seven mortgages, and five personal
  loans. Two are stale: an old combined student-card family and an old
  US-dollar redeemable GIC candidate whose exact replacements are approved.
- Public/canonical audit:
  - exact current cards are active with verified names and values, including
    Classic $0 / 19.50% and Gold $99 / 19.50%
  - prod__eKASmTjodHuonf4 (cand-fff352021249cbc9) remains an active generic
    duplicate of the exact student low-interest card
  - prod_uGjaqi6V-kGTUoM4 (cand-2d4f710f1a1c9a60) remains active with the
    unsafe scalar redeemable_flag=true; the latest safe Escalating candidate
    cand-fff2b456f306ff10 omits that scalar and remains in Review
- Verification: worker pipeline full suite 452 passed; API service full
  suite 412 passed; tracked test-generated fixtures and aggregate log content
  restored after testing.
- Decision required: explicitly authorize audited deactivation of only the two
  canonical/candidate pairs above. After authorization, verify the refreshed
  CA Public projection, resolve the two stale Review tasks through the audited
  workflow, run final diff checks, and close WBS 5.35/goal.md only when all
  acceptance criteria pass.

## 2026-08-20 - Vancity Coverage Recovery Completed

- WBS: 5.35
- Status: completed after explicit Product Owner authorization for the two
  exact canonical safety remediations and the CA Public refresh.
- Audited remediation:
  - candidate cand-fff352021249cbc9 was rejected with reason
    duplicate_generic_canonical_replaced and canonical product
    prod__eKASmTjodHuonf4 was changed to inactive
  - candidate cand-2d4f710f1a1c9a60 was rejected with reason
    mixed_account_scope_redeemability and canonical product
    prod_uGjaqi6V-kGTUoM4 was changed to inactive
  - each action emitted its candidate audit event and canonical Discontinued
    change event; no other candidate, product, bank, or country was remediated
- Public refresh:
  - the two actions coalesced into CA request
    aggreq_1zAX6DXMN2vNS9tz
  - snapshot agg_Mr-u6biHMK1jbtTj completed at
    2026-08-20T13:20:53.371523+00:00 with stale_flag=false and no error
  - active Public rows changed from 113 to 111, exactly matching the two
    approved deactivations; the snapshot retains both products as inactive
    audit history while the Public API excludes them
  - exact replacement prod_Gl4AJToJBwc0LFX5 remains active as
    enviro Visa Classic low interest for students at $50 and 11.25%
  - all eight exact Vancity card product IDs remain active with their expected
    names, annual fees, and purchase interest rates
- Final verification:
  - aggregate audit: 183 projection rows, 111 active, 72 inactive, 27
    intentionally excluded incomplete-comparison rows
  - worker pipeline full suite: 452 passed
  - API service full suite: 412 passed
  - git diff --check passed and tracked test/refresh artifacts were restored
- Known non-public follow-up: 14 genuine Vancity evidence-gap Review tasks and
  two identified stale Review tasks remain safely outside Public. Exact-name
  reruns now supersede ordinary stale tasks; the old combined two-product
  student-card task is intentionally not auto-collapsed because that would
  weaken the multi-product boundary.

## 2026-08-20 - Bankoompare Public Brand Refinement

- Status: completed the Product Owner-requested Public title and paired-eye
  mark refinement without changing FPDS internal naming or product behavior.
- Outcome:
  - renamed the customer-facing Public wordmark, accessible brand name,
    metadata, and EN/KO/JA brand references from Bankoom to Bankoompare
  - retained the emphasized paired `oo` while extending the wordmark as
    Bank + `oo` + mpare
  - separated the two outlined eye circles by a small visible gap and kept each
    pupil exactly centered; the shell mark and app icon use the same scaled
    geometry
  - preserved the exact 390px behavior that hides the longer wordmark while
    retaining the mark, primary navigation, and country control
- Key files: Public mark and app icon, layout metadata, locale resources,
  Public README, and Product Grid identity baseline.
- Verification:
  - Public `pnpm run typecheck`: passed
  - Public `pnpm run build`: passed
  - rendered header inspected at 390px, 768px, and 1440px; no wordmark wrapping
    or header overflow was observed
  - legacy customer-facing `Bankoom` references: none in Public runtime
    or the active Product Grid identity baseline
- Known issues: none for this refinement. Temporary browser profiles and
  screenshots used for visual QA were removed after inspection.

## 2026-08-20 - First-Collection Precision Source Coverage

- WBS: 5.36
- Status: completed the Product Owner-requested first-versus-subsequent source
  coverage behavior without changing Review, approval, or Public publication.
- Server contract:
  - a bank/Product Type has completed collection only when server-side
    `ingestion_run` history contains a completed run with a non-empty source
    scope; generated-source count and browser state do not qualify
  - first collection is forced to `precision`, while completed items use
    `standard` current-source collection unless the operator requests
    `precision_rediscovery`
  - mixed bulk requests force only first-time items; a standard run whose
    active detail scope disappeared is changed to `precision_fallback`
- Precision coverage:
  - reuses verified homepage/coverage routes and eligible active official
    registry entry/detail rows
  - inspects at most 12 existing detail pages for newly linked sibling
    products and exact evidence routes
  - retains exact domain/verified-brand, country, source-language, SSRF,
    Product Type, page-evidence, product-boundary, companion, Review, and
    publication gates
  - records seed rejection/reuse, page attempts/successes, candidate,
    promoted/rejected, and reached-limit telemetry in run metadata
- Admin UX:
  - first-time coverage cards clearly show that precision discovery is
    required
  - completed cards expose a per-item precision-rediscovery checkbox
  - bank-list bulk collection exposes one completed-item option while keeping
    first-time selections visibly mandatory; queued EN/KO/JA feedback reports
    precision versus current-source item counts
  - narrow layouts keep the new short labels intact inside wrapping toolbars,
    and coverage cards retain their existing column-first mobile layout
- Regression coverage:
  - mixed first/completed plan resolution
  - official existing-detail sibling discovery and external-domain rejection
  - standard active-scope reuse without materialization
  - missing-detail precision fallback with operator-visible run reason
- Verification:
  - source catalog and runner suite: 176 passed
  - API service full suite: 416 passed
  - Admin `pnpm run typecheck`: passed
  - Admin `pnpm run build`: passed
  - `git diff --check`: passed before final documentation closeout
- Operations: no live bank collection, canonical mutation, Review decision, or
  Public refresh was run for this implementation slice.

## 2026-08-20 - RBC Collection Scope Audit and Pending Work Cancellation

- Status: operational investigation and requested cancellation completed; no
  product-behavior fix or completed-data rollback was authorized or applied.
- Scope finding: operator collection `collection_T7ROyyx3YehA9Twa` contained
  exactly seven `RBC` Product Type groups and no other bank. The operator had
  requested precision rediscovery for completed items; first-time RBC items
  were independently forced to precision by the server contract.
- Concurrent work: scheduler collection `collection_2C4inSKiDWSvtOWG` started
  one minute earlier and covered Alterna and BMO. This separate automation run,
  not the RBC selection payload, explains the visible cross-bank activity. A
  second scheduler plan, `collection_rWBBNtB-dv3V5MA9`, was created after the
  first scheduler plan completed.
- Completed automation outcome: the first scheduler plan created 20 candidates
  across Alterna/BMO and promoted four products; 15 BMO candidates remained in
  active Review. The second plan completed two additional Alterna candidates
  into Review before its four remaining BMO runs were cancelled.
- RBC outcome: the detached collection runner continued after the API server
  was stopped. All seven RBC runs reached terminal state by 20:03 Vancouver
  time: 41 candidates, 16 approved/promoted products, 25 candidates still in
  Review, and one no-detail partial Mortgage run. No completed RBC result was
  rolled back.
- Root cause: scheduler due-item selection looks only at runs whose current
  `run_metadata.pipeline_stage` remains `source_catalog_collection`. A normal
  run advances that field through snapshot, parse, extraction, normalization,
  and validation, so its recent terminal result is excluded from the scheduler
  cadence query and the same coverage can appear immediately due again.
- Cancellation: no collection runner/API process remained. The four BMO runs
  still persisted as `started` under `collection_rWBBNtB-dv3V5MA9` were changed
  to terminal `failed` with `operator_cancelled=true`, an explicit Product
  Owner cancellation reason, and preserved run history. The affected scopes
  were BMO Chequing, Credit Card, GIC, and Line of Credit.
- Verification: after a stability interval, nonterminal ingestion runs `0`,
  queued/started aggregate refresh requests `0`, and FPDS API/collection runner
  processes `0`.
- Known risk: `COLLECTION_AUTOMATION_ENABLED` remains `true`, and the runtime
  defaults its scheduler switch to enabled. A broad automation pause was not
  applied because it exceeds cancellation of current work. Until the due-item
  defect is fixed or a separate pause is approved, restarting the API can
  recreate broad scheduled collection work.

## 2026-08-20 - Automatic Collection Scheduler Paused

- Status: completed by explicit Product Owner instruction; automatic scheduler
  work remains disabled until a later explicit re-enablement instruction.
- Runtime: `.env.dev` now sets
  `FPDS_AUTOMATION_SCHEDULER_ENABLED=false`, so an API restart does not create
  the collection-automation scheduler task. Manual Admin collection remains
  available.
- Database policy: active `COLLECTION_AUTOMATION_ENABLED` version `2` resolves
  to `false`; the former enabled version is inactive. The new policy preserves
  the Product Owner request, pause time, and re-enable boundary.
- Race cleanup: API startup immediately before the pause created scheduler plan
  `collection_ItwximlkzJAsgtnI`. Alterna Chequing completed before termination;
  the active Alterna GIC runner and four queued BMO runs were stopped and closed
  as `failed` with `operator_cancelled=true`. No completed data was rolled back.
- Runtime continuity: the old API/runner process tree was stopped and the API
  was restarted successfully on port `4000` with the scheduler flag forced
  false. `/healthz` returned `200`.
- Verification: active DB policy `false`; nonterminal ingestion runs `0`;
  queued/started aggregate requests `0`; collection runner processes `0`; and
  no scheduler advisory lock.
- Re-enable rule: do not reactivate either runtime or DB switch until the
  Product Owner explicitly requests it. Correct the scheduler due-item defect
  and run its regression coverage before normal automation is restored.

## 2026-08-20 - Bankoompare Public Discovery Refinement

- Status: completed the requested Public copy, Home-scope, catalog-sort, and
  Grid/List presentation refinement without changing financial data or APIs.
- Brand copy: EN/KO/JA metadata, footer tagline, Home hero, and Deposit,
  Credit Card, and Loan catalog headings now reinforce Bankoompare as a place
  to look into bank products and compare grounded facts across banks.
- Home scope: Home parsing and Home links retain only `locale` and
  `country_code`; bank, Product Type, customer tag, amount, fee, term, sort,
  page, axis, and catalog-view state from product screens no longer narrow
  Home.
- Catalog sort: Deposit now opens at `display_rate desc`, Credit Card at
  `annual_fee asc`, and Loan at `display_rate asc`. The visible Default
  option and legacy `sort_by=default` parsing path were removed.
- View modes: accessible localized Grid/List icon controls now end the sort
  rail. Grid retains the existing comparison cards; List renders compact rows
  whose active sort value is visually dominant while Compare, detail, and
  available official-bank actions remain reachable.
  Catalog sort, page, and view state also travels through product detail and
  back; rendered Credit Card HTML confirmed `annual_fee asc` plus List.
- Responsive follow-up: long Japanese headings and source-derived product
  names receive bounded wrapping, and Home/list containers now keep narrow
  content from widening the document. The mobile sort/view rail remains an
  intentionally bounded horizontal scroller.
- Runtime checks: rendered HTML confirmed clean Home scope links, no active
  Home scope section, Deposit Interest rate active with Grid, Credit Card
  Annual fee active with List, Loan Interest rate active, and no Default sort.
- Verification:
  - Public `pnpm run typecheck`: passed
  - Public `pnpm run build`: passed
  - headless Chrome captures checked Home and catalogs at `1440px` and
    `390px` in EN/KO/JA; a filtered Home request retained the full 126-product,
    15-bank snapshot shown by the current local aggregate
  - `git diff --check`: passed before journal closeout
- Boundaries: no Admin, collection, canonical-data, Review, publish, or public
  API mutation was performed. Automatic collection scheduling remains disabled.

## 2026-08-20 - Public Instant Search, Infinite Loading, and Information Notice

- Status: completed the requested Deposit, Credit Card, and Loan discovery
  behavior plus Home/detail information notice without changing canonical
  financial data, Review state, or publication gates.
- Search API: public products and filters now accept a bounded q, normalize
  whitespace, and match public bank or product names case-insensitively with
  literal contains semantics. Percent and underscore remain literal. Applied
  responses expose the normalized q; regression covers bank-name,
  product-name, case, whitespace, wildcard-literal, and option-count behavior.
- Instant conditions: every catalog includes a localized bank-or-product
  search field. Search input is debounced 350ms; checkbox and select changes
  update the shareable URL immediately. Apply was removed, filter changes start
  at page 1, and Home continues to discard catalog search/filter state.
- Continuous results: catalogs render the first 20 products and use a
  same-origin Public route plus an IntersectionObserver sentinel to load and
  deduplicate later API pages. Stale requests are aborted on scope changes;
  localized loading/completion/error/retry states replace Previous/Next.
  Grid/List and comparison remain available over appended rows.
- Trust notice: a shared EN/KO/JA Home/detail notice identifies AI-agent
  assistance, non-advertising, no compensation from displayed institutions,
  update efforts, change risk, and required official-site verification before
  applying.
- Runtime verification: API was restarted on port 4000 only after confirming
  the .env.dev scheduler flag was false; /healthz returned ok. Live API
  searches returned seven Royal Bank deposit products for q=royal and one
  product for q=Signature No Limit.
- Verification:
  - Public-products unit suite: 12 passed
  - API standalone regression suite: 11 passed
  - API package compile: passed
  - Public pnpm run typecheck: passed
  - Public pnpm run build: passed
  - headless Chrome at exact 390px and 1440px: instant text search, instant RBC
    checkbox, 20-to-64 product automatic loading, all three search fields,
    Home/detail notice, and no horizontal overflow passed
  - rendered HTML: no Apply or Previous/Next controls; same-origin next-page
    proxy returned the standard public envelope
- Operations: automatic collection scheduling remains disabled. No collection,
  Review, canonical, aggregate-refresh, or publish operation was launched.

## 2026-08-21 - Bankompare Public Identity

- WBS: `5.37`
- Status: completed the Product Owner-requested customer-facing rename and
  logo decision without changing the internal FPDS identity or product data.
- Outcome:
  - renamed Public metadata, accessible labels, EN/KO/JA brand references,
    information notices, and the exact-spelling wordmark from `Bankoompare` to
    `Bankompare`
  - replaced the paired-eye mark, which conflicted with the new single-`o`
    spelling, with one code-native comparison lens: a circular `o`, a central
    split, and one record point on each side
  - applied the same geometry to the shell mark and evergreen app icon while
    preserving the mark-only exact-390px header behavior
- Decision: `D-054`; `FPDS` remains the internal platform/runtime name and no
  Home, catalog, comparison, API, localization, or publication behavior changed.
- Key files: Public mark/icon, layout metadata, locale resources, Public
  README, requirements, Product Grid IA, decision log, and WBS.
- Verification:
  - Public `pnpm run typecheck`: passed
  - Public `pnpm run build`: passed
  - production-rendered Home inspected at `1440px` EN, `768px` KO, and exact
    `390px` JA; the mark and wordmark were visually clear at applicable widths
  - measured document/body scroll width equaled the viewport at all three
    widths; exact `390px` hid only the wordmark and kept every visible header
    action within the viewport at a minimum `44px` target
  - active Public runtime and README contain no stale `Bankoompare` or
    `Bankoom` customer-facing references
- Boundaries: no Admin, collection, canonical-data, Review, aggregate-refresh,
  publish, or external write was performed. Automatic scheduling remains
  disabled.

## 2026-08-22 - Bankompare Ledger-B Identity Refinement

- WBS: `5.38`; supersedes the rejected visual treatment from `5.37` while
  retaining the approved `Bankompare` customer name.
- Status: completed the Product Owner-requested logo and wordmark redesign
  without changing internal FPDS naming or product behavior.
- Design decision:
  - removed the comparison-lens symbol and all single-letter color emphasis
  - rendered `Bankompare` as one uninterrupted same-color text node with no
    styled child letter
  - selected a ledger `B` after considering lens, bank-pillar, BK-monogram,
    table, and record-based concepts; two stacked rounded record rows share a
    spine and carry one short data stroke each
  - used the outlined geometry in the shell and the same solid white-on-
    evergreen geometry in the app icon
- Decision: `D-055`; the exact-390px mark-only header, EN/KO/JA behavior,
  accessible naming, and every data/publication boundary remain unchanged.
- Key files: Public mark, footer composition, app icon, Public README,
  requirements, Product Grid IA, decision log, and WBS.
- Verification:
  - Public `pnpm run typecheck`: passed
  - Public `pnpm run build`: passed, including static `/icon.svg`
  - production-rendered Home visually inspected at `1440px` EN, `768px` KO,
    and exact `390px` JA; the mark remained identifiable and the wordmark read
    as one typographic unit at applicable widths
  - rendered favicon inspected at `256px`; the two record rows and `B`
    silhouette remained clear
  - document/body scroll width equaled the viewport at all three widths;
    exact `390px` retained every visible header action inside the viewport at
    a minimum `44px` target, and the footer brand remained in bounds
  - rendered wordmark text was exactly `Bankompare`, used one computed color,
    and had zero styled child elements
- Boundaries: no Admin, collection, canonical-data, Review, aggregate-refresh,
  publish, or external write was performed. Automatic scheduling remains
  disabled.

## 2026-08-22 - Bankompare Globe and Focused Review Detail

- WBS: `5.39`, `5.40`; supersedes only the rejected ledger-B mark in `5.38`
  while retaining the approved `Bankompare` name and monochrome wordmark.
- Status: completed the Product Owner-requested global globe identity and Admin
  Review Detail simplification without changing product data or mutation rules.
- Outcome:
  - replaced the shell and favicon ledger-B geometry with one simple globe made
    from a circular boundary, equator, and paired meridian form; the globe
    signals the worldwide product direction without widening current market scope
  - retained the one-color uninterrupted `Bankompare` title and exact-390px
    mark-only header behavior
  - reduced Review Detail to a compact identity/facts band, recommendation,
    expanded source check, affected fields, and decision path
  - collapsed product facts, unaffected fields, advanced overrides, decision
    notes, diff, evidence/audit context, and AI `Official sources`; active or
    attention-requiring AI verification still opens and keeps field citations
    beside the compared value
- Decisions: `D-056`, `D-057`; review authorization, CSRF, correction staging,
  audit, canonical, aggregate-refresh, and publication boundaries are unchanged.
- Key files: Public mark/app icon, Admin Review Detail surface, both boundary
  READMEs, requirements, Public/Admin IA, UI override register, decision log,
  and WBS.
- Verification:
  - Public `pnpm run typecheck`: passed
  - Public `pnpm run build`: passed, including static `/icon.svg`
  - Admin `pnpm run typecheck`: passed
  - Admin `pnpm run build`: passed
  - production-like local Public Home rendered at `1440px` EN, `768px` KO, and
    exact `390px` JA; the globe remained clear in header/footer, the wordmark
    stayed intact, and document/body width stayed within the viewport
  - an isolated, non-persisting Review Detail fixture rendered at `1440px`,
    `768px`, and exact `390px`; document/body width matched the viewport,
    `Source check` was open, `Official sources` was closed, and all secondary
    disclosure sections remained closed
- Boundaries: the QA fixture and screenshots were removed after inspection. No
  API, database, Review decision, canonical-data, aggregate-refresh, publish,
  or external write was performed. Automatic scheduling remains disabled.

## 2026-08-22 - Vercel FastAPI Public-Read Deployment

- WBS: `5.41` (`Completed`).
- Status: FastAPI is deployed to Vercel Production and Preview with live Public
  reads from the Product Owner-approved current development database.
- Outcome:
  - added the repository-root FastAPI entrypoint and retained the existing
    `api_service.main` route contract
  - forced `FPDS_AUTOMATION_SCHEDULER_ENABLED=false` whenever `VERCEL` is set,
    even if another environment value tries to enable it
  - pinned Vercel to Python 3.12 and consolidated FastAPI, psycopg, uvicorn,
    and worker dependencies in the root `pyproject.toml`/`uv.lock`
  - added upload and function-bundle exclusions for Public/Admin web builds,
    local environments, tests, docs, storage, and temporary data
  - created and linked the Vercel project `bankompare-api` to the existing
    GitHub repository
  - registered the current development database URL as a sensitive Preview and
    Production variable by explicit Product Owner direction; `.env.dev` itself
    and its auth secrets were not uploaded
  - generated distinct 384-bit session and CSRF secrets for Preview and
    Production and kept the scheduler disabled in both environments
  - deployed the public Production alias and a protected Preview deployment
- Decision: `D-058`. The first Vercel API period is Public-read oriented and
  serves only existing completed snapshots; worker and refresh automation stay
  outside Vercel.
- Key files: root Vercel entrypoint/configuration, Python runtime manifests,
  API README, environment strategy, decision/RAID logs, and WBS.
- Verification:
  - API unit suite: 425 tests passed
  - root Vercel-mode import: app title and Public products route found;
    scheduler remained false after an explicit attempted `true` override
  - dependency metadata dry run: both repository Python packages resolved
    before dependency consolidation
  - clean-source `vercel build --yes`: passed with Python 3.12
  - Production `/healthz`: `ok`
  - Production `/api/public/countries`: CA 142 and US 21
  - Production `/api/public/products?country_code=CA&page=1&page_size=1`: one
    item returned from 142 total
  - protected Preview `/healthz`: `ok` via authenticated Vercel request
  - protected Preview `/api/public/countries`: CA 142 and US 21
- Known issue / next step: Preview and Production now share the development
  database, so traffic, development work, authenticated API writes, capacity,
  and incident impact remain coupled. Keep Vercel Admin operations unused and
  migrate Production to a separate database before this becomes
  release-critical. Public data will remain at the latest completed snapshot
  until an explicitly operated refresh occurs.

## 2026-08-22 - Vercel Bankompare Public Deployment

- WBS: `5.42` (`Completed`).
- Status: Bankompare Public is deployed to separate Vercel Production and
  protected Preview environments, both backed by the deployed Bankompare API.
- Outcome:
  - created `bankompare-public`, connected the existing GitHub repository, and
    set its Git Root Directory to `app/public` with the Next.js preset
  - set `FPDS_PUBLIC_API_ORIGIN=https://bankompare-api.vercel.app` for Public
    Preview and Production without exposing an API credential to browser code
  - retained the existing server-component and same-origin Public BFF model for
    country and paginated product reads
  - deployed the stable anonymous Production alias and a deployment-protected
    Preview
  - updated the FastAPI Preview/Production Public web and allowed-origin values
    to `https://bankompare-public.vercel.app`, then redeployed both API targets
  - added Public env example, upload exclusions, and repeatable deployment notes
- Decision: `D-059`. No visual, localization, comparison, canonical-data,
  collection, scheduler, or Admin web behavior changed.
- Key files: Public README/env/ignore deployment files plus environment
  strategy, decision/RAID logs, WBS, and journal.
- Verification:
  - Public `pnpm run typecheck`: passed
  - Public production `pnpm run build` against deployed API: passed
  - Vercel Production and Preview builds: passed with Next.js 16.2.3
  - Production Home: HTTP 200 and rendered `Bankompare`
  - Production `/api/public/countries`: CA 142 and US 21
  - Production `/api/public/products?country_code=CA&page=1&page_size=1`: one
    item returned from 142 total
  - protected Preview `/api/public/countries`: CA 142 and US 21 through an
    authenticated Vercel request
  - API Production `/healthz`: HTTP 200 with
    `Access-Control-Allow-Origin: https://bankompare-public.vercel.app`
- Known issue / next step: anonymous Public reads now exercise the temporarily
  shared development database through the API. Keep the current bounded cache,
  scheduler-off posture, and no-Vercel-Admin operating rule until Production
  moves to its own database. Custom-domain/DNS work remains out of scope.

## 2026-08-22 - Responsive Public Discovery and Country Coverage

- WBS: `5.43` (`Completed`).
- Status: completed the Product Owner-requested Public shell, Home coverage,
  and catalog-default refinement without changing product data or API meaning.
- Outcome:
  - tightened the globe-to-wordmark gap in header and footer and retained the
    full `Bankompare` wordmark at exact `390px`
  - replaced mobile product icons and the separate country control with one
    hamburger containing Home, Deposit, Credit Card, Loan, and every published
    country; desktop navigation remains visible
  - replaced the Public/Current snapshot, Visible products, and Banks count
    ledger with a simple code-native world map plus localized published product
    counts from the existing public country catalog
  - gave Deposit, Credit Card, and Loan equal Home action emphasis
  - added an implicit responsive catalog view: Grid at `768px` and wider,
    List below `768px`; explicit `view=grid` and `view=list` persist
    through catalog filters and sorting
- Decision: `D-060`. Country availability, aggregate formulas, canonical
  data, publication gates, evidence privacy, and recommendation boundaries are
  unchanged.
- Key files: Public shell/mobile menu, country map, dashboard load/surface,
  catalog query/view components, locale resources, Public README, requirements,
  Public IA/metric design, decision log, and WBS.
- Verification:
  - Public `pnpm run typecheck`: passed twice, including final state
  - Public `pnpm run build`: passed twice, including final production build
  - local production-rendered Home checked at `1440px` EN, `768px` KO, and
    exact `390px` JA with live CA/US published counts
  - exact `390px` mobile menu contained localized Home, Deposit, Credit Card,
    Loan, Canada, and United States entries; all menu items measured `44px`
  - Deposit, Credit Card, and Loan all defaulted to List at `390px`; Deposit
    defaulted to Grid at `768px` and `1440px`; explicit Grid/List overrides
    rendered and persisted at the opposite form factor
  - document width stayed within the viewport for every checked Home/catalog
    state; a final network/browser-error rerun reported no failures
  - `git diff --check`: passed before journal closeout
- Boundaries: no Admin, collection, Review, canonical-data, aggregate-refresh,
  publication, or external write was performed. The local QA API ran with the
  automation scheduler explicitly disabled.

## 2026-08-23 - Vercel FastAPI Entrypoint Repair

- WBS: corrective follow-up to `5.41` (no new delivery scope).
- Status: repository fix is verified and ready to push; no Vercel deployment or
  project mutation was performed in this slice.
- Outcome:
  - added `[tool.vercel] entrypoint = "app:app"` so current Vercel FastAPI
    builds resolve the repository wrapper explicitly instead of relying on
    static inference through its dynamic `api_service.main` import
  - retained the repository root for `bankompare-api` and documented the
    FastAPI-error diagnostic for a mis-rooted `bankompare-public` project,
    whose Git Root Directory remains `app/public`
  - hardened upload and function exclusions for local `node_modules` and
    `.next` artifacts while keeping the function pattern below Vercel's
    256-character configuration limit
- Decision: no architecture or runtime-ownership decision changed; `D-058`
  and `D-059` remain authoritative.
- Key files: root `pyproject.toml`, `vercel.json`, `.vercelignore`, API and
  Public deployment READMEs.
- Verification:
  - Vercel-mode root import: app title, `/healthz`, and
    `/api/public/products` found; an attempted scheduler `true` override was
    forced to `false`
  - API full suite: 425 tests passed
  - API standalone regression suite: 11 tests passed
  - root `uv lock --check`: passed
  - clean tracked-source `vercel build --prod --yes`: passed with Vercel CLI
    59.5.0 and Python 3.12; generated `fastapi.func` routing covered all API
    paths
- Boundaries: no route, financial data, database state, environment variable,
  scheduler ownership, Public UI behavior, deploy, promotion, or external write
  changed.

## 2026-08-23 - Vercel Public Monorepo Isolation Repair

- WBS: corrective follow-up to `5.42` (no new delivery scope).
- Status: completed; `bankompare-public` is Ready in Production at its stable
  alias after a successful Next.js build.
- Cause:
  - the first Git commit containing the repository-root FastAPI `vercel.json`
    caused Public Git deployments to detect FastAPI
  - the Public project had the correct `app/public` Root Directory and Next.js
    preset, but `sourceFilesOutsideRootDirectory=true` remained enabled and
    the app root had no project-local `vercel.json`
  - the failed build log explicitly warned that `vercel.json` should exist
    inside the configured Root Directory before reporting the missing FastAPI
    entrypoint
- Outcome:
  - disabled source access outside the Public Root Directory in the live Vercel
    project while retaining `app/public` and the Next.js preset
  - added `app/public/vercel.json` with `framework=nextjs`, making the Public
    deployment contract explicit and independent of the API root configuration
  - deployed the corrected source to Production; the stable
    `https://bankompare-public.vercel.app` alias now targets the Ready build
- Verification:
  - saved Vercel project settings: `rootDirectory=app/public`,
    `framework=nextjs`, and `sourceFilesOutsideRootDirectory=false`
  - Public `pnpm run typecheck`: passed
  - clean monorepo Vercel build detected Next.js 16.2.3, compiled successfully,
    passed TypeScript, and generated all 10 routes; Windows local output linking
    then hit `EPERM`, while the authoritative remote Linux build completed
  - Production deployment: Ready; Home returned HTTP 200 and rendered
    `Bankompare`
  - Production same-origin `/api/public/countries`: CA 142 and US 21
- Boundaries: no API route, Public product behavior, financial data, database
  state, environment value, scheduler ownership, domain, or secret changed.

## 2026-08-23 - Vercel Public Turbopack Collision Hardening

- WBS: corrective follow-up to `5.42` (no new delivery scope).
- Status: implementation and local verification complete; the next Git-triggered
  Vercel build remains the production verification point.
- Cause:
  - the latest failed `bankompare-public` deployment and the immediately prior
    successful deployment both resolved Next.js 16.2.3 and React 19.2.5
  - the failed run stopped inside `next build` before compilation completed
    because different Turbopack JavaScript and sourcemap assets were emitted to
    the same `[root-of-the-server]` chunk paths
  - the same baseline succeeded in the prior uncached deployment and in a local
    build, confirming a nondeterministic Turbopack output collision rather than
    a route, type, or application-data failure
- Outcome:
  - changed only the Public production build to the supported
    `next build --webpack` opt-out; `next dev` continues to use Turbopack
  - documented the temporary production-bundler boundary in the Public README
  - retained the existing Next.js 16.2.3 lockfile and Vercel project isolation
- Verification:
  - inspected failed Production deployment logs: eight duplicate-output errors
    across two server chunks and their sourcemaps
  - Public `pnpm run typecheck`: passed
  - Public `pnpm run build`: passed with `Next.js 16.2.3 (webpack)`, all ten
    routes generated, and no Turbopack `[root-of-the-server]` output
- Known issue: remote verification requires the corrective files to reach the
  Git revision built by Vercel; no deployment or production alias changed in
  this slice.
- Boundaries: no Public route/UI behavior, financial data, API, database,
  scheduler, environment value, domain, secret, or external deployment changed.

## 2026-08-23 - SwitchaBank Public Identity and Discovery Copy

- WBS: `5.44` (`Completed`).
- Status: completed the Product Owner-requested Public rebrand and Home
  discovery-copy refinement without changing product data or recommendation
  boundaries.
- Outcome:
  - changed the customer-facing Public identity from `Bankompare` to
    `SwitchaBank` across the shell, metadata, methodology, comparison, and
    information-notice surfaces
  - replaced the globe with a simple code-native switch mark composed of two
    opposing horizontal arrows, including a matching white-on-evergreen favicon
  - changed the English Home hero to `Compare banks. Compare products. Switch
    smarter.` and aligned the Korean and Japanese hero/tagline meanings
  - refined supporting copy around side-by-side review and checking current
    bank terms before switching, while retaining explicit non-recommendation
    language
  - kept `FPDS` as the internal system name and retained the existing
    `bankompare-public` / `bankompare-api` Vercel project names
- Decision: `D-061`. The rebrand changes presentation and customer-facing
  language only; canonical data, eligibility, ranking, publication, and
  evidence boundaries are unchanged.
- Key files: Public mark/favicon, metadata and EN/KO/JA locale resources,
  Public README, requirements, Public IA, environment/RAID records, decision
  log, and WBS.
- Verification:
  - Public `pnpm run typecheck`: passed
  - Public `pnpm run build`: passed with Next.js 16.2.3 using the documented
    webpack production path; all ten routes generated
  - local production-rendered Home checked in Chrome at `1440px` EN,
    `768px` KO, and exact `390px` JA
  - every checked viewport rendered the localized title, two-path switch mark,
    full `SwitchaBank` wordmark, localized Home link label, and hero; document
    width stayed within the viewport
  - active Public runtime and README search found no customer-facing
    `Bankompare` reference
- Boundaries: no Admin behavior, API, financial data, database state,
  collection, scheduler, publication, environment value, Vercel project,
  deployment, domain, secret, or external write changed.

## 2026-08-23 - SwitchaBank Vercel Project Rename

- WBS: `5.45` (`Completed`).
- Status: completed the Product Owner-requested in-place rename of both
  existing Vercel projects.
- Outcome:
  - renamed `bankompare-api` to `switchabank-api` while retaining project ID
    `prj_CyWm7Bby1p1J4nMuO6Ntb3uegnGf`
  - renamed `bankompare-public` to `switchabank-public` while retaining
    project ID `prj_tU5QSEqRIZ6V3a5Lz0g64tLgRQWl`
  - preserved the API repository root, Public `app/public` root, framework
    presets, Git integration, deployments, environment values, and deployment
    protection
  - refreshed both ignored local `.vercel/project.json` links to the new
    project names without changing their IDs
  - confirmed Vercel retained the separately assigned
    `bankompare-api.vercel.app` and `bankompare-public.vercel.app`
    Production domains; no alias/domain migration or redeploy was performed
- Decision: `D-062`. Project naming now matches SwitchaBank, while domain
  migration remains a separate Product Owner decision because it also affects
  origin variables, CORS, aliases, and deployment sequencing.
- Key files: API/Public deployment READMEs, environment separation strategy,
  decision log, WBS, and journal.
- Verification:
  - Vercel project inspection reported both new names with their original
    project IDs and unchanged root/framework settings
  - the team project list contains `switchabank-api` and
    `switchabank-public`
  - API Production `/healthz`: HTTP 200 with
    `Access-Control-Allow-Origin: https://bankompare-public.vercel.app`
  - Public Production Home: HTTP 200 and rendered `SwitchaBank`
  - Public same-origin `/api/public/countries`: HTTP 200 with CA 149 and US 21
  - Public same-origin CA `/api/public/products?page=1&page_size=1`: HTTP 200
    with one product item
- Boundaries: no domain, alias, environment value, secret, deployment,
  financial data, database state, scheduler, collection, publication, API
  contract, or UI behavior changed.

## 2026-08-23 - SwitchaBank Vercel Deployment and Domain Migration

- WBS: `5.46` (`Completed`).
- Status: completed the Product Owner-requested API/Public deployment and
  Production-domain migration after the in-place project rename.
- Outcome:
  - updated API Production and Preview
    `FPDS_ALLOWED_PUBLIC_ORIGINS`/`FPDS_PUBLIC_WEB_ORIGIN` to
    `https://switchabank-public.vercel.app`
  - updated API Production and Preview
    `FPDS_PUBLIC_API_ORIGIN`/`FPDS_ADMIN_API_ORIGIN`, plus Public Production
    and Preview `FPDS_PUBLIC_API_ORIGIN`, to
    `https://switchabank-api.vercel.app`
  - created Ready API deployment `dpl_EBFtngDSVBntEEHq6i4BrmMxk391` under
    `switchabank-api`; Vercel shortened its generated URL to
    `switchabank-6fhtrk2nm-kevins-projects-e2dcc34c.vercel.app`
  - created Ready Public deployment `dpl_96RhJfEm86ZYgLL7PWDZEK6oPLDP` with
    generated URL
    `switchabank-public-1cdzgkxm5-kevins-projects-e2dcc34c.vercel.app`
  - assigned `switchabank-api.vercel.app` and
    `switchabank-public.vercel.app` as stable project domains
  - after new-domain verification, removed the six legacy API/Public
    `bankompare-*` stable, team, and main-branch aliases with explicit Product
    Owner approval; historical generated deployments were not deleted
- Deployment handling:
  - the first two direct Public CLI deploy attempts failed before build because
    the project Git Root Directory `app/public` was applied relative to an
    already narrowed CLI upload; neither attempt changed Production
  - the successful Public deployment used Vercel's supported redeploy path from
    the prior Ready Production source, preserving the project Root Directory
    and applying the updated environment value
- Decision: `D-063`. The active operational identity is now SwitchaBank
  across project, deployment, stable domain, upstream origin, and CORS
  boundaries.
- Key files: Public env example, API/Public deployment READMEs, environment
  separation strategy, decision log, WBS, and journal.
- Verification:
  - API `https://switchabank-api.vercel.app/healthz`: HTTP 200 with
    `Access-Control-Allow-Origin: https://switchabank-public.vercel.app`
  - Public `https://switchabank-public.vercel.app/dashboard`: HTTP 200 with
    `SwitchaBank` and the compare-then-switch hero
  - Public same-origin countries BFF: HTTP 200 with CA 150 and US 21
  - Public same-origin CA product BFF: HTTP 200 with one requested item
  - Vercel alias listing contains the new SwitchaBank stable/team/main aliases
    and no `bankompare-*` alias
  - the removed legacy stable API and Public URLs both return HTTP 404
- Known issue: Vercel CLI `project list` still reports the removed legacy
  domains in its cached `Latest Production URL` column even though the alias
  list no longer contains them and live HTTP requests return 404. No additional
  Production redeploy was performed solely to refresh this display metadata.
- Boundaries: no historical deployment was deleted and no product data,
  database state, scheduler, collection, publication, API contract, or UI
  behavior changed.
