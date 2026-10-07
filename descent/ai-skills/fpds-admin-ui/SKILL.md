---
name: fpds-admin-ui
description: FPDS Admin의 화면, 폼, 목록, dialog, route와 EN/KO/JA 상호작용을 기존 디자인 시스템으로 구현하거나 수정할 때 사용한다. 금융 수집 판정이나 Public 화면 재설계는 별도 작업이다.
---

# FPDS Admin UI 개발

## 적용과 기준 찾기

현재 요청에 필요한 Admin UI slice를 구현한다. 경로는 스킬 설치 위치가 아니라 FPDS repository root 기준이다. 다른 프로젝트에서는 적용하지 않는다.

AGENTS.md와 root README → docs/00-governance/development-journal.md → docs/README.md 순서로 읽고 app/admin/README.md, app/admin/routes.manifest.json을 확인한다. 이미 읽은 세션이라면 최신 변경만 확인한다.

UI 편집 전 docs/03-design/README.md, fpds-design-system.md, fpds_design_system_stripe_benchmark.md, admin-information-architecture.md, localization-governance-and-fallback-policy.md를 읽는다. 이 파일명들은 docs/03-design 기준이다. 지표·시각화 변경은 design index가 연결하는 해당 계약을 더 읽고 vendor UI 직접 변경은 adoption log, block inventory, override register를 읽는다.

## 변경 추적

- route composition은 app/admin/src/app/admin, domain surface는 app/admin/src/components/fpds/admin, primitive는 app/admin/src/components/ui에 있다.
- server API read/type은 app/admin/src/lib/admin-api.ts, UI 문구·locale URL은 admin-i18n.ts, browser auth는 admin-auth-client.ts를 확인한다.
- 기존 shell/token/domain component를 재사용한다. 새 기본 UI 체계를 만들거나 필요 없이 vendor block을 재설치하지 않는다.
- API 계약이 바뀌면 해당 route.ts proxy → API main.py → 서비스/테스트를 추적한다. UI 표시 변경만으로 DB나 금융 gate를 바꾸지 않는다.

## 유지할 운영 의미

Overview/Runs/Banks가 일상 업무다. Review는 More tools의 read-only history다. 승인·수정 승인·보류·AI Verify·bulk selection을 복원하지 않는다. 가입 승인은 별도다.

국가는 API 세션이 정한다. query/body를 국가 권한으로 쓰지 않는다. 국가 전환은 CSRF와 활성 국가 제한을 지키고 Overview로 이동한다. server auth/RBAC를 UI 숨김으로 대체하지 않는다.

Runs Auto refresh는 15초의 기존 dirty/busy/focus/dialog/visibility 제어를 유지한다. source-catalog 페이지 redirect가 있어도 Banks가 사용하는 proxy는 보존한다. Product Type required/optional UI는 보호된 금융 essentials와 국가별 설정을 그대로 표현한다.

EN/KO/JA UI 문구와 locale/filter 문맥을 유지한다. source-derived 이름·조건은 원문으로 둔다. error/unavailable/empty/loading/permission-denied, retry, label/focus/non-color 상태 단서를 영향 범위에 맞게 구현한다.

## 검증과 결과

관련 app/admin/tests 회귀를 실행하고 typecheck/test/build를 격리 개발 clone에서 수행한다. package에 없는 lint script를 만들어 호출하지 않는다. layout 변경은 EN/KO/JA × 정확한 390px/768px/1440px와 키보드 주요 흐름을 확인한다. 합성 데이터 화면은 real-data/UAT 증거와 구분한다.

결과에는 수정한 operator behavior, 변경 계약/파일, 실제 실행 결과, 브라우저 검증 범위와 미수행 항목을 적는다. 해당 README/design/journal과 기존 goal의 이번 slice만 갱신하고 git diff --check를 실행한다. UI 구현 요청으로 라이브 수집·계정 변경·배포 권한이 추가되지 않는다.
