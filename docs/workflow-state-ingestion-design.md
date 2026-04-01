# FPDS Workflow and State Design - End-to-End Ingestion Flow

Version: 1.0  
Date: 2026-03-31  
Status: Approved Baseline for WBS 1.3.1  
Source Documents:
- `docs/FPDS_Requirements_Definition_v1_5.md`
- `docs/plan.md`
- `docs/WBS.md`
- `docs/domain-model-canonical-schema.md`
- `docs/decision-log.md`
- `docs/scope-baseline.md`
- `docs/stage-gate-checklist.md`

---

## 1. Purpose

이 문서는 FPDS의 `WBS 1.3.1 end-to-end ingestion flow 상세화`를 구현 가능한 수준으로 정의한다.

목적:
- source discovery부터 publish 준비, aggregate refresh, admin override까지의 공식 흐름을 한 장으로 고정한다.
- 각 단계의 입력/출력, 저장물, 실패 처리, idempotency 기준을 명확히 한다.
- 이후 `1.3.2 review state machine`, `1.3.3 run lifecycle`, `1.3.4 publish lifecycle`, `1.3.5 audit trail scope`의 기준 문서로 사용한다.
- `1.4.x`, `1.5.3`, `1.8.2`가 같은 ingestion 흐름을 참조하도록 맞춘다.

이 문서는 구현 코드나 세부 DB schema를 직접 정의하는 문서가 아니다.  
세부 state chart, ERD, BX-PF field mapping, vector backend 선택은 후속 WBS에서 구체화한다.

---

## 2. Baseline Decisions

본 문서는 아래 결정을 반영한다.

1. review queue 생성 단위는 `candidate` 기준으로 본다.
2. retry 기본 모델은 `source/stage 단위 재시도 + run partial completion 허용 + publish 별도 retry/reconciliation`이다.
3. source identity는 `bank_code + normalized_source_url + source_type`를 기본 키로 보고, `checksum/fingerprint`는 change detection과 idempotency 판단에 사용한다.
4. retrieval은 `retrieval-ready evidence 저장`까지를 이 문서에서 고정하고, vector index 구현 상세는 `WBS 1.4.4`에서 닫는다.
5. BX-PF publish는 `interface-first + publish state 중심`으로 정의하고, exact write contract와 field mapping은 `WBS 1.5.4`에서 닫는다.

---

## 3. Design Principles

1. **Evidence First**: 모든 canonical 결과는 가능한 한 evidence chunk와 연결 가능해야 한다.
2. **Human Review by Design**: Prototype에서는 전량 review, Phase 1에서는 policy/config 기준 auto-approve를 허용한다.
3. **Idempotent by Default**: 동일 source 재수집과 동일 run 재처리 시 중복 product 생성, 중복 publish, 불필요한 change event를 최소화해야 한다.
4. **Partial Failure Isolation**: 일부 source/stage 실패가 전체 run 중단으로 곧바로 이어지면 안 된다.
5. **FPDS Owns Operational Truth**: source snapshot, parsed text, evidence, run, review, audit, publish/reconciliation metadata는 FPDS가 소유한다.
6. **Interface First**: retrieval backend와 BX-PF connector 구현 상세는 후속 설계로 열어 두되, ingestion 흐름에서 요구하는 입출력 계약은 먼저 고정한다.

---

## 4. End-to-End Flow Summary

| Stage | Input | Core Action | Primary Output | Persisted Artifacts | Failure Handling |
|---|---|---|---|---|---|
| 0. Run Initialization | schedule or manual trigger | run 생성, 대상 source set 확정 | `run_id`, source batch | run header, trigger metadata | invalid trigger면 run fail |
| 1. Discovery | source registry, bank/product scope | crawl target 발견/정규화 | discovered source list | source metadata | source 단위 warning 기록 |
| 2. Snapshot Fetch | discovered source | HTML/PDF fetch, 원문 보존 | raw snapshot | snapshot object, fetch metadata | source 단위 retry, 최종 실패 시 source failed |
| 3. Parse | raw snapshot | parsed text 생성 | parsed document | parsed text, parser metadata | parser retry 후 partial failure 가능 |
| 4. Chunk & Evidence Registration | parsed text | retrieval 가능한 chunk 생성 | evidence-ready chunks | chunk rows, chunk metadata | source 단위 partial failure |
| 5. Extraction | chunks, schema context | structured field 후보 추출 | extracted draft | extraction result, model run ref, usage | retry 또는 review fallback |
| 6. Normalization | extracted draft, taxonomy/schema | canonical candidate 매핑 | normalized candidate | candidate record, field mapping | invalid taxonomy면 validation error |
| 7. Validation | normalized candidate | field/cross-field 규칙 검증 | validation result | issue codes, severity, validation status | error면 review 강제 |
| 8. Review Routing | candidate + validation + confidence policy | auto-approve 또는 review queue 분기 | routed candidate | review task or approval marker | routing policy 불가 시 review |
| 9. Canonical Upsert & Change Assessment | approved candidate or auto-approved candidate | canonical continuity 판단, version/change event 생성 | canonical product version | canonical product, evidence links, change event | continuity 불명확 시 review/defer |
| 10. Publish Preparation | approved canonical record | BX-PF payload 준비, publish eligibility 판단 | publish-ready item or pending | publish request draft, pending reason | pending/retry/reconciliation 상태로 이관 |
| 11. Publish / Queue | publish-ready item | BX-PF publish 또는 queue 적재 | publish result | publish event, reconciliation metadata | publish retry queue 사용 |
| 12. Aggregate Refresh | canonical/publish result | public/admin aggregate 갱신 | refreshed datasets | metric snapshots, ranking/scatter source | refresh failure는 run warning |
| 13. Admin Inspection & Override | run, review, publish outputs | 운영자 확인, override, reason 기록 | review decision / manual override | review decision, override diff, audit log | override 후 change/audit 갱신 |

---

## 5. Stage-by-Stage Design

### 5.1 Stage 0. Run Initialization

- 입력: scheduler trigger, manual re-run trigger, prototype test trigger
- 처리:
  - `run_id`를 발급한다.
  - 실행 범위(`bank`, `country`, `product_type`, source subset)를 고정한다.
  - run 시작 시각, trigger 종류, actor/system 식별자를 남긴다.
- 출력:
  - run header
  - 이번 run에서 처리할 source candidate 목록
- 저장물:
  - `crawl_run` 또는 동등 run record
- 규칙:
  - 동일 source를 여러 번 발견해도 run 내 source candidate는 deduplicate한다.
  - run은 source별 세부 결과 집계를 허용해야 한다.

### 5.2 Stage 1. Discovery

- 입력: source registry, seed URL, linked PDF discovery rule
- 처리:
  - HTML page와 linked PDF를 발견한다.
  - URL을 정규화한다.
  - source identity를 `bank_code + normalized_source_url + source_type`로 계산한다.
  - `source_language`, `discovered_at`, `country_code`, `bank_code`, `source_type`를 기록한다.
- 출력:
  - normalized discovered source set
- 저장물:
  - source metadata row
- 규칙:
  - redirect, query noise, duplicate links는 normalized URL 기준으로 합친다.
  - source registry 밖의 예외 source는 warning으로 남기고 자동 확장하지 않는다.

### 5.3 Stage 2. Snapshot Fetch

- 입력: discovered source
- 처리:
  - HTML/PDF를 fetch한다.
  - raw response 또는 equivalent snapshot을 object storage에 저장한다.
  - fetch 시점의 checksum/fingerprint를 계산한다.
  - fetch status, content type, size, response metadata를 남긴다.
- 출력:
  - raw snapshot reference
  - fingerprint
- 저장물:
  - snapshot object
  - fetch metadata
- idempotency:
  - 동일 `source identity + fingerprint`이면 중복 snapshot 생성 대신 기존 snapshot을 재사용할 수 있다.
- 실패 처리:
  - source 단위 retry를 허용한다.
  - 최종 실패한 source는 run 전체를 즉시 fail시키지 않고 source failure로 누적한다.

### 5.4 Stage 3. Parse

- 입력: raw snapshot
- 처리:
  - HTML/PDF를 extraction 가능한 parsed text로 변환한다.
  - parser version, parse timestamp, parse quality note를 남긴다.
- 출력:
  - parsed document
- 저장물:
  - parsed text
  - parser metadata
- 실패 처리:
  - parser retry 가능
  - parse가 완전히 불가능하면 source failed
  - 부분 파싱만 가능하면 이후 `partial_source_failure` 후보가 될 수 있다

### 5.5 Stage 4. Chunk and Evidence Registration

- 입력: parsed document
- 처리:
  - retrieval-ready chunk를 생성한다.
  - chunk offset, page/section anchor, excerpt를 기록한다.
  - source document와 chunk를 연결한다.
- 출력:
  - evidence-ready chunk set
- 저장물:
  - chunk records
  - chunk metadata
- 규칙:
  - 공개 사용자에게는 노출하지 않지만 admin trace에서는 재조회 가능해야 한다.
  - 이 단계에서는 retrieval readiness만 고정하며 vector index backend 선택은 `1.4.4`에서 결정한다.

### 5.6 Stage 5. Extraction

- 입력: chunk set, canonical schema context, taxonomy registry
- 처리:
  - extraction agent가 구조화 field 후보를 만든다.
  - 가능한 경우 field-to-evidence linkage 초안을 함께 만든다.
  - LLM/model usage와 model run reference를 기록한다.
- 출력:
  - extracted draft
- 저장물:
  - extraction result
  - model run reference
  - usage record
- 실패 처리:
  - extraction 실패는 source 단위 retry 대상이다.
  - partial extraction만 가능하면 다음 단계에서 validation/review routing으로 보낸다.

### 5.7 Stage 6. Normalization

- 입력: extracted draft, taxonomy registry, canonical schema v1
- 처리:
  - 추출 결과를 `normalized_candidate`로 매핑한다.
  - `product_type`, `subtype_code`, source-derived field 정책을 적용한다.
  - `candidate_id`와 `run_id`를 연결한다.
- 출력:
  - normalized candidate
- 저장물:
  - candidate record
  - field mapping metadata
- 규칙:
  - source-derived text는 locale별 복제 저장하지 않는다.
  - subtype이 미등록이면 `other`로 수용하고 source label을 보존한다.

### 5.8 Stage 7. Validation

- 입력: normalized candidate
- 처리:
  - canonical schema 문서의 field-level validation rule을 적용한다.
  - identity, taxonomy, subtype, language, timestamp, financial sanity, product-type requiredness, cross-field rule을 검사한다.
  - issue code와 severity를 기록한다.
- 출력:
  - `validation_status`
  - `validation_issue_codes`
- 저장물:
  - validation result
- 필수 issue code 연결:
  - `required_field_missing`
  - `invalid_taxonomy_code`
  - `invalid_numeric_range`
  - `invalid_term_value`
  - `conflicting_evidence`
  - `ambiguous_mapping`
  - `partial_source_failure`
  - `inconsistent_cross_field_logic`

### 5.9 Stage 8. Review Routing

- 입력: candidate, validation result, confidence score, routing config
- 처리:
  - Prototype에서는 모든 candidate를 review queue로 보낸다.
  - Phase 1에서는 config 기반 auto-approve를 허용한다.
  - `FORCE_REVIEW_ISSUE_CODES` 또는 `conflicting_evidence`가 있으면 review 강제다.
- 출력:
  - review task 또는 approval marker
- 저장물:
  - `review_task`
  - routing reason
- review queue 단위:
  - 기본 단위는 `candidate`다.
  - review item은 `candidate_id`, bank, country, product_type, product_name, issue summary, confidence, validation result, linked evidence를 가져야 한다.
- 관련 config:
  - `AUTO_APPROVE_MIN_CONFIDENCE`
  - `REVIEW_WARNING_CONFIDENCE_FLOOR`
  - `FORCE_REVIEW_ISSUE_CODES`
  - `DISCONTINUED_ABSENCE_RUN_THRESHOLD`

### 5.10 Stage 9. Canonical Upsert and Change Assessment

- 입력: approved candidate 또는 auto-approved candidate
- 처리:
  - 기존 canonical product와 continuity를 비교한다.
  - 신규/변경/중단/재분류/수동수정 여부를 판단한다.
  - canonical product version을 생성 또는 갱신한다.
  - field evidence link를 확정한다.
- 출력:
  - canonical product version
  - change event
- 저장물:
  - `canonical_product`
  - `field_evidence_link`
  - `change_event`
- idempotency:
  - 동일 source 재실행으로 의미 있는 필드 변경이 없으면 중복 change event를 만들지 않는다.
  - 동일 continuity product는 새 `product_id`를 남발하지 않는다.
- 주의:
  - continuity rule의 세부 알고리즘은 ERD/API 설계와 함께 후속 상세화가 필요하다.

### 5.11 Stage 10. Publish Preparation

- 입력: approved canonical record
- 처리:
  - BX-PF publish 가능 조건을 점검한다.
  - publish payload 초안을 만든다.
  - 환경/권한/계약 미충족 시 `pending`으로 남기고 사유를 기록한다.
- 출력:
  - publish-ready item 또는 pending item
- 저장물:
  - publish request draft
  - pending reason
- 규칙:
  - 이 단계는 interface-first 수준으로만 고정한다.
  - exact BX-PF write contract와 field mapping은 `1.5.4`에서 정의한다.

### 5.12 Stage 11. Publish / Queue

- 입력: publish-ready item
- 처리:
  - BX-PF publish를 실행하거나 queue에 적재한다.
  - 성공, 실패, retry 필요, reconciliation 필요 상태를 남긴다.
- 출력:
  - publish result
- 저장물:
  - `publish_event`
  - reconciliation metadata
- 실패 처리:
  - publish는 ingestion run과 분리된 retry 모델을 가진다.
  - publish 실패가 canonical approval 자체를 되돌리지는 않는다.

### 5.13 Stage 12. Aggregate Refresh

- 입력: canonical product, change event, publish result
- 처리:
  - public product grid index를 갱신한다.
  - dashboard summary/ranking/scatter용 aggregate dataset을 갱신한다.
  - freshness timestamp를 기록한다.
- 출력:
  - refreshed aggregate views
- 저장물:
  - metric snapshot
  - ranking/scatter source dataset
- 규칙:
  - aggregate refresh 실패는 warning으로 남길 수 있으나 canonical data commit 자체를 취소하지는 않는다.

### 5.14 Stage 13. Admin Inspection and Override

- 입력: review task, canonical product, trace data, publish state
- 처리:
  - 운영자가 approve, reject, edit & approve, defer를 수행한다.
  - override diff와 사유를 저장한다.
  - manual override 시 change history와 audit log를 함께 남긴다.
- 출력:
  - review decision
  - manual override result
- 저장물:
  - `review_decision`
  - override diff
  - audit log

---

## 6. Idempotency and Retry Model

### 6.1 Idempotency Rules

- source identity는 `bank_code + normalized_source_url + source_type`로 계산한다.
- content identity는 `checksum/fingerprint`로 판단한다.
- 동일 source identity에서 fingerprint가 변하지 않으면 불필요한 downstream 재처리를 생략할 수 있다.
- candidate는 항상 `run_id`와 연결해 생성 이력을 남긴다.
- canonical continuity는 동일 상품의 versioning을 우선하고, 재실행만으로 새 product를 만들지 않는다.
- publish는 canonical approval와 분리된 상태로 추적해 중복 publish를 막는다.

### 6.2 Retry Rules

- retry 기본 단위는 `source` 또는 `stage`다.
- run은 partial completion을 허용한다.
- source fetch, parse, extraction 실패는 source 단위 retry 후 최종 실패로 마감할 수 있다.
- publish는 별도 retry queue와 reconciliation 흐름으로 처리한다.
- quarantine, backoff, DLQ 같은 세부 운영 메커니즘은 `1.3.3`, `1.3.4`, runbook 설계에서 구체화한다.

---

## 7. Prototype vs Phase 1 Routing Difference

| Area | Prototype | Phase 1 |
|---|---|---|
| review routing | 모든 candidate review | policy/config 조건 충족 시 auto-approve 가능 |
| publish | actual publish flow 비필수 | BX-PF interface/pending/retry/reconciliation 추적 필요 |
| admin surface | basic internal result viewer 중심 | review queue, trace, run, history, usage 필요 |
| operational strictness | feasibility 우선 | auditability, repeatability, publish readiness 우선 |

---

## 8. Interfaces This Document Unlocks

이 문서는 아래 후속 작업의 기준 입력이다.

- `1.3.2`: review task 상태와 전이 정의
- `1.3.3`: run 상태, stage별 집계, retry boundary 정의
- `1.3.4`: publish pending/retry/reconciliation 상태 정의
- `1.3.5`: review/auth/publish/audit event 저장 범위 정의
- `1.4.1`: public/admin/api/worker/storage/BX-PF 경계도 작성
- `1.4.2`: run, source, snapshot, chunk, candidate, review, publish, change 중심 ERD 작성
- `1.4.4`: retrieval/vector backend 시작점 결정
- `1.5.3`: internal orchestration interface 초안 작성
- `1.8.2`: prototype backlog를 stage/task 단위로 분해

---

## 9. Open Follow-Up Items

아래 항목은 이 문서에서 일부러 열어 둔다.

- review/run/publish/audit state detail은 `docs/review-run-publish-audit-state-design.md`에서 종료 (`1.3.2` ~ `1.3.5`)
- vector index 구현 여부와 pgvector 도입 범위 (`1.4.4`)
- BX-PF exact payload, required fields, response contract (`1.5.4`)

---

## 10. WBS Mapping

| WBS ID | Closure in This Document |
|---|---|
| 1.3.1 | Sections 2-9 |

---

## 11. Change History

| Date | Change |
|---|---|
| 2026-03-31 | Initial end-to-end ingestion flow baseline created for WBS 1.3.1 |
| 2026-04-01 | Closed 1.3.2 - 1.3.5 follow-up items by linking `docs/review-run-publish-audit-state-design.md` |
