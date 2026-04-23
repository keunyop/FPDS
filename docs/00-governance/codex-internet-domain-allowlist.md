# FPDS Codex Internet Domain Allowlist

Version: 1.0
Date: 2026-04-06
Status: Recommended Baseline
Source Documents:
- `docs/02-requirements/FPDS_Requirements_Definition_v1_5.md`
- `docs/02-requirements/scope-baseline.md`
- `docs/01-planning/plan.md`
- `docs/01-planning/WBS.md`
- `docs/archive/01-planning/td-savings-source-inventory.md`
- `docs/03-design/security-access-control-design.md`
- `docs/03-design/environment-separation-strategy.md`
- `docs/03-design/api-interface-contracts.md`
- `docs/00-governance/decision-log.md`

---

## 1. Purpose

이 문서는 `FPDS용 Codex 작업 환경`에서 인터넷 접근을 켜야 할 때, 어떤 도메인을 허용하는 것이 프로젝트 문서 기준으로 적절한지 정리한다.

목적:
- `모두(무제한)` 대신 least-privilege 방식의 허용 도메인 기준을 둔다.
- FPDS가 실제로 필요로 하는 공식 source, vendor docs, 공통 개발 의존성만 열어 둔다.
- 아직 프로젝트 문서에서 확정되지 않은 외부 통합 도메인과, 지금 열 필요가 없는 범용 인터넷을 구분한다.

이 문서는 `앱 런타임 egress allowlist`가 아니라 `Codex 작업 환경`의 인터넷 허용 정책 기준이다.
실제 앱/worker의 CORS, SSRF, outbound allowlist는 별도 보안 문서 기준을 따른다.

---

## 2. Baseline Principles

1. `무제한`보다 `필요한 공식 도메인만 허용`을 기본으로 한다.
2. 은행 source는 현재 범위에 포함된 공식 public domain만 허용한다.
3. vendor 도메인은 `문서 확인`, `공식 API/console`, `패키지/의존성 설치`에 필요한 것만 포함한다.
4. 로그인 후 내부 화면, personalized flow, compare tool, promo page는 기본 허용 목록에 넣지 않는다.
5. 문서상 아직 host가 고정되지 않은 통합 대상은 placeholder로만 남기고, 실제 값이 정해질 때 추가한다.

---

## 3. What the Docs Require

문서 기준으로 Codex가 인터넷 접근이 필요한 이유는 아래 5가지다.

1. 은행 공식 public source와 PDF를 검증해야 한다.
2. OpenAI 기반 LLM/API 문서와 사용 기준을 확인해야 한다.
3. Node/Next.js 기반 공통 의존성과 패키지 정보를 확인해야 한다.
4. FPDS 권장 스택인 Vercel, Supabase, AWS, Sentry 관련 공식 문서를 확인해야 한다.
5. 이후 Phase 1에서 Canada Big 5 source registry를 확장해야 한다.

---

## 4. Recommended Allowlist

### 4.1 Tier A: Recommended Initial Allowlist

지금 시점에서 가장 먼저 허용할 도메인이다.
Prototype 문서 정리, 설계, 구현, 테스트 준비까지 커버하는 최소 추천값이다.

| Domain | Why It Is Needed | Basis |
|---|---|---|
| `td.com` | Prototype source inventory의 공식 public source와 PDF 검증 | `docs/archive/01-planning/td-savings-source-inventory.md` |
| `openai.com` | OpenAI 제품/정책/안내 문서의 공식 루트 | PRD suggested stack: OpenAI |
| `platform.openai.com` | API/usage/auth 문서 확인 | PRD suggested stack: OpenAI |
| `developers.openai.com` | 최신 개발 문서 확인 | PRD suggested stack: OpenAI |
| `api.openai.com` | 실제 API 호출 또는 스펙 확인 | PRD suggested stack: OpenAI |
| `github.com` | 공통 개발 의존성, 소스, 이슈, 릴리스 확인 | engineering dependency baseline |
| `raw.githubusercontent.com` | GitHub raw 문서/설정/샘플 조회 | engineering dependency baseline |
| `npmjs.com` | npm package page 확인 | Node/Next.js stack |
| `registry.npmjs.org` | npm install / metadata fetch | Node/Next.js stack |

### 4.2 Tier B: Recommended Phase 1 Banking Source Domains

Prototype 이후 `Canada Big 5` 확장을 고려하면 같이 허용해 둘 만한 은행 공식 도메인이다.

| Domain | Why It Is Needed | Basis |
|---|---|---|
| `rbcroyalbank.com` | Canada Big 5 source registry 확장 시 RBC public source 확인 | Phase 1 Canada Big 5 |
| `bmo.com` | Canada Big 5 source registry 확장 시 BMO public source 확인 | Phase 1 Canada Big 5 |
| `scotiabank.com` | Canada Big 5 source registry 확장 시 Scotiabank public source 확인 | Phase 1 Canada Big 5 |
| `cibc.com` | Canada Big 5 source registry 확장 시 CIBC public source 확인 | Phase 1 Canada Big 5 |

### 4.3 Tier C: Optional Official Vendor Docs

이 도메인들은 FPDS 문서상 권장 스택과 운영 준비에 맞지만, 당장 모든 세션에서 필수는 아니다.

| Domain | Why It Is Needed | Basis |
|---|---|---|
| `vercel.com` | public/admin hosting 문서와 배포 가이드 확인 | PRD suggested stack |
| `supabase.com` | auth/vendor 문서 확인 | PRD suggested stack |
| `aws.amazon.com` | worker/storage/private integration 문서 확인 | PRD suggested stack |
| `docs.aws.amazon.com` | AWS 서비스 상세 문서 확인 | AWS integration planning |
| `sentry.io` | error tracking 및 운영 문서 확인 | PRD suggested stack |
| `docs.sentry.io` | Sentry 구현 문서 확인 | monitoring/error tracking baseline |

---

## 5. Add Later When Actual Values Are Known

아래는 문서에서 `필요성`은 확인되지만, 아직 정확한 호스트 값이 프로젝트 문서에 고정되지 않은 항목이다.

| Placeholder | Why It Is Not in the Fixed Allowlist Yet |
|---|---|
| `BX-PF actual host` | remote endpoint, auth header, transport detail이 아직 미확정 |
| `actual Supabase project host` | 프로젝트별 서브도메인이 아직 미확정 |
| `actual Vercel preview/prod host` | 배포 도메인이 아직 미확정 |
| `actual S3-compatible bucket endpoint` | storage vendor/endpoint가 아직 미확정 |
| `actual Sentry ingest host` | region/project별 ingest host가 아직 미확정 |

운영 원칙:
- 이 항목들은 host 값이 정해진 뒤에만 allowlist에 추가한다.
- broad wildcard로 미리 열어 두지 않는다.

---

## 6. Domains Not Recommended by Default

아래는 기본 허용 목록에서 제외하는 것을 권장한다.

| Domain/Type | Why Excluded |
|---|---|
| `모두(무제한)` | prompt injection, 악성 코드, 라이선스 이슈, 비의도적 데이터 유출 위험이 커짐 |
| 일반 검색/블로그/포럼 전반 | 공식 문서와 무관한 low-trust source가 많음 |
| `discovery.td.com` | source inventory에서 personalized recommendation/discovery tool은 제외됨 |
| 은행 로그인/인증 전용 경로 | FPDS source inventory와 무관하고 보안 리스크만 늘어남 |
| promo / compare / campaign 전용 경로 | canonical source 기준에서 제외됨 |
| 광범위한 cloud wildcard (`*.amazonaws.com` 등) | 편하긴 하지만 범위가 너무 넓고 보안상 과함 |

---

## 7. Recommended Configuration Choice

Codex 환경에서 선택지를 고른다면 아래를 권장한다.

1. 인터넷 연결: `켜기`
2. 허용 방식: `무제한`이 아니라 `허용 도메인 목록 사용`
3. 초기 허용 목록: Section 4.1 `Tier A`
4. Big 5 조사/확장 단계 진입 시: Section 4.2 `Tier B` 추가
5. 실제 인프라 작업이 시작되면: Section 4.3과 Section 5를 필요한 만큼만 추가

추천 초기 목록:
- `td.com`
- `openai.com`
- `platform.openai.com`
- `developers.openai.com`
- `api.openai.com`
- `github.com`
- `raw.githubusercontent.com`
- `npmjs.com`
- `registry.npmjs.org`

Phase 1 확장용 추가 목록:
- `rbcroyalbank.com`
- `bmo.com`
- `scotiabank.com`
- `cibc.com`

---

## 8. Validation Notes

`2026-04-06` 기준으로 아래 공식 public banking domains는 실제 public banking/savings surface가 확인되었다.

- `td.com`
- `rbcroyalbank.com`
- `bmo.com`
- `scotiabank.com`
- `cibc.com`

이 확인은 FPDS 문서 범위와 public banking/savings surface 존재 여부를 맞추기 위한 것이며, exact product inventory는 각 은행별 source inventory 문서에서 별도로 확정한다.

---

## 9. WBS / Governance Impact

이 문서는 별도 WBS closure 문서는 아니지만, 아래 작업에 간접 기준을 제공한다.

- `1.6.4`, `1.6.5`: allowlist-only / safe fetch 원칙과의 정합성 유지
- `1.8.x`: source inventory / backlog / spike의 공식 source 검증
- `2.x`: foundation setup 시 vendor docs 및 dependency 접근 범위 결정
- `5.1`: Canada Big 5 source registry 확장 준비

---

## 10. Change History

| Date | Change |
|---|---|
| 2026-04-06 | Initial Codex internet domain allowlist baseline created from FPDS docs |
