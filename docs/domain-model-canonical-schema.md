# FPDS Domain Model and Canonical Schema v1

Version: 1.0  
Date: 2026-03-30  
Status: Approved Baseline for WBS 1.2.1 - 1.2.7  
Source Documents:
- `docs/FPDS_Requirements_Definition_v1_5.md`
- `docs/plan.md`
- `docs/WBS.md`
- `docs/scope-baseline.md`
- `docs/decision-log.md`
- `docs/raid-log.md`

---

## 1. Purpose

이 문서는 FPDS의 Domain Model과 canonical schema v1을 정의한다.

목적:
- Canada deposit taxonomy를 공식 기준으로 고정한다.
- Phase 1의 canonical product schema v1을 구현 가능한 수준으로 정의한다.
- source-derived 필드와 localized display resource의 경계를 고정한다.
- validation, confidence routing, change event 모델을 문서 기준으로 통일한다.
- Japan 확장 시 schema를 어떻게 유지/확장할지 메모를 남긴다.

이 문서는 WBS `1.2.1`부터 `1.2.7`까지의 공식 산출물이다.

---

## 2. Design Principles

1. canonical schema는 Phase 1에서는 Canada deposit product를 우선 지원한다.
2. schema 구조는 country/product expansion을 허용해야 하며, `product_type`과 `subtype_code`는 늘어나거나 변경될 수 있다.
3. `product_type`과 `subtype_code`는 고정 DB enum이 아니라 관리 가능한 code registry로 운영한다.
4. source-derived product data는 source language 단일 값으로 유지하고, UI 번역 리소스는 별도 관리한다.
5. validation과 confidence routing은 hard-coded 임계값이 아니라 정책 + 외부 설정값 기준으로 운영한다.
6. 핵심 필드는 evidence linkage와 review 가능성을 우선한다.

---

## 3. Taxonomy Model

### 3.1 Taxonomy Structure

FPDS taxonomy는 아래 5개 축으로 관리한다.

| Axis | Type | Description | Rule |
|---|---|---|---|
| `country_code` | string | 국가 코드 | ISO 3166-1 alpha-2 사용 |
| `product_family` | string code | 상위 상품군 | Phase 1 초기값은 `deposit`, 이후 확장 가능 |
| `product_type` | string code | 국가/상품군 내 canonical type | 관리형 code registry 사용, 하드코딩 enum 금지 |
| `subtype_code` | string code | `product_type` 하위 분류 | optional, 관리형 code registry 사용 |
| `source_subtype_label` | string | 원문 subtype 라벨 | source-derived 값 그대로 보존 |

### 3.2 Taxonomy Governance Rules

- `product_type`는 Phase 1에서 `chequing`, `savings`, `gic`를 공식 기준으로 사용한다.
- `subtype_code`는 `country_code + product_family + product_type` 기준 registry로 관리한다.
- 현재 registry에 맞지 않는 상품은 `subtype_code = other`로 수용하고 `source_subtype_label`을 반드시 보존한다.
- subtype이 실제로 늘어나야 할 경우 schema 변경이 아니라 taxonomy registry 변경으로 처리한다.
- `registered`, `student`, `newcomer`, `senior` 같은 분류는 subtype이 아니라 가능한 한 orthogonal attribute 또는 tag로 관리한다.

### 3.3 Canada Deposit Taxonomy v1

| product_type | subtype_code | Meaning | Notes |
|---|---|---|---|
| `chequing` | `standard` | 일반 수시 입출금 계좌 | 기본 chequing |
| `chequing` | `package` | 번들/패키지형 chequing | 혜택 묶음형 |
| `chequing` | `interest_bearing` | 이자 제공 chequing | displayed rate 존재 가능 |
| `chequing` | `premium` | premium tier chequing | 월 수수료/혜택 상위형 |
| `chequing` | `other` | 위 기준에 직접 맞지 않는 경우 | source label 보존 필수 |
| `savings` | `standard` | 일반 savings | 기본 savings |
| `savings` | `high_interest` | high-interest savings | HISA 포함 |
| `savings` | `youth` | youth/student oriented savings | target customer와 함께 해석 가능 |
| `savings` | `foreign_currency` | 외화 savings | 예: USD savings |
| `savings` | `other` | 위 기준에 직접 맞지 않는 경우 | source label 보존 필수 |
| `gic` | `redeemable` | 중도해지/현금화 가능 GIC | redeemable flag와 정합 |
| `gic` | `non_redeemable` | 만기 보유형 GIC | non-redeemable |
| `gic` | `market_linked` | 시장 연동형 GIC | market linked / index linked |
| `gic` | `other` | 위 기준에 직접 맞지 않는 경우 | source label 보존 필수 |

### 3.4 Orthogonal Attributes Outside Subtype

아래 속성은 subtype으로 고정하지 않고 별도 필드/flag/tag로 관리한다.

- `student_plan_flag`
- `newcomer_plan_flag`
- `registered_flag`
- `registered_plan_supported`
- `target_customer_tags`
- `currency`

이 원칙은 subtype explosion을 막고, country별 은행 상품을 더 안정적으로 수용하기 위한 것이다.

---

## 4. Canonical Schema v1

### 4.1 Record Types

`1.2` 범위에서 정의하는 핵심 record는 아래 4가지다.

| Record | Purpose |
|---|---|
| `canonical_product` | 검토/승인/게시 기준이 되는 정규화 상품 레코드 |
| `normalized_candidate` | extraction + normalization 결과로 생성되는 검토 대상 초안 |
| `field_evidence_link` | 각 필드가 어떤 evidence에서 왔는지 추적 |
| `change_event` | 상품 상태/분류/수동수정 변경 이력 |

### 4.2 Canonical Product Common Fields

| Field | Type | Required | Description |
|---|---|---:|---|
| `product_id` | UUID/string | O | canonical product identifier |
| `country_code` | string | O | `CA`, `JP` 등 |
| `bank_code` | string | O | canonical bank code |
| `bank_name` | string | O | canonical single display name |
| `product_family` | string code | O | Phase 1 초기값 `deposit` |
| `product_type` | string code | O | `chequing`, `savings`, `gic` 등 |
| `subtype_code` | string code | X | product-specific subtype |
| `source_subtype_label` | string | X | source-derived subtype label |
| `product_name` | string | O | source-derived single-language value |
| `source_language` | string | O | source language, unknown이면 `und` 허용 |
| `currency` | string | O | ISO 4217 currency code |
| `status` | enum | O | `active`, `inactive`, `discontinued`, `draft` |
| `target_customer_tags` | string array | X | normalized tags |
| `description_short` | text | X | source-derived short description |
| `public_display_rate` | decimal | X | public-facing snapshot rate |
| `public_display_fee` | decimal | X | public-facing snapshot fee |
| `product_highlight_badge_code` | string code | X | UI label mapping용 badge code |
| `effective_date` | date | X | source-effective date if available |
| `last_verified_at` | timestamp | O | last verification timestamp |
| `last_changed_at` | timestamp | X | latest detected change timestamp |
| `current_version_no` | integer | O | current version number |
| `created_at` | timestamp | O | record created time |
| `updated_at` | timestamp | O | record updated time |

### 4.3 Canonical Financial Fields

| Field | Type | Required | Description |
|---|---|---:|---|
| `monthly_fee` | decimal | X | monthly fee |
| `minimum_balance` | decimal | X | minimum balance |
| `minimum_deposit` | decimal | X | minimum deposit |
| `introductory_rate_flag` | boolean | X | introductory/promo indicator |
| `standard_rate` | decimal | X | standard rate |
| `promotional_rate` | decimal | X | promotional rate |
| `promotional_period_text` | string | X | promo period text |
| `term_length_text` | string | X | term text for GIC |
| `term_length_days` | integer | X | normalized term length if parseable |
| `fee_waiver_condition` | text | X | fee waiver rule |
| `eligibility_text` | text | X | eligibility text |
| `notes` | text | X | additional notes |

### 4.4 Product-Type Specific Fields

#### Chequing

- `included_transactions`
- `unlimited_transactions_flag`
- `interac_e_transfer_included`
- `overdraft_available`
- `cheque_book_info`
- `student_plan_flag`
- `newcomer_plan_flag`

#### Savings

- `interest_calculation_method`
- `interest_payment_frequency`
- `tiered_rate_flag`
- `tier_definition_text`
- `withdrawal_limit_text`
- `registered_flag`

#### GIC

- `redeemable_flag`
- `non_redeemable_flag`
- `compounding_frequency`
- `payout_option`
- `registered_plan_supported`

### 4.5 Candidate and Review Fields

| Field | Type | Required | Description |
|---|---|---:|---|
| `candidate_id` | UUID/string | O | normalized candidate identifier |
| `source_confidence` | number | O | 0~1 confidence score |
| `validation_status` | enum | O | `pass`, `warning`, `error` |
| `validation_issue_codes` | string array | X | validation issue list |
| `review_status` | enum | O | `queued`, `approved`, `rejected`, `edited`, `deferred` |
| `review_reason_code` | string code | X | review or override reason |
| `run_id` | UUID/string | O | producing run identifier |

### 4.6 Evidence Linkage Fields

| Field | Type | Required | Description |
|---|---|---:|---|
| `field_name` | string | O | linked canonical field |
| `candidate_value` | string/text | O | extracted or normalized value |
| `evidence_chunk_id` | UUID/string | O | source chunk reference |
| `evidence_text_excerpt` | text | O | excerpt shown in trace |
| `source_document_id` | UUID/string | O | source document reference |
| `citation_confidence` | number | O | evidence linkage confidence |

### 4.7 Source-Derived Field Policy

아래 필드는 source-derived 값으로 간주하고 locale별 복수 저장을 하지 않는다.

- `product_name`
- `description_short`
- `eligibility_text`
- `fee_waiver_condition`
- `notes`
- `source_subtype_label`

아래 리소스는 상품 레코드가 아니라 display/resource layer에서 EN/KO/JA로 관리한다.

- `product_type` display label
- `subtype_code` display label
- `status` label
- `product_highlight_badge_code` label
- methodology/help text

---

## 5. Validation Rules v1

### 5.1 Validation Severity Model

| Severity | Meaning | Routing Impact |
|---|---|---|
| `error` | canonical record로 사용 불가 | review 강제 |
| `warning` | 사용 가능하나 검토 권장 | policy/config에 따라 review |
| `info` | 참고용 | auto-approve 차단 없음 |

### 5.2 Core Field Rules

| Field Group | Rule | Severity |
|---|---|---|
| identity | `country_code`, `bank_code`, `product_family`, `product_type`, `product_name`, `currency`, `status`는 비어 있으면 안 됨 | error |
| taxonomy | `product_type`는 active taxonomy registry에서 resolve되어야 함 | error |
| subtype | `subtype_code`가 있으면 해당 `product_type` registry에서 유효해야 함 | error |
| language | `source_language`는 BCP-47 또는 ISO language code로 normalize되어야 함 | warning |
| timestamps | `last_verified_at`, `created_at`, `updated_at`는 timestamp여야 함 | error |

### 5.3 Financial Sanity Rules

| Field Group | Rule | Severity |
|---|---|---|
| rate | `standard_rate`, `promotional_rate`, `public_display_rate`는 0 이상 100 이하 decimal | error |
| fee | `monthly_fee`, `public_display_fee`는 0 이상 decimal | error |
| balance/deposit | `minimum_balance`, `minimum_deposit`는 0 이상 decimal | error |
| term | `term_length_days`는 1 이상 integer | error |
| promo | `promotional_rate`가 있으면 `introductory_rate_flag = true` 또는 promo 맥락이 설명 가능해야 함 | warning |

### 5.4 Product-Type Requiredness Rules

| product_type | Minimum Required Data | Severity if Missing |
|---|---|---|
| `chequing` | identity fields + `monthly_fee` 또는 `public_display_fee` 또는 `fee_waiver_condition` 중 하나 | error |
| `savings` | identity fields + `standard_rate` 또는 `promotional_rate` 또는 `public_display_rate` 중 하나 | error |
| `gic` | identity fields + rate field 1개 이상 + `term_length_text` 또는 `term_length_days` + `minimum_deposit` | error |

### 5.5 Cross-Field Rules

- `redeemable_flag`와 `non_redeemable_flag`는 동시에 `true`일 수 없다.
- `product_type = gic`인데 `minimum_balance`만 있고 `minimum_deposit`가 없으면 warning 또는 error 대상이다.
- `status = discontinued`이면 `last_changed_at`가 권장된다.
- source evidence가 2개 이상 충돌하면 `conflicting_evidence` issue를 남긴다.
- source parsing failure 이후 partial extraction이면 `partial_source_failure` issue를 남긴다.

### 5.6 Validation Issue Codes

- `required_field_missing`
- `invalid_taxonomy_code`
- `invalid_numeric_range`
- `invalid_term_value`
- `conflicting_evidence`
- `ambiguous_mapping`
- `partial_source_failure`
- `inconsistent_cross_field_logic`

---

## 6. Confidence Scoring and Review Routing

### 6.1 Confidence Inputs

`source_confidence`는 아래 신호를 종합해 산정한다.

- field completeness
- evidence coverage
- evidence conflict 여부
- parser reliability
- normalization certainty
- validation severity

### 6.2 Externalized Policy Rule

confidence 기준 점수는 고정 문서값이 아니라 외부 설정값으로 운영한다.

최소 필요 설정 예시:

| Config Key | Purpose |
|---|---|
| `AUTO_APPROVE_MIN_CONFIDENCE` | auto-approve 최소 confidence |
| `REVIEW_WARNING_CONFIDENCE_FLOOR` | warning 상태라도 review 없이 통과 가능한 하한선 |
| `FORCE_REVIEW_ISSUE_CODES` | score와 무관하게 review 강제하는 issue code 목록 |
| `DISCONTINUED_ABSENCE_RUN_THRESHOLD` | absence 기반 discontinued 판정 임계치 |

### 6.3 Baseline Routing Rule

#### Prototype

- Prototype에서는 `auto-approve`를 사용하지 않는다.
- 모든 candidate는 review 대상이다.

#### Phase 1

- `source_confidence >= AUTO_APPROVE_MIN_CONFIDENCE`
- `validation_status != error`
- `FORCE_REVIEW_ISSUE_CODES`에 해당하는 issue가 없음
- `conflicting_evidence` 없음

위 조건을 모두 만족할 때만 auto-approve 가능하다.  
그 외에는 review queue로 보낸다.

### 6.4 Default Baseline Recommendation

Phase 1 초기 권장값은 아래와 같다.

- `AUTO_APPROVE_MIN_CONFIDENCE = 0.95`
- `FORCE_REVIEW_ISSUE_CODES = required_field_missing, conflicting_evidence, ambiguous_mapping, invalid_numeric_range, partial_source_failure`

이 값은 운영 중 변경 가능하며, schema 문서 수정 없이 설정값으로 조정한다.

### 6.5 Queue Reason Codes

- `low_confidence`
- `required_field_missing`
- `conflicting_evidence`
- `ambiguous_mapping`
- `validation_error`
- `manual_sampling_review`
- `partial_source_failure`

---

## 7. Change Event Model

### 7.1 Event Types

| Event Type | Meaning | Trigger |
|---|---|---|
| `New` | 신규 canonical product 생성 | 이전 product 없음 |
| `Updated` | 동일 분류 내 주요 필드 변경 | price/rate/fee/balance/term/description 등 의미 있는 변경 |
| `Discontinued` | 상품 비활성/중단 | source 명시 또는 configured absence rule 충족 |
| `Reclassified` | `product_type` 또는 `subtype_code` 변경 | taxonomy remap 필요 |
| `ManualOverride` | 운영자 수동 수정 | review 승인/수정 과정에서 canonical field 변경 |

### 7.2 Event Boundary Rules

- `Updated`는 동일한 canonical 분류 안에서 필드 값이 바뀐 경우다.
- `Reclassified`는 상품 식별 continuity는 유지되지만 분류 체계가 바뀐 경우다.
- `ManualOverride`는 `Updated`와 별도 event로 남긴다.
- `ManualOverride`가 발생하면 change history와 audit log를 모두 남기는 것을 기본 원칙으로 한다.

### 7.3 Change Event Payload

| Field | Description |
|---|---|
| `change_event_id` | event identifier |
| `product_id` | affected product |
| `event_type` | change type |
| `previous_version_no` | previous version |
| `current_version_no` | current version |
| `changed_field_names` | changed field list |
| `event_reason_code` | reason code |
| `detected_at` | detection timestamp |
| `detected_by` | `system` or actor id |
| `run_id` | related run |
| `review_task_id` | related review task if any |
| `evidence_refs` | supporting evidence refs |

### 7.4 Change Reason Codes

- `source_content_changed`
- `taxonomy_reclassified`
- `manual_override`
- `status_discontinued`
- `absence_threshold_reached`

---

## 8. Japan Expansion Readiness Memo

### 8.1 Current Readiness

schema v1은 Japan 확장에 대해 아래 기준으로 충분히 확장 가능하다.

- `country_code`가 core field에 포함되어 있다.
- `product_type`와 `subtype_code`가 registry 기반이므로 국가별 확장이 가능하다.
- source-derived text와 localized display resource가 분리되어 있다.
- `source_language`를 별도 필드로 유지한다.

### 8.2 What Must Stay Core

- identity fields
- status/version timestamps
- review/validation/confidence fields
- evidence linkage model
- change event payload shape

### 8.3 What Can Expand by Locale

- `product_type` registry values
- `subtype_code` registry values
- display label translation resources
- locale-specific financial subtype fields

### 8.4 Caution Notes for Phase 2

- Japan 확장 시에도 core schema를 깨지 않고 registry/locale field extension으로 처리한다.
- Phase 2에서 deposit 외 family가 추가되면 `product_family` registry만 확장하고 common identity/review/evidence 구조는 유지한다.
- locale-specific subtype가 늘어나더라도 `source_subtype_label` 보존 원칙은 유지한다.

---

## 9. WBS Mapping

| WBS ID | Closure in This Document |
|---|---|
| 1.2.1 | Section 3 Taxonomy Model |
| 1.2.2 | Section 4 Canonical Schema v1 |
| 1.2.3 | Section 4.7 Source-Derived Field Policy |
| 1.2.4 | Section 5 Validation Rules v1 |
| 1.2.5 | Section 6 Confidence Scoring and Review Routing |
| 1.2.6 | Section 7 Change Event Model |
| 1.2.7 | Section 8 Japan Expansion Readiness Memo |

---

## 10. Change History

| Date | Change |
|---|---|
| 2026-03-30 | Initial domain model and canonical schema baseline created for WBS 1.2.1 - 1.2.7 |
