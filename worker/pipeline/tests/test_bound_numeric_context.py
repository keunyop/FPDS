import unittest
from dataclasses import replace
from unittest.mock import patch
from worker.pipeline.tests.test_normalization import _build_input, _field, _evidence
from worker.pipeline.fpds_normalization.service import _normalize_candidate

class BoundNumericContextTests(unittest.TestCase):
    def test_bound_rate_does_not_merge_unrelated_matching_percentages(self):
        sentence = "The current preferred annual interest rates for the Account are: 21.99% on purchases and 22.99% on cash advances (including balance transfers and cash-like transactions)."
        metadata = {"official_grounding_contract_version": "collection-official-grounding-v2", "official_verification_status": "match", "official_web_sources": [{"url": "https://www.td.com/card"}], "evidence_quote": sentence}
        rate = replace(_field("purchase_interest_rate", 21.99, "decimal", 1, evidence_chunk_id="bound"), evidence_text_excerpt=sentence, anchor_value="Rates and Fees", field_metadata=metadata)
        bound = replace(_evidence("purchase_interest_rate", "21.99", "bound"), evidence_text_excerpt=sentence, anchor_value="Rates and Fees")
        unrelated = replace(_evidence("currency_context", "", "other"), evidence_text_excerpt="For an introductory offer, purchases attract 21.99% for the first month if you qualify.", anchor_value="Offer")
        item = replace(_build_input(), source_metadata={"product_type": "credit-card", "expected_fields": ["annual_fee", "purchase_interest_rate"]}, schema_context={"product_type": "credit-card", "product_family": "credit"}, extracted_fields=[_field("product_type", "credit-card", "string", 1), _field("product_name", "Example Card", "string", 1), _field("currency", "CAD", "string", 1), rate], evidence_links=[bound, unrelated])
        with patch("worker.pipeline.fpds_normalization.service.llm_provider_configured", return_value=False):
            record, _, _, _ = _normalize_candidate(run_id="run-test", candidate_id="candidate", normalization_model_execution_id="model", item=item)
        self.assertEqual(record["candidate_payload"].get("purchase_interest_rate"), 21.99)
        self.assertEqual(record["field_mapping_metadata"]["purchase_interest_rate"]["evidence_chunk_id"], "bound")

    def test_bound_conditional_rate_still_excluded(self):
        # Shared full-evidence acceptance remains binding even for an exact extraction.
        from worker.pipeline.fpds_collection_accuracy import quote_supports_value
        self.assertFalse(quote_supports_value("purchase_interest_rate", 21.99, "The current preferred annual interest rates for the Account are: 21.99% on purchases and 22.99% on cash advances. Provided you make every payment."))

    def test_current_no_fee_is_distinct_from_future_changes_or_temporary_waivers(self):
        from worker.pipeline.fpds_collection_accuracy import quote_supports_value
        current = "Rates and Fees: There is currently no annual fee for the primary card and no fee for each additional card. All rates, fees, features and benefits are subject to change."
        self.assertTrue(quote_supports_value("annual_fee", 0, current))
        for bad in ["No annual fee in the first year.", "No annual fee subject to maintaining a balance.", "No annual fee if you qualify.", "No annual fee for the first 6 months.", "No annual fee subject to change after one year.", "No annual fee only for new customers. All fees are subject to change.", "Introductory no annual fee."]:
            self.assertFalse(quote_supports_value("annual_fee", 0, bad))
