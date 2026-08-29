# FPDS Admin 인수인계 최소 실행 플레이북

상태: 실행용 체크리스트

대상: FPDS Admin만 해당하며 FPDS Public은 제외

## 1. 이 문서 사용법

위에서 아래로 한 단계씩 진행한다. 각 단계의 체크박스를 모두 완료하고
`통과 조건`에 해당하는 증거 링크를 확보한 뒤에만 다음 단계로 이동한다.
구두로 “완료했다”는 답은 증거로 인정하지 않는다.

먼저 아래 빈칸을 채운다.

| 항목 | 기입 |
|---|---|
| Product Owner |  |
| 인계 측 총괄 |  |
| 의뢰자 시스템 책임자 |  |
| 의뢰자 Admin 운영자 |  |
| 의뢰자 보안 책임자 |  |
| 목표 Cutover 일시 |  |
| Hypercare 종료일 | Cutover 후 10영업일 |
| 문서·증거 저장 위치 |  |

의뢰자가 소유한 제한된 문서 저장소에 아래 폴더를 만든다.

```text
FPDS-Admin-Handover/
  00-Scope/
  01-Code-And-Assets/
  02-Environment-And-Access/
  03-Data-And-Recovery/
  04-Manuals-And-Training/
  05-UAT/
  06-Cutover/
  07-Hypercare/
```

비밀번호, API key, DB URL, session/CSRF secret, private evidence 원문은 이
폴더에 넣지 않는다. 실제 secret은 의뢰자 secret manager에서만 관리한다.

## 2. 절대 생략하지 않는 기준

- `app/public/`, Public 배포, Public 매뉴얼과 Public UAT는 범위에서 제외한다.
- 모든 production 계정과 비용 주체는 의뢰자 소유여야 한다.
- collection, Review 승인, AI 호출은 이관 rehearsal 동안 의뢰자 `dev`에서만 한다.
- 백업을 만들기만 해서는 안 된다. 실제 restore까지 성공해야 한다.
- 의뢰자 운영자가 전달자 도움 없이 Admin을 사용해야 최종 인수한다.

현재 Public-read Vercel API는 Admin production 배포로 보지 않는다. Admin
web, API, long-running worker의 실제 운영 위치를 별도로 확정한다.

## 3. 단계별 실행

### Step 1. 범위와 담당자를 서명한다

내가 할 일:

- [v] 인수 범위를 `app/admin`, Admin API, Worker, DB, private evidence
      storage, 운영환경, 문서, 교육과 지원으로 고정한다.
- [v] `app/public`과 Public 운영은 제외한다고 적는다.

작성할 문서:

- `00-Scope/scope.md`

통과 조건: Scope 문서를 작성한다.


### Step 2. 코드와 자산 목록을 받는다

인계 측에 아래 항목을 한 번에 요청한다.

- [ ] release tag와 정확한 commit SHA
- [ ] Admin transfer manifest: 포함·제외 파일 목록과 공유 파일 사유
- [ ] Git history, branch, CI, lockfile와 runtime version
- [ ] cloud, DB, storage, domain, DNS, TLS, LLM, monitoring 계정 목록
- [ ] migration 목록과 현재 schema version
- [ ] SBOM, third-party license/notice, known issue 목록
- [ ] secret scan과 dependency/security scan 결과

내가 확인할 일:

- [ ] `app/public`이 기본 전달 package에 없는지 확인한다.
- [ ] 실제 secret이나 private evidence가 Git/압축파일에 없는지 확인한다.
- [ ] 전달하려는 release tag에서 clean build 증거가 있는지 확인한다.

받아야 할 증거:

- `01-Code-And-Assets/01-admin-transfer-manifest.md`
- `01-Code-And-Assets/02-release-and-build-report.md`
- `01-Code-And-Assets/03-account-and-asset-inventory.xlsx`
- `01-Code-And-Assets/04-sbom-license-security.zip`

통과 조건: release tag, transfer manifest, clean build 결과와 자산 목록이
서로 같은 버전을 가리킨다.

멈춤 조건: commit이 불명확하거나 secret이 발견되면 폐기·회전 후 다시
검사한다.

### Step 3. 의뢰자 소유 환경을 준비한다

의뢰자 시스템 책임자에게 아래 준비를 요청한다.

- [ ] 의뢰자 소유 Git/cloud/domain/DNS/TLS 계정
- [ ] 서로 분리된 `dev`와 `prod` PostgreSQL
- [ ] 서로 분리된 private object storage bucket 또는 prefix
- [ ] 의뢰자 secret manager와 신규 Admin session/CSRF/storage/DB secret
- [ ] LLM provider account와 비용 한도·경보
- [ ] monitoring/log/alert와 장애 연락 대상
- [ ] Admin web host, API host, long-running worker host

내가 확인할 일:

- [ ] 개인 계정이 production owner가 아닌지 확인한다.
- [ ] `dev`와 `prod`가 DB credential과 storage를 공유하지 않는지 확인한다.
- [ ] browser에서 private storage에 직접 접근할 수 없는지 확인한다.
- [ ] Admin collection이 운영자 수동 실행으로만 시작되는지 확인한다.
- [ ] 모든 계정의 주 담당자와 대체 담당자를 기록한다.

받아야 할 증거:

- `02-Environment-And-Access/01-client-ownership-matrix.xlsx`
- `02-Environment-And-Access/02-environment-readiness.pdf`
- `02-Environment-And-Access/03-topology-and-monitoring.pdf`

통과 조건: 의뢰자 시스템·보안 책임자가 environment readiness에 서명했다.

멈춤 조건: production이 개발 DB를 사용하거나 개인 계정에 종속되면
다음 단계로 가지 않는다.

### Step 4. 의뢰자 dev에서 전체 rehearsal을 한다

기술팀이 새 clone에서 아래 순서로 수행하게 한다.

- [ ] release tag clone과 dependency 설치
- [ ] 빈 `dev` DB에 migration 전체 적용
- [ ] API → Worker → Admin web 배포
- [ ] 의뢰자 최초 `admin` 계정 bootstrap
- [ ] Admin build, API test, Worker test, repository check 실행
- [ ] 암호화 DB dump와 private object sync rehearsal
- [ ] 전후 table row count, object count, hash와 핵심 데이터 수 비교
- [ ] 별도 DB/storage로 backup restore
- [ ] 이전 release와 backup으로 rollback rehearsal
- [ ] `/healthz`, 로그인, 국가 선택, Overview, Review, Runs, Banks smoke test
- [ ] Banks collection과 Runs retry를 통한 수동 운영 가능 여부 확인

최소 검증 명령은 release tag의 깨끗한 clone에서 실행한다.

```powershell
cd app/admin
pnpm run typecheck
pnpm run build

cd ../..
uv run --directory api/service python -m unittest discover -s tests -p 'test_*.py'
uv run python -m unittest discover -s worker -p 'test_*.py'
powershell -ExecutionPolicy Bypass -File scripts/harness/invoke-foundation-checks.ps1
git diff --check
```

받아야 할 증거:

- `03-Data-And-Recovery/01-rehearsal-report.md`
- `03-Data-And-Recovery/02-data-reconciliation.xlsx`
- `03-Data-And-Recovery/03-restore-and-rollback-report.md`
- `03-Data-And-Recovery/04-test-logs.zip`

통과 조건: build/test, 데이터 비교, restore와 rollback이 모두 통과했다.

멈춤 조건: 하나라도 실패하면 production Cutover 날짜를 확정하지 않는다.

### Step 5. 최소 매뉴얼 5종을 받는다

아래 5개만큼은 반드시 최신 release tag와 실제 운영 URL을 기준으로 받는다.

- [ ] `00-read-me-first.md`: 버전, URL, 담당자, 범위, known limitation
- [ ] `deployment-operations-recovery.md`: 설치, 배포, migration, 수동 collection,
      장애 처리, backup/restore, rollback
- [ ] `admin-user-manual.md`: 로그인·국가·언어, Overview, Review/AI verify,
      Runs/retry, Banks/collection, Sources, Product Types, Countries, Changes,
      Health 사용법
- [ ] `security-access.md`: 역할, signup 승인, 접근회수, session/CSRF/CORS,
      SSRF, secret rotation, private evidence 보호
- [ ] `uat-cutover-acceptance.md`: UAT 결과, defect, Cutover, 승인 서명란

내가 확인할 일:

- [ ] 새 운영자가 문서만 보고 로그인부터 run 진단까지 따라 할 수 있다.
- [ ] 모든 명령과 screenshot이 현재 release와 일치한다.
- [ ] 실제 secret, 개인정보와 private evidence 원문이 문서에 없다.

받아야 할 증거: 승인된 문서 5종을 `04-Manuals-And-Training/`에 보관한다.

통과 조건: 의뢰자 운영자와 시스템 책임자가 문서를 읽고 승인했다.

### Step 6. 역할별 교육을 하고 의뢰자가 직접 실습한다

최소 교육 세션:

- [ ] 운영자 2시간: Overview → Review → Runs → Banks
- [ ] 관리자/Data 2시간: 계정·국가·은행·상품 유형·수집·evidence 경계
- [ ] SRE/보안 3시간: 배포·migration·수동 collection·alert·restore·rollback·접근회수

교육 방식:

1. 전달자가 한 번 보여준다.
2. 의뢰자가 같은 작업을 직접 한다.
3. 의뢰자가 오류 상황에서 중단 또는 escalation을 선택한다.

받아야 할 증거:

- `04-Manuals-And-Training/attendance.xlsx`
- `04-Manuals-And-Training/training-recording-link.md`
- `04-Manuals-And-Training/operator-practice-result.md`

통과 조건: 의뢰자 운영자가 매뉴얼만 보고 Review와 실패 run 진단을
완료했다.

멈춤 조건: 전달자가 대신 클릭해야 완료된다면 교육을 다시 한다.

### Step 7. 의뢰자 dev에서 최소 UAT를 통과한다

의뢰자가 직접 아래 시나리오를 수행한다.

- [ ] `admin`, `reviewer`, `read_only`의 허용·거부 확인
- [ ] 로그인 실패, logout, session 만료/회수, CSRF 거부 확인
- [ ] 국가 선택·전환 후 다른 국가 데이터가 섞이지 않는지 확인
- [ ] EN/KO/JA와 desktop/정확한 `390px` 기본 화면 확인
- [ ] Banks에서 승인된 소규모 collection 실행
- [ ] Review에서 evidence 확인 후 approve/reject/defer/edit-approve 실행
- [ ] Runs에서 completed/partial/failed 진단과 승인된 retry 실행
- [ ] API/Worker/DB/LLM 장애 시 alert와 복구 절차 실행
- [ ] SSRF/private network, CORS, cookie/security header 차단 확인
- [ ] backup restore와 release rollback 재확인
- [ ] 전달자 도움 없이 일일 점검과 escalation 수행

받아야 할 증거:

- `05-UAT/01-uat-result.xlsx`
- `05-UAT/02-defect-register.xlsx`
- `05-UAT/03-uat-approval.pdf`

통과 조건: 모든 필수 시나리오가 통과하고 `Critical`과 `High` defect가
0건이며, 의뢰자 운영자·시스템·보안 책임자가 서명했다.

멈춤 조건: UAT를 production 데이터로 대신하거나 Public UI 결과로
판정하지 않는다.

### Step 8. Production Cutover와 소유권 이전을 한다

Cutover 전:

- [ ] `T-2`: change freeze, release tag, open defect와 rollback 승인
- [ ] `T-1`: 최종 암호화 backup, object manifest, 연락망 확인
- [ ] GO/NO-GO 회의에서 Product Owner와 의뢰자 책임자 서명

Cutover 당일:

- [ ] final data sync와 reconciliation
- [ ] DB migration → API → Worker → Admin web 순서로 배포
- [ ] `/healthz`, 로그인, RBAC, 국가 scope의 read-only smoke
- [ ] 승인된 최소 stateful smoke만 실행
- [ ] 의뢰자 admin과 비상 계정 확인
- [ ] Admin 수동 collection·retry 운영모드 기록
- [ ] 의뢰자 secret으로 최종 rotation
- [ ] 전달자 개인/공유 production 접근 회수

받아야 할 증거:

- `06-Cutover/01-go-no-go.pdf`
- `06-Cutover/02-cutover-log.md`
- `06-Cutover/03-production-smoke.md`
- `06-Cutover/04-access-and-secret-rotation.pdf`
- `06-Cutover/05-handover-acceptance.pdf`

통과 조건: production smoke, 소유권 이전, secret rotation과 접근회수가
완료되고 양측이 인수확인서에 서명했다.

실패 시: 새 쓰기를 중지하고 승인된 application rollback 또는 restore를
수행한다. 현장에서 즉흥적인 destructive SQL을 사용하지 않는다.

### Step 9. 10영업일 Hypercare 후 종료한다

- [ ] 최초 3영업일은 매일 장애·문의·비용·alert 상태를 확인한다.
- [ ] 이후 7영업일은 합의한 빈도로 issue log를 관리한다.
- [ ] 발견된 manual gap은 매뉴얼과 FAQ에 반영한다.
- [ ] 미해결 항목에는 owner, 위험, 목표일과 승인자를 기록한다.
- [ ] 의뢰자 계정·비용·backup·on-call 소유권을 최종 확인한다.
- [ ] 전달자 접근권이 다시 생기지 않았는지 최종 audit한다.
- [ ] Product Owner와 의뢰자 책임자가 Hypercare 종료에 서명한다.

받아야 할 증거:

- `07-Hypercare/01-issue-log.xlsx`
- `07-Hypercare/02-final-access-audit.pdf`
- `07-Hypercare/03-hypercare-closure.pdf`

통과 조건: 운영 책임이 의뢰자에게 완전히 이전되고 최종 종료 서명이 있다.

## 4. 최종 GO/NO-GO 한 장 점검

아래 중 하나라도 `아니오`이면 인수 완료로 서명하지 않는다.

- [ ] 의뢰자가 코드, production 계정, 비용과 domain을 소유하는가?
- [ ] release tag의 clean build/test가 통과했는가?
- [ ] dev/prod DB와 private storage가 분리되었는가?
- [ ] 데이터 비교, restore와 rollback이 실제로 성공했는가?
- [ ] Critical/High defect가 0건인가?
- [ ] 의뢰자 운영자가 전달자 없이 Admin을 사용할 수 있는가?
- [ ] 최소 매뉴얼 5종과 UAT 증적이 최신인가?
- [ ] 신규 secret으로 회전했고 전달자 접근을 회수했는가?
- [ ] Public 제외, BX-PF/audit 한계와 Admin 수동 운영 기준이 서명되었는가?
- [ ] 10영업일 Hypercare와 종료 책임자가 정해졌는가?

모두 `예`일 때만 FPDS Admin 인수 완료로 서명한다.
