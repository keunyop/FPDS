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

> FPDS가 은행들의 다양한 공개된 상품 페이지를 수집하여 표준화된 상품정보로 바꾸는 과정을 보여드리겠습니다. 운영자는 Admin에서 은행과 상품 유형을 선택하고, FPDS는 공식 source를 수집해 snapshot 저장, 분석, 근거추출, 상품정보 표준화, 검증을 거친 뒤 검증된 상품을 public dashboard에 반영합니다. 또한 어떤 agent가 실행됐고, AI가 어디서 사용됐으며, token 사용량과 검증이 어떻게 남는지도 함께 보여드리겠습니다.

비즈니스 문제를 짧게 정리:

- 은행 상품 정보는 상품 상세 페이지, 각종 문서, PDF, 동적 페이지에 흩어져 있다.
- FPDS는 이 불안정한 원천 정보를 표준화된 데이터로 전환한다.
- Public 사용자는 깔끔한 비교 화면을 보고, 운영자는 검증, 실행, 사용량, 검증 결과를 본다.

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

## 5. 상세 시연 절차

### Step 1 - Admin 로그인과 운영자 경계 설명

화면:

- `http://localhost:3001/admin/login`
- 로그인 후 `/admin`

진행:

1. Admin 계정으로 로그인한다.
2. 메뉴 그룹을 짧게 보여준다.

멘트:

> Admin은 운영자 전용 화면입니다. 수집 은행 및 수집 자료 관리, 수집 실행, 리뷰, 토큰 사용량 등을 확인할수 있습니다.

### Step 2 - 상품 유형과 수집 은행 확인

화면:

- `/admin/product-types`
- `/admin/banks`

진행:

1. 등록된 deposit product type을 보여준다: `chequing 요구불`, `savings 적금`, `gic 예금`.
2. `/admin/banks`에서 BMO 상세 modal을 연다.
3. BMO의 chequing과 savings coverage card를 보여준다.
4. TD도 같은 방식으로 coverage가 있음을 보여준다.

멘트:

> 운영자가 수집할 은행의 프로필과 수집할 상품 유형을 관리합니다. 상품 정보 수집은 등록된 은행 홈페이지와 상품 유형 정의를 기준으로 실제 상세 원천 정보가 생성됩니다.


### Step 3 - Demo Scope Collection 실행

권장 live UI 절차:

1. `/admin/banks`에서 BMO 상세 modal을 연다.
2. BMO `Chequing` coverage card의 `Collect`를 클릭한다.
3. BMO `Savings` coverage card의 `Collect`를 클릭한다.
4. TD 상세 modal을 연다.
5. TD `Chequing` coverage card의 `Collect`를 클릭한다.
6. TD `Savings` coverage card의 `Collect`를 클릭한다.


멘트:

> 상품 수집은 비동기로 이뤄집니다.서버에서는 홈페이지 탐색, 원천정보의 snapshot 저장, 파싱과 chunking, 상품정보 추출, 표준화, 검증이 background에서 이어집니다.


### Step 4 - 실행 상태와 Pipeline Stage 확인

화면:

- `/admin/runs`
- `/admin/runs/:runId`

진행:

1. 최신 run을 started_at 기준으로 확인한다.
2. BMO 또는 TD run detail을 연다.
3. source count, candidate count, review queued count, partial completion flag를 보여준다.
4. stage summary와 source processing summary를 보여준다.

멘트:

> Run은 수집 실행의 운영 record입니다. 전체가 성공하면 completed가 되고, 일부 source 문제가 있어도 partial completion으로 진단 가능한 결과를 남깁니다. 따라서 운영자는 어떤 source나 stage가 문제였는지 확인하고 재시도할 수 있습니다.


### Step 5 - 생성된 소스 확인

화면:

- `/admin/sources?bank_code=BMO&product_type=savings`
- `/admin/sources/:sourceId`

진행:

1. BMO + savings로 source list를 filter한다.
2. source detail을 연다.
3. URL, role/status, discovery summary, AI-predicted role이 있으면 함께 보여준다.
4. recent collection history를 보여준다.



### Step 6 - Evidence와 Reviewability 설명

화면:

- review task가 있으면 `/admin/reviews`, `/admin/reviews/:reviewTaskId`
- review task가 없으면 `/admin/runs/:runId`와 `/admin/sources/:sourceId`

진행:

1. review task가 있으면 proposed fields, evidence links, model execution references, decision actions를 보여준다.
2. review task가 없으면 `review_queued_count = 0`을 보여주고 auto-validation/auto-promotion path를 설명한다.

멘트:

> FPDS가 상품 정보를 수집할때 점수가 낮으면 사람의 review 프로세스를 거치도록 설계되었습니다. validation issue, 낮은 confidence, ambiguous mapping, dynamic product type은 review로 보냅니다. 반대로 policy를 만족한 candidate는 auto-promote됩니다.

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



### Step 10 - Governance와 운영 통제 확인

화면:

- `/admin/audit`
- `/admin/health/dashboard`


진행:

1. audit event category를 보여준다.
2. dashboard health와 latest successful snapshot 상태를 보여준다.


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
