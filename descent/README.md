# FPDS Admin 인수인계 실행 가이드

상태: 실행용 체크리스트

적용 범위: FPDS Admin, Admin API, worker, DB, private evidence storage

이 문서는 위에서 아래 순서대로 실행한다. 각 단계의 체크박스와 통과 조건을
모두 만족한 후에만 다음 단계로 이동한다.

## 1. 인수인계 완료 기준

아래 조건을 모두 만족하면 인수인계가 완료된 것으로 본다.

- [ ] 의뢰자가 소스, 운영 계정, 비용 계정, 도메인과 데이터를 소유한다.
- [ ] 확정된 release tag에서 build와 테스트가 통과한다.
- [ ] `Critical`과 `High` 결함이 0건이다.
- [ ] 의뢰자 운영자가 전달자 도움 없이 Admin 운영과 장애 진단을 수행한다.
- [ ] 인수인계 후 안정화 지원과 최종 종료 승인이 완료된다.

## 2. 시작할 때 사용할 제안문

아래 문구로 인수인계 착수를 제안한다.

> FPDS Admin 인수인계를 단계적으로 시작하고자 합니다. 먼저 범위와 담당자를
> 확정하고, 전달할 소스와 데이터 상태를 정리한 뒤 의뢰자 환경에서
> 시스템 이관을 진행하겠습니다. 이 단계가 통과되면 운영 문서와
> 교육, UAT, 안정화 지원 순으로 진행하겠습니다.

## 3. 시작 전에 채울 항목

| 항목 | 기입 |
|---|---|
| 의뢰자 운영자 | 황인협 |
| 전달자 총괄 | 이근엽 |
| 목표 이관일 |  |
| 최종 종료일 | 이관 후 10영업일 |
| 업무 연락 채널 | kylee1112@hotmail.com |

## 4. 최소 산출물

인수인계 과정에서 이 가이드 외 아래 8개 문서를 유지한다. 실제 비밀번호,
API key, DB URL,
session/CSRF secret, recovery code와 private evidence 원문은 어떤 산출물에도
기록하지 않는다. Secret은 의뢰자 secret manager에서만 생성·보관한다.

```text
descent/
  README.md
  01-scope-and-owners.md
  02-release-readiness.md
  03-environment-and-access.md
  04-data-migration-and-recovery.md
  05-operations-handbook.md
  06-training-and-uat.md
  07-cutover-and-acceptance.md
  08-hypercare-closure.md
```

보안상 제한이 필요한 계정·접근·backup 증거는 Git에 저장하지 않고 의뢰자
제한 저장소에 둔다.

## 5. 단계별 실행

### Step 1. 범위와 담당자를 확정한다

목적: 무엇을 누구에게 언제까지 넘기는지 먼저 고정한다.

실행:

- [v] 기본 범위가 `app/admin`, Admin API, worker, DB migration, private
      evidence storage와 운영 문서임을 확인한다.
- [v] 전달자와 의뢰자의 시스템·운영·보안 담당자 및 최종 승인자를 지정한다.
- [v] 이관일과 10영업일 안정화 기간을 정한다.
- [v] 산출물과 승인 증거를 보관할 저장소를 정한다.

산출물 `01-scope-and-owners.md`에 최소한 다음을 기록한다.

- 포함 범위
- 양측 담당자 연락 방법
- 목표 일정
- 소스·데이터·계정의 최종 소유자

통과 조건:

- [ ] 인수자가 범위와 내용을 승인했다.

멈춤 조건:

- 범위 또는 최종 소유자가 정해지지 않았으면 소스나 데이터를 이전하지 않는다.

### Step 2. 전달할 소스를 고정하고 품질을 확인한다

목적: 재현 가능하고 secret이 없는 하나의 전달 버전을 만든다.

실행:

- [ ] 전달 대상 Git repository와 의뢰자 소유 organization을 확정한다.
- [ ] 포함·제외 경로와 공유 파일의 사유를 기록한다.
- [ ] 불필요한 log, cache, 임시파일과 재생성 가능한 산출물을 제외한다.
- [ ] Git과 전달 archive에 실제 secret, DB URL, 고객 데이터, private evidence
      원문이 없는지 검사한다.
- [ ] 빈 환경에서 dependency를 설치하고 아래 검증을 실행한다.
- [ ] 검증이 끝난 commit에 변경 불가능한 release tag를 만든다.
- [ ] 미해결 결함을 심각도, 영향, 우회 방법, 담당자와 목표일로 기록한다.
- [ ] `Critical`과 `High` 결함은 모두 해결하거나 Production 전환을 중단한다.

최소 검증:

```powershell
cd app/admin
pnpm run typecheck
pnpm run build

cd ../..
uv run --directory api/service python -m unittest discover -s tests -p test_*.py
uv run python -m unittest discover -s worker -p test_*.py
powershell -ExecutionPolicy Bypass -File scripts/harness/invoke-foundation-checks.ps1
git diff --check
```

산출물 `02-release-readiness.md`에 최소한 다음을 기록한다.

- repository URL, branch, commit과 release tag
- 포함·제외 경로
- 실행한 명령, 일시와 실제 결과
- 알려진 결함과 제한사항
- secret/private evidence 검사 결과
- 기술 책임자와 Product Owner 승인

통과 조건:

- [ ] 깨끗한 clone에서 모든 필수 검증이 통과했다.
- [ ] `Critical`과 `High` 결함이 0건이다.
- [ ] 전달 release tag와 알려진 제한사항을 양측이 승인했다.

멈춤 조건:

- build/test 실패, secret 노출 또는 미승인 `Critical`/`High` 결함이 있으면
  환경 이관을 시작하지 않는다.

### Step 3. 의뢰자 소유 환경과 접근권을 준비한다

목적: 개인 또는 전달자 계정에 의존하지 않는 운영 기반을 만든다.

실행:

- [ ] 의뢰자 소유 Git organization/repository를 준비한다.
- [ ] Admin web, Admin API와 long-running worker host를 각각 확정한다.
- [ ] 의뢰자 소유 `dev`와 `prod` PostgreSQL을 분리한다.
- [ ] 의뢰자 소유 `dev`와 `prod` private object storage를 분리한다.
- [ ] Admin web/API domain, DNS, TLS와 갱신 책임자를 정한다.
- [ ] 의뢰자 secret manager에 신규 dev/prod secret을 생성한다.
- [ ] OpenAI organization/project, service account, 예산·quota·경보를 정한다.
- [ ] log, monitoring, alert와 on-call 연락처를 연결한다.
- [ ] 각 외부 서비스에 주 담당자, 대체 담당자, 비용·보안 담당자를 기록한다.
- [ ] 의뢰자 담당자가 각 console에 직접 로그인하고 MFA와 recovery를 확인한다.

산출물 `03-environment-and-access.md`에 최소한 다음을 기록한다.

- 서비스별 provider, project/resource ID와 console URL
- dev/prod 구분, region과 비용 소유자
- 주 담당자, 대체 담당자, MFA/recovery owner
- secret manager 항목명 또는 경로만 기재한 참조
- backup/PITR, monitoring, support와 escalation 정보
- 전달자 접근 회수 예정일

통과 조건:

- [ ] 의뢰자 시스템·보안 책임자가 환경과 접근권 준비를 승인했다.
- [ ] 개인 계정이 Production owner가 아니다.
- [ ] dev/prod의 DB, storage와 credential이 분리되어 있다.

멈춤 조건:

- Production이 shared dev DB를 사용하거나 개인 계정에 종속되면 다음 단계로
  진행하지 않는다.

### Step 4. 의뢰자 dev에서 데이터 복구와 전체 이관 연습을 한다

목적: Production 전환 전에 동일한 절차를 의뢰자 dev에서 실제로 증명한다.

실행:

- [ ] 확정 release tag를 새 작업 디렉터리에 clone한다.
- [ ] 현재 repository migration과 대상 DB의 migration history를 비교한다.
- [ ] 알려진 migration drift를 DBA와 Product Owner 승인 절차로 해소한다.
- [ ] 빈 dev DB에 migration을 처음부터 순서대로 적용한다.
- [ ] 암호화 DB backup과 private object manifest를 만든다.
- [ ] 별도의 dev DB/storage에 실제 restore한다.
- [ ] restore 전후 table/row count, 핵심 canonical/aggregate 수, object count와
      hash를 비교한다.
- [ ] DB migration → Admin API → worker → Admin web 순서로 배포한다.
- [ ] 의뢰자 최초 `admin` 계정을 bootstrap한다.
- [ ] `/healthz`, 로그인, 국가 선택, RBAC, Overview, Review, Runs와 Banks를
      확인한다.
- [ ] 승인된 소규모 collection과 실패 run retry를 한 번씩 실행한다.
- [ ] 이전 release와 backup을 사용한 application rollback 및 data restore를
      실제로 연습한다.
- [ ] Step 2의 필수 검증을 의뢰자 환경에서 다시 실행한다.

데이터 안전 기준:

- raw evidence는 private storage에만 둔다.
- browser나 Public surface에 private object 접근권을 주지 않는다.
- row를 임의로 삭제하거나 현장에서 즉흥적인 destructive SQL을 실행하지 않는다.
- backup 생성만으로 완료 처리하지 않고 restore와 reconciliation까지 확인한다.

산출물 `04-data-migration-and-recovery.md`에 최소한 다음을 기록한다.

- repository target migration과 대상 DB 적용 version
- migration history 및 drift 처리 승인
- backup ID, 암호화 여부, 보관 위치 참조와 hash
- restore 대상과 실행 결과
- table/row/object count 및 핵심 데이터 비교 결과
- 배포, smoke, rollback과 재복구 결과
- 실패 항목, 조치 담당자와 재검증 결과

통과 조건:

- [ ] migration, build/test, 배포, data reconciliation, restore와 rollback이
      모두 성공했다.
- [ ] 의뢰자 시스템 책임자와 DBA가 결과를 승인했다.

멈춤 조건:

- 한 항목이라도 실패하면 Production 전환일을 확정하지 않는다.

### Step 5. 운영 핸드북을 완성하고 역할별 교육을 한다

목적: 의뢰자가 전달자 도움 없이 일상 운영과 장애 대응을 수행하게 한다.

기존 인수인계 매뉴얼의 필수 내용을 `05-operations-handbook.md` 하나로
통합한다. 이 문서에는 최소한 다음을 포함한다.

- release tag, 실제 URL, 담당자, 범위와 알려진 제한사항
- 시스템 구성과 dev/prod 환경 구분
- 설치, 배포, migration, rollback과 release 확인 방법
- 로그인, 국가·언어, Overview, Review/AI verify, Runs/retry,
  Banks/collection, Sources, Product Types, Countries, Changes와 Health 사용법
- Admin은 수동 collection/retry로 운영한다는 기준
- backup/restore, 장애 진단, monitoring, alert와 escalation 절차
- 역할, signup 승인, 계정 생성·회수와 break-glass 절차
- session, CSRF, CORS, SSRF, security header, secret rotation과 private
  evidence 보호 기준
- 자주 발생하는 오류, 중단 조건과 FAQ

교육 실행:

- [ ] 운영자 교육: Overview → Review → Runs → Banks 순으로 일상 업무를
      실습한다.
- [ ] 시스템·보안 교육: 배포, migration, monitoring, restore, rollback,
      계정 회수와 secret rotation을 실습한다.
- [ ] 전달자가 한 번 시연한 뒤 의뢰자가 같은 작업을 직접 수행한다.
- [ ] 의뢰자가 실패 run을 진단하고 계속 진행, 중단 또는 escalation을 직접
      선택한다.
- [ ] 교육 중 발견한 문서 오류를 핸드북에 반영한다.

산출물 `06-training-and-uat.md`의 교육 부분에 최소한 다음을 기록한다.

- 교육 일시, 참석자와 역할
- 다룬 기능과 복구 절차
- 의뢰자 직접 실습 결과
- 미숙 항목과 재교육 결과
- 의뢰자 운영·시스템 책임자의 교육 완료 승인

통과 조건:

- [ ] 의뢰자 운영자가 핸드북만 보고 Review와 실패 run 진단을 완료했다.
- [ ] 의뢰자 시스템 담당자가 핸드북만 보고 배포와 복구 절차를 설명하고
      rehearsal 결과를 재현할 수 있다.

멈춤 조건:

- 전달자가 대신 조작해야 완료되면 교육을 다시 한다.

### Step 6. 의뢰자 UAT와 GO/NO-GO 승인을 받는다

목적: 의뢰자가 직접 필수 업무와 안전 경계를 검증한다.

`06-training-and-uat.md`의 UAT 부분에서 다음을 실행한다.

- [ ] `admin`, `reviewer`, `read_only` 역할의 허용·거부를 확인한다.
- [ ] 로그인 실패, logout, session 만료·회수와 CSRF 거부를 확인한다.
- [ ] 국가 전환 후 다른 국가 데이터가 섞이지 않는지 확인한다.
- [ ] EN/KO/JA와 desktop, tablet, 정확한 `390px` 기본 화면을 확인한다.
- [ ] Banks에서 승인된 소규모 collection을 실행한다.
- [ ] Review에서 evidence 확인 후 approve, reject, defer와 edit-approve를
      실행한다.
- [ ] Runs에서 completed, partial, failed 상태 진단과 승인된 retry를 실행한다.
- [ ] API, worker, DB 또는 LLM 장애 시 alert와 escalation 절차를 확인한다.
- [ ] backup restore와 release rollback 결과를 재확인한다.
- [ ] SSRF/private network, CORS, cookie/security header 차단을 확인한다.
- [ ] 의뢰자 운영자가 전달자 도움 없이 일일 점검을 완료한다.

UAT 기록에 최소한 다음을 포함한다.

- 시나리오별 실행자, 일시, 결과와 증거 링크
- 결함 목록, 심각도, owner, 목표일과 재검증 결과
- 알려진 `Medium`/`Low` 결함의 영향과 승인된 우회 방법
- `Critical`/`High` 0건 확인
- 의뢰자 운영·시스템·보안 책임자 승인

통과 조건:

- [ ] 모든 필수 UAT 시나리오가 통과했다.
- [ ] `Critical`과 `High` 결함이 0건이다.
- [ ] Product Owner와 의뢰자 책임자가 GO를 승인했다.

멈춤 조건:

- UAT 실패, 복구 불가 또는 `Critical`/`High` 결함이 있으면 NO-GO로 기록하고
  Production 전환을 연기한다.

### Step 7. Production을 전환하고 소유권을 이전한다

목적: 승인된 release와 데이터를 의뢰자 Production으로 안전하게 전환한다.

전환 전:

- [ ] 변경 동결, release tag, 미해결 결함과 rollback 기준을 재확인한다.
- [ ] 최종 암호화 backup, object manifest, 담당자와 비상 연락망을 확인한다.
- [ ] Product Owner와 의뢰자 책임자가 GO/NO-GO에 서명한다.

전환 당일:

- [ ] 최종 데이터 sync와 reconciliation을 수행한다.
- [ ] DB migration → Admin API → worker → Admin web 순서로 배포한다.
- [ ] `/healthz`, 로그인, RBAC와 국가 scope의 read-only smoke를 수행한다.
- [ ] 승인된 최소 stateful smoke만 수행한다.
- [ ] 의뢰자 admin과 break-glass 계정을 확인한다.
- [ ] 의뢰자 신규 secret으로 최종 rotation한다.
- [ ] 전달자 개인/shared Production 접근, token, deploy key와 API key를
      회수한다.
- [ ] 실패 시 새 쓰기를 중지하고 승인된 rollback 또는 restore를 실행한다.

산출물 `07-cutover-and-acceptance.md`에 최소한 다음을 기록한다.

- GO/NO-GO 승인
- 단계별 작업 시각, 실행자와 결과
- 최종 migration/data reconciliation 결과
- Production smoke 결과
- secret rotation과 전달자 접근 회수 결과
- rollback 실행 여부와 결과
- 양측 인수확인 서명

통과 조건:

- [ ] Production smoke와 데이터 비교가 통과했다.
- [ ] 의뢰자 소유 계정과 secret으로 시스템이 동작한다.
- [ ] 전달자의 Production 접근이 회수됐다.
- [ ] 양측이 인수확인서에 서명했다.

### Step 8. 10영업일 Hypercare 후 종료한다

목적: 전환 직후 문제를 정리하고 운영 책임을 완전히 이전한다.

실행:

- [ ] 최초 3영업일은 매일 장애, 문의, 비용, backup과 alert를 확인한다.
- [ ] 이후 7영업일은 합의한 빈도로 issue를 확인한다.
- [ ] 발견한 운영 절차 누락을 `05-operations-handbook.md`에 반영한다.
- [ ] 미해결 항목에 owner, 위험, 우회 방법, 목표일과 승인자를 기록한다.
- [ ] 계정, 비용, backup, on-call과 support 소유권을 최종 확인한다.
- [ ] 전달자 접근이 다시 부여되지 않았는지 최종 access audit을 수행한다.

산출물 `08-hypercare-closure.md`에 최소한 다음을 기록한다.

- 일자별 issue, 영향, 조치와 상태
- 잔여 `Medium`/`Low` 항목과 인수 승인
- 최종 access audit 결과
- 운영 핸드북 최종 version
- Product Owner와 의뢰자 책임자의 종료 승인

통과 조건:

- [ ] 운영 책임이 의뢰자에게 완전히 이전됐다.
- [ ] 잔여 항목의 owner와 처리일이 정해졌다.
- [ ] Product Owner와 의뢰자 책임자가 Hypercare 종료에 서명했다.

## 6. 최종 한 장 점검

아래 질문에 모두 `예`라고 답할 수 있어야 한다.

| 질문 | 예/아니오 | 증거 링크 |
|---|---|---|
| 의뢰자가 소스, Production 계정, 비용과 domain을 소유하는가? |  |  |
| 확정 release tag의 build/test가 통과했는가? |  |  |
| dev/prod DB, storage와 credential이 분리됐는가? |  |  |
| migration history와 target schema가 정합한가? |  |  |
| backup/restore, reconciliation과 rollback이 실제 성공했는가? |  |  |
| `Critical`과 `High` 결함이 0건인가? |  |  |
| 의뢰자 운영자가 전달자 없이 Admin을 운영할 수 있는가? |  |  |
| 운영 핸드북, 교육 기록과 UAT 승인이 최신인가? |  |  |
| 신규 secret 적용과 전달자 접근 회수가 완료됐는가? |  |  |
| 10영업일 Hypercare와 최종 종료 승인이 완료됐는가? |  |  |

모든 답이 `예`일 때만 FPDS Admin 인수인계를 완료 처리한다.

## 7. 저장소 기준 문서

상세 확인이 필요할 때만 아래 문서를 참고한다.

- [Admin 인수인계 최소 실행 플레이북](../docs/01-planning/fpds-admin-handover-minimum-playbook.md)
- [인수인계 범위와 최종 체크리스트](../00-Scope/scope.md)
- [외부 서비스 및 계정 대장](../00-Scope/external-services-and-accounts.md)
- [DB migration, schema와 ERD](../00-Scope/database-migrations-schema-erd.md)
- [Admin 운영 경계](../app/admin/README.md)
- [Admin API 운영 경계](../api/service/README.md)
- [Worker 운영 경계](../worker/README.md)
- [DB 운영 경계](../db/README.md)
