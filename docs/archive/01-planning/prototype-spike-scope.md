# Prototype Spike Scope

Version: 1.0
Date: 2026-04-06
Status: Approved Baseline for WBS 1.8.4
Source Documents:
- `docs/01-planning/WBS.md`
- `docs/01-planning/plan.md`
- `docs/archive/01-planning/td-savings-source-inventory.md`
- `docs/archive/01-planning/prototype-backlog.md`
- `docs/archive/01-planning/prototype-acceptance-checklist.md`
- `docs/03-design/workflow-state-ingestion-design.md`
- `docs/03-design/source-snapshot-evidence-storage-strategy.md`
- `docs/03-design/domain-model-canonical-schema.md`
- `docs/00-governance/raid-log.md`

---

## 1. Purpose

이 문서는 Prototype 전에 먼저 검증해야 하는 `parser/snapshot spike` 범위와 종료 조건을 정의한다.

목적:
- 가장 위험한 source slice를 먼저 검증해 feasibility 리스크를 줄인다.
- `무엇을 알아내기 위한 spike인지`와 `무엇은 아직 결정하지 않는지`를 분리한다.
- snapshot, parse, evidence anchor, extraction 가능성에 대한 최소 판단 근거를 확보한다.

---

## 2. Spike Questions

이번 spike는 아래 질문에 답하는 것을 목표로 한다.

1. TD public HTML/PDF source를 안정적으로 snapshot할 수 있는가?
2. HTML와 PDF에서 evidence-ready parsed text와 anchor를 만들 수 있는가?
3. savings 핵심 field 추출에 필요한 구조적 신호가 충분한가?
4. `TD Growth Savings`와 governing PDF처럼 난이도 높은 source를 review fallback과 함께 다룰 수 있는가?

---

## 3. In-Scope Spike Targets

### 3.1 Primary Spike Sources

| Source ID | Why It Is In Scope | Spike Focus |
|---|---|---|
| `TD-SAV-004` | cross-product dependency와 boosted-rate logic이 가장 까다로움 | HTML structure, condition text, special-case note handling |
| `TD-SAV-007` | fee/service governing PDF의 표 구조가 복잡함 | PDF snapshot, table parse quality, fee evidence anchor |
| `TD-SAV-008` | interest calculation/tier rule의 핵심 governing PDF | PDF parse quality, tier anchor, interest rule extraction |

### 3.2 Secondary Spike Sources

| Source ID | Why It Is In Scope | Spike Focus |
|---|---|---|
| `TD-SAV-002` | 가장 단순한 HTML detail baseline | happy-path HTML pipeline 검증 |
| `TD-SAV-005` | dynamic current rate drift 확인 필요 | rate page snapshot timing and extracted values |

---

## 4. Explicit Out of Scope

이번 spike에서 아래는 종료 조건이 아니다.

- 모든 P1 supporting PDF 처리
- production-grade parser architecture 완성
- 자동 재시도/스케줄러 완성
- full admin viewer 구현
- Big 5 은행 일반화
- BX-PF publish path
- public UI / localization

---

## 5. Experiments

### 5.1 Experiment A: Snapshot Viability

목표:
- target HTML/PDF source를 안정적으로 가져오고 저장 가능한지 확인한다.

확인 항목:
- fetch success/failure pattern
- content type consistency
- response size and checksum capture
- redirect / query normalization behavior

성공 조건:
- primary spike source 3개 모두 raw snapshot 저장 가능

### 5.2 Experiment B: Parse and Anchor Quality

목표:
- HTML/PDF에서 사람이 검토할 수 있는 parsed text와 anchor를 얻을 수 있는지 확인한다.

확인 항목:
- heading/section anchor 유지 여부
- PDF page/row grouping 품질
- excerpt 재현 가능성
- partial parse 발생 시 note 남기기 가능 여부

성공 조건:
- `TD-SAV-004`, `TD-SAV-007`, `TD-SAV-008`에서 evidence excerpt를 다시 찾을 수 있다.

### 5.3 Experiment C: Key Field Extraction Feasibility

목표:
- canonical schema의 savings 핵심 필드가 최소 수준으로 추출 가능한지 확인한다.

우선 필드:
- `product_name`
- `description_short`
- `monthly_fee`
- `public_display_rate` or `standard_rate`
- `transaction_fee`
- `tier_definition_text`
- `interest_calculation_method`
- `interest_payment_frequency`

성공 조건:
- primary spike source에서 핵심 field 다수가 evidence-linked draft로 남는다.

### 5.4 Experiment D: Risk Retirement for Special Cases

목표:
- known high-risk case가 `완전 자동화` 없이도 reviewable path를 가질 수 있는지 확인한다.

특수 케이스:
- `TD Growth Savings`의 boosted-rate eligibility
- PDF table row merge ambiguity
- current rate drift와 snapshot timestamp dependency

성공 조건:
- special-case note 또는 warning과 함께 reviewable candidate path를 설명할 수 있다.

---

## 6. Spike Outputs

이번 spike는 최소 아래 결과를 남겨야 한다.

- source-by-source fetch/parse 결과표
- sample snapshot metadata
- sample parsed excerpt and anchor
- field extraction sample
- known issue list
- continue/adapt/stop recommendation

---

## 7. Exit Criteria

### 7.1 Continue

아래가 충족되면 Prototype build sequence를 계획대로 진행한다.

- primary spike source 3개가 snapshot 가능하다.
- evidence excerpt와 anchor가 재확인 가능하다.
- key field extraction feasibility가 최소 수준으로 보인다.
- high-risk source도 review fallback과 함께 설명 가능하다.

### 7.2 Adapt

아래가 발생하면 backlog 또는 acceptance 기준을 조정한다.

- source는 fetch되지만 PDF parse quality가 불안정한 경우
- 일부 핵심 field는 추출되지만 field naming/normalization이 흔들리는 경우
- `TD Growth Savings`는 note/evidence 중심으로만 다뤄야 하는 경우

필수 조치:
- acceptance에 conditional pass 규칙 반영
- prototype findings memo에 special-case 처리 원칙 기록

### 7.3 Stop / Re-Scope

아래가 발생하면 Prototype approach를 재검토한다.

- primary spike source 중 둘 이상에서 snapshot 자체가 불안정
- evidence anchor가 재현되지 않아 traceability를 설명할 수 없음
- 핵심 field extraction이 전반적으로 문서화 가능한 수준에 못 미침

필수 조치:
- source inventory 또는 spike target 재선정
- backlog 순서와 acceptance 기준 재협의

---

## 8. Recommended Execution Order

1. `TD-SAV-002`로 happy-path HTML snapshot/parse를 확인한다.
2. `TD-SAV-007`, `TD-SAV-008`로 PDF parse와 evidence anchor를 검증한다.
3. `TD-SAV-004`로 boosted-rate special case를 검증한다.
4. `TD-SAV-005`로 current values drift와 snapshot timestamp rule을 본다.

---

## 9. Spike-to-RAID Mapping

| RAID Item | Spike Relevance | Expected Outcome |
|---|---|---|
| `A-001` | TD Savings source sufficiency validation | source set은 충분한지, parser risk는 어느 수준인지 판단 |
| `D-002` | source website/PDF accessibility | fetch/parse 안정성의 실제 감각 확보 |
| `R-002` | PDF parsing instability | PDF table risk를 조기 검증 |

---

## 10. WBS Mapping

| WBS | This Document Coverage |
|---|---|
| `1.8.4` | Sections 2-9 |
| `1.8.3` | acceptance conditional/fail rule 입력으로 Sections 5 and 7 사용 |
| `1.8.5` | Sprint 0 sequencing 입력으로 Section 8 사용 |

---

## 11. Change History

| Date | Change |
|---|---|
| 2026-04-06 | Initial prototype spike scope created for WBS 1.8.4 |
