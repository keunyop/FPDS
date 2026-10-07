---
name: fpds-admin-verification
description: FPDS Admin 변경의 영향별 회귀·문서 검사와 개발 인계 결과를 확인할 때 사용한다. local 테스트, 실제 배포, canonical/Public 결과와 의뢰자 UAT를 구분해 수행한 증거만 보고한다.
---

# FPDS Admin 검증과 개발 인계

## 변경 범위부터 확인

경로는 FPDS repository root 기준이다. AGENTS.md와 root README → docs/00-governance/development-journal.md → docs/README.md를 읽고 기존 git status/diff와 goal ownership을 확인한다. changed runtime README로 현재 명령을 확인한다. 이미 수행된 테스트는 코드 변경이나 unresolved failure가 없으면 불필요하게 반복하지 않는다.

각 acceptance에 연결되는 행동과 check를 선정한다. 문구·링크 편집에 금융/provider/API 전체 실행을 요구하지 않는다. UI/API/Worker/DB 변경에는 영향을 입증하는 behavior test가 필요하며 build/typecheck만으로 통과시키지 않는다.

## 영향별 검증

- UI: relevant Admin tests, typecheck/test/build. layout 변경은 EN/KO/JA × 390px/768px/1440px, loading/empty/error/permission/retry, keyboard/focus와 real-data 상태를 확인한다.
- API: 독립 api/service 환경의 성공/거부/국가/CSRF 회귀. Worker dependency가 우연히 API import 결함을 가리지 않게 한다.
- Worker/금융: source-backed success/boundary/failure, exact types/units/complete conditions/current origin, optional omission과 essential exclusion. 관련 promotion와 Public eligibility를 확인한다.
- DB: SQL/persistence 계약 검토와 승인된 격리 PostgreSQL의 migration/schema/constraint/transaction 확인. mock과 actual writes를 구분한다.
- docs/skills: local reference, UTF-8, frontmatter와 이름/적용 범위, 호출 예시와 source path/command 정합을 확인한다.

root 기준 명령:

```powershell
pnpm --dir app/admin run typecheck
pnpm --dir app/admin run test
pnpm --dir app/admin run build
uv run --directory api/service python -m unittest discover -s tests -p "test_*.py"
uv run python -m unittest discover -s worker -p "test_*.py"
git diff --check
```

문서 검사에는 scripts/harness/repo-doctor.ps1, validate-foundation-baseline.ps1, cleanup-audit.ps1를 사용한다. PowerShell 실행 정책은 root README의 명시적 Bypass 호출을 따른다. CI/harness 변경이면 docs/00-governance/harness-engineering-baseline.md를 읽는다.

full invoke-foundation-checks.ps1은 dependency 설치/build를 포함할 수 있다. active collecting workspace에서 실행하지 않고 격리 clone을 쓴다. cleanup-audit는 report-only이며 자동 삭제하지 않는다.

## 실패와 증거 범위

현재 변경으로 생긴 실패, 기존 결함, 환경 문제, 미수행을 구분한다. ignored tmp 복사본의 link 실패는 경로/영향을 기록하고 shared.ps1의 Get-MarkdownReferenceFindings로 changed docs도 검사한다. 전역 실패를 성공으로 표시하거나 관련 없는 tmp/user changes를 삭제하지 않는다. source fixture hash 실패는 원문 provenance를 조사하고 기대 hash를 교체해 통과시키지 않는다.

local fixture/replay passes, serving health/process version, live ordinary Run, canonical version, aggregate projection, Public list/detail readback은 각각 별도 사실이다. 의뢰자 clean-clone/restore/UAT/GO도 별도 gate다. 검증할 권한이 없는 단계는 미수행과 owner/다음 action을 명시한다.

## 인계 산출물

실제 변경된 workflow/contract/status 문서와 docs/00-governance/development-journal.md를 갱신한다. 일지는 outcome/key files/decision/실행 검증/known issues/next step만 기록한다.

최종 diff와 goal을 다시 읽고 모든 acceptance를 확인한다. 이번 slice가 끝나도 타 ownership이 남으면 goal 파일을 보존한다. 보고에는 무엇이 바뀌었는지, 왜 필요한지, 실제 test 결과와 material limitation을 적는다. production/go-live/계정 이전을 코드 준비 완료로 대신 승인하지 않는다.
