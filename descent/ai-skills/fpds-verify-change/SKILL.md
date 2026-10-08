---
name: fpds-verify-change
description: FPDS 인수 후 로컬라이징·기능 변경·수집 수정의 완료 조건을 검증하고 배포 준비 결과를 정리할 때 사용한다. 영향 영역의 실제 검사와 남은 적용·복구 작업을 확인한다.
---

# 변경 검증과 배포 준비

FPDS clone의 AGENTS.md와 descent/FPDS_Admin_개발_가이드.md를 읽고 git diff/goal/이미 실행한 결과를 확인한다. 경로는 repository root 기준이다. acceptance에 필요한 검사만 고르고 수정 없이 통과한 검사를 불필요하게 반복하지 않는다.

## 영향별 검사

- 언어/화면: 기존·추가 locale, URL/fallback, 날짜·통화 표시, success/loading/empty/error/permission, keyboard/focus, 390px/tablet/desktop. layout 변경은 browser 확인이 필요하다.
- API: 독립 api/service 환경에서 정상·비관리자·CSRF·session·다른 국가 ID·잘못된 입력 회귀.
- 금융/수집: 공식 source fixture, native 타입/단위/조건/current-origin, optional omission와 essential exclusion, 영향 promotion/Public eligibility.
- DB: schema/persistence 검토와 허용된 격리 DB에서 upgrade/constraint/transaction/복구 확인. mock을 실제 migration 성공으로 표시하지 않는다.
- 문서/스킬: 링크·UTF-8·frontmatter·적용 범위·명령과 실제 파일 정합. 문서 변경에 앱 전체 build를 요구하지 않는다.

실행 명령은 개발 가이드와 해당 runtime README를 사용한다. Admin은 typecheck/test/build, API는 uv run --directory api/service의 unittest, Worker는 root uv의 unittest다. full foundation은 설치/build를 포함하므로 격리 clone에서 실행한다. harness 변경 시 docs/00-governance/harness-engineering-baseline.md를 읽는다.

## 실패와 완료 판정

현재 변경 결함, 기존 결함, 환경 문제와 미수행을 구분한다. fixture hash 실패를 expected hash 수정으로 숨기지 않는다. ignored tmp의 기존 문서 오류는 경로를 기록하고 전달 source에 대한 검사를 별도로 수행한다. 기존 사용자 파일이나 evidence를 검사 통과 목적으로 삭제하지 않는다.

배포 준비에는 필요한 migration → API/Worker → Admin의 영향 순서, config, health/read-only smoke, rollback 조건을 적는다. 해당 순서는 변경 영향에 맞춘다. 실제 배포와 데이터 쓰기는 허용된 대상 범위에서만 실행한다. 로컬 test, serving version, 실제 수집/canonical/Public 결과를 구분한다.

최종 diff와 goal acceptance를 확인하고 journal에 변경 이유·파일·실행 결과·known issue·다음 단계를 짧게 기록한다. 다른 goal ownership은 보존한다. 인수자에게 무엇이 바뀌었고 어떤 검증이 끝났으며 무엇이 남았는지 보고한다.
