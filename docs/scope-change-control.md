# FPDS Scope Change Control

Version: 1.0  
Date: 2026-03-29  
Status: Active  
Source Documents:
- `docs/FPDS_Requirements_Definition_v1_5.md`
- `docs/plan.md`
- `docs/WBS.md`
- `docs/decision-log.md`
- `docs/raid-log.md`
- `docs/working-agreement.md`

---

## 1. Purpose

이 문서는 FPDS 프로젝트에서 범위 변경을 어떻게 제안하고, 평가하고, 승인하고, 반영할지 정하는 기준 문서다.

목적:
- 문서 기준으로 확정된 범위가 구두 요청으로 흔들리지 않게 한다.
- must-have와 later 항목을 섞지 않도록 한다.
- 변경이 생겨도 WBS, roadmap, decision log, RAID log가 같은 상태를 유지하게 한다.
- 설계 단계와 구현 단계 모두에서 scope creep를 통제한다.

---

## 2. Change Control Principles

1. 범위 변경은 자동 반영하지 않는다.
2. Product Owner 승인 전까지 어떤 변경도 공식 범위가 아니다.
3. 변경은 반드시 문서로 남긴다.
4. 변경 요청은 기능 추가뿐 아니라 삭제, 우선순위 이동, acceptance 변경도 포함한다.
5. 구현 중인 항목보다 설계 마감과 gate 통과 기준을 우선 보호한다.
6. open item closure와 별개로, 새 기능 요구는 change request로 취급한다.

---

## 3. What Counts as a Scope Change

아래 항목은 모두 scope change로 본다.

- 신규 기능 추가
- 기존 기능의 사용자 대상 확대
- Prototype에서 Phase 1 기능을 당겨오는 요청
- Phase 1에서 Phase 2 기능을 당겨오는 요청
- acceptance 기준 변경
- 지원 국가, 은행, 상품군 확대
- 인증, 권한, 보안 정책의 범위 확대
- API 제공 범위 확대
- i18n 대상 언어 확대
- 운영 필수 문서나 evidence pack 범위 확대

아래 항목은 원칙적으로 scope change가 아니다.

- 이미 승인된 범위 안에서의 표현 수정
- 오탈자 수정
- 문서 명확화
- 이미 열린 open decision을 닫기 위한 상세화

---

## 4. Change Categories

| Category | Meaning | Typical Handling |
|---|---|---|
| Clarification | 기존 범위를 더 명확하게 설명하는 변경 | 문서 보완 후 관련 문서만 동기화 |
| Adjustment | 범위는 유지하되 우선순위/순서를 바꾸는 변경 | WBS/roadmap 재정렬 후 승인 |
| Expansion | 기능, 대상, acceptance가 실제로 늘어나는 변경 | impact review 후 Product Owner 승인 필요 |
| Reduction | 범위 축소 또는 cutline 조정 | acceptance 영향 검토 후 승인 |
| Deferral | 현재 범위를 later stage로 미루는 변경 | roadmap/WBS/update 필요 |

---

## 5. Required Review Dimensions

모든 change request는 최소 아래 항목을 함께 본다.

- Why: 왜 필요한가
- Scope impact: 어떤 WBS 항목이 바뀌는가
- Schedule impact: 일정이 얼마나 늘어나는가
- Staffing impact: 현재 인력으로 가능한가
- Acceptance impact: 기존 성공 기준이 바뀌는가
- Security impact: auth, RBAC, API, crawler 경계에 영향이 있는가
- Data impact: schema, taxonomy, validation에 영향이 있는가
- Dependency impact: BX-PF, 외부 source, reviewer, 번역 운영에 영향이 있는가

---

## 6. Change Request Workflow

1. 요청 등록  
   요청자는 변경 내용을 한 문장으로 적고 이유를 붙인다.
2. 분류  
   `Clarification`, `Adjustment`, `Expansion`, `Reduction`, `Deferral` 중 하나로 분류한다.
3. 영향 분석  
   일정, 범위, acceptance, 보안, 데이터, 의존성 영향을 문서 기준으로 평가한다.
4. 제안안 작성  
   승인 시 어떤 문서가 바뀌는지 명시한다.
5. Product Owner 결정  
   `Approve`, `Reject`, `Defer` 중 하나로 결정한다.
6. 문서 반영  
   승인된 경우 WBS, roadmap, decision log, 필요 시 RAID log를 같은 턴에 업데이트한다.
7. 실행 반영  
   구현 단계라면 승인된 변경만 backlog와 build sequence에 반영한다.

---

## 7. Approval Rules

| Change Type | Decision Owner | Notes |
|---|---|---|
| Clarification | Tech Lead draft + Product Owner confirm | 범위 증가가 없어야 한다 |
| Adjustment | Product Owner | stage 순서나 cutline 영향 확인 필요 |
| Expansion | Product Owner | roadmap/WBS/acceptance 영향 명시 필수 |
| Reduction | Product Owner | 어떤 가치를 포기하는지 기록 필요 |
| Deferral | Product Owner | later 이동 시 milestone 영향 기록 필요 |

추가 원칙:
- acceptance 기준이 바뀌면 반드시 Product Owner 승인 대상이다.
- Phase 2 기능을 Phase 1로 당기는 요청은 기본값이 `Reject` 또는 `Defer`다.
- Prototype First 원칙을 깨는 요청은 특별 사유 없이는 승인하지 않는다.

---

## 8. Required Document Updates

변경이 승인되면 아래 문서를 함께 갱신한다.

- `docs/WBS.md`
- `docs/roadmap.md`
- `docs/decision-log.md`
- `docs/raid-log.md`
- 필요 시 `docs/working-agreement.md`
- 필요 시 세부 설계 문서

최소 반영 규칙:
- 범위 정의가 바뀌면 `decision-log` 업데이트
- 일정/순서가 바뀌면 `roadmap` 업데이트
- 리스크/가정/이슈/의존성이 바뀌면 `raid-log` 업데이트
- task 상태나 구조가 바뀌면 `WBS` 업데이트

---

## 9. Change Request Template

아래 형식으로 기록한다.

```md
Change ID:
Date:
Requested By:
Category:
Requested Change:
Reason:
Affected WBS:
Schedule Impact:
Acceptance Impact:
Security/Data/Dependency Impact:
Decision:
Approved By:
Document Updates Required:
```

---

## 10. Definition of Done for WBS 0.4

`WBS 0.4 Scope change control 규칙 확정`은 아래 조건을 충족하면 완료로 본다.

- scope change 정의가 문서화되어 있다.
- change request workflow가 정의되어 있다.
- approval owner가 명시되어 있다.
- 문서 업데이트 규칙이 정리되어 있다.
- Product Owner 중심 승인 원칙이 working agreement와 정합성을 가진다.

---

## 11. Change History

| Date | Change |
|---|---|
| 2026-03-29 | Initial scope change control created |
