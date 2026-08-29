# FPDS Admin 인수인계 범위

## 목적

인수 대상은 FPDS Admin과 Admin 운영에 직접 필요한 내부 구성요소로 한정합니다. 이 문서는 인수자가 현재 운영 범위와 책임 경계를 빠르게 확인하기 위한 요약입니다.

## 인계 범위

- **Admin 화면**: 국가별 은행·수집 범위 관리, 수집 실행과 실패 진단, Review Queue의 근거 확인 및 승인·수정승인·거절·보류, 변경 이력 확인
- **Admin 데이터 처리**: 공식 출처 발견, 스냅샷, 파싱·추출·정규화·검증, 후보 검토와 canonical 반영
- **Admin 운영 기반**: EN/KO/JA, 인증·권한·세션·CSRF·SSRF 방어, Admin API, DB migration, worker 운영
- 대상 국가와 상품은 등록되고 승인된 활성 프로필 범위만 포함합니다.


## 인계 산출물과 완료 기준

- Admin 소스, 관련 API·worker·migration, 운영 문서, 환경변수 예시, 검증 명령은 저장소에서 관리합니다.
- Admin은 인증·국가 경계를 지키며 수집→검토→변경 이력 흐름이 동작해야 합니다.
- 원본 evidence, 운영 메모, 비밀값은 Admin의 인증·권한 경계 안에서만 취급해야 합니다.


## 인수자 확인 사항

1. 배포 환경의 DB·스토리지·API·worker 상태와 백업/복구 절차를 확인합니다.
2. 운영 계정, 비밀값, 외부 AI 자격 증명은 저장소 밖의 승인된 채널로 이전합니다.

## 인수인계 제공 파일

### 저장소에 포함하는 파일

| 제공 항목 | 파일 위치 | 용도 |
|---|---|---|
| 인수 범위와 최종 체크리스트 | 00-Scope/scope.md | 인수 범위, 제외 범위, 완료 판정 |
| 외부 서비스 목록·계정 기입 템플릿 | 00-Scope/external-services-and-accounts.md | cloud, DB, storage, domain, DNS, TLS, LLM, monitoring의 현재 상태와 계정 양식 |
| DB migration·schema·ERD | 00-Scope/database-migrations-schema-erd.md | 0001~0044 목록, shared dev 적용 상태, schema dictionary, ERD |
| 전체 실행 순서 | docs/01-planning/fpds-admin-handover-minimum-playbook.md | 환경 준비, rehearsal, 교육, UAT, Cutover, Hypercare |
| 환경변수 계약 | .env.dev.example, .env.prod.example | placeholder-only dev/prod 설정 목록 |
| Admin web 운영 경계 | app/admin/README.md | 화면, route/code map, build 명령, 안전 경계 |
| Admin API 운영 경계 | api/service/README.md | API, auth, Vercel Public-read 예외, test/실행 방법 |
| Worker 운영 경계 | worker/README.md | collection/pipeline 경계와 runtime invariant |
| DB 원본 migration | db/migrations/, db/README.md | SQL 원본과 적용 순서 |
| Private storage 계약 | storage/README.md, docs/03-design/object-storage-evidence-bucket-baseline.md | bucket/key/access 경계 |
| Monitoring 계약 | shared/observability/README.md, docs/03-design/monitoring-error-tracking-baseline.md | log, error, redaction, provider 준비 기준 |

### Git에 넣지 않고 제한 저장소로 받아야 하는 파일

실제 계정, backup, UAT와 서명 증거는 의뢰자 소유
FPDS-Admin-Handover/ 아래에 보관합니다.

| 위치 | 받아야 할 파일 |
|---|---|
| 02-Environment-And-Access/ | 01-client-ownership-matrix.xlsx, 02-environment-readiness.pdf, 03-topology-and-monitoring.pdf |
| 03-Data-And-Recovery/ | migration history, schema-only dump, schema diff, encrypted backup manifest, restore/reconciliation, rollback report, test log |
| 04-Manuals-And-Training/ | 운영 매뉴얼 5종, 교육 참석, recording link, operator practice 결과 |
| 05-UAT/ | UAT 결과, defect register, UAT 승인 |
| 06-Cutover/ | GO/NO-GO, cutover log, production smoke, access/secret rotation, 인수 승인 |
| 07-Hypercare/ | issue log, final access audit, hypercare 종료 승인 |

비밀번호, API key, DB URL, session/CSRF secret, AWS key, OpenAI key,
recovery code와 private evidence 원문은 위 문서 폴더에도 저장하지 않고
의뢰자 secret manager 또는 승인된 private data store에서만 관리합니다.

## 인수인계 체크리스트

### A. 범위와 코드

- [ ] Product Owner, 인계 총괄, 의뢰자 시스템·운영·보안 책임자와
      Cutover/Hypercare 날짜를 기록했다.
- [ ] 전달 release tag/commit과 Admin transfer 범위를 양측이 승인했다.
- [ ] app/public과 Public 운영이 이번 Admin 인수 범위에서 제외됐음을
      확인했다.
- [ ] app/admin, Admin API, worker, DB migration, private storage 계약과
      운영 문서를 의뢰자 repository에서 열 수 있다.
- [ ] Git/압축 산출물에 실제 secret, DB URL, private evidence가 없음을
      검사했다.

### B. 외부 서비스와 계정

- [ ] 00-Scope/external-services-and-accounts.md의 EXT 항목별 실제 provider,
      organization/project/resource ID를 제한 계정 대장에 기입했다.
- [ ] 모든 production 계정과 비용 계정이 의뢰자 조직 소유이며 주 담당자와
      대체 담당자가 있다.
- [ ] 의뢰자 owner가 GitHub, compute, Supabase/PostgreSQL, AWS S3, OpenAI,
      monitoring, domain/DNS/TLS console에 직접 로그인했다.
- [ ] MFA, recovery, break-glass, billing, budget/quota/expiry alert와 support
      연락처를 확인했다.
- [ ] Admin web, Admin API, long-running worker의 production host를 별도로
      확정했다.
- [ ] Admin production domain, DNS record, TLS 발급·자동 갱신·만료 경보를
      검증했다.
- [ ] 의뢰자 secret manager에 dev/prod secret을 새로 만들고 전달자
      secret/접근을 Cutover 후 회수하도록 계획했다.
- [ ] monitoring runtime 연동과 test alert가 실제 on-call 대상에게 도착했다.
- [ ] Vercel Public-read 환경의 shared dev DB 재사용 예외를 production
      인수 전에 제거했다.

### C. DB·storage·data recovery

- [ ] db/migrations/의 0001~0044 파일과 shared dev 최신 기록 0044를
      대조했다.
- [ ] 0013 적용 효과 부재 drift와 history 미기록 0009/0014/0015의 처리·증적
      방식을 DBA/Product Owner가 승인했다.
- [ ] 깨끗한 dev DB에 전체 migration을 순서대로 적용하고 schema diff가
      승인된 target과 일치했다.
- [ ] dev/prod DB project, role, credential, private bucket/IAM이 분리됐다.
- [ ] 암호화 DB backup과 private object manifest를 만들고 별도 target에
      실제 restore했다.
- [ ] restore 전후 table/row count, object count/hash와 핵심
      canonical/aggregate 데이터를 reconciliation했다.
- [ ] rollback과 PITR rehearsal을 완료하고 승인된 증거를
      03-Data-And-Recovery/에 보관했다.
- [ ] audit_event/llm_usage_record가 0040 이후 physical ledger가 아닌
      discard-only compatibility view임을 운영·보안 담당자가 이해했다.

### D. Admin 보안과 운영

- [ ] 의뢰자 dev에서 최초 admin을 bootstrap하고 admin, reviewer,
      read_only의 허용·거부를 확인했다.
- [ ] login 실패, logout, session 만료/회수, CSRF/CORS/security header와
      SSRF/private-network 차단을 확인했다.
- [ ] 국가 선택·전환 후 다른 국가 데이터가 섞이지 않음을 확인했다.
- [ ] raw evidence와 private object URL이 Public/browser에 직접 노출되지
      않음을 확인했다.
- [ ] collection과 retry가 인증된 운영자의 수동 action으로만 시작됨을
      확인했다.
- [ ] OpenAI 장애·quota·rate limit 시 누락/Review/fail-safe 경계를
      확인하고 자동으로 금융 사실을 만들지 않음을 검증했다.

### E. 검증·UAT·Cutover·종료

- [ ] 새 clone에서 Admin typecheck/build, API test, worker test,
      foundation check와 git diff --check가 통과했다.
- [ ] EN/KO/JA, desktop/tablet/정확한 390px의 affected Admin 화면을
      확인했다.
- [ ] 의뢰자 운영자가 전달자 도움 없이 Overview → Review → Runs → Banks와
      실패 run 진단/retry를 완료했다.
- [ ] UAT의 Critical/High defect가 0건이고 운영·시스템·보안 책임자가
      승인했다.
- [ ] Cutover에서 DB migration → API → worker → Admin web 순서, health,
      read-only smoke와 승인된 최소 stateful smoke를 완료했다.
- [ ] 신규 secret rotation, 전달자 접근 회수와 final access audit를
      완료했다.
- [ ] 10영업일 Hypercare issue를 정리하고 Product Owner와 의뢰자 책임자가
      종료에 서명했다.

위 체크박스 중 하나라도 미완료이면 FPDS Admin 인수 완료로 서명하지
않습니다.
