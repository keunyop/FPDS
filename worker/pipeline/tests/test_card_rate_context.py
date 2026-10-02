import unittest
from worker.pipeline.fpds_collection_accuracy import quote_supports_value, sanitize_candidate, acceptance_receipt_valid
from worker.pipeline.tests.test_collection_accuracy import candidate_fixture

CARD_CONTEXT = 'or secondary cardholders of a Scotiabank personal credit card in the past 2 years, including those that switch from an existing Scotiabank personal credit card, as well as employees of Scotiabank, are not eligible for the Offer. Subject to the above exclusions, Scotiabank small business credit cardholders are also eligible for the Offer.\nRates and Fees: The current annual fee is $399 for the primary card and $99 for each additional card (including those issued to co-borrowers and supplementary cardholders).\nThe current preferred annual interest rates for the Account are: 9.99% on purchases and 9.99% on cash advances (including balance transfers and cash-like transactions). All rates, fees, features and benefits are outlined in the Application Disclosure Statement and are subject to change.'
RATE_SENTENCE = "The current preferred annual interest rates for the Account are: 9.99% on purchases and 9.99% on cash advances (including balance transfers and cash-like transactions)."

class CardRateContextTests(unittest.TestCase):
    def test_explicit_current_rates_survive_unrelated_switch_exclusion(self):
        for context in [CARD_CONTEXT, CARD_CONTEXT.replace("\n", "\r\n")]:
            self.assertTrue(quote_supports_value("purchase_interest_rate", 9.99, context))
            self.assertTrue(quote_supports_value("cash_advance_rate", 9.99, context))
            self.assertTrue(quote_supports_value("balance_transfer_rate", 9.99, context))
        self.assertTrue(quote_supports_value("purchase_interest_rate", 9.99, RATE_SENTENCE))
        self.assertFalse(quote_supports_value("purchase_interest_rate", 8.99, CARD_CONTEXT))

    def test_rate_conditions_and_ambiguous_boundaries_still_fail(self):
        variants = [
            CARD_CONTEXT.replace("9.99% on purchases", "from 9.99% on purchases"),
            CARD_CONTEXT.replace("9.99% on purchases", "9.99% to 12.99% on purchases"),
            CARD_CONTEXT.replace("9.99% on purchases", "9.99% on purchases if you switch cards"),
            CARD_CONTEXT.replace("9.99% on purchases", "9.99% on purchases for the introductory period"),
            CARD_CONTEXT.replace("9.99% on purchases", "9.99% on purchases when you qualify"),
            CARD_CONTEXT.replace("9.99% on purchases", "12.99% on purchases"),
            CARD_CONTEXT.replace("9.99% on purchases", "9.99% on purchases provided you pay the balance"),
            CARD_CONTEXT.replace("9.99% on purchases", "9.99% on purchases only for new customers"),
            CARD_CONTEXT + "\nA penalty purchase rate of 9.99% applies after a missed payment.",

            CARD_CONTEXT.replace("Rates and Fees:", "Offer rates:"),
            CARD_CONTEXT.replace("The current preferred annual", "The introductory annual"),
            CARD_CONTEXT.replace("switch from an existing", "rates from an existing"),
            CARD_CONTEXT.replace("switch from an existing", "switch from a 9.99% existing"),
            CARD_CONTEXT.replace("switch from an existing", "from the second year with an existing"),
            "Purchase annual interest rate from just 9.99%.",
            "From the second year, purchase annual interest rate 9.99%.",
        ]
        for context in variants:
            with self.subTest(context=context):
                self.assertFalse(quote_supports_value("purchase_interest_rate", 9.99, context))

    def test_full_evidence_receipt_and_annual_basis(self):
        row, meta, _ = candidate_fixture()
        url = "https://bank.example/platinum"
        payload = {"product_name": "Example Platinum", "annual_fee": 399, "purchase_interest_rate": 9.99}
        quotes = {"product_name": "Example Platinum in CAD", "annual_fee": "The current annual fee is $399 for the primary card", "purchase_interest_rate": RATE_SENTENCE}
        row.update(product_type="credit-card", product_name=payload["product_name"], candidate_payload=payload)
        row["field_mapping_metadata"] = {name: {"normalized_value": value, "evidence_chunk_id": name,
            "official_grounding_contract_version": "collection-official-grounding-v2", "official_verification_status": "match",
            "official_evidence_quote": quotes[name], "official_web_sources": [{"url": url}]}
            for name, value in payload.items()}
        meta.update(normalized_source_url=url, expected_fields=list(payload))
        evidence = [{"evidence_chunk_id": name, "source_url": url, "evidence_excerpt": quotes[name] if name == "product_name" else CARD_CONTEXT} for name in payload]
        cleaned, receipt = sanitize_candidate(row, source_metadata=meta, evidence=evidence)
        self.assertTrue(receipt["accepted"], receipt)
        self.assertTrue(acceptance_receipt_valid(cleaned))
        from copy import deepcopy
        for annual in [True, False]:
            context = CARD_CONTEXT.replace("9.99% on purchases", "from 9.99% on purchases") if annual else CARD_CONTEXT.replace("annual", "monthly")
            changed = [dict(e, evidence_excerpt=context) if e["evidence_chunk_id"] == "purchase_interest_rate" else e for e in evidence]
            proposal = deepcopy(row)
            if not annual:
                proposal["field_mapping_metadata"]["purchase_interest_rate"]["official_evidence_quote"] = RATE_SENTENCE.replace("annual", "monthly")
            _, receipt = sanitize_candidate(proposal, source_metadata=meta, evidence=changed)
            self.assertFalse(receipt["accepted"], receipt)
            if not annual:
                self.assertEqual(receipt["omitted_fields"]["purchase_interest_rate"], "annual_rate_basis_unproven")

    def test_dynamic_card_prompt_matches_gate_without_extra_other_type_text(self):
        from dataclasses import replace
        from unittest.mock import patch
        from worker.pipeline.tests.test_normalization import _build_input
        from worker.pipeline.fpds_normalization.service import _normalize_dynamic_fields_with_ai
        from worker.pipeline.fpds_comparison_instructions import CARD_RATE_CONTEXT_INSTRUCTIONS
        response = {"summary": "", "product_name": "", "subtype_code": "other", "source_subtype_label": "", "normalized_fields": []}
        for fields, applies in [(["purchase_interest_rate", "annual_fee"], True), (["standard_rate", "monthly_fee"], False)]:
            item = replace(_build_input(), source_metadata={"expected_fields": fields})
            with patch("worker.pipeline.fpds_normalization.service.llm_provider_configured", return_value=True), patch("worker.pipeline.fpds_normalization.service.invoke_openai_json_schema", return_value=(response, {})) as invoke:
                _normalize_dynamic_fields_with_ai(item=item, extracted_by_field={}, candidate_payload={})
            self.assertEqual(CARD_RATE_CONTEXT_INSTRUCTIONS in invoke.call_args.kwargs["instructions"], applies)
