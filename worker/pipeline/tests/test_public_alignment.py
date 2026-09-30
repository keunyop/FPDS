import unittest
from unittest.mock import patch
from worker.pipeline.fpds_extraction.models import ExtractionDocumentContext
from worker.pipeline.fpds_extraction.service import _extract_official_fields_with_ai, _extract_term_length_days
from worker.pipeline.fpds_approval_policy import collection_fields_for_product_type, comparison_quality, dynamic_repair_fields
from worker.pipeline.fpds_extraction.service import _extract_interest_calculation_method, _extract_interest_rate_summary, _ai_verified_value_is_supported_by_quote
from worker.pipeline.fpds_rate_safety import contains_explicit_rate_percentage, canonical_deposit_rate_suppression_reason, rate_component_only
from worker.pipeline.fpds_aggregate_refresh.models import CanonicalAggregateRow
from worker.pipeline.fpds_aggregate_refresh.service import AggregateRefreshService


class PublicAlignmentTests(unittest.TestCase):
    def test_optional_conditions_do_not_expand_approval_or_repair(self):
        for country in ("CA", "US"):
            fields = collection_fields_for_product_type(country_code=country, product_type="savings")
            payload = {"standard_rate": 1, "monthly_fee": 0, "minimum_balance": 0}
            self.assertTrue(comparison_quality(country_code=country, product_type="savings", expected_fields=fields, candidate_payload=payload).complete)
            self.assertEqual(dynamic_repair_fields(country_code=country, product_type="savings", expected_fields=fields, candidate_payload=payload), ["standard_rate", "monthly_fee", "minimum_balance"])
            self.assertIn("interest_calculation_method", fields)
            self.assertNotIn("eligibility_text", fields)
            self.assertEqual(len(fields), len(set(fields)))

    def test_single_grounding_pass_separates_essential_and_opportunistic_fields(self):
        fields = list(collection_fields_for_product_type(country_code="US", product_type="gic"))
        context = ExtractionDocumentContext("parsed", "document", "snapshot", "BANK", "US", "html", "en", {
            "product_type": "gic", "expected_fields": fields,
            "allowed_domains": ["bank.example"], "source_url": "https://bank.example/cd",
        })
        with patch("worker.pipeline.fpds_extraction.service.invoke_openai_json_schema", return_value=({"fields": []}, {})) as call:
            _extract_official_fields_with_ai(context=context, candidates=[], requested_fields=fields, collected_fields=[])
        call.assert_called_once()
        payload = call.call_args.kwargs["payload"]
        self.assertIn("early_withdrawal_penalty", payload["required_comparison_fields"])
        self.assertIn("interest_rate_summary", payload["required_comparison_fields"])
        self.assertIn("interest_calculation_method", payload["supplemental_fields"])
        self.assertIn("redeemable_flag", payload["supplemental_fields"])
        self.assertFalse(set(payload["required_comparison_fields"]) & set(payload["supplemental_fields"]))
        self.assertIn("Do not start extra searches", call.call_args.kwargs["instructions"])

    def test_us_projection_preserves_conditions_and_hides_private_fields(self):
        row = CanonicalAggregateRow("id", "BANK", "Bank", "US", "deposit", "gic", None, "CD", "en", "USD", "active", "2026-09-01", None, "v1", {
            "standard_rate": 3.5, "minimum_deposit": 500, "term_length_text": "1 year",
            "interest_calculation_method": "Annual percentage yield (APY).",
            "compounding_frequency": "daily", "redeemable_flag": False,
            "early_withdrawal_penalty": "90 days interest", "notes": "private operator note",
            "eligibility_text": "private unused copy", "promotional_rate": 4,
        })
        result = AggregateRefreshService()._build_projection_row(snapshot_id="snapshot", canonical_row=row)
        metadata = result["refresh_metadata"]
        self.assertIs(metadata["redeemable_flag"], False)
        self.assertEqual(metadata["deposit_conditions"]["compounding_frequency"], "daily")
        self.assertEqual(metadata["deposit_conditions"]["promotional_rate"], 4)
        self.assertNotIn("notes", metadata)
        self.assertNotIn("eligibility_text", metadata)
        self.assertEqual(result["last_verified_at"], "2026-09-01")

    def test_basis_requires_explicit_source_and_rejects_fx_calculator(self):
        self.assertEqual(_extract_interest_calculation_method("3.25% APY."), "3.25% APY.")
        self.assertEqual(_extract_interest_calculation_method("Interest is calculated daily at the annual interest rate."), "Interest is calculated daily at the annual interest rate.")
        self.assertIsNone(_extract_interest_calculation_method("How is the US conversion rate calculated?"))
        self.assertIsNone(_extract_interest_calculation_method("Earn 3.25%."))
        self.assertEqual(_extract_interest_rate_summary("3.25% APY."), "3.25% APY.")

    def test_ai_cannot_invent_annual_basis_from_bare_rate_quote(self):
        self.assertFalse(_ai_verified_value_is_supported_by_quote(
            field_name="interest_calculation_method", value="Annual interest rate.",
            evidence_quote="Interest is calculated daily. Rate: 3.25%."))
        self.assertTrue(_ai_verified_value_is_supported_by_quote(
            field_name="interest_calculation_method", value="Annual interest rate.",
            evidence_quote="Annual interest rate. Interest is calculated daily."))

    def test_cd_maturity_excludes_guarantee_funding_and_penalty_days(self):
        for text in ("10-Day CD Rate Guarantee", "Deposit to the CD within the first 10 days.", "CD penalty: 90 days interest.", "CD 10-day grace period."):
            self.assertIsNone(_extract_term_length_days(text), text)
        self.assertEqual(_extract_term_length_days("CD term: 12 months."), 360)
        self.assertEqual(_extract_term_length_days("CD term: 1 year interest rate 3%."), 365)

    def test_discount_and_capped_bonus_are_not_total_rates(self):
        for value, text in ((0.375, "Interest rate reduction of 0.375%"), (0.25, ".25% interest rate discount"), (0.25, "0.25% interest rate discount"), (1, "1% annual savings bonus up to $100"), (1, "1.00% APY rate boost")):
            with self.subTest(text=text):
                self.assertTrue(rate_component_only(value=value, context=text))
                self.assertFalse(contains_explicit_rate_percentage(text))
                self.assertEqual(canonical_deposit_rate_suppression_reason(value=value, context=text), "rate_component_not_total")
                self.assertFalse(_ai_verified_value_is_supported_by_quote(field_name="standard_rate", value=value, evidence_quote=text))

    def test_discounted_rate_requires_its_full_summary(self):
        text = "Interest rate 5.25% includes a 0.25% discount for autopay."
        self.assertTrue(contains_explicit_rate_percentage(text))
        self.assertFalse(rate_component_only(value=5.25, context=text))
        self.assertTrue(rate_component_only(value=0.25, context=text))
        self.assertFalse(_ai_verified_value_is_supported_by_quote(field_name="interest_rate", value=5.25, evidence_quote=text))
        self.assertTrue(_ai_verified_value_is_supported_by_quote(field_name="interest_rate_summary", value=text, evidence_quote=text))
        self.assertFalse(_ai_verified_value_is_supported_by_quote(field_name="interest_rate", value=0.25, evidence_quote=text))
        self.assertTrue(contains_explicit_rate_percentage("APR 9.99%-17.49% including 0.5% autopay discount."))


if __name__ == "__main__":
    unittest.main()
