# FPDS 디자인 시스템 v1
**Stripe 벤치마크 기반 설계안**

## 0. 문서 목적

본 문서는 FPDS(Finance Product Data Service)를 위한 **실행 가능한 디자인 시스템 기준서**다.
벤치마크는 Stripe의 제품 경험과 정보 밀도, 상태 커뮤니케이션, 토큰 중심 스타일 철학을 참고하되, FPDS는 **금융상품 데이터 인프라 / 금융 인텔리전스 플랫폼**이라는 성격에 맞게 재구성한다.

이 문서는 다음 전제를 반영한다.

- Public 사이트의 홈은 별도 마케팅 홈페이지가 아니라 **바로 `/dashboard`** 다.
- Public은 **Product Grid + Insight Dashboard** 중심이다.
- Admin은 **review / trace / runs / changes / publish / usage / health** 중심의 운영 콘솔이다.
- 디자인은 Stripe와 **구조는 가깝게**, 브랜드 무드와 토큰은 **FPDS 고유**로 설정한다.
- 테마는 **Light only** 기준이다.
- 정보 밀도는 **Public = balanced / Admin = compact** 기준이다.

---

## 1. FPDS에 맞는 Stripe 벤치마크 해석

### 1.1 그대로 가져올 것

1. **절제된 제품 표면**
   - 큰 데이터 화면에서 배경은 밝고 차분해야 한다.
   - 카드와 테이블은 과한 장식 대신 얇은 border와 낮은 shadow로 구분한다.
   - 페이지는 “브랜드 쇼케이스”보다 “업무 수행”이 먼저 읽혀야 한다.

2. **강한 구조, 약한 장식**
   - 좌측 내비게이션, 상단 검색/유틸, 본문 헤더, sticky filter, 카드/테이블/상태배지 구조를 우선한다.
   - 컴포넌트는 개별 화면마다 새로 꾸미지 않고, 토큰과 패턴으로 반복한다.

3. **컨텍스트 중심 UX**
   - 사용자가 현재 보고 있는 상태를 잃지 않게 한다.
   - Public은 동일한 filter scope를 Grid와 Insights가 공유한다.
   - Admin은 list → detail → trace → action 흐름이 끊기지 않아야 한다.

4. **상태 커뮤니케이션의 명확함**
   - banner, toast, badge, empty state, skeleton, no-data, stale 상태를 분리한다.
   - 운영 리스크가 큰 화면은 “정상인지 / 조치가 필요한지”가 즉시 보여야 한다.

### 1.2 그대로 가져오지 않을 것

1. Stripe 메인홈의 강한 마케팅형 gradient hero
2. Stripe 고유의 보라-오렌지 브랜드 연출
3. 결제/인보이스 중심 CTA 구조
4. 브랜드보다 플랫폼 정체성이 앞서는 public marketing narrative

### 1.3 FPDS용 재해석

FPDS는 Stripe처럼 **운영형 B2B 제품 경험**을 가져가되, public 쪽은 “상품 탐색과 비교”를, admin 쪽은 “품질 검수와 운영 진단”을 더 강하게 드러낸다.

---

## 2. 제품 포지셔닝과 경험 원칙

### 2.1 제품 포지셔닝 문장

**FPDS는 은행 금융상품을 evidence-grounded 방식으로 수집, 정규화, 검증, 검수, 공개 제공하는 Financial Intelligence Platform이다.**

### 2.2 디자인 원칙

1. **Evidence before polish**
   - 예쁜 화면보다, 신뢰 가능한 데이터 구조와 상태 설명이 먼저다.

2. **Useful comparison over decorative charts**
   - 차트는 보기에 예쁜 것보다 실제 비교에 도움이 되어야 한다.

3. **Public and Admin are siblings, not clones**
   - Public과 Admin은 같은 토큰을 쓰되 밀도와 상호작용 목적은 다르다.

4. **Stable shells, changing data**
   - 레이아웃은 안정적으로 유지하고, 데이터와 상태만 자주 바뀌게 설계한다.

5. **One screen, one job**
   - 각 화면은 한 가지 주요 업무를 책임진다.
   - 예: Review Queue는 triage, Review Detail은 diagnosis + decision.

6. **Trilingual by default**
   - UI label은 EN/KO/JA를 지원하되 source-derived product text는 원문 유지 원칙을 따른다.

7. **Trust signals must be visible**
   - freshness, methodology, status, validation health, publish health를 숨기지 않는다.

---

## 3. 경험 구조

## 3.1 Public Experience

Public은 “메인홈”이 아니라 **Dashboard가 첫 화면**이다.

### Route baseline
- `/` → `/dashboard` 리다이렉트
- `/dashboard`
- `/dashboard/products`
- `/dashboard/insights`
- `/methodology`
- `/about`는 선택 사항

### Public의 핵심 목표
- 캐나다 Big 5의 수신상품 landscape를 빠르게 파악
- Product Grid에서 탐색
- Insight Dashboard에서 비교와 ranking 확인
- EN/KO/JA 전환
- evidence는 공개하지 않음

## 3.2 Admin Experience

Admin은 운영 콘솔이며, 아래 surface를 분리 유지한다.

- Overview
- Review Queue
- Review Detail / Trace
- Runs
- Change History
- Publish Monitor
- LLM Usage
- Dashboard Health

### Admin의 핵심 목표
- review queue triage
- evidence trace 확인
- run / change / publish / usage / health 진단
- 승인 / 반려 / 수정 승인
- 검색과 drilldown

## 3.3 Shared Experience Rules

- 동일한 product/status vocabulary를 Public/Admin 모두에서 공유
- badge, chip, table cell, empty state 문법을 재사용
- 숫자/날짜/통화 formatting은 locale-aware
- product name, evidence excerpt, source-derived condition text는 source language 유지

---

## 4. 브랜드와 비주얼 언어

## 4.1 무드 키워드

- Precise
- Credible
- Analytical
- Calm
- Contemporary

## 4.2 시각 톤

FPDS는 Stripe처럼 과감한 브랜드 장식보다 구조와 정보 밀도를 중시한다.
다만 Stripe의 차가운 제품 경험보다 **조금 더 현대적이고 분석적인 감도**를 위해, 아래만 제한적으로 허용한다.

- 상단 hero-lite strip 또는 section top edge에만 제한적 gradient
- 공용 accent는 **Indigo 중심**
- 데이터 강조는 **Blue / Teal / Amber / Rose** 보조색으로 분리
- 카드 본문과 테이블은 무채색에 가깝게 유지

## 4.3 시그니처 표현

FPDS의 시그니처는 “화려한 배경”이 아니라 아래 조합으로 정의한다.

- 강한 제목 타이포
- 안정적인 좌측 기준선 정렬
- 얇은 keyline
- 분명한 badge / chip / tab 상태
- 소수의 브랜드 accent
- 명확한 freshness / methodology / status 노출

---

## 5. 디자인 토큰

## 5.1 Color Tokens

### Neutral
| Token | Value | Usage |
|---|---:|---|
| `--bg-canvas` | `#F7F8FC` | 전체 페이지 배경 |
| `--bg-surface` | `#FFFFFF` | 카드, 패널, 표면 |
| `--bg-subtle` | `#F3F5FA` | 필터바, 탭 컨테이너, muted block |
| `--bg-muted` | `#EEF1F7` | hover, table header, soft emphasis |
| `--line-default` | `#D8E0EA` | 기본 border |
| `--line-strong` | `#C7D2E0` | 강조 border |
| `--text-strong` | `#111827` | page title, important value |
| `--text-default` | `#243042` | body text |
| `--text-muted` | `#667085` | helper text |
| `--text-soft` | `#98A2B3` | placeholder, tertiary text |

### Brand
| Token | Value | Usage |
|---|---:|---|
| `--brand-50` | `#EEF2FF` | subtle brand background |
| `--brand-100` | `#E0E7FF` | hover / selected soft bg |
| `--brand-500` | `#4F46E5` | primary interactive |
| `--brand-600` | `#4338CA` | primary hover |
| `--brand-700` | `#3730A3` | pressed / strong emphasis |
| `--brand-gradient-a` | `#4F46E5` | restrained hero top start |
| `--brand-gradient-b` | `#06B6D4` | restrained hero top end |

### Semantic
| Token | Value | Usage |
|---|---:|---|
| `--success-500` | `#16A34A` | approved, published, healthy |
| `--success-50` | `#ECFDF3` | success badge bg |
| `--warning-500` | `#D97706` | caution, deferred, stale soon |
| `--warning-50` | `#FFF7ED` | warning badge bg |
| `--danger-500` | `#DC2626` | failed, rejected, critical |
| `--danger-50` | `#FEF2F2` | danger badge bg |
| `--info-500` | `#2563EB` | informational state |
| `--info-50` | `#EFF6FF` | info badge bg |

### Chart
| Token | Value | Usage |
|---|---:|---|
| `--chart-1` | `#4F46E5` | category 1 |
| `--chart-2` | `#2563EB` | category 2 |
| `--chart-3` | `#0F766E` | category 3 |
| `--chart-4` | `#D97706` | category 4 |
| `--chart-5` | `#BE185D` | category 5 |
| `--chart-grid` | `#E5EAF2` | chart gridline |
| `--chart-axis` | `#667085` | axis text |

### Focus
| Token | Value |
|---|---:|
| `--focus-ring` | `#4F46E5` |
| `--selection-bg` | `#E0E7FF` |

---

## 5.2 Typography Tokens

### Font stack
- UI: `Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif`
- Numeric emphasis: same stack + `font-variant-numeric: tabular-nums`

### Type scale
| Token | Size / Line | Weight | Usage |
|---|---|---|---|
| `display-lg` | `48 / 56` | 700 | optional hero-lite headline |
| `display-md` | `36 / 44` | 700 | public page headline |
| `heading-xl` | `30 / 38` | 700 | admin/public page title |
| `heading-lg` | `24 / 32` | 700 | major section title |
| `heading-md` | `20 / 28` | 700 | card section title |
| `heading-sm` | `18 / 26` | 600 | widget title |
| `body-lg` | `16 / 24` | 400 | base body |
| `body-md` | `14 / 22` | 400 | default UI text |
| `body-sm` | `13 / 20` | 500 | dense tables, helper |
| `label-sm` | `12 / 18` | 600 | field label, chip, badge |
| `mono-sm` | `12 / 18` | 500 | ids, run ids, code-like values |

### Typography rules
- page title는 숫자와 텍스트를 함께 쓸 때도 baseline 정렬 유지
- KPI / money / rate는 tabular numerals 사용
- Public 카드의 숫자보다 단위와 label의 판독성을 우선
- source-derived product name은 2줄 clamp 허용, 임의 번역 금지

---

## 5.3 Spacing Tokens

| Token | Value |
|---|---:|
| `0` | `0px` |
| `1` | `4px` |
| `2` | `8px` |
| `3` | `12px` |
| `4` | `16px` |
| `5` | `20px` |
| `6` | `24px` |
| `8` | `32px` |
| `10` | `40px` |
| `12` | `48px` |
| `16` | `64px` |

### Rule
- 컴포넌트 내부는 4px 계열
- 카드/패널 패딩은 16px 또는 24px
- major section 간격은 32px
- Public desktop section 간격은 40~48px
- Admin compact table row gap은 8~12px

---

## 5.4 Radius Tokens

| Token | Value | Usage |
|---|---:|---|
| `--radius-sm` | `8px` | field, chip, small card |
| `--radius-md` | `12px` | standard card |
| `--radius-lg` | `16px` | large panel |
| `--radius-xl` | `20px` | login card / hero-lite panel |
| `--radius-pill` | `999px` | pills, segmented control |

### Rule
Stripe 벤치마크처럼 **둥글지만 과도하지 않은 radius**를 유지한다.
기본 card radius는 `12px`를 기준으로 고정한다.

---

## 5.5 Shadow Tokens

| Token | Value |
|---|---|
| `--shadow-xs` | `0 1px 2px rgba(16,24,40,.04)` |
| `--shadow-sm` | `0 2px 8px rgba(16,24,40,.06)` |
| `--shadow-md` | `0 8px 24px rgba(16,24,40,.08)` |

### Rule
- 기본 분리는 shadow보다 border 우선
- hover나 modal/card 강조 때만 shadow 증가
- Public/Admin 공통으로 heavy shadow 금지

---

## 5.6 Motion Tokens

| Token | Duration |
|---|---:|
| `fast` | `120ms` |
| `base` | `180ms` |
| `slow` | `240ms` |

### Rule
- hover, chip select, tab switch, toast, dropdown에만 제한 사용
- chart animation은 짧고 미세하게
- 운영 화면에서 attention을 끄는 motion 금지

---

## 6. Layout System

## 6.1 Global Grid

### Public
- max width: `1440px`
- content padding: `24px` mobile / `32px` desktop
- 12-column grid
- section spacing: `40px`

### Admin
- full-width fluid canvas
- left rail width: `248px`
- top utility bar height: `64px`
- content padding: `24px`
- table/list 중심 영역은 width 고정하지 않음

## 6.2 Public Shell

### Structure
1. top header
2. optional hero-lite strip
3. sticky shared filter bar
4. main content
5. footer / methodology links

### Public header
- 좌측: FPDS wordmark
- 중앙/우측: Products / Insights / Methodology
- 우측: locale switcher, last refresh pill
- 검색은 Public에서는 선택 사항

### Hero-lite
마케팅 hero가 아니라, 상단에만 제한적으로 쓰는 **market snapshot strip** 개념으로 사용한다.

허용 방식:
- 72~120px 높이
- left-aligned summary text
- 배경은 `brand-gradient-a → brand-gradient-b`를 6~10% opacity 수준으로만 사용
- CTA는 최대 1개
- 사용하지 않아도 무방

## 6.3 Admin Shell

### Structure
1. fixed left rail
2. top utility bar
3. page header
4. section content
5. optional sticky bottom action area

### Left rail
그룹 구조:
- Overview
- Review
- Operations
- Observability

부가 영역:
- environment badge
- current org / tenant
- collapse 가능
- footer에 version / keyboard help

### Top utility
- global search
- quick create / quick action
- locale switch
- alert center
- session menu

### Page header
- title
- scope summary
- page-level actions
- optional secondary tabs

---

## 7. Navigation and IA

## 7.1 Public IA

### `/dashboard`
대시보드 홈.
Products와 Insights 둘 중 어느 하나를 “부가 메뉴”로 두지 않고, 모두 1차 탐색 항목으로 취급한다.

### `/dashboard/products`
- sticky filters
- result summary
- sort toolbar
- product card grid
- pagination

### `/dashboard/insights`
- KPI strip
- composition section
- ranking widgets
- scatter section
- methodology / freshness note

### `/methodology`
- metric definition
- freshness meaning
- inclusion / exclusion logic
- source-derived text policy
- public evidence non-exposure 안내

## 7.2 Admin IA

### Primary nav
- `/admin`
- `/admin/reviews`
- `/admin/runs`
- `/admin/changes`
- `/admin/publish`
- `/admin/usage`
- `/admin/health/dashboard`

### Contextual routes
- `/admin/reviews/:reviewTaskId`
- `/admin/runs/:runId`
- `/admin/products/:productId`

### Rule
- Product Record는 primary nav가 아니라 contextual diagnostic surface
- Review / Runs / Changes / Publish / Usage / Health를 혼합 dashboard 하나로 합치지 않음

---

## 8. Core Components

## 8.1 App Header

### Public
- 높이 `64px`
- background `bg-canvas`
- bottom border 1px
- active nav는 underline이 아니라 text color + subtle pill bg 조합

### Admin
- 높이 `64px`
- 검색 바 중심
- utility icon group 우측 정렬
- header 자체는 강한 box보다 background continuity 유지

---

## 8.2 Page Header

### Anatomy
- eyebrow or scope
- page title
- brief explanatory line
- primary action 1개
- secondary actions 0~3개
- secondary tabs 가능

### Rule
- title area와 actions area를 한 줄에 두되, 모바일에서는 세로 stack
- primary action은 1개만 채색 버튼
- destructive는 page header primary 자리에 두지 않음

---

## 8.3 Cards

### Standard card
- background: `--bg-surface`
- border: `1px solid var(--line-default)`
- radius: `12px`
- padding: `16px` or `24px`
- shadow: `--shadow-xs`

### Elevated card
- shadow `--shadow-sm`
- 사용처: login, modal, hero-lite summary

### Dense card
- padding: `16px`
- title + value + mini chart / meta
- admin overview widgets, ranking widgets

---

## 8.4 KPI Card

### Public KPI Card
구성:
- label
- value
- unit
- scope note or freshness hint

스타일:
- label `body-sm`
- value `heading-xl` 또는 `heading-lg`
- border-only
- 4개 카드가 균등한 시각적 weight를 가져야 함

### Admin KPI Card
구성:
- label
- value
- delta / status
- drilldown link

스타일:
- compact
- 중요 widget은 caution/default/danger top edge accent 허용

---

## 8.5 Filter Bar

### Public
- sticky
- background `bg-canvas` 또는 `bg-surface`
- bottom border
- 필터는 chip + dropdown hybrid
- active filters는 항상 보임
- clear all 존재
- result summary와 dashboard sibling entry를 가까이 둠

### Admin
- compact
- dense chip row + date range + search within page
- bulk action이 없는 페이지는 필터와 액션을 과도하게 섞지 않음

---

## 8.6 Chips and Badges

### Filter chip
- height `32px`
- subtle border
- selected state = brand text + brand-50 bg + brand-100 border

### Status badge
- 높이 `24px`
- rounded pill
- icon optional
- color는 status semantics 고정

#### Status mapping
- queued / pending / in review → info
- approved / published / healthy → success
- deferred / reconciliation / stale soon → warning
- rejected / failed / critical → danger

### Highlight badge
Public product card에서 1개만 우선 노출
- High Rate
- Low Fee
- Low Minimum Deposit
- Recent Change
- Student
- Newcomer

---

## 8.7 Tabs

### Public
- products / insights sibling tabs 가능
- underline 2px + text emphasis
- section top에 위치

### Admin
- page 내부 secondary segmentation에만 사용
- overview 내 tab 남발 금지
- review detail에서 “candidate / trace / history” 형태보다는 split-pane 우선

---

## 8.8 Data Table

### Standard
- row height `48~56px`
- header bg `bg-muted`
- row border separator
- hover subtle bg
- first column sticky optional

### Compact admin table
- row height `44~48px`
- font `body-sm`
- inline badge와 mono id 지원
- actions는 끝 column kebab + primary inline link

### Rule
- 대용량 데이터는 기본적으로 table
- Grid는 Public product catalog에만 사용
- mobile에서 admin tables는 card stack으로 완전 재해석하지 말고, 최소 read-only table scrolling 허용

---

## 8.9 Ranking Widget

구성:
- widget title
- methodology hint
- ranked rows 5개
- metric label / value
- optional “view all filtered products”

스타일:
- dense white card
- 각 row는 44px 전후
- rank는 숫자보다 index marker 성격
- metric value는 source text보다 우측 정렬

---

## 8.10 Scatter / Chart Card

구성:
- title
- brief note
- chart controls
- chart canvas
- methodology footnote

스타일:
- chart area min height `320px`
- gridline는 매우 얇고 연함
- tooltip은 white surface + border + shadow-xs
- point hover 확대는 1.15x 이내

### Rule
- mixed-type scope에서는 scatter를 기본값으로 호출하지 않음
- type-specific scope에서만 default scatter 노출
- insufficient data 시 chart 대신 chart-empty card 노출

---

## 8.11 Banner

사용 시점:
- stale data
- retry needed
- reconciliation needed
- changed methodology
- login / security / publish notice

스타일:
- full-width under page header
- icon + title + body + action + dismiss
- type: default / caution / critical

### Rule
- banner는 **persistent**
- user action이 필요한 경우에만 사용
- page마다 최대 1개의 primary banner만

---

## 8.12 Toast

사용 시점:
- approve 성공
- reject 완료
- settings 저장
- publish 재시도 시작
- filter preset 저장

### Rule
- short text
- auto-dismiss
- user-triggered event에만 사용
- 페이지 상태 설명용으로 toast 남용 금지

---

## 8.13 Empty / No Data / Error State

### Public empty state
- 현재 filter scope를 설명
- clear filters CTA
- insights or products sibling link 제공
- illustration은 최소화, 아이콘 우선

### Admin no-data state
- dashed border panel 허용
- 예: failed payments 없음, no payouts, no review items
- “정상이라서 비어 있음”과 “문제가 있어서 못 불러옴”을 분리

### Error state
- title
- short explanation
- retry action
- correlation id or request id는 admin에서만 표시 가능

---

## 8.14 Skeleton Loading

- filters skeleton
- KPI skeleton
- card grid skeleton
- chart skeleton
- table row skeleton

### Rule
- 예상되는 최종 구조와 동일한 레이아웃 skeleton 제공
- spinner-only loading 금지

---

## 8.15 Locale Switcher

- EN / KO / JA 3-way segmented or dropdown
- Public/Admin 모두 동일 component 사용
- active locale는 session or local storage에 유지
- product name 자체는 locale switch로 번역되지 않음

---

## 8.16 Evidence Trace Row

Admin 전용.

구성:
- field name
- candidate value
- evidence source
- chunk excerpt
- citation anchor / chunk id
- confidence
- model run ref

스타일:
- table보다 inspection panel에 가까운 dense list
- selected field와 evidence는 같이 highlight
- raw storage path는 노출 금지

---

## 8.17 Diff Viewer

Admin 전용.

구성:
- before
- after
- changed by
- reason
- timestamp

스타일:
- split diff보다 field-group diff 우선
- changed rows만 색약 친화적 tinted background
- red/green 단독 구분 금지, icon/text 함께 사용

---

## 9. Page Templates

## 9.1 Public Home = `/dashboard`

### 목적
메인홈 없이 바로 “시장 이해”로 진입한다.

### 추천 구조
1. restrained market snapshot strip 또는 바로 page header
2. shared filter bar
3. KPI row
4. composition section
5. ranking widgets
6. product preview strip 또는 full insights flow로 연결
7. methodology/freshness note

### 핵심 규칙
- 첫 화면에서 marketing story보다 actual market state가 먼저 보여야 한다.
- “Products 보기”와 “Insights 보기”는 동등한 1차 액션이다.
- evidence는 숨기고 freshness와 metric meaning만 보여준다.

---

## 9.2 Public Products

### 구조
1. header
2. sticky filter bar
3. result summary row
4. sort toolbar
5. product grid
6. pagination
7. sibling nav to insights

### Grid columns
- `≥ 1440`: 4 columns
- `1200 ~ 1439`: 3 columns
- `768 ~ 1199`: 2 columns
- `< 768`: 1 column

### Product card structure
1. bank
2. product type badge
3. product name
4. metric strip 3개
5. highlight badge
6. target tag
7. freshness line

### Product-type metric emphasis
- `chequing`: fee → minimum balance → fee waiver or recent change
- `savings`: display rate → minimum balance → promo/high-interest hint
- `gic`: display rate → term length → minimum deposit

---

## 9.3 Public Insights

### mixed-type 기본 구조
1. KPI strip
2. products by bank
3. products by product type
4. highest display rate ranking
5. recently changed 30d ranking
6. methodology note

### single-type 기본 구조

#### chequing
1. lowest monthly fee
2. recently changed
3. fee vs minimum balance scatter

#### savings
1. highest display rate
2. recently changed
3. rate vs minimum balance scatter

#### gic
1. highest display rate
2. lowest minimum deposit
3. rate vs minimum deposit scatter
4. optional alternate term vs rate chart

### chart behavior
- hover: bank, product, metric values
- click: filtered grid or detail context로 연결 가능
- insufficient data 시 chart 숨기고 note 표시

---

## 9.4 Methodology Page

### 필수 섹션
- data scope
- included banks
- included product types
- metric definitions
- ranking logic
- scatter axis meaning
- freshness meaning
- what is not shown publicly
- source-derived text policy

### 톤
- 법률 고지처럼 차갑게 쓰지 않는다.
- 간결하고 검증 가능한 설명 중심.

---

## 9.5 Admin Login

### 구조
- neutral canvas
- centered elevated card
- wordmark
- title
- email / password
- remember me
- primary submit
- SSO optional
- footer links

### 스타일
- public 마케팅 gradient 사용 금지
- 상단 1px brand accent line 또는 카드 상단 subtle tint 정도만 허용
- card width `440~520px`

### 목표
“secure ops console”로 느껴져야 하며, public 사이트와 시각적으로 연결되되 더 절제되어야 한다.

---

## 9.6 Admin Overview

### 구조
1. page header
2. urgent attention strip
3. KPI widgets
4. recent failures / queued reviews / publish retry panels
5. recent changes
6. dashboard health / usage summary

### 레이아웃
- 12-column grid
- 우선순위 위젯은 상단 2줄 안에
- no-data widget은 dashed empty 허용

### 핵심 원칙
overview는 decision entrypoint이지, 모든 업무를 처리하는 화면이 아니다.

---

## 9.7 Review Queue

### 구조
1. header
2. sticky filters
3. summary row
4. compact table
5. pagination

### columns
- task id
- bank
- product type
- product name
- issue summary
- confidence
- validation status
- created at
- review status

### 액션
- open detail = primary
- approve / reject / defer = optional inline
- edit & approve = detail에서만

---

## 9.8 Review Detail / Trace

### desktop layout
- left 7 cols: candidate summary + normalized fields + validation
- right 5 cols: evidence trace + decision form
- sticky action footer or side action box

### sections
1. candidate summary
2. normalized fields
3. validation issues
4. evidence trace
5. decision form
6. override diff preview
7. action history

### 규칙
- field 선택 시 trace pane 연동
- raw object path 비노출
- read_only는 action form 비노출

---

## 9.9 Runs

### list
- run id
- state
- started
- completed
- source count
- candidate count
- review queued
- success/failure
- partial completion
- error summary

### detail
1. run summary
2. stage strip
3. source processing summary
4. failures
5. related review tasks
6. usage summary

### 스타일
- operation diagnosis 화면으로서 mono id와 status badge의 판독성 최우선
- colorful chart보다 structured table/card 중심

---

## 9.10 Change History

### 구조
- filter row
- event list
- contextual product link

### event card / row
- change type
- summary
- changed fields
- detected at
- related review/run
- product link

### 강조
- New / Updated / Discontinued / Reclassified / ManualOverride를 동일한 status 문법으로 표기

---

## 9.11 Publish Monitor

### 구조
1. state summary row
2. filter bar
3. publish table
4. contextual product detail link

### 우선순위
- retry
- reconciliation
- pending
- published

### 스타일
- danger/warning row emphasis 허용
- 대기와 실패를 시각적으로 명확히 분리

---

## 9.12 LLM Usage

### 구조
1. time range
2. totals cards
3. by model
4. by agent
5. by run
6. trend
7. anomaly table

### 규칙
- public KPI와 절대 같은 문법으로 섞지 않는다.
- cost는 strong numeric hierarchy 사용
- anomaly는 row click으로 run detail drilldown

---

## 9.13 Dashboard Health

### 구조
- aggregate domain list
- freshness
- last success
- last attempt
- stale flag
- completeness
- cache ttl
- error summary

### 목표
Public dashboard 의미 설명이 아니라 **serving health**를 운영자에게 보여주는 화면.

---

## 10. Data Visualization System

## 10.1 공통 규칙

- mixed-type scope에서는 market overview 중심
- type-specific scope에서만 scatter를 기본 노출
- numeric field가 없는 상품은 ranking/scatter에서 제외
- eligible item이 3개 미만이면 chart/widget 대신 insufficiency note
- chart는 동일 scope의 latest successful snapshot 기준

## 10.2 KPI Strip

### Public
고정 4개:
- total active products
- banks in scope
- highest display rate
- recently changed products 30d

### Admin
고정이 아니라 page 목적에 따라 다르되, 숫자보다 actionability가 중요

## 10.3 Composition Charts

- bar / segmented bar / donut 중 1개만 선택
- products by bank
- products by type

### Preferred default
- products by bank = horizontal bar
- products by type = segmented bar or donut

## 10.4 Scatter Rules

### chequing
- X = effective fee
- Y = minimum balance

### savings
- X = minimum balance
- Y = public display rate

### gic
- X = minimum deposit
- Y = public display rate
- alternate = term length vs rate

### Style rules
- axis label 항상 표시
- zero baseline 필요 시만 사용
- tooltip에 rank를 억지로 넣지 않음
- “best quadrant”는 chequing/savings/gic 각각 note로만 설명

---

## 11. 상태 시스템

## 11.1 Review states
- queued
- approved
- rejected
- edited
- deferred

## 11.2 Run states
- started
- completed
- failed
- retried
- partial completion flag

## 11.3 Publish states
- pending
- published
- retry
- reconciliation

## 11.4 State UI rules
- state는 badge + text 동시 표현
- icon only 금지
- red/green only 의존 금지
- long-form explanation은 banner 또는 inline note로

---

## 12. Localization System

## 12.1 What is translated
- navigation
- page titles
- widget titles
- filter labels
- chart titles
- methodology notes
- badges / status labels / helper text

## 12.2 What is not translated
- product name
- description_short
- eligibility_text
- fee_waiver_condition
- evidence excerpt
- source-derived condition text

## 12.3 Fallback
`selected locale -> en -> safe fallback label`

## 12.4 Locale-aware formatting
- currency
- number
- date
- relative time
- percentage
- pluralization

### Note
source language와 display locale을 혼동하지 않게, product source language가 다를 경우 작은 보조 라벨로 표시할 수 있다.

---

## 13. Accessibility and Trust

## 13.1 Accessibility baseline
- WCAG AA 수준 대비 목표
- keyboard navigation
- visible focus ring
- chart 색상 단독 구분 금지
- badge에 text 포함
- table row hover만으로 정보 제공 금지
- locale switcher, filter chips, tabs는 최소 32~40px hit area

## 13.2 Trust baseline
- freshness 항상 visible
- methodology note 항상 reachable
- no public evidence exposure
- admin에서만 trace/evidence 접근
- run id / review task id / product id는 필요한 화면에서만 노출

---

## 14. 반응형 기준

## 14.1 Public
- mobile에서도 Product Grid 핵심 metric 유지
- filter는 drawer로 축소 가능
- KPI는 1열 또는 2열
- ranking widgets는 세로 stack

## 14.2 Admin
- desktop 우선
- tablet까지 실사용 가능
- mobile은 triage/read 중심
- Review Detail split-pane은 tablet 이하에서 stack or tabs 전환
- dense table은 horizontal scroll 허용 가능

---

## 15. 구현 매핑 가이드

## 15.1 Tailwind + shadcn 매핑

### Semantic mapping
| Design Token | Tailwind / shadcn semantic |
|---|---|
| `bg-canvas` | `background` |
| `bg-surface` | `card`, `popover` |
| `bg-subtle` | `secondary` |
| `bg-muted` | `muted` |
| `text-strong` | `foreground` strong usage |
| `text-muted` | `muted-foreground` |
| `brand-500` | `primary` |
| `brand-50` | `accent` bg |
| `line-default` | `border` |
| `focus-ring` | `ring` |
| `danger-500` | `destructive` |

### shadcn component base
- `Button`
- `Card`
- `Badge`
- `Tabs`
- `Popover`
- `Tooltip`
- `Sheet`
- `Dialog`
- `Table`
- `DropdownMenu`
- `Select`
- `Skeleton`
- `Alert`

## 15.2 CSS Variable Baseline

```css
:root {
  --background: 247 248 252;
  --foreground: 17 24 39;

  --card: 255 255 255;
  --card-foreground: 36 48 66;

  --popover: 255 255 255;
  --popover-foreground: 36 48 66;

  --primary: 79 70 229;
  --primary-foreground: 255 255 255;

  --secondary: 243 245 250;
  --secondary-foreground: 36 48 66;

  --muted: 238 241 247;
  --muted-foreground: 102 112 133;

  --accent: 238 242 255;
  --accent-foreground: 67 56 202;

  --destructive: 220 38 38;
  --destructive-foreground: 255 255 255;

  --border: 216 224 234;
  --input: 216 224 234;
  --ring: 79 70 229;

  --radius: 12px;
}
```

## 15.3 Component Density Modes

### Public / Balanced
- base text `14px`
- card padding `24px`
- KPI card min height `132px`
- filters `40px` control height

### Admin / Compact
- base text `13px`
- card padding `16px`
- table row `44~48px`
- filters `32~36px` control height

---

## 16. FPDS에서 꼭 지켜야 할 안티패턴

1. Public dashboard를 marketing 랜딩처럼 만들지 않는다.
2. mixed-type scope에서 억지 scatter를 기본 노출하지 않는다.
3. source-derived 상품명을 locale별 번역 필드로 복제하지 않는다.
4. admin을 하나의 giant dashboard로 합치지 않는다.
5. evidence trace를 public에 노출하지 않는다.
6. strong shadow, glassmorphism, neon gradient를 사용하지 않는다.
7. 데이터가 부족한데도 ranking/chart를 강제로 채우지 않는다.
8. status를 color만으로 구분하지 않는다.
9. toast를 system health 설명에 쓰지 않는다.
10. Stripe의 exact purple/orange brand language를 복제하지 않는다.

---

## 17. 우선 적용 순서

### Phase A — Foundation
- token 정의
- typography / spacing / radius / shadow 고정
- Public/Admin app shell 구축
- status/badge/banner/toast 규칙 고정

### Phase B — Public
- `/dashboard` home
- Product Grid
- Insights
- Methodology
- EN/KO/JA 적용
- shared filter state

### Phase C — Admin
- login
- overview
- review queue
- review detail / trace
- runs
- changes
- usage
- dashboard health
- publish monitor

### Phase D — Polish
- hover / focus / responsive QA
- empty / loading / stale / insufficiency copy 정제
- chart tooltip / methodology note 정제
- locale QA
- accessibility QA

---

## 18. 최종 한 줄 기준

**FPDS는 Stripe처럼 안정적이고 절제된 구조를 가지되, 더 데이터 지향적이고 evidence-aware하며, public 비교 경험과 admin 운영 경험이 분명히 분리된 금융상품 데이터 플랫폼 UI로 설계한다.**
