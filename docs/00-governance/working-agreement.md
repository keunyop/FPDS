# FPDS Working Agreement

Version: 1.0  
Date: 2026-03-29  
Status: Active  
Based on:
- `docs/02-requirements/FPDS_Requirements_Definition_v1_5.md`
- `docs/01-planning/plan.md`
- `docs/01-planning/WBS.md`
- `docs/02-requirements/scope-baseline.md`
- `docs/00-governance/decision-log.md`
- `docs/00-governance/raid-log.md`

---

## 1. Purpose

이 문서는 FPDS 프로젝트의 기본 운영 방식과 협업 규칙을 고정하기 위한 문서입니다.

목적:
- Product Owner와 실행 담당자가 같은 방식으로 일하도록 맞춘다.
- 문서 우선순위와 의사결정 흐름을 명확히 한다.
- 설계 단계와 구현 단계의 경계를 분명히 한다.
- 일정, 범위, 승인, 보고 방식의 기준점을 만든다.

---

## 2. Working Principles

1. Product Owner가 범위, 우선순위, acceptance, go/no-go의 최종 결정권을 가진다.
2. Tech Lead는 실행과 문서화를 주도하되, 고비용 결정은 Product Owner 승인 없이 고정하지 않는다.
3. 현재 단계의 목표는 `개발 시작`이 아니라 `개발을 시작해도 되는 상태`를 만드는 것이다.
4. 구현은 Product Owner가 명시적으로 시작 승인할 때까지 진행하지 않는다.
5. Prototype First 원칙을 유지한다.
6. Canonical data, validation, review workflow가 UI polish보다 우선한다.
7. Security는 설계 단계부터 포함한다.
8. 범위 변경은 change control 없이 반영하지 않는다.

---

## 3. Document Authority

문서 우선순위는 아래 순서를 따른다.

1. 최신 Product Owner 명시 지시
2. `docs/02-requirements/FPDS_Requirements_Definition_v1_5.md`
3. `docs/01-planning/plan.md`
4. `docs/01-planning/WBS.md`
5. `docs/00-governance/decision-log.md`
6. `docs/00-governance/raid-log.md`
7. 세부 설계 문서

해석 원칙:
- 상위 문서와 하위 문서가 충돌하면 상위 문서를 따른다.
- open item은 구현으로 우회하지 않고 결정 또는 문서화로 닫는다.
- 문서에 없는 내용을 추정해야 할 때는 저위험 항목만 합리적 가정을 사용한다.
- 되돌리기 비싼 항목은 Product Owner 확인 후 진행한다.

---

## 4. Current Delivery Mode

현재 FPDS는 `Gate A Pass 승인 완료 / Execution Ready` 상태로 운영한다.

현재 단계의 공식 목표:
- Gate A 통과 상태를 기준 문서에 반영한다.
- Foundation과 Prototype build의 `Next` 작업 순서를 유지한다.
- 실제 구현 시작 전까지 문서 기준과 execution order를 어긋나지 않게 관리한다.

현재 단계의 금지 항목:
- 승인 없이 범위를 확장하는 구현
- Sprint 0 execution order를 무시한 임의 착수
- change control 없이 Prototype 범위를 넘어서는 구현
- scope baseline과 Gate A 결과를 무시한 임의 개발 착수

---

## 5. Roles and Responsibilities

| Role | Responsibility |
|---|---|
| Product Owner | 범위, 우선순위, 승인, acceptance, 출시 판단 |
| Tech Lead / Technical Co-Founder | 실행 주도, 문서 정합성, 리스크 조기 식별 |
| Backend Engineer | API, DB, workflow, publish 설계 및 구현 |
| AI/Data Engineer | source, parsing, extraction, normalization 설계 및 구현 |
| Frontend Engineer | public/admin UX, IA, i18n 설계 및 구현 |
| Security / DevOps | auth, RBAC, secret, infra, monitoring, 배포 운영 |
| QA / Reviewer | acceptance 시나리오, regression, 운영 검증 |
| Domain Reviewer | 금융상품 taxonomy, field mapping, rule 검토 |

현재 문서 단계에서는 Tech Lead가 초안을 만들고 Product Owner가 방향과 승인권을 가진다.

---

## 6. Communication and Reporting

### 6.1 Communication Style

- 설명은 가능한 한 쉬운 언어로 한다.
- 기술 선택은 제품/운영 영향까지 번역해 설명한다.
- 중요한 갈림길은 trade-off와 함께 공유한다.
- 진행 중에는 짧고 자주 상태를 공유한다.

### 6.2 Reporting Format

상태 보고는 기본적으로 아래 순서를 따른다.

1. 무엇을 진행했는지
2. 왜 그 작업이 다음 순서인지
3. 무엇이 완료되었는지
4. 어떤 파일이 업데이트되었는지
5. 다음으로 자연스러운 1개 작업이 무엇인지

### 6.3 Escalation Rules

아래 상황에서는 Product Owner 확인이 필요하다.

- 범위가 늘어나는 결정
- acceptance 기준이 바뀌는 결정
- 보안/인증 방식처럼 되돌리기 비싼 결정
- 일정/비용에 큰 영향을 주는 결정
- 문서 근거만으로 합리적 추정이 어려운 결정

---

## 7. Governance Cadence

기본 cadence는 `plan.md` 기준으로 아래와 같이 운영한다.

- 주 1회 Steering / PO Sync
- 주 2회 Delivery Sync
- 주 1회 Design Review
- 매 Sprint 종료 시 Demo + Acceptance Check

현재는 문서 중심 단계이므로 아래 산출물 갱신이 우선이다.

- Decision Log
- RAID Log
- WBS Status
- open item closure 문서

---

## 8. Decision and Change Control

### 8.1 Decision Rules

- 주요 결정은 `docs/00-governance/decision-log.md`에 기록한다.
- 아직 닫히지 않은 항목은 `Open`으로 유지한다.
- 구두 합의처럼 남기지 않고 문서로 고정한다.

### 8.2 Scope Change Rules

- 범위 추가는 자동 반영하지 않는다.
- 범위 변경 전 영향 범위를 먼저 설명한다.
- 변경이 승인되면 WBS, decision log, 필요 시 RAID log를 함께 갱신한다.

### 8.3 Gate Rules

구현 시작 전 최소 조건:
- detailed design 완료
- prototype backlog 확정
- Build Start Gate 점검 가능 상태
- `Build Start Sign-off Package` 준비 완료
- Product Owner의 명시적 시작 승인

---

## 9. Working Rules for This Phase

1. requirements definition이 기준 문서다.
2. open item이 닫히기 전에는 해당 구현을 고정하지 않는다.
3. dashboard는 지표 정의 없이 먼저 만들지 않는다.
4. UX polish는 canonical data와 review flow 안정화 이후에 다룬다.
5. Decision Log와 RAID Log는 계속 갱신한다.
6. WBS 기준으로 다음 1개 작업씩 진행한다.

---

## 10. Definition of Done for WBS 0.1

`WBS 0.1 프로젝트 운영 방식 확정`은 아래 조건이 충족되면 완료로 본다.

- working agreement 문서가 생성되어 있다.
- 문서 우선순위가 정의되어 있다.
- 현재 단계의 금지 사항이 명시되어 있다.
- 보고 방식과 escalation 기준이 정리되어 있다.
- gate와 change control 원칙이 정리되어 있다.

본 문서 생성으로 위 조건은 충족된 것으로 본다.

---

## 11. Change History

| Date | Change |
|---|---|
| 2026-03-29 | Initial working agreement created |
| 2026-03-29 | Scope change control and stage gate checklist adopted as linked governance documents |
| 2026-03-29 | Milestone tracker adopted for relative-week schedule governance |
| 2026-03-30 | Added scope baseline document and Build Start Sign-off Package minimum condition |
| 2026-04-06 | Updated current delivery mode after Gate A Pass approval and execution-ready transition |
