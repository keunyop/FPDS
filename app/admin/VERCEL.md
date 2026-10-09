# FPDS Admin Vercel 배포 가이드

2026-10-08 · Product Owner가 Admin 배포 완료를 알렸다. 현재 Admin 주소는
https://fpds-three.vercel.app 이다. 이번 작업의 원격 설정·검증 결과는 아래에 구분한다.

## 프로젝트 설정

같은 Git 저장소 `keunyop/FPDS`를 사용하는 기존 Admin 프로젝트를 유지한다.
프로젝트 설정은 다음과 같다. 새 프로젝트를 다시 만들 필요는 없다.

| 항목 | 값 |
|---|---|
| Production domain | `https://fpds-three.vercel.app` |
| Root Directory | `app/admin` |
| Framework Preset | Next.js |
| Node.js Version | 24.x |
| Package manager | `pnpm@10.33.0` (`package.json`) |
| Install Command | `npx --yes pnpm@10.33.0 install --frozen-lockfile` |
| Build Command | `npx --yes pnpm@10.33.0 run build` |
| Output Directory | Next.js 기본값 |

Admin의 [vercel.json](vercel.json)을 사용한다. 저장소 루트의 `vercel.json`은
기존 FastAPI 프로젝트 설정이며 Admin 설정으로 바꾸지 않는다.
이 가이드는 Git Import 배포를 기준으로 한다. 현재 루트 `.vercelignore`는 `app/`을
제외하고 기존 루트 CLI 연결도 API용일 수 있으므로 루트에서 그대로 CLI 배포하지 않는다.

Public은
`app/public`을 사용하는 별도 프로젝트다. Admin은 패키지 밖의 소스를 import하지
않으므로 외부 루트 소스 포함 옵션은 필요하지 않다.

[Vercel 모노레포 문서](https://vercel.com/docs/monorepos)에 따라 프로젝트마다
Root Directory를 지정한다. Git Import 방식으로 배포한다면 필요한 변경을 먼저
배포 대상 브랜치에 반영한다. 기존 API/Public 프로젝트가 같은 브랜치에 연결되어
있으면 push가 그 프로젝트들의 자동 배포도 유발할 수 있으므로 연결 설정을 확인한다.

## 환경변수와 인증 연결

Admin 프로젝트에는 아래 서버/빌드 환경변수를 등록한다.

| 환경 | 변수 | 값 |
|---|---|---|
| Production | `FPDS_ADMIN_API_ORIGIN` | 기존 API 사용 시 `https://switchabank-api.vercel.app` |
| Preview | `FPDS_ADMIN_API_ORIGIN` | 별도 Preview API의 고정 HTTPS origin |
| Local | `FPDS_ADMIN_API_ORIGIN` | `http://localhost:4000` |

설치와 빌드가 `npx --yes pnpm@10.33.0`을 직접 실행한다. 저장소 루트에는
`package.json`이 없으므로 Vercel의 루트 Corepack 자동 발견에 의존하지 않는다.
`ENABLE_EXPERIMENTAL_COREPACK`은 필요하지 않으며 기존에 등록했다면 제거한다.
Admin의 `packageManager`와 frozen lockfile은 그대로 유지하며 `engines.node`는 24.x다.
[Vercel 사용자 지정 설치 명령](https://vercel.com/docs/builds/configure-a-build)을 따른다.

2026-10-08 설치 실패 복구: 수정한 `app/admin/vercel.json`을 push한 뒤 새 commit을
배포한다. Dashboard의 Install/Build Command에 기존 `pnpm ...` Override가 있으면
저장소 설정을 사용하도록 Override를 해제하거나 위 명령으로 동일하게 맞춘다.
Root Directory는 `app/admin`을 유지한다. 이전 실패 deployment를 같은 commit으로
재시도하기보다 수정된 commit을 배포한다. 빌드 로그에서 pnpm 10.33.0 실행과 frozen
install 성공을 확인한다. 잠금파일을 삭제하거나 frozen 검증을 해제하지 않는다.

Preview API는 분리된 DB와 해당 환경의 session/CSRF secret을 사용한다.
Preview에 Production API를 그대로 연결하면 로그인·국가 전환·운영 mutation이
실제 데이터에 영향을 주므로 이 가이드의 기본 구성으로 사용하지 않는다.
`NEXT_PUBLIC_*` 변수로 API 주소나 비밀을 전달하지 않는다. `.env.dev` 또는
`.env.local` 업로드도 하지 않는다. Admin의 [.vercelignore](.vercelignore)가
환경 파일·로컬 빌드·의존성 디렉터리를 제외한다.

Vercel에서는 API origin이 없거나 HTTP/localhost/경로/인증정보가 포함된 값이면
API 연결을 거부한다. 주소 변경은 재배포 후 반영한다. API가 Vercel Deployment
Protection으로 서버 호출을 차단하면 보호를 무작정 해제하지 않고 접근 가능한
승인된 API origin을 준비한다. 이 변경에는 bypass secret 연동이 없다.

브라우저는 Admin의 `/api/admin/auth/countries`, `/api/admin/auth/login`,
`/api/admin/auth/signup-requests`, `/api/admin/auth/logout`에 요청한다. Next.js가 고정된 API 경로로 중계하고, API가 발급한
`fpds_admin_session`/`fpds_admin_csrf` 쿠키를 Admin 호스트에 설정한다.
HttpOnly·SameSite·만료·CSRF 속성을 보존하며 HTTPS 응답에는 Secure를 적용한다.
이후 서버 조회와 기존 mutation 프록시가 쿠키/CSRF를 API로 전달한다.
새 인증 프록시의 POST는 Admin과 정확히 같은 Origin에서만 허용한다.
API의 session·role·국가·CSRF 검증이 계속 최종 권한을 결정한다.
기존 감사 입력인 User-Agent와 X-Forwarded-For도 전달한다. 최종 감사 IP는 API의
ingress 및 기존 전달 IP 해석을 따르므로 실제 환경의 기록을 smoke에서 확인한다.

같은 호스트에서 브라우저 요청이 끝나므로 인증 프록시는 API의 브라우저 CORS 허용에
의존하지 않는다. API의 명시적 Admin origin 목록은 새 주소와 일치시키되 기존에
승인된 다른 Admin origin과 Public CORS 설정을 보존한다.
API의 `FPDS_ADMIN_WEB_ORIGIN=https://fpds-three.vercel.app` 및
`FPDS_ALLOWED_ADMIN_ORIGINS=https://fpds-three.vercel.app`로 맞추고,
`FPDS_COOKIE_SECURE=true`, `FPDS_COOKIE_SAMESITE=Lax` 및 기존 환경별 secrets를
유지한다. 이는 API 프로젝트 설정이며 Admin에 secret을 복사하지 않는다.
현재 계정은 API가 연결한 DB에 있어야 하며 새 계정 bootstrap/승인은 별도 작업이다.

기존에 명시적으로 허용한 다른 Admin origin이 있으면 해당 항목을 보존하고 새 origin을
쉼표로 추가한다. localhost 개발 설정은 로컬 파일에서 유지한다. origin 값에는 끝 `/`를
붙이지 않는다. `.env.prod.example` 변경은 실제 Vercel 환경변수를 변경하지 않는다.
API 프로젝트의 Production 환경변수를 변경한 뒤 해당 API를 재배포해야 반영된다.
Admin 주소를 `FPDS_ADMIN_API_ORIGIN`에 넣지 않는다. 이 변수는 FastAPI 주소다.
Admin의 API 대상 주소를 바꾼 경우에는 Admin도 재배포한다.

이번 작업 환경에는 Vercel 관리 인증이 없어 Dashboard 값 조회·수정과 원격 재배포를
수행하지 못했다. API 프로젝트의 위 두 origin과 Secure/Lax 설정은 Dashboard에서
확인해야 한다. Preview 설정은 별도 격리 API의 실제 origin을 유지한다.

## 현재 호스팅 읽기 전용 확인 - 2026-10-08

- 새 Admin `/admin/login`: HTTP 200.
- 새 Admin `/api/admin/auth/countries`: HTTP 200, JSON 응답.
- 기존 API `/healthz`: HTTP 200, status ok, collection process v9.
- 기존 API에 `Origin: https://fpds-three.vercel.app`로 보낸 CORS preflight:
  HTTP 400 / Disallowed CORS origin. 새 주소의 API CORS 허용이 아직 반영되지 않았다.

프록시의 국가 조회가 정상이라는 결과와 API의 CORS 거부는 별개의 결과다.
로그인 계정·세션·권한·실제 수집은 이번 확인에서 검증하지 않았다.
Dashboard 환경변수와 serving runtime 변경 완료로 간주하지 않는다.

## 수집 운영 경계

Admin 화면을 Vercel로 옮기는 것과 수집 프로세스를 옮기는 것은 별도다.
현재 API의 `source_catalog.py::_launch_source_catalog_collection_runner`는
저장소의 `tmp/source-catalog-collections`에 plan/log를 쓰고 `subprocess.Popen`으로
API 응답 이후에도 계속 실행되는 수집 프로세스를 시작한다. Worker에도 로컬 실행
환경과 비공개 evidence 저장소/provider 설정이 필요하다.

[Vercel Functions 실행 제한](https://vercel.com/docs/functions/limitations)과
[Python runtime](https://vercel.com/docs/functions/runtimes/python)을 고려하면,
현재 detached subprocess가 Vercel에서 수집 완료까지 지속된다고 보장할 수 없다.
기존 API 배포도 최초 public-read 용도로 문서화되어 있다. 로그인·조회 검증을
수집 운영 검증으로 취급하지 않는다.

전체 수집 운영에는 현재 API/Worker를 실행할 지속 실행 서버의 HTTPS origin 또는
별도로 승인된 durable 실행 연결이 필요하다. Vercel Admin은 인터넷에서 접근할
수 없는 사용자 PC의 localhost API에 연결할 수 없다. 장시간 수집 서버를 정하기
전에는 Vercel API를 대상으로 실제 수집 버튼을 테스트하지 않는다. 이 준비에서는
Worker host/queue/integration을 새로 만들거나 수집을 시작하지 않는다.
API/Worker 현행 코드·migration 상태도 별도 확인하며 Admin 배포로 갱신되지 않는다.
서버 준비와 연결 순서는 [지속 실행 수집 서버 가이드](../../api/service/PERSISTENT_HOST.md)를 따른다.

## 검증과 실제 배포 순서

로컬에서 실행 중인 Admin/수집 환경과 분리된 clone에서 확인한다.

```powershell
pnpm --dir app/admin install --frozen-lockfile
pnpm --dir app/admin run test
pnpm --dir app/admin run typecheck
pnpm --dir app/admin run build
git diff --check
```

실제 배포 시 다음 순서로 진행한다.

1. API 환경·migration·계정·현행 serving version과 장시간 수집 호스트를 확인한다.
   이 변경 자체에는 migration이나 API/Worker 코드 변경이 없다.
2. 새 Admin 프로젝트에 위 Root Directory/Node 버전과 환경별 API origin을 설정한다.
   분리된 Preview API가 아직 없으면 Preview의 API 연결은 준비될 때까지 두지 않는다.
3. Preview를 배포하고 아래 smoke를 수행한다. 통과 후 Production 배포를 진행한다.
4. Production의 실제 도메인을 확인하고 API의 Admin web origin을 맞춘다.
   동일 smoke를 반복한 뒤 배포 URL/버전/결과를 기록한다.

Smoke 항목:

- `/` → `/admin` → 미인증 `/admin/login`; EN/KO/JA와 `next`/locale 보존.
- 국가 목록 성공/빈 목록/오류, 잘못된 로그인과 API 연결 실패 안내.
- 격리된 테스트 계정 로그인 후 Admin 호스트에 HttpOnly session 및 CSRF cookie가
  생기고 새로고침·직접 URL 진입에도 세션이 유지되는지 확인.
- `read_only`의 조회 및 mutation 거부, 다른 국가 데이터 접근 거부,
  CSRF 누락/오류 거부를 격리 환경에서 확인. 계정 권한을 바꾸어 우회하지 않는다.
- 국가 전환 후 Overview 이동, 로그아웃 후 API 세션 폐기·두 쿠키 삭제·보호 URL 차단.
- 가입 요청을 시험하려면 격리 API/DB의 테스트 계정을 사용하고 기존 관리자 승인
  절차를 유지한다. Production smoke에서 새 계정/운영 데이터 mutation은 수행하지 않는다.
- 390px/태블릿/데스크톱 로그인 및 가입, 키보드 focus, 요청 pending/error 상태 확인.
- 장시간 수집은 지속 실행 호스트가 준비된 뒤 별도로 허용된 환경에서 검증한다.

실패 시 기존 로컬 Admin을 계속 사용한다. 첫 Vercel 배포는 이전 Admin 배포가 없으므로
해당 배포의 접근/트래픽을 중단하고 설정을 수정한다. 이후 릴리스는 직전 정상 Admin
배포로 rollback한다. Vercel 웹 rollback은 DB·수집·API 설정·기존 API 세션을 복구하지
않으므로 이들을 별도로 확인한다. 로컬과 배포 호스트의 쿠키는 별개라 재로그인이 필요하다.
