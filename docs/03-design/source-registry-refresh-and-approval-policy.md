# FPDS Source Registry Refresh and Approval Policy

Version: 1.0
Date: 2026-04-10
Status: Active Operating Baseline
Source Documents:
- `docs/02-requirements/FPDS_Requirements_Definition_v1_5.md`
- `docs/02-requirements/scope-baseline.md`
- `docs/01-planning/WBS.md`
- `docs/01-planning/td-savings-source-inventory.md`
- `docs/03-design/workflow-state-ingestion-design.md`
- `docs/03-design/source-snapshot-evidence-storage-strategy.md`
- `docs/00-governance/decision-log.md`

---

## 1. Purpose

이 문서는 prototype와 Phase 1에서 사용할 source registry 운영 정책을 정의한다.

목적:
- bank 사이트의 URL drift, 상품 폐지, 신규 상품 출시를 운영 가능한 방식으로 다룬다.
- ingestion 재현성과 evidence traceability를 지키면서도 source drift를 빠르게 감지한다.
- active registry, 자동 refresh 결과, 운영자 승인 반영의 책임 경계를 고정한다.

이 문서는 운영 정책과 refresh flow를 정의한다.
candidate registry 저장 방식, admin UI, diff 화면, scheduler 배포 방식 같은 exact 구현은 후속 slice에서 구체화한다.

---

## 2. Problem Statement

은행 public site의 source는 아래 이유로 고정 자산이 아니다.

- 상품 detail URL이 별도 공지 없이 바뀔 수 있다.
- PDF 링크가 새 버전으로 교체되거나 redirect될 수 있다.
- 기존 상품이 종료되거나 비노출 처리될 수 있다.
- 신규 상품이 출시되어 entry page와 fee/rate page에 추가될 수 있다.

따라서 registry를 한 번 만든 뒤 수동으로만 오래 유지하면 drift가 누적된다.
반대로 ingestion 시작마다 registry를 자동 변경하면 run 재현성, evidence auditability, 운영 통제가 약해진다.

---

## 3. Baseline Policy

FPDS는 아래 하이브리드 방식을 baseline으로 채택한다.

1. `active registry`는 승인된 source set만 가진다.
2. ingestion 실행 시에는 registry를 자동 변경하지 않는다.
3. ingestion 실행 시에는 drift를 감지만 하고 warning 또는 review signal로 남긴다.
4. 별도 `refresh flow`는 source drift와 신규 candidate를 탐지할 수 있다.
5. refresh 결과는 바로 active registry로 승격하지 않고 `candidate diff`로 남긴다.
6. Product Owner 또는 운영자가 검토 후 승인한 변경만 active registry에 반영한다.

한 줄로 정리하면 아래와 같다.

`active registry is stable, refresh is exploratory, promotion is approved`

---

## 4. Why This Policy Was Chosen

### 4.1 Why Not Auto-Update On Every Ingestion Run

매 run 시작 시 registry를 자동 최신화하면 아래 문제가 생긴다.

- 같은 run type이라도 source scope가 시점마다 달라진다.
- evidence trace와 replay 결과가 흔들린다.
- 새 URL이나 새 상품이 operator review 없이 production-like flow에 들어온다.
- source registry가 운영 통제 문서가 아니라 crawler side effect가 된다.

### 4.2 Why Not Manual-Only Refresh

관리자가 필요할 때만 registry를 고치면 아래 문제가 생긴다.

- 404, redirect, drift를 늦게 발견한다.
- 신규 상품 누락이 길어질 수 있다.
- approved inventory와 live site의 차이가 누적된다.

### 4.3 Why The Hybrid Model Fits FPDS

하이브리드 모델은 아래 균형을 맞춘다.

- 재현성: ingestion은 승인된 active registry로 고정된다.
- 민감도: refresh와 preflight가 drift를 빠르게 감지한다.
- 통제: active registry 반영은 사람 승인 후에만 일어난다.
- 확장성: prototype에서는 CLI/문서 기반 승인으로 시작하고 later admin UI로 확장할 수 있다.

---

## 5. Registry States

source registry 운영에는 최소 아래 상태가 필요하다.

| State | Meaning | Can Ingestion Use It |
|---|---|---|
| `active` | 승인되어 현재 ingestion scope에 포함되는 source | Yes |
| `candidate` | refresh에서 새로 발견되었거나 변경 제안이 필요한 source | No |
| `deprecated` | 현재는 active에서 제외되지만 기록상 보존하는 source | No |
| `removed` | 더 이상 사용하지 않으며 운영상 종료된 source | No |

prototype 현재 구현은 사실상 `active`만 직접 사용한다.
`candidate`, `deprecated`, `removed`는 이번 문서에서 운영 정책으로 먼저 정의하고, runtime persistence와 UI는 후속 구현 범위로 둔다.

---

## 6. Registry Data Model Expectations

active registry와 candidate diff에는 아래 메타데이터가 필요하다.

- `source_id`
- `product_key` or equivalent stable logical product identifier
- `normalized_url`
- `source_type`
- `status`
- `priority`
- `discovery_role`
- `seed_source_flag`
- `last_verified_at`
- `last_seen_at`
- `change_reason`
- `redirect_target_url` if applicable
- `alias_urls` if applicable

중요 원칙:
- `source_id`는 운영 식별자다.
- URL은 바뀔 수 있으므로 stable product grouping key가 필요하다.
- URL 기반 `source_document_id`는 runtime lineage용으로 계속 유효하지만, registry 운영 관점에서는 URL과 독립적인 식별자도 함께 가져야 한다.

---

## 7. Operational Flows

### 7.1 Ingestion Preflight

목적:
- active registry를 바꾸지 않고도 drift를 조기에 감지한다.

권장 동작:
- active registry의 각 source에 대해 lightweight fetch 또는 head-equivalent 확인
- `200`, `3xx redirect`, `404`, `content-type changed`, `final URL changed` 같은 상태 기록
- entry/detail page에서는 기존 known product link set과 큰 차이가 있는지 체크
- 결과는 ingestion run metadata, warning, or operator note로 기록

중요 규칙:
- preflight는 registry를 자동 수정하지 않는다.
- preflight에서 신규 source를 active ingestion scope에 자동 추가하지 않는다.

### 7.2 Scheduled Refresh

목적:
- live site를 기준으로 source drift와 신규 candidate를 체계적으로 탐지한다.

권장 범위:
- entry page
- active detail pages
- known fee/rate pages
- active PDF links

refresh 결과는 아래 유형의 diff를 만들 수 있어야 한다.

- `new_source_candidate`
- `redirect_detected`
- `url_changed`
- `content_type_changed`
- `source_missing`
- `source_reappeared`
- `pdf_version_changed`
- `entry_listing_changed`

중요 규칙:
- refresh는 active registry를 직접 덮어쓰지 않는다.
- refresh 결과는 candidate change set 또는 equivalent review artifact로 남긴다.

### 7.3 Manual Approval and Promotion

운영자 또는 Product Owner는 refresh 결과를 보고 아래 중 하나를 선택한다.

- approve and promote to `active`
- keep as `candidate`
- mark as `deprecated`
- reject as out-of-scope

approval 시 필요한 최소 판단은 아래와 같다.

- 이 source가 현재 prototype 또는 Phase scope에 포함되는가
- 기존 source의 alias/redirect인가, 새로운 source인가
- 기존 canonical evidence 역할을 대체하는가, 보조 source인가
- URL 변경이 단순 drift인가, source identity 재정의가 필요한가

---

## 8. Recommended Cadence

prototype baseline 권장 cadence는 아래와 같다.

| Activity | Recommended Cadence | Purpose |
|---|---|---|
| ingestion preflight | every ingestion run | 직전 drift 감지 |
| scheduled refresh | once per day on business days | 신규 candidate 및 drift 탐지 |
| manual review | 2 to 3 times per week or on alert | candidate diff 처리 |
| active registry promotion | after explicit approval | 재현성 유지 |

트래픽과 site volatility가 높아지면 refresh cadence는 늘릴 수 있다.
하지만 active registry promotion은 계속 approval 기반을 유지하는 것을 원칙으로 한다.

---

## 9. Sequence Baseline

```text
Scheduler or Operator
    -> refresh job starts
    -> live entry/detail/pdf sources scanned
    -> candidate diffs generated
    -> review artifact stored

Operator or Product Owner
    -> reviews candidate diffs
    -> approves / rejects / deprecates

Registry Maintainer
    -> updates active registry
    -> records approval reason and date

Ingestion Run
    -> loads active registry only
    -> performs preflight drift check
    -> logs warnings if drift exists
    -> continues with approved active sources
```

---

## 10. Decision Rules for Common Cases

### 10.1 Redirect From Old URL To New URL

- refresh는 `redirect_detected`와 `redirect_target_url`를 기록한다.
- 기존 source와 동일 문서 역할이면 approval 후 active URL을 새 주소로 교체한다.
- 필요하면 old URL은 `alias_urls` 또는 change history에 남긴다.

### 10.2 Product Removed From Entry Page

- 즉시 삭제하지 않는다.
- `source_missing` 또는 `deprecated candidate`로 기록한다.
- 일정 기간 연속 미노출 또는 운영 확인 후 `deprecated`로 내린다.

### 10.3 New Product Appears On Entry Page

- 자동 active 추가 금지
- `candidate`로 생성
- scope 적합성과 expected field value를 검토 후 승인 반영

### 10.4 PDF File Name Changes But Role Stays The Same

- source role continuity를 우선 판단한다.
- 같은 governing document의 새 버전이면 같은 logical source 아래 URL만 갱신할 수 있다.
- 완전히 다른 약관 문서라면 새 candidate source로 본다.

---

## 11. Current Repository State vs Target Operating Model

현재 repo 구현 상태:

- `worker/discovery/data/td_savings_source_registry.json`은 approved active registry seed다.
- discovery는 active registry를 source of truth로 사용한다.
- snapshot capture는 selected source에 대해 lightweight preflight drift check를 수행할 수 있다.
- scheduled refresh artifact generation은 discovery warnings와 preflight drift 결과를 JSON artifact로 만들 수 있다.
- active registry 자동 승격, candidate persistence, approval UI는 아직 없다.

이번 문서가 정의하는 target operating model:

- ingestion preflight drift check 추가
- scheduled refresh 결과 artifact 추가
- candidate diff review and promotion 절차 추가
- later admin review UI 또는 equivalent operator tooling 추가

즉, 현재 구현은 `approved active registry + preflight signal + refresh artifact` 단계까지 와 있고, approval workflow automation은 후속 구현 범위다.

---

## 12. Non-Goals

이번 정책 문서가 아직 정하지 않는 것:

- exact scheduler platform
- admin UI wireframe
- diff persistence table schema
- notification channel detail
- cross-bank generalized registry engine

이 항목들은 prototype 운영 필요가 실제로 생기는 시점에 별도 slice로 닫는다.

---

## 13. Follow-On Work Unlocked

- discovery preflight drift check
- refresh result artifact design
- candidate diff persistence model
- operator review CLI or admin UI
- registry promotion audit log

---

## 14. Change History

| Date | Change |
|---|---|
| 2026-04-10 | Initial source registry refresh and approval policy added |
