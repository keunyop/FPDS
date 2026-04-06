# FPDS Product-Type Visualization Principles

Version: 1.0
Date: 2026-04-05
Status: Approved Baseline for WBS 1.7.3
Source Documents:
- `docs/02-requirements/FPDS_Requirements_Definition_v1_5.md`
- `docs/01-planning/WBS.md`
- `docs/03-design/product-grid-information-architecture.md`
- `docs/03-design/insight-dashboard-metric-definition.md`
- `docs/03-design/api-interface-contracts.md`
- `docs/03-design/domain-model-canonical-schema.md`
- `docs/00-governance/decision-log.md`

---

## 1. Purpose

이 문서는 `WBS 1.7.3 product-type별 시각화 원칙 확정`의 기준 문서다.

목적:
- `chequing`, `savings`, `gic`별 기본 비교 시각화와 강조 포인트를 고정한다.
- 어떤 product type에서 어떤 ranking/scatter가 기본이어야 하는지 닫는다.
- 의미가 맞지 않는 cross-type 비교나 synthetic metric 생성을 막는다.

---

## 2. Scope Boundary

이 문서는 아래를 결정한다.

- product type별 기본 dashboard 시각화 우선순위
- mixed-type scope에서의 시각화 원칙
- scatter preset의 기본 선택과 대체 노출 규칙
- Product Grid card의 product-type별 metric emphasis

이 문서는 아래를 결정하지 않는다.

- exact dashboard page layout choreography
- chart interaction이 Grid 상태에 반영되는 세부 클릭 규칙
- chart color palette, animation, microcopy wording detail

이 항목은 `5.10`, `5.11`, 그리고 `docs/03-design/localization-governance-and-fallback-policy.md`를 반영한 후속 구현/UX 설계에서 닫는다.

---

## 3. Baseline Decisions

1. Phase 1의 공식 active product type은 `chequing`, `savings`, `gic`다.
2. 시각화는 product type의 실제 비교 의미와 맞아야 하며, 의미가 맞지 않으면 노출하지 않는다.
3. KPI strip은 모든 product type에서 동일한 baseline을 유지한다.
4. ranking과 scatter는 `docs/03-design/insight-dashboard-metric-definition.md`의 공식 catalog 안에서만 선택한다.
5. Phase 1에서는 synthetic `convenience score`를 만들지 않는다.
6. `chequing` comparative chart는 `monthly fee`와 `minimum_balance`만 공식 비교축으로 사용한다.
7. mixed-type scope에서는 단일 scatter를 기본 비교 시각화로 삼지 않는다.

---

## 4. Route-State Visualization Rules

### 4.1 No Product Type Selected or Multiple Product Types Selected

기본 원칙:
- mixed-type scope는 상품군 의미가 달라 직접적인 scatter 비교를 기본값으로 삼지 않는다.
- 이 상태의 primary dashboard narrative는 market overview다.

기본 노출 우선순위:
1. headline KPI strip
2. `products_by_bank` breakdown
3. `products_by_product_type` breakdown
4. `highest_display_rate` ranking
5. `recently_changed_30d` ranking

규칙:
- `lowest_monthly_fee`와 `lowest_minimum_deposit`는 mixed-type 기본 노출 대상이 아니다.
- 사용자가 filter를 좁혀 단일 `product_type`만 남기면 해당 type의 default visualization으로 전환할 수 있다.
- mixed-type 상태에서는 "상품군별 비교 기준이 달라 세부 비교는 상품군 선택 후 제공"이라는 localized methodology note를 보여준다.

### 4.2 Exactly One Product Type Selected

기본 원칙:
- dashboard는 선택된 `product_type`의 비교 의미에 맞는 ranking/scatter를 우선 노출한다.
- chart title, axis label, methodology note는 type-specific wording을 사용한다.
- ranking widget은 최소 2개 노출을 우선하되, 의미 없는 widget은 억지로 채우지 않는다.

---

## 5. Product-Type-Specific Principles

### 5.1 Chequing

핵심 사용자 질문:
- 월 수수료가 얼마인지
- 수수료 면제 또는 유지 조건이 얼마나 빡빡한지
- 금리보다 비용/편의 관점에서 어떤 상품이 유리한지

기본 dashboard 우선순위:
1. `lowest_monthly_fee` ranking
2. `recently_changed_30d` ranking
3. `chequing_fee_vs_minimum_balance` scatter

조건부 노출:
- `highest_display_rate`는 `chequing` scope에서 non-null `public_display_rate`가 `3`개 이상일 때만 secondary widget으로 추가 노출할 수 있다.
- 이 widget은 interest-bearing subset insight로 취급하며 chequing의 primary narrative가 아니다.

comparative chart 원칙:
- 기본 preset은 `chequing_fee_vs_minimum_balance`다.
- X축은 effective fee (`public_display_fee ?? monthly_fee`), Y축은 `minimum_balance`다.
- lower-left가 일반적으로 유리한 영역으로 읽히지만, 혜택/거래편의/fee waiver text까지 모두 대체하지는 못한다.

Product Grid card emphasis:
1. effective fee
2. minimum balance
3. fee waiver or recent change hint

보조 요소:
- `No Monthly Fee`, `Fee Waiver`, `Student`, `Newcomer` 성격의 badge/tag를 rate-first badge보다 우선한다.

### 5.2 Savings

핵심 사용자 질문:
- 현재 금리가 얼마나 높은지
- 높은 금리를 얻기 위해 요구되는 최소 잔액이 얼마나 되는지
- promo/high-interest 맥락이 있는지

기본 dashboard 우선순위:
1. `highest_display_rate` ranking
2. `recently_changed_30d` ranking
3. `savings_rate_vs_minimum_balance` scatter

comparative chart 원칙:
- 기본 preset은 `savings_rate_vs_minimum_balance`다.
- X축은 `minimum_balance`, Y축은 `public_display_rate`다.
- upper-left가 일반적으로 더 유리한 영역으로 읽힌다.
- promo/tier 조건은 scatter point 하나만으로 완전히 설명되지 않으므로 methodology note와 card summary가 이를 보완한다.

Product Grid card emphasis:
1. display rate
2. minimum balance
3. promo/high-interest hint or recent change hint

### 5.3 GIC

핵심 사용자 질문:
- 현재 금리가 얼마나 높은지
- 진입 최소예치금이 얼마나 되는지
- 가입기간과 금리 사이 trade-off가 어떤지

기본 dashboard 우선순위:
1. `highest_display_rate` ranking
2. `lowest_minimum_deposit` ranking
3. `gic_rate_vs_minimum_deposit` scatter

alternate comparative chart:
- `gic_term_vs_rate`는 secondary comparative preset으로 제공한다.
- 기본 노출은 아니지만, 사용자가 term trade-off를 보고자 할 때 전환 가능한 공식 preset이다.

comparative chart 원칙:
- 기본 preset `gic_rate_vs_minimum_deposit`의 X축은 `minimum_deposit`, Y축은 `public_display_rate`다.
- 이 chart에서는 upper-left가 일반적으로 더 유리한 영역으로 읽힌다.
- `gic_term_vs_rate`에서는 long term이 자동으로 더 낫다는 뜻이 아니므로 "best quadrant"를 암시하지 않는다.

Product Grid card emphasis:
1. display rate
2. term length
3. minimum deposit

---

## 6. Scatter and Fallback Rules

1. scatter preset은 `docs/03-design/insight-dashboard-metric-definition.md`의 eligibility rule을 그대로 따른다.
2. 선택된 type의 default scatter에서 eligible point가 `3`개 미만이면 scatter는 숨기고 localized insufficiency note를 노출한다.
3. Phase 1에서는 scatter 부족을 메우기 위해 synthetic score, composite convenience metric, unsupported chart contract를 추가하지 않는다.
4. 이 경우 dashboard는 KPI + composition + eligible ranking widget 중심으로 유지한다.
5. mixed-type scope에서는 단일 scatter를 자동 선택하지 않는다.
6. `gic`만 공식 alternate scatter preset을 가진다.

---

## 7. Ranking Emphasis Matrix

| Scope | Primary Widget | Secondary Widget | Optional Additional Widget | Comparative Chart |
|---|---|---|---|---|
| mixed-type / all-types | `highest_display_rate` | `recently_changed_30d` | none by default | none by default |
| `chequing` | `lowest_monthly_fee` | `recently_changed_30d` | `highest_display_rate` if interest-bearing subset is eligible | `chequing_fee_vs_minimum_balance` |
| `savings` | `highest_display_rate` | `recently_changed_30d` | none by default | `savings_rate_vs_minimum_balance` |
| `gic` | `highest_display_rate` | `lowest_minimum_deposit` | `recently_changed_30d` | `gic_rate_vs_minimum_deposit` with `gic_term_vs_rate` as alternate |

이 matrix는 UI-level default emphasis를 정의한다.  
ranking catalog 자체는 `docs/03-design/insight-dashboard-metric-definition.md` 기준을 유지한다.

---

## 8. Product Grid Alignment

`1.7.1`에서 Grid card는 최대 3개의 핵심 수치를 노출하도록 고정되었다.  
`1.7.3`은 그 우선순위를 아래처럼 닫는다.

- `chequing`: fee -> minimum balance -> fee waiver/recent change
- `savings`: display rate -> minimum balance -> promo/high-interest hint
- `gic`: display rate -> term length -> minimum deposit

규칙:
- source-derived 상품명/조건 텍스트는 번역하지 않는다.
- product type label, chart title, methodology note, axis label은 locale-aware resource로 제공한다.
- card와 dashboard는 같은 product-type meaning을 공유해야 한다.

---

## 9. API and Aggregate Alignment

이 문서는 새 API endpoint를 요구하지 않는다.

필요한 기존 계약:
- `GET /api/public/dashboard-summary`
- `GET /api/public/dashboard-rankings`
- `GET /api/public/dashboard-scatter`
- `dashboard_metric_snapshot`
- `dashboard_ranking_snapshot`
- `dashboard_scatter_snapshot`

UI 규칙:
- 단일 `product_type`가 선택되면 해당 type의 default comparative preset을 우선 요청한다.
- `gic`에서는 `gic_rate_vs_minimum_deposit`를 기본으로 요청하고, 사용자가 alternate chart를 선택하면 `gic_term_vs_rate`로 전환한다.
- mixed-type scope에서는 scatter request를 기본 호출하지 않아도 된다.

---

## 10. Follow-On Work Unlocked

- `5.9`: Product Grid UI 구현
- `5.10`: Insight Dashboard UI 구현
- `5.11`: grid/dashboard cross-filter 적용
- `5.13`: methodology/freshness note 렌더링
- `5.14`: responsive QA 수행
