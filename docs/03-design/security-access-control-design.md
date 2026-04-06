# FPDS Security and Access Control Design

Version: 1.0
Date: 2026-04-05
Status: Approved Baseline for WBS 1.6.1-1.6.7
Source Documents:
- `docs/02-requirements/FPDS_Requirements_Definition_v1_5.md`
- `docs/01-planning/WBS.md`
- `docs/03-design/system-context-diagram.md`
- `docs/03-design/environment-separation-strategy.md`
- `docs/03-design/api-interface-contracts.md`
- `docs/03-design/review-run-publish-audit-state-design.md`
- `docs/03-design/source-snapshot-evidence-storage-strategy.md`
- `docs/00-governance/decision-log.md`

---

## 1. Purpose

이 문서는 `WBS 1.6 Security and Access Control Design`의 기준 문서다.

목적:
- admin auth, RBAC, external API auth, CORS, crawler safe fetch, session/CSRF/security header, secret rotation 기준을 하나의 baseline으로 고정한다.
- `public/admin/API/worker/storage/BX-PF` 경계가 같은 trust model을 참조하도록 만든다.
- Gate A 이전에 닫아야 하는 security/access open item을 문서 기준으로 종료한다.

이 문서는 구현 지시서가 아니라 설계 baseline이다.  
구현은 `Gate A = Pass + Product Owner explicit approval` 이후에만 시작한다.

---

## 2. Baseline Decisions

1. public dashboard는 anonymous public surface다.
2. admin surface는 browser 기반 human operator surface다.
3. browser는 DB, object storage, vector metadata, BX-PF에 직접 접근하지 않는다.
4. worker, crawler, publish adapter는 private boundary 안에서만 동작한다.
5. raw evidence artifact는 public에 노출하지 않고 admin에서도 direct object path 노출은 금지한다.
6. Phase 2 external API는 credential-bound tenant scope를 기본으로 한다.

---

## 3. Admin Authentication Baseline

### 3.1 Decision

`1.6.1`의 공식 baseline은 `server-side session cookie`다.

채택 이유:
- 현재 admin 사용자는 browser 기반 내부 운영 사용자다.
- `same-origin admin web + BFF/admin API` 구조와 가장 자연스럽게 맞는다.
- CSRF/session hardening을 브라우저 정책과 함께 통합하기 쉽다.
- browser local storage나 bearer token 보관보다 노출면을 줄일 수 있다.

### 3.2 Boundary Rules

- admin login은 human user 전용이다.
- admin API는 cookie-backed authenticated session이 없으면 접근할 수 없다.
- browser는 access token을 직접 저장하거나 전달하지 않는다.
- service-to-service 인증은 admin browser login과 분리된 별도 credential을 사용한다.

---

## 4. Human RBAC Baseline

### 4.1 Roles

human RBAC baseline은 아래 3개 역할이다.

| Role | Purpose |
|---|---|
| `admin` | 운영 전반 관리, 권한/설정/검토/이력/상태 조회 |
| `reviewer` | review queue 처리, trace 확인, run/product/change 이력 조회 |
| `read_only` | 운영 상태와 결과 조회 전용 |

### 4.2 Permission Rules

- `admin`만 privilege change, config change, credential lifecycle, override성 운영 액션을 수행할 수 있다.
- `reviewer`는 review action과 관련 조회를 수행할 수 있지만 권한/보안 정책 변경은 할 수 없다.
- `read_only`는 조회만 가능하며 write action은 수행할 수 없다.
- audit visibility는 세 역할 모두 가능하되, 민감 설정 변경은 `admin`만 가능하다.

---

## 5. External API Authentication Baseline

`1.6.3`의 공식 baseline은 `tenant-bound API key`다.

규칙:
- credential 1개는 tenant 1개에만 연결한다.
- request 기반 cross-tenant override는 허용하지 않는다.
- issuance, rotation, revocation은 audit 대상이다.
- Phase 2 이전에는 public browser surface에서 이 credential을 사용하지 않는다.

---

## 6. CORS and Origin Policy

- browser-facing API CORS는 allowlist-only다.
- public API는 anonymous read 기준이지만 wildcard 정책은 기본값으로 두지 않는다.
- admin API는 credentialed request이므로 exact origin allowlist만 허용한다.
- environment별 origin 값은 config로 분리하고 hard-coded wildcard를 두지 않는다.

---

## 7. Crawler Safe Fetch / SSRF Policy

- crawler fetch 대상은 source inventory에 등록된 은행으로 제한한다.
- 다만 등록된 은행의 허용 도메인 내부에서는 자유롭게 crawling할 수 있다.
- private IP, loopback, link-local, metadata endpoint는 차단한다.
- raw user-supplied arbitrary URL fetch는 허용하지 않는다.
- redirect는 bank-scoped allowlist를 벗어나면 중단한다.

---

## 8. Session / CSRF / Browser Security

- admin cookie baseline:
  - `HttpOnly`
  - `SameSite=Lax`
  - `Secure` in production
- cookie-authenticated admin write에는 CSRF 보호를 적용한다.
- baseline security headers:
  - CSP
  - HSTS in production
  - `X-Content-Type-Options: nosniff`
  - `Referrer-Policy`
  - `frame-ancestors` restriction via CSP

---

## 9. Secret Rotation and Audit Scope

- secret은 environment-separated owner/cadence 기준으로 관리한다.
- rotation 대상:
  - admin auth/session secret
  - external API key material
  - BX-PF integration credential
  - storage/service secrets
- audit 대상:
  - issuance
  - rotation
  - revocation
  - access grant
  - privilege-affecting secret/config change

---

## 10. Follow-On Work Unlocked

- `2.5`: auth scaffold 구성
- `2.8`: security baseline 적용
- `4.1`: admin login 구현
- `6.5`: 보안 하드닝 검증
- `7.4`: external API auth 구현
