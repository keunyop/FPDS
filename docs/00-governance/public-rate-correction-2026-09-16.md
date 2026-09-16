# Public 금리 의미 정정 및 자체 승인 — 2026-09-16

## 요청과 승인 범위

성장 제안서의 **전체 금리와 가산금리 혼동** 항목만 구현한다. 사용자는
기존 공개 데이터 정정과 화면/API 변경을 분리하여 자체 검증·승인하도록
명시했다. 성장 기능, 자동 수집 재개, freshness 정책, 국가·상품 확장과
애플리케이션 배포는 이 변경에 포함하지 않는다.

| 범위 | 자체 검토 결정 | 근거 |
|---|---|---|
| API / Public 코드 | 승인 | 원문 보존, 동일한 비교 금리 규칙, 전체 API 회귀 검사 및 실제 UI 확인 |
| 기존 BMO 데이터 | 쓰기 불필요 | 저장된 전체 금리는 null이고 원문에 Prime plus 0.5%가 남아 있다. 오류는 조회 시 파생되는 수치이다. |
| 기존 Vancity 데이터 1건 | 정정 승인 | 승인 후보의 공식 URL과 기존 버전·수치가 일치하고 공식 상품 표는 Prime + 0.75%를 명시한다. 전체 트랜잭션 시험 후 롤백, 타 상품 227행 불변 확인. |
| 기타 canonical 데이터 | 변경 없음 | 분류 결과만으로 원본 사실을 수정하거나 추정하지 않는다. |

## 공식 근거

- [BMO Professional Student Line of Credit](https://www.bmo.com/en-ca/main/personal/loans-line-of-credit/student-borrowing/professional-student-line-of-credit/):
  전공별 Prime 가산·차감 조건이 있으므로 0.5%를 전체 대출 금리로 읽을 수 없다.
- [Vancity Planet-Wise home renovation loan](https://www.vancity.com/borrow/loans-lines-of-credit/planet-wise-renovation):
  term loan의 조건은 **Vancity Prime + 0.75%**이다. 리노베이션 자격 조건과
  수수료가 없는 APR 가정을 유지한다. 페이지의 기준금리를 더하여 전체 금리를
  생성하지 않는다.

## 코드 변경과 공개 데이터 영향 감사

`public_rates.py`가 리스트·상세·정렬·대시보드의 금리 판단을 공유한다.
`rate.kind`는 absolute / range / reference / conditional / promotional /
unknown이며, 전체 수치가 확정된 absolute만 `comparable_rate`를 가진다.
기존 `public_display_rate`, `card_display_rate` 응답도 안전한 수치 또는 null로
반환한다. 저장된 projection이나 canonical을 API 조회가 수정하지 않는다.

- 문장형 plus/minus, 기호 및 유니코드 가산·차감, Prime/SOFR 등 기준금리,
  margin/spread, 금리 범위, 우대·프로모션, 스트레스 테스트 수치를 구분한다.
- 범위의 최저값, introductory 0%, 전제 조건이 있는 예시와 충돌하는 수치를
  순위·차이 계산에서 제외한다. 정상적인 전체 금리 0%는 유지한다.
- 여러 기간의 금리표는 그대로 표시하며 단일 수치로 축약하지 않는다.
- 일반적인 예금보험 한도나 배수 마케팅 문구를 금리 조건으로 오인하지 않는다.
- EN/KO/JA 유형 라벨과 원문 조건을 표시한다. 홈·finder·예상 이자·SEO도
  같은 비교 가능 값만 사용한다. 기존 수수료 비교는 유지한다.
- 금리 계약이 없는 구버전 캐시 응답은 프런트엔드에서 수치 비교를 하지 않는다.

수정 전 익명 공개 API 216건(CA 165 / US 51)을 저장하여 재생한 결과:

| 분류 | 건수 |
|---|---:|
| 비교 가능한 전체 금리 | 101 |
| 범위 / 기간별 금리 | 28 |
| 기준금리 가산·차감 | 6 |
| 조건부 / 충돌하는 금리 | 24 |
| 프로모션 | 10 |
| 수치 미공개 / 불확실 | 47 |

기존 숫자 비교값 **64건**이 null로 바뀐다(예금 상품 GIC 11·Savings 10,
신용카드 21, Mortgage 8·Personal Loan 10·Line of Credit 4). 상품을 삭제하는
것이 아니라 수치 비교에서 제외하고 조건을 표시하는 의도된 변경이다.
별도 Vancity 정정 후에는 추가 1건이 전체 금리에서 기준금리 가산식으로 바뀐다.
이 감사는 공개 자료의 의미 검사이며 모든 은행의 최신 금리를 재수집·보증한
것은 아니다. 구조화된 숫자만 남은 과거 데이터의 모든 오분류를 문장 분석으로
발견할 수 없으므로, 확인된 데이터 정정을 별도로 기록한다.

## Vancity 정정 절차와 보존

대상: `prod_dGBpyMydkwGWu30L`, CA / VANCITY / personal-loan, 승인 버전 1.

- `interest_rate: 0.75`를 null로 정정하고 출처 조건을 담은
  `interest_rate_summary`를 기록한다.
- 기존 승인 버전을 보존하고 새 버전과 `ManualOverride` change event를 만든다.
  이벤트에 사용자 승인 근거, 공식 URL, 확인한 사실, before/after를 기록한다.
- 최신 CA 스냅샷을 복제하고 대상 상품만 정정한다. 기존 스냅샷과 나머지
  227행은 보존한다. 출처 확인 시점 전체가 갱신된 것처럼 보이지 않도록 원래
  `refreshed_at`, source cutoff와 다른 상품의 검증일을 보존한다.
- 버전·기존 수치·공식 URL·상품 식별자 검사, 직렬화 트랜잭션, 잠금 제한,
  전체 diff/count 검사를 통과해야 커밋한다. 중복 실행은 no-op이다.
- [정정 스크립트](../../scripts/maintenance/correct_reference_rate_20260916.py)는
  기본 실행 시 실제 트랜잭션을 검증 후 롤백한다. `--apply`만 커밋한다.

정정 커밋 완료:

- 새 버전: `pver_f9553132696b4377860371a1fd77596c` (version 2)
- change event: `chg_c4802d710e4e403abd1df44635d8db40`
- 새 CA 스냅샷: `agg_ratefix_d4eb3c61663f48b692233d1f140062dc`
- 이전 스냅샷: `agg_lpF9eFd6M8w3rtBM` (원본 보존)
- 이전 `refreshed_at`: `2026-08-27 07:43:32.488463+00:00` 유지
- 커밋 후 재실행 `already_applied`, 변경 없음.
- 커밋 후 읽기 전용 확인: CA active 165 / US active 51, 기존 버전 1
  superseded / 새 버전 2 approved, 원래 스냅샷의 0.75 보존, 공식 링크 유지.
- 실제 익명 공개 응답에서도 Vancity `public_display_rate`와
  `card_display_rate`가 null이고 조건을 담은 Prime + 0.75% 원문이 반환됨.

## 최종 검증

- API 전체 unittest **481개 통과**, 신규 의미 분류 및 정렬·대시보드 회귀 포함.
- Public Node 테스트 **12개 통과**, lint / typecheck / production build 통과.
- Chromium 실제 데이터 **19개 시나리오 통과**: BMO catalog 3개 언어 ×
  3개 폭(1440/768/390), 3개 언어 상세, Home/finder 비교 제외,
  프로모션 기간, 범위 양 끝값, 기존 연회비 비교, 비교 선택, 오류 후 재시도,
  빈 검색. JavaScript 예외와 document 가로 넘침 없음. 한국어 390px
  스크린샷도 직접 확인했다. 분석 수집은 차단했고 로컬 API DB는 읽기 전용이었다.
- Repo doctor / foundation baseline / `git diff --check` 통과.
- 위 검증은 로컬 변경 코드와 현재 공개 데이터에 대한 결과이다. 새 API/Public
  코드의 운영 배포 및 배포 후 검증은 수행하지 않았다.

## 배포와 복구

API 먼저 배포한 후 Public을 배포하고 기존 캐시 TTL 만료를 확인한다.
현재 변경은 애플리케이션 배포를 수행하지 않는다. 구버전 UI는 안전하게
null을 표시할 수 있지만 새 유형 라벨은 새 Public 배포 이후 제공된다.

데이터 정정 복구는 change event의 previous version/snapshot과 before 값을
근거로 별도 감사되는 새 정정을 생성한다. 이전 이력이나 스냅샷을 삭제하지
않는다. 코드만 되돌리면 예전 가산율 추출 오류가 다시 발생할 수 있으므로
데이터 정정과 코드 배포를 별개로 관리한다.
