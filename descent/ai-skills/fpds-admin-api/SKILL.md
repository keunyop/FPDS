---
name: fpds-admin-api
description: FPDS Admin의 FastAPI endpoint, domain service, session, RBAC, CSRF, 국가 scope 또는 Next.js API proxy 계약을 구현·수정할 때 사용한다. 실 계정 조작이나 배포 권한은 제공하지 않는다.
---

# FPDS Admin API 개발

## 적용과 읽기

경로는 FPDS repository root 기준이다. AGENTS.md와 root README → docs/00-governance/development-journal.md → docs/README.md를 읽고 api/service/README.md, docs/03-design/api-interface-contracts.md, docs/03-design/security-access-control-design.md를 확인한다. UI proxy를 바꾸면 app/admin/README.md도 읽는다. 제품 동작/acceptance 변경이면 요구사항과 scope-baseline, 아키텍처/위험이면 decision/RAID를 추가 확인한다.

## 계약을 한 흐름으로 추적

호출 UI/proxy → app/admin/src/lib/admin-api.ts → api/service/api_service/main.py → domain service → SQL/DB → 테스트를 찾는다. route decorator의 method, response envelope/status, request validation, timeout과 transaction 경계를 먼저 파악한다.

main.py는 route/session/CSRF/role/country 적용을, auth.py/security.py는 인증 제어를, db.py는 DB 접속을 담당한다. 작업별 product_types.py, source_catalog.py, run_status.py, run_retry.py 등 해당 서비스에 최소 변경을 둔다.

## 보안과 현재 workflow

- session.country_code가 국가 권위다. 국가 소유 list/detail/write의 SQL과 ID lookup에 적용한다. 외부 country query/body로 접근 범위를 넓히거나 다른 국가 row의 존재를 드러내지 않는다.
- 보호된 운영 데이터 mutation에 admin role과 CSRF를 서버에서 검증한다. 로그인·가입 요청 등 인증 route는 별도 계약을 따른다. reviewer role 값은 과거 상품 review mutation을 복원할 근거가 아니다.
- 기존 signup 승인, login throttling, cookie/session expiry/revocation, logout 실패 표현, safe return URL, CORS/security headers를 보존한다.
- approve/reject/defer/edit-approve/ai-verify 상품 review endpoint는 retired 410이다. Sources 직접 create/update는 405이며 생성 설정은 bank coverage가 소유한다.
- source URL 변경은 shared safe-fetch/SSRF, official-domain/redirect/private-network 검사를 유지한다. model이 준 URL을 신뢰하거나 private object URL을 client에 반환하지 않는다.
- Public 응답은 승인 projection 필드만 반환한다. candidate payload/receipt/trace, private evidence, operator note, secret을 섞지 않는다.

## 독립 환경 회귀

API 의존성은 api/service/pyproject.toml와 api/service/uv.lock 기준이며 root Worker 환경과 분리된다. API는 beautifulsoup4를 선언한다. parser identity만 필요하면 worker/pipeline/fpds_parse_chunk/version.py를 사용하고 pypdf parser를 API에서 import하지 않는다. 새 Worker import가 생기면 독립 API interpreter에서 startup/import를 검증한다.

회귀는 정상 성공 외에 unauthenticated/expired session, 비관리자 mutation, CSRF 누락·오류, 다른 국가 ID, invalid payload와 적용 가능한 transaction 실패를 포함한다. 실패 response를 UI permission/unavailable 상태로 이어 확인한다.

격리 clone 루트에서 `uv run --directory api/service python -m unittest discover -s tests -p "test_*.py"`를 실행한다. root uv로 API 테스트만 통과한 결과를 독립 API 통과로 표현하지 않는다. UI 계약 변경은 Admin 관련 테스트도 실행한다.

결과는 API 계약의 before/after, 실제 허용·거부 회귀, 필요한 migration/rollout과 미수행 항목을 기록한다. journal/관련 계약/이번 goal slice를 갱신하고 diff를 확인한다. 실 계정 생성·회수, schema 적용, collection와 canonical/Public writes는 요청에 포함된 대상·환경 권한 안에서만 실행한다.
