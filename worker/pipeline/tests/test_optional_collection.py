"""Optional facts share the required-fact evidence boundary and need no repair."""
import json
from copy import deepcopy
import unittest
from dataclasses import asdict
from unittest.mock import patch

from worker.pipeline.fpds_approval_policy import comparison_quality, dynamic_repair_fields
from worker.pipeline.fpds_collection_accuracy import sanitize_candidate, acceptance_receipt_valid
from worker.pipeline.fpds_evidence_retrieval.models import EvidenceChunkCandidate
from worker.pipeline.fpds_extraction.models import ExtractionDocumentContext
from worker.pipeline.fpds_extraction.service import _extract_official_fields_with_ai
from worker.pipeline.fpds_market_profile import country_product_profile
from worker.pipeline.fpds_normalization.models import NormalizationInput, NormalizationExtractedField, NormalizationEvidenceLink
from worker.pipeline.fpds_normalization.service import _normalize_candidate

URL = "https://bank.example/product"
INVOKE = "worker.pipeline.fpds_extraction.service.invoke_openai_json_schema"


def context(product_type="savings", country="CA", expected=None):
    return ExtractionDocumentContext("parsed", "source", "snapshot", "EXAMPLE", country, "html", "en", {
        "product_type": product_type, "product_type_dynamic": True,
        "expected_fields": expected or ["product_name"], "discovery_role": "detail",
        "official_domain_allowlist": ["bank.example"], "source_url": URL,
    })


def extract(ctx, facts, *, overrides=None):
    chunks, entries = [], []
    for name, (value, quote) in facts.items():
        chunks.append(EvidenceChunkCandidate(name, "parsed", 0, "section", "product", None, "en", quote,
            {}, "source", "snapshot", "EXAMPLE", ctx.country_code, "html"))
        entries.append({"field_name": name, "status": "match", "has_verified_value": True,
            "verified_value_json": json.dumps(value), "evidence_chunk_id": name,
            "evidence_quote": quote, "confidence": .99, "sources": [{"url": URL}],
            **(overrides or {}).get(name, {})})
    with patch(INVOKE, return_value=({"fields": entries}, {"web_search_sources": [{"url": URL}]})) as call:
        result = _extract_official_fields_with_ai(context=ctx, candidates=chunks,
            requested_fields=list(ctx.source_metadata["expected_fields"]), collected_fields=[])
    call.assert_called_once()
    return result, call, chunks


class OptionalCollectionTests(unittest.TestCase):
    def test_all_supported_profiles_request_optional_fields_without_making_them_required(self):
        for country in ("CA", "US"):
            for product_type in ("chequing", "savings", "gic", "credit-card", "mortgage", "personal-loan", "line-of-credit"):
                with self.subTest(country=country, product_type=product_type):
                    profile = country_product_profile(country_code=country, product_type=product_type)
                    _, call, _ = extract(context(product_type, country), {})
                    payload = call.call_args.kwargs["payload"]
                    self.assertTrue(set(profile.collection_fields) <= set(payload["requested_fields"]))
                    self.assertEqual(set(profile.supplemental_fields), set(payload["supplemental_fields"]))
                    self.assertFalse(set(payload["supplemental_fields"]) & set(payload["required_comparison_fields"]))
                    self.assertNotIn("eligibility_text", payload["requested_fields"])
                    self.assertIn("Do not start extra searches", call.call_args.kwargs["instructions"])

    def test_registered_optional_field_has_contract_but_unknown_field_is_not_requested(self):
        _, call, _ = extract(context("credit-card", expected=["product_name", "rewards_summary", "invented_field"]), {})
        payload = call.call_args.kwargs["payload"]
        self.assertIn("rewards_summary", payload["supplemental_fields"])
        self.assertNotIn("invented_field", payload["requested_fields"])
        self.assertEqual(payload["expected_fields"], payload["requested_fields"])

    def test_optional_extraction_requires_exact_consulted_evidence_and_native_type(self):
        facts = {"minimum_deposit": (500, "Minimum opening deposit $500 CAD")}
        cases = ({}, {"verified_value_json": '\"500\"'}, {"evidence_quote": "Minimum deposit $500"},
                 {"sources": [{"url": "https://other.example/product"}]}, {"evidence_chunk_id": "invented"},
                 {"verified_value_json": "0"}, {"status": "unverified"})
        for override in cases:
            with self.subTest(override=override):
                (fields, _, _), _, _ = extract(context(), facts, overrides={"minimum_deposit": override})
                self.assertEqual(len(fields), 0 if override else 1)
                if fields:
                    self.assertEqual(float(fields[0].candidate_value), 500)
                    self.assertEqual(fields[0].value_type, "decimal")

    def test_missing_optional_output_is_not_an_extraction_failure(self):
        (_, notes, _), _, _ = extract(context(), {})
        self.assertNotIn('"minimum_deposit": "model_field_missing"', " ".join(notes))
        self.assertIn('"monthly_fee": "model_field_missing"', " ".join(notes))

    def test_proven_optional_facts_survive_normalization_and_acceptance_with_old_source_fields(self):
        cases = (
            ("savings", {
                "product_name": ("Example Savings", "Example Savings in Canadian dollars"),
                "standard_rate": (2.5, "Annual interest rate 2.5% CAD"),
                "monthly_fee": (0, "Monthly fee $0 CAD"),
                "minimum_deposit": (500, "Minimum opening deposit $500 CAD"),
            }, "minimum_deposit", 500),
            ("personal-loan", {
                "product_name": ("Example Personal Loan", "Example Personal Loan in Canadian dollars"),
                "interest_rate": (6.5, "Annual interest rate 6.5% CAD"),
                "term_length_text": ("Term: 12 months", "Term: 12 months"),
                "secured_flag": (False, "This loan is unsecured. No collateral required."),
            }, "secured_flag", False),
        )
        for product_type, facts, optional_name, value in cases:
            with self.subTest(product_type=product_type):
                ctx = context(product_type)
                facts = {**facts, "currency": ("CAD", "Currency: CAD")}
                (fields, _, _), _, chunks = extract(ctx, facts)
                self.assertIn(optional_name, [f.field_name for f in fields])
                item = NormalizationInput("src", "source", "snapshot", "parsed", "extract", "private/key", None,
                    "EXAMPLE", "CA", "html", "en", ctx.source_metadata,
                    {"product_type": product_type, "product_family": "deposit" if product_type == "savings" else "lending"},
                    [NormalizationExtractedField(**asdict(f)) for f in fields],
                    [NormalizationEvidenceLink(f.field_name, str(f.candidate_value), f.evidence_chunk_id,
                        f.evidence_text_excerpt, "source", "snapshot", .99, "extract", f.anchor_type,
                        f.anchor_value, f.page_no, f.chunk_index) for f in fields], [], normalized_source_url=URL)
                with patch("worker.pipeline.fpds_normalization.service.llm_provider_configured", return_value=False):
                    record, _, _, _ = _normalize_candidate(run_id="run", candidate_id="candidate",
                        normalization_model_execution_id="normalize", item=item)
                evidence = [{"evidence_chunk_id": c.evidence_chunk_id, "evidence_excerpt": c.evidence_excerpt,
                             "source_url": URL} for c in chunks]
                clean, receipt = sanitize_candidate(record, source_metadata=ctx.source_metadata, evidence=evidence)
                self.assertEqual(clean["candidate_payload"].get(optional_name), value, (receipt, record["field_mapping_metadata"].get(optional_name)))
                self.assertIsInstance(clean["candidate_payload"][optional_name], bool if isinstance(value, bool) else (int, float))
                self.assertTrue(receipt["accepted"], receipt)
                self.assertTrue(acceptance_receipt_valid(clean))
                invalid = deepcopy(record)
                invalid["field_mapping_metadata"][optional_name]["official_evidence_quote"] = "Invented quote"
                omitted, omitted_receipt = sanitize_candidate(invalid, source_metadata=ctx.source_metadata, evidence=evidence)
                self.assertNotIn(optional_name, omitted["candidate_payload"])
                self.assertTrue(omitted_receipt["accepted"], omitted_receipt)
                self.assertTrue(acceptance_receipt_valid(omitted))
                incomplete = deepcopy(record)
                for name in ("standard_rate", "public_display_rate", "interest_rate", "interest_rate_summary"):
                    incomplete["candidate_payload"].pop(name, None)
                self.assertFalse(sanitize_candidate(incomplete, source_metadata=ctx.source_metadata, evidence=evidence)[1]["accepted"])
                # An unavailable optional value does not veto acceptance or add repair targets.
                del clean["candidate_payload"][optional_name]
                self.assertTrue(comparison_quality(country_code="CA", product_type=product_type,
                    expected_fields=list(facts), candidate_payload=clean["candidate_payload"]).complete)
                self.assertNotIn(optional_name, dynamic_repair_fields(country_code="CA", product_type=product_type,
                    expected_fields=list(facts), candidate_payload=clean["candidate_payload"]))
