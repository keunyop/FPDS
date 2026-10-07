"""Source-backed ordinary services, not direct injected financial values."""
from dataclasses import replace
from hashlib import sha256
from pathlib import Path
import json
import unittest
from tempfile import TemporaryDirectory
from unittest.mock import MagicMock, patch

from worker.pipeline.fpds_approval_policy import comparison_quality
from worker.pipeline.fpds_collection_accuracy import quote_supports_value
from worker.pipeline.tests.test_evidence_research_parity import input_from_segments, run_services

FIXTURES = Path(__file__).parent / "fixtures/admin-collection-parity"
MANIFEST = json.loads((FIXTURES / "sources.json").read_text(encoding="utf8"))


def official_input(target, *, filename=None, role="detail", parent=None, ident="detail"):
    from worker.discovery.fpds_discovery.fetch import DiscoveryFetchPolicy, FetchedResponse
    from worker.discovery.fpds_snapshot.capture import CaptureSource, SnapshotCaptureService
    from worker.discovery.fpds_snapshot.storage import SnapshotStorageConfig, build_object_store as snapshot_store
    from worker.pipeline.fpds_parse_chunk.models import ParseSourceSnapshot
    from worker.pipeline.fpds_parse_chunk.service import ParseChunkService
    from worker.pipeline.fpds_parse_chunk.storage import ParseChunkStorageConfig, build_object_store as parse_store
    from worker.pipeline.fpds_evidence_retrieval.models import EvidenceChunkCandidate
    file = filename or target["file"]
    content_type = "application/pdf" if file.endswith(".pdf") else "text/html"
    item = input_from_segments(bank="NATIONAL", url=target["url"],
        product=target.get("type", "credit-card"), name=target.get("name", "Official disclosure"),
        segments=[], role=role, parent=parent, ident=ident)
    ctx = replace(item.context, source_metadata={**item.context.source_metadata,
        "product_family": "card" if target.get("type") == "credit-card" else "deposit"})
    source = CaptureSource(ident, ctx.source_document_id, target["url"], target["url"],
        "pdf" if file.endswith(".pdf") else "html", "en", "NATIONAL", "CA", "P0", True, ctx.source_metadata)
    response = FetchedResponse((FIXTURES / file).read_bytes(), target["url"], content_type, 200,
        {"content-type": content_type}, "2026-10-06T14:30:00+00:00", 0)
    with TemporaryDirectory() as tmp:
        scfg = SnapshotStorageConfig("filesystem", "test", "snapshots", "hot", filesystem_root=tmp)
        captured = SnapshotCaptureService(fetch_policy=DiscoveryFetchPolicy(allowed_domains=("nbc.ca",), block_private_networks=False),
            storage_config=scfg, object_store=snapshot_store(scfg), fetcher=lambda *_: response).capture_sources(
                run_id="run", sources=[source]).source_results[0]
        if captured.snapshot_action != "stored":
            raise AssertionError(captured.error_summary)
        pcfg = ParseChunkStorageConfig("filesystem", "test", "snapshots", "parsed", "hot", filesystem_root=tmp)
        parsed = ParseChunkService(storage_config=pcfg, object_store=parse_store(pcfg)).parse_snapshots(run_id="run",
            snapshots=[ParseSourceSnapshot(captured.snapshot_id, ctx.source_document_id, captured.object_storage_key,
                content_type, "en", "NATIONAL", "CA", ident)]).source_results[0]
        if parsed.parse_action != "stored":
            raise AssertionError(parsed.error_summary)
        ctx = replace(ctx, snapshot_id=captured.snapshot_id, parsed_document_id=parsed.parsed_document_id)
        keys = {"evidence_chunk_id", "parsed_document_id", "chunk_index", "anchor_type", "anchor_value", "page_no",
                "source_language", "evidence_excerpt", "retrieval_metadata"}
        chunks = [EvidenceChunkCandidate(**{k: v for k, v in row.items() if k in keys},
            source_document_id=ctx.source_document_id, source_snapshot_id=ctx.snapshot_id,
            bank_code=ctx.bank_code, country_code=ctx.country_code, source_type=ctx.source_type)
            for row in parsed.evidence_chunk_records]
        return replace(item, context=ctx, candidates=chunks)


def ordinary_inputs(target, *, rendered=False):
    filename = target["file"]
    rendered_file = filename.replace(".html", "-rendered.html")
    if rendered and (FIXTURES / rendered_file).exists():
        filename = rendered_file
    detail = official_input(target, filename=filename)
    inputs = [detail]
    for c in MANIFEST["companions"]:
        if c["kind"] != "linked_pdf":
            continue
        if target["type"] == "credit-card" and c["file"] == "card-information.pdf" or (
            target["name"] == "Redeemable Plus GIC" and c["file"] == "plus-disclosure.pdf"):
            inputs.append(official_input({**c, "type": target["type"]}, role="linked_pdf",
                parent=target["url"], ident=c["file"]))
    return inputs


class AdminCollectionParityTests(unittest.TestCase):
    def test_preserved_seventeen_candidates_are_incomplete_under_current_essentials(self):
        self.assertEqual(len(MANIFEST["targets"]), 17)
        for target in MANIFEST["targets"]:
            with self.subTest(product=target["name"]):
                quality = comparison_quality(product_type=target["type"], expected_fields=[],
                    candidate_payload=target["baseline_payload"], country_code="CA")
                self.assertFalse(quality.complete)
                self.assertTrue(quality.missing_fields)

    def test_source_fixture_hashes_and_priority_count(self):
        self.assertEqual(sum(t["expected_complete"] for t in MANIFEST["targets"]), 6)
        for source in [*MANIFEST["targets"], *MANIFEST["companions"]]:
            self.assertEqual(sha256((FIXTURES / source["file"]).read_bytes()).hexdigest(),
                source["fixture_sha256"])

    def test_priority_facts_pass_actual_artifact_origin_normalization_and_routing(self):
        for target in MANIFEST["targets"]:
            if not target["expected_complete"]:
                continue
            with self.subTest(product=target["name"]):
                inputs = ordinary_inputs(target)
                record, validation, _ = run_services(inputs)
                self.assertEqual(validation.validation_action, "auto_validated",
                    record["candidate_payload"].get("_collection_accuracy"))
                self.assertIsNone(validation.review_task_record)
                self.assertEqual(record["currency"], "CAD")
                self.assert_real_promotion(record, validation, target, inputs[0].context.source_metadata)
                for field, value in target["expected_facts"].items():
                    self.assertEqual(record["candidate_payload"].get(field), value, field)
                if target["type"] == "credit-card":
                    self.assertIn("9 consecutive months", record["candidate_payload"]["purchase_interest_rate_summary"])
                    self.assertEqual(record["candidate_payload"]["cash_advance_rate"], 22.49)
                if target["type"] == "savings":
                    self.assertIn("monthly", record["candidate_payload"]["interest_payment_frequency"])
                    self.assertIn("annual", record["candidate_payload"]["interest_calculation_method"])
                if target["type"] == "gic":
                    self.assertIn("0.125%", record["candidate_payload"]["interest_calculation_method"])
                    self.assertNotIn("term_length_days", record["candidate_payload"])
                    self.assertIn("anniversary", record["candidate_payload"]["early_withdrawal_penalty"])

    def assert_real_promotion(self, record, validation, target, source_metadata):
        from api_service import candidate_auto_promotion as promotion
        from worker.pipeline.fpds_collection_accuracy import acceptance_receipt_valid
        row = {**record, **(validation.candidate_update_record or {}),
            "source_metadata": source_metadata, "discovery_role": "detail",
            "collection_ai_assessment": validation.model_execution_record["execution_metadata"]["collection_ai_assessment"]}
        self.assertTrue(acceptance_receipt_valid(row))
        policy = {"auto_approve_min_confidence": .82, "force_review_issue_codes": ["required_field_missing", "conflicting_evidence"]}
        with patch.object(promotion, "_load_auto_promotion_policy", return_value=policy), \
             patch.object(promotion, "_load_candidate_rows", return_value=[row]), \
             patch.object(promotion, "_apply_canonical_approval", return_value={"product_id": "fixture-product", "product_version_id": "fixture-version", "change_event_types": []}) as apply, \
             patch.object(promotion, "_mark_candidate_auto_promoted"), \
             patch.object(promotion, "_record_candidate_auto_promotion_audit_event"), \
             patch.object(promotion, "_supersede_stale_reviews_for_source", return_value=[]), \
             patch.object(promotion, "queue_auto_promotion_aggregate_refresh_request"), \
             patch.object(promotion, "_queue_candidate_for_review") as review:
            result = promotion.promote_auto_validated_candidates(MagicMock(), run_id="run")
        self.assertEqual(result["promoted_count"], 1, result)
        review.assert_not_called()
        for field, expected in target["expected_facts"].items():
            self.assertEqual(apply.call_args.kwargs["approved_payload"][field], expected)

    def test_fixed_monthly_base_fee_negation_does_not_negate_other_costs(self):
        self.assertTrue(quote_supports_value("monthly_fee", 0, "No fixed\nmonthly fees"))
        for quote in ["No fixed monthly fees if you maintain $5,000.",
            "No fixed monthly fees for the first year.", "No fixed transaction fees.",
            "Monthly fee $5. No fixed transaction fees."]:
            with self.subTest(quote=quote):
                self.assertFalse(quote_supports_value("monthly_fee", 0, quote))

    def test_investment_horizon_is_not_a_contract_term(self):
        self.assertFalse(quote_supports_value("term_length_text", "1 year", "Investment horizon:\n1 year"))
        self.assertFalse(quote_supports_value("term_length_text", "1 year", "Cash in after 1 year."))
        self.assertTrue(quote_supports_value("term_length_text", "36 months", "Term\n36 months"))

    def test_ambiguous_reduced_rate_fee_row_cannot_prove_regular_fee(self):
        quote = "Annual fees\nCards Main card Additional card\nECHO Cashback, Edition and Allure with Cashback, reduced interest rate $30.00 $0.00"
        from worker.native_information_records import shared_card_fee
        self.assertIsNone(shared_card_fee(quote))

    def test_normalizer_cannot_rewrite_proven_price_or_optional_conditions(self):
        target = next(t for t in MANIFEST["targets"] if t["expected_complete"] and t["type"] == "credit-card")
        rewrite = {"product_name": "Investment family", "candidate_payload": {"purchase_interest_rate": 99,
            "annual_fee": 0, "cash_advance_rate": None, "purchase_interest_rate_summary": None}}
        with patch("worker.pipeline.fpds_normalization.service._normalize_dynamic_fields_with_ai",
                   return_value=(rewrite, [], {})) as model:
            record, validation, _ = run_services(ordinary_inputs(target))
        model.assert_called_once()
        self.assertEqual(validation.validation_action, "auto_validated")
        self.assertEqual(record["candidate_payload"]["purchase_interest_rate"], 20.99)
        self.assertEqual(record["candidate_payload"]["annual_fee"], 30)
        self.assertEqual(record["candidate_payload"]["cash_advance_rate"], 22.49)
        self.assertIn("missed payment", record["candidate_payload"]["purchase_interest_rate_summary"])

    def test_final_model_no_facts_cannot_remove_proven_capture(self):
        target = next(t for t in MANIFEST["targets"] if t["expected_complete"] and t["type"] == "credit-card")
        with patch("worker.pipeline.fpds_extraction.service.grounded_with_reuse",
                   return_value=([], ["No additional facts"], {"model_id": "mock-provider"})) as model:
            record, validation, _ = run_services(ordinary_inputs(target), provider=True)
        self.assertGreaterEqual(model.call_count, 1)
        self.assertEqual(validation.validation_action, "auto_validated")
        for field, expected in target["expected_facts"].items():
            self.assertEqual(record["candidate_payload"][field], expected)

    def test_anniversary_redemption_keeps_the_full_condition(self):
        quote = "All or part of the GIC can be cashed in without penalty on the anniversary of the issue date."
        self.assertTrue(quote_supports_value("redeemable_flag", True, quote))
        self.assertFalse(quote_supports_value("non_redeemable_flag", True, quote))
        self.assertFalse(quote_supports_value("redeemable_flag", True,
            "All or part of the GIC might be cashed in without penalty."))

    def test_other_preserved_targets_cannot_borrow_priority_facts(self):
        for target in MANIFEST["targets"]:
            if target["expected_complete"]:
                continue
            with self.subTest(product=target["name"]):
                _, validation, _ = run_services(ordinary_inputs(target))
                self.assertEqual(validation.validation_action, "excluded")
                self.assertIsNone(validation.review_task_record)

    def test_insufficient_security_and_car_loan_rate_stay_excluded(self):
        for target in MANIFEST["targets"]:
            if target["type"] not in {"line-of-credit", "personal-loan"}:
                continue
            with self.subTest(product=target["name"]):
                record, validation, _ = run_services(ordinary_inputs(target))
                self.assertEqual(validation.validation_action, "excluded")
                self.assertIsNone(validation.review_task_record)
                if target["type"] == "line-of-credit":
                    self.assertNotIn("secured_flag", record["candidate_payload"])


if __name__ == "__main__":
    unittest.main()
