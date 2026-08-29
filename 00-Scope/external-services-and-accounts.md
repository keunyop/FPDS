# FPDS Admin 외부 서비스 및 계정 인수인계 대장

상태: 인수인계용 현재 상태표 + 기입 템플릿

기준일: 2026-08-29

대상: FPDS Admin web, Admin API, worker, PostgreSQL, private evidence
storage와 이를 운영하는 데 직접 필요한 외부 계정

## 1. 보안 기입 원칙

- 이 Git 파일에는 비밀번호, API key, access/secret key, DB URL, session/CSRF
  secret, recovery code, private evidence URL을 적지 않는다.
- 계정 로그인 ID는 업무용 별칭 또는 회사 이메일만 적고 비밀번호는 적지
  않는다.
- secret은 의뢰자 secret manager에 저장하고 이 문서에는 secret의
  **경로/항목명 참조**만 적는다.
- 계정 대장의 실제 기입본은 의뢰자 제한 문서 저장소의
  02-Environment-And-Access/01-client-ownership-matrix.xlsx에 보관한다.
- 이 파일은 저장소 근거와 빈 양식을 제공한다. 계정 소유권 이전이나
  production 준비 완료를 의미하지 않는다.

상태 표기:

- 사용 중: 현재 shared dev 또는 운영 예외에서 실제 연결을 확인했다.
- 부분 사용: 공유 구성요소에는 존재하지만 Admin production으로 승인되지
  않았다.
- 설계만: 설정 계약 또는 예시는 있으나 실제 provider 연동은 확인되지
  않았다.
- 미구성: 인수 전에 의뢰자가 선택·생성해야 한다.
- 비범위: 현재 Admin runtime 계정이 아니다.

## 2. 현재 외부 서비스 목록

| ID | 영역 | 현재 서비스/Provider | 현재 상태 | Admin 용도와 경계 | 저장소/실행 근거 | 인수 전 조치 |
|---|---|---|---|---|---|---|
| EXT-01 | Source control/CI | GitHub repository, GitHub Actions | 사용 중 | 소스, 이력, CI workflow. 원격 host는 github.com으로 확인했으나 조직·repository owner는 이 파일에 고정하지 않는다. | .git/config, .github/workflows/, README.md | 의뢰자 조직 소유 repository, branch protection, Actions 권한·비용·2인 관리자 확인 |
| EXT-02 | Admin web compute | 현재 localhost 개발 실행 | 미구성 | app/admin은 현재 localhost:3001; Admin production web 배포는 확인되지 않았다. | app/admin/README.md, .env.dev.example | 의뢰자 소유 web host/project, production URL, deploy 권한과 rollback owner 결정 |
| EXT-03 | Admin API compute | 로컬 FastAPI; Vercel switchabank-api는 Public-read 예외 | 부분 사용 | Vercel에는 FastAPI 전체 app이 있지만 현재 배포 목적은 Public-read이고 Admin web은 배포되지 않았다. Admin production으로 인수하지 않는다. | vercel.json, app.py, api/service/README.md | Admin API의 실제 production host를 별도로 확정하고 Public-read 예외와 분리 |
| EXT-04 | Long-running worker compute | 로컬/명시적 subprocess 실행 | 미구성 | 수동 collection의 장시간 worker와 browser fallback을 실행할 상시 host가 없다. Vercel function을 worker host로 간주하지 않는다. | worker/README.md, api/service/api_service/source_collection_runner.py | 의뢰자 소유 worker host, 실행 identity, timeout, 배포·재시작·용량 정책 결정 |
| EXT-05 | Database | Supabase-hosted PostgreSQL, shared dev | 사용 중 | Admin auth, registry, run, evidence metadata, review, canonical, aggregate projection 저장. 현재 DB host가 Supabase pooler임을 비밀값 없이 확인했다. | FPDS_DATABASE_URL의 host 확인, db/, api/service/api_service/db.py | 의뢰자 소유 dev/prod project를 분리하고 DB owner, pool, backup/PITR, egress와 비용 확인 |
| EXT-06 | Private object storage | AWS S3, shared dev | 사용 중 | raw snapshot과 parse/extraction/normalization/validation artifact의 private 저장. worker는 AWS CLI s3api put-object를 사용한다. | FPDS_OBJECT_STORAGE_DRIVER=s3, worker/discovery/fpds_snapshot/storage.py, storage/README.md | 의뢰자 소유 dev/prod bucket·IAM·region·encryption·lifecycle·restore 검증 |
| EXT-07 | Domain/registrar | Admin domain 없음 | 미구성 | 현재 Admin origin은 localhost다. Public domain/brand domain은 Admin 인수 범위가 아니다. | .env.dev.example, .env.prod.example, Admin 플레이북 | 의뢰자 소유 Admin web/API domain과 registrar owner, 갱신·잠금·비상 연락처 결정 |
| EXT-08 | DNS | Admin DNS zone/record 없음 | 미구성 | production Admin web/API record와 변경 권한이 정의되지 않았다. | .env.prod.example의 placeholder origin | DNS provider, zone owner, record, TTL, change/rollback 승인자 결정 |
| EXT-09 | TLS/certificate | Admin TLS 없음 | 미구성 | localhost 개발 외 Admin certificate/renewal 증거가 없다. Vercel Public-read TLS를 Admin TLS로 인수하지 않는다. | api/service/README.md, .env.prod.example | 발급 주체, 자동 갱신, 만료 경보, key 보관, certificate rollback 확인 |
| EXT-10 | LLM | OpenAI API, gpt-5.6-luna | 사용 중 | 은행 onboarding, source 판단, 공식-domain grounding, Review AI에 사용. API key가 없으면 일부 경로는 fail-safe/fallback으로 동작한다. | FPDS_LLM_PROVIDER=openai, FPDS_LLM_MODEL=gpt-5.6-luna, worker/pipeline/fpds_ai_runtime.py | 의뢰자 OpenAI organization/project, service account, model access, budget·rate limit·alert·data control 확인 |
| EXT-11 | Monitoring/error tracking | dev disabled; Sentry는 production 선호 예시 | 설계만 | structured log/error contract는 있으나 Sentry SDK/runtime capture 연동은 확인되지 않았다. | shared/observability/, docs/03-design/monitoring-error-tracking-baseline.md, .env.prod.example | provider/project, DSN secret, sampling, retention, alert routing, on-call과 test alert 증거 확정 |
| EXT-12 | Secret management | 전용 provider 확인 안 됨 | 미구성 | 현재 로컬은 untracked env, Vercel 예외는 platform environment variables를 사용한다. 이것만으로 Admin production secret manager 준비가 완료된 것은 아니다. | .gitignore, docs/03-design/dev-prod-environment-spec.md, api/service/README.md | 의뢰자 secret manager 선택, dev/prod 분리, rotation·break-glass·access review 구축 |
| EXT-13 | External source sites | 등록된 금융기관 공식 HTTPS 사이트 | 사용 중 | 수동 collection이 공식 allowlist URL을 fetch한다. 계정형 SaaS가 아니라 외부 데이터 의존성이다. | worker/discovery/, source_registry_item, FPDS_SOURCE_FETCH_ALLOWLIST | 도메인 allowlist owner, robots/terms/legal 검토, 장애·429·WAF 대응 owner 기록 |
| EXT-14 | Admin auth/identity | FPDS PostgreSQL-backed session auth | 사용 중(내부) | 별도 Auth0/Clerk/Cognito 계정은 없다. 사용자·session·login attempt는 FPDS DB에 저장한다. | db/migrations/0002_admin_auth.sql, api/service/api_service/auth.py | bootstrap/break-glass 절차, password/MFA 정책의 현재 한계, 계정 회수 owner 확인 |
| EXT-15 | UI asset tooling | Shadcnblocks credential이 dev에 설정됨 | 개발 도구 | 런타임 서비스가 아니라 Admin UI 원본 asset 취득/라이선스 확인용이다. key 값은 출력하거나 Git에 기록하지 않는다. | dev 환경의 변수 이름 SHADCNBLOCKS_API_KEY, design provenance 문서 | 라이선스·구매 계정 소유권과 향후 asset update 필요 여부 확인 |
| EXT-16 | BX-PF integration | mock | 비범위/미연결 | dev는 mock이고 실제 write-back runtime은 구현·승인되지 않았다. | FPDS_BXPF_MODE=mock, shared/config/README.md | live 전환 승인이 있을 때만 별도 계정·endpoint·client credential 인수 |

## 3. 현재 확인된 인수 차단 사항

다음 항목이 닫히기 전에는 Admin production 인수 완료로 서명하지 않는다.

1. Admin web, Admin API, long-running worker의 production host가 의뢰자
   소유로 확정되지 않았다.
2. Admin production domain, DNS, TLS와 자동 갱신 경보가 없다.
3. 전용 production PostgreSQL과 private object storage의 분리·복구 증거가
   없다.
4. Vercel Public-read Preview/Production이 shared dev DB를 재사용하는 임시
   예외가 남아 있다. production DB 분리 전에는 release-ready로 보지 않는다.
5. production monitoring provider/alert/on-call이 실제 runtime에 연결되지
   않았다.
6. 의뢰자 secret manager와 신규 secret rotation/접근 회수 증거가 없다.

## 4. 계정·소유권 기입 템플릿

아래 표를 EXT-01부터 필요한 서비스별로 채운다. 로그인 ID는 회사 이메일
또는 service account 별칭까지만 허용한다.

| ID | Provider/상품 | 의뢰자 조직·tenant | Account alias/회사 이메일 | Project/account ID | Dev resource ID | Prod resource ID | Region | 비용 계정/cost center | 계약·갱신일 |
|---|---|---|---|---|---|---|---|---|---|
| EXT-01 |  |  |  |  |  |  |  |  |  |
| EXT-02 |  |  |  |  |  |  |  |  |  |
| EXT-03 |  |  |  |  |  |  |  |  |  |
| EXT-04 |  |  |  |  |  |  |  |  |  |
| EXT-05 |  |  |  |  |  |  |  |  |  |
| EXT-06 |  |  |  |  |  |  |  |  |  |
| EXT-07 |  |  |  |  |  |  |  |  |  |
| EXT-08 |  |  |  |  |  |  |  |  |  |
| EXT-09 |  |  |  |  |  |  |  |  |  |
| EXT-10 |  |  |  |  |  |  |  |  |  |
| EXT-11 |  |  |  |  |  |  |  |  |  |
| EXT-12 |  |  |  |  |  |  |  |  |  |
| EXT-15 |  |  |  |  |  |  |  |  |  |

### 책임·보안 템플릿

| ID | 주 담당자 | 대체 담당자 | Billing owner | Security owner | MFA 방식/강제 여부 | Recovery owner | Break-glass 계정 참조 | Secret manager 경로/항목명 | 마지막 rotation | 전달자 접근 회수일 |
|---|---|---|---|---|---|---|---|---|---|---|
|  |  |  |  |  |  |  |  |  |  |  |

### 운영·복구 템플릿

| ID | Admin console URL | Support plan/연락처 | Backup/PITR | Restore 증거 위치 | Alert 대상 | 장애 escalation | RTO/RPO | Export/탈퇴 절차 | 이전 상태/승인자 |
|---|---|---|---|---|---|---|---|---|---|
|  |  |  |  |  |  |  |  |  |  |

## 5. 서비스별 최소 추가 기입 항목

- GitHub: organization/repository, repository visibility, owner team, branch
  protection, deploy key/App, Actions secret owner
- Compute: project/service ID, runtime version, region, deploy identity,
  environment variable scope, rollback release
- Supabase/PostgreSQL: organization/project ref, pool/direct host 구분, DB
  role owner, backup/PITR, connection limit, maintenance window
- AWS S3: AWS account ID, bucket ARN, region, IAM role/user, KMS key alias,
  block-public-access, versioning/lifecycle, restore test
- Domain/DNS/TLS: registrar, zone ID, registrant, transfer lock, record owner,
  certificate issuer, renewal 방식, 만료 alert
- OpenAI: organization ID, project ID, service account, 허용 model, 월 예산,
  rate limit, usage alert, key rotation
- Monitoring: organization/project, DSN secret ref, environment, sampling,
  retention, alert rule, on-call destination, test-event 결과
- Secret manager: vault/project, dev/prod path, reader/writer/rotator role,
  break-glass, audit retention

## 6. 계정 인수 체크리스트

- [ ] 모든 사용 중·부분 사용·미구성 항목의 의뢰자 owner와 대체 owner를
      기록했다.
- [ ] production 계정, 비용 계정, domain 등록자가 개인이 아닌 의뢰자
      조직 소유다.
- [ ] 전달자는 실제 secret을 문서로 전달하지 않고 의뢰자 vault에서 신규
      secret을 생성·회전했다.
- [ ] 의뢰자 owner가 각 console에 직접 로그인하고 MFA/recovery를 확인했다.
- [ ] dev/prod DB, storage, credential, LLM project와 monitoring environment가
      분리됐다.
- [ ] DB restore, object restore, compute rollback, DNS rollback, TLS renewal,
      monitoring test alert를 의뢰자가 직접 실행했다.
- [ ] 비용 한도와 예산·quota·만료 alert가 의뢰자 연락처로 간다.
- [ ] Cutover 후 전달자 개인/shared access, token, deploy key, API key를
      회수하고 access audit 증거를 남겼다.
- [ ] 06-Cutover/04-access-and-secret-rotation.pdf와
      07-Hypercare/02-final-access-audit.pdf에 최종 결과를 연결했다.

## 7. 근거 파일

- 환경 계약: .env.dev.example, .env.prod.example,
  docs/03-design/dev-prod-environment-spec.md
- Admin web: app/admin/README.md
- API/Vercel 예외: api/service/README.md, vercel.json, app.py
- DB: db/README.md, db/migrations/
- storage: storage/README.md,
  docs/03-design/object-storage-evidence-bucket-baseline.md
- LLM: worker/pipeline/fpds_ai_runtime.py,
  api/service/api_service/source_catalog.py
- monitoring: shared/observability/README.md,
  docs/03-design/monitoring-error-tracking-baseline.md
- 전체 인수 순서:
  docs/01-planning/fpds-admin-handover-minimum-playbook.md
