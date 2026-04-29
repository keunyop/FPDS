# FPDS Homepage Discovery Scoring Enhancement

Version: 1.0
Date: 2026-04-18
Status: Approved Follow-On Design Baseline
Source Documents:
- `docs/02-requirements/FPDS_Requirements_Definition_v1_5.md`
- `docs/03-design/source-registry-refresh-and-approval-policy.md`
- `docs/03-design/admin-information-architecture.md`
- `docs/01-planning/WBS.md`
- `docs/00-governance/decision-log.md`

---

## 1. Purpose

This document defines the next design step for improving `homepage-first discovery` quality without replacing the current FPDS collection architecture.

Goals:
- improve detail-source selection quality while preserving the existing `bank homepage -> generated source -> collect` operator workflow
- promote AI from a last-resort fallback into a bounded parallel scorer that works alongside deterministic link heuristics
- use full product-type definition meaning, not only short keyword lists
- add page-level evidence scoring before a discovered URL is promoted into a candidate-producing `detail` source
- keep the operational model reviewable, auditable, and incrementally implementable

This is a design and operating baseline for follow-on implementation work. It does not itself widen public publish semantics or change the run/review contract.

---

## 2. Current Baseline

Current live homepage-first discovery is intentionally simple:
- fetch the bank homepage
- extract same-domain links
- score links with deterministic keyword and URL heuristics
- expand through a small number of hub pages
- if no `detail` links are found, use AI-assisted resolution as a fallback

This baseline has real strengths:
- simple and explainable operator behavior
- low cost when homepage or hub pages are well structured
- stable fit with the DB-backed `bank` plus `source_registry_catalog_item` plus `source_registry_item` workflow

This baseline also has clear weaknesses:
- it overweights URL or anchor-text patterns
- it underuses the stored product-type description
- it treats AI as an exception path instead of a routine quality signal
- it can promote links without enough page-level confirmation that the page is truly a product-detail page
- run diagnostics can clearly show fetch failures, but discovery diagnostics are still comparatively thin

---

## 3. Design Direction

FPDS should keep the current homepage-first pipeline, but split discovery quality into three explicit layers:

1. `Candidate generation`
2. `Hybrid scoring`
3. `Page-level evidence validation`

Short form:

`heuristic candidate generation + AI parallel scoring + page-level evidence scoring`

This design intentionally does not switch FPDS to:
- vector-first discovery
- full browser automation as the default path
- AI-only autonomous crawling
- silent registry mutation without audit-visible generated-source rows

Those paths add substantial complexity before the current architecture has exhausted the value of a better scoring model.

---

## 4. Proposed Discovery Flow

### 4.1 Stage A: Candidate Generation

Candidate generation remains mostly deterministic.

Inputs:
- bank homepage URL
- bank homepage HTML
- same-domain allowed links
- limited hub-page expansion
- approved seed entry URL hints when available
- approved seed detail hints when available

Output:
- a bounded candidate set of potential `detail`, `supporting_html`, and `linked_pdf` URLs

Rules:
- preserve existing safe-fetch, same-domain, and role-aware boundaries
- keep the bounded top-N candidate discipline so discovery remains reproducible and operable
- continue to treat `detail` as the candidate-producing role by default

This means heuristic extraction still matters, but it stops being the final authority on link promotion.

### 4.2 Stage B: Hybrid Scoring

FPDS should score the candidate set through two parallel paths.

Path 1: deterministic heuristic score
- URL token match
- anchor-text match
- hub-page path signals
- supporting-keyword penalties
- excluded-flow penalties such as login, compare, apply, authenticated, or promo flows

Path 2: AI parallel score
- evaluate each bounded candidate against the product-type definition
- return a structured score plus rationale
- decide whether the page is likely `detail`, `supporting`, or irrelevant

The AI path should not freely invent URLs at this stage.
It should score the candidate set produced by the deterministic path, plus approved seed hints, in parallel.

This is the key design shift:
- current baseline: `heuristics first, AI fallback`
- new baseline: `heuristics generate candidates, AI scores candidates in parallel`

### 4.3 Stage C: Page-Level Evidence Validation

After a candidate URL is tentatively scored as `detail`, FPDS should fetch or inspect that page and compute a page-level evidence score before promoting it into a generated `detail` source row.

Minimum page-level evidence inputs:
- final normalized URL
- page title
- main `h1`
- significant `h2` or section headings
- first meaningful body blocks
- presence of product-specific attributes such as rates, fees, transactions, term, eligibility, benefits, or account-opening context

The purpose is not full extraction.
The purpose is to answer:

`Does this page look like the official detail page for the selected product type?`

### 4.4 Promotion Decision

A URL should be promoted to a generated `detail` source only when:
- heuristic and AI scores do not indicate exclusion
- page-level evidence score crosses a minimum threshold
- the page remains same-domain and fetch-safe

Otherwise:
- demote to `supporting_html` if the page is useful but not candidate-producing
- keep as non-promoted candidate evidence only
- or drop it entirely when the score is too weak

---

## 5. AI Parallel Scorer Contract

### 5.1 Inputs

The AI parallel scorer should receive:
- product-type code
- product-type display name
- full product-type description
- discovery keywords
- bank name
- homepage URL
- bounded candidate URLs
- anchor text and local link context
- optional seed detail hints

### 5.2 Output Shape

The scorer should return structured output per candidate:
- `candidate_url`
- `candidate_label`
- `predicted_role`
- `relevance_score`
- `confidence_band`
- `reason_codes`
- `short_rationale`

Recommended reason-code vocabulary:
- `product_type_semantic_match`
- `detail_page_layout_signal`
- `pricing_or_feature_signal`
- `hub_page_not_detail`
- `supporting_terms_or_rates_page`
- `promo_or_apply_flow`
- `insufficient_evidence`
- `seed_hint_alignment`

### 5.3 Constraints

The parallel scorer:
- may rerank candidates
- may recommend demotion
- may elevate approved seed detail hints that match the current context
- should not broaden scope beyond approved same-domain candidates unless a separately approved URL-resolution path is active

This keeps the AI path useful without turning discovery into an unconstrained crawler.

---

## 6. Product-Type Description Usage

The current system already stores product-type `display_name`, `description`, and `discovery_keywords`.

The follow-on design requires stronger use of `description` itself.

Current runtime rule:
- when an operator creates a product type, FPDS generates `discovery_keywords` from the display name and full description through the configured AI provider when available
- the generator should use financial-domain knowledge to produce discovery-oriented terms and short phrases, not raw description tokens
- generated keywords should favor page-discovery signals such as product-category terms, URL or heading phrases, and product attributes that help find official bank pages
- filler words, generic single words, bank-specific product names, and sentence fragments should be filtered before persistence
- if the AI provider is unavailable, product type creation should still succeed using a conservative deterministic fallback, because missing AI credentials should not block registry administration

The description should explicitly inform:
- what makes a page a true detail page for this product type
- which fields or page signals should be present
- which nearby but non-detail pages are still useful as supporting sources
- what language should count as a semantic match even when the exact product-type label is absent from the URL

Current runtime note:
- product type identity remains the operator-managed DB code
- discovery may compute a bounded semantic profile from the registered display name, description, and discovery keywords when the code itself is too weak or mistyped
- this profile affects candidate generation, seed hints, page evidence, and supporting-link relevance only; persisted generated rows keep the registered product type code
- missing or inactive product type rows still fail clearly instead of being resolved through hidden aliases

Examples:
- `chequing` should weight transactions, monthly fee, debit-card usage, and day-to-day banking language
- `savings` should weight interest, savings growth, withdrawal or tiering language
- `gic` should weight term, maturity, redeemability, deposit minimum, or compounding language
- operator-managed product types should inherit the same contract through their stored display name and description

This is still not a full ontology engine.
It is a stronger text-grounded discovery contract for both heuristic feature generation and AI scoring.

---

## 7. Page-Level Evidence Scoring

### 7.1 Purpose

Page-level evidence scoring is the main guardrail against false-positive detail promotion.

It should answer:
- is this page clearly about one product or a product family
- does the page contain product-detail cues rather than only navigational or legal content
- does the content align with the selected product type

### 7.2 Minimum Signal Families

Evidence scoring should combine at least these signal families:

1. `identity signals`
- page title
- H1
- canonical path tokens

2. `product-detail signals`
- rates
- fees
- transactions
- term or maturity
- eligibility
- account benefits
- account-opening or account-usage instructions

3. `negative signals`
- compare pages
- apply/login flows
- promo-only landing pages
- generic category pages
- pure legal or footer pages with no product detail

### 7.3 Output

For each promoted URL, FPDS should retain evidence-scoring metadata such as:
- `page_evidence_score`
- `page_evidence_reason_codes`
- `page_title_match`
- `heading_match`
- `attribute_signal_count`
- `negative_signal_count`

This metadata should become part of generated-source explainability and future run diagnostics.

---

## 8. Confidence and Selection Model

FPDS should move from a single implicit selection decision to an explicit layered confidence model.

Recommended decision components:
- `heuristic_score`
- `ai_parallel_score`
- `page_evidence_score`
- `seed_alignment_bonus`
- `negative_signal_penalty`

Recommended output:
- `selection_confidence`
- `selection_reason_codes`
- `selection_path`

Recommended selection-path vocabulary:
- `heuristic_plus_ai_plus_page_evidence`
- `heuristic_plus_page_evidence`
- `seed_hint_plus_ai_plus_page_evidence`
- `supporting_only`
- `rejected_candidate`

This gives operators and later reviewers a clearer answer to:

`Why was this page promoted as a detail source?`

---

## 9. Observability and Operator UX

This design should improve discovery observability without changing the bank-centered workflow.

Minimum follow-on expectations:
- generated-source rows should retain discovery-scoring metadata or a compact explainability subset
- run detail should distinguish `discovery weak` from `fetch failed`
- no-detail outcomes should indicate whether candidate generation was empty or candidate validation rejected all pages
- audit history should preserve the reason a generated source was promoted, demoted, or preserved

This is especially important because current operator pain already shows a difference between:
- no detail found
- detail found but fetch timed out
- detail found but page-level evidence too weak

---

## 10. Rollout Strategy

This design should be implemented in narrow slices.

Recommended rollout:

1. add structured AI parallel scoring over bounded candidates
2. add page-level evidence score for tentative detail pages
3. persist discovery-scoring metadata on generated source rows
4. improve run/admin diagnostics for discovery-stage reasoning

This avoids a large one-shot refactor while still improving the weakest selection points first.

---

## 11. Non-Goals

This design does not require:
- replacing the DB-backed source registry model
- switching to vector-first retrieval for homepage discovery
- replacing same-domain safe-fetch rules
- allowing AI to autonomously expand into arbitrary off-domain pages
- auto-publishing candidates for product types that require generic fallback handling
- adding a browser-rendered crawler as the default path

Push-back note:
- a full browser or vector-first discovery engine may eventually be useful, but it is not the next best move while the current system still gains substantial value from better bounded scoring and explainability

---

## 12. Acceptance Shape for Future Implementation

Future implementation should be considered aligned to this design when:
- homepage-first discovery still begins from the bank homepage and bounded same-domain expansion
- AI is used as a parallel scorer for candidate reranking, not only as a fallback after heuristic failure
- product-type description materially affects discovery scoring
- page-level evidence scoring gates `detail` promotion
- generated-source explainability and run diagnostics improve accordingly

---

## 13. Change History

| Date | Change |
|---|---|
| 2026-04-18 | Added the homepage-first discovery quality-improvement baseline centered on AI parallel scoring, stronger product-type description usage, and page-level evidence scoring |
| 2026-04-18 | Recorded the first implementation slice: bounded AI parallel scorer, page-level evidence gating, generated-source discovery metadata persistence, and source-detail explainability |
| 2026-04-26 | Recorded the runtime rule that product type `discovery_keywords` are AI-generated from display name and description when the provider is configured, with deterministic fallback only for provider-unavailable cases |
