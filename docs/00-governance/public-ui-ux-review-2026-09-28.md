# SwitchaBank Public UI/UX review — 2026-09-28

## 범위

Home, 예금·카드·대출 목록, 상품 상세, 비교, 계산기, 가이드, Methodology와
공통 탐색을 검토했다. 기존의 차분한 색상, 금융 정보, 상품 검증 상태와
EN/KO/JA 지원을 유지하면서 발견된 사용성 문제를 수정했다.

## 발견 사항과 개선

| 확인한 문제 | 적용한 개선 |
|---|---|
| 검색창이 접힌 검색조건 안에 있어 바로 검색하기 어려움 | 검색창을 항상 노출하고 상세 조건만 접기 |
| 긴 목록 제목과 반복 안내로 실제 상품이 아래로 밀림 | 짧은 상품군 제목과 간결한 상단 여백 |
| 검색 결과 갱신 시 입력 노드가 교체되어 포커스가 사라짐 | 입력 노드를 유지하고 URL 변경과 값 동기화 |
| 체크박스·선택 상자 갱신 및 마지막 필터 해제 때 포커스 소실 | 안정적인 입력 노드와 사용자가 정한 패널 펼침 상태 유지 |
| 한·일 조합 입력 중 검색이 실행될 수 있음 | 조합 완료 후 검색, 갱신 중 작은 진행 표시 |
| 긴 검색어 칩이 모바일 폭을 넘길 수 있음 | 칩 내부 줄바꿈과 닫기 아이콘 공간 확보 |
| 모바일 정렬 영역 밖에 Grid/List 버튼이 가려짐, 버튼이 40px | 정렬 영역만 스크롤하고 전환 버튼을 고정 노출, 44px로 확대 |
| 태블릿 메뉴 아이콘에 접근 가능한 이름이 없음 | 1024px 미만은 이름이 보이는 메뉴, 데스크톱에는 이름·현재 페이지 속성 |
| 반복 내비게이션을 건너뛸 키보드 경로가 없음 | 현지화된 본문 바로가기와 포커스 대상 |
| Home 상품 선택이 방향키/Enter 조작을 지원하지 않음 | 방향키 선택, Enter 확정, Escape/Tab 닫기, 활성 항목 안내 |
| Home 검색보다 선택 필터가 먼저 보여 필수 입력처럼 읽힘 | 상품 검색을 먼저 배치하고 선택 필터를 한 줄로 묶음 |

불필요한 안내 문구를 추가하지 않았다. 금융 조건·검증 만료 표시와 필수
정보 고지는 유지한다. 비교 목록, 저장, 계산, 공식 은행 이동과 기존 URL
상태를 변경하지 않았다. API, Worker, FPDS Admin 및 정본 데이터는 수정하지
않았다. 기존 사용자 변경과 별도 미완료 목표는 보존한다.

## Verification

- Public: 74 tests, lint, standalone typecheck and production build passed.
- Production-build browser audit: 111 checks passed across EN/KO/JA
  and exact 390/768/1440px, including focus, IME, back/forward, suggestions,
  skip navigation, visible 44px view controls and nine existing routes.
- 18 additional flow/state checks passed: comparison selection/save/delete,
  sorting/view persistence, calculator privacy, official-bank popup/event,
  dialog/menu/dock coexistence, locale/country switching, long search, finder
  loading/empty/error/retry, catalog failures/retry, guides and Public Admin.
- Reviewed final Home/catalog screenshots in all three languages. No document
  overflow, browser exception or hydration warning was observed in the checks.
- Replayed previously read approved Public records and controlled local fixtures;
  no new bank-source verification, production data mutation or deployment.
- Repository doctor and final diff hygiene results are recorded in the journal.

The reusable audit is [ui-ux-audit.py](../../app/public/scripts/ui-ux-audit.py);
commands and prerequisites are in [Public README](../../app/public/README.md).

## 남은 경계

이 점검은 실제 기기 전체나 모든 브라우저에서의 무결함을 보증하지 않는다.
배포 및 실제 이용자 관찰은 별도 단계다. 과거 공개 데이터를 재생한 결과를
최신 은행 조건 재확인으로 해석하지 않는다.
