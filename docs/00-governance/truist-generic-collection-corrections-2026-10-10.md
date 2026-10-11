# Truist 직접 수집 및 범용 공시 처리 개선 — 2026-10-10

## 확인 범위와 기존 결과

FPDS Admin API를 사용하지 않고 기존 개발 환경 DB를 읽고 보존된 공식 원본을
확인했다. 최신 Truist 5개 유형 Run은 모두 completed였다. 후보 22개 중 1개
Travel rewards credit card가 승인됐고 21개가 탈락했다. 성공한 원본 연결은 54개,
중복을 제거한 선택 원본 52개의 보존 바이트와 체크섬을 검증했다.
기존 Run은 process v16이었다. 조사 시점의 serving은 v17이다.

현재 등록된 공식 Truist URL 52개를 안전한 HTTP 경로로 새로 가져왔다. 브라우저
유료 대체 경로, LLM, Admin API 호출은 없었다. 원본, SHA-256, 조회 시각과
파싱 결과를 보존하고 동일한 최신 입력을 반복 검증에 재사용했다. CD 등 이번
Run에 없는 유형을 임의로 추가하지 않았다.

## 왜 자동수집에서 놓쳤는가

1. 상품 페이지 H1이 마케팅 문구였다. 실제 상품명은 본문 H2 및 상품명을 명시한
   공시에 있었다. 기존 추출기는 이를 독립적으로 증명한 상품명으로 연결하지 못했다.
2. HTML 가격 공시가 여러 표와 문단으로 나뉘어 있었다. APR 범위뿐 아니라 소개
   기간 이후 조건, Prime Rate, 산정 방법, 수수료·면제 각주를 함께 보존해야 하지만
   기존 일반 청크만으로 완전한 조건의 근거를 만들지 못했다.
3. `**`, `***`가 명시적으로 정의된 공시 각주인데도 공유 정규화·금리 게이트는
   미확정 가격 마스크로 판단했다. 단순히 검증을 느슨하게 해서는 해결할 수 없다.

4. 정상 공개 후 재조회에서 최소 수집 필드 allowlist가 검증된 면제 조건을 Public
   metadata에서 제거하는 문제도 재현했다. canonical 보존만으로 완료 처리하지 않고
   공유 projection에서 검증된 가격 면제 조건을 유지하도록 수정했다.

같은 공식 입력으로 회귀 실패를 재현한 뒤 파서→추출→정규화→검증을 수정하고
재검증했다. 상품별 승인 예외나 신뢰도 우회는 추가하지 않았다.

## 범용 변경과 거부 경계

- 이름을 명시한 HTML 신용카드 공시를 완전한 atomic record로 보존한다. 공시
  종료 revision, 필수 가격 항목, 변수 금리 및 모든 고유 각주 정의가 필요하다.
  누락·중복·불일치·8,000자 초과 공시는 거부한다.
- 마케팅 H1 아래 H2 상품명은 동일 캡처의 SEO 제목, URL 경로, 발행기관 도메인,
  해당 상품의 완전한 공시가 유일하게 일치할 때만 채택한다. 메타데이터나 다른
  snapshot만으로 상품명을 만들지 않는다.
- 정의가 증명된 별표만 서식으로 처리하고 각주 전체 문장은 그대로 유지한다.
  `$***`, `X.XX%`, 미해결 템플릿은 계속 거부한다. 이 구분은 공유 금융 게이트에
  적용된다. 미래에 다른 유형도 같은 완전한 근거 구조를 제공하면 사용할 수 있다.
- 독립적인 Annual Fee None만 무조건 0으로 인정한다. 양수 기본 연회비와 면제
  조건은 함께 보존하고, 증명된 typed optional `fee_waiver_condition`도 저장한다.
- 모델 프롬프트, parser v27/process v18, 소유권·완전한 인용 검증을 함께 변경했다.
  기존 금액 단위, 필수 필드, 예산, 현재 선택 원본, 보안, 자동승인 규칙은 유지한다.

은행명을 다른 발행기관으로 바꾼 원본 구조의 회귀와 다른 계좌 유형의 기존 검증도
통과해야 한다. 범용은 모든 미지원 금융 구조를 자동으로 받아들인다는 뜻이 아니다.

## 나머지 후보가 공개되지 않은 이유

| 유형 | 확인한 한계 |
| --- | --- |
| Savings | 실제 공식 수수료·잔액별 0.01% 표가 있다. 일반 Disclosure Information 제목과 구간별 이율을 무제한 단일 금리로 오인하면 안 된다. 현재 정확한 상품 소유권/금리 경계의 필수 근거를 완성하지 못해 제외했다. |
| Checking | 월 수수료 및 ATM 비용은 확인되지만 ATM 무제한을 전체 거래 무제한으로 바꿀 수 없다. 일반 거래비용 필수 증명이 부족하다. |
| Personal loan | 자동차 페이지는 secured auto loan과 LightStream unsecured loan을 비교한다. 실제 유담보 APR 범위와 미해결 다른 상품 템플릿을 하나의 상품에 합칠 수 없다. Marine에도 금리는 있으나 실제 후보의 전체 금리/기간 필수 증명은 미완성이다. |
| Mortgage | 확보된 페이지의 25%·3.5%·0%는 down payment 조건 등이며 mortgage 금리가 아니다. 현재 상품별 실제 금리/유형/기간 근거가 부족하다. |
| Travel card | 기존 승인·공개 상품은 그대로 보존했다. 이번 모델 없는 직접 경로에서는 마케팅 명칭과 정식 공시명 연결을 완성하지 못해 새 버전을 만들지 않았다. 기존 승인을 재현했다고 주장하지 않는다. |

공식 자료에 사실이 전혀 없었다는 결론은 아니다. 상품 경계·조건을 입증하는 별도의
범용 지원이 필요한 후보가 남아 있다. 이번에 확인한 두 카드의 결함은 정상 자동
검증으로 재현·해결했고, 나머지는 추정하거나 과거 값으로 채우지 않았다.

## 실행·공개·검증 결과

최종 직접 처리 후보는 22개, 자동승인 2개, 제외 20개였다. 제외에는 기존 공개
Travel의 새 버전도 포함된다. 기존 Travel 승인·공개는 그대로 유지했다.

| 추가 공개 상품 | 연회비 | 금리 조건 |
| --- | --- | --- |
| [Truist Enjoy Beyond credit card](https://www.switchabank.com/products/prod_LUa_P6ql29vawnTQ?country_code=US) | USD 95, 전체 Wealth 고객 면제 조건 별도 보존 | 구매 APR 18.74%–27.74%, 신용도·Prime Rate·변경 조건을 전체 공시로 보존 |
| [Truist Future credit card](https://www.switchabank.com/products/prod_JKONJLB6cA8tSVNM?country_code=US) | USD 0 | 15개월 소개 APR 0%, 이후 16.74%–25.74%; balance transfer의 계좌개설 후 90일 조건 및 변동 조건 전체 보존 |

위 표는 공시의 요약이다. 저장·공개한 값은 모든 가격·면제·계산·신용승인 조건을
포함한 원문 summary이며, 범위 끝점이나 소개 금리를 비교용 scalar로 만들지 않았다.

- 정상 extraction artifact → normalization → validation과 DB에서 선택한 실제
  snapshot/parse origins 결과가 일치했다. 정상 자동승인을 실제 transaction에서
  실행하고 rollback하여 canonical/version/refresh 원복을 확인한 후 승인했다.
- Public 갱신 완료 후 검증된 optional 면제 조건의 projection 누락을 발견해 수정했다.
  정상 Public refresh 서비스로 재생성하고 API 및 실제 상세 페이지를 재검증했다.
  승인이나 canonical 값은 재작성하지 않았다.
- 실제 private storage의 22개 raw/parse pair와 공개 필드 origin 7개를 재조회했다.
  체크섬, chunk offset, 정확한 인용, 동일 은행·국가, 현재 선택 원본, 상품 소유권,
  정책 receipt가 통과했다. Public API와 실제 상세 HTTP 200에서 전체 조건과
  typed 면제 조건을 확인했다. private evidence는 노출하지 않았다.
- Truist 공개 1 → 3개, US 공개 72 → 74개, CA 120개 유지. 기존 5 Runs,
  22 candidates, 54 source joins, 80 documents, 158 snapshots와 1,595 version
  facts 및 기존 canonical 483개를 보존했다. 무관한 다른 은행 실행을 중단하지 않았다.
- 수동 상품승인·review task·LLM/provider·Admin API 호출은 0회다.

실제 검증: 최종 affected Worker 474개, 독립 API 전체 650개, 마지막 projection
수정 이후 독립 aggregate/Public API 20개 통과. Worker 전체 927개 실행에서는
4개 기존 실패가 있었다. admin-collection-parity 및 owned-deposit-tables fixture
hash 2개, named-annual-records의 카드 금리 기대 2개이며, 격리된 Git HEAD
스냅샷에서도 같은 4개 테스트가 실패했다. fixture 기대 해시나 기존 사실을 고쳐
숨기지 않았다. 최종 optional/projection 수정은 위 affected 474개로 재검증했다.
Foundation baseline, 최종 Python/JSON/UTF-8/로컬 참조 및 git diff --check를 확인했다.
분리 API 명령은 repo root를 PYTHONPATH에 지정해야 하며, PowerShell stderr
래핑의 exit code 대신 unittest의 실제 Ran/OK 및 실패 내용을 함께 확인했다.

로컬 코드는 parser v27/process v18이다. serving health는 v17이며 런타임 배포는
수행하지 않았다. 데이터 공개 완료와 향후 일반 Admin 수집 런타임 적용을 구분한다.
다음 동기화 배포에서는 API/Worker v18을 함께 적용하고 현재 health 계약과
bounded collection smoke를 확인해야 한다. DB migration이나 새 스케줄러는 없다.
개별 원본·로그·증거 연결은 비공개 `tmp/truist-20261010`과 작업별 private storage에
보존한다. 일회성 운영 스크립트는 제품 메뉴나 스케줄러로 추가하지 않는다.
