import unittest
from worker.pipeline.fpds_collection_accuracy import quote_supports_value
from worker.pipeline.fpds_normalization.service import _has_exact_official_card_purchase_rate

RATE = "The current preferred annual interest rates for the Account are: 20.99% on purchases and 22.99% on Cash Advances."
CONTEXT = "By accepting this Offer you confirm you meet all Offer eligibility requirements. We reserve the right to revoke this Offer at any time if we determine you do not meet the Offer eligibility requirements, including after you have accepted the Offer or been approved for the Account.\nRates and Fees: The current annual fee is $49 for the primary card and $15 for each additional card. " + RATE + " All rates, fees, features and benefits are subject to change."

class CardOfferRevocationTests(unittest.TestCase):
    def test_separate_offer_revocation_preserves_current_labelled_rates(self):
        for context in [CONTEXT, CONTEXT.replace("\n", "\r\n")]:
            self.assertTrue(quote_supports_value("purchase_interest_rate", 20.99, context))
            self.assertTrue(quote_supports_value("cash_advance_rate", 22.99, context))
            self.assertFalse(quote_supports_value("purchase_interest_rate", 22.99, context))
            self.assertFalse(quote_supports_value("balance_transfer_rate", 22.99, context))

    def test_conditions_conflicts_and_unresolved_boundaries_remain_excluded(self):
        bad = [
            CONTEXT.replace("Rates and Fees:", "Offer rates:"),
            CONTEXT.replace("\nRates and Fees:", " Rates and Fees:"),
            CONTEXT.replace("revoke this Offer", "change this rate"),
            CONTEXT.replace("if we determine you do not meet the Offer eligibility requirements", "if you pay every balance"),
            CONTEXT.replace("current preferred annual", "introductory annual"),
            CONTEXT.replace("current preferred annual", "current preferred monthly"),
            CONTEXT.replace("20.99% on purchases", "from 20.99% on purchases"),
            CONTEXT.replace("20.99% on purchases", "20.99% on purchases if payments are current"),
            CONTEXT + " If payments are late the rate changes.",
            CONTEXT + " A penalty rate applies.",
            CONTEXT + " Another purchase rate is 20.99%.",
            "If you qualify for the preferred rate. " + CONTEXT,
            CONTEXT.replace(RATE, RATE + " " + RATE),
            CONTEXT.replace("Cash Advances", "purchases"),
        ]
        for context in bad:
            with self.subTest(context=context):
                self.assertFalse(quote_supports_value("purchase_interest_rate", 20.99, context))

    def test_normalization_uses_unchanged_full_context(self):
        metadata = {"official_grounding_contract_version": "collection-official-grounding-v2", "official_verification_status": "match", "official_web_sources": [{"url": "https://bank.example/card"}], "official_evidence_quote": RATE}
        self.assertTrue(_has_exact_official_card_purchase_rate(field_name="purchase_interest_rate", value=20.99, context=CONTEXT, official_grounding_metadata=metadata))
        self.assertFalse(_has_exact_official_card_purchase_rate(field_name="purchase_interest_rate", value=20.99, context=CONTEXT + " If payments are late the rate changes.", official_grounding_metadata=metadata))


class CardNumberedFeeNoteTests(unittest.TestCase):
    def test_bound_card_cheque_label_and_separate_transaction_note(self):
        context = GOLD_CONTEXT
        self.assertTrue(quote_supports_value("purchase_interest_rate", 19.99, context))
        self.assertTrue(quote_supports_value("cash_advance_rate", 22.99, context))
        self.assertTrue(quote_supports_value("balance_transfer_rate", 22.99, context))
        for bad in [
            context.replace("5\nTransaction fees may apply when", "Transaction fees may apply when"),
            context.replace("Transaction fees may apply when", "Interest rates may apply when"),
            context.replace("The current preferred annual", "\n5\nTransaction fees may apply when\nThe current preferred annual"),
            context.replace("19.99% on purchases", "19.99% on purchases when payments are current"),
            context.replace("and cash-like transactions", "for eligible customers"),
            context + " A penalty rate of 19.99% applies.",
            context.replace("3\nRates and Fees:", "3\nOffer rates:"),
        ]:
            with self.subTest(context=bad):
                self.assertFalse(quote_supports_value("purchase_interest_rate", 19.99, bad))

GOLD_CONTEXT = 'oducts or services offered on or through that platform or any features and benefits offered through or on such platform including the ability to make \xa0condominium, housing, rental or leasing recurring bill payments. Other terms and conditions may apply as set by Casa for the Casa platform or such payments.\n3\nRates and Fees:\xa0The current annual fee is $110 for the primary card and $30 for each additional card. The current preferred annual interest rates for the Account are: 19.99% on purchases and 22.99% on cash advances (including balance transfers, Scotia® Credit Card Cheques and cash-like transactions).\nAll rates, fees, features and benefits are subject to change.\n4\nPoints are not awarded for cash advances, Scotia ® Credit Card cheques, credit vouchers, returns, payments, annual membership or card fees, interest charges or service transaction charges.\n5\nTransaction fees may apply when'
