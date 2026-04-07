# FPDS Development Journal

Version: 1.0
Date: 2026-04-07
Status: Active
Source Documents:
- `docs/00-governance/working-agreement.md`
- `docs/00-governance/harness-engineering-baseline.md`
- `docs/01-planning/WBS.md`
- `docs/02-requirements/scope-baseline.md`

---

## 1. Purpose

이 문서는 구현이 시작된 뒤 각 개발 slice의 핵심 내용을 짧게 남기는 repository memory다.

목적:
- 다음 Codex 세션이 코드 전체를 다시 읽지 않고도 최근 변경의 맥락을 빠르게 파악한다.
- Product Owner가 부분 완료 단위로 결과, 검증, 남은 리스크를 문서 기준으로 확인한다.
- chat history가 아니라 repo 문서만으로 handoff가 가능하게 만든다.

이 문서는 changelog가 아니다.
`무엇이 왜 바뀌었고, 어디까지 검증됐고, 다음에 어디서 이어야 하는지`를 남기는 용도다.

---

## 2. When To Update

아래 중 하나가 끝나면 entry를 추가한다.

- 의미 있는 WBS subtask 1개 이상 완료
- 사용자 또는 운영자가 체감하는 동작 변경 완료
- schema, workflow, config, deployment 방식처럼 재진입에 중요한 판단 반영
- 다음 slice가 이전 slice의 결과를 전제로 하게 되는 시점

아래는 entry 없이 지나가도 된다.

- 오타만 고친 문서 수정
- purely mechanical rename
- 실패 후 완전히 롤백된 실험

---

## 3. What Must Be Recorded

각 entry에는 최소 아래를 남긴다.

### 3.1 Identity

- date
- slice id or short title
- related WBS
- status: done / partial / blocked

### 3.2 Why

- 이번 slice의 목표
- 왜 지금 이 작업을 했는지

### 3.3 Outcome

- 실제로 바뀐 동작
- 이번 slice에서 의도적으로 하지 않은 것

### 3.4 Code Surface

- 핵심 변경 파일
- 새로 생긴 command, env key, route, table, script, workflow가 있으면 기록

### 3.5 Decisions and Constraints

- 구현하면서 확정한 local decision
- 다음 작업자가 반드시 알아야 하는 제약
- 임시 처리라면 why와 removal condition

### 3.6 Verification

- 실행한 command
- 통과/실패 결과
- 검증하지 못한 항목이 있으면 이유

### 3.7 Handoff

- known issues
- follow-up candidates
- next natural step 하나

---

## 4. Writing Rules

- 짧고 밀도 높게 쓴다.
- 코드 전체 설명 대신 resume에 필요한 판단만 남긴다.
- 파일 목록은 핵심 파일만 적는다.
- 명령은 실제로 실행한 것만 적는다.
- 추측과 사실을 섞지 않는다.
- 다음 세션이 바로 시작할 수 있게 마지막 줄에 next step을 남긴다.

---

## 5. Entry Template

```md
## YYYY-MM-DD - Slice Title

- WBS: `x.y`
- Status: `done | partial | blocked`
- Goal: 한 줄 목표
- Why now: 왜 이 순서였는지
- Outcome: 사용자/운영 관점에서 실제로 바뀐 점
- Not done: 이번 slice에서 의도적으로 남긴 범위
- Key files: `path/a`, `path/b`
- Decisions: 다음 작업자가 알아야 할 판단과 제약
- Verification:
  - `command`
  - result
- Known issues: 남아 있는 문제나 리스크
- Next step: 바로 이어서 할 1개 작업
```

---

## 6. Entries

아직 product implementation entry는 없다.
하네스 작업은 [docs/00-governance/harness-engineering-baseline.md](docs/00-governance/harness-engineering-baseline.md)에 기록하고, 이후 실제 WBS 2/WBS 3 구현부터 이 저널에 누적한다.

---

## 7. Change History

| Date | Change |
|---|---|
| 2026-04-07 | Initial development journal created |
