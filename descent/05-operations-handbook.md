# FPDS Admin 운영 핸드북 초안

상태: 2026-10-03 현행 상품수집 정책 반영. 의뢰자 환경·담당자·복구 증거 반영 전.
실제 URL, release tag, 지원 연락망, 환경 소유권은
[범위·담당자](01-scope-and-owners.md)와 [인수 준비 기록](02-release-readiness.md)에서
확정한다. 이 문서만으로 Production 전환을 승인하지 않는다.

## 1. 일일 운영

1. 승인된 환경 URL로 접속하고 업무 국가를 선택해 로그인한다. Header의 국가와
   Dev/Prod 표시를 확인한다. 미확인 표시는 정상 환경 확인으로 취급하지 않는다.
2. Overview에서 실행 확인 필요, 공개 데이터 상태, 가입 요청을 본다.
   확인 불가 값은 0건/정상으로 해석하지 않는다.
3. 상품수집은 자동 승인·제외로 끝난다. 필수 근거 부족은 자동 제외 사유로 확인하고,
   선택 정보 부족은 누락 상태로 유지한다. More tools의 Review는 과거 결정과
   evidence 조회용이며 수동 승인·수정·보류·AI 재검증을 제공하지 않는다.
4. Runs에서는 Search로 현재 상태를 조회하고 completed뿐 아니라 partial 표시를
   확인한다. 자동 새로고침은 없다. 상세에서 stage/source/자동 제외/오류를 확인한다.
   원인과 영향을 이해한 뒤 승인된
   범위만 retry한다. 반복 실패를 정상화하려고 과거 실행을 지우지 않는다.
5. Banks에서 은행별 coverage와 활성 Product Type을 확인한 뒤 필요한 항목만
   collection한다. 최초 수집은 상세 discovery가 필수다. 이미 완료된 범위는
   일반/상세 수집을 선택할 수 있다. 자동 예약 수집은 없다.
6. 종료 시 Account 메뉴에서 로그아웃한다. 오류가 뜨면 세션이 남았을 수 있으므로
   재시도하고, 지속 실패는 시스템 담당자에게 세션 회수를 요청한다.

## 2. 보조 도구와 역할

- Sources: 생성된 source와 상세 근거를 읽는 진단 도구. Banks의 coverage 설정을
  대체하는 수동 편집 화면이 아니다.
- Product Types: collection 계약을 관리하는 설정 도구. 새 유형 추가만으로
  수집 정확성이나 공개 자격이 생기지 않는다.
- Countries: admin 전용. 현재/마지막 활성 국가를 보호하며 비활성화는 역사 삭제가 아니다.
- Review history: 과거 검토 결정·근거의 읽기 전용 조회.
- Changes: 자동 승인과 canonical 변경의 업무 이력. 원문 evidence는 private 유지.
- Public Health: aggregate 최신 상태·실패 진단 및 권한 있는 재시도.
- admin은 설정·가입 승인·관리 작업을 맡고, reviewer는 과거 검토 이력과 관련 조회를,
  read_only는 조회를 맡는다. 버튼 비노출만으로 권한을 검증하지 말고 UAT에서
  서버의 거부도 확인한다.
- 국가 변경은 header에서 확인 후 진행하며 Overview로 돌아온다. URL query로
  국가 권한을 바꾸지 않는다. 언어는 Account 메뉴에서 EN/KO/JA로 바꾼다.
  상품명과 은행 원문·evidence는 번역된 UI와 다른 언어일 수 있다.

## 3. 설치와 실행

상세 기준은 [Admin](../app/admin/README.md), [API](../api/service/README.md),
[Worker](../worker/README.md), [DB](../db/README.md)를 따른다.
실제 secret·DB URL을 문서나 명령 기록에 붙여 넣지 않는다.

- 확정 tag의 새 clone에서 lockfile을 사용해 dependency를 설치한다.
- API 환경은 의뢰자 secret manager에서 주입한다. dev/prod DB와 private storage를
  분리하고 선택한 FPDS_ENV_FILE 및 FPDS_ENV를 확인한다.
- Admin의 .env.example을 로컬 설정 파일로 복사하고 FPDS_ADMIN_API_ORIGIN을 맞춘다.
  브라우저와 서버 양쪽에서 API에 접근 가능해야 하며 허용 origin과 cookie 정책을 확인한다.
- migration → API → long-running worker 실행 기반 → Admin 순서를 따른다.
  repository migration은 현재 0046까지다. 실제 적용 history는 별도 대조하고
  drift가 있으면 임의 SQL로 보정하지 않는다.
- 최초 admin은 기존 bootstrap_admin_user CLI를 사용하되 대상 환경과 계정 생성을
  승인한 뒤 실행한다. 비밀번호 인수를 생략해 숨김 입력을 사용한다.
- /healthz, 로그인, 역할, 국가, Overview/Review/Runs/Banks의 읽기 점검 후 승인된
  최소 collection/retry만 실행한다. API가 serverless인 것만으로 long-running
  collection을 지원한다고 가정하지 않는다.

저장소 root에서 로컬 개발 API를 시작하는 예:

```powershell
$env:FPDS_ENV_FILE = '.env.dev'
uv run --directory api/service uvicorn api_service.main:app --reload --host localhost --port 4000
```

Admin 개발 실행과 검증:

```powershell
cd app/admin
pnpm install --frozen-lockfile
pnpm run dev
# 별도 터미널에서
pnpm run typecheck
pnpm run test
pnpm run build
```

## 4. 오류와 중단 조건

| 증상 | 첫 확인 | 중단·escalation 기준 |
|---|---|---|
| 로그인 국가 목록/세션 조회 실패 | API health, 네트워크, 허용 origin, 환경 설정 | API 연결이 복구되지 않으면 인증 우회 금지 |
| 401 또는 만료 | 다시 로그인하고 국가 확인 | 회수 계정은 재생성/우회하지 않고 보안 담당자에게 요청 |
| 403/CSRF 거부 | 현재 세션으로 새로고침·재로그인, 역할 확인 | CSRF/RBAC를 꺼서 우회하지 않음 |
| collection partial/failed | run 상세의 stage/source/오류, 실제 지원 상품 범위 | 같은 원인의 반복 실패·DB/LLM 장애는 원인 해결 전 대량 retry 중지 |
| 수집 필수 근거 누락·모순 | Runs 자동 제외 사유와 공식 source/evidence | 수동 승인 우회 금지. 원인 해결 후 필요한 범위만 다시 수집 |
| Public Health 오래됨/실패 | aggregate 결과와 연결된 실행 | canonical을 직접 고쳐 숫자만 맞추지 않음 |
| 로그아웃 오류 | 재시도, API 상태 | 세션 회수가 확인될 때까지 정상 종료로 기록하지 않음 |

오류 보고에는 환경, 국가, 시간, run/review/request ID, 오류 종류, 영향 범위와
이미 한 조치를 기록한다. secret, credential URL, 원문 evidence는 일반 채널에 공유하지 않는다.
Monitoring provider, alert 수신자, on-call, 예산/quota는 의뢰자 환경 문서에서
확정하고 실제 장애 주입 또는 승인된 rehearsal로 알림 도달을 확인한다.

## 5. 계정·보안·복구

- Signup은 pending 요청이며 기존 admin 승인 전 로그인할 수 없다.
- 계정 비활성화·전체 세션 회수·비밀번호 복구의 실행 도구는
  [승인 대기 제안](02-release-readiness.md)에 있다. 현재 구현됐다고 교육하지 않는다.
  제공자의 계정 회수나 break-glass는 승인된 의뢰자 보안/DBA 절차와 실습 증거가 필요하다.
- 문서에 노출됐던 배포 자격증명의 실제 사용 여부를 확인하고 관련 비밀번호·세션
  서명 secret을 교체한다. 현행 문서에서 값을 지우는 것만으로 과거 이력/기존 세션이
  제거되지는 않는다.
- Cookie, CSRF, CORS, SSRF, private storage와 승인 경계를 유지한다. Admin web의
  frame 차단은 적용돼 있으나 Production TLS/HSTS/Secure cookie는 실제 배포에서 확인한다.
- backup은 암호화해 제한 저장소에 두고 참조 ID만 기록한다. 별도 DB/storage에서
  restore한 뒤 핵심 row/object count와 hash를 대조한다. backup 생성만으로 복구 완료가 아니다.
- 장애 시 새 쓰기를 중지하고 승인된 이전 release와 backup으로 rollback/restore한다.
  소유자·RPO/RTO·연락망·복구 명령·실습 결과는 실제 환경이 정해진 뒤
  04-data-migration-and-recovery 문서에 기록한다. 빈칸을 임의 값으로 채우지 않는다.

## 6. 교육 완료 조건

전달자 시연 후 인수자가 직접 자동 승인·제외 사유 확인, partial/failed 진단, 필요한 retry와
일일 점검을 수행한다. 시스템 담당자는 배포·계정 회수·복구 절차를 재현해야 한다.
결과는 06-training-and-uat 문서에 실행자·시간·증거·재검증과 함께 기록하고,
승인 전에는 교육/UAT 완료 체크를 하지 않는다.

## 7. 수집 중 저장소 정리

현재 수집이 사용하는 코드·설정·로그·증거·임시 파일과 프로세스를 유지한다.
문서 정리와 생성물의 Git 추적 제외는 로컬 파일을 보존한 상태에서 수행한다.
코드 재배치, dependency 설치, build와 프로세스 재시작은 별도 작업공간 또는
승인된 유지보수 시점에 수행한다. 전체 tmp·cache 폴더를 일괄 삭제하지 않는다.

현재 소스 전달 경계는 [범위·전달 목록](../00-Scope/scope.md)을 따른다.
