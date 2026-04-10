# TD Savings Source Inventory

Version: 1.0
Date: 2026-04-06
Status: Approved Baseline for WBS 1.8.1
Source Documents:
- `docs/02-requirements/scope-baseline.md`
- `docs/01-planning/plan.md`
- `docs/01-planning/WBS.md`
- `docs/03-design/domain-model-canonical-schema.md`
- `docs/03-design/workflow-state-ingestion-design.md`
- `docs/03-design/security-access-control-design.md`
- Official TD Canada Trust public pages and PDFs listed in Section 4

---

## 1. Purpose

이 문서는 Prototype 범위인 `TD Bank / Savings Accounts`에 대해 수집 대상 source를 공식 기준으로 고정한다.

목적:
- `1.8.2 backlog`, `1.8.3 acceptance`, `1.8.4 spike`가 같은 source set을 참조하도록 맞춘다.
- crawler safe fetch와 source registry seed를 구현 가능한 수준으로 좁힌다.
- HTML/PDF별 예상 필드와 위험도를 미리 분리해 parser 실험 범위를 줄인다.
- Prototype에서 어떤 source를 canonical로 보고 어떤 source를 보조 증빙으로 보는지 명확히 한다.

이 문서는 구현 코드를 정의하지 않으며, 실제 fetch/parse 성공 여부는 후속 spike에서 검증한다.

---

## 2. Scope Baseline

### 2.1 Included Scope

- 대상 기관: `TD Canada Trust`
- 대상 상품유형: `personal savings accounts`
- 대상 상품:
  - `TD Every Day Savings Account`
  - `TD ePremium Savings Account`
  - `TD Growth Savings Account`
- 대상 source language baseline: `English`
- 대상 source type: public HTML page, linked public PDF

### 2.2 Excluded Scope

- logged-in flow (`EasyWeb`, application wizard, authenticated open-account flow)
- personalized recommendation/discovery tool (`discovery.td.com`)
- promotion landing page
- compare tool page
- registered savings products (TFSA/RRSP/FHSA)
- chequing, GIC, U.S. banking, business banking
- French/Chinese locale mirror pages

### 2.3 Baseline Rules

1. Prototype source registry는 `www.td.com` public content만 seed로 사용한다.
2. product summary는 HTML detail page를 우선하고, fee/rate truth는 current fee/rate page와 governing PDF로 교차 검증한다.
3. source identity baseline은 `bank_code + normalized_source_url + source_type`를 따른다.
4. Prototype에서는 English public source만 등록하고, locale 확장은 후속 범위로 둔다.
5. promotion copy나 marketing banner는 canonical field source로 사용하지 않는다.

---

## 3. Source Selection Strategy

### 3.1 Canonical Source Layers

| Layer | Role | Rule |
|---|---|---|
| L1. Product Discovery | 상품 후보 발견 | savings list page에서 3개 대상 상품을 확정 |
| L2. Product Detail | 상품 설명/혜택/계정별 fee 요약 | 각 상품 detail page를 primary HTML source로 사용 |
| L3. Cross-Product Current Values | 현재 금리/수수료 비교 | rates page와 CAD savings fee page를 cross-check source로 사용 |
| L4. Governing Terms | 법적/운영상 상세 조건 | linked PDF를 canonical evidence source로 저장 |

### 3.2 Field Ownership by Source Type

- list/detail HTML:
  - `product_name`
  - `description_short`
  - `product_highlight_badge_code` 후보
  - `monthly_fee`
  - `withdrawal_limit_text`
  - `free transfer rule`
  - `eligibility_text`
  - `notes`
- current rates / fees HTML:
  - `public_display_rate`
  - `standard_rate`
  - `promotional_rate` 또는 boosted rate
  - `tier_definition_text`
  - `monthly_fee`
  - `included_transactions`
  - `transaction_fee`
- governing PDF:
  - `interest_calculation_method`
  - `interest_payment_frequency`
  - `tier_definition_text`
  - `fee_waiver_condition`
  - `eligibility_text`
  - `account/service legal constraints`
  - `effective date`

---

## 4. Inventory

### 4.1 P0 Seed Sources

| ID | Priority | Source Type | Purpose | URL | Expected Fields | Risk |
|---|---|---|---|---|---|---|
| TD-SAV-001 | P0 | HTML list | prototype 대상 상품 3종 seed, product discovery | `https://www.td.com/ca/en/personal-banking/products/bank-accounts/savings-accounts` | product name, short summary, monthly fee, high-level transfer/rate messaging, product detail links | Medium: marketing layout drift 가능, but seed 역할은 안정적 |
| TD-SAV-002 | P0 | HTML detail | `TD Every Day Savings` primary detail source | `https://www.td.com/ca/en/personal-banking/products/bank-accounts/savings-accounts/every-day-savings-account` | product_name, description_short, monthly_fee, included_transactions, additional_transaction_fee, transfer_rule, atm fees, paper_statement_fee | Medium: footnote 구조와 CTA 블록이 섞여 parser noise 발생 가능 |
| TD-SAV-003 | P0 | HTML detail | `TD ePremium Savings` primary detail source | `https://www.td.com/ca/en/personal-banking/products/bank-accounts/savings-accounts/epremium-savings-account` | product_name, description_short, monthly_fee, transaction_fee, free_online_transfers, atm fees, balance threshold summary | Medium: rate threshold 설명과 marketing copy가 혼합됨 |
| TD-SAV-004 | P0 | HTML detail | `TD Growth Savings` primary detail source | `https://www.td.com/ca/en/personal-banking/products/bank-accounts/savings-accounts/growth-savings-account` | product_name, description_short, monthly_fee, transaction_fee, boosted_rate_eligibility, qualifying transaction rules, tier summary | High: boosted-rate 조건이 길고 cross-product dependency를 포함 |
| TD-SAV-005 | P0 | HTML rates | current interest rate truth and tier values | `https://www.td.com/ca/en/personal-banking/products/bank-accounts/account-rates` | public_display_rate, standard_rate, boosted_rate, rate tiers, rate-as-of marker | High: dynamic current values라 change frequency 높음 |
| TD-SAV-006 | P0 | HTML fee summary | cross-product fee 비교와 fee normalization | `https://www.td.com/ca/en/personal-banking/products/bank-accounts-fees-services-charges-cad-savings` | monthly transaction limit, transaction fee, bill payment fee, atm fees, transfer exceptions | Medium: summary page라 일부 상세 조건이 생략될 수 있음 |
| TD-SAV-007 | P0 | PDF terms/fees | account/service fee의 canonical governing document | `https://www.td.com/content/dam/tdct/document/pdf/personal-banking/513796-en.pdf` | effective_date, account lineup, detailed account fees, service fees, paper statement fee, transaction definitions, fee applicability | Medium: PDF table parsing complexity, but legal baseline로 중요 |
| TD-SAV-008 | P0 | PDF interest | interest calculation and tier rule의 canonical governing document | `https://www.td.com/content/dam/tdct/document/pdf/personal-banking/513782-en.pdf` | interest_calculation_method, interest_payment_frequency, tier_definition_text, account-specific rate table logic | Medium: PDF row grouping과 tier parsing 난이도 존재 |

### 4.2 P1 Supporting Evidence Sources

| ID | Priority | Source Type | Purpose | URL | Expected Fields | Risk |
|---|---|---|---|---|---|---|
| TD-SAV-009 | P1 | PDF terms | account-level general legal terms | `https://www.td.com/content/dam/tdct/document/pdf/personal-banking/tdct-accounts-fst-en.pdf` | record availability, account change rules, liability, interest applicability references, contact/escalation info | Low: product attribute source라기보다 governance/support evidence |
| TD-SAV-010 | P1 | PDF compliance | account opening / basic banking access evidence | `https://www.td.com/content/dam/tdct/document/pdf/personal-banking/522050-en.pdf` | account opening requirements, refusal grounds, compliance notes | Low: onboarding/compliance evidence only, product normalization 직접도 낮음 |
| TD-SAV-011 | P1 | PDF agreement | access card / credentials / service access terms | `https://www.td.com/content/dam/tdct/document/pdf/aa-eng.pdf` | service access terms, credential usage, card/service constraints | Low: savings product core field에는 직접 영향이 작음 |
| TD-SAV-012 | P1 | PDF fee supplement | general service fee supplement evidence | `https://www.td.com/content/dam/tdct/document/pdf/personal-banking/802234-en.pdf` | ancillary service fees, service definitions, non-core fees | Medium: title/section 구조가 넓어 필요한 field가 흩어져 있을 수 있음 |

---

## 5. Crawl and Registry Baseline

### 5.1 Allowed Domains

- `www.td.com`

### 5.2 Initial Registry Seed

Prototype의 초기 source registry에는 Section 4의 12개 source만 수동 등록한다.

등록 metadata 최소값:
- `bank_code = TD`
- `country_code = CA`
- `product_type = savings`
- `source_language = en`
- `source_type = html | pdf`
- `seed_source_flag`
- `priority = P0 | P1`

### 5.3 Discovery Rules

1. `TD-SAV-001`을 entry page로 등록한다.
2. list/detail page에서 발견되는 target savings detail URL 3종만 허용한다.
3. detail/fee page에서 노출되는 linked PDF는 Section 4 등록 목록과 일치할 때만 source로 채택한다.
4. query string, tracking parameter, trailing slash 차이는 normalized URL 기준으로 dedupe한다.
5. promotion page, compare tool, authenticated flow, cross-domain link는 warning만 남기고 registry에 자동 추가하지 않는다.

Note:
- as of `2026-04-09`, TD live pages expose `TD-SAV-007` with the detail-page URL `https://www.td.com/content/dam/tdct/document/pdf/personal-banking/513796-en.pdf`
- the fee summary page also exposes a second live download path `https://www.td.com/content/dam/tdct/document/pdf/econsent/accounts/513796.pdf`
- the prototype registry now treats the detail-page URL as the canonical `TD-SAV-007` seed, and the alternate fee-summary path stays outside the 12-source baseline unless alias handling is explicitly added later

---

## 6. Expected Prototype Extraction Set

`1.8.4 spike`에서는 아래 필드를 우선 실험 대상으로 본다.

### 6.1 Product Core

- `product_name`
- `product_type = savings`
- `subtype_code`
- `description_short`
- `source_language`
- `currency = CAD`

### 6.2 Savings Financials

- `monthly_fee`
- `included_transactions`
- `withdrawal_limit_text`
- `transaction_fee`
- `public_display_rate`
- `standard_rate`
- `minimum_balance`
- `tiered_rate_flag`
- `tier_definition_text`
- `interest_calculation_method`
- `interest_payment_frequency`

### 6.3 Eligibility and Notes

- `eligibility_text`
- `fee_waiver_condition`
- `registered_flag`
- `notes`

### 6.4 Special Handling

- `TD Growth Savings`는 `boosted_rate_eligibility`, `qualifying transaction rule`, `cross-product dependency`를 별도 note/evidence linkage로 우선 보관한다.
- paper statement fee, ATM fee, bill payment fee는 canonical core보다는 `notes` 또는 ancillary fee evidence 후보로 본다.

---

## 7. Risks and Follow-on Implications

### 7.1 Main Risks

| Risk | Severity | Why It Matters | Next Step |
|---|---|---|---|
| HTML marketing layout drift | Medium | parser가 CTA/FAQ/legal section을 함께 잡을 수 있음 | detail page section anchor와 heading-aware parsing 실험 |
| PDF table parsing complexity | High | fee/rate truth가 PDF 표에 있어 row merge 오류 가능 | snapshot + parsed text + page anchor 동시 저장 |
| Dynamic current rate changes | High | rate page 값이 자주 바뀌어 snapshot timing이 중요 | rate snapshot timestamp와 evidence linkage 필수 |
| Boosted-rate cross-product logic | High | Growth account는 chequing dependency가 있어 단순 savings parser로 누락될 수 있음 | special-case extraction rule 또는 manual review fallback |
| Promotional copy contamination | Medium | marketing 문구가 canonical notes를 오염시킬 수 있음 | promotion/offer section은 extraction scope에서 제외 |

### 7.2 Inventory-Based Conclusions

1. TD Savings는 Prototype용으로 `상품 list + detail + current values + governing PDF` 구조를 충분히 제공한다.
2. 다만 parser 난이도는 `TD Growth Savings`와 PDF table parsing에서 집중될 가능성이 높다.
3. 따라서 Prototype acceptance는 `모든 source 완전 자동화`가 아니라 `핵심 field extraction + evidence trace + review fallback` 기준으로 잡는 것이 맞다.

### 7.3 Follow-on WBS Mapping

- `1.8.2`: backlog는 Section 4의 source group과 Section 6의 extraction set을 기준으로 `docs/01-planning/prototype-backlog.md`에서 분해한다.
- `1.8.3`: acceptance는 Section 7 risk와 conclusions를 기준으로 `docs/01-planning/prototype-acceptance-checklist.md`에서 작성한다.
- `1.8.4`: spike는 `TD-SAV-004`, `TD-SAV-007`, `TD-SAV-008`를 우선 실험 대상으로 두고 `docs/01-planning/prototype-spike-scope.md`에서 종료 조건을 정의한다.
