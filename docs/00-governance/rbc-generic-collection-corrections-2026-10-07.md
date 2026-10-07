# RBC 직접 수집, 범용 수정 및 공개 검증 — 2026-10-07

최신 RBC 수집에서는 41개 후보가 모두 자동 제외되었습니다. Admin 수집 API를
사용하지 않고 동일 수집 대상의 공식 페이지를 직접 캡처하고 공통 처리 코드를
수정한 결과, 15개 후보가 정상 자동 검증을 통과했습니다. 카드 13개, savings
1개, chequing 1개입니다. 수동 승인, 필수 조건 완화, 모델 신뢰도 예외는 없습니다.
직접 수집한 15개를 정상 자동 승인·공개했으며, 아래에 검증 결과와 배포 경계를 기록합니다.

## 확인 범위와 최신 결과

최신 일괄 요청은 2026-10-07 12:51:49 UTC(밴쿠버 05:51)입니다. 아래 일곱
상품 유형의 원래 Run, 41개 후보 및 65개 Run 소스 항목을 보존했습니다.
실제 후보가 생긴 여섯 Run의 process는
`2026-10-06-named-companion-binding-v4`입니다. mortgage는
`no_eligible_detail`로 수집 전 건너뛰었으며 후보가 없습니다. mortgage 금리표와
가이드/개요를 개별 상품으로 승격시키지 않았습니다.

| 유형 | 최신 후보 | 기존 승인 | 직접 수집 후 자동 통과 | 이번 자동 제외 |
|---|---:|---:|---:|---:|
| savings | 9 | 0 | 1 | 8 |
| chequing | 6 | 0 | 1 | 5 |
| gic | 3 | 0 | 0 | 3 |
| credit-card | 15 | 0 | 13 | 2 |
| personal-loan | 6 | 0 | 0 | 6 |
| line-of-credit | 2 | 0 | 0 | 2 |
| mortgage | 0 | 0 | 0 | 0 |

성공한 기존 대상 URL을 중복 제거하고 HTTPS로 정규화해 56개를 직접 안전하게
캡처했습니다. URL/최종 URL/시각/MIME/SHA-256과 원문을 비공개로 유지했습니다.
두 금리 페이지는 직접 HTML에 실제 데이터가 비어 있어 각각 한 번 렌더링했습니다.
최종 일반 safe-fetch 함수로도 같은 두 URL의 자동 렌더링을 확인했습니다.
추가 모델 호출 및 Admin 수집 API 호출은 모두 0회입니다. 오래된 수치를 복원하지
않았고 동일한 현재 입력을 재검증에 재사용했습니다.

## Admin 수집에서 놓친 이유와 공통 수정

1. **동적 금리 영역을 법적 각주의 숫자가 가렸습니다.**
   직접 HTML의 상품 행/금리 컨테이너는 비었는데 각주에 `5%` 등이 있어 기존
   렌더링 판정은 숫자 금리가 있는 페이지로 처리했습니다. 공식 도메인, 실제
   금리 로더와 빈 가격 영역을 함께 확인하는 공통 판정을 fetch와 필수 증거
   연구에 연결했습니다. 이 판정은 브라우저 실행만 요청하며 금융값을 만들지
   않습니다. 기존 렌더/연구 예산과 실패 처리 경계를 유지합니다.
2. **추천 상품의 가격이 본 상품의 가격으로 연결됐습니다.**
   Avion Infinite 본 상품의 연회비 120과 추천 카드 399/139가 같은 H1에
   연결되어 충돌했습니다. 실제 제품명 속성/패널 이름과 가까운 DOM 소유 관계를
   확인하며 다른 상품의 값을 거부합니다. 한 행에 여러 라벨/값 쌍이 있는 표도
   해당 쌍만 연결합니다. 특정 은행이나 상품명 예외를 추가하지 않았습니다.
3. **반복 제목과 실제 각주 표현을 처리하지 못했습니다.**
   반응형/고정 메뉴에서 동일 H1이 반복되면 단일 상품의 가격 증거가 사라졌습니다.
   동일 제목만 중복 제거하고 서로 다른 제목은 계속 차단합니다. `data-target`
   같은 실제 로컬 각주 참조를 유일한 목표와 연결합니다. 누락/중복 목표를
   축약 인용으로 우회할 수 없습니다. U.S. savings의 `Interest Rate: 0.250%`
   선언도 연간 계산 각주 전체와 함께 보존합니다.
4. **금리표의 명시 단위와 상품별 행을 잃었습니다.**
   셀에는 `20.99`만 있고 열 머리에는 `Interest Rate [%]`, NOTES에는 연간
   기준이 있습니다. 상품명 또는 실제 상세 URL로 정확한 행을 연결하고 구매/
   현금 금리를 구분합니다. 전체 연체 조건(인상률, 적용 기간, 발생 기준,
   세 번째 명세 기간)을 보존하며 알려지지 않은 조건이나 추가 금리는 차단합니다.
   all-balances 예금 행도 정확한 인접 상품명과 연간 기준이 필요합니다.
   계층/패키지/조건부 행은 일반 금리로 바꾸지 않습니다.
5. **거래 정의와 통화의 소유 범위가 맞지 않았습니다.**
   `Point of Sale`을 숫자 표현의 `point`로 오인한 거래수 제한을 수정했습니다.
   실제 월 기본 거래수 정의와 초과 비용은 별개 사실로 검증합니다. 금융적으로
   검증되지 않은 선택 필드의 다른 상품/환전 문구는 본 상품의 통화 선언이
   될 수 없습니다. 검증된 본 상품의 전체 문맥과 명시 통화 충돌은 유지하며,
   명시 충돌이 있으면 국가 기본 통화로 돌아갈 수 없습니다. `ION`과 `ION+`
   이름도 구분합니다. 조건부/학생 한정 무료를 기본 무료로 읽는 문제를 회귀
   검사로 재현하고 함께 차단했습니다.

6. **승인·공개 단계도 상품명의 `+`를 지우고 있었습니다.**
   공개 후 독립 검증에서 승인 후보 15개가 서로 다른 상품 ID 14개로 연결된 것을
   발견했습니다. 수집 단계의 ION/ION+ 구분만으로는 부족했습니다. 공통 canonical
   매칭 SQL의 이름 비교와 단일 출처 상품 수 판정 모두 `+`를 `plus`로 보존하도록
   수정했습니다. 실제 production SQL을 격리된 SQL fixture에서 실행하는 검사로
   다른 은행/예금 이름, 기호·단어 동치, 다른 은행/유형/국가 및 단일 출처의 여러
   상품 경계를 수정 전 재현하고 수정 후 통과했습니다.
   이번 작업이 잘못 배정한 ION+ 승인 버전의 상품 연결만 별도 ID로 바로잡고,
   기존 ION ID와 정상 ION 승인 버전을 복구했습니다. 금융 payload, 승인 후보,
   승인 시각, 근거 링크는 그대로입니다. 정정 전 상태와 감사 이력을 보존하고
   rollback 검증 후 반영했습니다. 중복 승인 방지 제약과 자동 검증을 유지했습니다.

파서 v15, process `2026-10-07-owned-price-rate-proof-v6`, 실제 원점 조회,
공통 정확성/정규화 검사, 모델 지침 및 캐시 코드 해시를 함께 맞췄습니다.
필드 단위/JSON 타입, 국가/상품 유형, 승인 정책 버전 및 필수 비용·인출·담보
조건은 그대로입니다. 새 증거 템플릿은 은행명 분기 없이 적용되며 지원하지
않는 형태는 계속 제외합니다.

## 직접 확인해 자동 통과한 값

금리는 연간 퍼센트포인트, 돈은 상품 통화, 거래수는 정수입니다. U.S. High
Interest eSavings는 명시 USD이며 나머지는 CAD입니다. 명시되지 않은 통화에만
승인된 CA/CAD 기본값과 비공개 provenance를 적용합니다. 현금 금리와 계산 방법
같은 검증된 선택 필드는 보존하고 미확인 값은 생략합니다.

| 상품 | 검증된 핵심 값 |
|---|---|
| RBC U.S. High Interest eSavings account | monthly_fee=0.0 / standard_rate=0.25 |
| RBC Avion Visa Infinite | annual_fee=120.0 / purchase_interest_rate=20.99 / cash_advance_rate=22.99 |
| RBC British Airways Visa Infinite | annual_fee=165.0 / purchase_interest_rate=20.5 / cash_advance_rate=22.99 |
| RBC ION+ Visa | annual_fee=48.0 / purchase_interest_rate=20.99 / cash_advance_rate=22.99 |
| RBC Avion Visa Platinum | annual_fee=120.0 / purchase_interest_rate=20.99 / cash_advance_rate=22.99 |
| RBC Visa Platinum | annual_fee=0.0 / purchase_interest_rate=20.99 / cash_advance_rate=22.99 |
| RBC Avion Visa Infinite Privilege | annual_fee=399.0 / purchase_interest_rate=20.99 / cash_advance_rate=22.99 |
| WestJet RBC Mastercard | annual_fee=39.0 / purchase_interest_rate=20.99 / cash_advance_rate=22.99 |
| RBC Cash Back Mastercard | annual_fee=0.0 / purchase_interest_rate=21.99 / cash_advance_rate=22.99 |
| WestJet RBC World Elite Mastercard | annual_fee=139.0 / purchase_interest_rate=20.99 / cash_advance_rate=22.99 |
| RBC Cash Back Preferred World Elite Mastercard | annual_fee=120.0 / purchase_interest_rate=21.99 / cash_advance_rate=22.99 |
| RBC Visa Classic Low Rate Option | annual_fee=20.0 / purchase_interest_rate=12.99 / cash_advance_rate=14.99 |
| RBC ION Visa | annual_fee=0.0 / purchase_interest_rate=20.99 / cash_advance_rate=22.99 |
| moi RBC Visa | annual_fee=0.0 / purchase_interest_rate=20.99 / cash_advance_rate=22.99 |
| RBC Day to Day Banking Account | monthly_fee=4.0 / included_transactions=12 / additional_transaction_fee=1.25 |

원문 확인: [카드 금리표](https://www.rbcroyalbank.com/rates/cardprod.html),
[예금 금리표](https://www.rbcroyalbank.com/rates/persacct.html),
[Day to Day Banking](https://www.rbcroyalbank.com/bank-accounts/chequing-accounts/day-to-day-banking.html).
동적 원문은 위 링크의 현재 화면과 캡처 시각을 구분해 판단합니다.

## 제외를 유지한 이유와 한계

나머지 26개를 채우기 위해 값을 추정하거나 승인 조건을 바꾸지 않았습니다.
More Rewards 두 후보는 연결된 자료에서 구매 연간 금리를 입증하지 못했습니다.
기타 savings에는 계층별 금리 또는 NOMI/Find & Save, HISA/eSavings의 서로
다른 표기 연결이 남아 있습니다. 남은 chequing에는 조건부 면제, 누락/중복
참조 또는 다른 제목/상품 경계가 있습니다. 대출/LOC에는 수치 금리·기간 또는
담보 필수 사실의 증거가 부족하고 GIC는 비교 가능한 연간 금리/기간 및 인출
조건이 완전하지 않습니다. 이는 **이번 보존 입력과 범용 자동 규칙의 미입증**이며
공식 사이트에 정보가 없다는 단정이나 모든 가능한 상품을 조사했다는 주장이
아닙니다. 선택 필드만 채우기 위한 추가 검색/반복/사람 검토는 하지 않았습니다.

## 실행 결과와 검증

공식 현재 입력에 대한 수정 전 재현은 0/41 통과, 최종 재실행은 15/41 통과입니다.
직접 Run 여섯 개가 완료됐고 후보 41개 중 15개가 자동 승인, 26개가 자동 제외됐습니다.
사람 검토는 0개입니다. persisted origin 재검증과 자동 승인 rollback rehearsal을
통과한 후 정상 승인으로 15개 버전을 생성했습니다. ION/ION+ 연결 정정은 금융
버전을 추가하거나 사실을 덮어쓰지 않았습니다. 정상 집계 갱신 후 캐나다 공개
상품은 88→103개, RBC는 기존 1→16개입니다. 미국 5개는 유지됩니다.

카드의 현금서비스 금리는 canonical에 typed optional 값으로 보존됩니다. 현재
Public API는 전용 `cash_advance_rate` 키 대신 승인된 전체 카드 금리 요약으로
이 값을 제공합니다. 실제 상세에서 현금서비스 금리와 연체 인상 조건 전체를
확인하는 방식으로 검증합니다. 별도 키가 제공된다고 주장하지 않습니다.

최종 독립 읽기 검증은 2026-10-07 16:17:44 UTC에 완료됐습니다. 15개 상품의
현재 승인 근거 78개 필드가 실제 캡처·문자 위치·상품 소유권·금융 의미와 일치했고
정확성 영수증도 모두 유효합니다. Public API 목록/상세와 실제 15개 상품 페이지
HTTP 200, 상품명, 통화, 결정 필드 및 카드의 전체 금리·연체 조건을 확인했습니다.
기존 공개 상품의 금융 값과 미국 목록은 유지됐고 비공개 근거 노출은 없었습니다.
원래 Run 7개/후보 41개/소스 항목 65개, 은행 source document 100개와 snapshot
189개는 그대로입니다. 이번 승인 대상 외 canonical 435개 및 원래 금융 버전
1,472개의 사실을 보존했습니다. 이전 승인 버전 11개는 정상 supersession입니다.

공개 예: [Day to Day Banking](https://www.switchabank.com/products/prod_OOufeYwge3pa1496?country_code=CA),
[ION](https://www.switchabank.com/products/prod_L2OpkniEu28BduHX?country_code=CA),
[ION+](https://www.switchabank.com/products/prod_BdS3Ll1Ccv78I1Ax?country_code=CA).
실행 전·후 상태, raw capture, dry-run/rollback/정정 감사 및 검증 JSON은 비공개로
보존했습니다. 동일 바이트의 snapshot은 재사용했고 새 raw snapshot은 1개입니다.
현재 직접 캡처 시각/해시는 별도 영수증으로 보존하며 과거 값으로 채우지 않았습니다.

검증은 직접 주입한 금융값이 아니라 일반 캡처 파서 → 실제 900자 청크 →
저장 extraction artifact → 정상 원점 해석 → normalization/taxonomy/routing
→ 자동 승인 경로를 사용했습니다. 신규 실패 재현 후 회귀 검사를 추가했고
다른 은행 패널, 연간 기준 부정, 불완전/중복 각주, 폐지 상품, 조건부 무료,
채널 전용 무제한, 잘못된 통화 및 타 은행 원점을 확인했습니다. 새로운 전체
공식 캡처는 불투명 `.bin` fixture와 `-text` 속성으로 원문 해시를 보존해
HTML 텍스트 정리/줄바꿈 변환이 증거를 바꾸지 않도록 했습니다.

실행한 검사:

- 신규 원문/소유권/조건/렌더 검사 21개 통과. 파서·정확성 검사와 함께 실행한
  관련 검사 55개 통과. 일반 safe-fetch의 실제 자동 렌더 2개도 성공했습니다.
- canonical 기호 식별 신규 검사 5개 및 승인 관련 검사 56개 통과.
- 독립 API 환경 전체 639개 통과.
- Worker 전체 844개 중 842개 통과, 기존 National/Oaken HTML fixture 해시
  검사 2개 실패. 초기 작업 트리가 깨끗했고 해당 fixture/manifest를 이번
  변경에서 수정하지 않았습니다. 실제 fixture SHA-256과 기존 manifest 값이
  다릅니다. 이 차이를 숨기기 위해 기존 해시를 덮어쓰지 않았습니다. 신규 RBC
  원문 SHA-256은 전부 일치합니다. 전체 Worker 성공으로 보고하지 않습니다.
- foundation baseline, 변경 문서 링크/JSON/공백/UTF-8 및 소스 해시,
  최종 `git diff --check` 통과. 최종 목표와 diff를 검토했습니다.

기존 실패 위치는 `test_admin_collection_parity.test_source_fixture_hashes_and_priority_count`
및 `test_owned_deposit_tables.test_current_official_fixture_hashes`입니다.
운영 원문이나 승인 금융값의 손상을 뜻하는 결과는 아닙니다. 저장 fixture와
그 manifest의 무결성 실패이며 별도 보존 원문 검증이 필요합니다.

## 배포 경계

조회한 실제 `/healthz`는 정상이고 정확성 버전
`collection-accuracy-2026-10-01-cost-access`, profile `2026-10-01-v7`로
직접 승인 결과와 호환됩니다. 당시 serving process는 v5였습니다. 최신 원래
RBC 일괄 Run의 v4와도 다릅니다. 이번 v6 코드는 로컬에서 검증한 수정이며
일반 Admin의 다음 수집에 적용하려면 API/Worker의 정상 배포가 필요합니다.
이번 작업은 런타임을 배포/재시작하지 않았습니다. 직접 공개의 결과와 배포
상태를 구분합니다. 새 복구 메뉴/스케줄러, UI, 수동 검토 또는 BX-PF 쓰기를
추가하지 않았습니다.
