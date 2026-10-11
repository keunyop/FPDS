# U.S. Bank · Wells Fargo · Western Alliance 수집 진단과 직접 발행 — 2026-10-10

최근 일반 수집에서는 50개 후보 중 Wells Fargo Way2Save 1개만 승인됐다.
Admin 수집 API 없이 공식 원문을 직접 확인하고 공통 결함을 수정한 결과,
추가 10개가 일반 자동승인 기준을 통과했고 실제 Public 공개까지 검증했다.
코드 수정은 로컬 parser v28/process v19이며, 서비스 런타임 배포와 데이터
발행 결과를 구분한다. 이 작업에서 API/Worker 런타임을 배포하지 않았다.

## 최근 수집 결과와 직접 검증 결과

| 은행 | 최근 후보 | 최근 승인 / 제외 | 직접 검증 후보 | 추가 승인 / 제외 |
|---|---:|---:|---:|---:|
| U.S. Bank | 28 | 0 / 28 | 28 | 1 / 27 |
| Wells Fargo | 19 | 1 / 18 | 27 | 8 / 19 |
| Western Alliance | 3 | 0 / 3 | 3 | 1 / 2 |
| 합계 | 50 | 1 / 49 | 58 | 10 / 48 |

최근 실행은 2026-10-10 20:13 UTC batch의 13개 상품유형 실행이다.
이보다 오래된 상품유형별 최신 zero-target 실행 4개도 조사/보존했으나
새 상품유형으로 확대하지 않았다. Wells Fargo Mortgage는 필수정보 부족 판정
전에 DB 연결 종료로 실패하여 후보 0개였다. 보존된 성공 원문과 현재 동일
대상을 직접 처리해 8개 후보를 검사했지만 증명된 필수정보가 부족하여 제외했다.
연결 종료 자체는 이번 작업에서 재현되지 않았으며 영구 복구나 유료 재시도를
추가하지 않았다. Savings/GIC/Checking의 partial source 실패도 원래 이력에 남겼다.

## Admin에서 놓친 원인과 공통 수정

1. `Important credit terms`라는 실제 필수 가격 링크의 탐색 점수가 0이었다.
   공통 필수 공시 마커와 우선순위를 수정하여 기존 SSRF/도메인/예산/목적 제한
   아래에서 카드와 대출 모두 발견한다. 최대 detail당 2개/run당 48개는 유지한다.
2. `FPID`, `product_code`, `subproduct_code`가 추적 매개변수와 함께 제거되어
   다른 신청 오퍼가 같은 URL로 합쳐졌다. 가격/상품 정체성 쿼리를 보존하고,
   실제 detail 링크와 저장 원문의 연결 검증도 같은 정규화 함수를 사용한다.
   자격증명 URL, 비표준 포트, 상대 URL만의 출처, 다른 오퍼/은행은 거절한다.
3. 이름별 HTML 신청 공시의 여러 가격표와 뒤쪽 APR 계산/자격조건을 완전한
   하나의 금융 레코드로 읽지 못했다. 일치하는 원래 H1/H2, 전체 가격표,
   도입기간/이체기한, 계산방법, 정보 기준일, 자격조건, 지수/마진/상한을 모두
   보존한다. 일부 APR만 잘라내거나 열거된 대안을 단일 금리/범위로 바꾸지 않는다.
   연회비와 APR 모두 현재 원문 링크 및 같은 run의 저장 출처를 요구한다.
4. 완전한 명명 가격공시가 corroborate하는 한 단어 고유 상품명과 H1의
   화면낭독기용 중복 상표 문구가 이름 증명을 막았다. 원래 H1/SEO/URL/이름별
   가격공시 일치를 요구하면서 정확히 중복되는 숨김 상표 문구만 제거한다.
   Plus/Select/다른 상품 구분, 원래 언어, 다른 숨김 정보는 유지한다.
5. `Monthly service charge of $5 waived with ... direct deposit ... $500`을
   기본 월 수수료로 인식하지 못했고 direct deposit 근처의 금액을 보너스로 제거했다.
   완전한 단일 소유 문장에서 기본 수수료 USD5와 전체 면제조건을 구분한다.
   USD500을 비용/최저잔액으로 만들거나 면제 가능성을 기본비용 0으로 바꾸지 않는다.
6. 날짜가 명시된 개인대출 APR 범위와 고객별 상환기간이 지원 문장 형태에서
   빠졌다. 전체 소유 공시와 자격조건을 유지하고 원래 월 단위/비고객 제한을
   보존한다. 금리 한 값 또는 일수 환산을 만들지 않는다.
7. 이름별 카드 가격표의 `Foreign Currency Conversion/Foreign Transaction None`
   수수료 셀을 통화 미확인으로 오인했다. 해당 완전한 무수수료 셀만 수수료
   문맥으로 분류하며 실제 통화/외화금액/충돌은 유지한다. 승인된 US/USD,
   CA/CAD 미공개 통화 기본값 외의 추정은 추가하지 않는다.

모든 변경은 은행명/URL별 수락 예외 없이 공유 탐색·파서·추출·정규화·자동 검증에
적용했다. 공통 프롬프트/캐시 지문/파서 및 프로세스 버전도 함께 갱신했다.
신뢰도 점수나 수동 검토로 증거를 대체하지 않았다. 이번 개선은 확인한 증거
구조에 적용되며, 모든 은행/상품의 수집 완전성을 보장한다는 의미는 아니다.

## 실제 공개한 추가 상품

| 은행 | Public 상품 | 보존한 결정 정보 |
|---|---|---|
| USBN | [Personal Loan](https://www.switchabank.com/products/prod_QoTbIN5UR-R6equX?country_code=US) | APR 9.24%–24.99%; 12–84개월, 비고객 최대 60개월; 전체 자격조건 보존 |
| WFBN | [Active Cash ® Credit Card](https://www.switchabank.com/products/prod_Lp2VkDmKUbNhSynr?country_code=US) | 연회비 USD 0; 도입/정규 APR 대안과 전체 조건 보존 |
| WFBN | [Autograph ® Card](https://www.switchabank.com/products/prod_O6kjj5UGKAlaMiAN?country_code=US) | 연회비 USD 0; 도입/정규 APR 대안과 전체 조건 보존 |
| WFBN | [Choice Privileges® Mastercard®](https://www.switchabank.com/products/prod_q_hRZk6Qz7Q7mkFE?country_code=US) | 연회비 USD 0; 도입/정규 APR 대안과 전체 조건 보존 |
| WFBN | [Choice Privileges® Select Mastercard®](https://www.switchabank.com/products/prod_U7hAmuHMpqHUfg-b?country_code=US) | 연회비 USD 95; 도입/정규 APR 대안과 전체 조건 보존 |
| WFBN | [One Key ® Card](https://www.switchabank.com/products/prod_on3mQgfs_2El3xBv?country_code=US) | 연회비 USD 0; 도입/정규 APR 대안과 전체 조건 보존 |
| WFBN | [One Key+ ™ Card](https://www.switchabank.com/products/prod_20OyAliPPPGDx3V1?country_code=US) | 연회비 USD 99; 도입/정규 APR 대안과 전체 조건 보존 |
| WFBN | [Wells Fargo Autograph Journey℠ Card](https://www.switchabank.com/products/prod_sFnI8DweYhPacB_S?country_code=US) | 연회비 USD 95; 도입/정규 APR 대안과 전체 조건 보존 |
| WFBN | [Wells Fargo Reflect® Card](https://www.switchabank.com/products/prod_l-HtWbSWv2JGNXnT?country_code=US) | 연회비 USD 0; 도입/정규 APR 대안과 전체 조건 보존 |
| WAB | [Personal Checking](https://www.switchabank.com/products/prod_0ZhAq3ulH1cDwnYh?country_code=US) | 월 USD 5; 월 반복 direct deposit 1회 또는 일 잔액 USD 500 조건 면제; 일반 거래 무제한 |

가격은 이 작업의 현재 공식 캡처 기준이며, 원문의 조건과 기준일이 함께 공개된다.
카드의 최대 APR/우대 자격/도입기간/이체기한도 전체 요약에 남는다.
기존 Way2Save, Prime Checking, WAB Personal Interest Checking 등은 보존했다.
남은 48개는 현재 확보한 증거/처리 경로에서 필수정보를 증명하지 못해 자동 제외했다.
예금의 현재 연간 금리, Checking의 일반 거래비용(ATM 무제한과 구분), CD의
인출 접근성/결과, 대출의 기간/담보 조건 등을 빈 값이나 0/false로 채우지 않았다.
기존 상품을 과거 사실로 복원하지 않았다.

## 실제 검증과 보존

- 원래 snapshot 142개의 저장 바이트/체크섬을 확인했다. 현재 공식 URL 152개를
  직접 시도해 151개를 확보했고 1개 `/fetch-pdf`는 404였다. 처음의 기본 terms
  URL 캡처와 실제 관측한 오퍼 쿼리 캡처를 구분하여 보존했다. 추가 링크 수집은
  원래 detail에서 관측한 근거만 사용했다. 모델/유료 호출 및 Admin API 호출 0회.
- 최종 영향 Worker 346개, 독립 API 전체 650개, Discovery 85개 통과.
  21개 공식 원문 fixture의 SHA-256, 성공/누락/오퍼 충돌/다른 은행/조건부 0/
  미완성 공시/마스킹/통화 충돌을 검사했다. 8개 현재 카드 모두 실제 서비스 경로를
  거쳐 자동승인되는 회귀를 포함한다.
- 추가 최종 경계 수정 전 전체 Worker 938개 중 4개가 실패했다. 같은 네 실패를
  격리된 Git HEAD에서도 재현했다: admin-collection-parity와 owned-deposit-tables의
  fixture hash 각 1개, named-annual-records의 기존 카드 기대 2개. 기대값/과거
  원문을 변경해 숨기지 않았다. 이후 변경의 최종 영향 회귀 346개는 모두 통과했다.
- 실제 DB의 현재 run/snapshot/parse 연결로 정규화·검증을 다시 실행했다.
  첫 승격 리허설은 작업 스크립트가 새 오퍼 detail을 supporting 역할로
  저장한 오류를 차단했다. 공개 상태 불변을 확인하고 이번 작업의 새 문서만
  실제 등록 detail 역할로 정정했으며 기존 문서/금융 사실은 건드리지 않았다.
  표준 자동승격의 트랜잭션 rollback 후 canonical/version/refresh가 복구되는지
  확인하고 같은 승격 함수를 커밋했다. review queue/수동 승인 0개.
- 저장한 원문/전체 parse 66쌍을 실제 private 저장소에서 재조회하여 일치 확인했다.
  발행한 52개 필드 출처/링크 및 승인 receipt를 확인했다.
- 실제 anonymous API의 US 전체 목록/상세, CA 목록, 각 상품의 Public 사이트
  HTTP200와 전체 금융조건 표시를 검사했다. 비공개 evidence/스토리지/필드 매핑은
  공개되지 않았다. US Public 75 → 85, CA 120개 유지.
- 원래 실행 17개/후보 50개/source join 153개,
  원래 문서 201개/snapshot 421개,
  이전 version 사실 1598개 및 영향 없는 canonical 484개를 보존했다.
- 최종 Python 문법/UTF-8/fixture JSON/문서 참조 및 `git diff --check`를 확인했다.
  기존 다른 작업의 수정과 미완료 goal은 보존했다. 영구 복구 기능/메뉴/스케줄러,
  스키마 변경 또는 외부 연동을 추가하지 않았다.

운영 재현 자료는 ignored `tmp/us-last-three-20261010/`와 같은 환경의 private
operation artifact에 보존했다. 다음 런타임 작업은 API/Worker v19의 조정 배포와
한정된 smoke 검증이다. 공개 데이터 10개와 런타임 배포 상태를 혼동하지 않는다.
