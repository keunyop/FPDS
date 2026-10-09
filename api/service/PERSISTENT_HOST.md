# FPDS 지속 실행 수집 서버

2026-10-08 · Admin: https://fpds-three.vercel.app

현재 코드를 유지하는 구성은 **Vercel Admin → HTTPS API 서버 → 같은 서버의 Worker**다.
기존 Public 앱/API는 계속 사용할 수 있다. API가 수집 프로세스를 직접 시작하므로
Worker만 다른 서버에 설치해도 기존 Vercel API의 수집 요청이 그 서버로 전달되지는 않는다.
별도 큐나 외부 실행 서비스는 이번 안내에 추가하지 않는다.

이 문서는 서버 설치 절차와 설정 예제다. 서버 구매·생성, 원격 설치, DNS 변경,
환경변수 등록, 재배포, DB 변경이나 유료 수집은 이번 작업에서 실행하지 않았다.

## 1. 준비할 것

- 계속 켜져 있고 유휴 종료가 없는 Ubuntu 서버 한 대와 운영자 SSH 접근.
  초기 용량 검토 기준은 2 vCPU / RAM 4 GB이며, 보장 용량이 아니다.
  실제 브라우저 메모리·동시 수집량·evidence 증가량을 보고 조정한다.
- 해당 서버를 가리킬 API 도메인. 아래 `api.example.com`은 실제 소유한 도메인으로 교체한다.
- 승인된 기존 PostgreSQL DB, 비공개 evidence 저장소, 필요한 provider 자격증명.
  기존 데이터를 계속 쓰려면 같은 승인된 DB와 evidence 저장소를 연결한다.
- Python 3.12, uv, Git, Chrome/Chromium, 현재 S3 저장 경로를 위한 AWS CLI,
  HTTPS reverse proxy(Caddy 예시)와 영구 디스크.

[Vercel Functions 제한](https://vercel.com/docs/functions/limitations)은 실행 시간을 제한한다.
현재 `source_catalog.py`는 로컬 plan/log와 응답 이후의 `subprocess.Popen`을 사용하므로
시간 제한을 늘리는 것만으로 현재 수집 프로세스의 지속 실행이 보장되지 않는다.
서버는 수집하는 동안 sleep/scale-to-zero/재배포로 종료되지 않아야 한다.

## 2. 동일 서버에 두 Python 환경 설치

운영용 `fpds` 일반 사용자와 그 사용자가 소유한 배포 디렉터리를 준비한다.
예제 위치는 /opt/fpds 이며, 아래 설치 명령은 해당 사용자로 실행한다.
`uv` 설치는 [공식 설치 안내](https://docs.astral.sh/uv/getting-started/installation/)를 따른다.
배포 대상은 확인된 동일 Git revision이어야 한다. 미완료 로컬 변경을 임의로 옮기지 않는다.

```bash
cd /opt/fpds
uv sync --frozen --python 3.12
uv sync --directory api/service --frozen --python 3.12
```

API와 Worker는 독립 환경이다. API의 수집 launcher는 현재 API Python으로 catalog runner를
실행하고, 각 Worker stage는 저장소 루트의 `uv run --project ...`를 사용한다.
그러므로 전체 저장소, 양쪽 virtualenv와 `uv`가 service의 PATH에 있어야 한다.
운영 서버에서 Next.js Admin을 실행할 필요는 없다.

Chrome/Chromium은 일반 사용자로 headless 실행할 수 있는 실제 binary를 설치하고,
아래 환경파일의 실행 경로를 그 binary로 지정한다. Ubuntu snap wrapper를 지정했을 때의
권한/프로필 문제가 없는지 확인한다. 브라우저 sandbox를 해제하는 옵션은 추가하지 않는다.

S3-compatible 저장 구현은 Python SDK 대신 `aws s3api` 하위 프로세스를 실행한다.
`aws`가 service PATH에 있어야 하고 운영 사용자가 해당 비공개 bucket에 접근할 수 있어야 한다.
기존 FPDS storage 변수만 채워도 AWS CLI credentials가 자동 설정되는 것은 아니다.
승인된 서버 IAM role/profile 또는 AWS CLI의 `AWS_ACCESS_KEY_ID`와
`AWS_SECRET_ACCESS_KEY`를 준비한다. 임시 credentials에는 `AWS_SESSION_TOKEN`도 필요하다.

## 3. API 환경파일

[production 예제](../../.env.prod.example)를 참고해 서버에 /etc/fpds/api.env를 준비한다.
실제 secret은 Git·Admin 프로젝트에 넣지 않고 `fpds` 사용자만 읽도록 권한을 제한한다.
기존 운영 환경과 저장 prefix를 확인하고 아래 **도메인 관련 값**을 맞춘다.

```dotenv
FPDS_ENV=prod
FPDS_RUNTIME_LABEL=persistent-api
FPDS_ADMIN_WEB_ORIGIN=https://fpds-three.vercel.app
FPDS_ALLOWED_ADMIN_ORIGINS=https://fpds-three.vercel.app
FPDS_ADMIN_API_ORIGIN=https://api.example.com
FPDS_COOKIE_SECURE=true
FPDS_COOKIE_SAMESITE=Lax
FPDS_SOURCE_BROWSER_EXECUTABLE=/usr/bin/google-chrome
FPDS_SOURCE_COLLECTION_STAGE_TIMEOUT_SECONDS=1800
```

이 블록만으로 실행할 수는 없다. DB URL, session/CSRF secret, 기존 Public origin/API 값,
저장소 driver/bucket/endpoint/region/prefix, 공식 domain fetch allowlist와 provider 설정도
production 예제 및 기존 승인 환경에 맞춰 채운다. country·통화·필수 금융 조건은 바꾸지 않는다.
현재 승인된 model과 key를 사용하며 수집 전에 해당 환경의 provider 사용 권한을 확인한다.
BX-PF를 새로 연결하지 않는다. 기존 승인된 연동이 없으면 `FPDS_BXPF_MODE=disabled`를 사용한다.

새 API와 기존 API가 같은 계정을 사용하려면 동일한 승인 DB를 연결한다.
API 대상을 바꾼 후에는 재로그인한다. 호스팅 전환을 이유로 계정을 다시 bootstrap하지 않는다.
서로 다른 환경의 session/CSRF secrets를 복사하지 않는다.

S3 사용 시 evidence는 기존 비공개 bucket에 보존하고, plan/log는 저장소의
`tmp/source-catalog-collections`, `tmp/source-collections`, `tmp/aggregate-refresh`에 쓴다.
이 디렉터리는 `fpds`가 쓸 수 있어야 하며 release 교체 때 삭제하지 않는다.
Filesystem storage를 사용하는 기존 환경이면 각 stage의 filesystem root도 영구 디스크에
지정하고 기존 object key/evidence를 보존한다. 새로 빈 저장소를 연결해 과거 근거를 잃지 않는다.

기존 DB는 [DB 구축 안내](../../db/README.md)를 참고해 migration_history와 현재 schema를
확인하고 필요한 미적용 migration만 따로 계획한다. 구축 문서의 빈 DB용 전체 적용 명령을
기존 운영 DB에 그대로 실행하지 않는다. 이번 도메인 변경은 migration이 필요하지 않다.

## 4. systemd로 API 지속 실행

아래는 /etc/systemd/system/fpds-api.service 예제다.
설치한 uv가 /home/fpds/.local/bin 이외에 있으면 PATH를 수정한다.

```ini
[Unit]
Description=FPDS Admin API and collection launcher
Wants=network-online.target
After=network-online.target

[Service]
Type=simple
User=fpds
Group=fpds
WorkingDirectory=/opt/fpds
Environment=FPDS_ENV_FILE=/etc/fpds/api.env
Environment=PATH=/home/fpds/.local/bin:/usr/local/bin:/usr/bin:/bin
ExecStart=/opt/fpds/api/service/.venv/bin/python -m uvicorn api_service.main:app --app-dir /opt/fpds/api/service --host 127.0.0.1 --port 4000 --workers 1 --proxy-headers --forwarded-allow-ips 127.0.0.1
Restart=on-failure
RestartSec=5
KillMode=control-group
TimeoutStopSec=30
UMask=0077

[Install]
WantedBy=multi-user.target
```

API를 한 프로세스로 시작해 현재 process-local 제한과 DB pool 예산을 유지한다.
`--reload`를 사용하지 않는다. 운영자가 환경파일과 경로를 확인한 뒤 실행한다.

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now fpds-api
sudo systemctl status fpds-api
curl --fail http://127.0.0.1:4000/healthz
sudo journalctl -u fpds-api -n 100 --no-pager
```

systemd는 API를 감시한다. 이미 시작한 수집을 자동 이어받는 영속 큐는 현재 없다.
API 재시작/서버 재부팅 시 같은 service의 수집 하위 프로세스도 종료된다.
새 수집 요청을 멈추고 Runs가 종료됐는지 확인한 뒤 정상 배포·재시작한다.
비정상 종료 시 plan/log와 Runs를 먼저 대조하고 기존 실패/재시도 흐름을 사용한다.
이미 발행된 상품을 덮어쓰거나 실패한 수집을 완료로 바꾸지 않는다.

## 5. HTTPS와 Vercel Admin 연결

API 도메인의 DNS를 서버에 연결하고 HTTPS proxy만 외부에 공개한다.
Caddy 예제는 다음과 같다. API port 4000은 localhost로 유지하고 비공개 evidence나
저장소 디렉터리는 HTTP 파일 서버로 노출하지 않는다.

```caddyfile
api.example.com {
    reverse_proxy 127.0.0.1:4000
}
```

[Caddy 자동 HTTPS](https://caddyserver.com/docs/automatic-https) 조건에 맞게 DNS,
80/443 접근과 certificate 저장 디렉터리를 준비한다. SSH는 운영자 접근으로 제한한다.
기존 audit IP와 trusted proxy 동작도 HTTPS 경유 smoke에서 확인한다.

새 API의 HTTPS health와 인증 조회가 통과한 뒤 **Vercel Admin 프로젝트의 Production**에서
`FPDS_ADMIN_API_ORIGIN=https://api.example.com`로 변경하고 Admin을 재배포한다.
이 값에 Admin 주소를 넣지 않는다. Preview는 별도 격리 API를 유지한다.
기존 Public의 API 대상은 이 작업을 이유로 바꾸지 않는다.
기존 Vercel public-read API는 계속 운영할 수 있지만 같은 범위의 수집을 두 API에서
동시에 시작하지 않는다. 새 API가 같은 DB를 쓰더라도 runtime version과 설정은 따로 확인한다.

## 6. 운영 전 확인과 rollback

1. 새 서버 /healthz의 collection process/accuracy/market profile version을
   배포 revision과 비교한다. 이번 확인의 기존 Vercel API는 process v9였으며,
   작업 폴더의 최신 변경은 v10이다. 어떤 revision이 실제 배포됐는지 확인한다.
2. Admin 로그인·국가 선택·재로그인·조회·로그아웃과 Secure/HttpOnly/CSRF cookies를 확인한다.
   role/CSRF/국가 격리 거부는 격리 환경의 기존 테스트로 확인한다.
3. 브라우저 binary, AWS CLI, 비공개 저장소 권한과 DB 연결을 확인한다.
4. 실제 수집이 별도로 허용된 환경에서 소규모 scope 하나만 실행한다.
   API 응답 후에도 runner가 남아 있고 Runs가 terminal 상태가 되는지 확인한다.
   plan/log, evidence 저장, 자동 승인/제외와 Public projection 결과를 각각 확인한다.
   missing essential은 자동 제외하며 수동 상품 승인으로 해결하지 않는다.
5. API restart, provider 실패, stage timeout, 저장 권한 오류는 격리 환경에서 확인한다.
   실제 수집 완료와 재부팅 후 자동 복구는 서로 다른 검증이다.

연결 실패 시 Admin의 API origin을 이전 정상 API로 되돌려 재배포하고 재로그인한다.
DB/evidence/진행 중 수집은 웹 rollback으로 복구되지 않는다.
이 서버 구성은 요청 종료 이후 수집 지속 실행을 제공한다. 장애 이후 자동 이어받기와
다중 서버 분산 실행이 필요하면 별도 durable queue 설계를 요청해야 한다.
