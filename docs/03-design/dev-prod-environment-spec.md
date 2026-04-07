# FPDS Dev and Prod Environment Spec

Version: 1.0
Date: 2026-04-07
Status: Approved Baseline for WBS 2.2
Source Documents:
- `docs/02-requirements/FPDS_Requirements_Definition_v1_5.md`
- `docs/01-planning/WBS.md`
- `docs/03-design/environment-separation-strategy.md`
- `docs/03-design/security-access-control-design.md`
- `docs/03-design/source-snapshot-evidence-storage-strategy.md`
- `docs/00-governance/decision-log.md`

---

## 1. Purpose

This document closes `WBS 2.2 environment separation and env template setup`.

Goals:
- turn the approved `dev/prod` environment strategy into a concrete minimum config shape
- keep the baseline vendor-neutral enough for upcoming scaffold work
- make it clear which values stay placeholders until real infrastructure exists

This is a config contract, not a framework-specific loader design.

---

## 2. Tracked Files in This Repository

| File | Purpose |
|---|---|
| `.env.dev.example` | placeholder-only starting point for local or shared `dev` |
| `.env.prod.example` | placeholder-only production config inventory |
| `shared/config/README.md` | landing zone for future config loading helpers |

Rules:
- track example files only
- keep real secrets out of git
- keep local development inside the `dev` model instead of creating a third environment

---

## 3. Environment Model

| Environment | Purpose | BX-PF | Source Fetch | Cookie Secure |
|---|---|---|---|---|
| `dev` | local or shared development, prototype unblock, rehearsal | `mock` or `disabled` | `controlled` by default | `false` |
| `prod` | public and admin production runtime | `live` when integration is ready | `live` | `true` |

Baseline notes:
- the only official environment layers are `dev` and `prod`
- `local` is treated as a form of `dev`
- `stg`, `preview`, and `qa` are not part of the current baseline

---

## 4. Config Groups

### 4.1 Environment Identity

| Key | Meaning |
|---|---|
| `FPDS_ENV` | environment selector, currently `dev` or `prod` |
| `FPDS_RUNTIME_LABEL` | human-readable runtime label for logs and operator context |

### 4.2 Origins and Surface Boundaries

| Key | Meaning |
|---|---|
| `FPDS_PUBLIC_WEB_ORIGIN` | public browser origin |
| `FPDS_ADMIN_WEB_ORIGIN` | admin browser origin |
| `FPDS_PUBLIC_API_ORIGIN` | public API or BFF origin |
| `FPDS_ADMIN_API_ORIGIN` | admin API or BFF origin |
| `FPDS_INTERNAL_API_ORIGIN` | private internal control endpoint origin |

Rules:
- browser-facing origins must be explicit
- exact origin values remain placeholders until deployment domains are finalized
- future CORS enforcement should consume these values rather than hard-coding origins

### 4.3 Data Plane

| Key | Meaning |
|---|---|
| `FPDS_DATABASE_URL` | environment-specific database connection string |
| `FPDS_DATABASE_SCHEMA` | default relational schema name |
| `FPDS_VECTOR_BACKEND` | retrieval/vector backend label |
| `FPDS_VECTOR_NAMESPACE` | environment-separated vector namespace |
| `FPDS_OBJECT_STORAGE_DRIVER` | logical object storage driver |
| `FPDS_OBJECT_STORAGE_ENDPOINT` | object storage endpoint |
| `FPDS_OBJECT_STORAGE_REGION` | object storage region or logical location |
| `FPDS_OBJECT_STORAGE_BUCKET` | private bucket or container name |
| `FPDS_OBJECT_STORAGE_PREFIX` | top-level environment prefix |
| `FPDS_OBJECT_STORAGE_ACCESS_MODE` | storage access mode, currently `private` |
| `FPDS_OBJECT_STORAGE_SIGNED_URL_MODE` | object access mode for internal retrieval |
| `FPDS_SNAPSHOT_OBJECT_PREFIX` | snapshot object subtree name |
| `FPDS_PARSED_OBJECT_PREFIX` | parsed object subtree name |
| `FPDS_PARSER_INTERMEDIATE_PREFIX` | parser intermediate subtree name |
| `FPDS_EVIDENCE_PREFIX_ROOT` | evidence namespace root |
| `FPDS_EVIDENCE_RETENTION_CLASS` | retention hook for later archival or purge work |

Rules:
- `dev` and `prod` must never share DB credentials, storage buckets, or vector namespaces
- object storage layout must preserve the `{env}/...` separation model
- object storage access stays `private` and signed access stays internal-only by default
- exact lifecycle rules, encryption settings, and retention days stay out of this baseline

### 4.4 Auth and Secret Inputs

| Key | Meaning |
|---|---|
| `FPDS_ADMIN_AUTH_MODE` | admin auth baseline, currently `server-session` |
| `FPDS_ADMIN_SESSION_SECRET` | session secret for admin authentication |
| `FPDS_ADMIN_CSRF_SECRET` | CSRF secret for admin write protection |
| `FPDS_STORAGE_ACCESS_KEY` | storage access credential |
| `FPDS_STORAGE_SECRET_KEY` | storage secret credential |
| `FPDS_CRAWLER_SHARED_SECRET` | worker or crawler shared secret |

Rules:
- browser surfaces must not receive these values
- all secrets stay placeholder-only in tracked files
- real secrets belong in a secret manager or untracked runtime env files

### 4.5 Fetch, LLM, and Publish Integration

| Key | Meaning |
|---|---|
| `FPDS_SOURCE_FETCH_MODE` | fetch policy such as `controlled` or `live` |
| `FPDS_SOURCE_FETCH_ALLOWLIST` | approved source domains |
| `FPDS_SOURCE_FETCH_BLOCK_PRIVATE_NETWORKS` | SSRF guardrail toggle |
| `FPDS_LLM_PROVIDER` | model provider label |
| `FPDS_LLM_MODEL` | model name |
| `FPDS_LLM_API_KEY` | model provider credential |
| `FPDS_BXPF_MODE` | publish mode such as `mock`, `disabled`, or `live` |
| `FPDS_BXPF_BASE_URL` | BX-PF endpoint placeholder |
| `FPDS_BXPF_CLIENT_ID` | BX-PF client identifier |
| `FPDS_BXPF_CLIENT_SECRET` | BX-PF client secret |

Rules:
- `dev` defaults to non-live BX-PF behavior
- real BX-PF write-back is `prod` only
- exact source allowlist values remain placeholders until security follow-on work wires the final approved list

### 4.6 Security and Browser Policy

| Key | Meaning |
|---|---|
| `FPDS_ALLOWED_PUBLIC_ORIGINS` | explicit public CORS allowlist |
| `FPDS_ALLOWED_ADMIN_ORIGINS` | explicit admin CORS allowlist |
| `FPDS_SECURITY_HEADERS_ENABLED` | baseline browser security header toggle |
| `FPDS_COOKIE_SECURE` | production secure-cookie rule |
| `FPDS_COOKIE_SAMESITE` | admin cookie same-site rule |
| `FPDS_CSRF_PROTECTION_ENABLED` | admin write CSRF guardrail |

Rules:
- no wildcard origin defaults
- admin auth remains cookie-backed server-side session auth
- `FPDS_COOKIE_SECURE=true` in `prod`

### 4.7 Observability

| Key | Meaning |
|---|---|
| `FPDS_LOG_LEVEL` | runtime log detail level |
| `FPDS_REQUEST_ID_HEADER` | request correlation header name |
| `FPDS_MONITORING_PROVIDER` | monitoring backend label |
| `FPDS_MONITORING_DSN` | error tracking or monitoring DSN |

Rules:
- `dev` may keep monitoring disabled during early scaffold work
- `prod` should point at the real monitoring backend before release

---

## 5. Placeholder Policy

The tracked example files intentionally keep these values unresolved:
- exact production domains and origin allowlists
- all secret values
- real BX-PF endpoint and credentials
- finalized storage region, bucket policy, lifecycle, and encryption settings
- final source fetch allowlist values beyond starter placeholders

These are placeholders by design because the baseline is ready for development, but the real infrastructure and operational ownership are not fully provisioned yet.

---

## 6. What Codex Can Do and What The Product Owner Must Do

Codex can:
- maintain the config contract and example files
- wire future scaffolds to read these keys
- keep docs, examples, and implementation aligned

The Product Owner or infrastructure owner must:
- provision real database, storage, monitoring, and secret-management targets
- choose exact public and admin domains
- store real secrets outside git
- provide real BX-PF credentials only when production integration is ready

---

## 7. Hand-off to Follow-On Work

This WBS 2.2 baseline is the input for:
- `2.3` database and migration baseline
- `2.4` object storage and evidence bucket setup
- `2.5` admin auth scaffold
- `2.7` monitoring and error tracking baseline
- `2.8` security baseline

---

## 8. WBS Mapping

| WBS ID | Closure in This Document |
|---|---|
| `2.2` | Sections 2-7 |

---

## 9. Change History

| Date | Change |
|---|---|
| 2026-04-07 | Initial dev and prod environment spec created for WBS 2.2 |
