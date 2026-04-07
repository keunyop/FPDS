# FPDS Object Storage and Evidence Bucket Baseline

Version: 1.0
Date: 2026-04-07
Status: Approved Baseline for WBS 2.4
Source Documents:
- `docs/01-planning/WBS.md`
- `docs/03-design/source-snapshot-evidence-storage-strategy.md`
- `docs/03-design/environment-separation-strategy.md`
- `docs/03-design/security-access-control-design.md`
- `docs/03-design/dev-prod-environment-spec.md`
- `docs/03-design/db-migration-baseline.md`
- `docs/00-governance/decision-log.md`

---

## 1. Purpose

This document closes `WBS 2.4 object storage and evidence bucket setup`.

Goals:
- turn the approved storage strategy into a concrete bucket and key-layout baseline
- define how `dev` and `prod` storage boundaries stay separated
- keep the baseline implementation-ready without locking to one cloud vendor

This is a storage contract and provisioning baseline, not an executable cloud deployment script.

---

## 2. Chosen Baseline

The current baseline is:
- storage model: `S3-compatible object storage`
- access mode: `private`
- environment separation: separate bucket per environment is preferred
- fallback environment separation: one private bucket with strict top-level env prefix separation
- browser access: never direct

This baseline is intentionally vendor-neutral.

---

## 3. Bucket Strategy

### 3.1 Preferred Shape

| Environment | Recommended Bucket |
|---|---|
| `dev` | `fpds-dev-private` |
| `prod` | `fpds-prod-private` |

Rules:
- `dev` and `prod` must not share credentials
- `prod` bucket access is never reused in `dev`
- both buckets stay private and non-public

### 3.2 Acceptable Fallback

If the provider or budget forces one physical bucket, use:
- one private bucket
- strict env prefix separation at the top level
- separate credentials or access policies per environment where possible

Even in fallback mode, the logical layout still begins with `{env}/...`.

---

## 4. Object Layout

The approved object key baseline is:

```text
{env}/snapshots/{country_code}/{bank_code}/{source_document_id}/{snapshot_id}/raw
{env}/parsed/{country_code}/{bank_code}/{source_document_id}/{parsed_document_id}/parsed.txt
{env}/parsed/{country_code}/{bank_code}/{source_document_id}/{parsed_document_id}/metadata.json
{env}/parsed/{country_code}/{bank_code}/{source_document_id}/{parsed_document_id}/intermediate/{artifact_name}
```

Why this shape:
- preserves lineage from source document to snapshot to parsed artifact
- matches the DB metadata model from `WBS 2.3`
- supports reprocessing without exposing raw objects to browser surfaces

---

## 5. Artifact Boundary

### 5.1 Stored in Object Storage

- raw HTML body
- raw PDF binary
- parsed text full body
- parser intermediate artifacts when needed

### 5.2 Stored in DB, Not in Object Storage

- source identity and discovery metadata
- fetch metadata, checksum, fingerprint
- parse metadata
- evidence chunk metadata and excerpt
- field-to-evidence links

This preserves the approved rule: full artifacts in object storage, operational metadata in DB.

---

## 6. Access Rules

Rules:
- public web and public API do not access raw object artifacts directly
- admin surfaces may show evidence summaries, but not raw object paths
- worker and internal API surfaces are the only normal runtime paths to object storage
- access should use signed internal access or equivalent private retrieval
- object keys are implementation detail, not browser contract

---

## 7. Retention and Integrity Baseline

### 7.1 Integrity

- object paths should be immutable once referenced by DB metadata
- checksum and fingerprint remain DB metadata, not only object metadata
- same `source identity + fingerprint` may reuse existing stored artifacts

### 7.2 Retention

The baseline supports `retention_class` without fixing exact durations yet.

Current placeholder classes:
- `hot`
- `archive`
- `legal_hold`

Not fixed yet:
- exact day counts
- archival transition timing
- purge timing
- encryption and KMS configuration

---

## 8. Tracked Files in This Repo

| File | Purpose |
|---|---|
| `storage/README.md` | storage entrypoint |
| `storage/object-layout.example.json` | placeholder-only bucket and key-layout contract |
| `.env.dev.example` | dev storage placeholders |
| `.env.prod.example` | prod storage placeholders |

---

## 9. What Codex Can Do and What The Product Owner Must Do

Codex can:
- maintain the storage contract
- wire future snapshot and parsing code to this layout
- keep env files, docs, and DB references aligned

The Product Owner or infrastructure owner must:
- provision the real private bucket or container
- choose the actual provider endpoint and region
- configure real credentials outside git
- apply provider-side lifecycle, encryption, and access policy settings

If the provider requires console-side setup or IAM policy work, that must be done outside this repo.

---

## 10. Hand-off to Follow-On Work

This baseline is the input for:
- `3.1` source discovery
- `3.2` snapshot capture
- `3.3` parsing and chunking
- `4.4` evidence trace viewer
- later storage lifecycle and security hardening work

---

## 11. WBS Mapping

| WBS ID | Closure in This Document |
|---|---|
| `2.4` | Sections 2-10 |

---

## 12. Change History

| Date | Change |
|---|---|
| 2026-04-07 | Initial object storage and evidence bucket baseline created for WBS 2.4 |
