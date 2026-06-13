# FPDS 고객사 시연 시나리오 - Admin 수집부터 Public 결과까지


## 1. 시연 목표

이번 시연의 핵심 메시지는 FPDS가 단순한 상품 목록 화면이 아니라, 공식 금융기관 원천 자료를 근거로 상품 데이터를 수집, 검증, 추적, 공개하는 데이터 플랫폼이라는 점이다.

고객에게 전달할 메시지:

1. FPDS Admin에서 은행과 상품 유형 수집 범위를 운영자가 직접 통제한다.
2. FPDS는 은행 공식 웹사이트와 PDF, 상세 페이지를 수집하고 근거 자료를 보존한다.
3. 수집 과정은 수집 실행, source 찾기, evidence 저장, 상품정보 추출, 토큰 사용량 기록, audit로 추적된다.
4. 검증을 통과한 상품은 canonical product와 public aggregate projection으로 반영된다.
5. FPDS Public은 수집한 상품정보를 B2C로 제공한다.

권장 시연 범위:

| 항목 | 시연 선택 | 이유 |
|---|---|---|
| 국가 | Canada | 현재 Phase 1 구현 대상 |
| 은행 | `BMO`, `TD` | 인지도가 높고, 검증된 Big 5 범위 안에서 상품 수가 적당함 |
| 상품 유형 | `chequing`, `savings` | 고객이 이해하기 쉽고 GIC보다 설명 부담이 낮음 |
| 예상 상품 수 | 17개 | 현재 source-backed golden dataset 기준 BMO 9개 + TD 8개 |

예상 상품 수:

| 은행 | Chequing | Savings | 합계 |
|---|---:|---:|---:|
| BMO | 5 | 4 | 9 |
| TD | 5 | 3 | 8 |
| 합계 | 10 | 7 | 17 |

---

## 3. 발표 시나리오

### 3.1 오프닝 멘트

권장 멘트:

> FPDS가 은행들의 다양한 공개된 상품 페이지를 수집하여 표준화된 상품정보로 바꾸는 과정을 보여드리겠습니다. 운영자는 Admin에서 은행과 상품 유형을 선택하고, FPDS는 공식 source를 수집해 snapshot, parsing, evidence retrieval, extraction, normalization, validation을 거친 뒤 검증된 상품을 public dashboard에 반영합니다. 또한 어떤 agent가 실행됐고, AI가 어디서 사용됐으며, token usage와 audit가 어떻게 남는지도 함께 보여드리겠습니다.

비즈니스 문제를 짧게 정리:

- 은행 상품 정보는 상품 상세 페이지, 요율 페이지, PDF, 동적 페이지에 흩어져 있다.
- FPDS는 이 불안정한 원천 정보를 재현 가능하고 검토 가능한 canonical 데이터로 전환한다.
- Public 사용자는 깔끔한 비교 화면을 보고, 운영자는 evidence, run 진단, usage, audit, health를 본다.

### 3.2 권장 발표 시간

| 구간 | 시간 | 목표 |
|---|---:|---|
| 1. 문제와 시연 범위 | 3분 | 왜 FPDS가 필요한지와 오늘 범위를 고정 |
| 2. 아키텍처 개요 | 5분 | public/admin/API/worker/storage 경계 설명 |
| 3. Admin coverage와 collection 실행 | 7분 | 은행/상품유형 통제와 collection 시작 |
| 4. Run 진단과 source lineage | 8분 | stage, source, candidate, failure/warning 확인 |
| 5. AI agent와 token usage | 8분 | AI 사용 위치, fallback, usage dashboard 설명 |
| 6. Public grid와 dashboard | 8분 | BMO/TD chequing/savings 결과 확인 |
| 7. Governance와 다음 단계 | 5분 | evidence, review, audit, security, roadmap 정리 |
| 합계 | 44분 | Q&A 10-15분 확보 |

20분 축약 버전:

1. 2분: 목표와 아키텍처.
2. 4분: Admin coverage와 collection launch.
3. 5분: 완료된 run detail과 usage dashboard.
4. 6분: Public products와 dashboard.
5. 3분: 리스크, 제한사항, 다음 단계.

---

## 4. 시연 전 준비 체크리스트

### 4.1 실행 환경

터미널을 분리해서 실행한다.

```powershell
# Terminal 1 - API
$env:FPDS_ENV_FILE=".env.dev"
uv run --directory api/service uvicorn api_service.main:app --reload --host localhost --port 4000
```

```powershell
# Terminal 2 - Admin web
cd app/admin
pnpm run dev
```

```powershell
# Terminal 3 - Public web
cd app/public
pnpm run dev
```

예상 URL:

| Surface | URL |
|---|---|
| API health | `http://localhost:4000/healthz` |
| Admin | `http://localhost:3001/admin` |
| Public dashboard | `http://localhost:3000/dashboard` |
| Public product grid | `http://localhost:3000/products` |

### 4.2 상태 확인

시연 전 실행:

```powershell
api\service\.venv\Scripts\python.exe tmp\fpds_admin_collection_goal_tool.py --env-file .env.dev state
```

확인할 것:

- `active_catalog_item_count`가 15인지.
- `canonical_product`가 0이 아닌지.
- `public_product_projection`이 0이 아닌지.
- 최신 collection에 failed run이 없는지.
- review queue가 0이거나, 남아 있다면 이유를 설명할 수 있는지.

### 4.3 데모 범위 사전 수집

고객 앞에서 은행 사이트 지연을 기다리지 않도록, 가능하면 시연 전에 BMO/TD chequing/savings 범위를 미리 수집한다.

```powershell
api\service\.venv\Scripts\python.exe tmp\fpds_admin_collection_goal_tool.py --env-file .env.dev launch --only-bank BMO --only-bank TD --only-product-type chequing --only-product-type savings
```

반환된 `collection_id`로 polling:

```powershell
api\service\.venv\Scripts\python.exe tmp\fpds_admin_collection_goal_tool.py --env-file .env.dev wait --collection-id <collection_id> --timeout-seconds 1800 --poll-seconds 20 --brief
```

주의:

- 현재 helper의 `compare` 명령은 Big 5 전체 98개 golden dataset과 비교한다.
- 17개 데모 subset 검증에는 그대로 사용하지 않는다. subset 비교가 필요하면 helper에 scope filter를 추가해야 한다.
- 고객 시연 중에는 live collection을 "실행 가능함"을 보여주는 용도로 사용하고, 결과 확인은 사전 완료 run tab을 백업으로 열어둔다.

---

## 5. 상세 시연 절차

### Step 1 - Admin 로그인과 운영자 경계 설명

화면:

- `http://localhost:3001/admin/login`
- 로그인 후 `/admin`

진행:

1. Admin 계정으로 로그인한다.
2. Admin Console이 인증된 운영자 영역임을 보여준다.
3. 좌측 navigation의 Review, Operations, Observability 그룹을 짧게 보여준다.

멘트:

> Admin은 운영자 전용 신뢰 경계입니다. source 관리, collection 실행, review, run diagnostics, audit, LLM usage는 로그인 후에만 접근할 수 있습니다. Public 사용자는 내부 evidence나 raw source trace를 보지 않습니다.

확인 포인트:

- Admin은 session auth가 필요하다.
- review/source write action은 role 권한과 CSRF token을 요구한다.
- Public과 Admin의 신뢰 경계가 분리되어 있다.

### Step 2 - Product Type과 Bank Coverage 확인

화면:

- `/admin/product-types`
- `/admin/banks`

진행:

1. 등록된 deposit product type을 보여준다: `chequing`, `savings`, `gic`.
2. `/admin/banks`에서 BMO 상세 modal을 연다.
3. BMO의 chequing과 savings coverage card를 보여준다.
4. TD도 같은 방식으로 coverage가 있음을 보여준다.

멘트:

> 운영자가 code나 JSON 파일을 직접 수정하는 방식이 아닙니다. 은행 프로필과 product coverage는 DB-backed Admin workflow에서 관리됩니다. Collection 시점에는 은행 홈페이지와 product-type definition을 기준으로 실제 detail source row가 생성됩니다.

확인 포인트:

- Bank와 product type registry가 운영 DB 기준이다.
- Generated source는 시스템이 만들며, 운영자는 inspection과 soft remove를 할 수 있다.

### Step 3 - Demo Scope Collection 실행

권장 live UI 절차:

1. `/admin/banks`에서 BMO 상세 modal을 연다.
2. BMO `Chequing` coverage card의 `Collect`를 클릭한다.
3. BMO `Savings` coverage card의 `Collect`를 클릭한다.
4. TD 상세 modal을 연다.
5. TD `Chequing` coverage card의 `Collect`를 클릭한다.
6. TD `Savings` coverage card의 `Collect`를 클릭한다.

이 방식을 쓰는 이유:

- Bank list의 bulk collect는 선택된 은행의 전체 coverage를 수집하므로 GIC까지 포함될 수 있다.
- 고객 시연 범위를 chequing/savings로 고정하려면 per-coverage `Collect`가 더 안전하다.

백업 실행 명령:

```powershell
api\service\.venv\Scripts\python.exe tmp\fpds_admin_collection_goal_tool.py --env-file .env.dev launch --only-bank BMO --only-bank TD --only-product-type chequing --only-product-type savings
```

멘트:

> Collection은 비동기 작업입니다. Admin UI는 queued run id를 빠르게 반환하고, 서버에서는 homepage discovery, source materialization, snapshot capture, parse/chunk, extraction, normalization, validation, auto-promotion 또는 review routing, aggregate refresh가 background에서 이어집니다.

확인 포인트:

- UI에 collection queued 메시지가 뜬다.
- `/admin/runs`에서 새 run을 확인할 수 있다.

### Step 4 - Run Status와 Pipeline Stage 확인

화면:

- `/admin/runs`
- `/admin/runs/:runId`

진행:

1. 최신 run을 started_at 기준으로 확인한다.
2. BMO 또는 TD run detail을 연다.
3. source count, candidate count, review queued count, partial completion flag를 보여준다.
4. stage summary와 source processing summary를 보여준다.

멘트:

> Run은 collection 실행의 운영 record입니다. 전체가 성공하면 completed가 되고, 일부 source 문제가 있어도 partial completion으로 진단 가능한 결과를 남깁니다. 따라서 운영자는 어떤 source나 stage가 문제였는지 확인하고 재시도할 수 있습니다.

설명할 pipeline stage:

1. Source catalog collection / homepage discovery.
2. Snapshot capture.
3. Parse and chunk.
4. Evidence retrieval.
5. Extraction.
6. Normalization.
7. Validation and routing.
8. Canonical upsert / auto-promotion.
9. Aggregate refresh.

### Step 5 - Generated Source와 Source Lineage 확인

화면:

- `/admin/sources?bank_code=BMO&product_type=savings`
- `/admin/sources/:sourceId`

진행:

1. BMO + savings로 source list를 filter한다.
2. source detail을 연다.
3. URL, role/status, discovery summary, AI-predicted role이 있으면 함께 보여준다.
4. recent collection history를 보여준다.

멘트:

> FPDS는 운영자가 입력한 coverage와 시스템이 생성한 source row를 분리합니다. 운영자는 은행과 상품군을 결정하고, FPDS가 그 범위 안에서 공식 detail source를 찾고 근거와 판단 정보를 남깁니다.

확인 포인트:

- Source URL은 은행 공식 public URL이다.
- Discovery metadata가 source role 판단 근거를 설명한다.
- 잘못 생성된 source는 삭제가 아니라 soft remove로 audit와 history를 보존한다.

### Step 6 - Evidence와 Reviewability 설명

화면:

- review task가 있으면 `/admin/reviews`, `/admin/reviews/:reviewTaskId`
- review task가 없으면 `/admin/runs/:runId`와 `/admin/sources/:sourceId`

진행:

1. review task가 있으면 proposed fields, evidence links, model execution references, decision actions를 보여준다.
2. review task가 없으면 `review_queued_count = 0`을 보여주고 auto-validation/auto-promotion path를 설명한다.

멘트:

> FPDS의 목표는 blind automation이 아닙니다. validation issue, 낮은 confidence, ambiguous mapping, dynamic product type은 review로 보냅니다. 반대로 policy를 만족한 candidate는 audited canonical path를 통해 auto-promote됩니다.

확인 포인트:

- Evidence trace는 Admin-only다.
- Review action은 approve, reject, defer, edit-approve다.
- Manual override는 change history와 audit event를 남긴다.

### Step 7 - AI Agent와 Token Usage 설명

화면:

- `/admin/runs/:runId`의 usage section
- `/admin/usage`

진행:

1. run detail에서 usage summary를 보여준다.
2. `/admin/usage`에서 total, by-model, by-agent, by-run, trend, anomaly를 보여준다.
3. 필요하면 recent run으로 search/filter한다.

멘트:

> FPDS는 AI를 선택적으로 사용합니다. 모든 stage를 LLM에 맡기지 않습니다. 현재 chequing/savings 같은 지원 product type은 주로 deterministic, evidence-driven extractor와 normalizer가 처리합니다. AI는 homepage source scoring에 사용될 수 있고, 전문 parser가 없는 dynamic product type에서는 structured JSON fallback으로 사용됩니다. 모든 model execution과 usage는 run, agent, model, token count, status, estimated cost 기준으로 저장됩니다.

Agent 설명:

| Agent | 사용 시점 | 외부 LLM 사용 | Token 영향 |
|---|---|---:|---|
| `fpds-homepage-ai-parallel-scorer` | homepage-first source discovery에서 후보 link scoring | OpenAI 설정이 있을 때 사용 | prompt/completion token과 estimated cost 기록 |
| `fpds-heuristic-extractor` | chequing/savings/GIC field extraction | 사용 안 함 | execution record는 남고 token은 0 |
| `fpds-heuristic-normalizer` | canonical mapping, subtype/taxonomy, evidence link 구성 | 사용 안 함 | execution record는 남고 token은 0 |
| `fpds-dynamic-product-extractor` | 전문 parser가 없는 operator-added product type extraction fallback | 사용 가능 | token/cost 기록, manual review 우선 |
| `fpds-dynamic-product-normalizer` | dynamic product canonical fallback | 사용 가능 | token/cost 기록, manual review 우선 |
| Validation/routing policy | required field, confidence, issue code, auto-promotion/review 결정 | 사용 안 함 | LLM token 없음 |

Token/cost 설명:

- Usage는 `llm_usage_record`에 저장된다.
- 실행 문맥은 `model_execution`에 저장된다.
- Run detail은 해당 run의 usage를 집계한다.
- Usage dashboard는 provider, model, agent, run, trend, anomaly 기준으로 집계한다.
- 현재 cost estimator는 모델별 가격 외부화 전까지의 보수적 placeholder다.
  - input token estimate: `prompt_tokens * 0.0000003`
  - output token estimate: `completion_tokens * 0.0000012`
- `FPDS_LLM_PROVIDER` 또는 API key가 없으면 AI scorer/fallback은 deterministic fallback을 사용하고, 그 사실을 model execution/runtime note로 남긴다.

### Step 8 - Public Product Grid 확인

화면:

- `http://localhost:3000/products`

진행:

1. bank filter를 BMO와 TD로 설정한다.
2. product type filter를 chequing과 savings로 설정한다.
3. product card와 sort control을 보여준다.
4. product detail을 하나 연다.
5. official bank page link, public facts, estimated-interest calculator, disclosure note를 보여준다.

열어볼 만한 상품:

- BMO Savings Builder Account
- TD Growth Savings Account
- BMO Performance Chequing Account
- TD Student Chequing Account

멘트:

> Public은 최신 성공 aggregate snapshot을 읽습니다. 은행 페이지를 실시간 호출하지 않고, raw evidence나 source excerpt도 노출하지 않습니다. 사용자는 approved projection field, filter, sort, official bank link를 봅니다. 데이터 경계와 metric 산정 설명은 필요 시 별도 methodology page를 직접 URL로 열어 확인합니다.

확인 포인트:

- Public은 anonymous read surface다.
- Public product fact는 projection field이며 raw source artifact가 아니다.
- Source-derived product text는 원천 언어를 유지한다.

### Step 9 - Public Dashboard 확인

화면:

- `http://localhost:3000/dashboard`

진행:

1. 가능하면 BMO/TD chequing/savings scope를 유지한다.
2. KPI card를 보여준다.
3. Top 5 Interest Rate ranking을 보여준다.
4. ranking row에서 product detail 또는 product grid로 이동한다.

멘트:

> Dashboard는 Product Grid와 같은 public aggregate projection을 사용합니다. Metric은 현재 filter scope에 맞춰 계산되고, 필요한 numeric field가 없는 상품은 해당 비교에서 추정하지 않고 제외합니다.

확인 포인트:

- Dashboard와 Grid가 URL-based shared filter vocabulary를 사용한다.
- Freshness copy와 direct-route methodology page가 snapshot serving 방식을 설명한다.

### Step 10 - Governance와 운영 통제 확인

화면:

- `/admin/audit`
- `/admin/health/dashboard`
- `http://localhost:3000/methodology` direct route. Public top navigation menu에는 없음.

진행:

1. audit event category를 보여준다.
2. dashboard health와 latest successful snapshot 상태를 보여준다.
3. 주소창에 직접 입력하거나 미리 준비한 탭으로 public methodology page를 보여준다.

멘트:

> FPDS의 운영 모델은 의도적으로 evidence-first입니다. 내부 evidence는 private/admin에만 남기고, public은 aggregate snapshot을 제공합니다. Review와 override는 audit되고, aggregate refresh health도 운영자가 확인할 수 있습니다. 이것이 단순 수집 script와 운영 가능한 product data service의 차이입니다.

---

## 6. 아키텍처와 수집 프로세스 설명

발표용 짧은 설명:

FPDS는 네 개의 논리 경계로 설명한다.

1. Public surface: anonymous Product Grid, Product Detail, Dashboard. Methodology는 top navigation이 아니라 direct route로 제공된다.
2. Admin surface: authenticated coverage, runs, review, source inspection, audit, usage, health.
3. API/Application boundary: FastAPI public read와 protected admin operation.
4. Private worker/data boundary: source discovery, snapshots, parsing, evidence chunks, extraction, normalization, validation, canonical data, aggregate refresh, model usage records.

주요 저장소:

- Operational DB: run, candidate, review, canonical product, product version, change, audit, usage, aggregate metadata.
- Object storage: raw snapshot, parsed text, extracted artifact, normalized artifact.
- Evidence chunk / embedding table: retrieval-ready evidence와 pgvector side table. vector row가 없어도 metadata-only fallback 가능.

Collection flow:

```text
Admin coverage selection
  -> source catalog collection / homepage discovery
  -> generated source rows
  -> snapshot capture
  -> parse and chunk
  -> metadata/vector-assisted evidence retrieval
  -> extraction
  -> normalization
  -> validation and confidence scoring
  -> auto-promotion or review task
  -> canonical product/version/change event
  -> aggregate refresh
  -> public product grid/dashboard
```

---

## 7. 시연 리스크와 대응

| 리스크 | 영향 | 대응 |
|---|---|---|
| 은행 사이트 지연 또는 page 구조 변경 | live collection이 느려지거나 일부 실패 가능 | 데모 범위 사전 수집, 완료 run tab 준비, live collection은 실행 가능성 확인 용도로만 사용 |
| 외부 LLM 설정/쿼터 문제 | AI scorer가 fallback되거나 fresh run token이 낮게 보일 수 있음 | selective AI design 설명, 완료 run의 usage dashboard 활용, fallback note를 governance 장점으로 설명 |
| Aggregate refresh 지연 | fresh collection 결과가 즉시 public에 안 보일 수 있음 | latest successful snapshot 기준 설명, dashboard health 확인, 필요 시 manual retry |
| Review queue가 비어 있음 | 고객이 review 예시를 기대할 수 있음 | policy-clear auto-promotion 설명, 필요한 경우 과거 review 예시를 별도 준비 |
| Big 5/GIC 범위 혼선 | 시연 범위가 커져 메시지가 흐려짐 | 오늘 범위는 BMO/TD chequing/savings라고 명확히 고정 |

---

## 8. 고객 Q&A 준비

| 질문 | 답변 |
|---|---|
| 이건 단순 웹 scraping 아닌가요? | 아닙니다. Fetch는 한 단계일 뿐입니다. FPDS는 snapshot, parse/chunk, evidence link, validation, canonical versioning, usage, audit, public aggregate까지 운영 record를 남깁니다. |
| AI가 상품 값을 만들어내나요? | 원칙은 evidence-grounded입니다. AI fallback은 근거 없는 field를 omit하도록 설계되어 있고, validation과 review routing이 모호한 값을 차단합니다. Public은 raw AI output이 아니라 canonical/aggregate record를 읽습니다. |
| Public 사용자가 evidence를 볼 수 있나요? | 아니요. Evidence trace와 raw snapshot은 Admin-only입니다. Public은 approved projection field와 official bank product link만 제공합니다. |
| token 비용은 어떻게 통제하나요? | 모든 usage는 run, model, agent, token, estimated cost, status 기준으로 저장됩니다. 지원 product type은 deterministic agent가 처리하고 외부 LLM은 선택적으로 사용합니다. |
| AI 또는 은행 page가 실패하면 어떻게 되나요? | deterministic fallback, partial failure, source/stage retry, manual review routing이 있습니다. 문제 후보가 조용히 public으로 나가지 않도록 설계되어 있습니다. |
| 새로운 상품 유형을 추가할 수 있나요? | Admin-managed product type registry가 있습니다. 단, 전문 parser가 없는 product type은 generic AI fallback과 manual review 우선으로 처리되며 바로 public publish하지 않습니다. |
| Public freshness는 어떻게 보장하나요? | Public은 latest successful aggregate snapshot을 사용합니다. 새 refresh가 실패해도 마지막 성공 snapshot serving은 유지되고, health는 Admin에서 확인합니다. |
| 아직 범위 밖인 것은 무엇인가요? | personalized recommendation, public evidence exposure, external SaaS/Open API, full BX-PF runtime integration, Phase 2 market expansion은 이번 시연 범위 밖입니다. |

---

## 9. ChatGPT 이미지 Prompt - 아키텍처 구조도

아래 prompt를 ChatGPT 이미지 생성에 사용한다.

```text
Create a professional architecture diagram for a financial product data platform named "FPDS".

Canvas: 16:9, clean enterprise style, white background, restrained blue/green/gray palette, no decorative gradients, no fictional logos.

Use three horizontal swimlanes:
1. External systems
2. FPDS platform boundary
3. Public and operator consumers

Show these nodes:
- Bank public websites and PDFs
- LLM provider
- FPDS Admin Console, authenticated
- FPDS Public Product Grid and Insight Dashboard, anonymous
- FastAPI Public/Admin API
- Private ingestion worker
- Operational PostgreSQL database
- Object storage for raw snapshots, parsed text, evidence artifacts
- Evidence chunk retrieval store with pgvector side table and metadata-only fallback
- Aggregate refresh and public projection
- Optional BX-PF target master store, marked "future / interface-ready"

Show the main data flow:
Admin selects bank and product-type coverage -> API queues collection -> private worker discovers official source pages -> snapshots are captured -> content is parsed and chunked -> evidence retrieval selects source chunks -> extraction and normalization create normalized candidates -> validation routes to auto-promotion or review -> canonical product/version/change records are stored -> aggregate refresh builds public_product_projection -> public grid/dashboard read the latest successful aggregate snapshot.

Show AI usage as dashed lines:
- LLM provider to homepage AI parallel scorer during source discovery
- LLM provider to dynamic product extractor/normalizer only for unsupported operator-defined product types
- Usage records flow into model_execution and llm_usage_record, visible in Admin Usage Dashboard

Add security/trust notes as small callouts:
- Public never receives raw evidence or source excerpts
- Evidence trace is admin-only
- Admin writes require session, role, and CSRF
- Worker is the only boundary that calls external bank sites

Labels should be concise and presentation-ready. Use Korean main labels with short English technical terms in parentheses, for example "공개 상품 목록 (Product Grid)".
```

## 10. ChatGPT 이미지 Prompt - 상품수집 프로세스 구조도

아래 prompt를 ChatGPT 이미지 생성에 사용한다.

```text
Create a detailed but readable process structure diagram for FPDS product collection.

Canvas: 16:9, clean process-flow style, white background, rectangular nodes, numbered stages, no icons unless simple and professional.

Title: "FPDS Product Collection Process - Evidence to Public Projection"

Use a left-to-right process with 10 numbered stages:
1. Admin coverage selection: bank + product type
2. Homepage discovery and generated source rows
3. Snapshot capture: HTML/PDF saved to object storage
4. Parse and chunk: parsed text + evidence chunks
5. Evidence retrieval: metadata filter + pgvector ranking + metadata-only fallback
6. Extraction agent: field candidates with evidence links
7. Normalization agent: canonical candidate payload
8. Validation and confidence routing: pass, warning, error, review
9. Canonical upsert and audit: product, version, change event, review decision
10. Aggregate refresh: public_product_projection, dashboard metrics, rankings, scatter

Add side artifacts under the stages:
- source_snapshot
- parsed_document
- evidence_chunk
- evidence_chunk_embedding
- extracted draft
- normalized_candidate
- field_evidence_link
- model_execution
- llm_usage_record
- review_task
- canonical_product / product_version
- aggregate_refresh_run
- public_product_projection

Show AI-agent usage as small colored badges:
- fpds-homepage-ai-parallel-scorer: optional during stage 2
- fpds-heuristic-extractor: stage 6, zero external LLM tokens for supported chequing/savings/GIC
- fpds-heuristic-normalizer: stage 7, zero external LLM tokens for supported chequing/savings/GIC
- fpds-dynamic-product-extractor / normalizer: optional fallback for unsupported product types, forced to manual review

Add a bottom governance band:
"Traceability | Validation | Reviewability | Token usage | Audit | Public freshness"

Labels should be Korean with technical field names preserved in English where exact table names matter.
```

---

## 11. 추가 ChatGPT 요청 Prompt

### 11.1 발표자료 목차 생성

```text
Act as a senior product/project manager preparing a customer demo deck.

Create a 12-slide Korean presentation outline for FPDS, a financial product data service.

Demo scope:
- Canada
- BMO and TD
- chequing and savings products
- Admin collection to Public product grid/dashboard
- Customer is technically interested in internal collection process, AI-agent usage, token usage, evidence trace, validation, and public freshness.

Use this narrative:
1. Business problem
2. FPDS product boundary
3. Architecture overview
4. Admin coverage management
5. Product collection pipeline
6. Evidence and validation model
7. AI-agent usage and token observability
8. Review/auto-promotion/audit governance
9. Public Product Grid
10. Public Insight Dashboard
11. Demo risks and controls
12. Next steps and roadmap

For each slide, provide:
- slide title
- key message
- 3-5 bullets
- suggested screen or diagram
- speaker notes in Korean

Keep tone professional, factual, and customer-ready.
```

### 11.2 기술 Q&A Sheet 생성

```text
Act as a solution architect preparing for technical customer Q&A.

Create a Korean Q&A sheet for FPDS customer demo reviewers.

Topics to cover:
- source discovery and official source control
- snapshot storage and evidence trace
- parsing/chunking and retrieval
- pgvector and metadata-only fallback
- extraction and normalization agents
- deterministic heuristic agents vs OpenAI-backed dynamic fallback
- model_execution and llm_usage_record
- token and estimated cost tracking
- validation, confidence, auto-promotion, and manual review routing
- public aggregate snapshot freshness
- security: admin auth, CSRF, RBAC, SSRF-safe fetching, public evidence non-exposure
- limitations and next steps

Format as a table with columns:
Question, Short answer, Technical detail, Demo screen to show.

Be honest about limitations. Do not overclaim full production readiness beyond the stated demo scope.
```

### 11.3 Executive Script 생성

```text
Act as a Korean-speaking executive presenter.

Write a 5-minute opening and closing script for an FPDS customer demo.

The message:
- FPDS turns official bank product pages into evidence-grounded canonical product data.
- Admin controls collection scope and sees run, evidence, audit, and token usage.
- Public users see the latest successful aggregate snapshot in Product Grid and Dashboard.
- Demo scope is BMO and TD chequing/savings products.
- AI is used selectively and observably, not as an uncontrolled black box.

Tone:
- professional
- concise
- confident but not salesy
- suitable for financial-services technical stakeholders
```

### 11.4 리허설 체크리스트 생성

```text
Act as a demo producer.

Create a one-page Korean rehearsal checklist for the FPDS demo.

Include:
- pre-demo environment checks
- browser tabs to open
- exact demo order
- expected proof points
- fallback plan if live collection is slow
- who speaks during each segment
- when to switch from live collection to pre-run data
- Q&A handoff plan

Keep it concise enough to print.
```

---

## 12. 최종 발표 유의사항

Product Owner가 명시적으로 승인하지 않는 한 FPDS를 production release 완료 상태로 표현하지 않는다.

권장 표현:

- 현재 Phase 1 플랫폼 build이며, Admin collection과 Public aggregate-backed surface가 동작한다.
- Evidence-first architecture와 operational traceability가 구현되어 있다.
- Big 5 deposit coverage는 내부 검증을 통과했다.
- 고객 시연은 메시지 집중을 위해 BMO/TD chequing/savings로 좁힌다.

피해야 할 표현:

- "AI가 모든 은행 page를 자동으로 이해합니다."
- "Manual review가 필요 없습니다."
- "Public data는 은행 페이지에서 실시간입니다."
- "BX-PF integration이 완전히 끝났습니다."

대신 사용할 표현:

- "AI는 선택적으로 사용되며 usage가 관측됩니다."
- "Validation이 auto-promotion과 review routing을 결정합니다."
- "Public은 latest successful aggregate snapshot을 읽습니다."
- "BX-PF는 interface-ready/future integration boundary이며 이번 시연 범위 밖입니다."
