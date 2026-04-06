# Prototype Backlog Baseline

Version: 1.0  
Date: 2026-04-06  
Status: Approved Baseline for WBS 1.8.2  
Source Documents:
- `docs/01-planning/WBS.md`
- `docs/01-planning/plan.md`
- `docs/01-planning/td-savings-source-inventory.md`
- `docs/02-requirements/scope-baseline.md`
- `docs/03-design/workflow-state-ingestion-design.md`
- `docs/03-design/domain-model-canonical-schema.md`
- `docs/00-governance/stage-gate-checklist.md`
- `docs/00-governance/decision-log.md`

---

## 1. Purpose

이 문서는 Prototype build 착수 전, `TD Savings` 범위의 구현 backlog를 user story와 task 단위로 공식 분해한다.

목적:
- `1.8.3 acceptance`, `1.8.4 spike`, `1.8.5 Sprint 0 board`가 같은 작업 단위를 참조하도록 맞춘다.
- Prototype에 필요한 최소 foundation과 end-to-end pipeline 작업을 한 문서에서 우선순위화한다.
- Gate B 통과에 직접 필요한 작업과 Prototype 이후로 미뤄도 되는 작업을 분리한다.
- Product Owner의 명시적 build 승인 전까지 구현 범위를 임의 확장하지 않도록 기준선을 고정한다.

이 문서는 구현 시작 승인을 의미하지 않는다.  
실제 개발 시작은 `Gate A = Pass + Product Owner explicit approval` 이후에만 가능하다.

---

## 2. Backlog Baseline

### 2.1 Backlog Goal

Prototype backlog의 목표는 아래 4가지를 만족하는 것이다.

1. `TD Savings` source set으로 최소 1회 end-to-end run이 가능하다.
2. 핵심 savings field가 evidence linkage와 함께 review 가능한 형태로 남는다.
3. 운영자가 read-only `basic internal result viewer`에서 결과를 확인할 수 있다.
4. Prototype findings memo로 Big 5 확장 가능성과 주요 기술 리스크를 설명할 수 있다.

### 2.2 Included Work

- Prototype에 필요한 minimum foundation
- TD source discovery, snapshot, parse, chunk, extraction, normalization, validation
- Prototype 전량 review routing
- read-only internal result viewer
- first successful run evidence pack
- prototype findings memo

### 2.3 Explicitly Deferred Work

- admin login
- full review queue 운영화
- change history 운영 화면
- BX-PF actual publish flow
- public product grid / dashboard
- EN/KO/JA locale 적용
- Big 5 확장

---

## 3. Prioritization Rules

### 3.1 Priority Labels

| Priority | Meaning | Gate Impact |
|---|---|---|
| `P0` | Gate B와 first successful run에 직접 필요한 작업 | 미완료 시 Prototype acceptance 불가 |
| `P1` | Prototype 품질과 재현성을 높이지만 first run 직전 필수는 아님 | Gate B 직전 또는 직후 보강 가능 |
| `Deferred` | Prototype 공식 범위 밖 작업 | Phase 1 또는 후속 WBS로 이동 |

### 3.2 Slicing Principles

1. source inventory 기준 `P0 seed source`를 먼저 처리한다.
2. stage 순서는 `discovery -> snapshot -> parse/chunk -> extraction -> normalization -> validation -> viewer -> run evidence`를 따른다.
3. 가장 위험한 slice인 `TD Growth Savings`, `governing PDF`, `current rates page`를 early risk retirement 대상으로 둔다.
4. Prototype은 feasibility가 목적이므로 production-grade automation보다 evidence trace와 reviewability를 우선한다.
5. 한 story는 데모 가능한 결과를 남겨야 하며, 미완료 task는 story split 또는 defer로 처리한다.

---

## 4. Backlog Lanes

| Lane | Goal | Included WBS | Priority |
|---|---|---|---|
| Lane A. Foundation Minimum | prototype 실행에 필요한 최소 환경과 저장 경로 준비 | `2.1`, `2.2`, `2.3`, `2.4`, `2.7`, `2.8`, `2.10` | P0 |
| Lane B. Source Ingestion Core | TD source를 수집해 normalized candidate까지 만든다 | `3.1` ~ `3.7` | P0 |
| Lane C. Reviewability Surface | operator가 결과와 evidence를 읽기 전용으로 확인한다 | `2.9`, `3.8` | P0 |
| Lane D. Demo and Learning Closure | first successful run, evidence pack, findings memo를 남긴다 | `3.9`, `3.10` | P0 |
| Lane E. Nice-to-Have Hardening | 재현성/운영 편의를 보강한다 | prototype 범위 내 추가 보강 | P1 |

---

## 5. User Story Backlog

| Story ID | Priority | User Story | Key Output | Implementing Owner | WBS Mapping |
|---|---|---|---|---|---|
| `PB-01` | P0 | As the team, we need a minimum prototype runtime so that TD sources can be fetched, stored, and replayed in a controlled way. | prototype-ready foundation baseline | Tech Lead, Backend, DevOps | `2.1`, `2.2`, `2.3`, `2.4`, `2.7`, `2.8`, `2.10` |
| `PB-02` | P0 | As an AI/Data engineer, I need a TD source registry and discovery flow so that the allowed HTML/PDF source set is reproducible. | discovered TD source set with metadata | AI/Data | `3.1` |
| `PB-03` | P0 | As an AI/Data engineer, I need HTML/PDF snapshot capture so that raw evidence can be preserved and retried safely. | raw snapshots + fetch metadata | AI/Data | `3.2` |
| `PB-04` | P0 | As the pipeline, I need parsed text and chunked evidence so that extraction can cite the source. | parsed documents + chunk metadata | AI/Data | `3.3`, `3.4` |
| `PB-05` | P0 | As the pipeline, I need extraction, normalization, validation, and forced review routing so that savings candidates become reviewable output. | normalized candidates + validation result + review status | AI/Data, Backend | `3.5`, `3.6`, `3.7` |
| `PB-06` | P0 | As an operator, I need a read-only internal viewer so that I can inspect prototype run results and evidence links. | basic internal result viewer | Frontend, Backend | `2.9`, `3.8` |
| `PB-07` | P0 | As the team, we need one successful end-to-end run with evidence artifacts so that Gate B feasibility can be demonstrated. | first successful run evidence pack | QA, Tech Lead, AI/Data | `3.9` |
| `PB-08` | P0 | As the team, we need a prototype findings memo so that we can explain Big 5 expansion readiness and open risks. | findings memo | Tech Lead | `3.10` |
| `PB-09` | P1 | As the team, we want lightweight replay and observability support so that prototype reruns are easier to diagnose. | rerun notes, error summary, repeatability checklist | Tech Lead, AI/Data, Backend | prototype hardening |

---

## 6. Task List by Story

### 6.1 `PB-01` Prototype Runtime Minimum

| Task ID | Priority | Task | Owner | Dependency |
|---|---|---|---|---|
| `T-01-01` | P0 | repo/app/worker/shared 기본 구조를 준비한다. | Tech Lead | `2.1` |
| `T-01-02` | P0 | dev/prod env template과 minimum config shape를 정리한다. | DevOps | `2.2` |
| `T-01-03` | P0 | prototype에 필요한 DB baseline과 migration skeleton을 준비한다. | Backend | `2.3` |
| `T-01-04` | P0 | snapshot/chunk 저장용 object storage path와 naming baseline을 준비한다. | DevOps | `2.4` |
| `T-01-05` | P0 | monitoring/error tracking minimum hook를 준비한다. | DevOps | `2.7` |
| `T-01-06` | P0 | crawler/storage/API 경계에 필요한 minimum security baseline을 적용한다. | Security, DevOps | `2.8` |
| `T-01-07` | P0 | lint/typecheck/build/test 기본 파이프라인을 준비한다. | DevOps | `2.10` |

Story complete when:
- source fetch와 snapshot 저장을 시도할 수 있는 최소 환경이 준비된다.
- prototype runtime에 필요한 저장 경로와 config shape가 문서/코드 기준으로 정리된다.

### 6.2 `PB-02` TD Source Registry and Discovery

| Task ID | Priority | Task | Owner | Dependency |
|---|---|---|---|---|
| `T-02-01` | P0 | `td-savings-source-inventory` 기준 12개 source를 registry seed로 등록한다. | AI/Data | `1.8.1` |
| `T-02-02` | P0 | `TD-SAV-001`을 entry page로 사용하는 discovery 규칙을 구현한다. | AI/Data | `T-02-01` |
| `T-02-03` | P0 | normalized URL + source type 기준 dedupe와 source identity 계산을 구현한다. | AI/Data | `T-02-02` |
| `T-02-04` | P0 | registry 밖 링크, cross-domain link, compare/authenticated flow를 warning으로 분류한다. | AI/Data | `T-02-02` |
| `T-02-05` | P1 | source priority(`P0`/`P1`)와 source language metadata를 discovery output에 포함한다. | AI/Data | `T-02-03` |

Story complete when:
- run initialization 시 prototype 대상 source set이 재현 가능하게 확정된다.
- 허용/비허용 source 경계가 warning과 함께 구분된다.

### 6.3 `PB-03` Snapshot Capture

| Task ID | Priority | Task | Owner | Dependency |
|---|---|---|---|---|
| `T-03-01` | P0 | HTML/PDF fetch를 수행하고 raw snapshot을 object storage에 저장한다. | AI/Data | `PB-01`, `PB-02` |
| `T-03-02` | P0 | content type, checksum/fingerprint, fetch timestamp, status metadata를 기록한다. | AI/Data | `T-03-01` |
| `T-03-03` | P0 | source 단위 retry와 partial failure 누적 규칙을 적용한다. | AI/Data | `T-03-02` |
| `T-03-04` | P1 | fingerprint 동일 시 snapshot 재사용 정책을 적용한다. | AI/Data | `T-03-02` |

Story complete when:
- `TD-SAV-002`, `TD-SAV-004`, `TD-SAV-007`, `TD-SAV-008` snapshot이 우선 저장된다.
- snapshot 실패와 partial completion이 run 단위로 설명 가능하다.

### 6.4 `PB-04` Parse, Chunk, and Evidence Registration

| Task ID | Priority | Task | Owner | Dependency |
|---|---|---|---|---|
| `T-04-01` | P0 | HTML snapshot을 parsed text로 변환한다. | AI/Data | `PB-03` |
| `T-04-02` | P0 | PDF snapshot을 parsed text로 변환한다. | AI/Data | `PB-03` |
| `T-04-03` | P0 | section/page anchor가 포함된 retrieval-ready chunk를 생성한다. | AI/Data | `T-04-01`, `T-04-02` |
| `T-04-04` | P0 | chunk metadata와 source document linkage를 저장한다. | AI/Data, Backend | `T-04-03` |
| `T-04-05` | P1 | parse quality note와 partial parse flag를 남긴다. | AI/Data | `T-04-02` |

Story complete when:
- extraction 단계가 source excerpt와 위치 정보를 참조할 수 있다.
- HTML/PDF 모두 최소 1개 이상 evidence chunk를 남긴다.

### 6.5 `PB-05` Extraction, Normalization, Validation, Review Routing

| Task ID | Priority | Task | Owner | Dependency |
|---|---|---|---|---|
| `T-05-01` | P0 | savings 핵심 field extraction을 구현한다. | AI/Data | `PB-04` |
| `T-05-02` | P0 | `TD Growth Savings`의 boosted-rate eligibility를 special-case note/evidence로 보존한다. | AI/Data | `T-05-01` |
| `T-05-03` | P0 | extracted draft를 canonical schema v1의 `normalized_candidate`로 매핑한다. | Backend, AI/Data | `T-05-01` |
| `T-05-04` | P0 | field-level validation rule과 issue code를 적용한다. | Backend | `T-05-03` |
| `T-05-05` | P0 | Prototype 전량 review routing 규칙을 적용한다. | Backend, AI/Data | `T-05-04` |
| `T-05-06` | P1 | source confidence와 citation confidence를 함께 남긴다. | AI/Data, Backend | `T-05-04` |

Story complete when:
- candidate가 `reviewable output`으로 남고, 핵심 field는 evidence excerpt와 연결된다.
- validation issue와 partial failure reason이 operator에게 설명 가능하다.

### 6.6 `PB-06` Basic Internal Result Viewer

| Task ID | Priority | Task | Owner | Dependency |
|---|---|---|---|---|
| `T-06-01` | P0 | prototype read-only route skeleton을 준비한다. | Frontend | `2.9`, `PB-01` |
| `T-06-02` | P0 | run 기준 결과 목록에서 bank, product name, product type, validation status를 보여준다. | Frontend, Backend | `T-06-01`, `PB-05` |
| `T-06-03` | P0 | selected candidate에서 핵심 field와 evidence excerpt를 보여준다. | Frontend, Backend | `T-06-02` |
| `T-06-04` | P0 | source URL, source type, run id, partial failure/warning 요약을 보여준다. | Frontend, Backend | `T-06-02` |
| `T-06-05` | P1 | rerun 비교 또는 raw trace deep link를 위한 placeholder를 둔다. | Frontend | `T-06-03` |

Story complete when:
- operator가 Prototype 결과를 read-only로 검토할 수 있다.
- full admin console 없이도 evidence-linked candidate 판단이 가능하다.

### 6.7 `PB-07` First Successful Run and Evidence Pack

| Task ID | Priority | Task | Owner | Dependency |
|---|---|---|---|---|
| `T-07-01` | P0 | P0 seed source 기준 첫 end-to-end run을 실행한다. | AI/Data, QA | `PB-01` ~ `PB-06` |
| `T-07-02` | P0 | 성공/실패 source, validation issue, reviewable candidate 수를 기록한다. | QA, AI/Data | `T-07-01` |
| `T-07-03` | P0 | sample evidence linkage, run summary, screenshot 또는 equivalent 증빙을 evidence pack으로 묶는다. | QA, Tech Lead | `T-07-02` |
| `T-07-04` | P1 | rerun 1회 이상으로 재현성을 점검한다. | QA, AI/Data | `T-07-03` |

Story complete when:
- Gate B에 제출 가능한 최소 prototype evidence pack이 남는다.
- first successful run이 문서와 artifact 기준으로 재설명 가능하다.

### 6.8 `PB-08` Findings Memo and Expansion Recommendation

| Task ID | Priority | Task | Owner | Dependency |
|---|---|---|---|---|
| `T-08-01` | P0 | source coverage, parse quality, extraction quality, reviewability 결과를 정리한다. | Tech Lead | `PB-07` |
| `T-08-02` | P0 | `TD Growth Savings`, PDF parsing, current rate drift 리스크에 대한 대응 방향을 정리한다. | Tech Lead, AI/Data | `T-08-01` |
| `T-08-03` | P0 | Big 5 확장 전 필요한 추가 설계/구현 항목을 제안한다. | Tech Lead | `T-08-01` |

Story complete when:
- Prototype 결과가 단순 성공 보고가 아니라 다음 단계 의사결정 입력으로 정리된다.

### 6.9 `PB-09` Lightweight Hardening

| Task ID | Priority | Task | Owner | Dependency |
|---|---|---|---|---|
| `T-09-01` | P1 | rerun checklist와 common failure triage note를 정리한다. | Tech Lead, QA | `PB-07` |
| `T-09-02` | P1 | prototype error summary와 warning taxonomy를 정리한다. | AI/Data, Backend | `PB-07` |
| `T-09-03` | P1 | source-by-source known issue list를 유지한다. | AI/Data | `PB-08` |

---

## 7. Recommended Execution Sequence

### Wave 1. Build Start Minimum

- `PB-01`
- `PB-02`

### Wave 2. Core Evidence Pipeline

- `PB-03`
- `PB-04`

### Wave 3. Reviewable Candidate

- `PB-05`
- `PB-06`

### Wave 4. Gate B Closure

- `PB-07`
- `PB-08`

### Wave 5. Optional Hardening

- `PB-09`

---

## 8. Source-Driven Story Focus

Prototype backlog는 모든 source를 동시에 깊게 처리하지 않고 아래 순서로 위험을 줄인다.

| Focus Order | Source IDs | Why First |
|---|---|---|
| F1 | `TD-SAV-002` | 단일 HTML detail로 discovery-snapshot-parse 기본 경로를 가장 빨리 검증 가능 |
| F2 | `TD-SAV-007`, `TD-SAV-008` | governing PDF parsing과 evidence anchor 난이도를 조기에 검증해야 함 |
| F3 | `TD-SAV-004` | boosted-rate cross-product logic이 가장 까다로운 savings case |
| F4 | `TD-SAV-005`, `TD-SAV-006` | current value reconciliation과 dynamic drift 대응 필요 |
| F5 | `TD-SAV-001`, `TD-SAV-003`, `TD-SAV-009`~`012` | seed completeness와 supporting evidence 보강 |

---

## 9. Prototype Out-of-Scope Guardrails

아래 작업은 backlog에 넣지 않는다.

- auth/session login flow
- review action UI
- change history screen
- BX-PF connector
- publish monitor
- usage dashboard
- public grid / dashboard
- locale resource wiring
- Japan/API work

backlog 추가 요청이 위 범위를 넘으면 change control 대상으로 본다.

---

## 10. WBS Mapping

| WBS | This Document Coverage |
|---|---|
| `1.8.2` | Sections 2-9 |
| `1.8.3` | `docs/01-planning/prototype-acceptance-checklist.md` 입력으로 Sections 2, 3, 5, 7, 9 사용 |
| `1.8.4` | `docs/01-planning/prototype-spike-scope.md` 입력으로 Sections 6, 8 사용 |
| `1.8.5` | `docs/01-planning/sprint-0-board.md` 입력으로 Sections 4-7 사용 |

---

## 11. Change History

| Date | Change |
|---|---|
| 2026-04-06 | Initial prototype backlog baseline created for WBS 1.8.2 |
