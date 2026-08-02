# Worker Boundary

This directory holds private pipeline and integration workers.

Current boundary:
- `discovery/` for source discovery and registry-driven fetch entry
- `pipeline/` for parse, chunk, extraction, normalization, validation, and review routing work
- `publish/` for BX-PF-facing publish and reconciliation work
- `runtime/` for worker bootstrap, scheduling, and execution plumbing

Current implementation slices:
- `WBS 3.1` source discovery, preflight drift checks, and scheduled refresh artifacts in `worker/discovery/`
- `WBS 3.2` snapshot capture and persistence in `worker/discovery/fpds_snapshot/`
- `WBS 3.3` parse/chunk pipeline in `worker/pipeline/fpds_parse_chunk/`
- `WBS 3.4` evidence retrieval in `worker/pipeline/fpds_evidence_retrieval/`
- `WBS 3.5` extraction flow in `worker/pipeline/fpds_extraction/`
- `WBS 3.6` normalization mapping in `worker/pipeline/fpds_normalization/`
- `WBS 3.7` validation/confidence routing in `worker/pipeline/fpds_validation_routing/`
- `WBS 3.8` result-viewer payload export in `worker/pipeline/fpds_result_viewer/`

Runtime invariants:
- one ingestion run owns exactly one normalized ISO alpha-2 country code;
  snapshot, parse/chunk, extraction, normalization, and validation persistence
  all write that country and reject mixed-country scopes before DB work
- HTML discovery reads ordinary anchors plus bounded JSON component links from
  `data-*` attributes; parser version `fpds-parse-chunk-v3` also retains
  bounded component text as `structured_component` evidence when a visible
  location gate hides the product copy
- market defaults are country-owned (`CA -> CAD`, `US -> USD`); an unknown
  country remains explicit instead of silently inheriting CAD
- product-title extraction prefers high-confidence official location-gated
  page identity and removes SEO action suffixes while rejecting legal
  documents, enrollment CTAs, calculators, and other non-product headings
- configured OpenAI collection runs apply one official-domain grounding pass to
  every candidate-producing `detail` source, including the standard Product
  Types. The pass receives the full active field contract and may replace or
  supplement a field only when the provider actually consulted an allowlisted
  official URL and the model returns an exact quote from the freshly captured
  evidence chunk. Supporting sources remain evidence-only, and provider
  unavailability falls back to the existing heuristic extraction path.
- dynamic/lending candidates that verify official product identity, at least
  two decision fields, and the configured `80%` decision-field ratio may use
  normal Phase 1 auto-validation; insufficient grounding remains review-bound
