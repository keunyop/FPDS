# FPDS Requirements Definition (PRD / Requirements Spec)
Version: 1.5
Date: 2026-03-28
Language: Korean-centered with English technical terms + English/Korean/Japanese UI support
Status: Updated Draft for Product Owner Review (Security Requirements Added)

---

## 1. Document Purpose

본 문서는 **FPDS(Finance Product Data Service)** 구축을 위한 요구사항 정의서이다.
대상 범위는 아래 3개 단계를 모두 포함한다.

- **Prototype**: 기술 검증(Technical Feasibility Validation)
- **Phase 1**: 캐나다 Big 5 수신상품 데이터 인프라 + 공개 Landscape Dashboard + 내부 Admin Console
- **Phase 2**: 일본 Big 5 수신상품 DB 확장 + 외부 SaaS/Open API 제공

본 문서의 목적은 다음과 같다.

1. 무엇을 만들지 명확히 정의한다.
2. 각 단계의 확정 범위와 제외 범위를 분리한다.
3. 개발, 테스트, 운영, BX-PF 연계, 외부 API 제공에 대한 공통 기준을 만든다.
4. 제안서 수준이 아닌 **실제 구현 가능한 제품 요구사항 기준선**을 제공한다.
5. 공개 사용자에게 어떤 방식으로 상품을 보여줄지에 대한 **Product Grid + Insight Dashboard 기준**을 제공한다.
6. 공개/운영 화면과 API 문서가 **English / Korean / Japanese**까지 확장 가능한 다국어 기준을 제공한다.

---

## 2. Product Definition

### 2.1 Product One-Liner
FPDS는 은행의 공개 웹페이지와 PDF 문서에 흩어져 있는 금융상품 정보를 자동 수집, 추출, 정규화, 검증, 검수하여 **비교 가능하고 재사용 가능한 금융상품 데이터 자산**으로 전환하고, 이를 **운영 콘솔, 공개 Dashboard, 외부 SaaS/Open API** 형태로 제공하는 **Financial Product Data Infrastructure**이다.

### 2.2 Product Positioning
FPDS는 단순 스크래핑 툴이 아니다.
FPDS는 다음을 제공하는 **Evidence-grounded operational data platform** 이다.

- 공개 웹/PDF 기반 수집
- Evidence-grounded extraction
- Canonical schema normalization
- Validation + confidence scoring
- Human-in-the-loop review
- Public landscape dashboard serving
- BX-PF 연계
- 외부 SaaS/Open API 제공

### 2.3 Relationship to MyBank
FPDS는 금융상품 데이터를 생산·운영하는 기반 플랫폼이다.
**MyBank**는 FPDS를 활용하는 후속 소비자 서비스이며, 개인 맞춤 추천, 금융기관 연결, 오픈뱅킹형 사용자 서비스는 **본 문서의 구현 범위가 아니다**.

### 2.4 Why This Product Exists
은행 상품 정보는 다음 문제를 가진다.

- 은행마다 표현 방식이 다르다.
- 상세 정보가 웹페이지와 PDF에 분산된다.
- 수수료, 금리, 조건 등 필드 위치와 형식이 제각각이다.
- 변경이 잦고 사람이 일일이 추적하기 어렵다.
- 비교 가능한 형태로 정리되지 않아 활용 가치가 낮다.

FPDS는 원문 근거(evidence)를 보존하면서 구조화된 상품 데이터를 생성하고, 검수 가능한 운영 흐름 위에서 품질과 추적 가능성을 높인다.

---

## 3. Product Goals and Non-Goals

### 3.1 Goals
본 프로젝트의 핵심 목표는 아래와 같다.

1. **Prototype에서 단일 은행·단일 상품유형 기준 End-to-End 기술 검증**
2. **Phase 1에서 캐나다 Big 5 수신상품 데이터 인프라 및 공개 Landscape Dashboard 구축**
3. **Phase 1에서 운영 검수, 추적 조회, BX-PF 연계 준비, LLM 사용량 모니터링 체계 구축**
4. **Phase 2에서 일본 Big 5 수신상품 DB 구축**
5. **Phase 2에서 외부 SaaS/Open API 제공**
6. **Phase 1 공개 화면에서 상품 Grid 탐색과 의미 있는 비교형 Dashboard 제공**

### 3.2 Non-Goals
아래는 본 프로젝트의 핵심 목표가 아니다.

- 사용자 맞춤 추천
- eligibility / fit matching
- 금융기관 대상 market insight portal
- product map / market analysis / insight mart
- 계좌 개설 대행
- 오픈뱅킹 사용자 서비스
- 일본 전체 금융기관 확대
- 일본의 여신/카드 상품 확대
- 공개 사용자용 evidence trace 노출
- 결제/구독 기능

---

## 4. Delivery Boundary

### 4.1 In Scope

#### Prototype
- 1개 은행(TD Bank)
- 1개 상품유형(Savings Accounts)
- 공개 웹 또는 PDF에서 상품 정보 수집
- evidence 저장
- 추출 및 정규화
- FPDS 내부 임시 상품정보 DB 저장
- 기본 확인용 Dashboard/UI

#### Phase 1
- 캐나다 Big 5 은행 대상
  - RBC
  - TD
  - BMO
  - Scotiabank
  - CIBC
- 상품군
  - Chequing
  - Savings
  - GIC / Term Deposits
- Evidence store
- Parsing / chunking / change detection
- Multi-agent orchestration
- Review queue
- Admin console
- Public market landscape dashboard
- Execution status / run history / change history
- English / Korean / Japanese multilingual UI
- BX-PF connector interface
- BX-PF write-back 준비 및 환경 충족 시 실제 적재
- LLM usage / token / cost tracking

#### Phase 2
- 일본 Big 5 은행 대상 수신상품 DB 구축
- 일본어 source 수집 및 정규화
- 일본 BwJ 협업을 전제로 한 검수/운영 workflow
- 외부 SaaS/Open API 제공
- API 문서화 및 외부 소비자 접근 제어
- FPDS DB / 검색 인덱스 / API delivery layer 확장

### 4.2 Out of Scope
- personalized recommendation
- institution insight portal
- product map / report portal
- user profile based ranking
- public evidence trace exposure
- Japan all-financial-institutions coverage
- Japan loan/card scope
- public consumer account features
- subscription / billing / Stripe

---

## 5. Product Users and Roles

### 5.1 User Types

#### A. Anonymous Public User
로그인 없이 공개 사이트에 접근하는 일반 사용자

주요 목적:
- 캐나다 Big 5 상품 landscape 확인
- 전체 상품 Grid 탐색
- 필터/정렬을 통한 시장 현황 파악
- 주요 rate / fee / minimum balance 비교 시각화 확인
- English / Korean / Japanese UI 이용

#### B. Admin Operator
운영 및 검수를 담당하는 내부 사용자

주요 목적:
- review queue 처리
- evidence trace 확인
- 승인/반려/수정/사유 기록
- 수집/실행 상태 모니터링
- 변경 이력 확인
- BX-PF 연계 상태 확인
- LLM 사용량 및 비용 모니터링

#### C. External API Consumer (Phase 2)
Phase 2 SaaS/Open API를 이용하는 외부 시스템 또는 기업 사용자

주요 목적:
- 상품 데이터 조회
- 필터 검색
- 변경 이벤트 소비
- API 기반 연계

### 5.2 Role Matrix

| Capability | Public User | Admin Operator | External API Consumer |
|---|---:|---:|---:|
| Public dashboard view | O | O | X |
| Public filter/sort use | O | O | X |
| Public chart interaction | O | O | X |
| Admin login | X | O | X |
| Review queue access | X | O | X |
| Evidence trace view | X | O | X |
| Approve/reject/edit candidate | X | O | X |
| View execution logs | X | O | X |
| View BX-PF integration status | X | O | X |
| View LLM usage dashboard | X | O | X |
| Call SaaS/Open API | X | X | O |

---

## 6. Core Product Principles

1. **Evidence First**
   모든 구조화 결과는 가능한 한 source evidence와 citation에 연결되어야 한다.

2. **FPDS Owns the Platform**
   LLM은 외부 reasoning provider일 뿐이며, 데이터 소유권, 운영 정책, trace, 검수, 모니터링은 FPDS가 소유한다.

3. **Human Review by Design**
   애매한 데이터는 자동 확정하지 않고 review queue로 보낸다.

4. **Canonical Before Consumer Features**
   추천보다 먼저 canonical product data의 품질과 운영 체계를 확보한다.

5. **BX-PF as Target Master Store**
   승인된 정규화 상품정보의 최종 마스터 저장 대상은 BX-PF로 정의한다. 단, Phase 1에서는 연계 환경/운영 조건이 충족된 경우에 실제 write-back을 acceptance에 포함한다.

6. **Operational Visibility by Default**
   처리 이력, evidence trace, run 상태, change history, LLM token/cost는 운영자가 추적 가능해야 한다.

7. **Useful Comparison Over Decorative Charts**
   Dashboard는 보기 좋은 차트보다 **상품 비교에 실제로 도움이 되는 지표**를 우선해야 하며, 모든 차트는 의미와 계산 기준이 설명 가능해야 한다.

8. **Trilingual UI and Multi-Locale Ready**
   Phase 1부터 Public/Admin UI는 English/Korean/Japanese를 지원해야 하며, Phase 2는 일본어 source 처리, 일본 상품 taxonomy, 일본어 API 문서까지 지원할 수 있어야 한다.

9. **Security by Default**
   공개 Dashboard, Admin Console, External API, Crawler/Fetcher 전 구간에 대해 인증/권한, 입력 검증, 네트워크 호출 통제, 감사추적, 보안 헤더를 기본값으로 설계해야 한다.

---

## 7. High-Level Scope by Stage

### 7.1 Prototype

#### Objective
기술적으로 다음이 가능한지 검증한다.

- 공개 웹/PDF 수집 가능성
- 상품 필드 추출 가능성
- evidence 저장 구조
- canonical schema 정규화 가능성
- FPDS 내부 임시 DB 저장 가능성

#### Done Definition
- 하나 이상의 savings product record가 저장된다.
- 주요 필드가 canonical schema로 매핑된다.
- 원문 evidence가 저장된다.
- 기본 UI에서 결과를 확인할 수 있다.
- 최소 1개 end-to-end 성공 run이 존재한다.

### 7.2 Phase 1

#### Objective
운영 가능한 수준의 캐나다 수신상품 데이터 인프라와 공개 대시보드(Product Grid + Insight Dashboard)를 구축한다.

#### Done Definition
- Big 5 은행의 Chequing / Savings / GIC 데이터가 수집 가능하다.
- 원문과 evidence가 저장된다.
- 정규화 후보가 생성된다.
- review workflow가 동작한다.
- 공개 landscape dashboard가 익명 사용자에게 제공된다.
- 공개 상품 Grid 화면에서 전체 상품 목록 탐색이 가능하다.
- 공개 insight dashboard에서 ranking / distribution / scatter plot 기반 비교가 가능하다.
- admin console에서 run status / review queue / trace / change history / LLM usage 확인이 가능하다.
- BX-PF connector가 동작 가능 상태로 준비된다.
- BX-PF 연계 환경 충족 시 approved product write-back이 가능하다.
- English / Korean / Japanese 언어 전환이 작동한다.

### 7.3 Phase 2

#### Objective
일본 Big 5 수신상품 DB를 구축하고, 외부 SaaS/Open API를 제공한다.

#### Done Definition
- 일본 Big 5 은행 수신상품 source inventory가 구축된다.
- 일본어 source 수집/파싱/정규화가 가능하다.
- 일본 상품 데이터가 canonical schema 또는 확장 taxonomy로 관리된다.
- 외부 API를 통해 검색 가능한 데이터 제공이 가능하다.
- API 인증/권한/문서/기본 운영 모니터링이 동작한다.

---

## 8. Functional Requirements

## 8.1 Public Site Requirements

### FR-PUB-001 Public Access
시스템은 공개 dashboard를 **익명 사용자에게 로그인 없이 제공**해야 한다.

### FR-PUB-002 Trilingual UI
공개 dashboard는 최소 **English / Korean / Japanese language toggle**을 제공해야 한다.

### FR-PUB-003 Product Catalog Grid
공개 사이트는 전체 상품목록을 **Grid 형식(card/tile based)** 으로 탐색할 수 있는 화면을 제공해야 한다.

표시 기본 단위:
- Bank
- Product type
- Product name
- Key rate snapshot
- Key fee snapshot
- Minimum balance or minimum deposit snapshot
- Key badge (예: High Rate / No Monthly Fee / Low Minimum Deposit)
- Status / last updated

### FR-PUB-004 Grid Card Content
각 상품 card/grid item은 최소 아래 정보를 표시할 수 있어야 한다.

- bank name
- product name
- product type
- displayed rate label
- monthly fee label
- minimum balance or minimum deposit
- target customer tag if available
- freshness indicator or updated timestamp

### FR-PUB-005 Filtering
사용자는 다음 필터를 사용할 수 있어야 하며, 필터 라벨은 선택된 locale에 따라 표시되어야 한다.

- 은행(bank)
- 상품군(product type)
- 금리 유형(rate type if applicable)
- 월 수수료 여부 / fee bucket
- 최소 예치금 / minimum balance bucket
- term bucket (GIC/term deposits when applicable)
- target customer tag (student / newcomer 등, if available)
- 신규/변경 상태(optional if available)
- 언어

### FR-PUB-006 Sorting
사용자는 다음 기준으로 정렬할 수 있어야 한다.

- last updated
- bank name
- product name
- displayed rate
- monthly fee
- minimum balance / minimum deposit

### FR-PUB-007 Insight Dashboard
공개 사이트는 상품 비교에 도움이 되는 **insight dashboard 화면 또는 동등한 탭/섹션**을 제공해야 한다.

최소 제공 범주:
- headline KPI cards
- ranking widgets
- distribution/composition charts
- comparative scatter plot

### FR-PUB-008 Headline KPI Cards
insight dashboard는 최소 아래 KPI를 표시해야 한다.

- total active products
- products by bank
- products by product type
- recently changed products count
- selected filter scope 기준 최고 표시 금리 또는 대표 금리 snapshot

### FR-PUB-009 Ranking Widgets
insight dashboard는 사용자가 빠르게 시장을 파악할 수 있도록 **Top N ranking widgets**를 제공해야 한다.

최소 후보 예시:
- 최대 금리 Top 5
- 최저 월 수수료 Top 5
- 최소 예치금/최소 가입금액 Top 5
- 최근 변경 상품 Top 5

> 실제 노출 ranking은 product type과 데이터 completeness를 고려해 선택적으로 조합할 수 있으나, 최소 2개 이상의 의미 있는 ranking widget이 Phase 1에 포함되어야 한다.

### FR-PUB-010 Comparative Scatter Plot
insight dashboard는 상품 간 trade-off를 보여주는 scatter plot 또는 동등한 comparative chart를 제공해야 한다.

권장 예시:
- Savings / GIC: X축 = minimum balance 또는 minimum deposit, Y축 = displayed rate
- GIC: X축 = term length, Y축 = displayed rate
- Chequing: X축 = monthly fee, Y축 = minimum balance 또는 equivalent convenience metric

### FR-PUB-011 Product-Type-Aware Visualization
chart와 ranking은 선택된 product type의 의미에 맞게 달라져야 한다.

예:
- Savings는 금리/최소잔액 중심
- Chequing은 월수수료/거래편의 중심
- GIC는 금리/가입기간/최소예치금 중심

### FR-PUB-012 Cross-Filtering Between Grid and Charts
가능한 경우 product grid와 insight dashboard는 동일한 필터 상태를 공유해야 하며, chart interaction이 결과 목록에 반영될 수 있어야 한다.

### FR-PUB-013 Metric Definition and Freshness
공개 dashboard의 주요 지표와 ranking은 계산 기준이 설명 가능해야 하며, 마지막 refresh 시각 또는 데이터 freshness 정보를 표시해야 한다. 이 설명 텍스트도 EN/KO/JA locale별로 제공되어야 한다.

### FR-PUB-014 No Public Evidence Exposure
공개 dashboard에서는 evidence trace를 일반 사용자에게 직접 노출하지 않는다.

### FR-PUB-015 Responsive Experience
공개 dashboard는 desktop 우선으로 설계하되 tablet/mobile에서도 사용 가능해야 한다.

### FR-PUB-016 Locale-Aware Presentation
공개 dashboard의 메뉴, 필터 라벨, 카드 라벨, KPI 명칭, 차트 제목, methodology 안내는 선택된 locale(EN/KO/JA)에 따라 표시되어야 하며, 통화/숫자/날짜 포맷도 locale-aware 하게 표시되어야 한다.

### FR-PUB-017 Translation Fallback
UI 번역 리소스 또는 설정 라벨이 불완전한 경우 시스템은 정의된 fallback 순서(권장: selected locale → English → source language 또는 default locale)에 따라 안전하게 표시해야 한다. 단, 상품명/상품설명/상품조건 등 source-derived 상품정보는 번역하지 않고 수집된 source language 값을 그대로 표시할 수 있어야 한다.


---

## 8.2 Admin Requirements

### FR-ADM-001 Admin Login
admin 사용자는 인증(auth)을 통해 로그인해야 한다.

### FR-ADM-002 Review Queue
시스템은 저신뢰/충돌/누락/정책 위반 후보를 review queue로 보낼 수 있어야 한다.

Review item 필수 정보:
- candidate id
- bank
- country
- product type
- product name
- issue summary
- confidence score
- validation result
- created time
- linked evidence
- current status

### FR-ADM-003 Review Decision
운영자는 각 review item에 대해 다음 액션을 수행할 수 있어야 한다.

- Approve
- Reject
- Edit & Approve
- Return / Defer (optional)

### FR-ADM-004 Decision Reason
운영자는 승인/반려/수정 시 사유(reason)를 기록할 수 있어야 한다.

### FR-ADM-005 Override History
시스템은 운영자의 수동 수정 내용과 전/후 값을 이력으로 보관해야 한다.

### FR-ADM-006 Evidence Trace Viewer
운영자는 candidate record의 각 필드가 어떤 원문 evidence에서 왔는지 확인할 수 있어야 한다.

Trace viewer 최소 요소:
- source URL
- source type (HTML/PDF)
- crawl timestamp
- chunk excerpt
- citation anchor or chunk id
- parsed field mapping
- model run reference

### FR-ADM-007 Change History
운영자는 상품 단위 또는 실행 단위의 변경 이력을 확인할 수 있어야 한다.

변경 유형 예시:
- New
- Updated
- Discontinued
- Reclassified
- Manual override

### FR-ADM-008 Run Status
운영자는 수집/파싱/정규화/검증/검수 라인의 실행 상태를 확인할 수 있어야 한다.

필수 상태 정보:
- run id
- started at
- completed at
- source count
- candidate count
- success/failure count
- review queued count
- error summary

### FR-ADM-009 Search and Drilldown
운영자는 bank / product name / run id / candidate id 기준으로 검색할 수 있어야 한다.

### FR-ADM-010 Trilingual Admin UI
관리자 화면도 English / Korean / Japanese language toggle을 제공해야 한다.

### FR-ADM-011 BX-PF Integration Status
운영자는 BX-PF connector 상태, write-back 결과, pending/retry 상태를 확인할 수 있어야 한다.

### FR-ADM-012 LLM Usage Dashboard
운영자는 agent별 / run별 LLM token usage와 estimated cost를 조회할 수 있어야 한다. 위젯 title과 상태 label은 EN/KO/JA locale을 지원해야 한다.

### FR-ADM-013 Dashboard Refresh and Metric Health
운영자는 공개 dashboard의 last refresh 시각, 집계 성공/실패 여부, 누락 데이터 비율 또는 equivalent metric health 정보를 확인할 수 있어야 한다.

### FR-ADM-014 Localization Management Visibility
운영자는 locale별 번역 적용 상태, 누락된 번역 항목 수, fallback 적용 여부 또는 동등한 localization health 정보를 확인할 수 있어야 한다.

### FR-ADM-015 Source Registry Management
운영자는 admin UI에서 은행 목록과 source registry catalog를 관리할 수 있어야 하며, generated source row는 read-only로 조회할 수 있어야 한다.

Source registry row 최소 정보:
- source id
- bank
- country
- product type
- source name
- normalized URL
- source type
- discovery role
- status
- last verified time
- updated time

### FR-ADM-016 Source Collection Trigger
운영자는 source registry 목록에서 하나 이상의 source를 선택해 상품정보 수집을 시작할 수 있어야 한다.

이 수집의 기본 의미는 raw fetch only가 아니라 `normalized_candidate`까지 생성하는 full collection이다.

---

Current Phase 1 source-registry admin note:
- `/admin/banks` is the primary operator-owned surface for bank profile setup, bank-owned coverage management, and collection launch.
- `/admin/source-catalog` may remain as a compatibility route, but it is no longer the preferred primary operator workflow.
- operators may launch collection per bank coverage item from the bank detail modal.
- operators may also multi-select banks from the bank list and bulk-launch collection across all attached coverage items.

### FR-ADM-017 Deferred Dynamic Product Type Management
FPDS should support an operator-managed product type registry, not only a fixed hard-coded product-type list.

Minimum later capability:
- admin can create and edit product types with at least `name` and `description`
- admin can search product types when attaching coverage to a bank
- AI-assisted discovery can use the stored product type name and description to infer relevant bank-site URLs during homepage-first source generation
- downstream parser, extraction, normalization, validation, and public/admin vocabulary rules must define safe fallback behavior when a newly added product type does not yet have full dedicated domain logic
- homepage-first discovery should use a bounded hybrid scoring model: deterministic link candidate generation plus AI parallel scoring over those candidates, rather than relying on AI only after heuristic failure
- product type `description` should be treated as a first-class discovery input for semantic matching, not only as a source of derived keywords
- page-level evidence scoring should validate title, heading, and early body signals before a candidate URL is promoted to a generated `detail` source

Current boundary:
- this capability is now implemented in live `WBS 5.16` for the admin registry and collection pipeline
- the live runtime now lets operators define additional deposit product types, attach them to bank coverage, and run homepage-first discovery plus generic AI fallback through manual review
- public publish, dashboard aggregation, and auto-approval semantics remain constrained to the existing reviewed canonical flow until later slices widen those downstream surfaces intentionally

## 8.3 Data Ingestion Requirements

### FR-DATA-001 Source Types
시스템은 다음 source type을 지원해야 한다.

- public HTML pages
- linked PDF documents

### FR-DATA-002 Crawl Scheduling
시스템은 정해진 schedule에 따라 source를 주기적으로 수집할 수 있어야 한다.

### FR-DATA-003 Snapshot Preservation
수집된 원문은 snapshot 형태로 저장해야 한다.

### FR-DATA-004 Parsing
HTML과 PDF는 후속 extraction이 가능한 parsed text로 변환되어야 한다.

### FR-DATA-005 Chunking
원문은 retrieval과 trace를 위해 chunk 단위로 분리 저장되어야 한다.

### FR-DATA-006 Source Metadata
각 source에는 최소 다음 metadata가 저장되어야 한다.

- source url
- bank
- country
- source type
- source language if detectable
- discovered at
- fetched at
- checksum / fingerprint

### FR-DATA-007 Change Detection
동일 source의 이전 snapshot과 비교해 변경 여부를 감지해야 한다.

### FR-DATA-008 Multi-Language Source Handling
시스템은 영어 및 일본어 source에 대해 파싱/정규화 workflow를 지원할 수 있어야 한다. UI locale은 EN/KO/JA를 지원하되, source language와 display language는 분리 관리되어야 한다.

### FR-DATA-009 UI Localization Resource Management
시스템은 공개/운영 화면에 필요한 UI display label, filter label, chart title, methodology text, status label 등 비상품성 resource를 EN/KO/JA 기준으로 저장하거나 제공할 수 있어야 한다. 단, 상품명/상품설명/상품 조건 등 source-derived product content는 수집된 source language 단일 값으로 관리해야 한다.

### FR-DATA-010 DB-Backed Active Source Registry
운영용 active source registry는 DB에서 관리되어야 하며, admin UI가 그 운영 source of truth를 직접 수정할 수 있어야 한다. `source_registry_catalog.json`과 bank별 registry JSON은 ongoing 운영 관리 기준으로 사용하지 않는다.

### FR-DATA-011 Candidate-Producing Scope Control
source registry는 candidate-producing scope를 제어할 수 있어야 한다. `detail` source는 기본적으로 상품 후보 생성 대상이고, supporting/entry source는 필요 시 같은 run에 포함될 수 있으나 기본적으로 standalone 상품 후보 생성 대상으로 취급하지 않는다.

---

### FR-DATA-012 Vector-Assisted Evidence Retrieval
Phase 1 retrieval must support a vector-assisted path for `evidence_chunk` only. The vector path must improve field-level evidence recall while preserving the same traceable `evidence_chunk_id`, excerpt, source, and anchor output used by metadata-only retrieval.

Minimum requirements:
- initial vector backend is Postgres `pgvector`
- vector scope is limited to `evidence_chunk` embeddings and retrieval metadata
- metadata filters must run before vector ranking
- missing pgvector infrastructure or missing embedding rows must fall back to metadata-only retrieval
- public APIs must not expose vector metadata or raw evidence
- production semantic embedding provider/model selection remains a separate follow-up decision

## 8.4 AI / Agent Workflow Requirements

### FR-AI-001 Orchestrated Workflow
시스템은 single generic extraction이 아니라 단계 분리된 orchestration workflow를 지원해야 한다.

### FR-AI-002 Specialized Agents
시스템은 최소 아래 agent responsibility를 지원해야 한다.

- Discovery
- Extraction
- Normalization
- Validation
- Confidence / Review Decision
- Change Assessment

### FR-AI-003 Guardrails
시스템은 timeout, retry, validation gating, review routing을 중앙에서 통제해야 한다.

### FR-AI-004 Minimal Prompt Package
외부 LLM 호출 시 내부 운영정보 전체를 보내지 않고 필요한 최소 컨텍스트만 전달해야 한다.

### FR-AI-005 Retrieval-Backed Extraction
추출 및 검증 단계는 evidence retrieval을 활용할 수 있어야 한다.

### FR-AI-006 Field-Level Citation Linkage
가능한 경우 정규화 결과의 핵심 필드는 field-to-evidence linkage를 유지해야 한다.

### FR-AI-007 Human-in-the-Loop Routing
낮은 신뢰도, 규칙 충돌, 근거 불충분 상황은 review queue로 라우팅되어야 한다.

---

## 8.5 Canonical Product Data and BX-PF Requirements

### FR-CAN-001 Prototype Temporary Store
Prototype에서는 FPDS 내부의 임시 상품정보 DB를 사용한다.

### FR-CAN-002 BX-PF Target Master
Phase 1부터 승인된 정규화 상품정보의 **Target Master Store**는 BX-PF로 정의한다.

### FR-CAN-003 Conditional Write-Back Acceptance
Phase 1에서 실제 BX-PF write-back은 필수 인터페이스로 설계하되, **BX-PF 연동 환경·권한·운영 규칙이 충족된 경우 mandatory acceptance**로 본다.

### FR-CAN-004 Approved Copy and Reconciliation
BX-PF write-back이 즉시 불가능한 경우에도 FPDS는 approved copy, publish status, reconciliation metadata를 관리할 수 있어야 한다.

### FR-CAN-005 Product Versioning
상품 레코드는 변경을 추적할 수 있도록 versioning 또는 equivalent history strategy를 가져야 한다.

### FR-CAN-006 Review-Aware State
상품 후보/정규화 결과는 최소 다음 상태를 가져야 한다.

- Draft
- Auto-Validated
- In Review
- Approved
- Rejected
- Pending Publish
- Published to BX-PF
- Publish Failed
- Superseded
- Discontinued

### FR-CAN-007 Canonical Schema Governance
canonical schema는 product type별 필수/선택 필드를 정의해야 하며, 국가별 taxonomy 확장을 허용해야 한다.

### FR-CAN-008 Localization Boundary Governance
canonical schema 또는 연계 display model은 UI terminology label, status label, badge label mapping 등 비상품성 표시 리소스에 대해 EN/KO/JA translation reference를 지원해야 한다. product_name, description_short 등 source-derived product field는 locale별 복수 필드 대신 source language 단일 필드로 관리해야 한다.

---

## 8.6 LLM Usage and Cost Monitoring Requirements

### FR-LLM-001 Usage Capture
시스템은 LLM 호출 단위로 prompt tokens, completion tokens, estimated cost, model id, agent name을 기록해야 한다.

### FR-LLM-002 Run-Level Aggregation
시스템은 run, bank, product type, stage, date 기준으로 usage를 집계할 수 있어야 한다.

### FR-LLM-003 Alertable Visibility
운영자는 비정상적 token 증가나 비용 급증을 탐지할 수 있어야 한다.

### FR-LLM-004 Audit Trace
LLM usage record는 실행 이력과 연결되어 원인 분석이 가능해야 한다.

---

## 8.7 Phase 2 SaaS / Open API Requirements

### FR-API-001 External Query API
Phase 2에서는 외부 시스템이 금융상품 데이터를 검색할 수 있는 API를 제공해야 한다.

### FR-API-002 Authentication and Access Control
외부 API는 최소한의 인증 방식(API key 또는 동등한 access control)을 가져야 한다.

### FR-API-003 Search and Filter
외부 API는 최소 아래 기준으로 검색/필터를 지원해야 한다.

- country
- bank
- product family / product type
- currency
- status
- last updated

### FR-API-004 Product Detail Response
외부 API는 상품 단위 조회 시 canonical identifier, 주요 조건, 최신 상태, last verified timestamp를 반환할 수 있어야 한다. 상품명과 설명 등 source-derived product field는 수집된 source language 값을 반환해야 하며, 필요 시 source_language를 함께 제공해야 한다.

### FR-API-005 Change Feed or Delta Query
외부 API는 변경 감지를 위해 last-updated 기반 delta query 또는 equivalent change feed를 지원해야 한다.

### FR-API-006 Documentation
외부 API는 사용 가능한 endpoint, parameter, response schema, auth 방식, 오류 응답을 문서화해야 한다.

### FR-API-007 Rate Limit and Abuse Control
외부 API는 오남용 방지를 위한 기본 rate limit 또는 equivalent protection을 가져야 한다.

### FR-API-008 Locale Parameter Support
외부 API는 locale parameter(예: en, ko, ja) 또는 동등한 localization control을 통해 enum label, status label, helper text 등 비상품성 표시 리소스를 제어할 수 있어야 한다. 상품명/설명/조건 등 source-derived product content는 locale과 무관하게 source language 값으로 유지할 수 있어야 한다.

### FR-API-009 Multilingual API Documentation
외부 API 문서는 최소 English와 Japanese를 지원하고, 가능하면 Korean도 제공할 수 있어야 한다.

---

## 8.8 Security and Access Control Requirements

### FR-SEC-001 Admin Authentication
Admin Console 및 내부 운영 API는 인증된 내부 사용자만 접근할 수 있어야 한다.

### FR-SEC-002 Authorization, RBAC, and Least Privilege
시스템은 최소 역할(Role) 기반 권한 통제(RBAC)를 지원해야 하며, Admin Operator, Reviewer, Read-Only Operator, System Integration Account 등 주요 역할별로 접근 범위를 분리해야 한다. 운영 계정, 배치 계정, API credential은 필요한 최소 권한만 가져야 한다.

### FR-SEC-003 Tenant Isolation for External API
Phase 2 External API는 client/tenant 단위의 credential scope, usage quota, audit separation을 지원해야 한다. 세부 정책은 RBAC 중심으로 시작하되, 필요한 경우 ABAC 또는 policy-based control로 확장 가능해야 한다.

### FR-SEC-004 CORS and Preflight Control
브라우저에서 호출되는 API는 허용된 origin, method, header만 허용해야 하며, preflight(OPTIONS) 요청을 명시적으로 처리해야 한다. wildcard CORS는 공개 read-only endpoint 등 명확히 승인된 경우를 제외하고 사용하지 않는다.

### FR-SEC-005 CSRF Protection
쿠키 또는 세션 기반 인증을 사용하는 admin state-changing 요청은 CSRF token 또는 동등한 보호기법을 적용해야 한다. Bearer token 기반 구조를 사용할 경우에도 cross-site 요청 악용을 방지할 수 있는 동등 수준의 방어가 필요하다.

### FR-SEC-006 Session and Cookie Security
웹 인증에 쿠키/세션을 사용할 경우 쿠키는 HttpOnly, Secure, SameSite 정책을 적용해야 하며, session timeout, logout, token/session invalidation 정책을 정의해야 한다.

### FR-SEC-007 Validation and Injection Defense
모든 외부 입력값은 서버 측에서 schema validation을 거쳐야 하며, DB 접근은 parameterized query 또는 동등한 SQL injection 방어기법을 사용해야 한다. URL, filter, sort, pagination, locale, file metadata 등도 동일하게 검증해야 한다.

### FR-SEC-008 XSS Defense and CSP
Public/Admin UI는 출력 시 context-aware escaping 또는 sanitization을 적용해야 하며, 가능한 범위에서 Content-Security-Policy(CSP)를 설정해야 한다. admin note, override reason, source-derived text 표시 영역은 특히 저장형/반사형 XSS를 방지해야 한다.

### FR-SEC-009 SSRF and Safe Fetch Policy
Crawler, fetcher, parser는 SSRF 방어를 위해 허용 스킴(http/https), redirect 제한, DNS/IP 재검증, private/internal IP range 및 cloud metadata endpoint 차단 정책을 가져야 한다. 또한 response size, content-type, download timeout 제한을 적용해야 한다.

### FR-SEC-010 Rate Limit and Brute-Force Protection
Admin login, admin API, external API는 rate limit, retry threshold, abuse detection 또는 동등한 brute-force 방어를 가져야 한다. Phase 2 external API는 tenant/client별 quota 및 burst 제어를 지원해야 한다.

### FR-SEC-011 Secret Management and Rotation
API key, DB credential, BX-PF integration credential, crawler secret, webhook secret 등 모든 secret은 안전한 secret storage 또는 environment management 체계로 관리해야 하며, repository 및 log에 노출되어서는 안 된다. 운영 단계에서 rotation 절차를 지원해야 한다.

### FR-SEC-012 HTTPS, HSTS, and Security Headers
운영 환경의 Public/Admin/API endpoint는 HTTPS를 강제해야 하며, HSTS와 기본 보안 헤더(X-Content-Type-Options, Referrer-Policy, frame embedding 통제 헤더 등)를 적용해야 한다.

### FR-SEC-013 Audit Log for Security-Sensitive Events
시스템은 로그인 성공/실패, 권한 변경, review 승인/반려/override, publish 요청, API credential 발급/폐기, 보안설정 변경 등 보안 민감 이벤트에 대해 actor, timestamp, target, action, result를 감사로그로 남겨야 한다.

### FR-SEC-014 Safe Error Handling
외부 사용자와 운영자 화면/API는 stack trace, internal path, raw SQL error, secret 값을 노출하지 않아야 하며, 추적 가능한 correlation id 또는 request id를 포함한 통제된 오류 응답을 제공해야 한다.

### FR-SEC-015 Dependency and Supply-Chain Scanning
애플리케이션 및 인프라 의존성에 대해 정기적 취약점 점검을 수행해야 하며, build/CI 단계에서 dependency vulnerability scanning 또는 동등한 통제를 적용해야 한다.

---

## 9. Canonical Schema (Initial Draft)

## 9.1 Core Entity Model
초기 데이터 모델은 최소 아래 엔터티를 포함한다.

- bank
- source_document
- evidence_chunk
- crawl_run
- extraction_run
- llm_usage_record
- normalized_candidate
- review_task
- review_decision
- canonical_product
- product_version
- publish_event
- change_event
- translation_resource
- dashboard_metric_snapshot
- dashboard_ranking_snapshot
- api_consumer
- api_credential
- user
- security_audit_log

## 9.2 Common Product Fields

> Note: UI 라벨과 설정 정보는 EN/KO/JA 다국어를 지원하되, 상품명/설명/조건 등 source-derived 상품정보는 **수집된 source language 단일 값**으로 관리한다.

| Field | Type | Required | Description |
|---|---|---:|---|
| product_id | UUID/string | O | 내부 canonical id |
| country_code | string | O | CA / JP |
| bank_code | string | O | 은행 식별자 |
| bank_name | string | O | 표시용 은행명(원문 또는 canonical single display name) |
| product_family | enum | O | deposit |
| product_type | string | O | chequing / savings / gic / localized subtype |
| product_name | string | O | 원문 상품명(수집 언어 단일 값) |
| source_language | string | O | en / ja 등 source language |
| currency | string | O | CAD / JPY 등 |
| status | enum | O | active / inactive / discontinued / draft |
| target_customer | string | X | 원문 기준 대상고객 태그 또는 normalized single text |
| description_short | text | X | 원문 또는 source-derived 요약 설명(수집 언어 단일 값) |
| public_display_rate | decimal | X | 공개 화면용 대표 금리 |
| public_display_fee | decimal | X | 공개 화면용 대표 수수료 |
| product_highlight_badge_code | string/enum | X | UI locale별 label로 렌더링되는 highlight badge code |
| source_confidence | number | O | 0~1 |
| review_status | enum | O | in_review / approved / rejected 등 |
| effective_date | date | X | 효력일 |
| last_verified_at | timestamp | O | 마지막 검증 시각 |
| last_changed_at | timestamp | X | 마지막 변경 감지 시각 |
| current_version_no | integer | O | 현재 버전 |
| created_at | timestamp | O | 생성일 |
| updated_at | timestamp | O | 수정일 |

## 9.3 Common Financial Fields

| Field | Type | Required | Description |
|---|---|---:|---|
| monthly_fee | decimal | X | 월 수수료 |
| minimum_balance | decimal | X | 최소잔액 |
| introductory_rate_flag | boolean | X | 프로모션 금리 여부 |
| standard_rate | decimal | X | 기본 금리 |
| promotional_rate | decimal | X | 프로모션 금리 |
| promotional_period_text | string | X | 예: 3 months |
| fee_waiver_condition | text | X | 수수료 면제 조건 |
| eligibility_text | text | X | 자격 요건 |
| notes | text | X | 기타 설명 |

## 9.4 Phase 1 Canada Deposit Subtype Fields

### Chequing
- included_transactions
- unlimited_transactions_flag
- interac_e_transfer_included
- overdraft_available
- cheque_book_info
- student_plan_flag
- newcomer_plan_flag

### Savings
- interest_calculation_method
- interest_payment_frequency
- tiered_rate_flag
- tier_definition_text
- withdrawal_limit_text
- registered_flag

### GIC / Term Deposits
- term_length_text
- term_length_days
- redeemable_flag
- non_redeemable_flag
- compounding_frequency
- payout_option
- minimum_deposit
- registered_plan_supported

## 9.5 Evidence Linkage Model
핵심 필드는 source evidence와 연결 가능해야 한다.

예:
- field_name
- candidate_value
- evidence_chunk_id
- evidence_text_excerpt
- source_document_id
- citation_confidence

---

## 10. Information Architecture (IA)

## 10.1 Public Site IA
- `/`
- `/dashboard`
- `/dashboard/products`
- `/dashboard/insights`
- `/dashboard?bank=...&type=...`
- `/about`
- `/methodology`

> Note: 공개 상품 상세 페이지와 public evidence trace는 본 범위에 포함하지 않는다.
> `/dashboard/products` 와 `/dashboard/insights` 는 별도 route 또는 동일 페이지 내 tab/view로 구현할 수 있다.

## 10.2 Admin IA
- `/admin/login`
- `/admin/dashboard`
- `/admin/review-queue`
- `/admin/review-queue/[taskId]`
- `/admin/products`
- `/admin/products/[productId]`
- `/admin/runs`
- `/admin/runs/[runId]`
- `/admin/change-history`
- `/admin/banks`
- `/admin/banks/[bankCode]`
- `/admin/source-catalog`
- `/admin/source-catalog/[catalogItemId]`
- `/admin/product-types` (later follow-on)
- `/admin/sources`
- `/admin/sources/[sourceId]`
- `/admin/bxpf-publish`
- `/admin/llm-usage`

> Note: `/admin/banks` 와 `/admin/source-catalog` 가 operator-owned 관리 surface이며, `/admin/sources` 는 generated source detail read-only surface다.

Admin IA note:
- `/admin/banks` is the primary live operator-owned management surface for bank setup, coverage management, and collection launch.
- `/admin/source-catalog` may remain as a compatibility route, but it is no longer the preferred primary operator workflow.
- `/admin/product-types` is the live operator-managed product type registry surface.
- `/admin/sources` remains the generated-source detail read-only surface.

## 10.3 External API / Docs IA (Phase 2)
- `/api/v1/products`
- `/api/v1/products/{id}`
- `/api/v1/banks`
- `/api/v1/changes`
- `/api/docs`

---

## 11. Detailed Screen Requirements

## 11.1 Public Product Catalog Grid
목적:
- 전체 상품을 빠르게 훑고 탐색할 수 있는 공개 catalog 화면 제공
- 필터/정렬 기반 비교 탐색 지원
- 상세 페이지 없이도 핵심 조건을 이해할 수 있도록 요약 정보 제공
- EN / KO / JA 사용자가 동일한 구조의 정보를 locale별로 이해할 수 있도록 지원
- 단, 상품명/상품설명 등 source-derived 값은 source language 그대로 표시될 수 있음

필수 요소:
- multilingual header (EN / KO / JA)
- sticky filters bar
- result count
- active filter chips
- grid/card view
- sort dropdown
- loading state
- empty state
- updated timestamp
- link or tab access to insight dashboard

Grid Card 필수 정보:
- bank name
- product name
- product type
- displayed rate
- monthly fee
- minimum balance or minimum deposit
- highlight badge
- target customer tag if available
- last updated

권장 동작:
- desktop에서 3~5 column grid
- mobile에서 1 column stacked card
- 필터 변경 시 grid와 summary가 즉시 갱신
- product type별 카드 강조 포인트가 달라질 수 있음

Acceptance Criteria:
- 익명 사용자가 접근 가능해야 한다.
- 전체 상품목록이 grid 형식으로 렌더링되어야 한다.
- 필터와 정렬이 동작해야 한다.
- English/Korean/Japanese 전환이 저장 또는 즉시 반영되어야 한다.
- locale별 label과 number/date/currency formatting이 일관되어야 한다.
- 모바일에서 핵심 정보가 잘려 보이지 않아야 한다.

## 11.2 Public Market Insights Dashboard
목적:
- 단순 목록을 넘어서 시장 구조와 상대 비교를 빠르게 이해하도록 돕는다.
- “어떤 상품이 더 높고/낮고/유리한지”를 한눈에 보여준다.
- ranking, chart label, methodology note가 EN / KO / JA로 읽히도록 지원한다.
- 단, 차트/목록에 노출되는 상품명 등 source-derived 상품 데이터는 수집된 언어 그대로 유지할 수 있다.

필수 섹션:
- KPI cards strip
- ranking widgets section
- composition/distribution charts section
- comparative scatter plot section
- chart disclaimer / metric definition note
- link or tab access to product catalog grid

### KPI Cards
최소 카드:
- total active products
- selected scope 최고 표시 금리
- fee-free 또는 low-fee candidate count
- recently changed products count

### Ranking Widgets
최소 2개 이상 구현:
- Highest Rate Top 5
- Lowest Monthly Fee Top 5
- Lowest Minimum Balance/Deposit Top 5
- Recently Updated Top 5

### Comparative Charts
최소 차트:
- products by bank (bar chart 또는 동등 표현)
- products by type (bar/pie/stacked chart 중 택1)
- scatter plot 1개 이상

### Scatter Plot Rules
권장 축:
- Savings / GIC: X = minimum balance or minimum deposit, Y = displayed rate
- GIC alternative: X = term length, Y = displayed rate
- Chequing: X = monthly fee, Y = minimum balance 또는 equivalent convenience metric

필수 동작:
- chart는 현재 filter scope를 반영해야 한다.
- point hover 또는 equivalent interaction으로 상품명/은행명/핵심 지표를 확인할 수 있어야 한다.
- 축 라벨과 metric meaning이 명확히 표시되어야 한다.

Acceptance Criteria:
- 공개 dashboard에서 최소 2개 ranking widget과 1개 scatter plot이 노출되어야 한다.
- “최대 금리 Top 5”와 동등한 rate ranking이 포함되어야 한다.
- chart가 선택된 product type과 충돌하지 않는 의미를 가져야 한다.
- 주요 차트와 KPI는 최신 refresh 시각을 표시해야 한다.
- chart title, axis label, methodology note는 EN/KO/JA locale을 지원해야 한다.

## 11.3 Admin Overview Dashboard
운영자가 선택한 locale에 따라 navigation, widget title, status label을 EN / KO / JA로 볼 수 있어야 한다.

필수 위젯:
- total products
- products by bank
- products by type
- runs today/this week
- queued review count
- approval rate
- recent failures
- recently changed products
- dashboard refresh status
- metric aggregation health

## 11.4 Review Queue
필수 컬럼:
- task id
- bank
- country
- product type
- product name
- issue type
- confidence
- created at
- status

필수 액션:
- open detail
- approve
- reject
- edit & approve

## 11.5 Review Detail / Trace Viewer
필수 패널:
- candidate summary
- normalized fields
- source evidence panel
- validation issues panel
- decision form
- override diff preview
- action history

## 11.6 BX-PF Publish Monitor
필수 기능:
- publish 대상 목록
- publish status
- retry / failure reason
- target master id mapping

## 11.7 LLM Usage Dashboard
필수 기능:
- model별 usage
- agent별 usage
- run별 token/cost
- 기간별 usage trend
- anomaly candidate drilldown

## 11.8 Admin Source Registry Management
필수 기능:
- bank 목록 조회 및 생성/수정
- bank code 자동 생성
- source catalog 목록 조회
- bank dropdown / product type dropdown 기반 catalog 생성/수정
- 다건 선택
- 선택 source catalog 기준 수집 실행
- generated source registry 조회
- 최근 실행 run으로 drilldown

수집 실행 규칙:
- 기본 의미는 `normalized_candidate`까지 생성하는 full collection
- `detail` source는 기본 candidate-producing scope
- supporting source는 evidence support를 위해 포함될 수 있으나 기본적으로 standalone candidate를 만들지 않는다


Current live admin behavior:
- bank create can include initial coverage selection for the currently supported product types
- bank detail can add more coverage and launch per-coverage collection
- bank list can multi-select banks and bulk-launch collection across all attached coverage items

Later follow-on requirement:
- operator-managed dynamic product type onboarding should exist as a separate management surface
- that later product type registry should support searchable `name` and `description`
- AI-assisted discovery should be able to use those product type definitions when inferring bank-site URLs from a homepage

---

## 12. Workflow Requirements

## 12.1 End-to-End Workflow
1. Scheduler triggers crawl job
2. Source pages/PDFs are discovered
3. Snapshot is stored
4. Text is parsed and chunked
5. Retrieval-ready evidence is stored
6. Extraction agent proposes structured fields
7. Normalization agent maps to canonical schema
8. Validation agent checks rule consistency
9. Confidence/review decision agent routes:
   - auto-approve candidate
   - or send to review queue
10. Approved records are prepared for BX-PF publish
11. BX-PF publish is executed or queued depending on environment readiness
12. Product grid index and dashboard metric aggregates are refreshed
13. Ranking/scatter dataset is regenerated or refreshed
14. Change history is updated
15. Admin can inspect and override if needed

## 12.3 Source Registry Collection Workflow
1. Admin opens bank registry
2. Admin creates or edits a bank profile if needed
3. Admin adds one or more bank-owned coverage items for the desired product types
4. Admin starts collection either from a single bank coverage item or from a multi-bank bank-list bulk selection
6. System materializes or refreshes generated source rows for the selected catalog scope
7. System records the selected source scope for the run
8. System fetches, parses, extracts, normalizes, and validates the selected scope
9. `normalized_candidate` rows are persisted
10. Review tasks are created when validation/confidence rules require them
11. Admin drills into generated Sources, Runs, and Review surfaces to inspect the outcome

## 12.3A Deferred Dynamic Product Type Onboarding Workflow
1. Admin opens a dedicated product type management surface
2. Admin creates or edits a product type with at least `name` and `description`
3. Admin searches that product type when attaching coverage to a bank
4. AI-assisted discovery uses the stored product type definition when inferring relevant bank-site URLs from the homepage, with deterministic candidate generation plus AI parallel scoring and page-level evidence validation
5. Parser and normalization flows either use dedicated product-type logic or fall back to an approved safe handling path

## 12.2 Review Workflow
1. Candidate enters review queue
2. Admin opens task
3. Admin inspects evidence trace
4. Admin approves / rejects / edits
5. Reason is recorded
6. Audit history is stored
7. Canonical product and publish status are updated

## 12.3 Phase 2 API Workflow
1. External consumer authenticates
2. Consumer searches products or changes
3. API returns normalized response
4. Access / usage logs are stored
5. Errors and rate-limit events are traceable

---

## 13. Business Rules

### BR-001 Phase 1 Product Type Constraint
Phase 1 확정 상품군은 chequing, savings, gic이다.

### BR-001A Deferred Product Type Extensibility
FPDS now supports operator-defined product types for the admin registry and collection pipeline, with the matching AI-assisted discovery contract plus generic extraction, normalization, validation, and vocabulary fallback rules. Those dynamic types remain review-first and are not implicitly widened into downstream public publish behavior without later approved slices.

### BR-002 Phase 2 Country Constraint
Phase 2 확정 범위는 일본 Big 5 은행의 수신상품이다.

### BR-003 Out-of-Scope Expansion Rule
일본 전체 금융기관 확대, 여신/카드 확대, 추천/인사이트 서비스는 별도 후속 프로젝트로 다룬다.

### BR-004 Evidence Requirement
핵심 필드는 가능한 한 evidence linkage를 가져야 한다.

### BR-005 Review Routing Rule
다음 경우 review queue로 보낸다.
- confidence below threshold
- required field missing
- conflicting evidence
- invalid rate range
- ambiguous mapping
- source parsing failure with partial extraction

### BR-006 Manual Override Rule
수동 수정은 반드시 actor, timestamp, changed fields, reason을 남겨야 한다.

### BR-007 Public Exposure Rule
공개 사이트에서는 내부 trace / evidence / log를 노출하지 않는다.

### BR-008 BX-PF Publish Rule
BX-PF는 승인된 정규화 상품정보의 target master store이며, 실제 publish 성공 여부는 별도 publish status로 추적해야 한다.

### BR-009 LLM Governance Rule
LLM 사용량과 비용은 agent/run 단위로 추적 가능해야 한다.

### BR-010 Dashboard Metric Consistency Rule
공개 dashboard의 KPI, ranking, scatter plot은 canonical product 데이터 또는 동등한 검증된 aggregate source로부터 계산되어야 한다.

### BR-011 Product-Type Visualization Rule
의미가 맞지 않는 시각화는 노출하지 않으며, product type별로 비교 기준을 다르게 적용할 수 있어야 한다.

---

## 14. Non-Functional Requirements

## 14.1 Performance
- Public dashboard initial load should feel fast on common broadband/mobile.
- Product grid와 insight dashboard는 실사용 가능한 수준의 interaction latency를 유지해야 한다.
- API search 응답은 실사용 가능한 수준의 latency를 유지해야 한다.
- caching strategy를 고려한다.

## 14.2 Reliability
- 실패한 run은 재시도 가능해야 한다.
- partial failure가 전체 시스템 중단으로 이어지지 않아야 한다.
- BX-PF publish 실패는 별도 재처리 가능해야 한다.

## 14.3 Security
- admin route와 internal ops API는 인증 필요
- external API는 인증/권한 통제 필요
- RBAC와 최소권한 원칙 적용
- multi-tenant external API 제공 시 tenant isolation 보장
- browser-facing API는 CORS allowlist 및 preflight 정책 적용
- cookie/session 기반 인증 사용 시 CSRF 방어와 HttpOnly/Secure/SameSite 적용
- 모든 외부 입력에 대해 validation, output encoding, injection defense 적용
- Public/Admin UI는 XSS 방어 및 CSP 적용
- crawler/fetcher는 SSRF 방어 정책과 safe fetch 제한 적용
- admin login/API/external API는 rate limit 및 brute-force protection 적용
- secret 관리 및 rotation 절차 필요
- HTTPS/HSTS 및 기본 보안 헤더 적용
- public/private/admin/tenant data separation 보장
- 상세 요구사항은 8.8 Security and Access Control Requirements를 따른다.

## 14.4 Auditability
- review decision history 보관
- run log 보관
- source snapshot 보관
- publish history 보관
- field override diff 보관
- llm usage history 보관
- login success/failure, privilege change, credential issuance/revocation 등 security-sensitive event 보관

## 14.5 Maintainability
- modular folder structure
- typed schemas
- documented environment setup
- clear README
- predictable component boundaries

## 14.6 Localization
- English/Korean/Japanese UI text와 설정/메타데이터 label 분리 관리
- locale fallback 전략(예: JA 미번역 시 EN fallback) 정의
- Japan source 처리 시 일본어 parsing/normalization 고려
- number/date/currency formatting과 label pluralization/localization 고려
- 상품명/설명/조건 등 source-derived 상품정보는 수집된 언어 단일 값으로 저장/표시하고 locale별 중복 필드를 두지 않는다

---

## 15. Suggested Technical Approach

## 15.1 Architecture Direction
권장 아키텍처 방향은 아래와 같다.

- Manager-pattern Multi-Agent System
- MCP-based tool/data interface
- Evidence store + retrieval layer
- Normalization / validation / review pipeline
- BX-PF connector
- LLM usage tracker
- Public dashboard + Admin console + External API

## 15.2 Suggested Stack
권장 기술 스택은 아래와 같다.

- Frontend / Admin / Public dashboard: Next.js
- UI: Tailwind CSS + shadcn/ui
- BFF: Next.js route handlers
- Background workers / crawler / parsing / orchestration: AWS 쪽 별도 서비스
- Database: Postgres
- Auth: Supabase Auth
- Validation: Zod
- Error Tracking: Sentry
- Hosting: public web/admin : Vercel
- Hosting: crawler/worker/storage/private integration : AWS
- File/object storage: S3-compatible storage
- Search / vector: Phase 1은 pgvector, 이후 필요 시 분리
- LLM provider: OpenAI 기본, provider abstraction 유지
- Integration layer: MCP는 connector boundary에만 선별 적용

---

## 16. Data Storage Strategy

## 16.1 Source of Truth by Domain

| Domain | System of Record |
|---|---|
| source registry | FPDS DB |
| source snapshots / parsed text / evidence chunks | FPDS |
| run logs / trace / review history | FPDS |
| llm usage / cost history | FPDS |
| dashboard aggregates | FPDS |
| external API delivery cache / index | FPDS |
| approved normalized product master | BX-PF (target), with FPDS publish/reconciliation metadata |

## 16.2 Storage Layers
- Source Evidence Store
- Parsed Text / Chunk Store
- Vector / Retrieval Metadata Store
- Candidate / Review Store
- Ops / Audit Store
- LLM Usage Store
- Publish / Reconciliation Store
- Translation / Locale Resource Store

---

## 17. API / Interface Draft

## 17.1 Public APIs / Routes
- `GET /api/public/products`
- `GET /api/public/filters`
- `GET /api/public/dashboard-summary`
- `GET /api/public/dashboard-rankings`
- `GET /api/public/dashboard-scatter`

## 17.2 Admin APIs / Routes
- `GET /api/admin/review-tasks`
- `GET /api/admin/review-tasks/:id`
- `POST /api/admin/review-tasks/:id/approve`
- `POST /api/admin/review-tasks/:id/reject`
- `POST /api/admin/review-tasks/:id/edit-approve`
- `GET /api/admin/products`
- `GET /api/admin/products/:id`
- `GET /api/admin/runs`
- `GET /api/admin/runs/:id`
- `GET /api/admin/change-history`
- `GET /api/admin/banks`
- `POST /api/admin/banks`
- `GET /api/admin/banks/:id`
- `PATCH /api/admin/banks/:id`
- `GET /api/admin/source-catalog`
- `POST /api/admin/source-catalog`
- `GET /api/admin/source-catalog/:id`
- `PATCH /api/admin/source-catalog/:id`
- `POST /api/admin/source-catalog/collect`
- `GET /api/admin/sources`
- `POST /api/admin/sources`
- `GET /api/admin/sources/:id`
- `PATCH /api/admin/sources/:id`
- `POST /api/admin/source-collections`
- `GET /api/admin/bxpf-publish`
- `GET /api/admin/llm-usage`

## 17.3 Internal Orchestration Interfaces
- source discovery interface
- evidence retrieval interface
- schema lookup interface
- normalization rule interface
- review queue create/update interface
- llm usage capture interface
- BX-PF connector interface

## 17.4 External SaaS/Open API (Phase 2)
- `GET /api/v1/products`
- `GET /api/v1/products/:id`
- `GET /api/v1/banks`
- `GET /api/v1/changes`

---

## 18. Acceptance Criteria by Stage

## 18.1 Prototype Acceptance
- TD savings 대상 source 수집 성공
- evidence 저장 성공
- canonical candidate 생성 성공
- basic internal UI에서 결과 확인 가능
- 최소 1개 end-to-end 성공 run 존재

## 18.2 Phase 1 Acceptance
- Big 5 + 3 product categories configured
- public dashboard 익명 접근 가능
- public product catalog grid 동작
- public insight dashboard에서 최소 2개 ranking widget + 1개 scatter plot 동작
- trilingual public/admin UI 작동
- admin authentication 및 role-based authorization 작동
- admin review queue 작동
- admin source registry 관리 화면 작동
- source registry에서 다건 선택 후 `normalized_candidate`까지 생성하는 수집 실행 가능
- evidence trace 확인 가능
- run status / change history 확인 가능
- Public/Admin web에 보안 헤더 및 기본 CSP 정책 적용
- cookie/session 기반 admin 인증을 사용할 경우 CSRF 방어 및 secure cookie 정책 적용
- crawler/fetcher에 SSRF safe fetch 정책 적용
- BX-PF connector 인터페이스 구현 완료
- BX-PF 연계 환경 충족 시 approved products write-back 가능
- BX-PF 미연계 시 publish pending / retry / reconciliation 상태 추적 가능
- LLM usage / cost dashboard 작동
- monitoring / error tracking enabled
- README and environment setup documented

## 18.3 Phase 2 Acceptance
- Japan Big 5 deposit scope configured
- 일본어 source 수집/파싱/정규화 가능
- external API auth 동작
- external API client/tenant scope, rate limit, audit separation 동작
- external API CORS allowlist 및 abuse protection 동작
- external API product search 동작
- delta query or change feed 동작
- source_language 포함 product response 및 locale-aware enum/label control 동작
- API 문서 제공(최소 English / Japanese)
- API usage / error monitoring enabled

---

## 19. MVP Cutline vs Later Enhancements

## 19.1 Must Have in Current Contract Scope
- Prototype single-bank validation
- Phase 1 Canada Big 5 deposit coverage
- Review queue
- Evidence trace viewer
- Change history
- Run status
- BX-PF connector
- LLM usage monitoring
- Public dashboard
- Trilingual UI support
- Phase 2 Japan Big 5 deposit expansion
- External SaaS/Open API

## 19.2 Later Enhancements
- personalized recommendation
- institution portal
- market analysis / product map / insight services
- Japan full-market expansion
- loan / card expansion
- richer analytics and reporting
- advanced compare mode / personalized watchlist

---

## 20. Risks and Mitigations

| Risk | Description | Mitigation |
|---|---|---|
| Source variability | 은행별 구조 차이 큼 | evidence-first extraction, review fallback |
| PDF parsing quality | PDF 구조 추출 불안정 가능 | snapshot + parsed text + review fallback |
| BX-PF dependency | 실제 연동 환경/권한 미정 | interface first + conditional acceptance + reconciliation metadata |
| Cross-country taxonomy drift | 캐나다/일본 상품 분류 차이 | canonical core + locale subtype mapping |
| Japanese source complexity | 일본어 문서 해석/정규화 난이도 | locale-aware prompts + human review + BwJ collaboration |
| Cost drift | LLM/API/infra 비용 변동 | usage dashboard + cap governance + stage-level monitoring |
| Over-scope | 추천/인사이트까지 확장 욕심 | scope cutline 고정 |

---

## 21. Recommended Build Order

### Step 1. Foundation
- repo / env / auth / DB / i18n scaffold (EN / KO / JA)
- evidence storage
- monitoring
- baseline security controls (RBAC, secure session strategy, CORS policy, secret management, security headers)
- README

### Step 2. Prototype Pipeline
- TD savings source discovery
- snapshot / parsing / chunking
- candidate generation
- internal result viewer

### Step 3. Phase 1 Admin and Ops Core
- review queue
- trace viewer
- run status
- change history
- llm usage tracking

### Step 4. Phase 1 Canada Expansion
- Big 5 source coverage
- chequing / savings / gic
- public dashboard
- EN / KO / JA locale rendering
- BX-PF connector

### Step 5. Phase 1 Publish Readiness
- BX-PF publish workflow
- pending/retry/reconciliation handling
- operational documentation

### Step 6. Phase 2 Japan Expansion
- Japan Big 5 source inventory
- Japanese source normalization
- locale-aware taxonomy mapping

### Step 7. Phase 2 API Delivery
- external auth
- search/detail/change API
- source_language-aware product response + locale-aware enum/label control
- multilingual API docs
- API monitoring

---

## 22. Open Items for Detailed Design
아래 항목은 후속 상세설계 단계에서 더 구체화한다.

- exact BX-PF write contract and field mapping
- country-specific deposit subtype taxonomy
- confidence threshold 수치
- exact validation rules by field
- Japan Big 5 최종 대상 은행 목록
- API auth 방식
- API rate limit / SLA 기준
- admin auth의 session cookie vs token 전략
- RBAC role matrix와 승인권한 세부 범위
- external API tenant isolation 단위와 credential scope 설계
- CORS allowlist 및 environment별 origin policy
- crawler SSRF 방어를 위한 network egress / allowlist 정책
- cache TTL and refresh strategy
- dashboard KPI formula와 ranking 기준 정의
- product type별 scatter plot axis 최종 정의
- vector indexing implementation detail
- UI localization workflow ownership
- Japanese fallback policy and terminology glossary ownership

---

## 23. Final Product Boundary Statement

본 프로젝트의 핵심은
**“Prototype으로 기술 검증을 수행하고, Phase 1에서 캐나다 Big 5의 주요 수신상품을 evidence 기반으로 수집·정규화·검증·검수하여 운영 가능한 데이터 인프라와 공개 Product Grid + Insight Dashboard를 만들고, Phase 2에서 일본 Big 5의 수신상품 DB와 외부 SaaS/Open API를 제공하는 것”** 이다.

즉, 지금 만드는 것은 MyBank 추천 서비스가 아니라
**검증 가능한 금융상품 데이터를 생산·운영·제공하는 FPDS 플랫폼** 이다.

---

## Appendix A. Product Owner Decisions Reflected
본 문서에는 아래 결정사항을 반영했다.

- 문서명은 `FPDS Requirements Definition`
- Prototype / Phase 1 / Phase 2 모두 본문 범위에 포함
- BX-PF는 Phase 1의 필수 인터페이스
- 실제 BX-PF write-back은 연계 환경/조건 충족 시 mandatory acceptance
- Prototype 저장소는 FPDS 내부 임시 DB
- Phase 1 공개 dashboard는 익명 공개
- 공개 화면에는 Product Catalog Grid와 Insight Dashboard를 포함
- Public/Admin UI는 English/Korean/Japanese를 지원
- 상품정보는 locale별 복수 번역 필드가 아니라 source language 단일 값으로 관리
- Admin 화면은 별도 로그인 필요
- LLM usage / cost monitoring을 요구사항에 포함
- Phase 2 범위는 일본 Big 5 수신상품 DB + SaaS/Open API
- 맞춤 추천 및 인사이트 서비스는 후속 MyBank 프로젝트 범위
