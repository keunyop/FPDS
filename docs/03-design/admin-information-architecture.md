# FPDS Admin Information Architecture

Version: 1.0
Date: 2026-04-06
Status: Approved Baseline for WBS 1.7.4
Source Documents:
- `docs/02-requirements/FPDS_Requirements_Definition_v1_5.md`
- `docs/01-planning/WBS.md`
- `docs/02-requirements/scope-baseline.md`
- `docs/03-design/api-interface-contracts.md`
- `docs/03-design/security-access-control-design.md`
- `docs/03-design/review-run-publish-audit-state-design.md`
- `docs/03-design/workflow-state-ingestion-design.md`
- `docs/03-design/erd-draft.md`
- `docs/03-design/aggregate-cache-refresh-strategy.md`
- `docs/00-governance/decision-log.md`

---

## 1. Purpose

이 문서는 `WBS 1.7.4 admin 정보 구조 설계`의 기준 문서다.

목적:
- Admin Console의 화면 구조, 탐색 체계, 정보 우선순위를 구현 전 vocabulary로 고정한다.
- review, trace, run, change, publish, usage, dashboard health가 서로 다른 운영 목적을 가진 surface라는 점을 UI 구조에 반영한다.
- admin API contract, RBAC/security baseline, workflow/state model, aggregate health 기준이 같은 admin UX vocabulary를 참조하도록 만든다.

이 문서는 구현 시작 신호가 아니다.  
구현은 `Gate A = Pass + Product Owner explicit approval` 이후에만 시작한다.

---

## 2. Baseline Decisions Carried Forward

1. admin surface는 browser 기반 human operator console이며, 인증 baseline은 `server-side session cookie`다.
2. review queue 생성 단위는 `candidate`이며, review state는 `queued`, `approved`, `rejected`, `edited`, `deferred`를 사용한다.
3. run, review, canonical product/change, publish, usage, dashboard health는 서로 다른 운영 단위이므로 하나의 혼합 리스트로 합치지 않는다.
4. trace viewer는 evidence metadata와 excerpt를 보여주되 raw object path나 private storage key를 직접 노출하지 않는다.
5. Admin UI의 navigation, widget title, status label, help text는 `en`, `ko`, `ja`를 지원하고, source-derived product text와 evidence excerpt는 source language 값을 유지한다.
6. human RBAC baseline은 `admin`, `reviewer`, `read_only`이며, write action visibility는 역할에 따라 제한된다.
7. PRD와 admin API contract가 `review queue`, `trace viewer`, `run status`, `change history`, `BX-PF publish monitor`, `LLM usage`, `dashboard health`를 모두 요구하므로, 본 IA는 WBS row의 예시보다 넓게 admin console 전체 구조를 함께 고정한다.

---

## 3. Scope of 1.7.4

이 문서는 아래를 결정한다.
- admin shell과 primary navigation
- overview dashboard, review queue, review detail/trace viewer, run list/detail, change history, publish monitor, usage dashboard, dashboard health의 화면 목적과 정보 우선순위
- global search entry와 cross-surface drilldown 규칙
- role-based action visibility baseline
- desktop/tablet/mobile 대응의 정보 구조 baseline

이 문서는 아래를 결정하지 않는다.
- i18n ownership workflow, locale fallback governance, Japanese glossary ownership의 세부 baseline은 `docs/03-design/localization-governance-and-fallback-policy.md`
- 시각 스타일, 디자인 토큰, component library 세부 구현
- exact table virtualization, chart library, pagination widget 구현 방식
- publish retry 실행 UX의 세부 조작 방식

---

## 4. Information Architecture Principles

### 4.1 Triage First, Diagnosis Second, Mutation Last

- overview와 queue/list surface는 "무엇이 급한가"를 보여주는 triage surface다.
- detail surface는 "왜 이런 상태가 되었는가"를 보여주는 diagnosis surface다.
- approve/reject/edit/defer 같은 state-changing action은 detail surface를 중심으로 배치한다.

### 4.2 One Primary Home Per Operational Entity

- `review_task`의 primary home은 Review Queue다.
- `run`의 primary home은 Runs다.
- `canonical_product`와 `change_event`의 primary home은 Product/Change surface다.
- `publish_item`의 primary home은 Publish Monitor다.
- `llm_usage`와 aggregate freshness는 Observability surface다.

같은 엔터티를 여러 화면에서 보더라도, 동일한 current-state vocabulary를 재사용하고 별도 의미로 재해석하지 않는다.

### 4.3 Preserve Context on Drilldown

- list에서 detail로 들어갈 때 현재 filter/time-scope를 잃지 않아야 한다.
- detail header에는 상위 context로 돌아갈 수 있는 breadcrumb 또는 equivalent back context가 필요하다.
- cross-link는 entity id 중심으로 이동하며, 임시 UI label만으로 화면을 연결하지 않는다.

### 4.4 Separate Current State from History

- review queue의 current state와 decision history는 분리해서 보여준다.
- run summary와 error event detail은 분리해서 보여준다.
- product current version과 change history는 분리해서 보여준다.
- publish current state와 publish attempt history는 분리해서 보여준다.

---

## 5. Admin Shell Baseline

### 5.1 Global Chrome

모든 admin 화면은 아래 공통 chrome을 가진다.

1. environment badge (`dev` / `prod`)
2. page title and short scope note
3. global search entry
4. locale toggle (`en`, `ko`, `ja`)
5. last refresh or data-generated hint
6. user/session menu

### 5.2 Navigation Groups

권장 primary navigation group은 아래와 같다.

| Group | Surface | Route Baseline | Purpose |
|---|---|---|---|
| Overview | Admin Overview Dashboard | `/admin` | 전체 운영 상황 triage |
| Review | Review Queue | `/admin/reviews` | reviewer work intake와 queue 처리 |
| Operations | Runs | `/admin/runs` | ingestion/run 상태 진단 |
| Operations | Change History | `/admin/changes` | canonical 변화 추적 |
| Operations | Publish Monitor | `/admin/publish` | BX-PF pending/retry/reconciliation 확인 |
| Observability | LLM Usage | `/admin/usage` | token/cost 모니터링 |
| Observability | Dashboard Health | `/admin/health/dashboard` | public aggregate freshness/health 확인 |

### 5.3 Contextual Routes

아래 surface는 drilldown 또는 search 기반 contextual route로 둔다.

| Surface | Route Baseline | Entry Path |
|---|---|---|
| Review Detail / Trace Viewer | `/admin/reviews/:reviewTaskId` | review queue, run detail, search |
| Run Detail | `/admin/runs/:runId` | runs list, review detail, usage drilldown, search |
| Product Record | `/admin/products/:productId` | change history, publish monitor, search, review result context |

`/admin/products` list route는 구현 시 둘 수 있지만, 본 IA baseline에서는 primary navigation 필수 항목으로 두지 않는다.  
canonical product는 triage-first surface가 아니라 contextual diagnostic surface로 본다.

### 5.4 Reserved Follow-On Navigation

- `Localization Health`는 PRD `FR-ADM-014`를 반영해 future admin health surface로 자리만 확보한다.
- owner, fallback, glossary governance는 `docs/03-design/localization-governance-and-fallback-policy.md`를 따른다.
- exact route와 widget layout 구현은 후속 구현 단계에서 확정한다.

---

## 6. Global Search and Cross-Surface Drilldown

### 6.1 Search Baseline

global search는 최소 아래 query를 지원해야 한다.

- `bank`
- `product name`
- `run id`
- `candidate id`

권장 result grouping:
- review task
- run
- product

### 6.2 Search Routing Rules

- `run id` hit는 `Run Detail`로 이동한다.
- `candidate id` hit는 `Review Detail / Trace Viewer`로 이동한다.
- `product name` hit는 active review task가 있으면 review 결과를 우선 보여주고, 그렇지 않으면 canonical product record로 이동할 수 있다.
- bank name/code 검색 결과는 직접 action보다 scoped list 진입점을 제공하는 것이 우선이다.

### 6.3 Cross-Link Rules

핵심 cross-link baseline:

| From | To | Why |
|---|---|---|
| Review Queue | Review Detail | decision과 trace 확인의 기본 진입 |
| Review Detail | Run Detail | producing run 진단 |
| Review Detail | Product Record | approved/edited 결과 continuity 확인 |
| Run Detail | Related Review Tasks | run에서 나온 review workload 확인 |
| Run Detail | LLM Usage | same run cost drilldown |
| Change History | Product Record | 현재 버전과 변경 문맥 확인 |
| Publish Monitor | Product Record | publish 대상 상품 문맥 확인 |
| Dashboard Health | Public aggregate domain reference | stale/failure 원인 추적 |

---

## 7. Surface Definitions

### 7.1 Admin Overview Dashboard

이 화면은 로그인 직후 기본 triage surface다.

권장 구성 순서:
1. overview heading and environment/scope note
2. top KPI row
3. urgent attention panels
4. composition and recent activity panels
5. quick links to owning surfaces

필수 widget baseline:
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

규칙:
- overview는 "읽고 판단하는 화면"이지, 직접 review 승인 작업을 대체하지 않는다.
- widget은 모두 owning surface로 drilldown entry를 제공해야 한다.
- review queue, recent failures, publish retry/reconciliation, dashboard health는 화면 상단 절반에서 먼저 보이는 영역에 배치한다.

### 7.2 Review Queue

Review Queue는 reviewer의 primary work intake surface다.

권장 구성 순서:
1. queue header with active-state count
2. sticky filter bar
3. result summary row
4. queue table/list
5. pagination

권장 filter:
- `review_state`
- `bank_code`
- `product_type`
- `validation_status`
- `created_from`
- `created_to`

기본 list scope:
- first-load 기본값은 active task인 `queued`, `deferred`만 보여준다.
- terminal state 조회는 filter를 통해 들어간다.

필수 컬럼 baseline:
- task id
- bank
- country
- product type
- product name
- issue type or issue summary
- confidence
- validation status
- created at
- status

행동 규칙:
- `open detail`은 항상 1차 액션이다.
- `approve`, `reject`, `defer`는 inline quick action으로 둘 수 있다.
- `edit & approve`는 field-level 검토가 필요하므로 detail surface 진입과 연결하는 것을 baseline으로 본다.
- bulk approval/rejection은 Phase 1 baseline 필수 요구사항으로 두지 않는다.

### 7.3 Review Detail / Trace Viewer

Review Detail은 review decision과 evidence diagnosis의 중심 surface다.

desktop baseline은 `primary detail pane + trace pane + action area` 구조를 권장한다.

필수 영역:
1. candidate summary header
2. normalized fields pane
3. validation issues pane
4. source evidence / trace pane
5. decision form
6. override diff preview
7. action history

header 최소 정보:
- review task id
- current review state
- bank
- product type
- product name
- run id
- source confidence
- validation status
- created/updated timestamps

trace pane 최소 정보:
- source URL
- source type
- crawl or fetch timestamp
- chunk excerpt
- citation anchor or chunk id
- parsed field mapping
- model run reference

상호작용 규칙:
- 운영자가 특정 field를 선택하면 trace pane은 해당 field의 evidence link를 우선 보여줘야 한다.
- raw object key, private bucket path, full parsed artifact direct link는 노출하지 않는다.
- `read_only`는 같은 진단 정보를 볼 수 있지만 decision form과 write action은 보지 않는다.

### 7.4 Runs Surface

Runs는 ingestion execution을 진단하는 primary surface다.

`/admin/runs` list baseline:
- run id
- run state
- started at
- completed at
- source count
- candidate count
- review queued count
- success/failure count
- partial completion flag
- error summary

`/admin/runs/:runId` detail baseline:
1. run summary header
2. stage summary strip
3. source processing summary
4. error/failure event section
5. related review tasks
6. usage summary

규칙:
- run detail은 실행 실패 원인과 영향 범위를 설명하는 진단 surface다.
- review action과 canonical edit는 run detail에서 직접 수행하지 않는다.
- partial completion 여부는 state badge와 별도로 항상 명시한다.

### 7.5 Change History and Product Record

Change History는 canonical change event 중심 surface다.

`/admin/changes` baseline:
- filter by product, bank, product type, change type, date range
- list row는 `change type`, `summary`, `changed fields`, `detected at`, `related review/run context`를 포함한다.

Product Record는 continuity-centric contextual surface다.

`/admin/products/:productId` baseline:
1. product summary
2. current approved version summary
3. finalized field evidence links
4. change events
5. publish summary

규칙:
- change history는 event chronology를 보여주고, product record는 current canonical truth를 보여준다.
- `ManualOverride`는 change history와 audit 문맥을 동시에 드러내야 한다.

### 7.6 Publish Monitor

Publish Monitor는 BX-PF publish tracker의 primary home이다.

권장 구성 순서:
1. state summary row
2. filter bar
3. publish item list
4. contextual product/publish detail entry

필수 list 정보:
- publish item id
- canonical product id or product name
- product version id
- publish state
- pending or failure reason
- last attempted at
- attempt count
- target master id
- last result category/message

상태 우선순위:
- `retry`
- `reconciliation`
- `pending`
- `published`

규칙:
- active operational risk가 높은 `retry`와 `reconciliation`을 상단과 기본 tab/filter에서 우선 노출한다.
- publish monitor는 review queue 안에 종속시키지 않고 별도 surface로 둔다.
- exact retry execution control은 후속 구현 WBS에서 상세화하되, 상태 조회와 원인 확인 구조는 지금 고정한다.

### 7.7 LLM Usage Dashboard

LLM Usage는 cost/usage observability surface다.

권장 구성 순서:
1. time range and scope filter bar
2. totals cards
3. by-model section
4. by-agent section
5. by-run section
6. usage trend section
7. anomaly drilldown table

필수 기능:
- model별 usage
- agent별 usage
- run별 token/cost
- 기간별 usage trend
- anomaly candidate drilldown

규칙:
- public business dashboard metric과 혼동되지 않도록 별도 navigation group에 둔다.
- anomaly row는 가능한 경우 run detail 또는 review/product context로 drilldown을 제공한다.

### 7.8 Dashboard Health

Dashboard Health는 public aggregate freshness와 quality health를 운영자 시점에서 보는 surface다.

필수 domain row:
- `public_product_projection`
- `dashboard_metric_snapshot`
- `dashboard_ranking_snapshot`
- `dashboard_scatter_snapshot`

필수 정보:
- latest successful refresh time
- latest attempted refresh time
- refresh status
- stale flag
- missing data ratio or equivalent completeness note
- cache TTL
- last error summary if failed

규칙:
- overview에는 compact summary widget만 두고, 자세한 진단은 dedicated health surface에서 본다.
- 이 surface는 public dashboard KPI 의미를 다시 설명하는 곳이 아니라 aggregate serving health를 보여주는 운영 화면이다.

---

## 8. Role Visibility Baseline

exact permission enforcement detail은 `1.6.2 RBAC` 구현에서 확정하지만, IA 기준 visibility baseline은 아래와 같다.

| Surface / Action | `admin` | `reviewer` | `read_only` | Notes |
|---|---:|---:|---:|---|
| Overview dashboard | O | O | O | read-only triage 허용 |
| Review queue list/detail read | O | O | O | trace read 허용 |
| Review decision actions | O | O | X | approve/reject/edit/defer |
| Runs and run detail | O | O | O | diagnostic read |
| Change history and product record | O | O | O | diagnostic read |
| Publish monitor read | O | O | O | operational visibility |
| Usage dashboard read | O | O | O | cost visibility |
| Dashboard health read | O | O | O | aggregate health visibility |

현재 범위에는 privilege/config/credential management screen을 포함하지 않는다.  
그런 admin-only governance screen이 후속 추가되더라도, 본 문서의 core admin operations IA는 그대로 유지한다.

---

## 9. Responsive and Localization Baseline

### 9.1 Responsive Rules

- desktop 우선 설계
- Review Detail/Trace는 desktop에서 split-pane 구조를 우선한다.
- tablet에서는 pane 일부를 tab/stack 구조로 전환할 수 있다.
- mobile에서는 queue/list 중심 확인은 가능해야 하지만, heavy trace inspection과 multi-column diff는 축약된 stacked section으로 제공할 수 있다.
- 상태 badge, confidence, validation status, review action availability 같은 핵심 운영 정보는 작은 화면에서도 숨기지 않는다.

### 9.2 Localization Rules

- navigation, widget title, status label, filter label, help text는 `en`, `ko`, `ja` locale resource를 사용한다.
- `product_name`, `description_short`, `eligibility_text`, `fee_waiver_condition`, evidence excerpt는 source-derived/source-language 값을 그대로 보여준다.
- locale 미완성 시 fallback 운영 rule은 `docs/03-design/localization-governance-and-fallback-policy.md`를 따른다.

---

## 10. Follow-On Items

| Area | Follow-Up |
|---|---|
| i18n ownership / fallback | `docs/03-design/localization-governance-and-fallback-policy.md` |
| Admin login and route protection | `4.1` |
| Review queue / decision flow | `4.2`, `4.3` |
| Trace viewer implementation | `4.4` |
| Run status screen | `4.5` |
| Change history screen | `4.6` |
| Usage dashboard implementation | `4.8`, `4.9` |
| Publish monitor implementation | `6.4` |

---

## 11. Follow-On Work Unlocked

- `4.1`: admin login 구현
- `4.2`: review queue 구현
- `4.4`: evidence trace viewer 구현
- `4.5`: run status 화면 구현
- `4.6`: change history 화면 구현
- `4.9`: usage dashboard v1 구현
- `5.12`: EN/KO/JA admin locale 적용
- `6.4`: publish monitor UI 구현

---

## 12. WBS Mapping

| WBS ID | Closure in This Document |
|---|---|
| 1.7.4 | Sections 2-11 |

---

## 13. Change History

| Date | Change |
|---|---|
| 2026-04-06 | Initial admin information architecture baseline created for WBS 1.7.4 |
