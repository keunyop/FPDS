# FPDS Admin 개발 가이드

2026-10-07 · 대상: 국가별 로컬라이징과 기능 추가·수정을 담당하는 개발자

이 파일에서 개발 시작 방법, 주요 수정 위치와 AI 스킬 사용법을 확인하면 된다.

## 1. 프로젝트 이해하기

FPDS Admin은 공식 금융상품 정보를 수집하고 자동 검증한 결과를 운영하는 도구다. 수집 대상 국가, Banks, Runs, Review등의 기능을 제공한다.

| 위치 | 담당 기능 |
|---|---|
| app/admin | Next.js/TypeScript 화면, 사용자 입력, Python API 호출 |
| api/service | FastAPI 인증·권한·국가별 데이터, 업무 API, 수집 실행 조정 |
| worker | 공식 출처 발견, HTML/PDF 수집·파싱, 금융정보 추출·정규화·검증 |
| db/migrations | PostgreSQL schema 변경 이력 |
| shared | 언어·디자인·보안·공통 설정 계약 |
| storage | 비공개 원문 저장소 계약 |
| app/public | 별도 Public 앱; 공개 결과까지 변경할 때만 수정 |

흐름은 **Admin → API → Worker/DB → 승인된 Public projection**이다. 브라우저가 DB나 원문 저장소에 직접 접근하지 않는다. 실제 화면 경로는 [Admin route 목록](../app/admin/routes.manifest.json), 운영 방법은 [사용자 매뉴얼](FPDS_Admin_사용자_매뉴얼.md)을 참고한다.

## 2. 처음 실행하기

별도 개발 clone을 준비한다. Node 24, pnpm(package.json 기준), Python 3.12 이상, uv와 개발용 PostgreSQL이 필요하다. 실제 수집 테스트에는 private storage와 필요한 provider 자격증명도 필요하다.

저장소 루트에서 실행한다.

```powershell
uv sync --frozen
uv sync --directory api/service --frozen
pnpm --dir app/admin install --frozen-lockfile
```

API와 Worker는 독립 Python 환경이다. 두 프로젝트를 모두 준비하고 API 테스트는 api/service 환경에서 실행한다.

설정은 .env.dev.example → 로컬 .env.dev, app/admin/.env.example → app/admin/.env.local로 복사한다. 기존 파일은 덮어쓰지 않는다. 예제의 placeholder를 개발 환경 값으로 채운다. DB URL, 세션/CSRF secret, 저장소·provider key는 Git에 넣지 않는다.

신규 DB의 준비 사항, 전체 migration 적용 순서와 구축 확인 방법은 [DB README](../db/README.md)를 따른다. 최초 계정은 [API README](../api/service/README.md)의 bootstrap 절차를 사용한다. migration·계정 생성은 의도한 개발 DB를 대상으로 실행한다.

별도 터미널 두 개에서 서버를 시작한다.

```powershell
# 터미널 1: 저장소 루트
$env:FPDS_ENV_FILE = '.env.dev'
uv run --directory api/service uvicorn api_service.main:app --reload --host localhost --port 4000
```

```powershell
# 터미널 2: 저장소 루트
pnpm --dir app/admin run dev
```

API 확인: http://localhost:4000/healthz · Admin: http://localhost:3001/admin/login

개발 환경 표시, 국가 선택, 로그인/로그아웃을 확인한다. 수집 중인 기존 작업공간에서 설치·build·재시작을 수행하지 않는다.

## 3. 국가별 로컬라이징

먼저 대상 국가, 화면 언어, 상품 유형, 통화, 공식 금융기관 출처를 정한다. 예를 들어 일본어 화면을 쓰는 것과 일본 금융상품을 수집하는 것은 별도 영역이다. 현재 화면 언어는 EN/KO/JA이다.

| 바꿀 내용 | 주요 수정 위치 | 확인할 것 |
|---|---|---|
| 화면 언어·메뉴·오류 메시지 | [admin-i18n.ts](../app/admin/src/lib/admin-i18n.ts), app/admin/src/components, [shared locale 설정](../shared/i18n/locale-config.json) | locale 타입·선택기·fallback·URL 전달과 컴포넌트 내 문구를 함께 확인. JSON 번역만 추가해서 끝내지 않음 |
| 날짜·숫자·통화 표시 | admin-i18n.ts와 해당 UI formatter | 표시 언어와 실제 상품 통화를 구분. 숫자 표시는 바꿔도 금융 값·단위를 변경하지 않음 |
| 수집 대상 국가 | [countries.py](../api/service/api_service/countries.py), [국가 목록](../api/service/api_service/country_catalog.py), country_registry | 국가 활성화, 로그인/전환, 다른 국가 ID 접근 차단. 국가 활성화만으로 수집 준비가 완료되는 것은 아님 |
| 현지 상품명·검색어 | [product_type_localization.py](../api/service/api_service/product_type_localization.py), Product Type/은행 coverage 설정 | 현지 명칭·공식 사이트 언어와 실제 상품 유형을 연결. 이름 변경만으로 다른 금융 의미를 같은 유형으로 취급하지 않음 |
| 금융 필수 정보·통화 | [market profile](../worker/pipeline/fpds_market_profile.py), [country defaults](../worker/country_defaults.py), [field contract](../worker/pipeline/fpds_field_contract.py) | 새 국가의 명시적 계약과 공식 근거. 기존 국가의 금리·기간·통화 규칙을 복사해 추정하지 않음 |
| 공식 출처·수집 | API의 bank/source catalog, worker/discovery | 공식 domain, source language, 해당 상품의 identity와 근거, SSRF 방어 |

새 국가를 지원할 때는 **시장/상품 계약 → 언어와 표시 → source/수집 → API·화면 → 회귀 검증** 순서로 진행한다. UI 번역만 요청받았다면 시장 설정까지 바꾸지 않는다. 한국어/일본어 지원이 해당 국가의 금융 규칙 구현을 의미하지 않는다.

상품명·은행 원문·금리 조건은 source language로 보존한다. 화면 label만 번역한다. 새 국가의 기본값은 해당 시장 요구사항과 근거를 확인해 명시적으로 정한다.


## 4. 기능 추가와 수정

| 작업 | 시작 위치 |
|---|---|
| 화면·폼·목록·dialog | app/admin/src/app/admin, app/admin/src/components/fpds/admin |
| 스타일·기본 컴포넌트 | app/admin/src/app/globals.css, app/admin/src/components/ui |
| UI와 API 연결 | app/admin/src/lib/admin-api.ts, 해당 route.ts proxy |
| 업무 API | api/service/api_service/main.py와 기능별 service 파일 |
| DB 필드 | db/migrations의 새 migration, 관련 API/Worker persistence |
| 수집 오류·누락 | api/service/api_service/source_collection_runner.py, worker의 해당 pipeline service/persistence |

기능 변경은 화면 → API → 저장/처리 → 테스트를 한 흐름으로 확인한다. UI 표시만 바뀌는 경우 DB까지 변경할 필요는 없다. 기존 component와 semantic token을 재사용하고, 디자인 변경 시 [현재 UI 기준](../docs/03-design/fpds_design_system_stripe_benchmark.md)을 확인한다.

보존할 핵심 계약:

- 국가는 API 세션이 결정한다. 브라우저 query/body로 국가 접근 권한을 확대하지 않는다. 운영 데이터 mutation은 서버에서 role·CSRF를 검증한다.
- 공식 근거가 있는 금융 사실만 승인한다. 필수 정보 부족은 자동 제외하며 수동 상품 승인 대기열을 만들지 않는다.
- 변경 시 [수집 정확성 정책](../docs/03-design/collection-accuracy-policy.md)과 [금융 필드 계약](../docs/03-design/financial-product-field-contract.md)을 읽는다.
- 기존 migration, source fixture/hash, 상품 version/change 이력을 보존한다. DB·보안 변경은 [보존 정책](../docs/03-design/bounded-data-retention-policy.md)과 [보안 계약](../docs/03-design/security-access-control-design.md)을 확인한다.


## 5. 앞으로 사용할 AI 스킬

스킬은 AI가 작업별 수정 위치와 검증 기준을 따르도록 하는 지침이다.

| 스킬 파일 | 용도 | AI에 줄 입력 | 받아야 할 결과 |
|---|---|---|---|
| [fpds-localize-market](ai-skills/fpds-localize-market/SKILL.md) | 언어·표시 로컬라이징, 새 국가/상품 시장 지원 | 국가, locale, 상품 유형, 공식 출처, 변경 범위 | 수정 코드·설정, 시장별 근거/계약, 기존 국가와 언어 회귀 결과 |
| [fpds-change-feature](ai-skills/fpds-change-feature/SKILL.md) | 화면/API/DB에 걸친 기능 추가·수정 | 사용자 흐름, 기대 결과, 재현 사례, 허용 데이터 변경 | 최소 구현, 관련 migration이 있으면 적용 계획, 정상·실패 테스트 |
| [fpds-fix-collection](ai-skills/fpds-fix-collection/SKILL.md) | 현지 은행의 수집 실패·누락·잘못된 금융 값 교정 | bank/country/type/Run, 보존 evidence, 기대 사실 | 최초 결함 재현, 공통 경로 수정, 공식 근거 회귀, 실제 승인·제외 결과 |
| [fpds-verify-change](ai-skills/fpds-verify-change/SKILL.md) | 변경 검증과 배포 준비 | diff, 완료 조건, 대상 환경, 기존 검사 결과 | 영향별 테스트, 미해결 항목, 적용/복구 순서와 실제 수행 결과 |

가장 간단한 사용법은 AI에게 해당 파일을 읽게 하는 것이다. 파일 경로는 FPDS clone 루트를 기준으로 해석한다.

```text
descent/FPDS_Admin_개발_가이드.md와
descent/ai-skills/fpds-localize-market/SKILL.md를 읽고 작업해주세요.
대상: [국가 / 화면 언어 / 상품 유형]
요청: [언어·표시 변경 또는 해당 시장 수집 지원]
완료 조건: [사용자 흐름과 확인할 결과]
환경과 허용 작업: [개발 clone, fixture 또는 명시한 dev DB 작업]
관련 회귀를 실행하고 변경 파일, 결과와 남은 항목을 정리해주세요.
```

기능 변경은 fpds-change-feature, 수집 오류는 fpds-fix-collection 파일로 바꾸어 같은 형식을 사용한다. 마지막 검증에는 fpds-verify-change를 적용한다. 

Codex에 등록하려면 인수 clone의 .agents/skills 또는 사용자 홈의 .agents/skills에 필요한 스킬 폴더 전체를 복사하고 인식 여부를 확인한다. 등록 후 `$fpds-localize-market`처럼 호출할 수 있다. [공식 skill 위치 안내](https://learn.chatgpt.com/docs/build-skills#where-codex-loads-local-skills)