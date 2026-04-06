# FPDS Insight Dashboard Metric Definition

Version: 1.0
Date: 2026-04-05
Status: Approved Baseline for WBS 1.7.2
Source Documents:
- `docs/02-requirements/FPDS_Requirements_Definition_v1_5.md`
- `docs/01-planning/WBS.md`
- `docs/02-requirements/scope-baseline.md`
- `docs/03-design/api-interface-contracts.md`
- `docs/03-design/aggregate-cache-refresh-strategy.md`
- `docs/03-design/domain-model-canonical-schema.md`
- `docs/03-design/product-grid-information-architecture.md`
- `docs/00-governance/decision-log.md`

---

## 1. Purpose

This document closes `WBS 1.7.2 Insight Dashboard metric definition`.

Goals:
- define the public dashboard summary KPI baseline
- define ranking widget semantics and eligibility rules
- define scatter dataset preset vocabulary and axis meaning
- align aggregate snapshot, API contract, and public UI vocabulary before implementation

This is a design baseline, not an implementation start signal.  
Implementation still waits for `Gate A blocker closed + Product Owner explicit approval`.

---

## 2. Baseline Decisions Carried Forward

The dashboard metric baseline carries forward these prior decisions.

1. Phase 1 public experience includes both Product Grid and Insight Dashboard.
2. Dashboard responses use the latest successful aggregate snapshot, not live canonical reads.
3. Product Grid and Insight Dashboard share the same public filter vocabulary.
4. Localized labels/help/methodology use `en`, `ko`, `ja`, while source-derived product text remains in the source language.
5. Public dashboard metrics are derived only from public-facing canonical/aggregate fields and never expose evidence trace or raw source artifacts.
6. Phase 1 scope is Canada Big 5 deposit products with `chequing`, `savings`, and `gic` as the active canonical product types.
7. `recently_changed_products` uses a fixed trailing `30 day` window measured from aggregate `refreshed_at`.

---

## 3. Scope of 1.7.2

This document decides:
- headline KPI cards
- summary breakdown metrics for bank and product-type composition
- ranking widget catalog, ordering, and tie-break rules
- scatter dataset preset keys and axis meaning
- common eligibility, missing-data, freshness, and localization rules

This document does not decide:
- final chart placement/layout or exact page choreography
- exact click interaction between chart points/widgets and Product Grid state
- localization ownership workflow and glossary governance

Product-type-specific dashboard visual emphasis is closed by `docs/03-design/product-type-visualization-principles.md`.  
The remaining follow-on work is `5.10`, `5.11`, `1.7.5`, and `1.7.6`.

---

## 4. Shared Metric Rules

### 4.1 Scope and Eligibility Baseline

- All public dashboard metrics are computed from the latest successful aggregate snapshot for the applied filter scope.
- Filter scope matches the public grid/dashboard query vocabulary:
  - `country_code`
  - `bank_code`
  - `product_type`
  - `subtype_code`
  - `target_customer_tag`
  - `fee_bucket`
  - `minimum_balance_bucket`
  - `minimum_deposit_bucket`
  - `term_bucket`
- Public dashboard counts use distinct `product_id`.
- Only `status = active` products participate in public dashboard counts, rankings, and scatter points unless explicitly noted otherwise.

### 4.2 Numeric Field Usage Rules

- Rate-based metrics use `public_display_rate`.
- Fee-based metrics use `public_display_fee` if present; otherwise they fall back to `monthly_fee`.
- Deposit/balance metrics use canonical numeric fields directly:
  - `minimum_balance`
  - `minimum_deposit`
  - `term_length_days`
- No metric imputes missing numeric data.
- Any ranking or scatter preset that depends on a numeric field excludes products where that field is null.

### 4.3 Minimum Data Rule

- A ranking widget or scatter preset is considered display-eligible only when at least `3` products remain after applying scope and field eligibility rules.
- If fewer than `3` products are eligible, the API may return an empty dataset with a localized insufficiency note instead of forcing a misleading comparison.

### 4.4 Stable Ordering Rule

Unless a widget-specific secondary sort is defined, ties are broken by:
1. `bank_name` ascending
2. `product_name` ascending
3. `product_id` ascending

### 4.5 Freshness Rule

- All dashboard datasets use the same snapshot freshness object already defined for public aggregate APIs.
- `recently changed` calculations use the trailing `30` calendar days relative to aggregate `refreshed_at`, not browser time.

---

## 5. Dashboard Summary Metrics

### 5.1 Headline KPI Card Set

Phase 1 headline KPI cards are fixed to the following four metrics.

| `metric_key` | Definition | Formula Baseline | Unit | Scope Note Rule |
|---|---|---|---|---|
| `total_active_products` | total active products in current scope | count of distinct `product_id` where `status = active` | `count` | no extra scope note required |
| `banks_in_scope` | number of banks represented in current scope | count of distinct `bank_code` across active products | `count` | no extra scope note required |
| `highest_display_rate` | highest public display rate visible in scope | max `public_display_rate` across eligible active products | `percent` | note that products without display-rate data are excluded |
| `recently_changed_products_30d` | products changed during the trailing 30-day window | count of distinct `product_id` where `last_changed_at >= refreshed_at - 30 days` | `count` | note that the window is fixed at 30 days |

### 5.2 Composition Metrics in Summary Surface

The PRD mentions `products by bank` and `products by product type`.  
These are treated as summary breakdown datasets, not extra scalar KPI cards, because they are categorical composition views.

Required summary breakdowns:

| `breakdown_key` | Definition | Output Shape |
|---|---|---|
| `products_by_bank` | active products grouped by `bank_code` | `{ bank_code, bank_name, count, share_percent }[]` |
| `products_by_product_type` | active products grouped by `product_type` | `{ product_type, product_type_label, count, share_percent }[]` |

Rules:
- `share_percent` uses the current `total_active_products` denominator.
- breakdown ordering is `count desc`, then stable ordering by label/code.
- breakdowns count all active products in scope, even if some products lack rate/fee/balance fields.

---

## 6. Ranking Widget Catalog

### 6.1 Widget Catalog

Phase 1 ranking widgets are defined by the following canonical keys.

| `ranking_key` | Intent | Eligibility | Sort Order | Default `top_n` | Notes |
|---|---|---|---|---:|---|
| `highest_display_rate` | show highest current display-rate products | active products with non-null `public_display_rate` | `public_display_rate desc` | 5 | cross-type allowed; most useful for `savings`, `gic`, and interest-bearing `chequing` |
| `lowest_monthly_fee` | show lowest-fee chequing options | active `chequing` products with non-null effective fee (`public_display_fee ?? monthly_fee`) | effective fee `asc` | 5 | chequing-only |
| `lowest_minimum_deposit` | show lowest entry-deposit GIC options | active `gic` products with non-null `minimum_deposit` | `minimum_deposit asc`, then `public_display_rate desc` | 5 | gic-only |
| `recently_changed_30d` | show most recently changed products | active products with `last_changed_at >= refreshed_at - 30 days` | `last_changed_at desc` | 5 | fixed 30-day window |

### 6.2 Widget Rendering Priority

When no single `product_type` is selected, the public dashboard should attempt to render widgets in this priority order:
1. `highest_display_rate`
2. `recently_changed_30d`

Rules:
- render the first `2` eligible widgets in priority order
- if only `2` widgets are eligible, render `2`
- if fewer than `2` widgets are eligible, return the available widget plus a localized insufficiency note rather than fabricating comparison coverage
- `lowest_monthly_fee` and `lowest_minimum_deposit` remain valid catalog widgets but are not the mixed-type default exposure
- single-type visualization emphasis and default widget ordering are governed by `docs/03-design/product-type-visualization-principles.md`

### 6.3 Ranking Row Baseline

Each ranking row must expose:
- `rank`
- `product_id`
- `bank_code`
- `bank_name`
- `product_name`
- `product_type`
- `metric_value`
- `metric_unit`
- `last_changed_at`

`recently_changed_30d` also carries `window_days = 30` in widget metadata.

---

## 7. Scatter Dataset Baseline

### 7.1 Preset Catalog

The scatter dataset contract supports the following preset keys.

| `axis_preset` | Eligible Product Type | X Axis | Y Axis | Point Eligibility |
|---|---|---|---|---|
| `chequing_fee_vs_minimum_balance` | `chequing` | effective fee (`public_display_fee ?? monthly_fee`) | `minimum_balance` | both numeric fields present |
| `savings_rate_vs_minimum_balance` | `savings` | `minimum_balance` | `public_display_rate` | both numeric fields present |
| `gic_rate_vs_minimum_deposit` | `gic` | `minimum_deposit` | `public_display_rate` | both numeric fields present |
| `gic_term_vs_rate` | `gic` | `term_length_days` | `public_display_rate` | both numeric fields present |

This closes the metric-level meaning of the Phase 1 scatter presets.

### 7.2 Point Rules

- one point represents one active product snapshot
- point labels use canonical `bank_name` and source-derived `product_name`
- `highlight_badge_code` may be returned when a public badge exists
- no point includes evidence text, review metadata, or raw source references

### 7.3 Visualization Boundary

`1.7.2` freezes the metric meaning of the scatter presets above.  
`docs/03-design/product-type-visualization-principles.md` closes:
- which preset is the primary default per product type or route state
- when an alternate comparative chart is preferable to scatter because of sparse data or product semantics
- final visual wording and chart treatment per product type

---

## 8. Freshness and Methodology Note Baseline

Every public dashboard surface must support localized methodology/freshness notes that can explain at least:

1. metrics come from the latest successful aggregate snapshot
2. rates use the current `public_display_rate`
3. fee comparisons use `public_display_fee` with fallback to `monthly_fee`
4. `recently changed` means the trailing `30` days from snapshot refresh time
5. products missing required numeric fields are excluded from the affected ranking/scatter comparison
6. public dashboard does not expose evidence trace or source-document excerpts

---

## 9. Public API and Aggregate Alignment

This metric baseline requires the following API/aggregate alignment.

- `GET /api/public/dashboard-summary`
  - returns the exact four headline KPI cards above
  - returns `products_by_bank` and `products_by_product_type` breakdown datasets
- `GET /api/public/dashboard-rankings`
  - returns ranking widgets from the Section 6 catalog
- `GET /api/public/dashboard-scatter`
  - accepts only the Section 7 preset keys
- `dashboard_metric_snapshot`
  - stores headline KPI values plus summary breakdown datasets for the scoped snapshot
- `dashboard_ranking_snapshot`
  - stores widget rows keyed by `ranking_key`
- `dashboard_scatter_snapshot`
  - stores point sets keyed by `axis_preset`

---

## 10. Follow-On Work Unlocked

- `5.6`: build aggregate datasets using the fixed metric/ranking/preset vocabulary
- `5.8`: implement public dashboard APIs
- `5.10`: build public Insight Dashboard UI against a stable metric contract
- `5.11`: implement exact grid/dashboard cross-filter choreography
- `5.13`: render methodology/freshness note copy
