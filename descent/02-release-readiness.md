# FPDS Admin 인수 전 기술 점검

기준일: 2026-09-06 · 상태: 저장소 수정·로컬 검증 완료, 인수/Production GO 미승인

기준: [실행 가이드](README.md), [범위·담당자](01-scope-and-owners.md).
기준 branch는 main, 점검 시작 HEAD는 3f134d6이다. 이번 수정은 미커밋 작업 트리이며
전달 release tag가 아니다. 기존 사용자 변경과 삭제 파일을 보존했다.
Repository URL·의뢰자 organization·전달 commit/tag는 양측 확정 대기다.

## 1. 수정한 결함

| 항목 | 영향 | 수정 및 검증 |
|---|---|---|
| 로그아웃 CSRF 검사 누락 | 세션 종료 요청이 다른 쓰기와 동일한 보호를 받지 못함 | 활성 세션의 CSRF를 검사하고 잘못된 요청은 회수·cookie 삭제 전에 거부. 만료/무세션 종료는 멱등 유지. API 회귀 검증 |
| 로그아웃 실패를 성공처럼 처리 | 네트워크/API 실패 후에도 Login으로 이동해 세션 회수 여부를 오해 | 15초 timeout, CSRF 전달, 성공 때만 이동. EN/KO/JA 오류·재시도 표시. 브라우저에서 실패 유지와 성공 cookie 삭제 검증 |
| 외부 로그인 복귀 주소 허용 | next 값의 //host 또는 역슬래시 등으로 외부 이동 가능 | 같은 origin의 /admin 경계만 허용, locale·업무 query 유지. 외부/인코딩/잘못된 경로 테스트 |
| Dev/Prod 표시 오류 | 배포 방식으로 환경을 추정해 dev 연결도 Prod로 표시 | API session의 environment 사용. 구버전 API는 미확인 표시. production build + fixture dev 조합 검증 |
| Overview의 완료된 부분 실패 누락·중복 | completed partial을 조회하지 않고 failed partial은 중복 계산 가능 | 전체 기본 상태에서 failed OR partial을 한 번만 집계. 연결된 Runs에서도 completed를 제외하지 않음. 실제 집계 SQL의 혼합 상태·국가·빈 결과 회귀 검증 |
| Admin web 응답 보호 누락 | API에만 있는 헤더가 별도 web 문서를 보호하지 못함 | frame-ancestors/object/base 제한, X-Frame-Options DENY, nosniff, Referrer-Policy 적용. 배포 빌드 응답 검증 |
| 인수 API 테스트 실패 | Public 로고 구조 변경 후 이전 문자열을 검사하여 필수 suite 실패 | migration의 공식 로고·사용자 URL 보존 검증 유지. Public 컴포넌트 문자열 결합 제거. Public 자체 로고 회귀 3개는 전체 harness에서 통과 |
| 동작하지 않는 Account 메뉴 | 설정 화면이 있는 것으로 오인 | disabled placeholder 제거, 언어·로그아웃 유지 |
| 시작 문서 오류 | 없는 환경 예제·잘못된 middleware 경로 안내 | Admin .env.example 추가 및 README 경로·test 명령 수정 |
| 배포 비밀번호가 문서에 기록됨 | 전달 Git에 자격증명으로 명시된 값이 포함 | 현행 요구사항/보안 설계에서 값 제거. 실제 자격증명 교체·Git 과거 이력 검사는 아래 High 항목으로 유지 |

## 2. 화면과 기능 판정

| 화면/기능 | 판정 | 운영상 이유 |
|---|---|---|
| Login / Signup / Overview의 가입 승인 | 유지 | 국가 선택, 인증, 승인 전 접근 차단; 별도 가입 승인 화면을 추가할 필요 없음 |
| Overview | 유지·집계 수정 | 일일 실행 오류, 검토, 공개 데이터 상태, 가입 요청의 진입점 |
| Review / 상세 / AI verify / evidence | 유지 | 근거 확인과 승인·반려·보류·수정 승인. 원문과 UI 번역을 구분 |
| Runs / 상세 / retry | 유지 | 단계·source 오류 진단과 승인된 재시도. 과거 실패 기록 삭제는 부적절 |
| Banks / coverage / collection | 유지 | 은행 설정과 수동 collection의 단일 운영 진입점 |
| Sources / 상세 | 보조 도구로 유지 | 생성된 소스·수집 근거 진단. 수동 source CRUD 화면 추가 불필요 |
| Product Types | 관리자 보조 도구로 유지 | 수집 계약 설정. 새 유형의 안전한 공개를 자동 보장하지 않음 |
| Countries | 관리자 전용 유지 | 로그인 국가 활성/비활성. 현재·마지막 국가 보호 |
| Changes | 유지 | canonical 변경과 검토 결과의 업무 이력 |
| Public Health | 유지 | 공개 aggregate 생성 상태·실패 복구 진단. Public UI 인계와 별개 |
| 이전 bank/detail·source-catalog 화면 경로 | redirect 유지 | 기존 링크 호환. source-catalog mutation API는 Banks가 사용하므로 삭제하면 안 됨 |
| disabled Account 메뉴 | 제거 | 실행할 수 있는 기능이 없음 |
| 독립 Audit / Usage / 자동 예약 수집 | 복원하지 않음 | D-044/WBS 5.27 및 D-069/WBS 5.54의 명시적 제거 기준 |
| 계정 회수·비밀번호 복구 | 필수 운영 공백 | 아래 승인 대기 제안. 새 계정 관리 화면보다 제한된 DBA CLI로 먼저 충족 가능 |

## 3. 실행한 검증

모두 이 작업 트리의 기존 dependency 환경에서 실행했다. 깨끗한 clone이나 의뢰자
환경에서의 검증으로 기록하지 않는다.

| 명령/검증 | 실제 결과 |
|---|---|
| pnpm --dir app/admin run typecheck | 통과 |
| pnpm --dir app/admin run test | 5개 통과 |
| pnpm --dir app/admin run build | 최종 수정 포함 통과 |
| uv run --directory api/service python -m unittest discover -s tests -p 'test_*.py' | 최초 466개 중 1개 실패 → 수정 후 최종 474개 통과 |
| uv run python -m unittest discover -s worker -p 'test_*.py' | 527개 통과 |
| powershell -NoLogo -NoProfile -ExecutionPolicy Bypass -File scripts/harness/invoke-foundation-checks.ps1 | 통과. repo doctor·foundation·Admin typecheck/test/build·Public lint/typecheck/8 tests/build 포함 |
| 격리된 Chrome + 로컬 fixture API | EN/KO/JA × 정확한 390/768/1440px = 9개 조합 통과. 가로 넘침 0, 메뉴·오류·CSRF 전달·로그아웃 성공/cookie 삭제·Dev 표시·web header 확인 |
| git diff --check 및 최종 문서 검사 | 최종 문서 갱신 후 repo doctor와 git diff --check 통과 |

브라우저 검증은 실제 production build를 사용했지만 데이터와 계정은 합성 fixture다.
실제 금융 데이터·의뢰자 역할·국가 전환·collection/review mutation UAT를 대신하지 않는다.
로컬 재현 자료는 ignored tmp/admin-handover-browser.mjs와
 tmp/admin-handover-browser/report.json 및 ko-390.png/ko-1440.png에 있다.
Node 24.13.0에서 실행했으며 Admin 단위 테스트에는 기존 package의 module type
자동 판별 경고가 있으나 실패는 없다.

## 4. 전달 자료와 비밀값 검사

- 기본 포함: app/admin, Admin API, worker, 필요한 shared 코드, DB migrations,
  runtime lockfiles, 운영 문서. 전체 migration은 현재 0046까지이며, Admin-only라는
  이유로 공유 스키마 migration을 임의로 빼지 않는다.
- 제외: .env 실제값, .venv, node_modules, .next, tsbuildinfo, tmp, .vercel 연결 정보,
  개인 계정 파일, raw evidence, backup, 비공개 object URL/manifest, 불필요한 archive.
  최종 archive의 포함 목록은 기술 책임자와 인수자가 승인해야 한다.
- Git 추적 파일만 대상으로 private key/API key/credential DB URL/배포 비밀번호
  문구를 검사했다. 실제 환경 파일은 추적되지 않았다. 후보 5곳 중 3곳은
  테스트/예시 DB URL이고, 2곳은 배포 비밀번호 명시 문서였다. 후자는 값을 제거했다.
- 이 검사는 제한된 패턴 검사다. Git 전체 이력, LFS, 최종 전달 archive, private
  evidence 원문의 완전한 검사를 했다고 주장하지 않는다.

## 5. 남은 필수 항목과 NO-GO 조건

담당자는 기존 문서에 확정된 범위를 넘어서 임의 배정하지 않았다. 목표일이 미정인
항목은 이관 전에 Product Owner가 지정해야 한다.

| 우선도/상태 | 항목 | 필요한 조치·완료 근거 | 책임/목표 |
|---|---|---|---|
| High / 미완료 | 계정 lifecycle 공백 | 전달자/퇴사자 비활성화, 모든 세션 회수, 비밀번호 복구 수단 및 의뢰자 실습. 아래 CLI 구현 승인 또는 승인된 외부 IAM/DBA 절차 필요 | PO + 의뢰자 시스템·보안 책임자 / 이관 전 |
| High / 미완료 | Git에 명시됐던 배포 자격증명 | 보안 책임자가 실제 사용 여부를 확인하고 관련 비밀번호·세션 서명 secret을 교체해 기존 세션을 무효화. 전체 이력/전달 archive 검사 및 필요 시 승인된 이력 정리 | 의뢰자 보안 책임자 지정 필요 / 전달 전 |
| Release gate / 미완료 | 깨끗한 clone·고정 release | 의뢰자 소유 repo, commit/tag, frozen dependency 설치, 동일 검증 증거 | 기술 책임자 + PO / 이관 전 |
| Release gate / 미완료 | dev/prod 분리·worker host | R-007의 기존 shared-dev 예외를 고객 production 승인으로 사용하지 않음. 환경·DB·storage·credential·long-running worker host 확인 | 의뢰자 시스템 책임자 지정 필요 / 이관 전 |
| Release gate / 미완료 | migration/restore/rollback | 빈 DB 적용, migration history/drift 확인, backup restore·row/object/hash reconciliation, 실제 rollback 연습 | DBA + 시스템 책임자 지정 필요 / GO 전 |
| Release gate / 미완료 | 역할·보안·실데이터 UAT | admin/reviewer/read_only 거부, 만료/회수, 국가 격리, CSRF/CORS/SSRF, 실제 TLS/HSTS/Secure cookie, 장애 alert/escalation 실습 | 운영·시스템·보안 책임자 / GO 전 |
| Medium / 결정 대기 | 안정화 기간 문서 불일치 | README의 10영업일과 01-scope-and-owners의 한 달 중 계약상 기준 확정; 승인 없는 날짜 변경 없음 | 이근엽 + 황인협 / Step 1 승인 전 |
| Release gate / 미완료 | 운영 인수 승인 | 03/04/06/07/08 문서의 실제 환경·복구·교육·UAT·전환·종료 증거와 서명 | 양측 담당자 / 각 단계 전 |

현재 인수인계 완료 또는 Critical/High 0건을 선언할 수 없다. 코드 수정·로컬
검증 통과와 Production GO는 별개다.

## 6. 계정 관리 CLI 승인 대기 제안

자동 승인 검토가 계정 비활성화·전체 세션 회수·비밀번호 재설정 CLI의 코드 추가를
거절했다. 이유는 지속적인 특권 기능 추가이며 목표 파일에서 계정 변경을 제외했다는
것이다. 이번에는 실제 계정 작업 없이 코드·테스트만 추가하려 했으나, 해당 파일은
생성하지 않았고 명시적 승인을 요청한 상태다.

검토 가능한 구현 범위:

- 의뢰자 DB 접근권을 가진 시스템/DBA 전용 CLI. 공개 API나 새 Admin 화면 없음.
- inspect, revoke-sessions, disable, reset-password 네 동작. 기본값은 조회/preview.
- env-file과 expect-env를 필수로 받아 환경이 다르면 DB 연결 전에 중단.
- 쓰기는 apply와 승인/ticket 참조를 요구하고, 최종 active admin 비활성화 방지.
- password는 숨김 입력·재확인 후 scrypt로 저장하며 명령행 인수/출력에 남기지 않음.
- 비밀번호 복구와 비활성화는 해당 사용자의 모든 국가 세션을 같은 transaction에서 회수.
- disabled 계정을 비밀번호 복구로 다시 활성화하지 않음. DB 오류 시 전체 rollback.
- 무쓰기 preview, 대상/환경 오류, 마지막 admin, 비밀번호·회수·실패 회귀 테스트 포함.
- 실제 공유 dev/Production 계정 변경은 별도 승인된 운영 작업이며 이번 구현에 포함하지 않음.

## 7. 승인

- [ ] 기술 책임자: 전달 commit/tag와 검사 결과 승인
- [ ] Product Owner: 잔여 항목의 담당자·목표일·범위 승인
- [ ] 인수자: 알려진 제한사항 및 Step 2 결과 승인
