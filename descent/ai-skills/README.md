# FPDS Admin AI 개발 스킬셋

한국어 초안 v1 · 기준일: 2026-10-06 · 진입 문서: [Admin 개발 인계 가이드](../FPDS_Admin_개발_가이드.md)

이 패키지는 인수자가 AI에게 FPDS Admin 개발을 맡길 때 사용할 실제 작업 지침이다. 각 폴더의 SKILL.md에는 선택 조건, 읽을 기준 문서, 코드 진입점, 유지할 계약과 검증 산출물이 들어 있다. 일반적인 프로그래밍 설명을 반복하지 않고 FPDS에서 실수하기 쉬운 경계를 안내한다.

## 1. 제공 파일

```text
descent/ai-skills/
  README.md
  fpds-admin-ui/SKILL.md
  fpds-admin-api/SKILL.md
  fpds-collection-evidence/SKILL.md
  fpds-database-change/SKILL.md
  fpds-admin-verification/SKILL.md
```

| 스킬 | 언제 선택하는가 | 필요한 입력 | 기대 산출물 |
|---|---|---|---|
| [fpds-admin-ui](fpds-admin-ui/SKILL.md) | Admin 화면·폼·목록·dialog·route·다국어 상호작용 | route, role/country/locale, 재현 상태, 기대 동작, layout 영향 | 기존 token/component를 사용한 UI 변경, 상태·locale·화면 검증 |
| [fpds-admin-api](fpds-admin-api/SKILL.md) | FastAPI 서비스, session/RBAC/CSRF/국가 scope, proxy 계약 | endpoint/method, request/response, role/country, 정상·실패 재현 | 최소 API/proxy 변경, 서버 허용·거부 회귀, 독립 API 환경 결과 |
| [fpds-collection-evidence](fpds-collection-evidence/SKILL.md) | 공식 evidence 누락, parser/field loss, origin·금융 gate 실패 | bank/type/country/Run, 보존 registry/snapshot/artifact 접근, 독립 기대 사실 | 최초 차이 진단, source-backed shared fix, 정상/경계/실패 회귀, 제외·생략 근거 |
| [fpds-database-change](fpds-database-change/SKILL.md) | schema/migration/persistence 변경 준비 | 현재 SQL/schema/history, 대상 환경, 허용 쓰기, 보존·복구 조건 | migration/contract delta, 적용·복구 계획, 격리 DB 검증 또는 명시적 미수행 |
| [fpds-admin-verification](fpds-admin-verification/SKILL.md) | 변경의 acceptance 확인과 개발 인계 정리 | diff, goal ownership, 이미 실행한 결과, 변경 runtime | 영향별 검증, 정확한 성공/실패·한계 보고, journal과 최종 diff |

현재 스킬은 repository source를 참조하는 문서 패키지다. installer, live collection/deployment script, secret이나 외부 MCP 연결을 포함하지 않는다. 새 executable helper는 반복되는 실제 필요가 확인될 때만 추가하고 별도로 검증한다.

## 2. 공통 실행 조건

AI 도구는 인계받은 FPDS clone의 파일 읽기·편집·터미널에 접근할 수 있어야 한다. repository context 없이 SKILL.md만 제공하면 현재 구현을 검증할 수 없다. 외부 연결/권한은 인수자의 환경에서 별도로 제공한다.

스킬 본문의 파일 경로는 모두 FPDS repository root 기준이다. SKILL.md를 다른 곳에 복사해도 repository의 docs/app/api/worker/db 경로를 현재 clone 루트에서 찾는다. 변경 전에 AGENTS.md, root README, development journal, docs map을 읽고 관련 boundary README로 진행한다. 한국어 가이드가 최신 원문 계약보다 우선하지 않는다.

필요한 스킬만 선택한다. UI+API처럼 두 영역에 걸치면 둘 다 읽고 한 acceptance에 연결한다. 다섯 파일을 매 작업마다 일괄 로드하지 않는다. 검증 스킬은 마지막 결과 확인에 사용하며 기존에 통과한 테스트를 사유 없이 전부 반복하는 지시가 아니다.

## 3. 인수자 환경에서 사용하기

### 3.1. 파일을 직접 읽게 하는 방식

어떤 AI 코딩 도구든 저장소 문서를 읽을 수 있다면 다음처럼 시작할 수 있다. 이 패키지는 descent 아래에 보관되므로 그 자체로 자동 등록됐다고 가정하지 않는다.

```text
이 FPDS repository의 AGENTS.md와 개발 시작 문서를 읽으세요.
descent/FPDS_Admin_개발_가이드.md와
descent/ai-skills/fpds-admin-api/SKILL.md를 적용하세요.
[받은 변경 요청과 재현 사례]를 구현하고 관련 검증·journal까지 완료하세요.
이번 작업의 허용 대상은 [격리 clone / fixture 또는 승인된 dev 환경]입니다.
라이브 데이터 쓰기와 배포는 이번 요청 범위에 포함하지 않습니다.
```

대괄호 부분은 요청마다 실제 내용으로 채우는 입력이며 구현할 기능 목록이 아니다. 허용 범위에 쓰기/배포가 이미 포함됐다면 그 내용을 그대로 적고 스킬을 이유로 같은 승인을 반복하지 않는다.

### 3.2. Codex 스킬로 옮기는 방식

현재 공식 OpenAI 문서의 repository skill 위치는 인수 clone의 .agents/skills이며 사용자 공통 위치는 사용자 홈의 .agents/skills다. 필요한 스킬 폴더 전체를 인수 환경의 해당 위치로 복사하고, 같은 이름의 기존 스킬이 있으면 덮어쓰기 전에 내용을 비교한다. 이 패키지는 descent에 보관만 했으며 자동 discovery 경로나 사용자 전역 설정을 변경하지 않았다. 등록 후 인수자의 도구가 인식하는지 확인한다. 위치와 discovery 규칙은 [공식 OpenAI Build skills 문서](https://learn.chatgpt.com/docs/build-skills#where-codex-loads-local-skills)를 따른다.

```text
$fpds-admin-api
FPDS Admin의 [endpoint] 변경을 구현해주세요.
대상 clone과 기대 동작, role/country 경계는 아래와 같습니다: ...
```

다른 AI 도구는 그 도구의 skill/context 등록 방식을 따른다. 자동 선택/검색 규칙이 다르면 파일 직접 읽기 방식을 사용한다. 외부 installer/plugin이나 새 account 연결은 필수 조건이 아니다.

## 4. 작업별 예시

예시는 이미 허용된 작업을 전달하는 형식이며 새 기능의 승인이나 실행 요청이 아니다.

### 4.1. Admin UI 표시 수정

```text
descent/ai-skills/fpds-admin-ui/SKILL.md를 적용해주세요.
Runs의 [구체적인 오류 상태]에서 [기대 표시]가 나오도록 개선해주세요.
EN/KO/JA, session country와 safe Auto refresh를 유지해주세요.
정확한 390px/768px/1440px, keyboard, empty/error/success 상태를 확인하고
Admin 관련 테스트 결과와 journal을 남겨주세요.
```

### 4.2. API 계약 또는 권한 수정

```text
descent/ai-skills/fpds-admin-api/SKILL.md를 적용해주세요.
[method/endpoint]의 [재현 가능한 문제]를 수정해주세요.
정상 admin, 비관리자 거부, CSRF 실패, 다른 국가 ID를 회귀로 확인하세요.
반환 type/proxy/status/body와 독립 API 환경 테스트를 함께 확인하세요.
라이브 계정/DB 조작과 배포는 별도 허용 없이는 수행하지 마세요.
```

### 4.3. 수집 evidence 누락 교정

```text
descent/ai-skills/fpds-collection-evidence/SKILL.md를 적용해주세요.
[Run ID / bank / type / country]의 보존된 동일 입력에서
[공식 원문에 있는 기대 사실]이 사라지는 최초 위치를 찾고 수정해주세요.
source hash, 실제 parent/origin, stored artifact와 financial 조건을 확인하세요.
regression을 먼저 추가하고 모든 관련 prompts/gates를 함께 검토하세요.
이번 범위는 offline fixture/replay이며 paid recollection과 live write는 제외합니다.
```

### 4.4. schema 변경 준비

```text
descent/ai-skills/fpds-database-change/SKILL.md를 적용해주세요.
[승인된 schema 변경]의 SQL과 persistence 계약을 준비해주세요.
source migration과 실제 dev schema/history를 구분하고 적용/복구 계획을 작성하세요.
대상 [격리 dev DB]에 대한 [허용된 적용 검증]만 수행하세요.
계정/canonical/production data 변경을 섞지 마세요.
```

### 4.5. 결과 검증과 인계

```text
descent/ai-skills/fpds-admin-verification/SKILL.md를 적용해주세요.
이번 diff와 goal acceptance에 필요한 검증을 완료하고 journal을 갱신하세요.
이미 수행된 테스트, 현재 변경 실패, 기존 결함, 환경 한계를 구분하세요.
local replay/실제 serving version/실제 canonical/Public 결과를 각각 보고하세요.
다른 goal ownership과 사용자 변경을 보존하세요.
```

## 5. 권한과 비용의 해석

스킬 사용은 원래 요청에 없는 상태 변경 권한을 만들지 않는다. code change, DB migration 적용, 계정 생성/회수, collection/provider 호출, canonical/publication, deployment의 대상·환경·비용을 구분한다. 이미 명시적으로 허용된 작업은 해당 범위에서 계속하며, 새 위험 경계를 넘기 전에 구체적 변경과 검증/복구 조건을 준비한다.

상품 데이터는 사람 검토/수정 승인 없이 자동 gate를 통과하거나 제외된다. 계정·보안·인수 승인은 별도다. AI가 충분히 확신한다는 이유로 금융 사실, false/zero나 provenance를 생성하지 않는다. optional completeness를 위해 호출·retry를 추가하지 않는다.

## 6. 검증과 유지 방법

SKILL.md는 name/description YAML frontmatter와 Markdown body로 구성된다. folder와 name이 일치해야 하며 name은 영문 소문자·숫자·hyphen을 사용한다. 설명에는 적용할 작업과 경계를 적는다. 본문에서 repository-root 경로를 사용하는 이유는 인수자의 skill directory로 이동해도 참조가 유지되게 하기 위해서다.

이 패키지는 skill-creator 작성 규칙을 따르며 기존 제품 계약을 복제해 새 권위로 만들지 않는다. 제품 workflow/금융 contract/runtime 경계가 실제 바뀌면 관련 스킬과 개발 가이드도 함께 검토한다. 코드 identifier/경로/명령은 영어판에서도 유지하고 description/body만 의미를 확인해 번역한다.

인수자가 실제 작업에서 스킬을 사용한 뒤 변경 범위, 필요한 source 접근, 적절한 검증 선택, 결과 보고가 맞는지 확인한다. 형식 검사만으로 AI의 판단 품질이 입증되는 것은 아니다. 개선은 재현된 오판이나 누락에 한정하고 일반 규칙을 계속 쌓지 않는다.

개발 가이드의 H11 문서/harness 검사를 실행하고 Git diff를 확인한다. 새 tooling 설치 없이 검증할 수 없는 항목은 수행하지 않은 이유를 기록한다. 라이브 계정/유료 수집/Production으로 스킬 동작을 시험하지 않는다.
