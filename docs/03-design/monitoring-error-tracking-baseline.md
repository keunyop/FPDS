# FPDS Monitoring and Error Tracking Baseline

Version: 1.0
Date: 2026-04-07
Status: Approved Baseline for WBS 2.7
Source Documents:
- `docs/02-requirements/FPDS_Requirements_Definition_v1_5.md`
- `docs/01-planning/WBS.md`
- `docs/01-planning/prototype-backlog.md`
- `docs/03-design/environment-separation-strategy.md`
- `docs/03-design/dev-prod-environment-spec.md`
- `docs/03-design/api-interface-contracts.md`
- `docs/00-governance/decision-log.md`

---

## 1. Purpose

This document closes `WBS 2.7 monitoring and error tracking baseline`.

Goals:
- define the minimum observability contract that future API, worker, and prototype code must share
- keep the baseline vendor-neutral while still naming the current preferred production path
- make prototype failures diagnosable without exposing stack traces, secrets, or internal infrastructure detail to browser-facing surfaces

This is a baseline contract, not a complete runtime SDK integration guide.

---

## 2. Baseline Decisions

1. Every browser-facing error response must stay controlled and must include a traceable `request_id` or equivalent correlation token.
2. Internal logs and monitoring events must use structured fields instead of free-form text only.
3. `request_id`, `correlation_id`, and `run_id` are separate identifiers and must not be collapsed into one field.
4. Observability configuration must come from the tracked env contract, not from hard-coded provider values.
5. `dev` may run with monitoring disabled during scaffold work, but the logging and id-propagation contract must still exist.
6. The current preferred production provider label is `sentry`, but the shared contract stays provider-neutral so later implementation can swap the backend if needed.

---

## 3. Minimum Scope for WBS 2.7

This baseline covers:
- request and orchestration correlation identifiers
- structured runtime log/event shape
- safe external error response shape
- monitoring provider mode rules by environment
- redaction rules for secrets and sensitive internals
- repository artifacts that future code can implement against without reopening the contract

This baseline does not yet cover:
- framework-specific SDK wiring
- alert routing, paging, and on-call policy
- metrics backend selection beyond the monitoring provider label
- dashboard implementation
- retention duration, sampling percentage, or cost caps

---

## 4. Identifier Model

| Field | Scope | Purpose |
|---|---|---|
| `request_id` | browser/API request | user-facing support and controlled error responses |
| `correlation_id` | orchestration chain | follow the same flow across API, worker, DB writes, and monitoring |
| `run_id` | ingestion or processing run | connect pipeline work, evidence artifacts, usage, and retries |

Rules:
- browser-facing routes should expose `request_id`, not raw internal trace data
- internal orchestration should propagate `correlation_id` and `run_id` together when both exist
- worker stages should log their stage name plus `run_id` and `correlation_id`

---

## 5. Safe External Error Response Baseline

External responses for public, admin, and browser-facing APIs must:
- avoid stack traces
- avoid internal file paths
- avoid raw SQL or query text
- avoid secret values or token fragments
- include a stable machine-readable `code`
- include a short safe message
- include `request_id`

Reference example:
- `shared/observability/error-envelope.example.json`

---

## 6. Structured Internal Event Baseline

Internal logs and monitoring payloads should follow one shared event vocabulary with at least:

| Field | Meaning |
|---|---|
| `timestamp` | event time |
| `level` | `debug`, `info`, `warn`, `error`, or `fatal` |
| `environment` | `dev` or `prod` |
| `runtime_label` | human-readable runtime label from env |
| `surface` | `public-api`, `admin-api`, `internal-api`, `worker`, or `prototype-viewer` |
| `component` | concrete subsystem or stage |
| `event_type` | request, retry, validation failure, stage failure, publish failure, and similar |
| `request_id` | request trace id when available |
| `correlation_id` | orchestration trace id when available |
| `run_id` | run trace id when available |
| `error_code` | stable internal error taxonomy code |
| `message` | short operator-readable summary |
| `safe_context` | non-secret diagnostic context |
| `monitoring.provider` | configured backend label |
| `monitoring.capture` | whether the event was sent to the external backend |

Reference example:
- `shared/observability/structured-log-event.example.json`

---

## 7. Redaction Rules

The following values must never be emitted to browser responses and should be excluded or masked in monitoring payloads unless a secured internal-only diagnostic surface explicitly requires them:
- secrets from env or secret managers
- session ids, CSRF secrets, API keys, DB credentials, BX-PF credentials
- raw SQL statements
- private bucket paths or signed URLs
- full request bodies when they may contain credentials or personal data
- internal hostnames or filesystem paths unless a secured operator-only surface intentionally needs them

Allowed safe context examples:
- `source_id`
- `source_type`
- `bank_code`
- stage name
- retry count
- HTTP status code
- content type

---

## 8. Environment Rules

| Environment | Provider Label | DSN Expectation | Capture Rule |
|---|---|---|---|
| `dev` | `disabled` by default | may be blank | local logging still required |
| `prod` | `sentry` preferred baseline | placeholder in git, real value outside git | external capture required before release |

Notes:
- the provider label comes from `FPDS_MONITORING_PROVIDER`
- the backend entrypoint comes from `FPDS_MONITORING_DSN`
- future runtime code should degrade safely when provider is `disabled`

---

## 9. Repository Artifacts Added for This Baseline

| Path | Role |
|---|---|
| `shared/observability/README.md` | landing zone for future shared observability helpers |
| `shared/observability/error-envelope.example.json` | safe external error response example |
| `shared/observability/structured-log-event.example.json` | structured internal event example |
| `scripts/harness/validate-foundation-baseline.ps1` | static validation for env and observability baseline files |

---

## 10. What Codex Can Do and What The Product Owner Must Do

Codex can:
- maintain the env and observability contract
- wire future runtime code to the shared fields and examples
- keep CI and docs aligned with the baseline

The Product Owner or infrastructure owner must:
- provision the real production monitoring project and DSN
- choose alert routing and ownership
- store real monitoring credentials outside git
- confirm which production environments should notify humans and at what severity thresholds

---

## 11. Follow-On Work Unlocked

This baseline is the input for:
- `3.1` source discovery and later worker stages that need diagnosable failures
- `4.5` run status error summary
- `4.8` LLM usage tracking correlation
- `6.5` release hardening and operator runbook work
- `7.8` external API monitoring and audit separation

---

## 12. WBS Mapping

| WBS ID | Closure in This Document |
|---|---|
| `2.7` | Sections 2-11 |

---

## 13. Change History

| Date | Change |
|---|---|
| 2026-04-07 | Initial monitoring and error tracking baseline created for WBS 2.7 |
