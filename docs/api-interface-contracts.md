# FPDS API and Interface Contracts

Version: 1.0
Date: 2026-04-01
Status: Approved Baseline for WBS 1.5.1-1.5.5
Source Documents:
- `docs/FPDS_Requirements_Definition_v1_5.md`
- `docs/WBS.md`
- `docs/system-context-diagram.md`
- `docs/domain-model-canonical-schema.md`
- `docs/workflow-state-ingestion-design.md`
- `docs/review-run-publish-audit-state-design.md`
- `docs/erd-draft.md`
- `docs/source-snapshot-evidence-storage-strategy.md`
- `docs/retrieval-vector-starting-point.md`
- `docs/aggregate-cache-refresh-strategy.md`
- `docs/environment-separation-strategy.md`
- `docs/decision-log.md`

---

## 1. Purpose

이 문서는 `WBS 1.5 API and Interface Contracts`를 닫기 위한 기준 문서다.

목적:
- `public`, `admin`, `internal orchestration`, `BX-PF`, `external API`의 경계를 구현 전 기준으로 고정한다.
- `1.5.1 public API`, `1.5.2 admin API`, `1.5.3 internal orchestration interface`, `1.5.4 BX-PF write contract`, `1.5.5 external SaaS/Open API draft`를 하나의 문서 기준으로 정리한다.
- `1.6.x security`, `1.7.x UX`, `5.x/6.x/7.x implementation`이 같은 request/response vocabulary를 참조하도록 맞춘다.

이 문서는 route/resource contract와 payload baseline을 닫는다. exact auth mechanism, exact RBAC matrix, exact CORS allowlist, exact BX-PF remote schema, exact external API quota는 후속 WBS에서 구체화한다.

---

## 2. Baseline Decisions Carried Forward

본 문서는 아래 확정 사항을 반영한다.

1. public API는 익명 읽기 전용 경계이며 evidence raw artifact를 노출하지 않는다.
2. admin API는 인증된 운영자 전용 경계이며 review, run, publish, usage, audit-facing 데이터를 조회하거나 변경한다.
3. internal orchestration interface는 browser-facing route가 아니라 private worker/service boundary다.
4. approved normalized product의 target master store는 BX-PF이며, FPDS는 publish/reconciliation metadata를 유지한다.
5. public dashboard/grid는 latest successful aggregate snapshot을 기준으로 서빙한다.
6. source-derived text는 source language 단일 값으로 유지하고, localized label은 display/resource layer에서 분리한다.
7. external SaaS/Open API는 Phase 2 대상이지만 resource contract draft는 지금 고정한다.

---

## 3. Cross-Cutting Contract Rules

### 3.1 Surface and Base Path Rules

| Surface | Base Path or Boundary | Intended Client |
|---|---|---|
| Public | `/api/public/*` | anonymous browser UI |
| Admin | `/api/admin/*` | authenticated admin UI |
| Internal | private service / queue / worker interface | API server, worker, scheduler |
| External SaaS/Open API | `/api/v1/*` | Phase 2 client/tenant consumer |
| BX-PF | private connector boundary | publish worker only |

### 3.2 Data Formatting Rules

- timestamp는 UTC ISO 8601 string을 기본으로 한다.
- 금액과 rate는 machine-readable numeric field를 우선 제공한다.
- UI label이 필요한 경우 code와 display label을 함께 반환한다.
- `product_name`, `description_short`, `eligibility_text`, `fee_waiver_condition`, `notes`, `source_subtype_label`은 source-derived value를 그대로 반환한다.
- locale은 `en`, `ko`, `ja`를 baseline으로 하며, locale은 label/help/freshness note 표현에만 영향을 준다.

### 3.3 Response Envelope Baseline

성공 응답 baseline:

```json
{
  "data": {},
  "meta": {
    "request_id": "req_123",
    "locale": "en",
    "generated_at": "2026-04-01T00:00:00Z"
  }
}
```

목록 응답 baseline:

```json
{
  "data": {
    "items": []
  },
  "meta": {
    "request_id": "req_123",
    "page": 1,
    "page_size": 20,
    "total_items": 120
  }
}
```

오류 응답 baseline:

```json
{
  "error": {
    "code": "validation_error",
    "message": "Invalid query parameter",
    "details": {}
  },
  "meta": {
    "request_id": "req_123"
  }
}
```

### 3.4 Freshness and Cache Metadata Rules

- public products/filter API는 `public_product_projection` freshness를 노출한다.
- public dashboard summary/rankings/scatter API는 대응 aggregate snapshot freshness를 노출한다.
- admin metric health API는 aggregate job status, latest successful snapshot, missing-data ratio를 함께 노출한다.
- freshness metadata 예시는 아래와 같다.

```json
{
  "freshness": {
    "snapshot_id": "metric_snap_001",
    "refreshed_at": "2026-04-01T00:00:00Z",
    "cache_ttl_sec": 900,
    "status": "fresh"
  }
}
```

### 3.5 Security Boundary Rules

- public API는 anonymous access를 허용하지만 write action은 없다.
- admin API는 authenticated actor context를 전제로 한다.
- internal interface와 BX-PF contract는 browser에서 직접 호출하지 않는다.
- external API는 Phase 2 credential-bound access를 전제로 한다.
- exact session cookie vs token, tenant credential type, CORS allowlist, CSRF policy는 `1.6.x`에서 닫는다.

---

## 4. Public API Contract

### 4.1 Contract Scope

이 섹션은 아래 WBS 범위를 닫는다.

- `1.5.1 public API contract`

대상 기능:
- products grid
- filters
- dashboard summary
- dashboard rankings
- dashboard scatter

### 4.2 Shared Query Model

public API는 가능한 한 동일한 filter scope를 공유한다.

권장 query field:

| Query | Type | Notes |
|---|---|---|
| `locale` | string | `en`, `ko`, `ja`, default locale fallback 허용 |
| `country_code` | string | Phase 1 baseline은 `CA` |
| `bank_code` | string or repeated | multi-select 허용 |
| `product_type` | string or repeated | `chequing`, `savings`, `gic` |
| `subtype_code` | string or repeated | optional |
| `target_customer_tag` | string or repeated | optional |
| `fee_bucket` | string | optional |
| `minimum_balance_bucket` | string | optional |
| `minimum_deposit_bucket` | string | optional |
| `term_bucket` | string | optional |
| `sort_by` | string | products endpoint 전용 |
| `sort_order` | string | `asc`, `desc` |
| `page` | integer | default `1` |
| `page_size` | integer | default `20`, max `100` |

### 4.3 `GET /api/public/products`

목적:
- public product grid를 위한 product list를 제공한다.
- filter/sort/page 결과는 `public_product_projection` 기준으로 반환한다.
- public evidence는 포함하지 않는다.

응답 `data.items[]` baseline:

| Field | Description |
|---|---|
| `product_id` | canonical continuity id |
| `bank_code` | bank code |
| `bank_name` | canonical bank display name |
| `country_code` | country |
| `product_family` | `deposit` baseline |
| `product_type` | canonical type code |
| `product_type_label` | localized label |
| `subtype_code` | optional canonical subtype |
| `subtype_label` | localized subtype label if available |
| `product_name` | source-derived product name |
| `source_language` | source language code |
| `currency` | currency code |
| `status` | product lifecycle status |
| `public_display_rate` | display rate snapshot |
| `public_display_fee` | display fee snapshot |
| `minimum_balance` | minimum balance if available |
| `minimum_deposit` | minimum deposit if available |
| `product_highlight_badge_code` | badge code |
| `product_highlight_badge_label` | localized badge label |
| `target_customer_tags` | normalized tag codes |
| `target_customer_tag_labels` | localized tag labels |
| `last_verified_at` | last verification timestamp |
| `last_changed_at` | latest detected change if available |

응답 `meta` 추가 field:

- `applied_filters`
- `sort`
- `freshness`

### 4.4 `GET /api/public/filters`

목적:
- grid/dashboard 공통 filter option과 count를 제공한다.
- client가 임의 option set을 하드코딩하지 않도록 한다.

응답 `data` baseline:

| Field | Description |
|---|---|
| `banks[]` | `{ code, label, count }` |
| `product_types[]` | `{ code, label, count }` |
| `subtypes[]` | `{ code, label, product_type, count }` |
| `target_customer_tags[]` | `{ code, label, count }` |
| `fee_buckets[]` | `{ code, label, count }` |
| `minimum_balance_buckets[]` | `{ code, label, count }` |
| `minimum_deposit_buckets[]` | `{ code, label, count }` |
| `term_buckets[]` | `{ code, label, count }` |

### 4.5 `GET /api/public/dashboard-summary`

목적:
- KPI cards와 freshness note를 제공한다.
- backing dataset은 `dashboard_metric_snapshot`이다.

응답 `data.metrics[]` baseline:

| Field | Description |
|---|---|
| `metric_key` | `total_active_products`, `highest_display_rate`, `recently_changed_products`, etc. |
| `label` | localized metric label |
| `value` | numeric or stringified scalar |
| `unit` | `count`, `percent`, `currency`, `days`, etc. |
| `scope_note` | optional localized note |

### 4.6 `GET /api/public/dashboard-rankings`

목적:
- ranking widget dataset을 제공한다.
- backing dataset은 `dashboard_ranking_snapshot`이다.

응답 `data.widgets[]` baseline:

| Field | Description |
|---|---|
| `ranking_key` | `highest_rate`, `lowest_monthly_fee`, `lowest_minimum_deposit`, `recently_updated`, etc. |
| `title` | localized widget title |
| `metric_label` | localized metric label |
| `items[]` | ranked product summary rows |

ranked row baseline:
- `rank`
- `product_id`
- `bank_name`
- `product_name`
- `product_type`
- `metric_value`
- `metric_unit`
- `last_changed_at`

### 4.7 `GET /api/public/dashboard-scatter`

목적:
- comparative scatter plot dataset을 제공한다.
- backing dataset은 `dashboard_scatter_snapshot`이다.

추가 query:

| Query | Type | Notes |
|---|---|---|
| `axis_preset` | string | product-type-aware preset |

응답 `data` baseline:

| Field | Description |
|---|---|
| `chart_key` | scatter configuration key |
| `title` | localized chart title |
| `x_axis` | `{ key, label, unit }` |
| `y_axis` | `{ key, label, unit }` |
| `points[]` | product points |
| `methodology_note` | localized note |

point baseline:
- `product_id`
- `bank_code`
- `bank_name`
- `product_name`
- `product_type`
- `x_value`
- `y_value`
- `highlight_badge_code`

### 4.8 Public API Explicit Exclusions

- source URL raw list
- snapshot object path
- parsed full text body
- evidence chunk excerpt
- internal validation issue detail
- review decision history

---

## 5. Admin API Contract

### 5.1 Contract Scope

이 섹션은 아래 WBS 범위를 닫는다.

- `1.5.2 admin API contract`

대상 기능:
- review queue and decision
- product detail and change history
- run status
- BX-PF integration status
- usage dashboard
- dashboard refresh and metric health

### 5.2 `GET /api/admin/review-tasks`

목적:
- review queue list를 제공한다.

권장 query:
- `state`
- `bank_code`
- `product_type`
- `validation_status`
- `assigned_to`
- `created_from`
- `created_to`
- `page`
- `page_size`

응답 `data.items[]` baseline:

| Field | Description |
|---|---|
| `review_task_id` | queue item id |
| `candidate_id` | candidate id |
| `run_id` | producing run id |
| `country_code` | country |
| `bank_code` | bank code |
| `bank_name` | bank display name |
| `product_type` | canonical type |
| `product_name` | source-derived name |
| `review_state` | current task state |
| `candidate_state` | candidate lifecycle state |
| `validation_status` | pass/warning/error |
| `validation_issue_codes` | issue list |
| `source_confidence` | confidence |
| `issue_summary` | short summary |
| `created_at` | queue creation time |
| `updated_at` | latest task update |

### 5.3 `GET /api/admin/review-tasks/:id`

목적:
- review detail과 trace viewer 데이터를 제공한다.

응답 `data` baseline:

| Field | Description |
|---|---|
| `review_task` | current task summary |
| `candidate` | normalized candidate snapshot |
| `proposed_fields` | canonical field/value pairs |
| `evidence_links[]` | field-level evidence summary |
| `validation_issues[]` | issue detail |
| `decision_history[]` | previous decisions |
| `model_executions[]` | relevant execution references |

`evidence_links[]`는 아래를 포함한다.

- `field_name`
- `candidate_value`
- `evidence_chunk_id`
- `evidence_text_excerpt`
- `source_document_id`
- `source_snapshot_id`
- `source_url`
- `citation_confidence`
- `model_execution_id`

### 5.4 Review Decision Routes

결정 route baseline:

- `POST /api/admin/review-tasks/:id/approve`
- `POST /api/admin/review-tasks/:id/reject`
- `POST /api/admin/review-tasks/:id/edit-approve`
- `POST /api/admin/review-tasks/:id/defer`

공통 request field:

| Field | Description |
|---|---|
| `reason_code` | normalized decision reason |
| `reason_text` | optional operator note |
| `actor_context` | server-side actor snapshot |

`edit-approve` 추가 field:

| Field | Description |
|---|---|
| `edited_fields` | field patch set |
| `edit_summary` | optional summary |

공통 response baseline:

| Field | Description |
|---|---|
| `review_decision_id` | persisted decision id |
| `review_state` | new review state |
| `candidate_state` | new candidate state |
| `canonical_product_id` | created or matched product id when applicable |
| `product_version_id` | approved version id when applicable |
| `publish_item` | publish tracker summary if created |

### 5.5 `GET /api/admin/products`

목적:
- canonical product list와 admin drilldown entry를 제공한다.

권장 query:
- `bank_code`
- `product_type`
- `status`
- `changed_after`
- `page`
- `page_size`

응답 `data.items[]` baseline:
- `canonical_product_id`
- `country_code`
- `bank_code`
- `bank_name`
- `product_type`
- `product_name`
- `status`
- `current_version_no`
- `last_verified_at`
- `last_changed_at`
- `latest_change_event_type`
- `publish_state`

### 5.6 `GET /api/admin/products/:id`

목적:
- canonical continuity record, current version, change summary, publish summary를 제공한다.

응답 `data` baseline:

| Field | Description |
|---|---|
| `product` | canonical product summary |
| `current_version` | latest approved product version |
| `field_evidence_links[]` | finalized evidence linkage |
| `change_events[]` | change history summary |
| `publish_items[]` | publish tracker summary |

### 5.7 `GET /api/admin/runs`

목적:
- run list와 운영 상태 요약을 제공한다.

응답 `data.items[]` baseline:
- `run_id`
- `run_type`
- `run_status`
- `started_at`
- `completed_at`
- `source_item_count`
- `candidate_count`
- `review_queued_count`
- `success_count`
- `failure_count`
- `partial_completion_flag`
- `error_summary`

### 5.8 `GET /api/admin/runs/:id`

목적:
- run detail, stage summary, failure summary, usage summary를 제공한다.

응답 `data` baseline:

| Field | Description |
|---|---|
| `run` | run core fields |
| `source_items[]` | per-source processing summary |
| `stage_summaries[]` | stage-level status and counts |
| `error_events[]` | failure or degraded event summary |
| `usage_summary` | token/cost summary |
| `related_review_tasks[]` | queue items produced by run |

### 5.9 `GET /api/admin/change-history`

목적:
- product or run-linked change event list를 제공한다.

권장 query:
- `product_id`
- `bank_code`
- `product_type`
- `change_type`
- `changed_from`
- `changed_to`

응답 `data.items[]` baseline:
- `change_event_id`
- `canonical_product_id`
- `product_version_id`
- `change_type`
- `change_summary`
- `changed_fields`
- `detected_at`
- `review_task_id`
- `actor_type`

### 5.10 `GET /api/admin/bxpf-publish`

목적:
- BX-PF publish monitor를 제공한다.

권장 query:
- `publish_state`
- `bank_code`
- `product_type`
- `attempt_result`
- `page`
- `page_size`

응답 `data.items[]` baseline:
- `publish_item_id`
- `canonical_product_id`
- `product_version_id`
- `publish_state`
- `pending_reason_code`
- `last_attempted_at`
- `attempt_count`
- `target_master_id`
- `last_result_category`
- `last_result_message`
- `reconciliation_required`

### 5.11 `GET /api/admin/llm-usage`

목적:
- run, agent, model 단위 usage dashboard 데이터를 제공한다.

권장 query:
- `from`
- `to`
- `run_id`
- `agent_name`
- `model_name`

응답 `data` baseline:

| Field | Description |
|---|---|
| `totals` | aggregate tokens/cost |
| `by_model[]` | per-model aggregation |
| `by_agent[]` | per-agent aggregation |
| `by_run[]` | per-run aggregation |
| `anomaly_candidates[]` | unusual usage drilldown |

### 5.12 `GET /api/admin/dashboard-health`

목적:
- public dashboard aggregate freshness와 metric health를 제공한다.

응답 `data` baseline:
- `domains[]`

domain row baseline:
- `domain_key`
- `latest_snapshot_id`
- `latest_success_at`
- `latest_failure_at`
- `status`
- `missing_data_ratio`
- `cache_ttl_sec`

### 5.13 Admin API Notes

- exact admin auth mechanism은 `1.6.1`에서 닫는다.
- exact role matrix는 `1.6.2`에서 닫는다.
- admin API는 evidence trace를 제공하지만 raw object storage path를 browser에 직접 노출하지 않는다.

---

## 6. Internal Orchestration Interface

### 6.1 Contract Scope

이 섹션은 아래 WBS 범위를 닫는다.

- `1.5.3 internal orchestration interface`

대상 인터페이스:
- discovery
- retrieval
- normalization
- review queue create/update
- usage capture

이 계약은 public HTTP route 설계가 아니라 private service boundary 설계다.

### 6.2 Shared Internal Rules

- 모든 internal request는 `correlation_id`와 `run_id`를 포함해야 한다.
- replay/retry 가능한 step은 idempotency key 또는 equivalent dedupe metadata를 포함해야 한다.
- worker 간 경계에서는 source raw artifact 대신 DB/object reference id를 우선 전달한다.
- internal interface는 PII나 browser session context를 전제로 하지 않는다.

### 6.3 Source Discovery Interface

request baseline:

| Field | Description |
|---|---|
| `correlation_id` | orchestration trace id |
| `run_id` | run id |
| `country_code` | country |
| `bank_code` | bank |
| `seed_urls[]` | known source entry points |
| `discovery_mode` | scheduled, manual, retry |

response baseline:
- `source_items[]`

source item baseline:
- `source_document_id`
- `source_type`
- `resolved_url`
- `discovery_status`
- `discovery_notes`

### 6.4 Evidence Retrieval Interface

목적:
- field-level evidence linking을 위한 candidate chunk set을 반환한다.

request baseline:

| Field | Description |
|---|---|
| `correlation_id` | orchestration trace id |
| `run_id` | run id |
| `parsed_document_id` | parsed body reference |
| `field_names[]` | target canonical fields |
| `metadata_filters` | bank/product/source filters |
| `retrieval_mode` | metadata-only or vector-assisted |

response baseline:
- `matches[]`

match baseline:
- `evidence_chunk_id`
- `field_name`
- `score`
- `retrieval_mode`
- `evidence_text_excerpt`
- `source_document_id`
- `source_snapshot_id`
- `model_execution_id`

### 6.5 Schema Lookup and Normalization Interface

schema lookup request baseline:
- `country_code`
- `product_type`
- `taxonomy_version`

schema lookup response baseline:
- `canonical_fields[]`
- `required_fields[]`
- `validation_rules[]`
- `localized_label_keys[]`

normalization request baseline:
- `correlation_id`
- `run_id`
- `candidate_id`
- `extracted_fields`
- `source_language`
- `schema_context`

normalization response baseline:
- `normalized_candidate`
- `validation_status`
- `validation_issue_codes`
- `source_confidence`
- `field_evidence_links[]`

### 6.6 Review Queue Interface

create/update request baseline:
- `candidate_id`
- `run_id`
- `queue_reason_codes`
- `issue_summary`
- `validation_status`
- `source_confidence`
- `evidence_link_count`

response baseline:
- `review_task_id`
- `review_state`
- `queue_created_at`

### 6.7 Usage Capture Interface

request baseline:
- `run_id`
- `model_execution_id`
- `agent_name`
- `provider_name`
- `model_name`
- `input_tokens`
- `output_tokens`
- `estimated_cost`
- `started_at`
- `completed_at`
- `execution_status`

response baseline:
- `llm_usage_record_id`
- `recorded_at`

---

## 7. BX-PF Write Contract Draft

### 7.1 Contract Scope

이 섹션은 아래 WBS 범위를 닫는다.

- `1.5.4 BX-PF write contract draft`

이 계약은 FPDS publish service와 BX-PF connector 사이의 adapter-facing contract를 고정한다. 실제 BX-PF remote API endpoint, auth header 이름, transport 세부 값은 후속 integration 구현에서 맞춘다.

### 7.2 Publish Preconditions

BX-PF publish request는 아래 조건을 만족할 때만 생성한다.

1. review decision이 `approved` 또는 `edited_approved`다.
2. approved canonical version이 생성되어 있다.
3. publish item이 존재하고 current state가 publish-eligible이다.
4. environment rule상 real write가 허용되는 경우에만 real connector를 호출한다.

### 7.3 Connector Request Baseline

request object 이름 권장안:

- `BxpfProductUpsertRequest`

payload baseline:

```json
{
  "publish_item_id": "pub_001",
  "canonical_product_id": "prod_001",
  "product_version_id": "ver_003",
  "idempotency_key": "fpds-prod_001-ver_003",
  "source_system": "FPDS",
  "environment": "prod",
  "product": {},
  "pricing": {},
  "features": {},
  "provenance": {}
}
```

### 7.4 Required Field Mapping Baseline

모든 BX-PF publish payload는 아래 identity/classification field를 포함해야 한다.

| FPDS Source | BX-PF Adapter Field | Required | Notes |
|---|---|---:|---|
| `canonical_product.product_id` | `canonical_product_id` | O | FPDS continuity identity |
| `product_version.product_version_id` | `product_version_id` | O | approved version snapshot id |
| `product_version.version_no` | `product_version_no` | O | version sequence |
| `country_code` | `country_code` | O | Phase 1 baseline `CA` |
| `bank_code` | `bank_code` | O | canonical bank code |
| `bank_name` | `bank_name` | O | display and audit trace |
| `product_family` | `product_family` | O | Phase 1 baseline `deposit` |
| `product_type` | `product_type` | O | canonical type |
| `subtype_code` | `subtype_code` | X | optional subtype |
| `source_subtype_label` | `source_subtype_label` | X | source-derived |
| `product_name` | `product_name` | O | source-derived single-language value |
| `source_language` | `source_language` | O | source language code |
| `currency` | `currency` | O | ISO 4217 |
| `status` | `status` | O | active/inactive/discontinued/draft |
| `target_customer_tags` | `target_customer_tags` | X | normalized tags |
| `effective_date` | `effective_date` | X | source effective date |
| `last_verified_at` | `last_verified_at` | O | verification timestamp |
| `last_changed_at` | `last_changed_at` | X | latest detected change |

### 7.5 Pricing and Product-Specific Field Mapping

공통 financial field:

| FPDS Source | BX-PF Adapter Field | Required |
|---|---|---:|
| `public_display_rate` | `pricing.public_display_rate` | X |
| `public_display_fee` | `pricing.public_display_fee` | X |
| `monthly_fee` | `pricing.monthly_fee` | X |
| `minimum_balance` | `pricing.minimum_balance` | X |
| `minimum_deposit` | `pricing.minimum_deposit` | X |
| `standard_rate` | `pricing.standard_rate` | X |
| `promotional_rate` | `pricing.promotional_rate` | X |
| `promotional_period_text` | `pricing.promotional_period_text` | X |
| `term_length_text` | `pricing.term_length_text` | X |
| `term_length_days` | `pricing.term_length_days` | X |
| `fee_waiver_condition` | `pricing.fee_waiver_condition` | X |
| `eligibility_text` | `pricing.eligibility_text` | X |
| `notes` | `pricing.notes` | X |

product-type specific block:

| Product Type | Required Baseline |
|---|---|
| `chequing` | identity fields + one of fee-related fields |
| `savings` | identity fields + one of rate-related fields |
| `gic` | identity fields + one of rate-related fields + one of term fields + `minimum_deposit` |

type-specific optional field는 `features` block으로 보낸다.

### 7.6 Provenance Block Baseline

BX-PF connector request는 아래 provenance metadata를 함께 받을 수 있어야 한다.

| Field | Description |
|---|---|
| `source_document_ids[]` | supporting source document ids |
| `source_snapshot_ids[]` | supporting snapshot ids |
| `field_evidence_refs[]` | `{ field_name, evidence_chunk_id }` summary |
| `review_decision_id` | approving decision reference |
| `run_id` | producing run |

이 provenance block은 adapter boundary의 감사/재처리를 위한 기준이다. 실제 BX-PF remote payload에 그대로 전송할지 여부는 connector implementation에서 결정한다.

### 7.7 Connector Response Baseline

response object 이름 권장안:

- `BxpfProductUpsertResponse`

응답 field baseline:

| Field | Description |
|---|---|
| `publish_item_id` | originating publish tracker |
| `result_category` | `applied`, `duplicate`, `retryable_error`, `contract_error`, `ambiguous` |
| `target_master_id` | target master identifier if known |
| `target_version_ref` | optional target-side version reference |
| `target_status_code` | transport or domain status code |
| `target_message` | short result summary |
| `received_at` | target receive timestamp if known |
| `completed_at` | attempt completion timestamp |
| `retry_after_sec` | retry hint if present |
| `reconciliation_required` | boolean |
| `raw_response_ref` | persisted raw response reference if stored |

### 7.8 Publish State Mapping Rule

| Connector `result_category` | FPDS Publish State | Reason Code Guidance |
|---|---|---|
| `applied` | `published` | target linkage persisted |
| `duplicate` | `published` | same target state already exists |
| `retryable_error` | `retry` | `transient_transport_error`, `rate_limited`, etc. |
| `contract_error` | `pending` | `target_validation_error` or `missing_contract_mapping` |
| `ambiguous` | `reconciliation` | `response_ambiguous`, `target_state_mismatch` |

### 7.9 Environment Rule

- `dev`에서는 BX-PF real write를 수행하지 않는다.
- `dev` publish flow는 stub connector 또는 validation-only mode를 사용한다.
- `prod`에서만 real connector write를 허용한다.
- browser-facing route는 BX-PF를 직접 호출하지 않는다.

---

## 8. External SaaS/Open API Draft

### 8.1 Contract Scope

이 섹션은 아래 WBS 범위를 닫는다.

- `1.5.5 external SaaS/Open API draft`

이 계약은 Phase 2 external API의 resource model draft를 정한다. exact credential type, quota, tenant isolation enforcement detail은 후속 security/API WBS에서 닫는다.

### 8.2 Draft Principles

1. external API는 public UI API의 단순 재노출이 아니라 client-facing stable resource contract다.
2. external API는 machine-friendly code/value payload를 우선하고 localized label은 보조 필드로 제공한다.
3. external API는 evidence raw artifact를 반환하지 않는다.
4. tenant/client scope는 credential-bound context를 기본으로 한다.

### 8.3 Draft Authentication and Tenant Scope

- 모든 external API request는 client or tenant credential을 요구한다.
- exact mechanism은 `API key` 또는 `Bearer token` 중 하나로 후속 `1.6.3`에서 확정한다.
- Phase 2 baseline에서는 credential 하나가 하나의 tenant scope에 바인딩되는 모델을 우선한다.
- request query로 임의 `tenant_id`를 넘겨 cross-tenant scope를 바꾸는 모델은 기본 허용하지 않는다.

### 8.4 `GET /api/v1/products`

목적:
- tenant/client가 normalized product list를 조회한다.

권장 query:
- `country_code`
- `bank_code`
- `product_type`
- `status`
- `updated_after`
- `cursor`
- `limit`
- `locale`

응답 `data.items[]` baseline:
- `product_id`
- `country_code`
- `bank_code`
- `bank_name`
- `product_type`
- `product_type_label`
- `subtype_code`
- `subtype_label`
- `product_name`
- `source_language`
- `currency`
- `status`
- `public_display_rate`
- `public_display_fee`
- `minimum_balance`
- `minimum_deposit`
- `last_verified_at`
- `last_changed_at`

`meta` baseline:
- `next_cursor`
- `returned_count`
- `request_id`

### 8.5 `GET /api/v1/products/:id`

목적:
- single normalized product detail을 제공한다.

응답 `data` baseline:
- `product`
- `current_version`
- `change_summary`
- `publish_status_summary`

public/admin 전용 internal fields, evidence detail, review history는 포함하지 않는다.

### 8.6 `GET /api/v1/banks`

목적:
- available bank registry와 product coverage summary를 제공한다.

응답 `data.items[]` baseline:
- `bank_code`
- `bank_name`
- `country_code`
- `active_product_count`
- `product_types[]`
- `last_verified_at`

### 8.7 `GET /api/v1/changes`

목적:
- downstream consumer가 product change feed를 조회한다.

권장 query:
- `changed_after`
- `cursor`
- `limit`
- `country_code`
- `bank_code`
- `product_type`

응답 `data.items[]` baseline:
- `change_event_id`
- `product_id`
- `product_version_id`
- `change_type`
- `changed_at`
- `summary`
- `bank_code`
- `product_type`

### 8.8 External API Explicit Exclusions

- review queue
- run history
- LLM usage
- BX-PF connector status
- raw evidence and trace viewer
- admin-only audit events

---

## 9. Open Items Not Blocking This Contract Set

| Area | Open Item | Follow-Up WBS | Why It Does Not Block 1.5 |
|---|---|---|---|
| Admin Auth | session cookie vs token | `1.6.1` | route contract와 auth mechanism은 분리 가능하다. |
| RBAC | role matrix and action permission detail | `1.6.2` | admin route shape를 먼저 고정하고 권한 matrix를 후속 적용할 수 있다. |
| External Auth | exact credential type and tenant isolation enforcement | `1.6.3` | external API resource model draft를 먼저 닫을 수 있다. |
| CORS / CSRF | exact origin and browser policy | `1.6.4`, `1.6.6` | route/payload contract와 transport security detail은 후속 분리 가능하다. |
| BX-PF Remote Schema | exact endpoint, header, remote field names | `6.1` | adapter-facing contract만 먼저 고정해도 connector 구현을 시작할 수 있다. |
| Rate Limits | public/admin/external quota and abuse thresholds | `6.5`, `7.6` | functional route contract를 먼저 닫을 수 있다. |

---

## 10. Interfaces and Follow-On Work Unlocked

- `1.6.1`: admin auth mechanism decision
- `1.6.2`: RBAC matrix and decision action permission
- `1.6.3`: external API auth direction
- `1.7.1`: public grid UI structure
- `1.7.4`: admin information architecture
- `5.7`: public products API implementation
- `5.8`: dashboard APIs implementation
- `6.1`: BX-PF connector implementation
- `7.5`: external search/detail/change API implementation

---

## 11. WBS Mapping

| WBS ID | Closure in This Document |
|---|---|
| 1.5.1 | Section 4 |
| 1.5.2 | Section 5 |
| 1.5.3 | Section 6 |
| 1.5.4 | Section 7 |
| 1.5.5 | Section 8 |

---

## 12. Change History

| Date | Change |
|---|---|
| 2026-04-01 | Initial API and interface contract baseline created for WBS 1.5.1-1.5.5 |
