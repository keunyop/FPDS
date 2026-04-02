# FPDS Environment Separation Strategy

Version: 1.1
Date: 2026-04-01
Status: Approved Baseline for WBS 1.4.6
Source Documents:
- `docs/FPDS_Requirements_Definition_v1_5.md`
- `docs/plan.md`
- `docs/WBS.md`
- `docs/system-context-diagram.md`
- `docs/source-snapshot-evidence-storage-strategy.md`
- `docs/retrieval-vector-starting-point.md`
- `docs/aggregate-cache-refresh-strategy.md`
- `docs/decision-log.md`

---

## 1. Purpose

이 문서는 `WBS 1.4.6 환경 분리 전략 정리`를 닫기 위한 기준 문서다.

목적:
- 1인 개발자 운영 모델에 맞는 `dev/prod` 환경 분리 원칙을 정의한다.
- public/admin surface와 private worker/storage/data boundary를 분리한다.
- 후속 `CORS/origin`, `SSRF/egress`, `secret rotation` 정책이 같은 환경 모델을 참조하도록 맞춘다.

`stg`는 현재 baseline에서 제외한다. 필요해지면 `dev/prod` 경계를 유지한 채 후속 확장 환경으로 추가한다.

---

## 2. Baseline Decisions Carried Forward

본 문서는 아래 확정 사항을 반영한다.

1. public surface는 익명 공개 경계다.
2. admin surface는 인증이 필요한 운영 경계다.
3. worker, crawler, publish는 private boundary에서 동작해야 한다.
4. DB, object storage, vector metadata, BX-PF credential은 public surface에서 직접 접근하면 안 된다.
5. exact CORS allowlist와 SSRF egress allowlist 값은 후속 security WBS에서 닫는다.

---

## 3. Environment Model

FPDS의 현재 공식 환경 모델은 아래 2개로 둔다.

| Environment | Purpose | Data Class | External Integration Mode |
|---|---|---|---|
| `dev` | local or shared development, prototype unblock, 운영 전 검증 | synthetic, masked, or limited non-production data | mock/stub 우선, 필요 시 제한된 live source access |
| `prod` | public/admin 운영 환경 | production operational data | real BX-PF integration and official live source access |

참고:
- local 개발 환경은 `dev`의 하위 실행 형태로 본다.
- 별도 `preview`, `qa`, `stg`가 생기더라도 현재 baseline은 `dev/prod` 2계층이다.
- 1인 개발자 운영에서는 환경 수를 줄이고, `dev` 안에서 mock/stub와 rehearsal을 최대한 흡수하는 쪽이 효율적이다.

---

## 4. Trust Boundary Model

### 4.1 Public/Admin Surface

- public web과 admin web은 브라우저에 노출되는 surface다.
- admin은 인증이 필요하지만 여전히 public-facing server boundary 위에 있다.
- browser는 DB, object storage, vector store, BX-PF에 직접 연결하지 않는다.

### 4.2 Private Worker and Data Boundary

아래 구성요소는 private boundary로 본다.

- crawler and fetcher
- parsing and chunking
- retrieval and vector processing
- publish worker
- DB
- object storage
- secret store

### 4.3 Allowed Access Pattern

허용 baseline:

- browser -> public/admin API
- API -> DB and aggregate/cache
- API -> private worker control endpoint or queue
- worker -> source websites / LLM provider / BX-PF
- worker -> DB / object storage / vector store

비허용 baseline:

- browser -> DB direct access
- browser -> object storage raw snapshot direct access
- public route -> BX-PF direct call
- public route -> crawler egress execution

---

## 5. Environment Separation Rules

### 5.1 Data Plane Separation

- `dev`와 `prod`는 서로 다른 DB instance, schema, or project boundary를 가져야 한다.
- object storage bucket 또는 top-level prefix는 환경별로 분리한다.
- vector index namespace는 환경별로 분리한다.
- 한 환경의 credential을 다른 환경에서 재사용하지 않는다.

### 5.2 Secret Separation

- BX-PF real credential은 `prod`에서만 허용한다.
- `dev`는 기본적으로 mock/stub credential 또는 disabled mode를 사용한다.
- admin auth secret, DB credential, storage credential, crawler secret은 환경별로 별도 발급한다.

### 5.3 Traffic Separation

- `prod` worker는 private outbound policy 하에서만 source, LLM, BX-PF와 통신한다.
- `dev`는 안전을 위해 outbound scope를 최소화한다.
- `dev`에서 real target write는 허용하지 않는다.

---

## 6. Recommended Deployment Shape

이 문서가 권장하는 logical deployment shape는 아래와 같다.

| Layer | Recommended Placement |
|---|---|
| public/admin web | public hosting zone |
| public/admin API/BFF | public app zone with protected server-side access |
| worker/orchestration | private compute zone |
| DB/vector metadata | private data zone |
| object storage | private bucket or container |
| secret management | environment-isolated secret store |

이 baseline은 vendor-neutral이다.
PRD suggested stack의 `public/admin on Vercel`, `worker/storage/private integration on AWS`는 참고 방향으로만 본다.

---

## 7. BX-PF and Source Access Rules by Environment

| Environment | Source Fetch | LLM Call | BX-PF |
|---|---|---|---|
| `dev` | limited or controlled | allowed with lower-risk config | mock/stub only by default |
| `prod` | official live source access | production config | real target integration |

운영 원칙:
- BX-PF real write-back은 `prod`만 기본 허용한다.
- `dev`에서는 reconciliation rehearsal이나 payload validation을 하더라도 real target write는 하지 않는다.
- `dev`의 live fetch는 운영 보호를 위해 제한된 대상과 빈도로만 허용한다.

---

## 8. Open Items Not Blocking This Strategy

| Area | Open Item | Follow-Up WBS | Why It Does Not Block 1.4.6 |
|---|---|---|---|
| CORS | exact origin allowlist by env | `1.6.4` | environment topology가 먼저 있어야 allowlist를 정할 수 있다. |
| SSRF/Egress | exact outbound allowlist and deny policy | `1.6.5` | private worker boundary가 먼저 정의되면 세부 값은 후속 분리 가능하다. |
| Session/Auth | session cookie vs token, auth vendor detail | `1.6.1` | admin protected boundary를 먼저 고정하면 된다. |
| Secret Rotation | owner, cadence, audit depth | `1.6.7` | environment 분리와 rotation 운영 rule은 separate concern이다. |

---

## 9. Interfaces and Follow-On Work Unlocked

- `1.6.4`: public/admin/api origin policy
- `1.6.5`: crawler safe fetch and egress policy
- `1.6.6`: session and security header policy
- `2.2`: dev/prod env spec
- `2.4`: object storage and evidence bucket 준비
- `2.7`: monitoring and error tracking baseline 구성

---

## 10. WBS Mapping

| WBS ID | Closure in This Document |
|---|---|
| 1.4.6 | Sections 2-9 |

---

## 11. Change History

| Date | Change |
|---|---|
| 2026-04-01 | Initial environment separation strategy created for WBS 1.4.6 |
| 2026-04-01 | Simplified baseline from `dev/stg/prod` to `dev/prod` for single-developer operating model |
