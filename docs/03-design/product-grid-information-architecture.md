# FPDS Product Grid Information Architecture

Version: 1.0
Date: 2026-04-05
Status: Approved Baseline for WBS 1.7.1
Source Documents:
- `docs/02-requirements/FPDS_Requirements_Definition_v1_5.md`
- `docs/01-planning/WBS.md`
- `docs/02-requirements/scope-baseline.md`
- `docs/03-design/api-interface-contracts.md`
- `docs/03-design/aggregate-cache-refresh-strategy.md`
- `docs/03-design/domain-model-canonical-schema.md`
- `docs/00-governance/decision-log.md`

---

## 1. Purpose

이 문서는 `WBS 1.7.1 Product Grid 정보 구조 설계`의 기준 문서다.

목적:
- Public Product Grid의 화면 구조와 정보 우선순위를 고정한다.
- card field, filter bar, sort, loading/empty state를 구현 전 vocabulary로 정리한다.
- public products API, filters API, aggregate projection, i18n, responsive QA가 같은 UI vocabulary를 참조하도록 만든다.

dashboard KPI formula, ranking semantics, scatter preset은 `docs/03-design/insight-dashboard-metric-definition.md`에서 닫고, product-type별 visualization emphasis는 `docs/03-design/product-type-visualization-principles.md`에서 닫는다.

---

## 2. Baseline Decisions

1. public surface는 Product Grid와 Insight Dashboard를 함께 포함한다.
2. public surface는 anonymous read 기준이다.
3. Product Grid와 Insight Dashboard는 shared filter vocabulary를 사용한다.
4. source-derived product text는 번역하지 않고 source language 값을 유지한다.
5. public surface는 evidence trace와 raw artifact를 노출하지 않는다.

---

## 3. Page Structure

Product Grid page baseline:

1. page heading / short scope note
2. sticky filter bar
3. result summary row
4. sort / clear filter toolbar
5. product card grid
6. pagination
7. dashboard로 이동 가능한 sibling navigation

---

## 4. Filter Bar Baseline

### 4.1 Primary Filters

- `bank`
- `product_type`
- `target_customer_tag`

### 4.2 Secondary Filters

- `fee_bucket`
- `minimum_balance_bucket`
- `minimum_deposit_bucket`
- `term_bucket`

규칙:
- active chip은 filter bar 또는 summary row에서 항상 보인다.
- `term_bucket`은 `gic` 맥락에서만 노출한다.
- `minimum_deposit_bucket`은 `gic` 우선, `minimum_balance_bucket`은 `chequing/savings` 우선이다.

---

## 5. Result Summary Row

result summary row는 아래 정보를 포함한다.

- result count
- active filter 요약
- latest freshness note
- clear filters action
- dashboard sibling entry

이 row는 dashboard KPI card를 대체하지 않는다.
grid summary는 탐색 상태 요약, dashboard metric은 시장 비교 요약으로 역할을 분리한다.

---

## 6. Sort Baseline

Phase 1 API sort baseline:

- relevance-like default aggregate order
- `display_rate desc`
- `monthly_fee asc`
- `minimum_balance asc`
- `minimum_deposit asc`
- `last_changed_at desc`

Phase 1 public Deposit catalog visible sort toolbar:

- default aggregate order
- `display_rate desc`
- `monthly_fee asc`
- `minimum_balance asc`

Numeric sort values must tolerate null, invalid, or non-finite source values without failing the public render; unavailable numeric values sort after valid values and serialize as `null`.

sort availability는 product type과 field completeness에 따라 제한될 수 있다.

---

## 7. Product Card Baseline

### 7.1 Card Header

- small locally served real bank logo with fixed dimensions
- bank name
- localized product type label
- product name
- product name links to `/products/[productId]` in the live public surface
- an optional official bank product-page action is shown when a single public `product_url` is available

### 7.2 Primary Metric Strip

카드에는 최대 3개의 핵심 수치만 노출한다.

우선순위 예시:
- `public_display_rate`
- `public_display_fee`
- `minimum_balance` or `minimum_deposit`
- `term_length_days` for `gic`

### 7.3 Supporting Elements

- highlight badge 1개
- target customer tag 최대 2개
- freshness / recent change hint

---

## 8. States

### 8.1 Loading

- filter skeleton
- summary row placeholder
- card skeleton grid

### 8.2 Empty / No Result

- current filter scope 안내
- clear all filters action
- dashboard 또는 retry-later guidance

---

## 9. Responsive Baseline

- desktop 우선 설계
- tablet에서는 card column 수를 줄인다
- mobile에서는 filter bar를 compact drawer 방식으로 축소할 수 있다
- 중요한 metric과 freshness 정보는 mobile에서도 유지한다

---

## 10. Relationship to Insight Dashboard

- Product Grid와 Insight Dashboard는 sibling public surfaces다.
- 사용자는 grid에서 insight로, insight에서 grid로 쉽게 이동할 수 있어야 한다.
- shared filter vocabulary는 동일하게 유지한다.
- exact click/state choreography는 `5.11`에서 결정한다.

---

## 10.5 Aggregate Bucket Baseline

### 10.6 Implemented Cross-Filter Baseline

- shared grid/dashboard state is carried in the URL query string using the approved shared public filter vocabulary
- sibling top navigation preserves shared scope, but does not carry Product Grid-only paging/sort state or Dashboard-only axis-preset state
- dashboard breakdown rows, ranking rows, and scatter points may drill back into the Product Grid with a narrower bank/product-type scope
- dashboard ranking product names may drill into `/products/[productId]`; the ranking header may still provide a Deposit/Product Grid `more` link
- when drill-in selects exactly one product type, bucket filters hidden for that type should be pruned before opening the Product Grid

### 10.7 Implemented Deposit Catalog Simplification

- Product Owner direction on `2026-05-21` removed the visible heading eyebrow, short scope note, home action, filter-card scope/freshness header, clear-all action, primary-filter helper copy, result-summary title, result count, and full-scope empty copy from `/products`.
- The filter form, active filter chips, sort controls, pagination, product-detail links, and locale-preserving query behavior remain in place.
- Official bank product-page actions should appear in the top-right of each product card when a public `product_url` is available.
- Product Owner follow-up on `2026-05-21` made the `/products` search-condition card collapsible and removed the product-card footer that showed `Changed` and `Verified` dates.
- Product Owner follow-up on `2026-05-21` refined the same Deposit catalog screen with denser filter controls and comparison-focused product cards. Product cards now prioritize user-relevant product metrics and avoid using repeated `Last change` tiles as filler metrics.
- Product Owner follow-up on `2026-05-22` moved public Deposit catalog sort controls below search conditions and above the product list, focusing the visible choices on interest rate, monthly fee, and minimum balance. Product cards and product detail now show compact bank brand marks.
- Product detail now shows a compact public disclosure note, an estimated-interest calculator, source-derived signup/application facts, and a period-by-rate table when approved aggregate metadata includes those rows.
- Product Owner follow-up on `2026-06-08` added a sort-aware Top 5 list above the product-card grid. The list uses the same public products API and current filter/sort scope, requesting page 1 with `page_size=5` without changing the API contract.
- Product Owner follow-up on `2026-06-08` simplified public bank branding: when a local bank logo is available, the public list and detail surfaces show the logo without a separate visible bank-name label or logo frame. Bank names remain available to assistive technology through the logo label and remain in API data.
- Product Owner follow-up on `2026-06-08` removed the product-detail Decision Summary card from the public surface while preserving official-bank, similar-product, calculator, product-fact, key-condition, term-rate, and disclosure sections.
- Product Owner follow-up on `2026-06-09` added a purpose-first entry pattern to `/products` so users can start from everyday cost, savings-rate, fixed-term return, or low-entry-amount comparison paths before refining filters.
- Product Owner follow-up on `2026-06-09` added a client-side comparison workspace to `/products`; users can select up to four products from the current result page and compare product, reason-to-compare, rate, monthly fee, entry amount, term, application method, and official bank page without changing the public API contract or exposing evidence data.
- Product Owner follow-up on `2026-06-11` removed the shared purpose-entry explanatory subtitle and compact trust cue block from the public surfaces while keeping the purpose entry cards and existing Product Grid filter/sort links.

### 10.8 Public Loan Catalog

- Product Owner direction on `2026-07-14` activates `/loans` as a sibling catalog to `/products`.
- `/loans` uses the same anonymous Public API, compact filters, sorting, comparison workspace, product detail route, locale handling, and public evidence boundary as the Deposit catalog.
- Its bounded Product Type scope is `mortgage`, `personal-loan`, and `line-of-credit`; Loan-specific cards prioritize rate, rate type, and term, while detail adds amortization, payment frequency, prepayment, and applicable lending conditions.
- The aggregate snapshot may include lending only from review-approved canonical products. Candidates, deferred products, and raw evidence remain unavailable to the Public surface.
- Deposit-only purpose cards and deposit amount/fee bucket controls are not shown in the Loan catalog.

### 10.8.1 Public Credit Card Catalog

- `/cards` uses annual fee and purchase APR as the minimum comparison facts and
  shares the anonymous Public API, comparison workspace, detail route, locale,
  and private-evidence boundary with the other catalogs.
- When an issuer discloses a purchase-APR range or qualification, comparison
  and detail retain the approved source-language summary. Per the later
  `2026-08-13` Product Owner direction in section 10.13, the list card presents
  the lowest explicit absolute purchase APR as its numeric Interest rate value.

### 10.9 Current Public Catalog Simplification

Product Owner direction on `2026-07-18` supersedes the earlier visible Top 5, repeated purpose-entry, hidden bank-name, and always-expanded comparison presentation decisions while preserving the API, canonical-data, locale, and evidence boundaries:

- Deposit and Loan catalog heroes expose only catalog identity, one short scope sentence, result count, and fixed-format freshness date.
- Search conditions are progressively disclosed and open automatically when filters are active. Deposit-only amount, fee, and term filters remain absent from Loan.
- Active scope and visible sort actions share one compact toolbar; the main result cards are the only catalog ranking/list presentation, so no duplicate Top 5 request or block is rendered.
- Each card exposes bank identity, product type, product name, one dominant type-aware metric, and at most two secondary facts. Visible bank names are retained because a remote or lazy logo alone is not a reliable identity cue.
- Cards expose Compare and Details. The official product-page action remains on detail and in the selected comparison, avoiding three competing actions on every list card.
- Before a selection, comparison is a compact count/control row. After selection, mobile comparison cards and a desktop comparison table expose only grounded public fields; the synthetic reason-to-compare field is removed.
- Product detail presents three primary facts, one available-facts section, applicable calculator or term-rate content, and one compact snapshot disclosure linked to Methodology. Recommendation-like `Best fit` language and duplicated key-condition summaries are not used.
- EN/KO/JA UI labels remain localized while source-derived product content remains in its source language.
- Production browser QA covers `1440px`, `768px`, and exact `390px` layouts for Home, Deposit, Loan, selected comparison, and product detail without horizontal document overflow.

### 10.10 Verified-Record Catalog Presentation

The Public design implementation completed on `2026-07-27` keeps the
`2026-07-18` information hierarchy and strengthens its financial-record
identity:

- The catalog hero states the exact Deposit or Loan coverage, visible result
  count, verification state, and snapshot date in one flat ledger composition.
- Product records use a family rail: evergreen for Deposit and ochre for Loan.
  Institution identity, product family, name, one primary fact, and no more than
  two supporting facts remain the scanning order.
- Filters, active scope, and sorting read as controls on one record set rather
  than separate dashboard widgets. Checkbox labels provide the full touch
  target, including at exact `390px`.
- Selecting up to four products opens one comparison ledger. Each fact becomes
  a responsive comparison row with one product cell per selection; two, three,
  and four selections use the corresponding number of columns where space
  allows and stack on mobile.
- Differing available values receive a quiet maple highlight. FPDS does not
  declare a winner, score suitability, estimate eligibility, or submit an
  application.
- Official-bank links belong to the selected comparison and detail page. Raw
  evidence links, source excerpts, reviewer state, and unapproved candidates
  remain private.
- Mobile sorting and dense term-rate data may use bounded internal horizontal
  scrolling. The document itself must not overflow horizontally.
- Loading, unavailable/error, no-result, no-selection, stale, fresh, and
  unavailable-value states use the same typography, border, and semantic-color
  vocabulary.
- EN, KO, and JA labels may wrap without clipping. Source-derived bank and
  product content remains in its source language.

The shared public aggregate vocabulary uses the following approved bucket boundaries:

- `fee_bucket`: `free` for `<= 0 CAD`, `low_fee` for `< 15 CAD`, `high_fee` for `>= 15 CAD`
- `minimum_balance_bucket`: `none` for `<= 0 CAD`, `under_1000` for `< 1000 CAD`, `from_1000_to_4999` for `1000-4999.99 CAD`, `5000_plus` for `>= 5000 CAD`
- `minimum_deposit_bucket`: `none` for `<= 0 CAD`, `under_500` for `< 500 CAD`, `from_500_to_4999` for `500-4999.99 CAD`, `5000_plus` for `>= 5000 CAD`
- `term_bucket`: `under_1y` for `< 365 days`, `from_1y_to_3y` for `365-1095 days`, `over_3y` for `> 1095 days`

These boundaries are the baseline for `5.6` aggregate projection generation and the shared filter vocabulary used by the later grid and dashboard APIs.

### 10.11 Country Selection And Global Readiness

- Public header utility space is reserved for country selection; language
  selection lives in the footer.
- The selector lists only countries represented by active products in their
  latest completed public snapshot. Current data therefore exposes Canada
  without suggesting unavailable worldwide coverage.
- Country names are localized from ISO region codes at the UI boundary. Flags
  and IP/browser geolocation are not used.
- `CA` is the clean-URL default. Other two-letter country codes persist through
  Home, Deposit, Loan, detail, and Methodology navigation.
- Changing country clears bank, product, bucket, axis, sort, and pagination
  state so country-owned codes cannot leak into the next market.
- Direct URLs for a valid but unavailable country render the existing honest
  unavailable/empty state.

### 10.12 Public Credit Card Catalog

- `/cards` is a sibling catalog to Deposit and Loan and uses the same country,
  locale, anonymous API, compact filters, result count, freshness, comparison,
  and shared `/products/[productId]` detail boundary.
- Only review-approved, active `credit-card` projections whose resolved market
  profile contains both annual fee and purchase interest rate are shown.
- Card list, comparison, and detail prioritize those two essentials. Annual fee
  is a sort option; missing or ungrounded legacy card facts remain private
  rather than rendering an unavailable placeholder.
- The surface remains factual and non-recommendatory and never exposes raw
  evidence, Review state, or internal traces.

### 10.13 Numeric Public Card Rate

Product Owner direction on `2026-08-13` supersedes earlier list-card prose
rules while preserving evidence and detail completeness:

- Deposit cards keep their approved `public_display_rate` semantics.
- Lending and Credit Card list cards show only a numeric Interest rate value.
  When approved data contains an explicit rate range, the card uses its lowest
  disclosed absolute rate; an explicit introductory APR is eligible because it
  is the customer-favorable currently disclosed value.
- The card projection ignores down-payment, discount, fee, LTV/CLTV, cap, and
  reference-rate component percentages. A formula such as `Prime + 2%` remains
  unavailable unless an explicit resulting absolute rate is also present.
- Comparison and product detail retain the complete source-language rate/APR
  summary and its qualifications. The numeric card value is not a replacement
  for canonical rate facts or evidence.
- `display_rate` sorting uses the same numeric value rendered on cards. The
  derivation runs from the current approved Public projection and does not
  initiate recollection, Review, or canonical mutation.

### 10.14 Launch Brand, Home, and Catalog Action Simplification

Product Owner direction on `2026-08-14` establishes the launch presentation:

- `BankingFacts` is the customer-facing Public name and `.com`-compatible brand
  label. FPDS remains the internal platform name. The same code-native
  list/check mark is used in the shell and favicon.
- Home removes `Products by bank`, the provenance-step ledger, repeated
  coverage blocks, and deposit ranking cards. It keeps one concise thesis,
  current product/bank/freshness facts, direct catalog actions, and a Loan Top
  5 list.
- Loan Top 5 uses the existing Public products API, the current country/filter
  scope, Loan Product Types, `display_rate asc`, and `page_size=5`. It labels
  the list as the lowest disclosed numeric rates, excludes unavailable numeric
  values, and tells users to compare full conditions before applying.
- Catalog cards retain the comparison selector and internal product-name detail
  link. The former `Compare details` secondary action is replaced by an
  official bank-page action only when a public `product_url` exists. The link
  opens in a new tab with `noopener noreferrer`; no destination is fabricated.
- EN/KO/JA UI labels and metadata use the new customer brand while
  source-derived institution/product content remains in its source language.

### 10.15 BankTable Identity and Dual Home Ranking

Product Owner follow-up on `2026-08-14` supersedes the `BankingFacts` identity
and single Loan-list Home hierarchy in Section 10.14:

- `BankTable` is the customer-facing Public name. Its code-native mark is one
  rounded 2-by-2 comparison table with no check badge, secondary color, or
  decorative detail. The same geometry is used in the shell and favicon.
- Home presents two equal ranking regions. Deposit Top 5 occupies the left
  column and Loan Top 5 the right column at desktop; both stack into one column
  below the desktop breakpoint without document-level horizontal scrolling.
- Deposit Top 5 requests the bounded Deposit Product Types with
  `display_rate desc` and `page_size=5`. Loan Top 5 requests the bounded Loan
  Product Types with `display_rate asc` and `page_size=5`.
- Both lists omit unavailable numeric rates, retain source-derived bank and
  product names, link product names to internal detail, expose the official
  bank action only when `product_url` exists, and state that fees, terms,
  eligibility, and other conditions still require comparison.
- A failed list request renders a localized unavailable state rather than the
  no-eligible-product empty state. Summary failure continues to use the full
  Home unavailable state.
- This refinement does not restore Products by bank, provenance steps, legacy
  dashboard widgets, personalized ranking, or public evidence exposure.

### 10.16 Home Ranking Group and Action Refinement

Product Owner follow-up on `2026-08-14` refines the presentation and action
hierarchy without changing Section 10.15 ranking semantics:

- Each ranking region uses a family-specific top rail and quiet header tint,
  plus an explicit Deposit or Loan label and family icon. Color supports the
  distinction but is not its only cue.
- Header-level View all buttons are removed. A localized, text-style catalog
  link sits below each list with a `44px` minimum interaction target and a
  directional icon.
- Home row official-bank actions reuse the Product Grid card's exact text-link
  composition: label plus external-link icon, `target="_blank"`, and
  `rel="noopener noreferrer"`. They are not rendered as outline buttons.
- Product count, rate ordering, independent unavailable states, internal
  product-detail navigation, responsive stacking, and evidence/privacy
  boundaries remain unchanged.

### 10.17 Bankoompare Identity and Paired-Eye Mark

Product Owner direction on `2026-08-20` supersedes the earlier
customer-facing name in Section 10.15 without changing Home or catalog
behavior:

- `Bankoompare` is the customer-facing Public name; `FPDS` remains the internal
  platform/runtime identity.
- The paired `oo` is the defining brand feature. Two simple circular eyes look
  outward to represent scanning two sides of a bank-product comparison.
- The shell uses the paired-eye mark beside a wordmark whose `oo` receives the
  visual emphasis. The favicon uses the same eye positions and outward pupils
  on the existing evergreen field.
- The mark stays code-native, flat, legible at small sizes, and free of
  decorative illustration or motion.
- EN/KO/JA metadata and customer-facing brand references use `Bankoompare`.

### 10.18 Calm-Density and Centered-Eye Refinement

Product Owner direction on `2026-08-15`, refined on `2026-08-20`,
defines the Public visual and information hierarchy without changing approved
financial meaning:

- each pupil is centered in its circular eye, and the two outlined eyes keep a
  small visible gap; the shell mark grows from the earlier compact treatment
  and the desktop/tablet Bankoompare wordmark uses a
  stronger title scale. The wordmark remains hidden at exact `390px` so the
  mark, three primary navigation actions, and country control fit without
  overflow;
- Home removes repeated kicker/family/evidence explanations, keeps one concise
  thesis and compact snapshot facts, and gives the dual Top 5 regions more
  deliberate separation. Desktop ranking rows keep rate and official-bank
  action on one scan line; mobile rows stack them;
- catalog list cards show one primary metric and no more than two essential
  supporting facts. Optional customer tags and highlight badges remain
  available to comparison/detail but do not compete with list scanning;
- the selection bar states the selected count directly and removes decorative
  capacity indicators and repeated guidance;
- Korean prose uses word-preserving breaks, Japanese prose uses strict line
  breaking, and compact nav/filter/action/rate/freshness labels do not split
  internally. Bounded sort rails and data tables may scroll internally, but
  the document must not overflow;
- shared product formatting is owned by one Public presentation module so list,
  comparison, and detail do not drift in currency, rate, term, transaction,
  redeemability, or security wording;
- product/filter/detail reads revalidate after five minutes and aggregate
  summary/ranking/scatter reads after fifteen minutes, matching the approved
  cache-refresh strategy. The API timeout and localized unavailable states
  remain unchanged.

### 10.19 Bankoompare Discovery, Sort, and View Refinement

Product Owner direction on `2026-08-20` strengthens the customer-facing
comparison language and catalog browsing behavior:

- Bankoompare Home and catalog headlines, taglines, metadata, and supporting
  descriptions invite users to look into bank products and compare facts.
- Home owns only locale and country scope. It ignores bank, Product Type,
  customer-tag, amount, fee, term, sort, pagination, and catalog-view query
  state carried from Deposit, Credit Card, or Loan.
- Deposit opens with `display_rate desc`, Credit Card with
  `annual_fee asc`, and Loan with `display_rate asc`. Catalogs expose no
  separate Default sort action.
- The sort rail ends with accessible Grid and List icon controls. Grid keeps
  the existing type-aware product cards; List uses compact rows whose active
  sort value is the dominant fact while product detail, Compare, and available
  official-bank actions remain reachable.
- Catalog view mode is URL state and remains stable when the user changes
  filters, sort, or pagination. Mobile keeps the sort/view rail internally
  scrollable without widening the document.

### 10.20 Instant Catalog Search, Continuous Loading, and Information Notice

Product Owner direction on 2026-08-20 supersedes the visible catalog
pagination behavior in Section 10.19:

- Deposit, Credit Card, and Loan Search conditions start with one localized
  text field. The q value matches the public bank name or source-derived
  product name case-insensitively as a literal substring; wildcard characters
  have no special meaning and no private evidence is searched.
- Text input uses a short debounce. Search, bank/Product Type/tag checkboxes,
  and applicable bucket selects immediately update URL-backed result state
  without an Apply button. Any condition change restarts at the first result
  page. Home still drops all catalog search/filter state.
- Catalogs server-render the first bounded API page. When an intersection
  sentinel approaches the viewport, the client requests the next page through
  a same-origin Public route, appends unseen product IDs, and repeats until
  has_next_page is false. Filter/sort changes abort stale requests and reset
  the list. Loading, completion, error, and retry states are localized and
  announced; Previous/Next controls are removed.
- Grid/List presentation and up-to-four comparison remain available as the
  list grows. View changes do not change the API scope, and additional-page
  loading does not alter canonical, aggregate, or ranking semantics.
- Home and every product detail use one EN/KO/JA information notice. It
  identifies AI-assisted public-source collection, the non-advertising and
  no-compensation boundary, best efforts to remain current, possible
  point-of-application changes, and the requirement to verify information and
  conditions on the institution's official website before applying.
- Raw evidence, Review state, personalized advice, scoring, and application
  submission remain outside Public.

### 10.21 Bankompare Identity and Comparison-Lens Mark

Product Owner direction on `2026-08-21` supersedes the Public name and mark in
Sections 10.17 and 10.18, plus the earlier brand reference in Section 10.19,
without changing any Home, catalog, comparison, localization, data, or
publication behavior:

- `Bankompare` is the customer-facing Public name; `FPDS` remains the internal
  platform/runtime identity.
- The defining brand feature is the name's single `o`. The code-native mark
  expresses it as one circular comparison lens split into two sides, with one
  record point on each side to represent side-by-side product comparison.
- The wordmark spells `Bankompare` exactly and emphasizes only that single
  `o`; the spelling is never extended to fit the mark.
- The shell mark and app icon share the same flat geometry. It remains legible
  at small sizes, conveys its two-sided structure without color, and uses no
  decorative illustration or motion.
- EN/KO/JA metadata, accessible brand labels, and customer-facing brand
  references use `Bankompare`. The compact-width rule continues to hide the
  wordmark while retaining the mark at exact `390px`.

### 10.22 Bankompare Monochrome Wordmark and Ledger-B Mark

Product Owner direction on `2026-08-22` supersedes only the comparison-lens
mark and single-letter wordmark emphasis in Section 10.21. The `Bankompare`
name and all existing product behavior remain unchanged:

- The wordmark renders `Bankompare` as one uninterrupted same-color word in
  each context. No letter, including `o`, receives a separate brand color or
  icon treatment.
- The code-native mark is a ledger `B`: two rounded comparison-record rows
  share one vertical spine, with one short data stroke inside each row. The
  silhouette communicates the brand initial first and the record-comparison
  idea second.
- The Public shell uses the outlined mark in its contextual foreground color;
  the app icon uses the same geometry in white on the established evergreen
  field. The mark does not reuse the rejected eye, lens, or generic table
  geometry.
- The exact-`390px` header remains mark-only. Accessible link naming,
  minimum-target sizing, EN/KO/JA behavior, and document-overflow rules remain
  unchanged.

### 10.23 Bankompare Global Product Globe Mark

Product Owner direction later on `2026-08-22` supersedes only the ledger-`B`
mark in Section 10.22. The `Bankompare` name and monochrome wordmark remain:

- The code-native mark is a minimal globe built from one circular boundary,
  one equator, and one closed meridian form. It stays recognizable in the
  32px shell treatment and in the 64px app-icon source without extra detail.
- The globe expresses the long-term goal of gathering comparable financial
  products across world markets. It is a direction signal, not a claim that
  unapproved countries are already collected or published.
- The shell uses the globe in its contextual foreground color. The favicon
  uses the same white geometry on the established evergreen field.
- The wordmark remains one uninterrupted same-color `Bankompare` text node.
  Exact-390px mark-only behavior, accessible naming, EN/KO/JA behavior, and
  document-overflow rules remain unchanged.

## 11. Follow-On Items

| Area | Follow-Up |
|---|---|
| Dashboard Metrics | `docs/03-design/insight-dashboard-metric-definition.md` |
| Visualization Rules | `docs/03-design/product-type-visualization-principles.md` |
| Cross-Filter Choreography | `5.11` completed baseline |
| Localization Ops | `docs/03-design/localization-governance-and-fallback-policy.md` |

---

## 12. Follow-On Work Unlocked

- `5.7`: public products API 구현
- `5.9`: Product Grid UI 구현
- `5.11`: grid/dashboard cross-filter 적용
- `5.14`: responsive QA refreshed on `2026-07-27` for the verified-record Public design
