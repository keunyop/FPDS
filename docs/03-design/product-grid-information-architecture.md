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

The shared public aggregate vocabulary uses the following approved bucket boundaries:

- `fee_bucket`: `free` for `<= 0 CAD`, `low_fee` for `< 15 CAD`, `high_fee` for `>= 15 CAD`
- `minimum_balance_bucket`: `none` for `<= 0 CAD`, `under_1000` for `< 1000 CAD`, `from_1000_to_4999` for `1000-4999.99 CAD`, `5000_plus` for `>= 5000 CAD`
- `minimum_deposit_bucket`: `none` for `<= 0 CAD`, `under_500` for `< 500 CAD`, `from_500_to_4999` for `500-4999.99 CAD`, `5000_plus` for `>= 5000 CAD`
- `term_bucket`: `under_1y` for `< 365 days`, `from_1y_to_3y` for `365-1095 days`, `over_3y` for `> 1095 days`

These boundaries are the baseline for `5.6` aggregate projection generation and the shared filter vocabulary used by the later grid and dashboard APIs.

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
- `5.14`: responsive QA completed on `2026-07-18`
