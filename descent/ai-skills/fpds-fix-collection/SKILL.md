---
name: fpds-fix-collection
description: FPDS의 기존 또는 새 국가 은행에서 수집 실패·금융정보 누락·잘못된 값이 재현될 때 공식 evidence를 추적해 공통 수집 경로를 교정한다. 수동 승인이나 필수 정보 완화로 우회하지 않는다.
---

# 수집 품질 유지보수

FPDS clone의 AGENTS.md, descent/FPDS_Admin_개발_가이드.md, api/service/README.md, worker/README.md와 docs/03-design의 collection-accuracy-policy.md·financial-product-field-contract.md를 읽는다. 모든 경로는 repository root 기준이다.

입력은 country/bank/type/Run, 보존 registry/snapshot/chunks/artifact 접근과 공식 원문에 근거한 기대 사실이다. private evidence와 secret은 Git/공개 보고서에 넣지 않는다. 관련 과거 보고서는 원인·회귀를 조사할 때만 읽는다.

## 재현하고 수정

같은 Run의 문서 선택 → 캡처와 파싱 → 추출 → 정규화 → 검증 → 상품 원본 반영 순서로 최초의 차이를 찾는다. 은행 상세에서 직접 관찰한 링크, 실제 요청 주소, 최종 도착 주소, 원문 SHA-256과 파서 버전을 확인한다. 문서를 찾지 못한 경우, 읽지 못한 경우, 읽고도 상품 조건을 입증하지 못한 경우를 구분한다. 자세한 예시는 [운영 가이드](../../은행_상품_수집_검증_가이드.md)를 따른다.

실제 parent/저장 artifact/current-origin을 재현하는 공식 source fixture와 독립 기대값을 먼저 만든다. 다른 상품·은행·국가·언어, 조건부 fee/금리 column/만료·충돌·origin mismatch의 부정 사례를 포함한다. 예상 hash를 통과 목적으로 바꾸지 않는다.

수정 위치는 api/service/api_service/source_collection_runner.py·collection_evidence_research.py, worker 단계별 service.py/persistence.py와 공유 financial/profile/field/instructions 모듈이다. 관련 prompts/gates와 cache/version 의미를 함께 확인한다. bank별 통과 예외를 만들지 않는다.

## 금융·비용 경계

rate/fee/term/currency의 원래 타입·단위·조건을 보존한다. unknown은 0/false가 아니다. required 부족/충돌은 자동 제외하고 같은 근거의 verified optional은 유지한다. 거래 비용, 조기 인출 허용/결과, 담보 조건과 국가별 added required를 유지한다.

trusted origin은 해당 Run의 성공 selected snapshot/parse DB join에서 얻는다. 모델 URL/ID로 provenance를 만들거나 과거 성공 Run으로 현재 실패를 채우지 않는다.

기존 동일 입력 재사용과 예산을 적용한다. 현재 essential research는 2 waves, detail당 추가 URL 2개, Run당 추가 URL 48개/계획 호출 8개이며 초기·추가 browser attempts가 48/Run 한도를 공유한다. 같은 URL browser 시도는 한 번이다. optional gap만으로 검색/재시도를 추가하지 않는다. 한도 변경은 요청 범위와 근거가 필요하다.

## 검증과 결과

source-backed 회귀 후 영향 Worker/독립 API suite, 자동 승인 결과를 확인한다. 실제 PostgreSQL 쓰기·유료 provider·배포 검증은 허용된 환경에서만 수행한다.

최초 결함, 공식 기대값, 누락 optional/제외 essential, 실제 테스트·비용·종료 사유를 보고한다. local replay, serving version, live Run, canonical 상품 기록을 구분한다. 재생 테스트 통과와 실제 상품 승인을 구분한다. journal과 이번 goal을 갱신한다.
