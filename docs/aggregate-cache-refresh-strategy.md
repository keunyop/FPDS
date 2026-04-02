# FPDS Aggregate and Cache Refresh Strategy

Version: 1.0  
Date: 2026-04-01  
Status: Approved Baseline for WBS 1.4.5  
Source Documents:
- `docs/FPDS_Requirements_Definition_v1_5.md`
- `docs/plan.md`
- `docs/WBS.md`
- `docs/erd-draft.md`
- `docs/workflow-state-ingestion-design.md`
- `docs/system-context-diagram.md`
- `docs/decision-log.md`

---

## 1. Purpose

이 문서는 `WBS 1.4.5 aggregate/cache refresh 전략 정의`를 닫기 위한 기준 문서다.

목적:
- public grid, dashboard summary, ranking, scatter용 aggregate dataset의 refresh 단위를 고정한다.
- synchronous canonical write와 asynchronous aggregate refresh의 경계를 정한다.
- TTL과 freshness 노출 규칙을 정의한다.

이 문서는 refresh mechanics를 정의한다.  
exact KPI formula, ranking metric semantics, scatter axis meaning은 `1.7.2`, `1.7.3`에서 별도로 닫는다.

---

## 2. Baseline Decisions Carried Forward

본 문서는 아래 확정사항을 반영한다.

1. public dashboard의 KPI/ranking/scatter는 canonical product 또는 equivalent verified aggregate source에서 계산되어야 한다.
2. aggregate refresh 실패가 canonical data commit 자체를 롤백하지는 않는다.
3. freshness timestamp와 metric health는 public/admin에서 모두 추적 가능해야 한다.
4. public surface는 aggregate/cached view 중심 읽기 경계다.

---

## 3. Aggregate Domains

이번 baseline에서 구분하는 aggregate domain은 아래 4가지다.

| Aggregate Domain | Purpose | Primary Consumer |
|---|---|---|
| `public_product_projection` | grid/filter/sort 조회용 flattened product view | public product API |
| `dashboard_metric_snapshot` | KPI card 및 freshness용 snapshot | public dashboard, admin metric health |
| `dashboard_ranking_snapshot` | Top N ranking widget 결과 | public dashboard |
| `dashboard_scatter_snapshot` | scatter plot 표시용 projected dataset | public dashboard |

참고:
- PRD의 `dashboard_metric_snapshot`, `dashboard_ranking_snapshot`는 직접 명시된 저장 단위다.
- scatter dataset은 WBS key output에 맞춰 별도 logical aggregate로 취급한다.

---

## 4. Refresh Triggers

### 4.1 Primary Trigger

아래 이벤트가 발생하면 aggregate refresh 대상이 된다.

- canonical product version 생성
- change event 생성
- publish state 변화가 public 표시 가능성에 영향을 주는 경우
- manual override가 public-facing canonical field를 바꾸는 경우

### 4.2 Trigger Boundary

- canonical write는 먼저 commit된다.
- aggregate refresh는 post-commit asynchronous job로 처리한다.
- aggregate refresh는 `ingestion_run`의 Stage 12 결과로 기록될 수 있다.

### 4.3 Full vs Incremental Rule

| Domain | Default Refresh Mode | Fallback |
|---|---|---|
| `public_product_projection` | changed product 중심 incremental upsert | daily or manual full rebuild |
| `dashboard_metric_snapshot` | scope-based recompute after successful aggregate job | full rebuild |
| `dashboard_ranking_snapshot` | scope-based recompute | full rebuild |
| `dashboard_scatter_snapshot` | scope-based recompute | full rebuild |

---

## 5. Freshness and TTL Rules

### 5.1 Dataset Freshness Rule

- aggregate dataset 자체에는 `refreshed_at`, `source_change_cutoff_at`, `refresh_status`를 남긴다.
- latest successful snapshot은 새 refresh가 실패해도 serving baseline으로 유지한다.
- stale 여부는 “가장 최근 eligible canonical change 이후 refresh가 성공했는가” 기준으로 판단한다.

### 5.2 API Response Cache TTL

권장 API cache TTL baseline은 아래와 같다.

| Surface | Backing Dataset | TTL Rule |
|---|---|---|
| public products/filter API | `public_product_projection` | 5분 |
| public dashboard summary API | `dashboard_metric_snapshot` | 15분 |
| public dashboard rankings API | `dashboard_ranking_snapshot` | 15분 |
| public dashboard scatter API | `dashboard_scatter_snapshot` | 15분 |
| admin refresh/metric health view | aggregate job status metadata | 1분 이하 또는 no-cache |

### 5.3 Invalidation Rule

- new aggregate job가 성공하면 관련 cache version을 invalidate한다.
- manual override가 public-facing field를 바꾸면 affected scope cache를 즉시 invalidate한다.
- failed refresh는 active cache를 제거하지 않는다.

---

## 6. Metric Health Baseline

admin metric health는 최소 아래를 보여줄 수 있어야 한다.

- last successful refresh time
- last attempted refresh time
- refresh status
- affected aggregate domain
- stale flag
- missing data ratio or equivalent completeness note
- last error summary if failed

---

## 7. Failure Handling Rules

- aggregate refresh 실패는 run warning으로 남긴다.
- canonical approval/publish state는 aggregate refresh failure 때문에 롤백하지 않는다.
- public API는 latest successful snapshot을 계속 서빙한다.
- latest successful snapshot이 없으면 해당 domain은 empty state 또는 degraded response를 반환하되 freshness/status를 함께 노출해야 한다.

---

## 8. What This Strategy Intentionally Does Not Decide

아래 항목은 이번 문서 범위 밖이다.

- KPI formula exact definition
- ranking metric tie-break rule
- scatter axis final meaning by product type
- chart color/UX semantics

이 항목은 `1.7.2`, `1.7.3` 및 public/admin UX 설계에서 닫는다.

---

## 9. Interfaces and Follow-On Work Unlocked

- `1.5.1`: public products/dashboard API source dataset 연결
- `1.5.2`: admin refresh health/status API 연결
- `5.6`: aggregate dataset 생성
- `5.8`: dashboard API 구현
- `5.13`: freshness/metric note 표기

---

## 10. WBS Mapping

| WBS ID | Closure in This Document |
|---|---|
| 1.4.5 | Sections 2-9 |

---

## 11. Change History

| Date | Change |
|---|---|
| 2026-04-01 | Initial aggregate and cache refresh strategy created for WBS 1.4.5 |
