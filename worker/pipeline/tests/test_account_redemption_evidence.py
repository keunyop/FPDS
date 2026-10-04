"""Saved official account/GIC facts survive ordinary automatic collection."""
import json
from dataclasses import replace
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from worker.pipeline.fpds_collection_accuracy import quote_supports_value
from worker.pipeline.fpds_extraction.service import _extract_early_withdrawal_penalty
from worker.pipeline.fpds_approval_policy import withdrawal_consequences_usable

FIXTURE = Path(__file__).parent / "fixtures/golden/coast_collection_evidence_2026_10_03.json"

class AccountRedemptionEvidenceTests(unittest.TestCase):
    def test_explicit_base_zero_survives_separate_no_cost_service_eligibility(self):
        quote = "Monthly Fee\n$0\n(this is our low-cost account and it can qualify as a no-cost account\n2\n)"
        self.assertTrue(quote_supports_value("monthly_fee", 0, quote))
        for suffix in [" if you are a student", " when you maintain $4,000", " for the first year", " only for eligible customers"]:
            self.assertFalse(quote_supports_value("monthly_fee", 0, quote + suffix))
        self.assertFalse(quote_supports_value("monthly_fee", 0, "Monthly Fee $0 if you qualify as a no-cost account"))

    def test_explicit_redemption_waiting_period_and_no_penalty_are_preserved(self):
        quote = "Redeemable after 30 days without penalty on payable interest."
        self.assertEqual(_extract_early_withdrawal_penalty(quote), quote)
        self.assertTrue(quote_supports_value("early_withdrawal_penalty", quote, quote))
        self.assertIsNone(_extract_early_withdrawal_penalty("Redeemable after 30 days. See the terms."))

    def test_explicit_loss_of_all_interest_is_a_material_consequence(self):
        quote = "No interest will be paid if you redeem this GIC within the first 6 months."
        self.assertTrue(withdrawal_consequences_usable(quote))
        self.assertEqual(_extract_early_withdrawal_penalty(quote), quote)
        for bad in ["Interest is paid after six months.", "No interest will be paid on the account.", "No interest may be paid if you redeem early.", "No interest will be paid if you do not redeem the GIC."]:
            self.assertFalse(withdrawal_consequences_usable(bad), bad)


    def test_qualified_or_conflicting_redemption_cannot_drop_conditions(self):
        for prefix in ["If you are eligible, ", "Subject to approval, ", "Unless otherwise agreed, "]:
            quote = prefix + "Redeemable after 30 days without penalty on payable interest."
            self.assertEqual(_extract_early_withdrawal_penalty(quote), quote)
        conflict = "Redeemable after 30 days without penalty on payable interest. Early withdrawal fee is $25."
        self.assertIsNone(_extract_early_withdrawal_penalty(conflict))

    def test_target_product_terms_survive_companion_budget(self):
        from worker.pipeline.fpds_extraction.service import _select_official_grounding_chunks
        from worker.pipeline.fpds_evidence_retrieval.models import EvidenceChunkCandidate
        from worker.pipeline.fpds_extraction.models import ExtractedFieldCandidate
        base = EvidenceChunkCandidate("own", "parsed", 0, "section", "heading", None, "en", "Everyday GIC", {}, "doc", "snap", "BANK", "CA", "html")
        field = ExtractedFieldCandidate("product_name", "Everyday GIC", "string", 1, "capture", "doc", "snap", "own", "Everyday GIC", "section", "heading", None, 0, {})
        noisy = [replace(base, evidence_chunk_id="noise-"+str(i), source_document_id="terms", evidence_excerpt="GIC rates and fees for Premium GIC.") for i in range(40)]
        target = replace(base, evidence_chunk_id="target", source_document_id="terms", anchor_type="product_terms_declaration", evidence_excerpt="Everyday GIC. Redeemable after 30 days without penalty on payable interest.")
        selected = _select_official_grounding_chunks(candidates=[base,*noisy,target], collected_fields=[field], product_name="Everyday GIC")
        self.assertLessEqual(len(selected),24)
        self.assertIn(target,selected)

    def test_captured_redemption_keeps_country_snapshot_and_product_boundaries(self):
        from worker.pipeline.fpds_extraction.service import _append_captured_decision_facts
        from worker.pipeline.fpds_extraction.models import ExtractionDocumentContext
        from worker.pipeline.fpds_evidence_retrieval.models import EvidenceChunkCandidate
        for bank,country,url in [("EXAMPLE", "US", "https://examplebank.com/cd"), ("OTHER", "CA", "https://examplebank.com/gic")]:
            ctx = ExtractionDocumentContext("parsed", "doc", "snap", bank, country, "html", "en", {"product_type":"gic",
                "discovery_role":"detail", "normalized_source_url":url, "official_domain_allowlist":["examplebank.com"],
                "discovery_metadata":{"product_identity_match":True,"primary_heading":"Everyday GIC","page_title":"Everyday GIC | Example Bank"}})
            base = EvidenceChunkCandidate("chunk", "parsed", 0, "section", "gic-details", None, "en", "Redeemable after 30 days without penalty on payable interest.", {}, "doc", "snap", bank, country, "html")
            fields = ["redeemable_flag","early_withdrawal_penalty"]
            self.assertEqual({f.field_name for f in _append_captured_decision_facts(context=ctx, candidates=[base], fields=[], requested_fields=fields)},set(fields))
            for bad in [replace(base,bank_code="FOREIGN"), replace(base,country_code="JP"), replace(base,source_snapshot_id="old"),
                        replace(base,parsed_document_id="other"), replace(base,anchor_value="compare-other-products")]:
                self.assertEqual(_append_captured_decision_facts(context=ctx, candidates=[bad], fields=[], requested_fields=fields),[])

    def test_redemption_minimum_stays_attached_to_loss_declaration(self):
        quote = "No interest will be paid if you redeem this GIC within the first 6 months. Minimum redemption amount of $500 while maintaining the minimum investment amount."
        self.assertEqual(_extract_early_withdrawal_penalty(quote), quote)

    def test_named_terms_do_not_prove_an_unrelated_or_ambiguous_product(self):
        from worker.pipeline.fpds_parse_chunk.parser import parse_snapshot_bytes
        from worker.pipeline.fpds_parse_chunk.service import _build_evidence_chunks
        raw = FIXTURE.with_name("coast_gic_product_terms_dom.html").read_bytes()
        art = parse_snapshot_bytes(body=raw, content_type="text/html")
        terms = [s for s in art.segments if s.anchor_type == "product_terms_declaration"]
        better = next(s for s in terms if s.anchor_value.endswith("1-year-better-than-cash-gic"))
        self.assertIn("No interest will be paid", better.text)
        self.assertNotIn("Months 1-8", better.text)
        chunks = _build_evidence_chunks(parsed_document_id="terms", source_language="en", artifact=art, max_chars=100, overlap_chars=10)
        ch = next(c for c in chunks if c.anchor_type == "product_terms_declaration" and c.anchor_value == better.anchor_value)
        self.assertEqual(ch.evidence_excerpt, better.text)
        ambiguous = raw.replace(b'class="prod-title"', b'class="unknown-title"')
        self.assertFalse(any(s.anchor_type == "product_terms_declaration" for s in parse_snapshot_bytes(body=ambiguous, content_type="text/html").segments))

    def test_saved_run_through_ordinary_services_recovers_three_products_without_waiving_missing_terms(self):
        from worker.pipeline.fpds_evidence_retrieval.models import EvidenceChunkCandidate
        from worker.pipeline.fpds_extraction.models import ExtractionDocumentContext, ExtractionInput, ExtractedFieldCandidate
        from worker.pipeline.fpds_extraction.service import ExtractionService, _bind_grounding_evidence
        from worker.pipeline.fpds_extraction.storage import ExtractionStorageConfig, build_object_store
        from worker.pipeline.fpds_normalization.models import NormalizationInput, NormalizationExtractedField, NormalizationEvidenceLink
        from worker.pipeline.fpds_normalization.service import NormalizationService
        from worker.pipeline.fpds_normalization.storage import NormalizationStorageConfig
        from worker.pipeline.fpds_validation_routing.models import ValidationInput, ValidationEvidenceLink, ValidationRoutingConfig
        from worker.pipeline.fpds_validation_routing.service import ValidationRoutingService
        from worker.pipeline.fpds_validation_routing.storage import ValidationRoutingStorageConfig
        products = json.loads(FIXTURE.read_text(encoding="utf8"))["products"]
        better = next(p for p in products if "better-than-cash" in p["url"])
        cases = [(p, True) for p in products] + [(better, False)]
        for product, include_companion in cases:
            ctx = ExtractionDocumentContext("parsed", "doc", "snap", "CCS", "CA", "html", "en", product["metadata"], "source")
            chunks = [EvidenceChunkCandidate(**row, parsed_document_id="parsed", source_document_id="doc",
                source_snapshot_id="snap", bank_code="CCS", country_code="CA", source_type="html") for row in product["chunks"]]
            saved = [ExtractedFieldCandidate(**field) for field in product["saved_fields"]]
            extraction_input = ExtractionInput(ctx, chunks)
            if "better-than-cash" in product["url"] and include_companion:
                from worker.pipeline.fpds_parse_chunk.parser import parse_snapshot_bytes
                from worker.pipeline.fpds_parse_chunk.service import _build_evidence_chunks
                art = parse_snapshot_bytes(body=FIXTURE.with_name("coast_gic_product_terms_dom.html").read_bytes(), content_type="text/html")
                terms_ctx = ExtractionDocumentContext("terms-parsed", "terms-doc", "terms-snap", "CCS", "CA", "html", "en",
                    {"discovery_role":"supporting_html", "normalized_source_url":"https://www.coastcapitalsavings.com/investments/gics",
                     "discovery_metadata":{"parent_detail_urls":[product["url"]]}})
                terms = [EvidenceChunkCandidate(**{k:v for k,v in ch.to_record().items() if k in EvidenceChunkCandidate.__dataclass_fields__},
                    source_document_id="terms-doc", source_snapshot_id="terms-snap", bank_code="CCS", country_code="CA", source_type="html")
                    for ch in _build_evidence_chunks(parsed_document_id="terms-parsed", source_language="en", artifact=art, max_chars=6400, overlap_chars=120)]
                extraction_input = _bind_grounding_evidence([extraction_input, ExtractionInput(terms_ctx, terms)])[0]
            with TemporaryDirectory() as temp:
                cfg = ExtractionStorageConfig("filesystem", "test", "extracted", "hot", filesystem_root=temp)
                store = build_object_store(cfg)
                # Replay recorded output of the original model; no new facts are
                # invented and no provider/network/data mutation is permitted.
                with patch("worker.pipeline.fpds_extraction.service.llm_provider_configured", return_value=True), patch(
                    "worker.pipeline.fpds_extraction.service.grounded_with_reuse", return_value=(saved, [], None)):
                    extracted = ExtractionService(storage_config=cfg, object_store=store)._extract_single_document(
                        run_id="run", extraction_input=extraction_input, correlation_id="test", request_id="test", override_field_names=None)
                self.assertIsNone(extracted.error_summary)
                item = NormalizationInput("source", "doc", "snap", "parsed", extracted.model_execution_id,
                    extracted.extracted_storage_key, extracted.metadata_storage_key, "CCS", "CA", "html", "en", ctx.source_metadata,
                    product["schema_context"], [NormalizationExtractedField(**f.to_dict()) for f in extracted.extracted_fields],
                    [NormalizationEvidenceLink(**f.to_dict()) for f in extracted.evidence_links], [], product["url"],
                    evidence_origins={c.evidence_chunk_id: {"run_id":"run", "bank_code":"CCS", "country_code":"CA",
                        "source_document_id":c.source_document_id, "snapshot_id":c.source_snapshot_id, "parsed_document_id":c.parsed_document_id,
                        "evidence_chunk_id":c.evidence_chunk_id, "evidence_excerpt":c.evidence_excerpt, "source_url":c.retrieval_metadata.get("source_url",product["url"])} for c in extraction_input.grounding_candidates or chunks}, evidence_origins_resolved=True)
                ncfg = NormalizationStorageConfig("filesystem", "test", "normalized", "hot", filesystem_root=temp)
                with patch("worker.pipeline.fpds_normalization.service.llm_provider_configured", return_value=False):
                    normalized = NormalizationService(storage_config=ncfg, object_store=store).normalize_inputs(run_id="run", inputs=[item]).source_results[0]
                self.assertIsNone(normalized.error_summary)
                record = normalized.normalized_candidate_record
                receipt = record["candidate_payload"]["_collection_accuracy"]
                expected_accepted = include_companion or "better-than-cash" not in product["url"]
                if "better-than-cash" in product["url"] and include_companion:
                    self.assertIn("No interest will be paid", record["candidate_payload"]["early_withdrawal_penalty"])
                self.assertEqual(receipt["accepted"], expected_accepted, receipt)
                links = [ValidationEvidenceLink(**{k:v for k,v in f.items() if k in ValidationEvidenceLink.__dataclass_fields__}) for f in normalized.field_evidence_link_records]
                vin = ValidationInput("source", "doc", "snap", "parsed", normalized.candidate_id, "run", normalized.normalization_model_execution_id,
                    normalized.normalized_storage_key, normalized.metadata_storage_key, "CCS", "CA", "html", "en", ctx.source_metadata, record, links, [])
                vcfg = ValidationRoutingStorageConfig("filesystem", "test", "validated", "hot", filesystem_root=temp)
                result = ValidationRoutingService(storage_config=vcfg, object_store=store).validate_and_route_inputs(run_id="run", inputs=[vin],
                    taxonomy_registry={"chequing":{"other","standard","package"},"gic":{"other","redeemable"}},
                    routing_config=ValidationRoutingConfig("phase1", .82, .6, set())).source_results[0]
                self.assertEqual(result.validation_action, "auto_validated" if expected_accepted else "excluded", result.runtime_notes)
                self.assertIsNone(result.review_task_record)

if __name__ == "__main__":
    unittest.main()
