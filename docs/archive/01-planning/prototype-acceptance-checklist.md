# Prototype Acceptance Checklist

Version: 1.0
Date: 2026-04-06
Status: Approved Baseline for WBS 1.8.3
Source Documents:
- `docs/01-planning/WBS.md`
- `docs/01-planning/plan.md`
- `docs/archive/01-planning/prototype-backlog.md`
- `docs/archive/01-planning/td-savings-source-inventory.md`
- `docs/02-requirements/scope-baseline.md`
- `docs/03-design/workflow-state-ingestion-design.md`
- `docs/03-design/domain-model-canonical-schema.md`
- `docs/00-governance/stage-gate-checklist.md`

---

## 1. Purpose

이 문서는 `TD Savings Prototype`의 공식 acceptance 기준을 고정한다.

목적:
- Gate B에서 무엇을 `성공`, `조건부 성공`, `실패`로 볼지 명확히 한다.
- demo, findings memo, evidence pack이 같은 기준을 참조하도록 맞춘다.
- Prototype이 `완전 자동화`를 증명하는 단계인지, `feasibility + reviewability`를 증명하는 단계인지 경계를 고정한다.

이 문서는 구현 자체를 승인하지 않는다.
실제 구현 시작은 별도 build-start approval 이후에만 가능하다.

---

## 2. Acceptance Principle

### 2.1 Prototype Success Meaning

Prototype success는 아래를 의미한다.

1. `TD Savings` 대상 source가 최소 1회 end-to-end로 처리된다.
2. review 가능한 candidate output과 evidence trace가 남는다.
3. operator가 read-only viewer로 결과를 확인할 수 있다.
4. 실패 원인과 확장 리스크가 findings memo로 정리된다.

### 2.2 Prototype Does Not Need to Prove

아래 항목은 Prototype acceptance의 필수 조건이 아니다.

- full admin console 운영화
- auto-approve
- BX-PF actual publish
- public grid/dashboard
- 다국어 UI 적용
- 모든 source 완전 자동화
- 모든 ancillary fee field 완전 정규화

---

## 3. Pass Conditions

### 3.1 Core Must-Pass Checklist

모든 항목이 충족되어야 `Pass`로 본다.

| Area | Pass Condition | Evidence |
|---|---|---|
| Source coverage | 3개 target product (`TD Every Day`, `TD ePremium`, `TD Growth`)가 run 결과에 포함된다. | run summary, viewer screenshot |
| Source type coverage | 최소 `HTML detail 1개`, `current values source 1개`, `governing PDF 1개` 이상이 parse/evidence 경로에 포함된다. | source-by-source run output |
| Pipeline execution | discovery, snapshot, parse, chunk, extraction, normalization, validation, review routing이 1회 이상 이어서 동작한다. | run detail or equivalent evidence |
| Reviewability | candidate가 read-only viewer 또는 동등한 화면에서 확인 가능하다. | viewer demo |
| Evidence linkage | 핵심 field가 source excerpt/page or section anchor와 함께 제시된다. | trace screenshot, evidence sample |
| Findings closure | prototype findings memo가 작성되어 다음 단계 리스크와 보완 방향을 설명한다. | findings memo |

### 3.2 Key Field Acceptance Set

아래 필드는 `각 target product`에 대해 가능한 범위에서 reviewable candidate에 포함되어야 한다.

필수:
- `product_name`
- `product_type = savings`
- `source_language`
- `description_short` 또는 동등한 source summary
- `monthly_fee` 또는 해당 account fee 표현
- `standard_rate` 또는 `public_display_rate`
- `validation_status`
- `review_status`

강권:
- `transaction_fee`
- `withdrawal_limit_text`
- `tier_definition_text`
- `interest_calculation_method`
- `interest_payment_frequency`
- `notes`

특수 항목:
- `TD Growth Savings`는 `boosted_rate eligibility / qualifying transaction rule`이 완전 정규화되지 않아도 된다.
- 대신 해당 내용이 `notes` 또는 equivalent evidence-linked field로 남아 있어야 한다.

### 3.3 Demo Readiness Checklist

Prototype demo는 아래를 보여줄 수 있어야 한다.

1. 어떤 source set으로 run을 실행했는지 설명 가능하다.
2. 3개 target product가 결과에 나타난다.
3. 최소 1개 field에 대해 evidence excerpt와 source anchor를 보여준다.
4. 최소 1개 warning 또는 failure reason을 설명할 수 있다.
5. findings memo에서 Big 5 확장 시 추가 보완점을 설명할 수 있다.

---

## 4. Conditional Pass Rules

아래 경우는 `Conditional Pass`로 본다.

| Scenario | Conditional Pass Rule | Required Follow-Up |
|---|---|---|
| 일부 P1 supporting PDF 실패 | P0 핵심 흐름이 성립하면 통과 가능 | known issue와 follow-up backlog 기록 |
| 일부 ancillary fee field 누락 | 핵심 product identity/rate/fee/evidence가 성립하면 통과 가능 | field gap를 findings memo에 명시 |
| current values source drift | snapshot timestamp와 source note가 남아 있으면 통과 가능 | drift 대응 전략 기록 |
| `TD Growth Savings` 특수 로직 완전 정규화 실패 | note/evidence linkage와 manual review 가능성이 있으면 통과 가능 | special-case extraction follow-up 기록 |
| rerun 재현성 미완성 | first successful run과 evidence pack이 충분하면 조건부 통과 가능 | rerun hardening을 P1로 이월 |

---

## 5. Fail Conditions

아래 중 하나라도 발생하면 `Fail`로 본다.

| Fail Condition | Why It Fails |
|---|---|
| 3개 target product 중 하나라도 결과에 나타나지 않음 | prototype scope coverage를 증명하지 못함 |
| end-to-end run이 stage 중간에서 반복적으로 끊겨 candidate output이 남지 않음 | feasibility 자체가 증명되지 않음 |
| evidence-to-field trace가 불가능함 | Evidence First 원칙 미충족 |
| read-only viewer 또는 동등한 검토 인터페이스가 없음 | operator reviewability를 증명하지 못함 |
| findings memo 없이 단순 성공 여부만 남음 | 확장 의사결정 입력이 부족함 |
| 결과 품질이 사람 설명 없이 재현 불가능하고 문서화도 없음 | Gate B 판단 근거가 부족함 |

---

## 6. Failure Handling and Next-Step Decision

### 6.1 If Pass

- Gate B demo 준비로 이동한다.
- findings memo 기준으로 Big 5 확장 준비 항목을 backlog에 연결한다.

### 6.2 If Conditional Pass

- Gate B decision note에 `조건부 통과` 사유를 남긴다.
- blocking이 아닌 보완 항목은 Prototype hardening 또는 Phase 1 backlog로 이월한다.

### 6.3 If Fail

- `snapshot/parsing/evidence/viewer` 중 어느 레이어가 막혔는지 분류한다.
- `1.8.4 spike` 범위를 조정하거나 추가 spike를 계획한다.
- Build sequence는 보완 계획 문서화 전까지 다음 단계로 넘어가지 않는다.

---

## 7. Required Acceptance Artifacts

Gate B 제출물은 최소 아래를 포함해야 한다.

- prototype demo
- first successful run summary
- source-by-source status summary
- sample evidence linkage 2건 이상
- viewer screenshot 또는 equivalent
- findings memo
- Gate B decision note

---

## 8. Mapping to Existing Backlog

| Backlog Story | Acceptance Meaning |
|---|---|
| `PB-01` ~ `PB-04` | source capture와 evidence pipeline이 실제로 동작해야 함 |
| `PB-05` | candidate, validation, review routing 결과가 남아야 함 |
| `PB-06` | operator reviewability를 보여줘야 함 |
| `PB-07` | first successful run evidence pack이 핵심 제출물 |
| `PB-08` | findings memo가 acceptance closure의 일부 |
| `PB-09` | 통과 필수는 아니지만 재현성 보강 항목 |

---

## 9. WBS Mapping

| WBS | This Document Coverage |
|---|---|
| `1.8.3` | Sections 2-8 |
| `1.8.4` | fail 시 추가 검증 대상 입력으로 Sections 4-6 사용 |
| `1.8.5` | Sprint 0 board의 done definition 입력으로 Sections 3 and 7 사용 |
| `1.8.6` | Build Start Gate review input으로 Sections 2-7 사용 |

---

## 10. Change History

| Date | Change |
|---|---|
| 2026-04-06 | Initial prototype acceptance checklist created for WBS 1.8.3 |
