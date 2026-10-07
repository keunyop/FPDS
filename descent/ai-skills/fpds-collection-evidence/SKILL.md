---
name: fpds-collection-evidence
description: FPDS 일반 Admin 수집의 공식 evidence 획득, HTML/PDF parse, field loss, provenance, 금융 정규화·검증 실패를 재현하고 shared path로 수정할 때 사용한다. 필수 조건 완화나 수동 상품 승인에는 사용하지 않는다.
---

# FPDS 수집 evidence 교정

## 적용과 현재 계약

경로는 FPDS repository root 기준이다. AGENTS.md와 root README → docs/00-governance/development-journal.md → docs/README.md를 읽는다. api/service/README.md와 worker/README.md, docs/03-design/collection-accuracy-policy.md, docs/03-design/financial-product-field-contract.md를 읽고 관련 최신 dated implementation report로 버전/한계를 확인한다.

작업 입력은 bank/country/type, Run ID, captured registry/snapshot/chunks/artifacts, 재현되는 기대 사실과 허용 side effects다. secret/raw evidence를 Git/공개 산출물에 복사하지 않는다. 실제 raw 자료는 기존 private 경로로 읽고 repo regression fixture로 추가할 내용은 승인된 공식 source와 private trace 분리를 확인한다.

## 최초 차이부터 확인

동일 입력의 capture → parse/chunk → retrieval/extraction → normalization → accuracy/validation → promotion → projection 순서로 값·조건·origin이 처음 바뀌는 위치를 찾는다. exclusion reason만으로 bank nondisclosure나 model 품질을 단정하지 않는다. live runtime/Run process 버전과 local code를 구분한다.

보존 evidence SHA-256와 parser/process/cache identity를 확인한다. 기대값은 공식 원문에서 독립적으로 정한다. 실제 missing-parent, chunk limit, persisted artifact와 origin loader를 재현하며 fixture가 실 서비스에 없는 parent/field를 미리 채우지 않게 한다. 불일치 hash를 통과 목적으로 교체하지 않는다.

새 accepted pattern 전에 source-backed regression을 추가한다. 성공과 함께 다른 상품/은행/국가/언어, 다른 fee/rate column, 조건부 zero, 불완전 footnote, conflict/expired evidence, 현재 origin mismatch와 optional-only gap을 확인한다.

## 금융 의미와 provenance

정확한 identity/통화/타입·단위를 지킨다. rate는 percentage points number, money는 상품 통화 number, count/day는 명시적 integer, flag는 boolean이다. APY/nominal/APR, range/prime+spread/promotion/penalty, investment horizon/contract term을 혼합하지 않는다. 기간을 추정 변환하거나 unknown을 0/false로 채우지 않는다.

checking 거래 비용, GIC/CD access·허용 시 결과/무벌금, LOC secured/unsecured는 조건부 essentials다. policy의 grouped alternatives와 country-owned added required fields를 적용한다. 명시적 currency를 우선하며 미공개 CA/CAD와 US/USD만 승인된 default다. conflict는 fail closed다.

profile/registered optional은 같은 공식 evidence가 증명하면 원래 값/조건을 normalization까지 보존한다. 미확인은 생략하며 추가 검색/재시도/penalty를 만들지 않는다. incomplete essentials는 자동 제외이며 사람 검토나 confidence 예외로 보내지 않는다.

trusted origin은 같은 Run의 성공 selected source/snapshot/parse/evidence DB join에서 얻는다. bank/country/language, exact quote와 실제 원문 URL/IDs를 유지한다. extraction/model metadata로 provenance를 만들거나 과거 성공 Run으로 현재 실패를 채우지 않는다.

## 공통 경로와 비용 경계

api/service/api_service/source_collection_runner.py와 collection_evidence_research.py, worker의 각 service.py/persistence.py, fpds_collection_accuracy.py/fpds_field_contract.py/fpds_market_profile.py/fpds_collection_fields.py/fpds_comparison_instructions.py를 확인한다. 관련 prompts와 모든 gates를 함께 검토하고 변경 의미에 맞는 version/cache fingerprint를 갱신한다.

현재 essential research는 두 waves, detail당 추가 URL 두 개, Run당 추가 URL 48개, planner calls 여덟 개다. browser attempt는 같은 URL 한 번, 초기/추가 render가 48/Run allowance를 공유한다. 관찰된 공식 lead와 supplied link ID만 사용하고 planner 결과를 사실로 승인하지 않는다. 실패·한도 종료 receipt를 보존한다. optional gaps에는 acquisition을 추가하지 않는다.

기존 identical-input cache/replay를 먼저 쓰고 요청 밖 paid retry·수집·canonical/Public write·배포를 하지 않는다. 일회성 legacy recovery를 영구 기능/메뉴/scheduler로 만들지 않는다.

## 검증과 인계

focused source-backed 회귀 후 root Worker suite와 독립 API suite를 실행한다. shared 금융 판정이 바뀌면 candidate promotion와 snapshot-pinned Public eligibility도 검증한다. meaningful DB write semantics는 격리 PostgreSQL 확인 전까지 fixture 통과와 구분한다.

결과는 proven facts/omitted optional/excluded essentials, 최초 결함, 동일 입력 결과, costs/stop reasons, local/serving/canonical/projection/Public readback 증거를 구분해 적는다. journal/계약/이번 goal slice와 diff를 확인한다. 신규 live acceptance가 허용되면 실제 ordinary Run과 정확한 canonical version·aggregate·Public list/detail을 확인하며 replay pass 수를 공개 상품 수로 보고하지 않는다.
