# Discovery Worker Area

Use this area for source discovery, seed registry handling, URL normalization, and fetch planning.

Prototype-first target:
- TD Savings source discovery baseline

Current implementation slice:
- `data/td_savings_source_registry.json` stores the approved 12-source TD savings registry seed.
- `fpds_discovery/` contains URL normalization, deterministic source identity, controlled fetch validation, and discovery rules for entry-page detail discovery plus linked PDF discovery.
- `fpds_snapshot/` contains snapshot capture, preflight drift checks, object key generation, storage adapters, checksum or fingerprint calculation, retry handling, and snapshot reuse logic.
- `fpds_registry_refresh/` contains scheduled refresh artifact generation for candidate diffs and source drift review.
- `tests/` contains offline fixtures and unit tests so discovery can be verified without live network access.

Operating policy:
- `docs/03-design/source-registry-refresh-and-approval-policy.md` defines the registry operating baseline: keep an approved active registry, detect drift during preflight or scheduled refresh, and promote changes only after explicit approval.

Run offline fixture-based discovery:

```powershell
python -m worker.discovery.fpds_discovery `
  --entry-html-path worker/discovery/tests/fixtures/td_savings_entry.html `
  --page-html "https://www.td.com/ca/en/personal-banking/products/bank-accounts/savings-accounts/every-day-savings-account=worker/discovery/tests/fixtures/td_every_day_detail.html" `
  --page-html "https://www.td.com/ca/en/personal-banking/products/bank-accounts/savings-accounts/epremium-savings-account=worker/discovery/tests/fixtures/td_epremium_detail.html" `
  --page-html "https://www.td.com/ca/en/personal-banking/products/bank-accounts/savings-accounts/growth-savings-account=worker/discovery/tests/fixtures/td_growth_detail.html" `
  --page-html "https://www.td.com/ca/en/personal-banking/products/bank-accounts/account-rates=worker/discovery/tests/fixtures/td_account_rates.html" `
  --page-html "https://www.td.com/ca/en/personal-banking/products/bank-accounts-fees-services-charges-cad-savings=worker/discovery/tests/fixtures/td_fee_summary.html"
```

Run unit tests:

```powershell
python -m unittest discover -s worker/discovery/tests -t .
```

Run snapshot capture with live env-backed storage:

```powershell
python -m worker.discovery.fpds_snapshot `
  --env-file .env.dev `
  --persist-db `
  --run-id run_20260410_0001 `
  --correlation-id corr_20260410_0001 `
  --source-id TD-SAV-002 `
  --source-id TD-SAV-004 `
  --source-id TD-SAV-007 `
  --source-id TD-SAV-008
```

Run scheduled registry refresh artifact generation:

```powershell
python -m worker.discovery.fpds_registry_refresh `
  --env-file .env.dev `
  --run-id run_20260410_refresh_0001 `
  --correlation-id corr_20260410_refresh_0001 `
  --output-path tmp/registry-refresh-0001.json
```

Notes:
- Discovery keeps the approved registry as the source of truth and treats out-of-registry or excluded flows as warnings instead of auto-expanding scope.
- Registry refresh strategy is approval-first: ingestion uses the active registry, while future refresh automation should produce candidate diffs instead of rewriting the active registry in place.
- Snapshot capture now performs lightweight preflight drift checks by default before fetching and storing raw artifacts. Use `--skip-preflight-drift-check` only when intentionally bypassing that operator signal.
- Live fetch uses the `FPDS_SOURCE_FETCH_ALLOWLIST` and `FPDS_SOURCE_FETCH_BLOCK_PRIVATE_NETWORKS` env settings from the shared baseline.
- Snapshot capture writes raw artifacts to the approved `{env}/snapshots/{country_code}/{bank_code}/{source_document_id}/{snapshot_id}/raw` key layout and returns DB-shaped metadata for `source_snapshot` and `run_source_item`.
- `--env-file` now overrides ambient process env values so live dev runs stay aligned to the chosen local env file.
- `--persist-db` creates or updates `ingestion_run`, upserts `source_document`, inserts new `source_snapshot`, and upserts `run_source_item`.
- Scheduled refresh generates a JSON artifact with preflight drift findings, discovery warnings, and candidate diffs. It does not mutate the active registry.
- When `FPDS_DATABASE_SCHEMA` points at a schema without the required snapshot tables but `public` contains them, snapshot persistence falls back to `public` and reports the resolved schema in the runtime output.
- `fetch_status` currently uses `fetched` or `reused`, while per-source `stage_status` stays conservative at `completed` or `failed` and keeps the finer-grained action in `stage_metadata.snapshot_action`.
