import unittest
from worker.pipeline.fpds_collection_accuracy import quote_supports_value
from worker.pipeline.tests.test_card_rate_context import CARD_CONTEXT

class CardLabelledRateTests(unittest.TestCase):
    def test_distinct_current_labels(self):
        context = CARD_CONTEXT.replace("9.99% on purchases", "21.99% on purchases").replace("9.99% on cash advances", "22.99% on cash advances")
        for source in [context, context.replace("\nThe current", " The current"), context.replace("the Account are", "this Account are")]:
            self.assertTrue(quote_supports_value("purchase_interest_rate", 21.99, source))
            self.assertTrue(quote_supports_value("cash_advance_rate", 22.99, source))
            self.assertTrue(quote_supports_value("balance_transfer_rate", 22.99, source))
            self.assertFalse(quote_supports_value("purchase_interest_rate", 22.99, source))

    def test_ambiguous_or_qualified_labels_fail(self):
        sentence = "The current preferred annual interest rates for the Account are: 21.99% on purchases and 22.99% on cash advances (including balance transfers and cash-like transactions)."
        bad = [sentence + " Another purchase rate is 21.99%.", sentence + " A penalty rate applies.", sentence + " Provided payments are current.", sentence.replace("21.99%", "from 21.99%"), sentence.replace("21.99%", "21.99% to 24.99%"), sentence.replace("purchases", "purchases for eligible customers"), sentence.replace("preferred", "introductory"), sentence.replace("annual", "monthly"), sentence.replace("cash advances", "purchases"), sentence + sentence]
        for source in bad:
            with self.subTest(source=source):
                self.assertFalse(quote_supports_value("purchase_interest_rate", 21.99, source))
        self.assertFalse(quote_supports_value("standard_rate", 21.99, sentence))
        self.assertFalse(quote_supports_value("purchase_interest_rate", 100, sentence.replace("21.99%", "100%")))

    def test_normalizer_uses_same_full_context_proof(self):
        from worker.pipeline.fpds_normalization.service import _has_exact_official_card_purchase_rate
        sentence = "The current preferred annual interest rates for the Account are: 21.99% on purchases and 22.99% on cash advances (including balance transfers and cash-like transactions)."
        metadata = {"official_grounding_contract_version": "collection-official-grounding-v2", "official_verification_status": "match", "official_web_sources": [{"url": "https://bank.example/card"}], "official_evidence_quote": sentence}
        self.assertTrue(_has_exact_official_card_purchase_rate(field_name="purchase_interest_rate", value=21.99, context=sentence, official_grounding_metadata=metadata))
        self.assertFalse(_has_exact_official_card_purchase_rate(field_name="purchase_interest_rate", value=22.99, context=sentence, official_grounding_metadata=metadata))
