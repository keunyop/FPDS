---
name: fpds-change-feature
description: FPDS Admin 인수 후 화면·API·DB에 걸친 기능을 추가하거나 기존 동작을 수정할 때 사용한다. 사용자 흐름을 기준으로 최소 변경과 정상·오류·권한 회귀를 완성한다.
---

# 기능 추가와 수정

FPDS clone의 AGENTS.md와 descent/FPDS_Admin_개발_가이드.md를 읽는다. 모든 경로는 repository root 기준이다. 요청을 사용자 role/국가/화면/동작/기대 결과로 정리하고 재현 사례와 완료 조건을 고정한다. MVP 계획·WBS·이전 gate 승인을 새 개발의 선행조건으로 요구하지 않는다.

## 구현

관련 runtime README를 읽고 UI → proxy/API → domain service → persistence → 테스트를 추적한다.

- UI route: app/admin/src/app/admin와 routes.manifest.json.
- UI domain/component: app/admin/src/components/fpds/admin, src/components/ui와 globals.css. 축약 src 경로는 app/admin 기준이다.
- UI API 계약: app/admin/src/lib/admin-api.ts와 route.ts proxy.
- API: api/service/api_service/main.py와 해당 기능 service.
- DB: db/migrations의 다음 migration과 영향 persistence. SQL 준비와 실제 적용은 구분한다.

기존 component/token을 재사용하고 label/locale/empty/loading/error/permission/retry를 함께 다룬다. UI 변경 전 현재 디자인·언어 계약을 읽고 vendor 직접 편집은 provenance/override 기록을 확인한다. 새 금융 필드나 수집 의미를 바꾸면 정확성/필드 계약도 읽는다.

운영 데이터의 국가 권위는 API session이다. server role/CSRF, cookie/session, source safe-fetch와 private evidence를 유지한다. 인증/가입 route의 별도 계약을 운영 mutation 권한과 혼동하지 않는다. UI에서 버튼을 숨기는 것만으로 권한 검증을 대체하지 않는다.

Review는 역사 조회이며 신규 상품 수동 승인 기능을 복원하지 않는다. Runs refresh의 dirty/busy/focus 제어와 source-catalog proxy 소비자를 보존한다. schema가 필요하면 기존 migration을 수정하지 않고 upgrade/rollback 또는 forward-fix 계획을 작성한다. scope 밖 refactor를 섞지 않는다.

## 검증과 결과

변경 behavior의 success/boundary/failure를 검증한다. API는 독립 api/service Python 환경에서 테스트하고 root Worker 의존성이 import 오류를 가리지 않게 한다. layout 영향은 기존/추가 locale·390px/tablet/desktop·keyboard로 확인한다. 실제 DB 동작은 허용된 격리 DB에서 검증한다.

요청 동작, 변경 파일/계약, 실행한 검사, 남은 제한과 적용 순서를 정리한다. 관련 문서와 journal, 이번 goal 항목을 갱신하고 git diff --check를 실행한다. live DB/계정 작업과 배포는 이미 허용된 대상 범위를 따르며 구현 요청으로 권한을 확대하지 않는다.
