# Sprint 0 Ready Board

Version: 1.0
Date: 2026-04-06
Status: Approved Baseline for WBS 1.8.5
Source Documents:
- `docs/01-planning/WBS.md`
- `docs/01-planning/plan.md`
- `docs/archive/01-planning/prototype-backlog.md`
- `docs/archive/01-planning/prototype-acceptance-checklist.md`
- `docs/archive/01-planning/prototype-spike-scope.md`
- `docs/00-governance/stage-gate-checklist.md`
- `docs/00-governance/milestone-tracker.md`
- `docs/00-governance/decision-log.md`

---

## 1. Purpose

이 문서는 `개발 시작 승인 직전` 기준의 Sprint 0 작업판을 고정한다.

목적:
- Gate A 통과 직후 어떤 순서로 작업을 열지 미리 정리한다.
- 아직 구현 승인 전인 항목과, 승인 즉시 착수 가능한 항목을 분리한다.
- prototype backlog의 P0 lane이 실제 실행 순서로 이어지도록 만든다.

이 문서는 Gate A `Pass` 이후 바로 참고할 `ready board`다.
이 문서 자체는 구현 시작 보고가 아니며, 현재 시점의 `next execution queue`를 정리한 것이다.

---

## 2. Sprint 0 Goal

Sprint 0의 목표는 아래 3가지다.

1. Build Start Gate 직후 곧바로 착수할 P0 작업 순서를 고정한다.
2. foundation minimum과 prototype spike 준비가 서로 충돌하지 않게 묶는다.
3. Gate B에 필요한 earliest evidence path를 가장 짧게 연다.

---

## 3. Board Columns

| Column | Meaning |
|---|---|
| `Design Closed` | 문서 기준이 닫혀 실행 준비가 된 항목 |
| `Ready to Start` | Gate A `Pass` 이후 곧바로 열 수 있는 항목 |
| `Queued Next` | 선행 작업 후 바로 이어질 항목 |
| `Deferred` | Sprint 0 범위 밖 |

---

## 4. Sprint 0 Ticket Board

### 4.1 Design Closed

| Ticket | Source | Why It Is Ready |
|---|---|---|
| `S0-00` | `1.8.1` | TD Savings source inventory가 확정되어 source scope가 닫힘 |
| `S0-01` | `1.8.2` | prototype backlog baseline이 확정되어 story/task ordering이 닫힘 |
| `S0-02` | `1.8.3` | acceptance checklist가 확정되어 done definition이 닫힘 |
| `S0-03` | `1.8.4` | spike scope와 exit criteria가 확정되어 risk-first 검증 범위가 닫힘 |

### 4.2 Ready to Start

| Ticket | Priority | Task | Linked WBS | Owner | Done Definition |
|---|---|---|---|---|---|
| `S0-10` | P0 | repo/app/worker/shared 구조 준비 | `2.1` | Tech Lead | prototype code placement가 합의된 구조로 시작 가능 |
| `S0-11` | P0 | dev/prod env spec 및 template 준비 | `2.2` | DevOps | minimum config shape가 실행 가능 형태로 정리됨 |
| `S0-12` | P0 | DB baseline / migration skeleton 준비 | `2.3` | Backend | prototype candidate/run/source 저장 준비 완료 |
| `S0-13` | P0 | object storage/evidence bucket baseline 준비 | `2.4` | DevOps | snapshot/chunk 저장 경로 준비 완료 |
| `S0-14` | P0 | monitoring/error tracking minimum hook 준비 | `2.7` | DevOps | prototype 실패 원인 추적 가능 |
| `S0-15` | P0 | minimum security baseline 적용 | `2.8` | Security, DevOps | crawler/storage/API 경계의 baseline guardrail 적용 |
| `S0-16` | P0 | CI/CD baseline 준비 | `2.10` | DevOps | lint/typecheck/build/test 최소 파이프라인 준비 |
| `S0-17` | P0 | TD source registry seed 등록 및 discovery baseline 착수 | `3.1` | AI/Data | `TD-SAV-001`~`012` seed 기준 discovery 가능 |

### 4.3 Queued Next

| Ticket | Priority | Task | Linked WBS | Owner | Entry Condition |
|---|---|---|---|---|---|
| `S0-20` | P0 | HTML/PDF snapshot capture baseline | `3.2` | AI/Data | `S0-13`, `S0-17` 완료 |
| `S0-21` | P0 | parse/chunking baseline | `3.3` | AI/Data | `S0-20` 완료 |
| `S0-22` | P0 | evidence linkage structure baseline | `3.4` | AI/Data, Backend | `S0-21` 완료 |
| `S0-23` | P0 | extraction flow baseline | `3.5` | AI/Data | `S0-22` 완료 |
| `S0-24` | P0 | normalization mapping baseline | `3.6` | Backend, AI/Data | `S0-23` 완료 |
| `S0-25` | P0 | validation / forced review routing baseline | `3.7` | Backend, AI/Data | `S0-24` 완료 |
| `S0-26` | P0 | read-only internal viewer baseline | `2.9`, `3.8` | Frontend, Backend | `S0-25` 완료 |
| `S0-27` | P0 | first end-to-end run and evidence pack | `3.9` | QA, Tech Lead | `S0-26` 완료 |
| `S0-28` | P0 | findings memo 작성 | `3.10` | Tech Lead | `S0-27` 완료 |

### 4.4 Deferred

| Ticket Group | Deferred To |
|---|---|
| admin login / review queue / trace 운영화 | WBS `4.x` |
| publish monitor / BX-PF connector | WBS `6.x` |
| public grid / dashboard | WBS `5.x` |
| i18n locale wiring | WBS `5.12` |

---

## 5. Sprint 0 Execution Order

승인 직후 추천 순서는 아래와 같다.

1. `S0-10` ~ `S0-16`
2. `S0-17`
3. `S0-20` ~ `S0-22`
4. `S0-23` ~ `S0-26`
5. `S0-27` ~ `S0-28`

---

## 6. Spike Overlay on Sprint 0

Sprint 0 안에서 risk-first로 먼저 확인할 source는 아래다.

| Order | Source IDs | Why |
|---|---|---|
| 1 | `TD-SAV-002` | happy-path HTML baseline |
| 2 | `TD-SAV-007`, `TD-SAV-008` | PDF parse/evidence anchor risk |
| 3 | `TD-SAV-004` | boosted-rate special case |
| 4 | `TD-SAV-005` | current rate drift |

이 overlay는 `S0-20` ~ `S0-25` 구간에 적용한다.

---

## 7. Sprint 0 Exit Criteria

Sprint 0 준비가 끝났다고 보려면 아래가 충족되어야 한다.

- Gate A `Pass` 이후 착수 순서가 팀 기준으로 문서화되어 있다.
- acceptance done definition이 각 ticket의 결과 기준으로 연결되어 있다.
- spike target과 foundation minimum이 같은 board에서 충돌 없이 보인다.
- `Ready to Start`와 `Queued Next`가 구분되어 execution order가 흔들리지 않는다.

---

## 8. WBS Mapping

| WBS | This Document Coverage |
|---|---|
| `1.8.5` | Sections 2-7 |
| `1.8.6` | Build Start Gate review 입력으로 Sections 3-7 사용 |

---

## 9. Change History

| Date | Change |
|---|---|
| 2026-04-06 | Initial Sprint 0 ready board created for WBS 1.8.5 |
| 2026-04-06 | Updated board wording after Gate A Pass and clarified the ready-queue vs actual-start distinction |
