# Pipeline Worker Area

Use this area for ingestion pipeline stages after discovery.

Current scope:
- `fpds_parse_chunk/` implements `WBS 3.3` parsed text generation, chunk creation, parsed artifact storage, and DB persistence
- `fpds_evidence_retrieval/` implements `WBS 3.4` metadata-only candidate chunk retrieval with field-aware scoring, DB reads, and pgvector-assisted candidate ranking when `evidence_chunk_embedding` rows are available
- `fpds_extraction/` implements `WBS 3.5` sparse extracted draft generation, extracted artifact storage, `model_execution` persistence, and zero-token heuristic usage records
- `fpds_normalization/` implements `WBS 3.6` canonical candidate mapping, `normalized_candidate` persistence, `field_evidence_link` persistence, and normalized artifact storage
- `fpds_validation_routing/` implements `WBS 3.7` candidate validation recheck, confidence recomputation, prototype review-task routing, and validation artifact storage
- `fpds_result_viewer/` implements `WBS 3.8` read-only prototype viewer payload export from persisted run, candidate, and evidence rows
- `fpds_aggregate_refresh/` implements `WBS 5.6` aggregate source dataset generation for `public_product_projection`, `dashboard_metric_snapshot`, `dashboard_ranking_snapshot`, and `dashboard_scatter_snapshot`

Planned follow-on scope:
- canonical upsert and change assessment
- publish preparation

Big 5 source-id note:
- when `--registry-path` is omitted, worker CLI stages that resolve `--source-id` now use the committed registry catalog, so `TD-*`, `RBC-*`, `BMO-*`, `SCOTIA-*`, and `CIBC-*` `chequing`, `savings`, and `gic` source ids can run without switching the default TD savings registry file by hand

Run parse/chunk against stored snapshots in dev:

```powershell
python -m worker.pipeline.fpds_parse_chunk `
  --env-file .env.dev `
  --persist-db `
  --run-id run_20260410_3301 `
  --source-id TD-SAV-002 `
  --source-id TD-SAV-004 `
  --source-id TD-SAV-007 `
  --source-id TD-SAV-008
```

Run evidence retrieval against stored parsed documents in dev:

```powershell
python -m worker.pipeline.fpds_evidence_retrieval `
  --env-file .env.dev `
  --run-id run_20260410_3401 `
  --source-id TD-SAV-007 `
  --field-name monthly_fee `
  --field-name fee_waiver_condition
```

Run vector-assisted evidence retrieval when `db/migrations/0012_evidence_chunk_embeddings.sql` has been applied and parsed chunks have embedding rows:

```powershell
python -m worker.pipeline.fpds_evidence_retrieval `
  --env-file .env.dev `
  --run-id run_20260410_3401 `
  --source-id TD-SAV-007 `
  --field-name monthly_fee `
  --retrieval-mode vector-assisted
```

If the pgvector table or embedding rows are unavailable, the worker reports a runtime note and falls back to `metadata-only`.

Run extraction against stored parsed documents in dev:

```powershell
python -m worker.pipeline.fpds_extraction `
  --env-file .env.dev `
  --persist-db `
  --run-id run_20260410_3501 `
  --source-id TD-SAV-002 `
  --source-id TD-SAV-007
```

Run normalization against the latest extraction artifacts in dev:

```powershell
python -m worker.pipeline.fpds_normalization `
  --env-file .env.dev `
  --persist-db `
  --run-id run_20260410_3603 `
  --source-id TD-SAV-002 `
  --source-id TD-SAV-007
```

Run validation/routing against the latest normalization artifacts in dev:

```powershell
python -m worker.pipeline.fpds_validation_routing `
  --env-file .env.dev `
  --persist-db `
  --run-id run_20260410_3701 `
  --source-id TD-SAV-002 `
  --source-id TD-SAV-007
```

Export a run into the prototype viewer payload in dev:

```powershell
python -m worker.pipeline.fpds_result_viewer `
  --env-file .env.dev `
  --run-id run_20260410_3701
```

Run aggregate refresh against the current canonical dataset in dev:

```powershell
python -m worker.pipeline.fpds_aggregate_refresh `
  --env-file .env.dev `
  --persist-db `
  --snapshot-id agg_20260413_5601 `
  --country-code CA
```

What `WBS 3.5` stores today:
- extracted draft JSON artifact per parsed document in object storage
- metadata JSON artifact with counts and storage references
- `model_execution` row per source extraction attempt
- `llm_usage_record` row with `0` tokens and `heuristic-no-llm-call` metadata for the current baseline
- updated `run_source_item.stage_metadata` for extraction status and artifact linkage

Current boundary:
- this stage produces source-level sparse drafts, not `normalized_candidate`
- `field_evidence_link` rows are still deferred because they require `candidate_id` or `product_version_id`
- the extraction baseline now includes product-type-specific canonical fields for `chequing`, `savings`, and `gic`, including transaction bundle signals, savings tiering or withdrawal text, and GIC term, redeemability, compounding, payout, and registered-plan support fields

What `WBS 3.6` stores today:
- normalized candidate JSON artifact per source candidate in object storage
- metadata JSON artifact with candidate id, validation status, and confidence
- `normalized_candidate` row per source candidate
- `field_evidence_link` rows tied to `candidate_id`
- `model_execution` and zero-token `llm_usage_record` rows for normalization
- updated `run_source_item.stage_metadata` for candidate id and normalization results
- for the TD Savings prototype, missing rate fields can now be supplemented from a product-matched `TD-SAV-005` current-rates extraction artifact when that supporting artifact exists
- for the TD Savings prototype, noisy `interest_calculation_method` fields can now be replaced with stronger `TD-SAV-008` governing-PDF wording when the detail-page extraction only captured PDF link text
- for the TD Savings prototype, `TD-SAV-007` fee-governing evidence can now suppress misleading `fee_waiver_condition` values for zero-monthly-fee savings products instead of persisting raw fee-table text
- `TD Growth` qualification text is now split more deliberately into `eligibility_text`, `boosted_rate_eligibility`, and `promotional_period_text`
- clearly noisy long-text fields such as generic notes, marketing promo copy, and fee-at-a-glance snippets can now be suppressed before canonical candidate persistence
- chequing subtype inference now aligns to the approved taxonomy: `standard`, `package`, `interest_bearing`, `premium`, `other`
- normalization and validation now also align GIC term and redeemability rules at candidate creation time so missing deposit or term values, invalid term lengths, and conflicting redeemability flags are surfaced before review routing

Current boundary:
- normalization now persists `normalized_candidate` and candidate-level evidence links
- supporting-source merge is still narrow and prototype-specific; it currently covers TD Savings current-rate supplementation, selective `TD-SAV-008` interest-rule replacement, and `TD-SAV-007`-based suppression of misleading zero-fee waiver text rather than general multi-source product merge
- canonical upsert, change assessment, and publish preparation still belong to later stages

What `WBS 3.7` stores today:
- validation/routing JSON artifact per source candidate in object storage
- metadata JSON artifact with candidate state, review reason, and review task id
- updated `normalized_candidate` validation fields and `candidate_state`
- `review_task` row per prototype candidate with `queued` review state
- `model_execution` and zero-token `llm_usage_record` rows for validation/routing
- updated `run_source_item.stage_metadata` for review queue linkage

Current boundary:
- Prototype routing mode sends every candidate to review even when validation passes
- review decisions, canonical upsert, change history, and audit-event emission still belong to later stages

What `WBS 3.8` exports today:
- static viewer payload JSON and browser-consumable JS for `app/prototype/index.html`
- run summary, candidate summary, canonical payload, validation issues, and evidence excerpt data loaded from DB
- registry-backed `source_id` labels mapped back onto persisted candidate rows for operator readability

Current boundary:
- this is a read-only prototype viewer export, not the full admin review queue or trace viewer
- write actions, queue mutation, and deep trace drilldown remain deferred to later admin slices

What `WBS 5.6` stores today:
- one `aggregate_refresh_run` row per attempted snapshot
- flattened `public_product_projection` rows with the shared filter vocabulary and approved bucket codes
- `dashboard_metric_snapshot` rows for the current aggregate scope baseline
- `dashboard_ranking_snapshot` rows for the approved ranking widget catalog
- `dashboard_scatter_snapshot` rows for the approved scatter preset catalog

Current boundary:
- this slice builds aggregate source datasets only; it does not implement the public products API, dashboard APIs, or public UI
- later public API work can now read from persisted aggregate rows instead of joining live canonical tables directly

Reliability note:
- DB-backed worker stages now run `psql` with `ON_ERROR_STOP=1` so SQL errors abort the stage instead of being reported as false-positive success

Run all worker tests:

```powershell
python -m unittest discover -s worker -t .
```
