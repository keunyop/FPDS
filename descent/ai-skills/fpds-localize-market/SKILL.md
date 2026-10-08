---
name: fpds-localize-market
description: FPDS Admin 인수 후 UI 언어·표시를 현지화하거나 요청된 국가의 금융상품 수집을 지원할 때 사용한다. UI locale과 금융시장 지원 범위를 구분하고 기존 국가·금융·보안 계약을 검증한다.
---

# 국가와 언어 로컬라이징

FPDS clone 루트의 AGENTS.md와 descent/FPDS_Admin_개발_가이드.md를 읽는다. 아래 경로는 스킬 설치 위치가 아니라 repository root 기준이다. 대상 국가/locale/상품 유형/공식 출처와 이번 요청이 번역인지 시장 지원인지 확인한다. 주어진 정보로 진행 가능한 부분부터 구현한다.

## 수정 위치

- UI: app/admin/src/lib/admin-i18n.ts의 locale type/labels/formatters, app/admin/src/components의 locale 분기·선택기·오류/빈 화면, shared/i18n/locale-config.json. shared JSON만 바꿔도 모든 UI가 번역된다고 가정하지 않는다.
- 국가: api/service/api_service/countries.py와 country_catalog.py, DB country_registry와 session.country_code. 활성화와 금융상품 수집 준비는 별도다.
- 현지 금융 용어: api/service/api_service/product_type_localization.py와 Product Type/은행 coverage 설정. 현지 이름으로 canonical 금융 의미를 바꾸지 않는다.
- 시장 계약: worker/pipeline/fpds_market_profile.py, fpds_field_contract.py, fpds_collection_fields.py와 worker/country_defaults.py. 파일명을 줄인 pipeline 모듈은 worker/pipeline 기준이다.
- 출처: API bank/source catalog, worker/discovery의 공식 domain·국가·언어·상품 경계와 safe-fetch.

UI 작업은 app/admin/README.md와 현재 디자인/언어 계약을, 시장 수집은 api/service/README.md·worker/README.md와 docs/03-design/collection-accuracy-policy.md·financial-product-field-contract.md를 읽는다. 작업에 필요한 문서만 읽는다.

## 구현 순서와 경계

새 시장이면 명시적 상품별 금융 계약과 공식 source fixture를 먼저 정하고, locale/표시·source/수집·API/UI를 연결한다. UI 번역만 요청되면 시장 설정은 확장하지 않는다. 국가 목록의 존재나 언어 지원만으로 금융 지원을 완료 처리하지 않는다.

원문 상품명·금융 조건·근거는 source language로 둔다. UI label과 날짜/숫자 표시만 현지화한다. 실제 통화와 표시 언어를 혼합하지 않는다. 미공개 통화의 현행 default는 CA/CAD, US/USD이며 새 default는 요청된 시장 계약과 근거에 따라 명시적으로 정한다.

금리의 percentage points, APR/APY/nominal 의미, 정확한 term과 조건을 유지한다. optional 미확인은 생략하고 required 공백은 자동 제외한다. 거래 비용·인출 결과·담보 조건을 낮춰 국가 지원률을 올리지 않는다. 새 시장의 법규·공시 사실이 필요한 경우 최신 공식 출처를 확인하며 추정하지 않는다.

## 완료 증거

추가/기존 locale의 success/empty/error/fallback·locale URL, 390px/tablet/desktop·keyboard를 확인한다. 새 국가의 login/switch와 다른 국가 ID 차단, typed 금융/통화/근거 회귀를 검증한다. Public 변경도 요청됐으면 해당 locale/projection/표시까지 확인한다.

변경된 시장 계약·코드, 검증 결과와 미지원 조건을 보고하고 journal에 기록한다. live 국가 활성화/등록·유료 수집·DB writes·배포는 요청된 환경과 허용 범위에서만 수행한다.
