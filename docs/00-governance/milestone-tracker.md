# FPDS Milestone Tracker

Version: 1.0  
Date: 2026-03-29  
Status: Active  
Source Documents:
- `docs/01-planning/WBS.md`
- `docs/00-governance/roadmap.md`
- `docs/00-governance/stage-gate-checklist.md`
- `docs/00-governance/working-agreement.md`
- `docs/00-governance/decision-log.md`

---

## 1. Purpose

이 문서는 FPDS의 milestone tracking 체계, 책임자, due date 기준을 정의한다.

목적:
- WBS와 roadmap의 주요 마일스톤을 한 장에서 추적한다.
- 현재 단계에서 절대 날짜가 아니라 상대 주차 기준으로도 일정 통제가 가능하게 한다.
- 각 milestone마다 owner, exit criteria, evidence, next review를 명확히 둔다.
- gate review와 milestone review가 같은 기준을 사용하게 한다.

---

## 2. Tracking Rules

1. milestone 기준 문서는 `docs/00-governance/roadmap.md`와 `docs/01-planning/WBS.md`다.
2. 현재는 공식 build start date가 확정되지 않았으므로 due date는 `relative week` 기준으로 관리한다.
3. 절대 날짜는 Gate A 직전 또는 Product Owner가 개발 시작일을 확정하는 시점에 추가한다.
4. milestone 상태는 `Not Started`, `In Progress`, `At Risk`, `Done`으로 관리한다.
5. milestone이 `At Risk`가 되면 RAID log와 함께 본다.
6. gate가 필요한 milestone은 gate note가 evidence에 포함되어야 한다.
7. 매 milestone 갱신 시 roadmap 진행률과 WBS 상태를 함께 점검한다.

---

## 3. Due Date Convention

현재 문서 단계의 due date 해석:

- `Target Week`는 공식 프로젝트 시계 기준 상대 주차다.
- `Week 0`은 Product Owner가 승인한 공식 실행 시작 주다.
- 현재는 설계 마감 단계이므로 Stage 0의 남은 일정을 기준으로 마일스톤을 추적한다.
- 절대 날짜 칼럼은 비워두거나 `TBD`로 두고, 공식 시작일 확정 후 채운다.

---

## 4. Milestone Board

| Milestone | Stage | Status | Owner | Target Week | Calendar Due | Gate | Key Exit Criteria | Evidence Required |
|---|---|---|---|---|---|---|---|---|
| M0 | Detailed Design Closure | In Progress | Product Owner, Tech Lead | Week 3 | TBD | Gate A | open gate blockers closed, core design package ready | gate review note, updated WBS, updated roadmap |
| M1 | Foundation Setup Complete | Not Started | Tech Lead | Week 5 | TBD | - | repo/app/db/auth/i18n/ops baseline ready | foundation checklist, environment notes |
| M2 | Prototype Acceptance | Not Started | Tech Lead, QA | Week 8 | TBD | Gate B | TD Savings end-to-end feasibility proven | prototype demo, findings memo, evidence pack |
| M3 | Admin/Ops Core Complete | Not Started | Product Owner, Tech Lead | Week 11 | TBD | Gate C | internal review/trace/run/usage workflows operational | admin demo, QA summary |
| M4 | Canada Public Experience Complete | Not Started | Product Owner, Frontend, Backend | Week 15 | TBD | - | Big 5 public catalog and dashboard usable | public demo, metric validation note |
| M5 | Phase 1 Release Readiness | Not Started | Product Owner | Week 18 | TBD | Gate D | publish, security, runbook, release evidence ready | release checklist, acceptance pack |
| M6 | Japan Expansion Setup Complete | Not Started | Product Owner, Tech Lead | Week 22 | TBD | - | Japan source/taxonomy/parsing base ready | Japan scope memo, schema/taxonomy note |
| M7 | External API Delivery Complete | Not Started | Product Owner, Backend | Week 26 | TBD | - | external API v1 usable with auth/docs/monitoring | API docs, monitoring note, demo |
| M8 | Phase 2 Acceptance | Not Started | Product Owner | Week 28 | TBD | - | Japan + API scope accepted | acceptance evidence pack |

---

## 5. Milestone Review Checklist

각 review에서 아래 항목을 확인한다.

- status가 이전 review 대비 어떻게 바뀌었는가
- target week를 지킬 수 있는가
- blocker가 무엇인가
- 어떤 WBS task가 milestone을 막고 있는가
- 어떤 문서가 최신 상태여야 하는가
- evidence가 준비되었는가
- escalation이 필요한가

---

## 6. Update Cadence

| Review Type | Frequency | What Updates |
|---|---|---|
| Steering / PO Sync | Weekly | milestone status, due risk, owner actions |
| Delivery Sync | Twice weekly | blocked items, current stage progress, next milestone readiness |
| Gate Review | At gate boundary | pass/fail/deferred, evidence, follow-up actions |
| WBS Update | On task completion | task status, milestone impact, roadmap snapshot |

---

## 7. Escalation Triggers

아래 중 하나가 발생하면 milestone을 `At Risk`로 바꾼다.

- 핵심 dependency가 닫히지 않는다.
- gate blocking item이 남아 있다.
- target week 안에 끝나기 어려운 open decision이 남아 있다.
- staffing 또는 reviewer availability 가정이 깨진다.
- 보안/데이터/acceptance 기준이 미확정으로 남아 있다.

---

## 8. Review Note Template

```md
Milestone:
Review Date:
Status:
Owner:
Target Week:
Current Risks:
Blocking WBS:
Evidence Available:
Next Action:
Escalation Needed:
```

---

## 9. Definition of Done for WBS 0.6

`WBS 0.6 milestone tracking 체계 확정`은 아래 조건을 충족하면 완료로 본다.

- milestone board가 존재한다.
- 각 milestone의 owner와 target due convention이 정의되어 있다.
- relative week 기준 due date 방식이 정리되어 있다.
- review cadence와 escalation trigger가 정리되어 있다.
- WBS/roadmap/gate 운영과 연결되는 추적 규칙이 포함되어 있다.

---

## 10. Change History

| Date | Change |
|---|---|
| 2026-03-29 | Initial milestone tracker created |
