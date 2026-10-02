"""Regressions from the saved 2026-10-01 Alterna account captures."""
import unittest
from worker.pipeline.fpds_collection_accuracy import quote_supports_value, sanitize_candidate
from worker.pipeline.fpds_extraction.service import _ai_verified_value_is_supported_by_quote, _exact_quote_is_grounded
from worker.pipeline.tests.test_collection_accuracy import candidate_fixture

SAVINGS_CONTEXT = (
    "High Interest eSavings\nOverview\nHigh Interest eSavings\nNo Fee eChequing\n"
    "TFSA eSavings\nRRSP eSavings\nWays To Bank\nSaving made easy. Earn high interest on every dollar "
    "without having it locked in for an extended period of time. There are no monthly fees and no minimum balance required."
)
CHECKING_CONTEXT = (
    "No Monthly Account Fees\nNo monthly fee; No minimum balance required\n"
    "FREE , unlimited day-to-day transactions 1\nFREE\nFREE , unlimited Interac® e-Transfers\nFREE\n"
    "Award-winning No-Fee eChequing Account\nAward-winning\n"
    "Access to over 3,300 ATMs in THE EXCHANGE® Network - Canada's largest ATM network, surcharge-free! "
    "In the United States, access 40,000 surcharge-free ATM’s through the Allpoint Network .\nAllpoint Network"
)

class AlternaAccountEvidenceTests(unittest.TestCase):
    def test_saved_savings_zero_fee_survives_full_context(self):
        self.assertTrue(quote_supports_value("monthly_fee", 0, SAVINGS_CONTEXT))
        row, meta, evidence = candidate_fixture()
        row["field_mapping_metadata"]["monthly_fee"]["official_evidence_quote"] = "There are no monthly fees"
        next(e for e in evidence if e["evidence_chunk_id"] == "monthly_fee")["evidence_excerpt"] = SAVINGS_CONTEXT
        result, receipt = sanitize_candidate(row, source_metadata=meta, evidence=evidence)
        self.assertTrue(receipt["accepted"])
        self.assertEqual(result["candidate_payload"]["monthly_fee"], 0)

    def test_saved_checking_zero_fee_passes_grounding_meaning(self):
        self.assertTrue(_ai_verified_value_is_supported_by_quote(
            field_name="monthly_fee", value="0.00", evidence_quote="No monthly fee; No minimum balance required"))
        self.assertTrue(quote_supports_value("monthly_fee", 0, CHECKING_CONTEXT))

    def test_saved_ordinary_day_to_day_unlimited(self):
        quote = "FREE , unlimited day-to-day transactions 1"
        self.assertTrue(_ai_verified_value_is_supported_by_quote(
            field_name="unlimited_transactions_flag", value=True, evidence_quote=quote))
        self.assertTrue(quote_supports_value("unlimited_transactions_flag", True, CHECKING_CONTEXT))

    def test_actual_conditions_survive_negated_minimum_balance(self):
        for quote in [
            "No monthly fee; minimum balance required",
            "No monthly fee does not mean no minimum balance required",
            "No monthly fee; not no minimum balance required",
            "No monthly fee with a minimum balance of $100",
            "No monthly fee; no minimum balance required if you qualify",
            "No monthly fee; no minimum balance required for the first year",
            "No monthly fee; no minimum balance required until graduation",
            "No monthly fee when you maintain a balance; no minimum balance required",
            "No monthly fee for eligible customers; no minimum balance required",
        ]:
            with self.subTest(quote=quote):
                self.assertFalse(quote_supports_value("monthly_fee", 0, quote))

    def test_day_to_day_still_rejects_channels_counts_and_conditions(self):
        for quote in [
            "Unlimited day-to-day transactions only for public transit",
            "Unlimited day-to-day transactions at ATMs",
            "Unlimited free day-to-day transactions only at ATMs",
            "Unlimited day-to-day transactions 1 only for public transit",
            "Unlimited day-to-day transactions when you qualify",
            "Not unlimited day-to-day transactions",
            "12 monthly transactions. Unlimited day-to-day transactions",
            "Unlimited Interac e-Transfers",
        ]:
            with self.subTest(quote=quote):
                self.assertFalse(quote_supports_value("unlimited_transactions_flag", True, quote))
        self.assertFalse(quote_supports_value("unlimited_transactions_flag", False, "Unlimited day-to-day transactions"))

    def test_savings_still_requires_grounded_rate(self):
        row, meta, evidence = candidate_fixture()
        del row["field_mapping_metadata"]["standard_rate"]["official_grounding_contract_version"]
        row["field_mapping_metadata"]["monthly_fee"]["official_evidence_quote"] = "There are no monthly fees"
        next(e for e in evidence if e["evidence_chunk_id"] == "monthly_fee")["evidence_excerpt"] = SAVINGS_CONTEXT
        result, receipt = sanitize_candidate(row, source_metadata=meta, evidence=evidence)
        self.assertFalse(receipt["accepted"])
        self.assertIn("standard_rate", receipt["missing_fields"])
        self.assertEqual(result["candidate_payload"]["monthly_fee"], 0)

    def test_checking_receipt_still_needs_both_official_fields(self):
        row, meta, evidence = candidate_fixture()
        row["product_type"] = "chequing"
        row["candidate_payload"]["unlimited_transactions_flag"] = True
        row["field_mapping_metadata"]["unlimited_transactions_flag"] = dict(
            row["field_mapping_metadata"]["monthly_fee"], normalized_value=True,
            evidence_chunk_id="ordinary", official_evidence_quote="FREE , unlimited day-to-day transactions 1")
        evidence.append(dict(evidence[0], evidence_chunk_id="ordinary", evidence_excerpt=CHECKING_CONTEXT))
        row["field_mapping_metadata"]["monthly_fee"]["official_evidence_quote"] = "No monthly fee; No minimum balance required"
        next(e for e in evidence if e["evidence_chunk_id"] == "monthly_fee")["evidence_excerpt"] = CHECKING_CONTEXT
        result, receipt = sanitize_candidate(row, source_metadata=meta, evidence=evidence)
        self.assertTrue(receipt["accepted"])
        del row["field_mapping_metadata"]["unlimited_transactions_flag"]["official_grounding_contract_version"]
        _, missing = sanitize_candidate(row, source_metadata=meta, evidence=evidence)
        self.assertFalse(missing["accepted"])
        self.assertIn("unlimited_transactions_flag", missing["missing_fields"])

    def test_short_rate_quote_does_not_gain_invented_context(self):
        self.assertFalse(_exact_quote_is_grounded(quote="Annual interest rate 1.05%", excerpt="1.05%*\nGet Started"))

if __name__ == "__main__":
    unittest.main()
