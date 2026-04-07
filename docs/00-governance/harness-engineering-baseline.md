# FPDS Harness Engineering Baseline

Version: 1.0
Date: 2026-04-07
Status: Active
Source Documents:
- `docs/00-governance/working-agreement.md`
- `docs/00-governance/stage-gate-checklist.md`
- `docs/00-governance/decision-log.md`
- `docs/01-planning/WBS.md`
- `docs/01-planning/prototype-backlog.md`
- `docs/02-requirements/scope-baseline.md`
- `docs/02-requirements/FPDS_Requirements_Definition_v1_5.md`

---

## 1. Purpose

이 문서는 WBS 2와 WBS 3 착수 전에 먼저 깔아 두는 repository harness 기준을 고정한다.

목적:
- 구현 시작 전에도 작업 방식, 자동 검증, 문서 정합성 점검 기준을 갖춘다.
- Product Owner가 흐름을 따라가기 쉬운 작은 slice 방식과 자동 점검 기준을 연결한다.
- product implementation과 harness work를 구분해 build hold rule을 깨지 않도록 한다.

이 문서는 제품 기능 구현 승인 문서가 아니다.
현재 범위는 repository harness와 workflow guardrail에 한정한다.

---

## 2. Baseline Decisions

1. `AGENTS.md`는 60줄 이하의 항상 적용되는 규칙만 둔다.
2. pre-commit hook은 `staged files only`를 기준으로 동작한다.
3. pre-commit hook은 low-risk text hygiene만 자동 수정하고, 성공 시 조용히 끝난다.
4. cleanup audit는 `report-only`로 시작하며 자동 삭제/자동 리팩터링을 수행하지 않는다.
5. repository-wide 검증은 CI에서 수행한다.
6. harness는 product code implementation을 시작하지 않는다.

---

## 3. Harness Scope

포함:
- `AGENTS.md`
- root `README.md`
- development journal
- Git hook entrypoint와 install script
- staged-only pre-commit checks
- repo doctor
- report-only cleanup audit
- CI workflow for harness checks

비포함:
- app/api/worker 기능 구현
- parser, DB, API, UI, BX-PF connector 구현
- cleanup auto-delete
- agent-driven autonomous refactor loop

---

## 4. Hook Model

### 4.1 Pre-Commit

현재 pre-commit은 아래만 수행한다.

- staged text file trailing whitespace / final newline 자동 보정
- staged Markdown local reference 검증
- staged PowerShell syntax 검증

원칙:
- 성공은 조용히 끝난다.
- 실패 시에만 commit을 막고 메시지를 보여준다.
- staged 범위를 넘어 repository 전체를 검사하지 않는다.

### 4.2 CI

CI는 repository-wide로 아래를 수행한다.

- required harness file 존재 여부 확인
- Markdown reference 검증
- PowerShell syntax 검증
- future package script 감지 시 `lint`, `typecheck`, `test`, `build` 실행
- cleanup audit report 생성

---

## 5. Cleanup Audit Model

cleanup audit는 report-only다.

점검 항목:
- broken local doc references
- trailing whitespace
- required harness file 누락
- TODO/FIXME/HACK marker

후속 확장 가능 항목:
- unused code/import/export
- unused env key
- dependency vulnerability report
- docs-vs-code drift checks

위 항목은 product code가 생긴 뒤에 단계적으로 추가한다.

---

## 6. Development Journal Model

부분 완료가 생길 때마다 `development-journal.md`에 slice summary를 남긴다.

기록 목적:
- 다음 Codex 세션이 코드 전체를 다시 읽지 않고도 최근 구현 의도와 상태를 빠르게 파악한다.
- Product Owner가 각 slice의 결과, 검증, 남은 리스크를 문서로 추적한다.
- handoff가 chat history가 아니라 repo 문서 기준으로 이어지게 만든다.

각 entry에는 최소 아래를 남긴다.

- slice name and date
- 목표와 왜 이 작업을 먼저 했는지
- 실제로 바뀐 사용자/운영 동작
- 변경한 주요 파일 또는 모듈
- 핵심 설계 판단 또는 새 제약
- 실행/검증한 명령
- 아직 남아 있는 known issue, follow-up, next natural step

제외 원칙:
- 장황한 코드 설명
- commit diff 전체 복붙
- chat transcript 의존 설명

---

## 7. File Map

| Path | Role |
|---|---|
| `AGENTS.md` | agent operating rules |
| `README.md` | repository entrypoint |
| `docs/00-governance/development-journal.md` | implementation memory and resume log |
| `.githooks/pre-commit` | Git hook entrypoint |
| `scripts/harness/install-hooks.ps1` | local hook install |
| `scripts/harness/pre-commit.ps1` | staged-only hook logic |
| `scripts/harness/repo-doctor.ps1` | repository health gate |
| `scripts/harness/cleanup-audit.ps1` | report-only cleanup audit |
| `scripts/harness/invoke-project-checks.ps1` | future package-script checks |
| `.github/workflows/harness.yml` | CI baseline |

---

## 8. Operating Notes

- local 시작 시 `powershell -NoLogo -NoProfile -ExecutionPolicy Bypass -File scripts/harness/install-hooks.ps1`로 hooks를 연결한다.
- docs map은 `docs/README.md`를 기준으로 유지한다.
- WBS 2 foundation가 시작되면 package manager와 framework가 정해지는 시점에 project checks를 강화한다.
- cleanup audit가 실제 수정까지 하려면 Product Owner 승인을 다시 받는다.
- 의미 있는 구현 slice가 끝나면 `development-journal.md`를 같은 turn 안에서 함께 갱신한다.

---

## 9. Change History

| Date | Change |
|---|---|
| 2026-04-07 | Initial harness engineering baseline created |
| 2026-04-07 | Added development journal rule for resume-friendly slice summaries |
