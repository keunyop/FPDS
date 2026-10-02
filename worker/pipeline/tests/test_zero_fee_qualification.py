import unittest
from worker.pipeline.fpds_collection_accuracy import quote_supports_value

class ZeroFeeQualificationTests(unittest.TestCase):
    def test_temporal_and_balance_tier_zero_are_not_unconditional_prices(self):
        contexts = [
            "New to Canada. Start banking with this account and pay no monthly fee for 2 years.",
            "No monthly fee for two years. Monthly fee $0.",
            "No monthly fee until age 25.",
            "No monthly fee for full-time students. Benefits until 6 months after graduation. Monthly fee $0.",
            "Tier 2. $40,000 to $99,999 Average Monthly Balance in personal deposit and investment holdings. Monthly fee: $0.",
            "Average daily balance $25,000 or more. Monthly fee $0.",
        ]
        for context in contexts:
            with self.subTest(context=context):
                self.assertFalse(quote_supports_value("monthly_fee", 0, context))
                self.assertFalse(quote_supports_value("public_display_fee", 0, context))

    def test_regular_base_fee_and_unqualified_zero_are_preserved(self):
        self.assertTrue(quote_supports_value("monthly_fee", 16.95, "Monthly fee $16.95 or $0 rebated with an end-of-day account balance of $4,000 each day for that month."))
        self.assertTrue(quote_supports_value("monthly_fee", 0, "No monthly fee."))
        self.assertTrue(quote_supports_value("annual_fee", 0, "There is currently no annual fee for the primary card. All rates and fees are subject to change."))
        self.assertFalse(quote_supports_value("annual_fee", 0, "No annual fee for 2 years."))


    def test_qualification_omits_the_fee_and_automatically_excludes_incomplete_product(self):
        from worker.pipeline.tests.test_collection_accuracy import candidate_fixture
        from worker.pipeline.fpds_collection_accuracy import sanitize_candidate
        row, metadata, evidence = candidate_fixture()
        quote = "Monthly fee $0 CAD for 2 years."
        row["field_mapping_metadata"]["monthly_fee"]["official_evidence_quote"] = quote
        evidence = [dict(e, evidence_excerpt=quote) if e["evidence_chunk_id"] == "monthly_fee" else e for e in evidence]
        clean, receipt = sanitize_candidate(row, source_metadata=metadata, evidence=evidence)
        self.assertFalse(receipt["accepted"])
        self.assertIn("monthly_fee", receipt["missing_fields"])
        self.assertNotIn("monthly_fee", clean["candidate_payload"])
        self.assertNotIn("public_display_fee", clean["candidate_payload"])
