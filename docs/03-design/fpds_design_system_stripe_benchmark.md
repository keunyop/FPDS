# FPDS 디자인 시스템 v2
**Stripe 벤치마크 + Shadcnblocks Template-First Baseline**

Version: 2.0
Date: 2026-04-13
Status: Working Baseline for Template-First Overhaul

Source Documents:
- `docs/02-requirements/FPDS_Requirements_Definition_v1_5.md`
- `docs/02-requirements/scope-baseline.md`
- `docs/03-design/product-grid-information-architecture.md`
- `docs/03-design/insight-dashboard-metric-definition.md`
- `docs/03-design/product-type-visualization-principles.md`
- `docs/03-design/admin-information-architecture.md`
- `docs/03-design/fpds-design-system.md` (pre-overhaul baseline)
- `https://docs.stripe.com/stripe-apps/design`
- `https://docs.stripe.com/stripe-apps/style`
- `https://docs.stripe.com/stripe-apps/patterns`
- `https://www.shadcnblocks.com/docs`
- `https://www.shadcnblocks.com/docs/blocks/getting-started`
- `https://www.shadcnblocks.com/docs/shadcn-cli/overview`
- `https://www.shadcnblocks.com/docs/blocks/styles`
- `https://www.shadcnblocks.com/docs/templates/getting-started`
- `https://www.shadcnblocks.com/docs/templates/project-structure`
- `https://www.shadcnblocks.com/docs/templates/adding-blocks`
- `https://www.shadcnblocks.com/admin-dashboard`

---

## 0. 문서 목적

본 문서는 FPDS(Finance Product Data Service)의 디자인 시스템을 **직접 설계한 bespoke UI 중심 방식에서, Shadcnblocks 상용 템플릿을 기반으로 구현하는 template-first 방식으로 전면 전환**하기 위한 기준서다.

이번 개편에서 고정하는 전제는 아래와 같다.

- Stripe는 여전히 **벤치마크**다.
- Shadcnblocks는 FPDS UI의 **실행 베이스와 구현 출발점**이다.
- FPDS는 더 이상 버튼, 카드, 배지, 테이블, 레이아웃 셸을 처음부터 새로 정의하는 프로젝트가 아니다.
- FPDS가 직접 설계해야 하는 범위는 **도메인 특화 화면과 상태 의미, 정보 구조, 데이터 시각화 규칙, 다국어, evidence boundary**다.
- Public은 계속해서 **Product Grid + Insight Dashboard** 중심이며, 첫 화면은 `/dashboard` 다.
- Admin은 계속해서 **review / trace / runs / changes / publish / usage / health** 중심의 운영 콘솔이다.
- 테마는 **Light only** 기준을 유지한다.
- 밀도는 **Public = balanced, Admin = compact** 기준을 유지하되, 이 차이는 Shadcnblocks 스타일과 페이지별 spacing override로 해결한다.

이 문서는 “Stripe와 비슷한 자체 UI를 만든다”가 아니라, **Stripe의 구조적 원칙을 유지하면서 Shadcnblocks를 FPDS의 공식 UI 플랫폼으로 채택한다**는 결정으로 이해해야 한다.

---

## 1. 이번 개편의 한 줄 결정

### 1.1 결정 문장

**FPDS는 Stripe를 정보 구조와 상태 커뮤니케이션의 벤치마크로 유지하되, 실제 화면 구현은 Shadcnblocks 템플릿과 블록을 기반으로 구성한다.**

### 1.2 책임 분리

| Layer | Source of Truth | FPDS에서 하는 일 |
|---|---|---|
| Product benchmark | Stripe | 구조, 밀도, state pattern, contextual workflow 원칙 참고 |
| UI implementation base | Shadcnblocks | template, shell, block, section, table, chart, layout의 출발점 사용 |
| Domain system | FPDS | 상품 비교 규칙, evidence boundary, review trace, status semantics, i18n, methodology, product-type-aware visualization 정의 |

### 1.3 이번 변경으로 바뀌는 핵심

기존 방향:
- bespoke token system을 먼저 만들고
- shell, card, table, filter, chart container를 FPDS 전용으로 직접 설계하고
- shadcn/ui는 그 구현 수단 중 하나로 사용

새 방향:
- **Shadcnblocks template / Admin Kit / Blocks를 먼저 채택**하고
- FPDS는 그 위에 **theme override + domain wrapper + business-specific sections**만 올린다.

즉, 이번 v2에서 디자인 시스템의 핵심은 **새 컴포넌트를 많이 발명하는 것**이 아니라, **Shadcnblocks를 FPDS에 맞게 통제된 방식으로 조합·커스터마이즈하는 규칙을 만드는 것**이다.

---

## 2. Stripe 벤치마크와 Shadcnblocks의 관계 재정의

## 2.1 Stripe가 계속 영향을 주는 영역

FPDS는 Stripe에서 아래를 계속 참고한다.

1. **강한 구조, 약한 장식**
   - 정보 밀도가 높은 화면에서도 배경, border, shadow, hierarchy가 절제되어야 한다.

2. **Context first**
   - 기본은 contextual view다.
   - 더 깊은 업무와 의사결정이 필요할 때만 넓은 캔버스나 집중형 화면으로 이동한다.

3. **상태 커뮤니케이션 분리**
   - badge, inline state, empty, loading, stale, banner, toast의 역할을 혼합하지 않는다.

4. **token-driven styling**
   - 임의의 one-off 스타일보다 design token / preset / pattern 중심으로 일관성을 유지한다.

## 2.2 Shadcnblocks가 새로 책임지는 영역

Shadcnblocks는 아래의 공식 구현 베이스가 된다.

1. **Public / Admin shell의 출발점**
2. **사이드바, 탑바, 페이지 헤더, 카드, 데이터 테이블, 필터, pagination, chart card, form layout**
3. **section/block 단위 페이지 조립 방식**
4. **shadcn/ui 기반의 theme variable 구조**
5. **Next.js template project structure**
6. **CLI 기반 설치와 dependency resolution**

## 2.3 FPDS가 계속 직접 정의해야 하는 영역

템플릿을 써도 아래는 FPDS가 소유한다.

- Product Grid card의 metric emphasis
- Product-type-aware ranking / scatter logic
- Methodology / freshness / insufficiency note
- Evidence Trace Viewer
- Review decision flow UI
- Run / Publish / Health / Usage의 운영 semantics
- Public evidence non-exposure 규칙
- EN/KO/JA locale rules
- 상태 label과 domain badge taxonomy

---

## 3. FPDS UI 시스템의 새로운 아키텍처

## 3.1 Layer 1 — Vendor Template Layer

이 레이어는 Shadcnblocks가 제공하는 템플릿과 블록을 의미한다.

구성 범위:
- Shadcnblocks Next.js template conventions
- Shadcn Admin Kit
- Shadcn Blocks library
- shadcn/ui primitives installed by CLI

원칙:
- 가능한 한 **원본 구조를 유지**한다.
- 작은 요구 때문에 template page 전체를 fork하지 않는다.
- vendor 업데이트를 받을 수 있게 **변경 범위를 최소화**한다.

## 3.2 Layer 2 — FPDS Theme Layer

이 레이어는 FPDS 브랜드와 상태 의미를 템플릿에 주입하는 레이어다.

구성 범위:
- `components.json` style decision
- `globals.css`의 shadcn semantic CSS variables
- chart/status supplemental tokens
- font, spacing rhythm, density overrides

원칙:
- 기존 bespoke token tree를 별도로 유지하지 않는다.
- **shadcn semantic variable system 위에 FPDS theme를 입히는 방식**으로 정리한다.

## 3.3 Layer 3 — FPDS Domain Component Layer

이 레이어는 템플릿만으로 해결되지 않는 FPDS 전용 컴포넌트를 다룬다.

대표 예시:
- `ProductCard`
- `ProductMetricStrip`
- `FilterScopeSummary`
- `DashboardRankingList`
- `ScatterPresetSwitcher`
- `MethodologyNote`
- `FreshnessIndicator`
- `ReviewActionBar`
- `ValidationIssueList`
- `EvidenceTracePane`
- `OverrideDiffPreview`
- `RunStageStrip`
- `PublishStateCard`
- `UsageAnomalyTable`
- `DashboardHealthDomainList`

원칙:
- vendor primitive를 조합해 만든다.
- generic button / card / input / dialog를 다시 발명하지 않는다.
- business meaning이 들어간 UI만 FPDS domain component로 만든다.

## 3.4 Layer 4 — Route Composition Layer

이 레이어는 실제 화면 조합 규칙이다.

- Public route는 Shadcnblocks public template section + FPDS domain section 조합
- Admin route는 Shadcn Admin Kit shell + FPDS ops section 조합
- route는 business job 기준으로 분리하고, 한 페이지에 너무 많은 template demo를 섞지 않는다.

---

## 4. Shadcnblocks 채택 기준선

## 4.1 Frontend template baseline

FPDS는 UI layer에서 **Shadcnblocks의 Next.js template conventions**를 기준으로 삼는다.

적용 범위:
- Next.js App Router 기반 public/admin surface
- Tailwind 4 + shadcn/ui theming variables
- section-based page composition
- co-located page / component structure

주의:
- 이 결정은 FPDS 전체 백엔드 구조를 다시 정의하는 문서가 아니다.
- Shadcnblocks는 **frontend implementation base**이며, FPDS의 API / worker / ingestion architecture 결정은 별도 문서를 따른다.

## 4.2 Primitive library baseline

FPDS v2는 **Radix UI baseline**을 사용한다.

이유:
- Shadcnblocks 문서 기준으로 Radix UI는 여전히 preferred / stable / battle-tested choice다.
- FPDS Admin은 review, publish, trace, health 등 운영형 surface가 많아 안정성이 우선이다.

따라서 Base UI는 현재 기본값이 아니며, 별도 성능 검토가 필요할 때만 재평가한다.

## 4.3 Global style baseline

FPDS의 global shadcn style baseline은 **`radix-nova`** 로 고정한다.

이유:
- Shadcnblocks 문서에서 Nova는 **reduced padding + tight spacing + small radius**를 가지며, **data-heavy interfaces / dashboards**에 적합하다고 설명한다.
- FPDS의 Admin은 compact density가 핵심이다.
- Public은 balanced density가 필요하지만, 이것은 global style를 Vega로 바꾸기보다 **section spacing과 card padding을 public layer에서 완화**하는 쪽이 유지보수에 유리하다.

### Result
- **Global style = Nova**
- **Admin = Nova defaults 적극 활용**
- **Public = Nova 위에 spacing 완화 wrapper 적용**

## 4.4 Installation baseline

FPDS의 Shadcnblocks 도입 방식은 **CLI-first** 다.

기본 원칙:
1. block 설치는 `shadcn` CLI를 우선 사용한다.
2. pro / premium block 사용 시 `SHADCNBLOCKS_API_KEY`와 registry auth를 설정한다.
3. copy & paste는 exploratory use 또는 예외 상황에서만 허용한다.
4. vendor code의 dependency install을 수동으로 맞추는 방식은 기본값으로 쓰지 않는다.

### Reason
CLI 방식은 아래를 자동 처리한다.
- 필요한 npm package 설치
- dependent shadcn/ui component 설치
- `components.json`의 style / alias / theme settings 존중
- primitive library 선택 반영

## 4.5 `components.json` baseline

FPDS는 아래와 같은 방향의 `components.json` 구성을 사용한다.

```json
{
  "$schema": "https://ui.shadcn.com/schema.json",
  "style": "radix-nova",
  "rsc": true,
  "tsx": true,
  "tailwind": {
    "config": "",
    "css": "src/app/globals.css",
    "baseColor": "neutral",
    "cssVariables": true,
    "prefix": ""
  },
  "iconLibrary": "lucide",
  "aliases": {
    "components": "@/components",
    "utils": "@/lib/utils",
    "ui": "@/components/ui",
    "lib": "@/lib",
    "hooks": "@/hooks"
  },
  "registries": {
    "@shadcnblocks": {
      "url": "https://shadcnblocks.com/r/{name}",
      "headers": {
        "Authorization": "Bearer ${SHADCNBLOCKS_API_KEY}"
      }
    }
  }
}
```

주의:
- `tailwind.css` 경로는 실제 template 구조에 맞게 조정한다.
- Shadcnblocks template docs가 `src/app/globals.css` 구조를 사용하므로, FPDS도 이 구조를 기본값으로 본다.

## 4.6 Project structure baseline

Shadcnblocks template structure를 FPDS에 맞게 아래처럼 확장한다.

```text
src/
  app/
    (public)/
      dashboard/
      methodology/
    (admin)/
      admin/
    globals.css
    layout.tsx
  components/
    ui/               # CLI로 설치된 shadcn/ui primitives
    layout/           # vendor/global shell blocks
    sections/         # vendor/public section blocks
    fpds/
      public/         # Product Grid, Insight Dashboard 전용 섹션
      admin/          # review, trace, runs, publish 등 도메인 전용 섹션
      shared/         # status, freshness, methodology, locale-aware helpers
  lib/
```

규칙:
- `components/ui` 는 vendor-managed primitive layer다.
- `components/layout`, `components/sections` 는 template-derived layer다.
- `components/fpds` 가 FPDS 전용 domain layer다.

---

## 5. 템플릿 기반으로 재해석한 FPDS 경험 원칙

## 5.1 Template first, custom second

새 화면은 아래 순서로 만든다.

1. Shadcnblocks template 또는 Admin Kit에서 가장 가까운 shell / page / section을 찾는다.
2. 필요한 block을 CLI로 설치한다.
3. theme variable과 spacing wrapper로 FPDS 맞춤값을 입힌다.
4. 그 다음에도 부족한 부분만 FPDS domain section으로 만든다.

이 순서를 뒤집지 않는다.

## 5.2 One domain component, one business meaning

FPDS custom component는 아래 중 하나를 가져야 한다.

- product comparison meaning
- evidence / validation meaning
- operational state meaning
- localization / methodology meaning

그렇지 않으면 custom component를 만들지 않는다.

## 5.3 Stable shells, replaceable sections

Shadcnblocks 도입 이후의 핵심은 **route shell을 안정적으로 유지하고, page section만 교체 가능하게 설계하는 것**이다.

예:
- Admin shell은 Admin Kit sidebar/topbar/page-header 리듬을 유지
- Review Detail의 중앙 section만 FPDS evidence workflow에 맞게 교체
- Public Dashboard는 top nav와 section rhythm을 유지한 채 KPI/ranking/scatter section을 FPDS 논리로 구성

## 5.4 Stripe-style restraint through template discipline

Stripe를 닮게 만드는 방식은 보라색을 베끼는 것이 아니다.

FPDS에서 Stripe-like restraint는 아래로 구현한다.

- 과한 hero 대신 restrained header strip
- border-first separation
- dense but readable tables
- one clear primary action
- persistent banner vs transient toast 분리
- context-preserving drilldown
- chart보다 state와 summary의 우선순위 강화

---

## 6. Theme와 Token baseline

## 6.1 Token system의 변경

v1에서는 FPDS 고유 token namespace를 상세히 정의했다.
v2에서는 token system을 **shadcn/ui semantic variable 중심으로 재정렬**한다.

즉, 앞으로의 source of truth는 아래다.

1. `globals.css`의 shadcn semantic variables
2. `components.json` style selection
3. chart/status supplemental tokens
4. route-level spacing and density rules

## 6.2 FPDS semantic theme baseline

FPDS는 아래 semantic roles를 공식 theme layer로 사용한다.

### Core shadcn variables
- `--background`
- `--foreground`
- `--card`
- `--card-foreground`
- `--popover`
- `--popover-foreground`
- `--primary`
- `--primary-foreground`
- `--secondary`
- `--secondary-foreground`
- `--muted`
- `--muted-foreground`
- `--accent`
- `--accent-foreground`
- `--destructive`
- `--destructive-foreground`
- `--border`
- `--input`
- `--ring`

### Sidebar-aware variables
- `--sidebar-background`
- `--sidebar-foreground`
- `--sidebar-primary`
- `--sidebar-primary-foreground`
- `--sidebar-accent`
- `--sidebar-accent-foreground`
- `--sidebar-border`
- `--sidebar-ring`

### Supplemental variables
- `--success`
- `--warning`
- `--info`
- `--chart-1`
- `--chart-2`
- `--chart-3`
- `--chart-4`
- `--chart-5`

## 6.3 FPDS color baseline

아래 palette는 FPDS가 유지할 색 방향이다.

- canvas / background: very light neutral
- primary: indigo
- secondary / muted: neutral blue-gray
- success: teal-green
- warning: amber
- destructive: red
- charts: indigo / blue / teal / amber / rose

권장 baseline 예시:

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

  --sidebar-background: 255 255 255;
  --sidebar-foreground: 36 48 66;
  --sidebar-primary: 79 70 229;
  --sidebar-primary-foreground: 255 255 255;
  --sidebar-accent: 243 245 250;
  --sidebar-accent-foreground: 36 48 66;
  --sidebar-border: 216 224 234;
  --sidebar-ring: 79 70 229;

  --success: 22 163 74;
  --warning: 217 119 6;
  --info: 37 99 235;

  --chart-1: 79 70 229;
  --chart-2: 37 99 235;
  --chart-3: 15 118 110;
  --chart-4: 217 119 6;
  --chart-5: 190 24 93;
}
```

## 6.4 Typography baseline

FPDS v2의 기본 원칙은 **template와 충돌하지 않는 범위에서 typography를 단순화**하는 것이다.

권장:
- UI sans: `Inter`
- numeric / ids: `IBM Plex Mono`

규칙:
- sans / mono 외에 별도 editorial serif를 core product UI에 포함하지 않는다.
- font 변경은 `next/font`와 root layout variable 수준에서 처리한다.
- dense admin tables에는 mono를 제한적으로 사용한다.

## 6.5 Density baseline

### Admin
- global style: Nova 기본 밀도 사용
- compact rows / compact cards 허용
- filter bar와 toolbar spacing 최소화

### Public
- same style family 유지
- section gap, card padding, metric whitespace를 Admin보다 완화
- marketing 사이트처럼 과도하게 spacious 하게 만들지 않음

## 6.6 Motion baseline

- hover, dropdown, sheet, dialog, filter transition만 짧게 사용
- chart entrance는 subtle 하게만
- admin triage 화면에서 bouncy motion 금지

---

## 7. Layout과 Navigation baseline

## 7.1 Public shell

Public shell은 **Shadcnblocks public template section rhythm**을 따르되, FPDS는 메인홈이 아니라 dashboard-first 구조를 쓴다.

### Route baseline
- `/` → `/dashboard`
- `/dashboard`
- `/dashboard/products`
- `/dashboard/insights`
- `/methodology`

### Public shell structure
1. compact top nav
2. optional restrained header strip
3. shared filter row or local toolbar
4. main content sections
5. footer / methodology link

### Hero-lite rule
허용한다. 하지만 아래를 지킨다.
- marketing hero 금지
- 72~120px 높이 내 restrained strip 정도로만 사용
- gradient는 top edge 수준으로만 제한
- CTA는 최대 1개
- 없어도 된다

## 7.2 Admin shell

Admin shell은 **Shadcn Admin Kit**를 기본으로 한다.

### Structure
1. sidebar
2. top utility bar
3. page header
4. content canvas
5. optional sticky action area / sheet / drawer

### Navigation groups
- Overview
- Review
- Operations
- Observability

### Contextual routes
- `/admin/reviews/:reviewTaskId`
- `/admin/runs/:runId`
- `/admin/products/:productId`

규칙:
- canonical product는 primary nav가 아니라 contextual diagnostic surface다.
- review / run / change / publish / usage / health를 giant dashboard 하나로 합치지 않는다.

---

## 8. Surface별 Template Mapping

## 8.1 Public surface mapping

| FPDS Surface | Shadcnblocks Base | FPDS Custom Layer | Rule |
|---|---|---|---|
| `/dashboard` | public template header + stats/card sections | market snapshot strip, methodology note, shared filter context | marketing home가 아니라 market overview 첫 화면 |
| `/dashboard/products` | card/grid section + filter toolbar + pagination patterns | `ProductCard`, `FilterScopeSummary`, product-type metric emphasis | evidence 비노출 |
| `/dashboard/insights` | stats cards + chart cards + ranking/list blocks | `DashboardRankingList`, scatter preset logic, insufficiency note | mixed-type 기본 scatter 금지 |
| `/methodology` | docs/article/content sections | metric definition, freshness, public exposure boundary | long-form readability 우선 |

## 8.2 Admin surface mapping

| FPDS Surface | Shadcnblocks Base | FPDS Custom Layer | Rule |
|---|---|---|---|
| `/admin` | Admin Kit dashboard shell, KPI widgets, activity panels | urgent attention strip, dashboard health summary | triage first |
| `/admin/reviews` | Admin Kit table, filter, badge, pagination | confidence/validation/review-state columns | queue는 table-first |
| `/admin/reviews/:id` | Admin Kit page shell, card/form layout, sheet/dialog patterns | `EvidenceTracePane`, `ReviewActionBar`, `OverrideDiffPreview` | custom 비중 가장 큼 |
| `/admin/runs` | Admin Kit data table and summary widgets | run state semantics, stage summary | diagnostic read 중심 |
| `/admin/changes` | Admin Kit list/table + badges | change-event taxonomy | chronology + context |
| `/admin/publish` | Admin Kit list/table + warning cards | retry/reconciliation semantics | operational risk visible |
| `/admin/usage` | Admin Kit chart + metric widgets | agent/run/model cost semantics | public KPI와 분리 |
| `/admin/health/dashboard` | Admin Kit health/status panels | aggregate freshness, completeness, cache TTL semantics | serving health 전용 |

## 8.3 High-custom surfaces

아래는 템플릿만으로 끝나지 않는 FPDS 고유 surface다.

1. Review Detail / Trace Viewer
2. Product Grid card with product-type emphasis
3. Ranking widgets with FPDS metric semantics
4. Scatter preset switcher and insufficiency state
5. Methodology / Freshness note modules
6. Publish reconciliation panels
7. Dashboard health domain list

즉, **Shadcnblocks를 쓴다고 해서 FPDS 고유 화면이 없어지는 것이 아니라, generic shell과 generic UI를 vendor에 맡기고 domain-specific UI만 남기는 것**이 이번 개편의 요점이다.

---

## 9. Component ownership policy

## 9.1 Vendor-managed primitives

아래는 가능하면 vendor/shadcn layer를 그대로 쓴다.

- `Button`
- `Card`
- `Badge`
- `Input`
- `Textarea`
- `Checkbox`
- `Select`
- `Tabs`
- `Dialog`
- `Sheet`
- `DropdownMenu`
- `Tooltip`
- `Alert`
- `Table`
- `Skeleton`
- generic chart container

## 9.2 FPDS-managed domain components

아래는 FPDS wrapper 또는 domain component로 만든다.

- `ProductCard`
- `ProductMetricStrip`
- `FilterScopeSummary`
- `FreshnessIndicator`
- `MethodologyNote`
- `DashboardRankingList`
- `ScatterPresetSwitcher`
- `ReviewActionBar`
- `ValidationIssueList`
- `EvidenceTracePane`
- `FieldEvidenceRow`
- `OverrideDiffPreview`
- `RunStageStrip`
- `PublishStateCard`
- `UsageAnomalyTable`
- `DashboardHealthDomainList`

## 9.3 Customization boundary

### Allowed
- theme variables 변경
- layout spacing override
- page section 조합 변경
- domain-specific wrappers 추가
- table column / cell semantics 변경
- chart title / methodology / note / locale behavior 변경

### Not allowed as default
- vendor button/card/input/dialog를 별도 FPDS 전용 primitive로 재작성
- route마다 badge 색을 새로 정의
- template shell을 route마다 다르게 다시 만드는 것
- 공통 generic component를 무분별하게 fork하는 것

## 9.4 Rule for editing vendor code

1. 우선 wrapper로 해결한다.
2. wrapper로 해결되지 않을 때만 vendor code를 수정한다.
3. vendor code를 수정했으면 source block/template와 변경 이유를 기록한다.
4. upgrade 시점에 재병합 가능한 수준으로만 수정한다.

---

## 10. Public 경험 규칙

## 10.1 Dashboard-first public

Public의 first impression은 marketing pitch가 아니라 **market state** 여야 한다.

따라서 `/dashboard`는 아래를 우선 보여준다.
- scope-aware KPI
- bank/type composition
- ranking preview
- Products / Insights sibling navigation
- freshness + methodology reachable entry

## 10.2 Product Grid

Grid는 template card gallery가 아니라 **비교 가능한 product catalog** 여야 한다.

필수 구조:
1. bank
2. localized product type label
3. source-language product name
4. metric strip 최대 3개
5. highlight badge 1개
6. target tag 최대 2개
7. freshness line

Product-type emphasis:
- `chequing`: fee → minimum balance → fee waiver/recent change
- `savings`: display rate → minimum balance → promo/high-interest hint
- `gic`: display rate → term length → minimum deposit

## 10.3 Insight Dashboard

mixed-type와 single-type를 분리한다.

### Mixed-type default
- KPI strip
- products by bank
- products by product type
- highest display rate ranking
- recently changed 30d ranking
- methodology note

### Single-type default
- `chequing`: lowest fee / recently changed / fee vs minimum balance
- `savings`: highest rate / recently changed / rate vs minimum balance
- `gic`: highest rate / lowest minimum deposit / rate vs minimum deposit / optional term vs rate

## 10.4 Methodology page

이 페이지는 template docs/article sections를 활용하되, FPDS는 아래 내용을 반드시 포함한다.

- included banks
- included product types
- KPI definition
- ranking logic
- scatter preset meaning
- freshness meaning
- what is not shown publicly
- source-derived text policy

---

## 11. Admin 경험 규칙

## 11.1 Overview

Overview는 widget showcase가 아니라 triage surface다.

상단 우선순위:
1. queued reviews
2. recent failures
3. retry / reconciliation
4. stale aggregates
5. recent changes

## 11.2 Review Queue

Review Queue는 Admin Kit table pattern을 적극 활용한다.

핵심 rule:
- table-first
- dense scanability
- inline quick action은 보조
- primary action은 open detail

## 11.3 Review Detail / Trace Viewer

이 화면은 template page가 아니라 **FPDS domain page**로 본다.

Desktop baseline:
- left: candidate summary + normalized fields + validation
- right: trace + decision + diff

원칙:
- field 선택과 trace를 연동
- raw object path 비노출
- read_only는 write action 비노출

## 11.4 Runs / Changes / Publish / Usage / Health

이 화면들은 모두 Admin Kit의 dashboard/table/card 패턴을 활용할 수 있다.
하지만 의미는 FPDS가 직접 부여한다.

예:
- `retry` 와 `reconciliation` 은 단순 warning이 아니라 publish risk surface
- `stale` 는 시각적 장식이 아니라 freshness issue
- `usage anomaly` 는 chart 장식이 아니라 비용 통제 surface

---

## 12. Status, Localization, Accessibility

## 12.1 Status semantics

Status는 template badge를 사용하되 FPDS 의미를 고정한다.

| State | Meaning | UI Direction |
|---|---|---|
| queued / in review / pending | 진행 중 | info |
| approved / published / healthy | 정상 완료 | success |
| deferred / stale soon / reconciliation | 조치 필요 가능 | warning |
| rejected / failed / critical | 강한 주의 | destructive |

규칙:
- color-only 금지
- icon-only 금지
- text label 포함

## 12.2 Localization

번역 대상:
- navigation
- page titles
- widget labels
- filter labels
- chart titles
- methodology note
- helper text
- status / badge labels

번역하지 않는 대상:
- product name
- description_short
- eligibility_text
- fee_waiver_condition
- evidence excerpt
- source-derived condition text

fallback:
- `selected locale -> en -> safe fallback`

## 12.3 Accessibility

- visible focus ring 유지
- badge는 color와 text를 함께 제공
- dense table에서도 hover만으로 정보 전달 금지
- chart는 색상 단독 구분 금지
- locale switch, chips, tabs의 hit area 확보

---

## 13. Upgrade와 유지보수 원칙

## 13.1 Why this matters

Shadcnblocks는 commercial template이므로, **초기 개발 속도** 뿐 아니라 **추후 업데이트 수용 전략**이 중요하다.

Admin Kit 페이지는 monthly updates를 강조하므로, FPDS는 vendor update를 받을 수 있는 구조로 유지해야 한다.

## 13.2 Upgrade-safe rules

1. `components/ui` 직접 수정 최소화
2. domain customization은 `components/fpds` 로 격리
3. 설치한 block / template source를 기록
4. vendor-specific modification은 변경 로그를 남김
5. theme override는 `globals.css`와 wrapper class에 모음
6. screenshot regression과 locale regression을 함께 검증

## 13.3 Recommended tracking artifacts

권장 산출물:
- `docs/03-design/shadcnblocks-adoption-log.md`
- `docs/03-design/shadcnblocks-block-inventory.md`
- `docs/03-design/ui-override-register.md`

이 문서에는 아래를 남긴다.
- 어떤 template / block을 도입했는지
- source URL / block id
- 로컬 수정 여부
- 교체 가능성
- upgrade 시 주의사항

---

## 14. 안티패턴

1. Shadcnblocks를 쓰면서 또 다른 bespoke primitive library를 만들지 않는다.
2. route마다 서로 다른 style family(Vega / Nova / Maia...)를 섞지 않는다.
3. CLI 설치 가능한 block을 copy & paste 기본 방식으로 가져오지 않는다.
4. marketing hero block을 dashboard first screen에 그대로 쓰지 않는다.
5. Public에 evidence trace를 노출하지 않는다.
6. mixed-type scope에서 억지 scatter를 기본 노출하지 않는다.
7. template radius / shadow / spacing을 매 화면마다 임의로 덮어쓰지 않는다.
8. vendor code를 대량 수정해 upgrade path를 끊지 않는다.
9. generic component에 business logic를 숨기지 않는다.
10. theme variable과 무관한 ad-hoc hex color를 곳곳에 박아 넣지 않는다.

---

## 15. 적용 순서

## Phase A — Template foundation
- Shadcnblocks template / Admin Kit acquisition 및 baseline 정리
- `components.json` / theme variable / registry auth 설정
- `radix-nova` baseline 적용
- public/admin shell scaffold 정리

## Phase B — Public
- `/dashboard`
- `/dashboard/products`
- `/dashboard/insights`
- `/methodology`
- shared filter state와 EN/KO/JA 연결

## Phase C — Admin
- overview
- review queue
- review detail / trace
- runs
- changes
- publish
- usage
- dashboard health

## Phase D — Domain hardening
- evidence trace polish
- methodology copy
- insufficiency / stale / retry state copy
- locale QA
- accessibility QA
- vendor update strategy 문서화

---

## 16. 최종 기준 문장

**FPDS v2는 Stripe를 구조적 벤치마크로 유지하되, 실제 UI 구현은 Shadcnblocks template-first 방식으로 전환하고, FPDS는 domain-specific surface와 evidence-aware semantics만 직접 소유한다.**

---

## 17. Change History

| Date | Change |
|---|---|
| 2026-04-13 | Replaced bespoke-first UI direction with Shadcnblocks template-first baseline |
| 2026-04-13 | Chose `Radix UI + radix-nova` as the global Shadcnblocks baseline |
| 2026-04-13 | Added vendor/theme/domain/page composition layer model |
| 2026-04-13 | Added CLI-first installation, registry auth, project structure, and upgrade-safe customization rules |
| 2026-04-13 | Re-mapped Public/Admin surfaces to Shadcnblocks template and Admin Kit starting points |
