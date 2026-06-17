# FPDS 중간 보고 - Admin 수집부터 Public 결과까지


## 1. 개요

이번 시연의 핵심 메시지는 FPDS가 단순한 상품 목록 화면이 아니라, 은행의 원천 자료를 근거로 상품 정보를 수집, 검증, 추적, 공개하는 데이터 플랫폼입니다.

### 비즈니스 문제:

- 은행의 상품 정보는 상품 상세 페이지, 각종 문서, PDF, 동적 페이지 등에 흩어져 있습니다.
- 각 은행은 서로 다른 용어를 사용하여 상품 정보가 표준화되어 있지 않습니다.


---

## 2. 시연 시나리오

### Step 1 - Admin 로그인

1. Admin 계정으로 로그인한다.
2. 메뉴 그룹을 짧게 본다.


### Step 2 - 상품 유형과 수집 은행

1. 등록된 상품 유형을 본다.
2. 등록된 은행을 본다.


### Step 3 - 상품 수집 실행

1. 은행 상세 modal을 연다.
2. 상품 수집을 실행한다.



### Step 4 - 실행 상태 확인

1. 실행 run을 확인한다.
2. Run detail을 연다.



### Step 5 - 생성된 소스 확인

1. source를 확인한다.
2. source detail을 연다.



### Step 6 - review 설명


### Step 7 - AI Agent와 Token Usage 설명

1. run detail에서 usage summary를 본다.
2. `/admin/usage`에서 total, by-model, by-agent, by-run, trend, anomaly를 본다.

### Step 8 - Public Dashboard 확인


### Step 9 - Public Product 확인


## Agent

| Agent | 사용 시점 | 외부 LLM 사용 | Token 영향 |
|---|---|---:|---|
| `fpds-homepage-ai-parallel-scorer` | homepage-first source discovery에서 후보 link scoring | OpenAI 설정이 있을 때 사용 | prompt/completion token과 estimated cost 기록 |
| `fpds-heuristic-extractor` | chequing/savings/GIC field extraction | 사용 안 함 | execution record는 남고 token은 0 |
| `fpds-heuristic-normalizer` | canonical mapping, subtype/taxonomy, evidence link 구성 | 사용 안 함 | execution record는 남고 token은 0 |
| `fpds-dynamic-product-extractor` | 전문 parser가 없는 operator-added product type extraction fallback | 사용 가능 | token/cost 기록, manual review 우선 |
| `fpds-dynamic-product-normalizer` | dynamic product canonical fallback | 사용 가능 | token/cost 기록, manual review 우선 |
| Validation/routing policy | required field, confidence, issue code, auto-promotion/review 결정 | 사용 안 함 | LLM token 없음 |
