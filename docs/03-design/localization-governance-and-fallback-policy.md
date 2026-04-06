# FPDS Localization Governance and Fallback Policy

Version: 1.0
Date: 2026-04-06
Status: Approved Baseline for WBS 1.7.5 - 1.7.7
Source Documents:
- `docs/02-requirements/FPDS_Requirements_Definition_v1_5.md`
- `docs/01-planning/WBS.md`
- `docs/02-requirements/scope-baseline.md`
- `docs/03-design/domain-model-canonical-schema.md`
- `docs/03-design/api-interface-contracts.md`
- `docs/03-design/product-grid-information-architecture.md`
- `docs/03-design/insight-dashboard-metric-definition.md`
- `docs/03-design/product-type-visualization-principles.md`
- `docs/03-design/admin-information-architecture.md`
- `docs/03-design/security-access-control-design.md`
- `docs/00-governance/decision-log.md`
- `docs/00-governance/raid-log.md`

---

## 1. Purpose

이 문서는 `WBS 1.7.5`, `1.7.6`, `1.7.7`의 기준 문서다.

목적:
- EN/KO/JA UI resource의 owner, authoring 흐름, review/approval 책임을 고정한다.
- locale fallback 순서와 source-derived text 처리 원칙을 public/admin/API vocabulary와 맞춘다.
- Japanese glossary의 scope, owner, change rule을 정의해 Phase 2 확장 전에 terminology drift를 줄인다.

이 문서는 구현 시작 신호가 아니다.  
구현은 `Gate A = Pass + Product Owner explicit approval` 이후에만 시작한다.

---

## 2. Baseline Decisions Carried Forward

1. Public/Admin UI는 `en`, `ko`, `ja`를 baseline locale로 지원한다.
2. `product_name`, `description_short`, `eligibility_text`, `fee_waiver_condition`, `notes`, `source_subtype_label`, evidence excerpt 같은 source-derived content는 locale별 복수 번역 필드로 관리하지 않는다.
3. locale은 label, help, methodology, status, badge, axis title, widget title 같은 display resource에만 영향을 준다.
4. admin/public/API contract에서 locale-aware control이 필요한 대상은 code-based label과 helper text이며, source language content 자체를 기계 번역해 덮어쓰지 않는다.
5. 현재 팀 baseline은 Product Owner + Codex 2인 체제이므로 localization governance는 named person이 아니라 role-based ownership으로 설계한다.
6. Phase 1 운영과 Phase 2 Japan 확장을 모두 고려하되, Japanese glossary는 현재 시점에서 "정책과 운영 모델"을 닫는 것이 목적이며 실제 대규모 용어집 구축 자체는 후속 운영으로 본다.

---

## 3. Scope of 1.7.5 - 1.7.7

이 문서는 아래를 결정한다.
- `1.7.5`: i18n resource ownership와 review/approval 방식
- `1.7.6`: locale fallback chain, non-translatable field policy, formatting fallback
- `1.7.7`: Japanese glossary owner, entry scope, maintenance rule
- admin localization health에서 추적해야 할 최소 운영 지표

이 문서는 아래를 결정하지 않는다.
- exact file/folder scaffold naming과 framework-specific i18n library 선택
- Japan Big 5별 actual source parsing prompt나 locale-aware extractor prompt 설계
- Phase 2 external API docs의 actual Japanese sentence set

---

## 4. Localization Boundary and Resource Classes

### 4.1 Default Resource Locale

`en`을 default resource locale로 고정한다.

이유:
- PRD가 fallback 예시에서 `English`를 우선 fallback으로 제시한다.
- Phase 1 public market scope가 Canada Big 5이므로 English baseline이 가장 자연스럽다.
- External API와 future public documentation도 English-first 확장이 더 단순하다.

이 결정은 문서 authoring 언어를 제한하지 않는다.  
하지만 persisted UI resource registry의 기준 locale과 fallback root는 `en`이다.

### 4.2 Localizable vs Non-Localizable Boundary

| Class | Localized by Resource | Why |
|---|---|---|
| navigation, menu, button, form label | O | UI chrome이기 때문이다 |
| filter label, sort label, empty-state copy | O | public/admin UX readability에 직접 영향 |
| product type / subtype / status / badge label | O | code-based display resource이기 때문이다 |
| chart title, axis label, methodology note, freshness note | O | public/admin metric interpretation에 필요 |
| admin widget title, validation issue display label, reason-code label | O | 운영 화면 readability에 필요 |
| bank brand name | X | 기관 고유명사이므로 번역하지 않는다 |
| product name | X | source-derived 상품명 그대로 유지 |
| description_short, notes, eligibility_text, fee_waiver_condition | X | source-derived 상품 조건이기 때문이다 |
| evidence excerpt, candidate value, source URL | X | trace integrity를 유지해야 하기 때문이다 |

### 4.3 Resource Domains

resource ownership은 아래 domain으로 구분한다.

| Domain | Examples |
|---|---|
| `public_navigation` | global nav, page heading, CTA |
| `public_filters` | filter/sort label, empty state, result summary |
| `public_metrics` | KPI, ranking title, chart label, methodology/freshness |
| `admin_operations` | queue, run, publish, usage, health label |
| `shared_taxonomy` | product type, subtype, status, badge, issue/reason label |
| `system_messages` | validation helper, degraded/fallback note |

---

## 5. I18n Resource Ownership and Workflow

### 5.1 Accountability Model

| Role | Responsibility |
|---|---|
| Product Owner | localization meaning owner, final approval owner, glossary dispute resolution |
| Frontend Engineer | resource key lifecycle, locale file maintenance, missing key detection, implementation steward |
| Domain Reviewer | 금융 용어, taxonomy label, methodology wording 검토가 필요한 경우 consult |
| QA / Reviewer | high-impact screen에서 locale rendering과 fallback behavior 검증 |

현재 팀 baseline에서는 별도 localization PM이나 dedicated translator를 두지 않는다.  
따라서 Product Owner가 의미 승인권을 가진다.

### 5.2 Resource-Class Ownership Matrix

| Resource Class | Draft Author | Review / Approval | Notes |
|---|---|---|---|
| public navigation / CTA / empty state | Product Owner | Product Owner final | Frontend는 key와 placement 관리 |
| public metric / methodology copy | Product Owner | Product Owner + Domain Reviewer consult | 숫자 의미 변경과 함께 검토 |
| admin operations copy | Product Owner | Product Owner final | ops vocabulary 일관성 우선 |
| taxonomy/status/badge/reason labels | Frontend initial registry + Product Owner wording | Product Owner final, Domain Reviewer consult when financial meaning changes | code-based label set |
| system fallback / degraded notes | Frontend | Product Owner final | implementation-safe text 필요 |
| Japanese glossary entry | Product Owner draft | Product Owner final, Domain Reviewer consult | `1.7.7` policy 대상 |

### 5.3 Workflow Baseline

모든 localizable resource는 아래 흐름을 따른다.

1. resource key 생성
2. `en` baseline copy 작성
3. `ko`, `ja` copy 작성 또는 pending 상태 기록
4. Product Owner review and approval
5. release candidate 반영

운영 규칙:
- 새로운 UI surface는 English baseline copy 없이 merge-ready 상태로 보지 않는다.
- `ko`, `ja`가 미완성일 경우에도 fallback policy가 정의돼 있으면 구현을 막지 않지만, missing 상태는 admin localization health에서 추적되어야 한다.
- 동일 의미를 가진 label은 새 key를 남발하지 않고 shared taxonomy/resource domain을 재사용한다.

### 5.4 Resource Status Baseline

resource 상태는 최소 아래 의미를 가져야 한다.

| Status | Meaning |
|---|---|
| `draft` | 작성 중, 사용자 노출 기준 미충족 |
| `approved` | fallback root 또는 locale target으로 사용자 노출 가능 |
| `deprecated` | 새 key/resource로 대체 예정, 신규 사용 금지 |

Phase 1 baseline에서는 `approved`만 public/admin 노출 대상으로 본다.  
`draft`는 내부 authoring 상태로만 유지한다.

### 5.5 Localization Health Visibility Baseline

PRD `FR-ADM-014`를 만족시키기 위해 admin localization health는 최소 아래를 추적할 수 있어야 한다.

- locale별 approved resource count
- locale별 missing resource count
- fallback hit count or equivalent indicator
- glossary-covered financial term count
- last reviewed at

exact admin route나 widget layout은 후속 구현에서 정하되, 위 지표 vocabulary는 지금 고정한다.

---

## 6. Locale Fallback Policy

### 6.1 Fallback Categories

fallback policy는 아래 3개 category로 나눠 적용한다.

| Category | Examples | Policy |
|---|---|---|
| UI resource | nav label, status label, chart title, issue label | locale fallback chain 적용 |
| code-derived display label | `product_type_label`, `subtype_label`, badge/reason label | locale fallback chain 적용 |
| source-derived content | product name, source condition, evidence excerpt | fallback chain을 적용하지 않고 source value 직접 표시 |

### 6.2 UI Resource Fallback Chain

UI resource와 code-derived display label의 공식 fallback 순서는 아래와 같다.

1. selected locale의 `approved` resource
2. `en` locale의 `approved` resource
3. stable code-derived safe label

`stable code-derived safe label` 예시:
- `status.active` -> `Active`
- `product_type.savings` -> `Savings`
- `badge.high_rate` -> `High Rate`

규칙:
- raw resource key 문자열 자체를 최종 사용자에게 직접 노출하지 않는다.
- `ko`, `ja` 미번역 상태는 English fallback으로 안전하게 흡수한다.
- 동일 값이 `en`에도 없으면 code humanization 또는 equivalent safe label을 사용한다.

### 6.3 Source-Derived Content Rule

아래 값에는 locale fallback 체인을 적용하지 않는다.

- `product_name`
- `description_short`
- `eligibility_text`
- `fee_waiver_condition`
- `notes`
- `source_subtype_label`
- evidence excerpt
- candidate value copied from source

표시 규칙:
- source-derived value는 수집된 source language 값을 그대로 표시한다.
- selected locale과 source language가 다를 수 있으며, 필요하면 source-language badge를 함께 표시한다.
- source-derived value를 machine translation으로 runtime 변환해 canonical 또는 display value를 덮어쓰지 않는다.

### 6.4 Brand and Proper-Noun Rule

- bank name과 institution brand는 번역하지 않는다.
- product brand/marketing slogan도 source-derived proper noun로 간주해 번역하지 않는다.
- Japanese glossary는 brand translation이 아니라 terminology consistency에만 사용한다.

### 6.5 Formatting Fallback Rule

number/date/currency formatting의 공식 fallback 순서는 아래와 같다.

1. selected locale formatter
2. `en-CA` formatter
3. machine-readable canonical value

규칙:
- 통화 값은 currency code를 바꾸지 않는다.
- percent, amount, date formatting은 selected locale의 표현만 바꾸고 underlying numeric value는 바꾸지 않는다.
- formatter 부재가 계산 의미 변경으로 이어지면 안 된다.

### 6.6 Surface-Specific Fallback Notes

| Surface | Rule |
|---|---|
| Public Grid | product name은 source language 유지, badge/filter/sort는 locale fallback 적용 |
| Public Insight Dashboard | KPI/methodology/axis label은 locale fallback 적용 |
| Admin Console | ops label/status/reason은 locale fallback 적용, trace/evidence text는 source language 유지 |
| External API Phase 2 | locale parameter는 enum/helper label에만 영향, source-derived product fields는 원문 유지 |

---

## 7. Japanese Glossary Policy

### 7.1 Glossary Objective

Japanese glossary의 목적은 아래 3가지다.

1. 금융 용어와 운영 용어의 Japanese label drift를 줄인다.
2. public/admin 화면에서 같은 개념이 다른 일본어 표현으로 흩어지는 것을 막는다.
3. Phase 2 Japan 확장 시 UI/API 문서 terminology baseline을 재사용 가능하게 만든다.

### 7.2 Glossary Scope

Japanese glossary가 다루는 대상:
- product type / subtype display label
- status label
- badge label
- filter label
- chart/methodology terminology
- admin operations terminology
- validation / reason-code display label

Japanese glossary가 다루지 않는 대상:
- bank brand name
- product name
- source marketing copy
- evidence excerpt
- source-derived product condition sentence 전체

### 7.3 Ownership Model

| Responsibility | Owner |
|---|---|
| glossary policy owner | Product Owner |
| glossary registry steward | Frontend Engineer |
| finance-term semantic consult | Domain Reviewer |
| future native-level Japanese review | later dedicated reviewer or partner |

현재 단계의 공식 rule:
- dedicated Japanese reviewer가 없더라도 Product Owner가 glossary approval owner다.
- semantic ambiguity가 큰 금융 용어는 Domain Reviewer consult 없이는 glossary finalization을 권장하지 않는다.
- unresolved Japanese term은 무리한 임시 번역보다 English fallback 유지가 우선이다.

### 7.4 Glossary Entry Baseline

glossary entry는 최소 아래 필드를 가져야 한다.

| Field | Meaning |
|---|---|
| `term_key` | stable key |
| `domain` | public/admin/shared taxonomy/system |
| `source_term_en` | English baseline term |
| `term_ko` | Korean approved label |
| `term_ja` | Japanese approved label |
| `term_status` | approved/deprecated |
| `do_not_translate_flag` | proper noun 여부 |
| `usage_note` | short note or context |
| `last_reviewed_at` | review timestamp |

### 7.5 Glossary Maintenance Rules

- shared financial term은 화면마다 별도 Japanese 표현을 만들지 않고 glossary entry를 먼저 참조한다.
- 새 `product_type`, `subtype_code`, `status`, `badge`, `reason_code`가 추가되면 corresponding glossary/resource entry를 함께 검토한다.
- `do_not_translate_flag = true`인 항목은 locale rendering에서도 원문을 유지한다.
- glossary가 미확정인 Japanese term은 English fallback을 허용하고, ad-hoc Japanese copy를 여러 화면에 흩뿌리지 않는다.
- deprecated entry는 신규 UI에서 사용하지 않는다.

### 7.6 Japanese Wording Principles

- 의미가 확정된 금융 용어는 카타카나 음역보다 업계에서 통용되는 Japanese finance term을 우선한다.
- 코드값과 표시값은 분리한다. 내부 code는 English를 유지하고 display label만 locale-aware 하게 바꾼다.
- 한 term이 public/admin 양쪽에 공통으로 쓰이면 같은 Japanese base term을 유지하고, 필요 시 usage note로 문맥 차이를 설명한다.

---

## 8. Follow-On Items

| Area | Follow-Up |
|---|---|
| i18n scaffold and locale file structure | `2.6` |
| trilingual UI rendering rollout | `5.12` |
| admin localization health surface | future admin observability follow-on |
| Phase 2 Japanese docs/API terminology extension | `7.x` Phase 2 design |

---

## 9. Follow-On Work Unlocked

- `2.6`: i18n scaffold 구성
- `5.12`: EN/KO/JA locale 적용
- admin localization health surface 설계/구현 follow-on
- Phase 2 Japan/API terminology 확장

---

## 10. WBS Mapping

| WBS ID | Closure in This Document |
|---|---|
| 1.7.5 | Sections 2, 4, 5, 8 |
| 1.7.6 | Sections 2, 6, 7, 8 |
| 1.7.7 | Sections 2, 7 |

---

## 11. Change History

| Date | Change |
|---|---|
| 2026-04-06 | Initial localization governance, fallback policy, and Japanese glossary baseline created for WBS 1.7.5 - 1.7.7 |
