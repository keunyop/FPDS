from __future__ import annotations

import json
from pathlib import Path
from shutil import rmtree
import unittest
from unittest.mock import patch

from worker.pipeline.fpds_evidence_retrieval.models import EvidenceChunkCandidate, EvidenceMatch
from worker.pipeline.fpds_extraction.__main__ import _context_with_registry_metadata
from worker.pipeline.fpds_field_contract import field_contract
from worker.pipeline.fpds_extraction.models import ExtractedFieldCandidate, ExtractionDocumentContext, ExtractionInput
from worker.pipeline.fpds_extraction.persistence import ExtractionDatabaseConfig, PsqlExtractionRepository
from worker.pipeline.fpds_extraction.service import (
    _DEFAULT_EXTRACTABLE_FIELDS,
    ExtractionService,
    _ai_candidate_value_is_contract_safe,
    _append_included_transactions_fallback,
    _append_fee_waiver_fallback,
    _append_labeled_numeric_extension_fallback,
    _append_minimum_deposit_fallback,
    _append_monthly_fee_fallback,
    _append_unlimited_transactions_fallback,
    _append_rate_fallback_fields,
    _append_promotional_period_fallback,
    _clean_title_candidate,
    _extract_candidate_value,
    _extract_application_method,
    _extract_deposit_insurance,
    _extract_description,
    _extract_document_title,
    _extract_eligibility_text,
    _extract_fee_waiver_condition,
    _field_evidence_semantic_score,
    _extract_from_matches,
    _extract_interest_calculation_method,
    _extract_interest_rate_summary,
    _extract_included_transactions,
    _extract_notes_text,
    _extract_promotional_period_text,
    _extract_tax_benefits,
    _extract_transaction_fee,
    _extract_withdrawal_limit_text,
    _exact_quote_is_grounded,
    _filter_official_web_sources,
    _infer_currency,
    _looks_like_navigation_description,
    _looks_like_non_product_summary,
    _resolve_field_names,
    _uses_dynamic_product_type,
    _validated_field_sources,
)
from worker.pipeline.fpds_extraction.storage import ExtractionStorageConfig, build_object_store


class ExtractionServiceTests(unittest.TestCase):
    def test_official_grounding_requires_exact_snapshot_quote_and_consulted_allowlisted_source(self) -> None:
        self.assertTrue(_ai_candidate_value_is_contract_safe(field_name="standard_rate", value="3.25"))
        self.assertFalse(_ai_candidate_value_is_contract_safe(field_name="standard_rate", value="30.00"))
        self.assertTrue(_ai_candidate_value_is_contract_safe(field_name="mortgage_rate", value="4.25"))
        self.assertFalse(_ai_candidate_value_is_contract_safe(field_name="mortgage_rate", value="100.00"))
        self.assertFalse(_ai_candidate_value_is_contract_safe(field_name="monthly_fee", value="501.00"))
        self.assertTrue(
            _exact_quote_is_grounded(
                quote="Minimum deposit: $500.",
                excerpt="Open an account. Minimum deposit: $500.",
            )
        )
        self.assertFalse(
            _exact_quote_is_grounded(
                quote="Minimum deposit: $5,000.",
                excerpt="Open an account. Minimum deposit: $500.",
            )
        )
        self.assertFalse(
            _exact_quote_is_grounded(
                quote="$500",
                excerpt="Open an account. Minimum deposit: $500.",
            )
        )
        provider_sources = _filter_official_web_sources(
            [
                {"url": "https://www.bank.example/product", "title": "Product"},
                {"url": "https://untrusted.example/product", "title": "Untrusted"},
            ],
            allowed_domains=["bank.example"],
        )
        self.assertEqual(provider_sources, [{"url": "https://www.bank.example/product", "title": "Product"}])
        validated = _validated_field_sources(
            [
                {"url": "https://www.bank.example/product", "title": "Product"},
                {"url": "https://bank.example/not-consulted", "title": "Not consulted"},
            ],
            provider_source_by_url={item["url"]: item for item in provider_sources},
            allowed_domains=["bank.example"],
        )
        self.assertEqual(validated, provider_sources)

    def test_promotional_period_fallback_recovers_duration_from_any_product_chunk(self) -> None:
        context = ExtractionDocumentContext(
            source_id="BANK-SAV-001",
            parsed_document_id="parsed-001",
            source_document_id="src-001",
            snapshot_id="snap-001",
            bank_code="BANK",
            country_code="CA",
            source_type="html",
            source_language="en",
            source_metadata={"product_type": "savings", "product_name": "High Interest Savings Account"},
        )
        candidate = EvidenceChunkCandidate(
            evidence_chunk_id="chunk-offer",
            parsed_document_id="parsed-001",
            chunk_index=3,
            anchor_type="section",
            anchor_value="welcome-offer",
            page_no=None,
            source_language="en",
            evidence_excerpt=(
                "High Interest Savings Account. Just open a savings account and get this special "
                "interest rate for 5 months."
            ),
            retrieval_metadata={},
            source_document_id="src-001",
            source_snapshot_id="snap-001",
            bank_code="BANK",
            country_code="CA",
            source_type="html",
        )
        fields = [
            ExtractedFieldCandidate(
                field_name="promotional_rate",
                candidate_value="4.60",
                value_type="decimal",
                confidence=0.9,
                extraction_method="heuristic",
                source_document_id="src-001",
                source_snapshot_id="snap-001",
                evidence_chunk_id="chunk-offer",
                evidence_text_excerpt=candidate.evidence_excerpt,
                anchor_type="section",
                anchor_value="welcome-offer",
                page_no=None,
                chunk_index=3,
                field_metadata={},
            )
        ]

        _append_promotional_period_fallback(
            context=context,
            candidates=[candidate],
            requested_fields={"promotional_rate", "promotional_period_text"},
            extracted_fields=fields,
        )

        period = next(field for field in fields if field.field_name == "promotional_period_text")
        self.assertEqual(period.candidate_value, "5 months")

    def test_wrapped_product_description_and_ongoing_rate_are_recovered_beside_offer(self) -> None:
        context = ExtractionDocumentContext(
            source_id="BANK-SAV-001",
            parsed_document_id="parsed-001",
            source_document_id="src-001",
            snapshot_id="snap-001",
            bank_code="BANK",
            country_code="CA",
            source_type="html",
            source_language="en",
            source_metadata={"product_type": "savings", "product_name": "USD Savings Account"},
        )
        excerpt = (
            "USD Savings Account\n"
            "With this USD Savings Account, you can save your US\n"
            "funds with a great interest rate and no monthly fees.\n"
            "0.10%†\nInterest rate\n$0\nMonthly fee\nSpecial Offer\n"
            "Earn 4.50% for 5 months"
        )
        candidate = EvidenceChunkCandidate(
            evidence_chunk_id="chunk-hero",
            parsed_document_id="parsed-001",
            chunk_index=0,
            anchor_type="page",
            anchor_value="page-1",
            page_no=1,
            source_language="en",
            evidence_excerpt=excerpt,
            retrieval_metadata={},
            source_document_id="src-001",
            source_snapshot_id="snap-001",
            bank_code="BANK",
            country_code="CA",
            source_type="html",
        )
        fields = [
            ExtractedFieldCandidate(
                field_name="promotional_rate",
                candidate_value="4.50",
                value_type="decimal",
                confidence=0.9,
                extraction_method="heuristic",
                source_document_id="src-001",
                source_snapshot_id="snap-001",
                evidence_chunk_id="chunk-hero",
                evidence_text_excerpt=excerpt,
                anchor_type="page",
                anchor_value="page-1",
                page_no=1,
                chunk_index=0,
                field_metadata={},
            )
        ]

        _append_rate_fallback_fields(
            context=context,
            candidates=[candidate],
            requested_fields={"standard_rate", "promotional_rate", "public_display_rate"},
            extracted_fields=fields,
        )

        self.assertEqual(_extract_description(context=context, candidates=[candidate]), (
            "With this USD Savings Account, you can save your US funds with a great interest rate and no monthly fees."
        ))
        standard = next(field for field in fields if field.field_name == "standard_rate")
        self.assertEqual(standard.candidate_value, "0.10")

    def test_description_prefers_product_summary_over_recommender_and_cross_sell_copy(self) -> None:
        context = ExtractionDocumentContext(
            source_id="BANK-CHQ-001",
            parsed_document_id="parsed-001",
            source_document_id="src-001",
            snapshot_id="snap-001",
            bank_code="BANK",
            country_code="CA",
            source_type="html",
            source_language="en",
            source_metadata={"product_type": "chequing", "product_name": "Performance Chequing Account"},
        )
        excerpts = (
            "Still not sure?\nLet us help you decide.\nAnswer a few quick questions and we'll recommend the best chequing account for you.",
            "Get a Canadian and U.S. dollar Savings Account to use at no additional cost.\nUp to 25 transactions per month.",
            "Features Details Monthly fee $0 Interest rate 0.550% Monthly savings requirement $200 Number of transactions per month one.",
            "High interest savings accounts explained in 2025. We take a deeper look at the benefits and limitations of this popular savings account.",
            "What is a Performance Chequing Account?\nA Performance Chequing Account offers unlimited everyday banking transactions and convenient Interac e-Transfers.",
        )
        candidates = [
            EvidenceChunkCandidate(
                evidence_chunk_id=f"chunk-{index}",
                parsed_document_id="parsed-001",
                chunk_index=index,
                anchor_type="section",
                anchor_value="benefits",
                page_no=None,
                source_language="en",
                evidence_excerpt=excerpt,
                retrieval_metadata={},
                source_document_id="src-001",
                source_snapshot_id="snap-001",
                bank_code="BANK",
                country_code="CA",
                source_type="html",
            )
            for index, excerpt in enumerate(excerpts)
        ]

        self.assertEqual(
            _extract_description(context=context, candidates=candidates),
            "A Performance Chequing Account offers unlimited everyday banking transactions and convenient Interac e-Transfers.",
        )

    def test_reward_earning_example_is_not_product_eligibility(self) -> None:
        self.assertIsNone(
            _extract_eligibility_text(
                "For example, this account lets you earn 2x the Points for every $2 in eligible grocery, "
                "wholesale club, EV charging and gas purchases."
            )
        )

    def test_explicit_no_monthly_fee_outranks_nearby_cash_offer(self) -> None:
        context = ExtractionDocumentContext(
            source_id="BANK-CHQ-YOUTH",
            parsed_document_id="parsed-001",
            source_document_id="src-001",
            snapshot_id="snap-001",
            bank_code="BANK",
            country_code="CA",
            source_type="html",
            source_language="en",
            source_metadata={
                "product_type": "chequing",
                "discovery_metadata": {
                    "page_title": "A Bank Account for Youth Under 25",
                    "primary_heading": "Smart Start",
                },
            },
        )
        excerpt = (
            "Smart Start Under 25? Enjoy no-monthly fee everyday banking. "
            "Get $175 Cash and a free membership. Fees and details."
        )

        fee, value_type, *_ = _extract_candidate_value(
            context=context,
            field_name="monthly_fee",
            excerpt=excerpt,
            anchor_value="overview",
        )

        self.assertEqual(fee, "0.00")
        self.assertEqual(value_type, "decimal")
        self.assertIsNone(
            _extract_eligibility_text(
                "Start with a Smart Account, then apply and get approved for any eligible credit card."
            )
        )

    def test_temporal_no_fee_offer_becomes_a_bounded_waiver_condition(self) -> None:
        context = ExtractionDocumentContext(
            source_id="AUTO-BANK-CHQ-NEWCOMER",
            parsed_document_id="parsed-newcomer",
            source_document_id="src-newcomer",
            snapshot_id="snap-newcomer",
            bank_code="BANK",
            country_code="CA",
            source_type="html",
            source_language="en",
            source_metadata={"product_type": "chequing", "product_name": "Smart Account for Newcomers"},
        )

        self.assertEqual(
            _extract_fee_waiver_condition(context=context, text="Pay no monthly fee for 2 years."),
            "Monthly fee is waived for 2 years.",
        )
        self.assertEqual(
            _extract_fee_waiver_condition(context=context, text="$0 monthly fee for 24 months."),
            "Monthly fee is waived for 24 months.",
        )
        self.assertEqual(
            _extract_fee_waiver_condition(context=context, text="Enjoy no monthly fee until age 25."),
            "Monthly fee is waived until age 25.",
        )

    def test_savings_transaction_terms_are_reduced_to_typed_fee_and_concise_limit(self) -> None:
        context = ExtractionDocumentContext(
            source_id="BANK-SAV-001",
            parsed_document_id="parsed-001",
            source_document_id="src-001",
            snapshot_id="snap-001",
            bank_code="BANK",
            country_code="CA",
            source_type="html",
            source_language="en",
            source_metadata={"product_type": "savings", "product_name": "Savings Builder Account"},
        )
        text = (
            "One eligible debit transaction per month at no cost. "
            "Any additional transactions, including withdrawals or transfers out, are $5 per transaction."
        )

        self.assertEqual(_extract_withdrawal_limit_text(context=context, text=text), (
            "One eligible debit transaction per month at no cost."
        ))
        self.assertEqual(_extract_transaction_fee(text=text), "5.00")
        self.assertEqual(_extract_transaction_fee(text=text, require_additional=True), "5.00")

    def test_deposit_insurance_extracts_membership_sentence_from_footer_navigation(self) -> None:
        value = _extract_deposit_insurance(
            "Resources Help centre Contact us ABM locator Rates Careers Community Get our app "
            "Example Bank is a wholly-owned subsidiary and a CDIC member in its own right. Privacy Legal"
        )

        self.assertEqual(
            value,
            "Example Bank is a wholly-owned subsidiary and a CDIC member in its own right.",
        )

        full_name_value = _extract_deposit_insurance(
            "Get started Meet with us Call us 1-800-000-0000 Find a banking centre "
            "Example Bank is a member of Canada Deposit Insurance Corporation (CDIC). Terms and conditions"
        )
        self.assertEqual(
            full_name_value,
            "Example Bank is a member of Canada Deposit Insurance Corporation (CDIC).",
        )

        navigation_value = _extract_deposit_insurance(
            "Legal We are members of the Canada Deposit Insurance Corporation (CDIC) "
            "Explore our services Bank Accounts Credit Cards Mortgages Loans Investments"
        )
        self.assertEqual(
            navigation_value,
            "We are members of the Canada Deposit Insurance Corporation (CDIC)",
        )
        self.assertEqual(
            _extract_deposit_insurance(
                "BOOK AN APPOINTMENT We are members of the Canada Deposit Insurance Corporation (CDIC) "
                "Explore our services Bank Accounts Credit Cards"
            ),
            "We are members of the Canada Deposit Insurance Corporation (CDIC)",
        )

    def test_extracts_dynamic_gic_rate_mechanism_without_inventing_numeric_rate(self) -> None:
        value = _extract_interest_rate_summary(
            "The one-year GIC earns a variable interest rate linked to changes in RBC Prime. "
            "The principal remains guaranteed."
        )

        self.assertEqual(
            value,
            "The one-year GIC earns a variable interest rate linked to changes in RBC Prime.",
        )

    def test_savings_defaults_include_transaction_terms(self) -> None:
        context = ExtractionDocumentContext(
            source_id="BANK-SAV-001",
            parsed_document_id="parsed-001",
            source_document_id="src-001",
            snapshot_id="snap-001",
            bank_code="BANK",
            country_code="CA",
            source_type="html",
            source_language="en",
            source_metadata={"product_type": "savings"},
        )

        fields = set(
            _resolve_field_names(
                context=context,
                override_field_names=None,
                default_fields=_DEFAULT_EXTRACTABLE_FIELDS,
            )
        )

        self.assertTrue(
            {"included_transactions", "transaction_fee", "additional_transaction_fee"}.issubset(fields)
        )

    def test_boosted_rate_eligibility_and_balance_tiers_are_condensed_from_full_rules(self) -> None:
        eligibility = _extract_eligibility_text(
            "Boosted Rate Eligibility Maintain an eligible Example Unlimited Chequing Account. "
            "Complete at least 2 out of the 3 Qualifying Monthly Transactions each month: "
            "Direct Deposit, Pre-Authorized Debit, Online Bill Payment."
        )
        tiers, *_ = _extract_candidate_value(
            context=ExtractionDocumentContext(
                source_id="BANK-SAV-001",
                parsed_document_id="parsed-001",
                source_document_id="src-001",
                snapshot_id="snap-001",
                bank_code="BANK",
                country_code="CA",
                source_type="html",
                source_language="en",
                source_metadata={"product_type": "savings"},
            ),
            field_name="tier_definition_text",
            excerpt=(
                "Daily Closing Balance Tiers Boosted Rate Standard Posted Rate "
                "$0 to $4,999.99 0.00% 0.00% $5,000 to $9,999.99 0.50% 0.00% "
                "$10,000 and over 1.00% 0.50% Additional Terms"
            ),
            anchor_value="rate chart",
        )

        self.assertEqual(
            eligibility,
            "Maintain an eligible Example Unlimited Chequing Account and complete at least 2 of 3 qualifying monthly transactions.",
        )
        self.assertIn("$5,000 to $9,999.99 0.50% 0.00%", tiers)

    def test_explicit_multistep_eligibility_outranks_marketing_summary(self) -> None:
        marketing = (
            "You could earn the Boosted Rate when you start with an eligible chequing account, "
            "helping you earn more as you save."
        )
        explicit = (
            "Boosted Rate Eligibility. Here's how to qualify: Maintain an eligible chequing account. "
            "Complete at least 2 out of the 3 qualifying monthly transactions."
        )
        self.assertGreater(
            _field_evidence_semantic_score(
                field_name="eligibility_text",
                candidate_value=_extract_eligibility_text(explicit),
                excerpt=explicit,
            ),
            _field_evidence_semantic_score(
                field_name="eligibility_text",
                candidate_value=_extract_eligibility_text(marketing),
                excerpt=marketing,
            ),
        )

    def test_flattened_account_fee_rows_extract_transaction_fees(self) -> None:
        self.assertEqual(
            _extract_transaction_fee(
                text="Account Fees Transaction Fee 3 $5.00 each Free Online Transfers Unlimited"
            ),
            "5.00",
        )

    def test_non_balance_eligibility_fee_waiver_is_preserved(self) -> None:
        context = ExtractionDocumentContext(
            source_id="AUTO-BANK-CHE-minimum",
            parsed_document_id="parsed-chequing",
            source_document_id="source-chequing",
            snapshot_id="snapshot-chequing",
            bank_code="BANK",
            country_code="CA",
            source_type="html",
            source_language="en",
            source_metadata={"product_type": "chequing"},
        )
        value = _extract_fee_waiver_condition(
            context=context,
            text=(
                "Monthly fee $3.95 ($0 if you are receiving the Guaranteed Income Supplement "
                "or are a beneficiary of a Registered Disability Savings Plan or are Indigenous Peoples from Canada)."
            ),
        )

        self.assertIn("Monthly fee 3.95 is waived to 0.00", value or "")
        self.assertIn("Guaranteed Income Supplement", value or "")
        self.assertEqual(
            _extract_transaction_fee(
                text="Transactions included per month 2 1 Additional Transactions 2 $3.00 each",
                require_additional=True,
            ),
            "3.00",
        )

    def test_prime_margin_is_preserved_as_formula_not_misreported_as_total_rate(self) -> None:
        context = ExtractionDocumentContext(
            source_id="AUTO-BANK-LOC-001",
            parsed_document_id="parsed-loc",
            source_document_id="src-loc",
            snapshot_id="snap-loc",
            bank_code="BANK",
            country_code="CA",
            source_type="html",
            source_language="en",
            source_metadata={"product_type": "line-of-credit"},
        )
        excerpt = "A lower interest rate of Prime + 1%. Payments can be as low as interest only."

        rate, *_ = _extract_candidate_value(
            context=context,
            field_name="interest_rate",
            excerpt=excerpt,
            anchor_value="rates",
        )
        summary = _extract_interest_rate_summary(excerpt)

        self.assertIsNone(rate)
        self.assertEqual(summary, "A lower interest rate of Prime + 1%.")

    def test_balance_transfer_rate_can_precede_its_label(self) -> None:
        context = ExtractionDocumentContext(
            source_id="AUTO-BANK-CC-001",
            parsed_document_id="parsed-card",
            source_document_id="src-card",
            snapshot_id="snap-card",
            bank_code="BANK",
            country_code="CA",
            source_type="html",
            source_language="en",
            source_metadata={"product_type": "credit-card"},
        )

        rate, *_ = _extract_candidate_value(
            context=context,
            field_name="balance_transfer_rate",
            excerpt="Get a 0.99% introductory interest rate on balance transfers for the first 9 months.",
            anchor_value="special-offer",
        )

        self.assertEqual(rate, "0.99")

    def test_profile_specific_rate_and_fee_fields_use_numeric_contracts(self) -> None:
        self.assertEqual(field_contract("regular_interest_rate").value_type, "decimal")
        self.assertEqual(field_contract("regular_interest_rate").unit, "percentage_points")
        self.assertEqual(field_contract("transaction_fee").value_type, "decimal")
        self.assertEqual(field_contract("transaction_fee").unit, "currency_amount")
        self.assertEqual(field_contract("rate_type").value_type, "string")
        self.assertEqual(field_contract("fees_text").value_type, "string")

    def test_registered_profile_extensions_reach_extraction_field_resolution(self) -> None:
        context = ExtractionDocumentContext(
            source_id="BANK-SAV-001",
            parsed_document_id="parsed-001",
            source_document_id="src-001",
            snapshot_id="snap-001",
            bank_code="BANK",
            country_code="CA",
            source_type="html",
            source_language="en",
            source_metadata={
                "product_type": "savings",
                "expected_fields": [
                    "regular_interest_rate",
                    "smart_interest_rate",
                    "transaction_fee",
                    "unregistered_free_text",
                ],
            },
        )

        fields = _resolve_field_names(
            context=context,
            override_field_names=None,
            default_fields=("product_name", "standard_rate"),
        )

        self.assertIn("regular_interest_rate", fields)
        self.assertIn("smart_interest_rate", fields)
        self.assertIn("transaction_fee", fields)
        self.assertNotIn("unregistered_free_text", fields)

    def test_labeled_numeric_extension_extraction_keeps_each_value_in_its_own_field(self) -> None:
        context = ExtractionDocumentContext(
            source_id="BANK-SAV-001",
            parsed_document_id="parsed-001",
            source_document_id="src-001",
            snapshot_id="snap-001",
            bank_code="BANK",
            country_code="CA",
            source_type="html",
            source_language="en",
            source_metadata={"product_type": "savings", "product_name": "High Interest Savings Account"},
        )
        excerpt = (
            "High Interest Savings Account Rates and fees. Regular Interest 0.30% to 0.60%. "
            "Smart Interest rate 0.05% when you save $200. Monthly fee $0. "
            "Fee for transactions: $5.00 each."
        )
        expectations = {
            "regular_interest_rate": "0.30",
            "smart_interest_rate": "0.05",
            "transaction_fee": "5.00",
        }
        for field_name, expected in expectations.items():
            with self.subTest(field_name=field_name):
                value, value_type, *_ = _extract_candidate_value(
                    context=context,
                    field_name=field_name,
                    excerpt=excerpt,
                    anchor_value="Rates and fees",
                )
                self.assertEqual(value, expected)
                self.assertEqual(value_type, "decimal")

    def test_labeled_numeric_extension_fallback_scans_exact_official_labels(self) -> None:
        context = ExtractionDocumentContext(
            source_id="BANK-SAV-001",
            parsed_document_id="parsed-001",
            source_document_id="src-001",
            snapshot_id="snap-001",
            bank_code="BANK",
            country_code="CA",
            source_type="html",
            source_language="en",
            source_metadata={"product_type": "savings", "product_name": "High Interest Savings Account"},
        )
        candidate = EvidenceChunkCandidate(
            evidence_chunk_id="chunk-rates-fees",
            parsed_document_id="parsed-001",
            chunk_index=4,
            anchor_type="section",
            anchor_value="Rates and fees",
            page_no=None,
            source_language="en",
            evidence_excerpt=(
                "High Interest Savings Account. Regular Interest 0.30% to 0.60%. "
                "Smart Interest rate 0.05%. Transactions $5.00 each."
            ),
            retrieval_metadata={},
            source_document_id="src-001",
            source_snapshot_id="snap-001",
            bank_code="BANK",
            country_code="CA",
            source_type="html",
        )
        extracted: list[ExtractedFieldCandidate] = []
        _append_labeled_numeric_extension_fallback(
            context=context,
            candidates=[candidate],
            requested_fields={"regular_interest_rate", "smart_interest_rate", "transaction_fee"},
            extracted_fields=extracted,
        )
        self.assertEqual(
            {item.field_name: item.candidate_value for item in extracted},
            {
                "regular_interest_rate": "0.30",
                "smart_interest_rate": "0.05",
                "transaction_fee": "5.00",
            },
        )

    def test_currency_uses_confirmed_discovery_identity_for_foreign_accounts(self) -> None:
        cases = (
            ("U.S. Dollar Savings Account", "USD"),
            ("RBC U.S. High Interest eSavings Account", "USD"),
            ("CIBC US$ Personal Account", "USD"),
            ("Euro Savings Account", "EUR"),
            ("RBC Euro eSavings", "EUR"),
            ("British Pound Savings Account", "GBP"),
            ("Hong Kong Dollar Savings Account", "HKD"),
        )
        for heading, expected in cases:
            with self.subTest(heading=heading):
                context = ExtractionDocumentContext(
                    source_id="AUTO-BANK-SAV-001",
                    parsed_document_id="parsed-001",
                    source_document_id="src-001",
                    snapshot_id="snap-001",
                    bank_code="BANK",
                    country_code="CA",
                    source_type="html",
                    source_language="en",
                    source_metadata={
                        "product_type": "savings",
                        "discovery_metadata": {
                            "primary_heading": heading,
                            "page_title": f"{heading} | Example Bank",
                        },
                    },
                )
                self.assertEqual(_infer_currency(context=context), expected)

    def test_currency_defaults_to_run_country_without_locale_inference(self) -> None:
        us_context = ExtractionDocumentContext(
            source_id="AUTO-US-BANK-CARD-001",
            parsed_document_id="parsed-us-001",
            source_document_id="src-us-001",
            snapshot_id="snap-us-001",
            bank_code="BANK",
            country_code="US",
            source_type="html",
            source_language="en",
            source_metadata={"product_type": "credit-card"},
        )
        unknown_context = ExtractionDocumentContext(
            **{
                **us_context.__dict__,
                "source_id": "AUTO-XX-BANK-CARD-001",
                "country_code": "XX",
            }
        )

        self.assertEqual(_infer_currency(context=us_context), "USD")
        self.assertEqual(_infer_currency(context=unknown_context), "XXX")

    def test_confirmed_discovery_product_title_beats_marketing_heading(self) -> None:
        context = ExtractionDocumentContext(
            source_id="AUTO-BANK-SAV-USD",
            parsed_document_id="parsed-001",
            source_document_id="src-001",
            snapshot_id="snap-001",
            bank_code="BANK",
            country_code="CA",
            source_type="html",
            source_language="en",
            source_metadata={
                "product_type": "savings",
                "discovery_metadata": {
                    "primary_heading": "U.S. Dollar Savings Account",
                    "page_title": "U.S. Dollar Savings Account | Example Bank",
                },
            },
        )
        candidates = [
            EvidenceChunkCandidate(
                evidence_chunk_id="chunk-001",
                parsed_document_id="parsed-001",
                chunk_index=0,
                anchor_type="section",
                anchor_value="hero",
                page_no=None,
                source_language="en",
                evidence_excerpt="Reach your savings goals faster\nEarn interest on every U.S. dollar.",
                retrieval_metadata={},
                source_document_id="src-001",
                source_snapshot_id="snap-001",
                bank_code="BANK",
                country_code="CA",
                source_type="html",
            )
        ]
        self.assertEqual(_extract_document_title(context=context, candidates=candidates), "U.S. Dollar Savings Account")

    def test_high_confidence_detail_h1_beats_audience_seo_title(self) -> None:
        context = ExtractionDocumentContext(
            source_id="AUTO-BANK-CHQ-YOUTH",
            parsed_document_id="parsed-youth",
            source_document_id="src-youth",
            snapshot_id="snap-youth",
            bank_code="CIBC",
            country_code="CA",
            source_type="html",
            source_language="en",
            source_metadata={
                "product_type": "chequing",
                "discovery_metadata": {
                    "primary_heading": "CIBC Smart Start",
                    "page_title": "A Bank Account for Youth Under 25 | CIBC",
                    "ai_predicted_role": "detail",
                    "ai_confidence_band": "high",
                    "ai_parallel_score": 9.5,
                },
            },
        )
        candidate = EvidenceChunkCandidate(
            evidence_chunk_id="chunk-youth-hero",
            parsed_document_id="parsed-youth",
            chunk_index=1,
            anchor_type="section",
            anchor_value="cibc-smart-start",
            page_no=None,
            source_language="en",
            evidence_excerpt="CIBC Smart Start\nUnder 25? Enjoy no-monthly fee everyday banking.",
            retrieval_metadata={},
            source_document_id="src-youth",
            source_snapshot_id="snap-youth",
            bank_code="CIBC",
            country_code="CA",
            source_type="html",
        )

        self.assertEqual(_extract_document_title(context=context, candidates=[candidate]), "CIBC Smart Start")

    def test_negative_unlimited_disclosure_does_not_become_unlimited_plan(self) -> None:
        context = ExtractionDocumentContext(
            source_id="AUTO-BANK-CHQ-001",
            parsed_document_id="parsed-001",
            source_document_id="src-001",
            snapshot_id="snap-001",
            bank_code="BANK",
            country_code="CA",
            source_type="html",
            source_language="en",
            source_metadata={"product_type": "chequing"},
        )
        value, *_ = _extract_candidate_value(
            context=context,
            field_name="unlimited_transactions_flag",
            excerpt="For accounts that do not provide unlimited debit transactions, excess fees apply.",
            anchor_value="legal",
        )
        self.assertIsNone(value)

    def test_exact_monthly_transaction_limit_is_not_unlimited(self) -> None:
        context = ExtractionDocumentContext(
            source_id="AUTO-BANK-CHQ-LIMITED",
            parsed_document_id="parsed-limited",
            source_document_id="src-limited",
            snapshot_id="snap-limited",
            bank_code="BANK",
            country_code="CA",
            source_type="html",
            source_language="en",
            source_metadata={"product_type": "chequing", "product_name": "Limited Chequing Account"},
        )
        for excerpt in (
            "6 Debits / Month. $1.25 each thereafter.",
            "12 debits of any kind, plus unlimited e-Transfers.",
        ):
            with self.subTest(excerpt=excerpt):
                value, *_ = _extract_candidate_value(
                    context=context,
                    field_name="unlimited_transactions_flag",
                    excerpt=excerpt,
                    anchor_value="account features",
                )
                self.assertFalse(value)

    def test_standard_fee_precedes_conditional_zero_on_same_fee_card(self) -> None:
        context = ExtractionDocumentContext(
            source_id="AUTO-BANK-CHQ-BASIC",
            parsed_document_id="parsed-basic",
            source_document_id="src-basic",
            snapshot_id="snap-basic",
            bank_code="BANK",
            country_code="CA",
            source_type="html",
            source_language="en",
            source_metadata={"product_type": "chequing", "product_name": "Basic Bank Account"},
        )
        for excerpt, expected in (
            ("Monthly account fee\n$3.95 or $0\n/month\nSenior pricing $0/month", "3.95"),
            (
                "Monthly account fee\n$11.95 or $0\n/month\nWaive the monthly account fee by holding $3,000 every day",
                "11.95",
            ),
        ):
            with self.subTest(excerpt=excerpt):
                fee, *_ = _extract_candidate_value(
                    context=context, field_name="monthly_fee", excerpt=excerpt, anchor_value="at a glance"
                )
                self.assertEqual(fee, expected)

    def test_balance_condition_does_not_turn_base_monthly_fee_into_zero(self) -> None:
        context = ExtractionDocumentContext(
            source_id="AUTO-BANK-CHQ-UNLIMITED",
            parsed_document_id="parsed-unlimited",
            source_document_id="src-unlimited",
            snapshot_id="snap-unlimited",
            bank_code="BANK",
            country_code="CA",
            source_type="html",
            source_language="en",
            source_metadata={"product_type": "chequing", "product_name": "Unlimited Chequing Account"},
        )

        fee, *_ = _extract_candidate_value(
            context=context,
            field_name="monthly_fee",
            excerpt="No monthly fee if you maintain $4,000 or more at the end of each day of the month.",
            anchor_value="benefits",
        )

        self.assertIsNone(fee)

        plan_fee, *_ = _extract_candidate_value(
            context=context,
            field_name="monthly_fee",
            excerpt="There is no monthly plan fee when you maintain the required daily balance.",
            anchor_value="faq",
        )
        self.assertIsNone(plan_fee)

    def test_minimum_balance_distinguishes_no_requirement_from_fee_waiver_threshold(self) -> None:
        context = ExtractionDocumentContext(
            source_id="AUTO-BANK-CHQ-REWARDS",
            parsed_document_id="parsed-rewards",
            source_document_id="src-rewards",
            snapshot_id="snap-rewards",
            bank_code="BANK",
            country_code="CA",
            source_type="html",
            source_language="en",
            source_metadata={"product_type": "chequing", "product_name": "Rewards Chequing Account"},
        )
        no_requirement, *_ = _extract_candidate_value(
            context=context,
            field_name="minimum_balance",
            excerpt=(
                "You don’t need to keep a minimum balance in the account as long as you pay "
                "the monthly plan fee of $17.95."
            ),
            anchor_value="minimum balance",
        )
        waiver_threshold, *_ = _extract_candidate_value(
            context=context,
            field_name="minimum_balance",
            excerpt=(
                "There’s no minimum balance required. If you keep and maintain at least $6,000 "
                "in the account, we’ll waive the monthly account fee."
            ),
            anchor_value="minimum balance",
        )

        self.assertEqual(no_requirement, "0.00")
        self.assertEqual(waiver_threshold, "6000.00")

    def test_separately_worded_monthly_fee_rebate_maps_daily_balance(self) -> None:
        context = ExtractionDocumentContext(
            source_id="AUTO-BANK-CHQ-SMART",
            parsed_document_id="parsed-smart",
            source_document_id="src-smart",
            snapshot_id="snap-smart",
            bank_code="BANK",
            country_code="CA",
            source_type="html",
            source_language="en",
            source_metadata={"product_type": "chequing", "product_name": "Smart Account"},
        )
        excerpt = (
            "Monthly fee for up to 3 accounts: $16.95 or $0, monthly fee rebated "
            "with an end-of-day account balance of $4,000 each day for that month."
        )

        minimum_balance, *_ = _extract_candidate_value(
            context=context, field_name="minimum_balance", excerpt=excerpt, anchor_value="fees"
        )
        fee_waiver, *_ = _extract_candidate_value(
            context=context, field_name="fee_waiver_condition", excerpt=excerpt, anchor_value="fees"
        )

        self.assertEqual(minimum_balance, "4000.00")
        self.assertEqual(
            fee_waiver,
            "Monthly fee 16.95 is waived to 0.00 with a 4000.00 minimum balance.",
        )

    def test_mobile_wallet_purchases_are_not_an_application_method(self) -> None:
        context = ExtractionDocumentContext(
            source_id="AUTO-BANK-CARD-CASHBACK",
            parsed_document_id="parsed-card",
            source_document_id="src-card",
            snapshot_id="snap-card",
            bank_code="BANK",
            country_code="CA",
            source_type="html",
            source_language="en",
            source_metadata={"product_type": "credit-card", "product_name": "Cashback Mastercard"},
        )

        application_method, *_ = _extract_candidate_value(
            context=context,
            field_name="application_method",
            excerpt=(
                "Learn how to sign up for eStatements. Pay anywhere with your phone. "
                "Make quick and secure purchases when you add your card to your mobile wallet."
            ),
            anchor_value="mobile-wallet",
        )

        self.assertIsNone(application_method)

    def test_standard_rate_does_not_use_promotional_rate_and_nonregistered_offer_is_scoped(self) -> None:
        context = ExtractionDocumentContext(
            source_id="AUTO-BANK-SAV-USD",
            parsed_document_id="parsed-001",
            source_document_id="src-001",
            snapshot_id="snap-001",
            bank_code="BANK",
            country_code="CA",
            source_type="html",
            source_language="en",
            source_metadata={"product_type": "savings", "product_name": "U.S. Dollar Savings Account"},
        )
        excerpt = (
            "Non-registered promotional rate of 4.50% applies for 153 days. "
            "Registered promotional rate of 4.60% applies to TFSA and RSP accounts."
        )
        standard, *_ = _extract_candidate_value(
            context=context, field_name="standard_rate", excerpt=excerpt, anchor_value="offer"
        )
        promotional, *_ = _extract_candidate_value(
            context=context, field_name="promotional_rate", excerpt=excerpt, anchor_value="offer"
        )
        self.assertIsNone(standard)
        self.assertEqual(promotional, "4.50")

    def test_five_month_offer_is_promotional_and_rsp_rif_are_registered_products(self) -> None:
        cases = (
            ("Savings Account", "Earn 4.50% for 5 months with this New Client offer.", "4.50"),
            ("RSP Savings Account", "Build momentum with a 5-month rate. Earn 4.60% on RSP Savings.", "4.60"),
            ("RIF Savings Account", "Welcome offer: earn 4.60% interest for 153 days.", "4.60"),
        )
        for product_name, excerpt, expected in cases:
            with self.subTest(product_name=product_name):
                context = ExtractionDocumentContext(
                    source_id="AUTO-TANGERINE-SAV-test",
                    parsed_document_id="parsed-test",
                    source_document_id="src-test",
                    snapshot_id="snap-test",
                    bank_code="TANGERINE",
                    country_code="CA",
                    source_type="html",
                    source_language="en",
                    source_metadata={"product_type": "savings", "product_name": product_name},
                )
                standard, *_ = _extract_candidate_value(
                    context=context, field_name="standard_rate", excerpt=excerpt, anchor_value="offer"
                )
                promotional, *_ = _extract_candidate_value(
                    context=context, field_name="promotional_rate", excerpt=excerpt, anchor_value="offer"
                )
                self.assertIsNone(standard)
                self.assertEqual(promotional, expected)

    def test_nonregistered_product_does_not_borrow_registered_only_legal_rate(self) -> None:
        context = ExtractionDocumentContext(
            source_id="AUTO-TANGERINE-SAV-test",
            parsed_document_id="parsed-test",
            source_document_id="src-test",
            snapshot_id="snap-test",
            bank_code="TANGERINE",
            country_code="CA",
            source_type="html",
            source_language="en",
            source_metadata={"product_type": "savings", "product_name": "Savings Account"},
        )
        excerpt = "The 4.60% Registered Promotional Rate applies to eligible RSP, TFSA and RIF accounts."

        promotional, *_ = _extract_candidate_value(
            context=context, field_name="promotional_rate", excerpt=excerpt, anchor_value="legal"
        )

        self.assertIsNone(promotional)

    def test_rate_table_separates_first_months_promotion_from_thereafter_standard(self) -> None:
        context = ExtractionDocumentContext(
            source_id="AUTO-BANK-SAV-HISA",
            parsed_document_id="parsed-hisa",
            source_document_id="src-hisa",
            snapshot_id="snap-hisa",
            bank_code="BANK",
            country_code="CA",
            source_type="html",
            source_language="en",
            source_metadata={"product_type": "savings", "product_name": "High Interest Savings Account"},
        )
        excerpt = "Interest Rates Time Rate First 3 months 4.60% Thereafter 0.550%"
        standard, *_ = _extract_candidate_value(
            context=context, field_name="standard_rate", excerpt=excerpt, anchor_value="rates"
        )
        promotional, *_ = _extract_candidate_value(
            context=context, field_name="promotional_rate", excerpt=excerpt, anchor_value="rates"
        )
        self.assertEqual(standard, "0.55")
        self.assertEqual(promotional, "4.60")

    def test_promotional_rate_uses_labeled_total_not_regular_component(self) -> None:
        context = ExtractionDocumentContext(
            source_id="AUTO-BANK-SAV-HISA",
            parsed_document_id="parsed-hisa",
            source_document_id="src-hisa",
            snapshot_id="snap-hisa",
            bank_code="BANK",
            country_code="CA",
            source_type="html",
            source_language="en",
            source_metadata={"product_type": "savings", "product_name": "High Interest Savings Account"},
        )
        excerpt = (
            "The Regular Interest Rate was 0.55% and the Bonus Interest Rate was 4.05%. "
            "The Promotional Interest Rate would be 4.60% per annum."
        )
        promotional, *_ = _extract_candidate_value(
            context=context, field_name="promotional_rate", excerpt=excerpt, anchor_value="offer"
        )
        self.assertEqual(promotional, "4.60")

    def test_promotional_rate_prefers_total_offer_over_incremental_component(self) -> None:
        context = ExtractionDocumentContext(
            source_id="AUTO-BANK-SAV-HISA",
            parsed_document_id="parsed-hisa",
            source_document_id="src-hisa",
            snapshot_id="snap-hisa",
            bank_code="BANK",
            country_code="CA",
            source_type="html",
            source_language="en",
            source_metadata={"product_type": "savings", "product_name": "High Interest Savings Account"},
        )
        excerpt = (
            "Earn up to 5.00% for the first 3 months. Promotional rate 2.80% plus a regular interest rate "
            "of up to 2.20%. Total Interest Rate Including Promo 5.00%."
        )
        promotional, *_ = _extract_candidate_value(
            context=context, field_name="promotional_rate", excerpt=excerpt, anchor_value="offer"
        )
        self.assertEqual(promotional, "5.00")

    def test_ongoing_bonus_tier_is_not_a_promotional_rate(self) -> None:
        context = ExtractionDocumentContext(
            source_id="AUTO-BANK-SAV-MONEY",
            parsed_document_id="parsed-money",
            source_document_id="src-money",
            snapshot_id="snap-money",
            bank_code="BANK",
            country_code="CA",
            source_type="html",
            source_language="en",
            source_metadata={"product_type": "savings", "product_name": "Money Master Savings Account"},
        )
        value, *_ = _extract_candidate_value(
            context=context,
            field_name="promotional_rate",
            excerpt="Annual interest rate 0.01%. Annual interest rate with Bonus Interest if enrolled: 0.50%.",
            anchor_value="rates",
        )
        self.assertIsNone(value)

        public_display, *_ = _extract_candidate_value(
            context=context,
            field_name="public_display_rate",
            excerpt="Annual interest rate 0.01%. Annual interest rate with Bonus Interest if enrolled: 0.50%.",
            anchor_value="rates",
        )
        self.assertEqual(public_display, "0.50")

    def test_minimum_deposit_accepts_money_before_investment_label(self) -> None:
        context = ExtractionDocumentContext(
            source_id="AUTO-BANK-GIC-001",
            parsed_document_id="parsed-001",
            source_document_id="src-001",
            snapshot_id="snap-001",
            bank_code="BANK",
            country_code="CA",
            source_type="html",
            source_language="en",
            source_metadata={"product_type": "gic"},
        )

        value, value_type, _, _ = _extract_candidate_value(
            context=context,
            field_name="minimum_deposit",
            excerpt="All GICs require a $500 minimum investment.",
            anchor_value="minimum investment",
        )

        self.assertEqual(value_type, "decimal")
        self.assertEqual(value, "500.00")

    def test_dynamic_ai_is_limited_to_candidate_producing_detail_sources(self) -> None:
        base = dict(
            source_id="AUTO-BANK-LOAN-001",
            parsed_document_id="parsed-001",
            source_document_id="src-001",
            snapshot_id="snap-001",
            bank_code="BANK",
            country_code="CA",
            source_type="html",
            source_language="en",
        )
        detail = ExtractionDocumentContext(
            **base,
            source_metadata={"product_type": "personal-loan", "product_type_dynamic": True, "discovery_role": "detail"},
        )
        supporting = ExtractionDocumentContext(
            **base,
            source_metadata={"product_type": "personal-loan", "product_type_dynamic": True, "discovery_role": "supporting_html"},
        )

        self.assertTrue(_uses_dynamic_product_type(detail))
        self.assertFalse(_uses_dynamic_product_type(supporting))

    def test_term_rate_table_pairs_rate_first_haventree_rows_without_shifting(self) -> None:
        context = ExtractionDocumentContext(
            source_id="AUTO-HAVENTREE-GIC-001",
            parsed_document_id="parsed-haventree-gic-rates",
            source_document_id="src-haventree-gic-rates",
            snapshot_id="snap-haventree-gic-rates",
            bank_code="HAVENTREE",
            country_code="CA",
            source_type="html",
            source_language="en",
            source_metadata={"product_type": "gic", "product_name": "Short Term GIC"},
        )
        excerpt = (
            "Rate Term 0.20% 1 month 0.25% 2 months 2.50% 3 months "
            "2.70% 6 months 2.85% 9 months 3.33% 1 year "
            "4.00% 2 years 3.85% 3 years 3.89% 4 years 4.00% 5 years"
        )

        table, value_type, _, _ = _extract_candidate_value(
            context=context,
            field_name="term_rate_table",
            excerpt=excerpt,
            anchor_value="rates",
        )

        self.assertEqual(value_type, "json")
        self.assertEqual(
            [(row["term_label"], row["rate"]) for row in table],
            [
                ("1 month", "0.20"),
                ("2 months", "0.25"),
                ("3 months", "2.50"),
                ("6 months", "2.70"),
                ("9 months", "2.85"),
                ("1 year", "3.33"),
                ("2 years", "4.00"),
                ("3 years", "3.85"),
                ("4 years", "3.89"),
                ("5 years", "4.00"),
            ],
        )

    def test_term_rate_table_preserves_fractional_year_and_ignores_calculator_money(self) -> None:
        context = ExtractionDocumentContext(
            source_id="AUTO-BANK-GIC-001",
            parsed_document_id="parsed-gic-rates",
            source_document_id="src-gic-rates",
            snapshot_id="snap-gic-rates",
            bank_code="BANK",
            country_code="CA",
            source_type="html",
            source_language="en",
            source_metadata={"product_type": "gic", "product_name": "Guaranteed Investment"},
        )
        excerpt = (
            "Term Interest rate 90 days 2.55% 1 year 3.15% 1.5 year 3.25% "
            "2 years 3.35% 5 years 3.65% GIC amount $1,000 Interest earned $31.44"
        )

        table, value_type, _, _ = _extract_candidate_value(
            context=context,
            field_name="term_rate_table",
            excerpt=excerpt,
            anchor_value="rates",
        )

        self.assertEqual(value_type, "json")
        self.assertEqual(
            [(row["term_label"], row["term_length_days"], row["rate"]) for row in table],
            [
                ("90 days", 90, "2.55"),
                ("1 year", 365, "3.15"),
                ("1.5 year", 548, "3.25"),
                ("2 years", 730, "3.35"),
                ("5 years", 1825, "3.65"),
            ],
        )
        self.assertTrue(all(row["minimum_deposit"] is None for row in table))

    def test_term_rate_table_rate_first_tie_uses_document_order_not_shifted_duplicates(self) -> None:
        context = ExtractionDocumentContext(
            source_id="BANK-SAV-001",
            parsed_document_id="parsed-001",
            source_document_id="src-001",
            snapshot_id="snap-001",
            bank_code="BANK",
            country_code="CA",
            source_type="html",
            source_language="en",
            source_metadata={"product_type": "savings", "product_name": "Premium Period Savings"},
        )
        excerpt = (
            "Premium Period Interest Rate 0.45% | 360 days 0.30% | 270 days "
            "0.25% | 180 days 0.20% | 90 days 0.45% 0.30% 0.25% 0.20% | 90 days"
        )

        table, *_ = _extract_candidate_value(
            context=context,
            field_name="term_rate_table",
            excerpt=excerpt,
            anchor_value="Premium Period Interest Rate",
        )

        self.assertEqual(
            [(row["term_label"], row["rate"]) for row in table],
            [("360 days", "0.45"), ("270 days", "0.30"), ("180 days", "0.25"), ("90 days", "0.20")],
        )

    def test_rate_fallback_adds_missing_advertised_total_beside_regular_rate(self) -> None:
        context = ExtractionDocumentContext(
            source_id="BANK-SAV-001",
            parsed_document_id="parsed-001",
            source_document_id="src-001",
            snapshot_id="snap-001",
            bank_code="BANK",
            country_code="CA",
            source_type="html",
            source_language="en",
            source_metadata={"product_type": "savings", "product_name": "Momentum Plus Savings Account"},
        )
        candidate = EvidenceChunkCandidate(
            evidence_chunk_id="chunk-offer",
            parsed_document_id="parsed-001",
            chunk_index=2,
            anchor_type="section",
            anchor_value="Offer details",
            page_no=None,
            source_language="en",
            evidence_excerpt=(
                "Momentum Plus Savings Account. Earn a savings rate of 4.65% for a limited time "
                "with a 90-day premium period."
            ),
            retrieval_metadata={},
            source_document_id="src-001",
            source_snapshot_id="snap-001",
            bank_code="BANK",
            country_code="CA",
            source_type="html",
        )
        extracted_fields = [
            ExtractedFieldCandidate(
                field_name="standard_rate",
                candidate_value="0.40",
                value_type="decimal",
                confidence=0.99,
                extraction_method="heuristic_percent",
                source_document_id="src-001",
                source_snapshot_id="snap-001",
                evidence_chunk_id="chunk-regular",
                evidence_text_excerpt="Regular Interest Rate 0.40%",
                anchor_type="section",
                anchor_value="Regular rate",
                page_no=None,
                chunk_index=1,
                field_metadata={},
            )
        ]

        _append_rate_fallback_fields(
            context=context,
            candidates=[candidate],
            requested_fields={"standard_rate", "promotional_rate", "public_display_rate"},
            extracted_fields=extracted_fields,
        )

        self.assertEqual(
            {field.field_name: field.candidate_value for field in extracted_fields},
            {"standard_rate": "0.40", "promotional_rate": "4.65"},
        )

    def test_foreign_currency_fee_and_separate_waiver_are_recovered(self) -> None:
        context = ExtractionDocumentContext(
            source_id="BANK-USD-SAV-001",
            parsed_document_id="parsed-001",
            source_document_id="src-001",
            snapshot_id="snap-001",
            bank_code="BANK",
            country_code="CA",
            source_type="html",
            source_language="en",
            source_metadata={"product_type": "savings", "product_name": "U.S. Dollar Savings Account"},
        )
        candidate = EvidenceChunkCandidate(
            evidence_chunk_id="chunk-fee",
            parsed_document_id="parsed-001",
            chunk_index=3,
            anchor_type="section",
            anchor_value="At a glance",
            page_no=None,
            source_language="en",
            evidence_excerpt=(
                "At a glance Monthly account fee $1 USD or $0 /month. How to waive the monthly account fee: "
                "waive the monthly account fee by holding $200 USD or more every day for the entire month."
            ),
            retrieval_metadata={},
            source_document_id="src-001",
            source_snapshot_id="snap-001",
            bank_code="BANK",
            country_code="CA",
            source_type="html",
        )
        extracted_fields: list[ExtractedFieldCandidate] = []

        _append_monthly_fee_fallback(
            context=context,
            candidates=[candidate],
            requested_fields={"monthly_fee"},
            extracted_fields=extracted_fields,
        )
        _append_fee_waiver_fallback(
            context=context,
            candidates=[candidate],
            requested_fields={"minimum_balance", "fee_waiver_condition"},
            extracted_fields=extracted_fields,
        )

        values = {field.field_name: field.candidate_value for field in extracted_fields}
        self.assertEqual(values["monthly_fee"], "1.00")
        self.assertEqual(values["minimum_balance"], "200.00")
        self.assertIn("200", values["fee_waiver_condition"])

    def test_euro_symbol_monthly_fee_uses_same_currency_agnostic_parser(self) -> None:
        context = ExtractionDocumentContext(
            source_id="BANK-EUR-SAV-001",
            parsed_document_id="parsed-001",
            source_document_id="src-001",
            snapshot_id="snap-001",
            bank_code="BANK",
            country_code="CA",
            source_type="html",
            source_language="en",
            source_metadata={"product_type": "savings", "product_name": "Euro Savings Account"},
        )
        value, *_ = _extract_candidate_value(
            context=context,
            field_name="monthly_fee",
            excerpt="Monthly account fee €1.00 per month.",
            anchor_value="At a glance",
        )
        self.assertEqual(value, "1.00")

    def test_parallel_rate_and_apy_table_uses_comparable_apy_column(self) -> None:
        context = ExtractionDocumentContext(
            source_id="BANK-GIC-001",
            parsed_document_id="parsed-001",
            source_document_id="src-001",
            snapshot_id="snap-001",
            bank_code="BANK",
            country_code="CA",
            source_type="html",
            source_language="en",
            source_metadata={"product_type": "gic", "product_name": "Guaranteed Investment Certificates"},
        )
        excerpt = (
            "Interest rates GIC/RGIC term Rate (%) APY (%) "
            "1 year 2.863% 2.90% 2 year 2.960% 3.00% 3 year 3.155% 3.20% "
            "4 year 3.494% 3.55% 5 year 3.591% 3.65%"
        )

        table, *_ = _extract_candidate_value(
            context=context,
            field_name="term_rate_table",
            excerpt=excerpt,
            anchor_value="Interest rates",
        )

        self.assertEqual([row["rate"] for row in table], ["2.90", "3.00", "3.20", "3.55", "3.65"])
        self.assertTrue(all(row["notes"] == "APY" for row in table))

    def test_as_little_as_amount_is_minimum_deposit(self) -> None:
        context = ExtractionDocumentContext(
            source_id="BANK-GIC-001",
            parsed_document_id="parsed-001",
            source_document_id="src-001",
            snapshot_id="snap-001",
            bank_code="BANK",
            country_code="CA",
            source_type="html",
            source_language="en",
            source_metadata={"product_type": "gic", "product_name": "Guaranteed Investment Certificates"},
        )
        value, *_ = _extract_candidate_value(
            context=context,
            field_name="minimum_deposit",
            excerpt="You can start with as little as $100 and your principal is always guaranteed.",
            anchor_value="Benefits",
        )
        self.assertEqual(value, "100.00")

    def test_generic_product_eligibility_rejects_adjacent_student_program(self) -> None:
        context = ExtractionDocumentContext(
            source_id="BANK-GIC-001",
            parsed_document_id="parsed-001",
            source_document_id="src-001",
            snapshot_id="snap-001",
            bank_code="BANK",
            country_code="CA",
            source_type="html",
            source_language="en",
            source_metadata={"product_type": "gic", "product_name": "Guaranteed Investment Certificates"},
        )
        value, _, method, metadata = _extract_candidate_value(
            context=context,
            field_name="eligibility_text",
            excerpt=(
                "Our International Student GIC Program helps you open and fund your account before you arrive "
                "in Canada and meet visa requirements."
            ),
            anchor_value="Are you an International student?",
        )
        self.assertIsNone(value)
        self.assertEqual(method, "heuristic_noise_filter")
        self.assertEqual(metadata["suppressed_reason"], "audience_specific_sibling_program")

    def test_product_eligibility_rejects_insurance_cta_and_bundle_offer_copy(self) -> None:
        context = ExtractionDocumentContext(
            source_id="BANK-SAV-001",
            parsed_document_id="parsed-001",
            source_document_id="src-001",
            snapshot_id="snap-001",
            bank_code="BANK",
            country_code="CA",
            source_type="html",
            source_language="en",
            source_metadata={"product_type": "savings", "product_name": "Example Savings Account"},
        )
        for excerpt in (
            "Give us a call. Eligible for CDIC Insurance. Regular interest is calculated daily.",
            "How to apply Talk to an advisor.",
            (
                "Open an eligible savings account and a new eligible Credit Card Account and "
                "complete certain qualifying transactions and qualifying conditions."
            ),
            (
                "Open a No Fee Chequing Account and set up an eligible direct deposit today of "
                "$100 or more for 3 straight months."
            ),
        ):
            with self.subTest(excerpt=excerpt):
                value, *_ = _extract_candidate_value(
                    context=context,
                    field_name="eligibility_text",
                    excerpt=excerpt,
                    anchor_value="Account details",
                )
                self.assertIsNone(value)

    def test_apply_by_channel_is_trimmed_before_following_rate_table(self) -> None:
        context = ExtractionDocumentContext(
            source_id="BANK-GIC-001",
            parsed_document_id="parsed-001",
            source_document_id="src-001",
            snapshot_id="snap-001",
            bank_code="BANK",
            country_code="CA",
            source_type="html",
            source_language="en",
            source_metadata={"product_type": "gic", "product_name": "Guaranteed Investment Certificates"},
        )
        value, *_ = _extract_candidate_value(
            context=context,
            field_name="application_method",
            excerpt=(
                "How to apply for this account Apply by signing on to online banking or calling us at "
                "1-888-723-8881. Interest rates GIC term Rate (%) APY (%)."
            ),
            anchor_value="How to apply",
        )
        self.assertEqual(value, "Apply by signing on to online banking or calling us at 1-888-723-8881")

    def test_term_rate_table_uses_most_complete_grounded_match(self) -> None:
        context = ExtractionDocumentContext(
            source_id="AUTO-BANK-GIC-RATES",
            parsed_document_id="parsed-gic-rates",
            source_document_id="src-gic-rates",
            snapshot_id="snap-gic-rates",
            bank_code="BANK",
            country_code="CA",
            source_type="html",
            source_language="en",
            source_metadata={"product_type": "gic", "product_name": "GICs"},
        )
        excerpts = {
            "chunk-short": "1 Year 3.30% 5 Year 4.00%",
            "chunk-full": "1 Year 3.30% 2 Year 3.55% 3 Year 3.65% 4 Year 3.75% 5 Year 4.00%",
        }
        candidates = {
            chunk_id: EvidenceChunkCandidate(
                evidence_chunk_id=chunk_id,
                parsed_document_id="parsed-gic-rates",
                chunk_index=index,
                anchor_type="section",
                anchor_value="rates",
                page_no=None,
                source_language="en",
                evidence_excerpt=excerpt,
                retrieval_metadata={},
                source_document_id="src-gic-rates",
                source_snapshot_id="snap-gic-rates",
                bank_code="BANK",
                country_code="CA",
                source_type="html",
            )
            for index, (chunk_id, excerpt) in enumerate(excerpts.items())
        }
        matches = [
            EvidenceMatch(
                evidence_chunk_id=chunk_id,
                field_name="term_rate_table",
                score=0.95 if chunk_id == "chunk-short" else 0.85,
                retrieval_mode="metadata-only",
                evidence_text_excerpt=excerpt,
                source_document_id="src-gic-rates",
                source_snapshot_id="snap-gic-rates",
                model_execution_id=None,
                parsed_document_id="parsed-gic-rates",
                anchor_type="section",
                anchor_value="rates",
                page_no=None,
                chunk_index=index,
                match_metadata={"matched_keywords": ["rate"]},
            )
            for index, (chunk_id, excerpt) in enumerate(excerpts.items())
        ]

        field = _extract_from_matches(
            context=context,
            field_name="term_rate_table",
            matches=matches,
            candidate_map=candidates,
        )

        self.assertIsNotNone(field)
        assert field is not None
        self.assertEqual(field.evidence_chunk_id, "chunk-full")
        self.assertEqual(len(field.candidate_value), 5)

    def test_term_rate_table_prefers_complete_target_table_over_rate_headline(self) -> None:
        context = ExtractionDocumentContext(
            source_id="AUTO-BANK-GIC-NONREDEEMABLE",
            parsed_document_id="parsed-gic-detail",
            source_document_id="src-gic-detail",
            snapshot_id="snap-gic-detail",
            bank_code="BANK",
            country_code="CA",
            source_type="html",
            source_language="en",
            source_metadata={"product_type": "gic", "product_name": "Bank Non-Redeemable GIC"},
        )
        excerpts = {
            "chunk-headline": "Bank Non-Redeemable GIC Get 2.70% on a 1 year Bank Non-Redeemable GIC.",
            "chunk-table": (
                "Non-Redeemable GIC Terms and rates: 1 year 2.70% 2 years 2.75% "
                "3 years 2.85% 4 years 3.00% 5 years 3.10%."
            ),
        }
        candidates = {
            chunk_id: EvidenceChunkCandidate(
                evidence_chunk_id=chunk_id,
                parsed_document_id="parsed-gic-detail",
                chunk_index=index,
                anchor_type="section",
                anchor_value="rates",
                page_no=1,
                source_language="en",
                evidence_excerpt=excerpt,
                retrieval_metadata={},
                source_document_id="src-gic-detail",
                source_snapshot_id="snap-gic-detail",
                bank_code="BANK",
                country_code="CA",
                source_type="html",
            )
            for index, (chunk_id, excerpt) in enumerate(excerpts.items())
        }
        matches = [
            EvidenceMatch(
                evidence_chunk_id=chunk_id,
                field_name="term_rate_table",
                score=0.99 if chunk_id == "chunk-headline" else 0.95,
                retrieval_mode="metadata-only",
                evidence_text_excerpt=excerpt,
                source_document_id="src-gic-detail",
                source_snapshot_id="snap-gic-detail",
                model_execution_id=None,
                parsed_document_id="parsed-gic-detail",
                anchor_type="section",
                anchor_value="rates",
                page_no=1,
                chunk_index=index,
                match_metadata={"matched_keywords": ["rate"]},
            )
            for index, (chunk_id, excerpt) in enumerate(excerpts.items())
        ]

        field = _extract_from_matches(
            context=context,
            field_name="term_rate_table",
            matches=matches,
            candidate_map=candidates,
        )

        self.assertIsNotNone(field)
        assert field is not None
        self.assertEqual(field.evidence_chunk_id, "chunk-table")
        self.assertEqual([row["rate"] for row in field.candidate_value], ["2.70", "2.75", "2.85", "3.00", "3.10"])

    def test_minimum_deposit_fallback_uses_explicit_product_investment_label(self) -> None:
        context = ExtractionDocumentContext(
            source_id="AUTO-BANK-GIC-NONREDEEMABLE",
            parsed_document_id="parsed-gic-detail",
            source_document_id="src-gic-detail",
            snapshot_id="snap-gic-detail",
            bank_code="BANK",
            country_code="CA",
            source_type="html",
            source_language="en",
            source_metadata={"product_type": "gic", "product_name": "Bank Non-Redeemable GIC"},
        )
        candidates = [
            EvidenceChunkCandidate(
                evidence_chunk_id="chunk-gic-terms",
                parsed_document_id="parsed-gic-detail",
                chunk_index=1,
                anchor_type="section",
                anchor_value="terms-and-rates",
                page_no=2,
                source_language="en",
                evidence_excerpt=(
                    "Non-Redeemable GIC Terms and rates. Minimum investment of $500. "
                    "1 year 2.70% 2 years 2.75%."
                ),
                retrieval_metadata={},
                source_document_id="src-gic-detail",
                source_snapshot_id="snap-gic-detail",
                bank_code="BANK",
                country_code="CA",
                source_type="html",
            )
        ]
        extracted_fields: list[ExtractedFieldCandidate] = []

        _append_minimum_deposit_fallback(
            context=context,
            candidates=candidates,
            requested_fields={"minimum_deposit"},
            extracted_fields=extracted_fields,
        )

        self.assertEqual(len(extracted_fields), 1)
        self.assertEqual(extracted_fields[0].candidate_value, "500.00")
        self.assertEqual(extracted_fields[0].evidence_chunk_id, "chunk-gic-terms")

    def test_minimum_deposit_fallback_replaces_payment_option_minimum_with_product_schedule(self) -> None:
        context = ExtractionDocumentContext(
            source_id="BANK-GIC-FAMILY",
            parsed_document_id="parsed-gic-family",
            source_document_id="src-gic-family",
            snapshot_id="snap-gic-family",
            bank_code="BANK",
            country_code="CA",
            source_type="html",
            source_language="en",
            source_metadata={"product_type": "gic", "product_name": "Guaranteed-Return GICs"},
        )
        schedule = EvidenceChunkCandidate(
            evidence_chunk_id="chunk-minimum-schedule",
            parsed_document_id="parsed-gic-family",
            chunk_index=5,
            anchor_type="section",
            anchor_value="minimum-investment",
            page_no=None,
            source_language="en",
            evidence_excerpt=(
                "Minimum Investment $500 for RRSP, TFSA, RESP and RDSP; $1,000 for non-registered GICs; "
                "$5,000 for terms between 30-364 days or monthly interest; $100,000 for terms under 30 days."
            ),
            retrieval_metadata={},
            source_document_id="src-gic-family",
            source_snapshot_id="snap-gic-family",
            bank_code="BANK",
            country_code="CA",
            source_type="html",
        )
        legal_option = EvidenceChunkCandidate(
            evidence_chunk_id="chunk-monthly-option",
            parsed_document_id="parsed-gic-family",
            chunk_index=115,
            anchor_type="legal",
            anchor_value="disclaimer",
            page_no=None,
            source_language="en",
            evidence_excerpt="For monthly interest payment option, minimum investment is $5,000.",
            retrieval_metadata={},
            source_document_id="src-gic-family",
            source_snapshot_id="snap-gic-family",
            bank_code="BANK",
            country_code="CA",
            source_type="html",
        )
        extracted_fields = [
            ExtractedFieldCandidate(
                field_name="minimum_deposit",
                candidate_value="5000.00",
                value_type="decimal",
                confidence=0.8,
                extraction_method="heuristic_money",
                source_document_id="src-gic-family",
                source_snapshot_id="snap-gic-family",
                evidence_chunk_id="chunk-monthly-option",
                evidence_text_excerpt=legal_option.evidence_excerpt,
                anchor_type="legal",
                anchor_value="disclaimer",
                page_no=None,
                chunk_index=115,
                field_metadata={},
            )
        ]

        _append_minimum_deposit_fallback(
            context=context,
            candidates=[schedule, legal_option],
            requested_fields={"minimum_deposit"},
            extracted_fields=extracted_fields,
        )

        self.assertEqual(len(extracted_fields), 1)
        self.assertEqual(extracted_fields[0].candidate_value, "500.00")
        self.assertEqual(extracted_fields[0].evidence_chunk_id, "chunk-minimum-schedule")
        self.assertTrue(extracted_fields[0].field_metadata["replaced_conditional_option_minimum"])

    def test_minimum_deposit_fallback_keeps_single_label_before_repeated_product_identity(self) -> None:
        context = ExtractionDocumentContext(
            source_id="CIBC-GIC-VARIABLE",
            parsed_document_id="parsed-cibc-variable",
            source_document_id="src-cibc-variable",
            snapshot_id="snap-cibc-variable",
            bank_code="CIBC",
            country_code="CA",
            source_type="html",
            source_language="en",
            source_metadata={"product_type": "gic", "product_name": "CIBC Variable Rate GIC"},
        )
        candidate = EvidenceChunkCandidate(
            evidence_chunk_id="chunk-cibc-variable-terms",
            parsed_document_id="parsed-cibc-variable",
            chunk_index=1,
            anchor_type="section",
            anchor_value="term-and-rate",
            page_no=None,
            source_language="en",
            evidence_excerpt=(
                "Term and rate Minimum investment of $1,000. What you need to know. "
                "You can automatically renew your GIC when it matures. "
                "How to invest in a CIBC Variable Rate GIC. Term Rate 1 year 2.00%."
            ),
            retrieval_metadata={},
            source_document_id="src-cibc-variable",
            source_snapshot_id="snap-cibc-variable",
            bank_code="CIBC",
            country_code="CA",
            source_type="html",
        )
        extracted_fields: list[ExtractedFieldCandidate] = []

        _append_minimum_deposit_fallback(
            context=context,
            candidates=[candidate],
            requested_fields={"minimum_deposit"},
            extracted_fields=extracted_fields,
        )

        self.assertEqual(extracted_fields[0].candidate_value, "1000.00")
        self.assertIn("Minimum investment of $1,000", extracted_fields[0].evidence_text_excerpt or "")

    def test_withdrawal_percentage_is_not_an_interest_rate(self) -> None:
        context = ExtractionDocumentContext(
            source_id="AUTO-BANK-GIC-001",
            parsed_document_id="parsed-gic-withdrawal",
            source_document_id="src-gic-withdrawal",
            snapshot_id="snap-gic-withdrawal",
            bank_code="BANK",
            country_code="CA",
            source_type="html",
            source_language="en",
            source_metadata={"product_type": "gic", "product_name": "EasyBuilder GIC"},
        )

        rate, *_ = _extract_candidate_value(
            context=context,
            field_name="standard_rate",
            excerpt="Each year, you can withdraw 20% of your initial investment without penalty.",
            anchor_value="Withdrawals",
        )

        self.assertIsNone(rate)

    def test_multi_term_list_is_preserved_as_text_and_not_collapsed_to_longest_term(self) -> None:
        context = ExtractionDocumentContext(
            source_id="AUTO-BANK-GIC-001",
            parsed_document_id="parsed-gic-terms",
            source_document_id="src-gic-terms",
            snapshot_id="snap-gic-terms",
            bank_code="BANK",
            country_code="CA",
            source_type="html",
            source_language="en",
            source_metadata={"product_type": "gic"},
        )
        excerpt = "Terms: 1, 2, 3, 4, 5, 10, 15 and 20-year terms available."
        term_text, *_ = _extract_candidate_value(
            context=context, field_name="term_length_text", excerpt=excerpt, anchor_value="terms"
        )
        term_days, *_ = _extract_candidate_value(
            context=context, field_name="term_length_days", excerpt=excerpt, anchor_value="terms"
        )
        self.assertEqual(term_text, "1, 2, 3, 4, 5, 10, 15 and 20-year terms")
        self.assertIsNone(term_days)

    def test_overdraft_service_waiver_is_not_account_monthly_fee(self) -> None:
        context = ExtractionDocumentContext(
            source_id="AUTO-BANK-CHQ-001",
            parsed_document_id="parsed-overdraft-fee",
            source_document_id="src-overdraft-fee",
            snapshot_id="snap-overdraft-fee",
            bank_code="BANK",
            country_code="CA",
            source_type="html",
            source_language="en",
            source_metadata={"product_type": "chequing", "product_name": "Smart Account"},
        )

        fee, *_ = _extract_candidate_value(
            context=context,
            field_name="monthly_fee",
            excerpt="Monthly fixed fee for Overdraft Protection Service: waived.",
            anchor_value="Overdraft protection",
        )

        self.assertIsNone(fee)

    def test_monthly_fee_label_does_not_capture_waiver_balance_or_annual_credit(self) -> None:
        context = ExtractionDocumentContext(
            source_id="AUTO-BANK-CHQ-001",
            parsed_document_id="parsed-fee-boundary",
            source_document_id="src-fee-boundary",
            snapshot_id="snap-fee-boundary",
            bank_code="BANK",
            country_code="CA",
            source_type="html",
            source_language="en",
            source_metadata={"product_type": "chequing", "product_name": "Basic Account"},
        )
        for excerpt in (
            "Monthly account fee waived if the minimum daily closing balance is $4,000.",
            "$60 annual safety deposit box credit. Monthly fee waived for eligible customers.",
        ):
            with self.subTest(excerpt=excerpt):
                fee, *_ = _extract_candidate_value(
                    context=context, field_name="monthly_fee", excerpt=excerpt, anchor_value="fees"
                )
                self.assertIsNone(fee)

    def test_conditional_zero_rebate_is_not_the_standard_monthly_fee(self) -> None:
        context = ExtractionDocumentContext(
            source_id="AUTO-BANK-CHQ-ADVANTAGE",
            parsed_document_id="parsed-advantage",
            source_document_id="src-advantage",
            snapshot_id="snap-advantage",
            bank_code="BANK",
            country_code="CA",
            source_type="html",
            source_language="en",
            source_metadata={"product_type": "chequing", "product_name": "Advantage Banking Account"},
        )
        conditional, *_ = _extract_candidate_value(
            context=context,
            field_name="monthly_fee",
            excerpt="Monthly fee as low as $0 with the Value Program Rebate.",
            anchor_value="fees",
        )
        standard, *_ = _extract_candidate_value(
            context=context,
            field_name="monthly_fee",
            excerpt="The standard monthly fee for the Advantage Banking Account is $12.95.",
            anchor_value="faq",
        )
        self.assertIsNone(conditional)
        self.assertEqual(standard, "12.95")

    def test_monthly_fee_match_prefers_target_product_identity_over_adjacent_product(self) -> None:
        context = ExtractionDocumentContext(
            source_id="AUTO-BANK-CHQ-DAY",
            parsed_document_id="parsed-day",
            source_document_id="src-day",
            snapshot_id="snap-day",
            bank_code="BANK",
            country_code="CA",
            source_type="html",
            source_language="en",
            source_metadata={
                "product_type": "chequing",
                "discovery_metadata": {
                    "primary_heading": "Day to Day Banking Account",
                    "page_title": "Day to Day Banking Account | Example Bank",
                },
            },
        )
        excerpts = {
            "chunk-adjacent": "VIP Banking Account Monthly Fee: $30 per month.",
            "chunk-target": "Day to Day Banking Account. The standard monthly fee is $4 per month.",
        }
        candidate_map = {
            chunk_id: EvidenceChunkCandidate(
                evidence_chunk_id=chunk_id,
                parsed_document_id="parsed-day",
                chunk_index=index,
                anchor_type="section",
                anchor_value="fees",
                page_no=None,
                source_language="en",
                evidence_excerpt=excerpt,
                retrieval_metadata={},
                source_document_id="src-day",
                source_snapshot_id="snap-day",
                bank_code="BANK",
                country_code="CA",
                source_type="html",
            )
            for index, (chunk_id, excerpt) in enumerate(excerpts.items())
        }
        matches = [
            EvidenceMatch(
                evidence_chunk_id=chunk_id,
                field_name="monthly_fee",
                score=0.98 if chunk_id == "chunk-adjacent" else 0.80,
                retrieval_mode="metadata-only",
                evidence_text_excerpt=excerpt,
                source_document_id="src-day",
                source_snapshot_id="snap-day",
                model_execution_id=None,
                parsed_document_id="parsed-day",
                anchor_type="section",
                anchor_value="fees",
                page_no=None,
                chunk_index=index,
                match_metadata={"matched_keywords": ["monthly fee"]},
            )
            for index, (chunk_id, excerpt) in enumerate(excerpts.items())
        ]
        field = _extract_from_matches(
            context=context,
            field_name="monthly_fee",
            matches=matches,
            candidate_map=candidate_map,
        )
        self.assertIsNotNone(field)
        assert field is not None
        self.assertEqual(field.candidate_value, "4.00")
        self.assertEqual(field.evidence_chunk_id, "chunk-target")

    def test_monthly_fee_match_rejects_explicitly_named_other_bank_product(self) -> None:
        context = ExtractionDocumentContext(
            source_id="AUTO-RBC-CHQ-VIP",
            parsed_document_id="parsed-vip",
            source_document_id="src-vip",
            snapshot_id="snap-vip",
            bank_code="RBC",
            country_code="CA",
            source_type="html",
            source_language="en",
            source_metadata={
                "product_type": "chequing",
                "discovery_metadata": {
                    "primary_heading": "RBC VIP Banking Account",
                    "page_title": "RBC VIP Banking Account - RBC Royal Bank",
                },
            },
        )
        excerpts = {
            "chunk-other": "The standard Monthly Fee for the RBC Advantage Banking account is $12.95.",
            "chunk-target": "Account Fees Monthly Fee $30/month with the Value Program rebate.",
        }
        candidate_map = {
            chunk_id: EvidenceChunkCandidate(
                evidence_chunk_id=chunk_id,
                parsed_document_id="parsed-vip",
                chunk_index=index,
                anchor_type="section",
                anchor_value="fees",
                page_no=None,
                source_language="en",
                evidence_excerpt=excerpt,
                retrieval_metadata={},
                source_document_id="src-vip",
                source_snapshot_id="snap-vip",
                bank_code="RBC",
                country_code="CA",
                source_type="html",
            )
            for index, (chunk_id, excerpt) in enumerate(excerpts.items())
        }
        matches = [
            EvidenceMatch(
                evidence_chunk_id=chunk_id,
                field_name="monthly_fee",
                score=0.99 if chunk_id == "chunk-other" else 0.80,
                retrieval_mode="metadata-only",
                evidence_text_excerpt=excerpt,
                source_document_id="src-vip",
                source_snapshot_id="snap-vip",
                model_execution_id=None,
                parsed_document_id="parsed-vip",
                anchor_type="section",
                anchor_value="fees",
                page_no=None,
                chunk_index=index,
                match_metadata={"matched_keywords": ["monthly fee"]},
            )
            for index, (chunk_id, excerpt) in enumerate(excerpts.items())
        ]

        field = _extract_from_matches(
            context=context,
            field_name="monthly_fee",
            matches=matches,
            candidate_map=candidate_map,
        )

        self.assertIsNotNone(field)
        assert field is not None
        self.assertEqual(field.candidate_value, "30.00")
        self.assertEqual(field.evidence_chunk_id, "chunk-target")

    def test_included_transactions_does_not_use_promotion_duration(self) -> None:
        context = ExtractionDocumentContext(
            source_id="AUTO-RBC-CHQ-ADVANTAGE",
            parsed_document_id="parsed-advantage",
            source_document_id="src-advantage",
            snapshot_id="snap-advantage",
            bank_code="RBC",
            country_code="CA",
            source_type="html",
            source_language="en",
            source_metadata={"product_type": "chequing", "product_name": "RBC Advantage Banking Account"},
        )
        value, *_ = _extract_candidate_value(
            context=context,
            field_name="included_transactions",
            excerpt=(
                "We will refund your monthly fees for up to 3 months. "
                "International money transfers and Interac transactions are also available."
            ),
            anchor_value="fees-and-other-benefits",
        )

        self.assertIsNone(value)

    def test_included_transactions_fallback_recovers_explicit_monthly_debit_count(self) -> None:
        context = ExtractionDocumentContext(
            source_id="RBC-CHQ-002",
            parsed_document_id="parsed-day",
            source_document_id="src-day",
            snapshot_id="snap-day",
            bank_code="RBC",
            country_code="CA",
            source_type="html",
            source_language="en",
            source_metadata={"product_type": "chequing", "product_name": "RBC Day to Day Banking Account"},
        )
        candidates = [
            EvidenceChunkCandidate(
                evidence_chunk_id="chunk-day-transactions",
                parsed_document_id="parsed-day",
                chunk_index=7,
                anchor_type="section",
                anchor_value="enjoy-12-included-debit-transactions",
                page_no=None,
                source_language="en",
                evidence_excerpt=(
                    "Enjoy 12 included debit transactions. "
                    "RBC Day to Day Banking provides 12 debit transactions each month."
                ),
                retrieval_metadata={},
                source_document_id="src-day",
                source_snapshot_id="snap-day",
                bank_code="RBC",
                country_code="CA",
                source_type="html",
            )
        ]
        extracted: list[ExtractedFieldCandidate] = []

        _append_included_transactions_fallback(
            context=context,
            candidates=candidates,
            requested_fields={"included_transactions"},
            extracted_fields=extracted,
        )

        self.assertEqual(len(extracted), 1)
        self.assertEqual(extracted[0].candidate_value, 12)
        self.assertEqual(extracted[0].evidence_chunk_id, "chunk-day-transactions")

    def test_comparison_table_footnotes_do_not_become_transaction_counts(self) -> None:
        context = ExtractionDocumentContext(
            source_id="AUTO-BANK-CHQ-BASIC",
            parsed_document_id="parsed-basic",
            source_document_id="src-basic",
            snapshot_id="snap-basic",
            bank_code="BANK",
            country_code="CA",
            source_type="html",
            source_language="en",
            source_metadata={"product_type": "chequing", "product_name": "Basic Chequing Account"},
        )
        cases = (
            (
                "Monthly Fee\n$3.95\nTransactions included per month 2 , 3\n12\nAdditional transaction Fee\n$1.25 each",
                12,
            ),
            (
                "Monthly Fee $11.95 or $0 2\nTransactions 2 included per month plus unlimited public transit transactions 8\n25",
                25,
            ),
            ("benefits 18 free transactions 2 per month Free Interac e-Transfer transactions", 18),
            ("benefits 25 free debit transactions 1 per month", 25),
        )
        for excerpt, expected in cases:
            with self.subTest(expected=expected):
                value, *_ = _extract_candidate_value(
                    context=context,
                    field_name="included_transactions",
                    excerpt=excerpt,
                    anchor_value="account fees",
                )
            self.assertEqual(value, expected)

    def test_unlimited_activity_list_is_account_wide_transactions(self) -> None:
        context = ExtractionDocumentContext(
            source_id="BANK-CHE-001",
            parsed_document_id="parsed-001",
            source_document_id="src-001",
            snapshot_id="snap-001",
            bank_code="BANK",
            country_code="CA",
            source_type="html",
            source_language="en",
            source_metadata={"product_type": "chequing", "product_name": "No Fee Chequing Account"},
        )

        value, *_ = _extract_candidate_value(
            context=context,
            field_name="unlimited_transactions_flag",
            excerpt="Enjoy unlimited debit purchases, bill payments and withdrawals.",
            anchor_value="Benefits and features",
        )

        self.assertTrue(value)

    def test_title_cleanup_removes_bank_brand_suffix(self) -> None:
        self.assertEqual(
            _clean_title_candidate("No Fee Chequing Account | Simplii Financial"),
            "No Fee Chequing Account",
        )
        self.assertEqual(
            _clean_title_candidate("GICs | Investments | Simplii Financial"),
            "GICs",
        )
        self.assertEqual(
            _clean_title_candidate("Accounts High Interest Savings Account"),
            "High Interest Savings Account",
        )
        self.assertEqual(
            _clean_title_candidate("Accounts Simplii Financial™ USD Savings Account"),
            "Simplii Financial™ USD Savings Account",
        )
        self.assertEqual(_clean_title_candidate("CIBC EasyBuilder GIC⑩"), "CIBC EasyBuilder GIC")
        self.assertEqual(_clean_title_candidate("CIBC Flexible GIC㈢"), "CIBC Flexible GIC")

    def test_included_transactions_accepts_legal_marker_before_per_month(self) -> None:
        self.assertEqual(_extract_included_transactions("6 Debits legal disclaimer 1 / Month"), 6)

    def test_application_and_program_copy_is_not_product_eligibility(self) -> None:
        self.assertIsNone(
            _extract_eligibility_text(
                "To apply, you’ll need: A valid ID and your personal information including employment status."
            )
        )
        self.assertIsNone(
            _extract_eligibility_text(
                "If you already have an eligible account, sign in to activate the Value Program."
            )
        )

    def test_sibling_gic_disclosure_is_not_a_product_description(self) -> None:
        context = ExtractionDocumentContext(
            source_id="BANK-GIC-INTEREST-LINKED",
            parsed_document_id="parsed-interest-linked",
            source_document_id="src-interest-linked",
            snapshot_id="snap-interest-linked",
            bank_code="BANK",
            country_code="CA",
            source_type="html",
            source_language="en",
            source_metadata={"product_type": "gic", "product_name": "Interest-Linked GIC"},
        )
        self.assertTrue(
            _looks_like_non_product_summary(
                context=context,
                value=(
                    "Funds are available after redemption, or in the case of Another Income Builder GIC, "
                    "after its payment date."
                ),
            )
        )

    def test_savings_support_fields_drop_navigation_referral_template_and_cross_sell_noise(self) -> None:
        context = ExtractionDocumentContext(
            source_id="AUTO-BANK-SAV-HISA",
            parsed_document_id="parsed-savings",
            source_document_id="src-savings",
            snapshot_id="snap-savings",
            bank_code="BANK",
            country_code="CA",
            source_type="html",
            source_language="en",
            source_metadata={"product_type": "savings", "product_name": "High Interest Savings Account"},
        )

        self.assertTrue(_looks_like_navigation_description("Accounts"))
        self.assertTrue(_looks_like_navigation_description("Save"))
        self.assertIsNone(
            _extract_eligibility_text(
                "Open a High Interest Savings Account or another eligible account using your unique referral link."
            )
        )
        self.assertIsNone(_extract_eligibility_text("Need to send U.S. dollars for free"))
        self.assertIsNone(_extract_eligibility_text("Earn rewards on eligible transactions you make with the account"))
        self.assertIsNone(
            _extract_eligibility_text(
                "For a limited time, open and fund a new account, then complete the qualifying activities."
            )
        )
        self.assertIsNone(
            _extract_notes_text(
                "Important banking info We use cookies, tracking tools and webforms on our digital properties."
            )
        )
        self.assertEqual(
            _extract_interest_calculation_method(
                "ished(undefined, annual_rate)(#O2#)% Interest is calculated on the daily closing balance and paid monthly."
            ),
            "Interest is calculated on the daily closing balance and paid monthly.",
        )
        self.assertIsNone(
            _extract_withdrawal_limit_text(
                context=context,
                text=(
                    "For day-to-day banking, try our No Fee Chequing Account with free ATM withdrawals."
                ),
            )
        )
        self.assertEqual(
            _extract_withdrawal_limit_text(
                context=context,
                text="Cash deposits and withdrawals are not available for this account.",
            ),
            "Cash deposits and withdrawals are not available for this account.",
        )
        self.assertEqual(
            _extract_withdrawal_limit_text(
                context=context,
                text=(
                    "Features Details Monthly fee $0 Withdrawal $5 Funds transfer (Digital and ATM) $0 "
                    "Funds transfer (Branch and associate) $5 We use cookies and tracking tools."
                ),
            ),
            "Withdrawal fee: $5.",
        )
        self.assertEqual(
            _extract_withdrawal_limit_text(
                context=context,
                text=(
                    "Number of transactions per month One eligible debit transaction per month at no cost. "
                    "$5 fee for each additional withdrawal."
                ),
            ),
            "One eligible debit transaction per month at no cost. $5 fee for each additional withdrawal.",
        )
        self.assertEqual(
            _extract_withdrawal_limit_text(
                context=context,
                text=(
                    "This depends on the bank plan for the chequing account. "
                    "Transaction limits are shared among these two accounts."
                ),
            ),
            "Transaction limits depend on and are shared with the paired account's bank plan.",
        )

    def test_registered_and_non_registered_savings_select_their_own_offer_terms(self) -> None:
        legal_text = (
            "The 4.60% Registered Promotional Rate will apply to eligible registered savings accounts "
            "for 153 days (5 months). "
            "The 4.50% Non-Registered Promotional Rate will apply to eligible Savings Accounts "
            "for 153 days (5 months)."
        )
        registered_context = ExtractionDocumentContext(
            source_id="AUTO-BANK-SAV-RSP",
            parsed_document_id="parsed-rsp",
            source_document_id="src-rsp",
            snapshot_id="snap-rsp",
            bank_code="BANK",
            country_code="CA",
            source_type="html",
            source_language="en",
            source_metadata={"product_type": "savings", "product_name": "RSP Savings Account"},
        )
        non_registered_context = ExtractionDocumentContext(
            source_id="AUTO-BANK-SAV-STANDARD",
            parsed_document_id="parsed-standard",
            source_document_id="src-standard",
            snapshot_id="snap-standard",
            bank_code="BANK",
            country_code="CA",
            source_type="html",
            source_language="en",
            source_metadata={"product_type": "savings", "product_name": "Savings Account"},
        )

        self.assertIn("4.60% Registered", _extract_promotional_period_text(context=registered_context, text=legal_text))
        self.assertIn("4.50% Non-Registered", _extract_promotional_period_text(context=non_registered_context, text=legal_text))
        self.assertIsNone(
            _extract_tax_benefits(
                context=registered_context,
                text="RSP Guaranteed Investment (GIC) combines guaranteed growth with the tax benefits of an RSP.",
            )
        )
        self.assertIsNone(
            _extract_withdrawal_limit_text(
                context=registered_context,
                text="RIF withdrawals and taxes Interest earned in your RIF isn't taxed.",
            )
        )

    def test_account_wide_unlimited_beats_footnote_numbers_but_transit_unlimited_does_not(self) -> None:
        context = ExtractionDocumentContext(
            source_id="AUTO-BANK-CHQ-UNLIMITED",
            parsed_document_id="parsed-unlimited",
            source_document_id="src-unlimited",
            snapshot_id="snap-unlimited",
            bank_code="BANK",
            country_code="CA",
            source_type="html",
            source_language="en",
            source_metadata={"product_type": "chequing", "product_name": "Unlimited Chequing Account"},
        )
        cases = (
            ("Transactions 3 included per month\nUnlimited", True),
            ("Transactions per month *52, *104\nUnlimited\n25", True),
            ("Peace of mind comes with unlimited everyday banking transactions.", True),
            ("25 transactions included per month plus unlimited public transit transactions.", False),
        )
        for excerpt, expected in cases:
            with self.subTest(excerpt=excerpt):
                value, *_ = _extract_candidate_value(
                    context=context,
                    field_name="unlimited_transactions_flag",
                    excerpt=excerpt,
                    anchor_value="account features",
                )
                self.assertEqual(value, expected)

    def test_evidence_wide_unlimited_fallback_recovers_explicit_account_benefit(self) -> None:
        context = ExtractionDocumentContext(
            source_id="AUTO-BANK-CHQ-PERFORMANCE",
            parsed_document_id="parsed-performance",
            source_document_id="src-performance",
            snapshot_id="snap-performance",
            bank_code="BANK",
            country_code="CA",
            source_type="html",
            source_language="en",
            source_metadata={"product_type": "chequing", "product_name": "Performance Chequing Account"},
        )
        candidate = EvidenceChunkCandidate(
            evidence_chunk_id="chunk-performance-unlimited",
            parsed_document_id="parsed-performance",
            chunk_index=4,
            anchor_type="section",
            anchor_value="benefits",
            page_no=None,
            source_language="en",
            evidence_excerpt=(
                "Performance Chequing Account Benefits Get unlimited transactions and Interac e-Transfer transactions."
            ),
            retrieval_metadata={},
            source_document_id="src-performance",
            source_snapshot_id="snap-performance",
            bank_code="BANK",
            country_code="CA",
            source_type="html",
        )
        extracted: list[ExtractedFieldCandidate] = []

        _append_unlimited_transactions_fallback(
            context=context,
            candidates=[candidate],
            requested_fields={"unlimited_transactions_flag"},
            extracted_fields=extracted,
        )

        self.assertEqual(len(extracted), 1)
        self.assertTrue(extracted[0].candidate_value)
        self.assertEqual(extracted[0].evidence_chunk_id, "chunk-performance-unlimited")

    def test_monthly_fee_fallback_recovers_strongly_labeled_detail_chunk(self) -> None:
        context = ExtractionDocumentContext(
            source_id="AUTO-BANK-CHQ-PREFERRED",
            parsed_document_id="parsed-preferred",
            source_document_id="src-preferred",
            snapshot_id="snap-preferred",
            bank_code="BANK",
            country_code="CA",
            source_type="html",
            source_language="en",
            source_metadata={"product_type": "chequing", "product_name": "Preferred Package"},
        )
        candidate = EvidenceChunkCandidate(
            evidence_chunk_id="chunk-fee",
            parsed_document_id="parsed-preferred",
            chunk_index=9,
            anchor_type="section",
            anchor_value="at-a-glance",
            page_no=None,
            source_language="en",
            evidence_excerpt=(
                "Monthly account fee $16.95 or $0 /month. Waive the monthly account fee when you "
                "hold $4,000 or more in this account every day. Total relationship balances may "
                "include savings accounts, GICs, and mutual funds."
            ),
            retrieval_metadata={},
            source_document_id="src-preferred",
            source_snapshot_id="snap-preferred",
            bank_code="BANK",
            country_code="CA",
            source_type="html",
        )
        discount_candidate = EvidenceChunkCandidate(
            evidence_chunk_id="chunk-senior-discount",
            parsed_document_id="parsed-preferred",
            chunk_index=21,
            anchor_type="section",
            anchor_value="benefits",
            page_no=None,
            source_language="en",
            evidence_excerpt=(
                "Preferred Package account holders receive benefits. Seniors aged 60 and up "
                "receive an automatic monthly account fee discount of up to $4."
            ),
            retrieval_metadata={},
            source_document_id="src-preferred",
            source_snapshot_id="snap-preferred",
            bank_code="BANK",
            country_code="CA",
            source_type="html",
        )
        extracted: list[ExtractedFieldCandidate] = []

        _append_monthly_fee_fallback(
            context=context,
            candidates=[discount_candidate, candidate],
            requested_fields={"monthly_fee", "public_display_fee"},
            extracted_fields=extracted,
        )

        self.assertEqual(
            {item.field_name: item.candidate_value for item in extracted},
            {"monthly_fee": "16.95", "public_display_fee": "16.95"},
        )
        self.assertTrue(all(item.evidence_chunk_id == "chunk-fee" for item in extracted))

    def test_monthly_fee_fallback_keeps_fee_beside_generic_bank_categories(self) -> None:
        context = ExtractionDocumentContext(
            source_id="AUTO-SCOTIA-CHQ-ULTIMATE",
            parsed_document_id="parsed-ultimate",
            source_document_id="src-ultimate",
            snapshot_id="snap-ultimate",
            bank_code="SCOTIA",
            country_code="CA",
            source_type="html",
            source_language="en",
            source_metadata={"product_type": "chequing", "product_name": "Ultimate Package"},
        )
        candidate = EvidenceChunkCandidate(
            evidence_chunk_id="chunk-ultimate-fee",
            parsed_document_id="parsed-ultimate",
            chunk_index=9,
            anchor_type="section",
            anchor_value="at-a-glance",
            page_no=None,
            source_language="en",
            evidence_excerpt=(
                "at a glance Monthly account fee $30.95 or $0 /month. Waive the monthly account fee "
                "when you hold $6,000 or more. The Total Relationship Balance includes eligible "
                "Scotiabank chequing accounts, savings accounts, guaranteed investment certificates, "
                "and mutual funds."
            ),
            retrieval_metadata={},
            source_document_id="src-ultimate",
            source_snapshot_id="snap-ultimate",
            bank_code="SCOTIA",
            country_code="CA",
            source_type="html",
        )
        extracted: list[ExtractedFieldCandidate] = []

        _append_monthly_fee_fallback(
            context=context,
            candidates=[candidate],
            requested_fields={"monthly_fee", "public_display_fee"},
            extracted_fields=extracted,
        )

        self.assertEqual(
            {item.field_name: item.candidate_value for item in extracted},
            {"monthly_fee": "30.95", "public_display_fee": "30.95"},
        )

    def test_monthly_fee_fallback_stops_before_cross_product_faq_lineup(self) -> None:
        context = ExtractionDocumentContext(
            source_id="AUTO-BANK-SAV-PREMIUM",
            parsed_document_id="parsed-premium",
            source_document_id="src-premium",
            snapshot_id="snap-premium",
            bank_code="BANK",
            country_code="CA",
            source_type="html",
            source_language="en",
            source_metadata={"product_type": "savings", "product_name": "Premium Savings Account"},
        )
        candidate = EvidenceChunkCandidate(
            evidence_chunk_id="chunk-premium-faq",
            parsed_document_id="parsed-premium",
            chunk_index=24,
            anchor_type="section",
            anchor_value="transaction-limits",
            page_no=None,
            source_language="en",
            evidence_excerpt=(
                "What are the transaction limits of a Premium Savings Account? This depends on the paired bank plan. "
                "What type of savings accounts does Example Bank offer? Example Bank offers several savings accounts, "
                "including Basic Savings with no monthly fees."
            ),
            retrieval_metadata={},
            source_document_id="src-premium",
            source_snapshot_id="snap-premium",
            bank_code="BANK",
            country_code="CA",
            source_type="html",
        )
        extracted: list[ExtractedFieldCandidate] = []

        _append_monthly_fee_fallback(
            context=context,
            candidates=[candidate],
            requested_fields={"monthly_fee", "public_display_fee"},
            extracted_fields=extracted,
        )

        self.assertEqual(extracted, [])

    def test_description_prefers_complete_hero_over_application_faq_and_truncated_card(self) -> None:
        context = ExtractionDocumentContext(
            source_id="AUTO-BANK-SAV-PREMIUM",
            parsed_document_id="parsed-premium",
            source_document_id="src-premium",
            snapshot_id="snap-premium",
            bank_code="BANK",
            country_code="CA",
            source_type="html",
            source_language="en",
            source_metadata={"product_type": "savings", "product_name": "Premium Savings Account"},
        )

        def candidate(chunk_id: str, index: int, excerpt: str) -> EvidenceChunkCandidate:
            return EvidenceChunkCandidate(
                evidence_chunk_id=chunk_id,
                parsed_document_id="parsed-premium",
                chunk_index=index,
                anchor_type="section",
                anchor_value=chunk_id,
                page_no=None,
                source_language="en",
                evidence_excerpt=excerpt,
                retrieval_metadata={},
                source_document_id="src-premium",
                source_snapshot_id="snap-premium",
                bank_code="BANK",
                country_code="CA",
                source_type="html",
            )

        description = _extract_description(
            context=context,
            candidates=[
                candidate(
                    "hero",
                    1,
                    "Premium Savings Account\nA flexible account that pairs seamlessly with a chequing plan.\nOpen Account",
                ),
                candidate(
                    "flattened-card",
                    2,
                    "Benefits\nGet a bonus interest rate for adding funds every month and enjoy one eligible debit transaction "
                    "at no cost while using transfers to another account and several other account features that are flattened "
                    "from a comparison card before the parser cuts the final Intera",
                ),
                candidate(
                    "faq",
                    20,
                    "Can I open the account online?\nYes, you can.\nIf you’re an existing bank customer, you can sign in to Online Banking "
                    "to add the Premium Savings Account.",
                ),
            ],
        )

        self.assertEqual(description, "A flexible account that pairs seamlessly with a chequing plan.")

    def test_holding_balance_waiver_outranks_no_opening_minimum(self) -> None:
        context = ExtractionDocumentContext(
            source_id="AUTO-BANK-CHQ-ULTIMATE",
            parsed_document_id="parsed-ultimate",
            source_document_id="src-ultimate",
            snapshot_id="snap-ultimate",
            bank_code="BANK",
            country_code="CA",
            source_type="html",
            source_language="en",
            source_metadata={"product_type": "chequing", "product_name": "Ultimate Package"},
        )
        excerpt = (
            "There's no minimum balance required to open an Ultimate Package. At a glance: "
            "Monthly account fee $30.95 or $0 /month. You can waive the monthly account fee "
            "by holding a minimum balance. You'll pay no monthly account fee by holding "
            "$6,000 or more every day for the entire month."
        )
        minimum_balance, *_ = _extract_candidate_value(
            context=context, field_name="minimum_balance", excerpt=excerpt, anchor_value="minimum balance"
        )
        monthly_fee, *_ = _extract_candidate_value(
            context=context, field_name="monthly_fee", excerpt=excerpt, anchor_value="monthly fee"
        )
        waiver, *_ = _extract_candidate_value(
            context=context, field_name="fee_waiver_condition", excerpt=excerpt, anchor_value="monthly fee"
        )
        self.assertEqual(minimum_balance, "6000.00")
        self.assertEqual(monthly_fee, "30.95")
        self.assertEqual(waiver, "Monthly fee 30.95 is waived to 0.00 with a 6000.00 minimum balance.")

        compact_excerpt = "$30.95 or $0 (with a minimum daily account balance of $6,000)."
        compact_monthly_fee, *_ = _extract_candidate_value(
            context=context, field_name="monthly_fee", excerpt=compact_excerpt, anchor_value="monthly fee"
        )
        compact_balance, *_ = _extract_candidate_value(
            context=context, field_name="minimum_balance", excerpt=compact_excerpt, anchor_value="monthly fee"
        )
        compact_waiver, *_ = _extract_candidate_value(
            context=context, field_name="fee_waiver_condition", excerpt=compact_excerpt, anchor_value="monthly fee"
        )
        self.assertEqual(compact_monthly_fee, "30.95")
        self.assertEqual(compact_balance, "6000.00")
        self.assertEqual(compact_waiver, "Monthly fee 30.95 is waived to 0.00 with a 6000.00 minimum balance.")

    def test_monthly_fee_match_uses_distinctive_product_token_over_audience_offer(self) -> None:
        context = ExtractionDocumentContext(
            source_id="AUTO-BANK-CHQ-PERFORMANCE",
            parsed_document_id="parsed-performance",
            source_document_id="src-performance",
            snapshot_id="snap-performance",
            bank_code="BANK",
            country_code="CA",
            source_type="html",
            source_language="en",
            source_metadata={
                "product_type": "chequing",
                "discovery_metadata": {
                    "primary_heading": "Performance Chequing Account",
                    "page_title": "Performance Chequing Account - Unlimited Transactions - Example Bank",
                },
            },
        )
        excerpts = {
            "chunk-offer": "Indigenous customers enjoy banking with no monthly plan fee for a year.",
            "chunk-fee": "Performance monthly plan fee $17.95 or $0/month with a $4,000 minimum balance.",
        }
        candidate_map = {
            chunk_id: EvidenceChunkCandidate(
                evidence_chunk_id=chunk_id,
                parsed_document_id="parsed-performance",
                chunk_index=index,
                anchor_type="section",
                anchor_value="fees",
                page_no=None,
                source_language="en",
                evidence_excerpt=excerpt,
                retrieval_metadata={},
                source_document_id="src-performance",
                source_snapshot_id="snap-performance",
                bank_code="BANK",
                country_code="CA",
                source_type="html",
            )
            for index, (chunk_id, excerpt) in enumerate(excerpts.items())
        }
        matches = [
            EvidenceMatch(
                evidence_chunk_id=chunk_id,
                field_name="monthly_fee",
                score=0.98 if chunk_id == "chunk-offer" else 0.80,
                retrieval_mode="metadata-only",
                evidence_text_excerpt=excerpt,
                source_document_id="src-performance",
                source_snapshot_id="snap-performance",
                model_execution_id=None,
                parsed_document_id="parsed-performance",
                anchor_type="section",
                anchor_value="fees",
                page_no=None,
                chunk_index=index,
                match_metadata={"matched_keywords": ["monthly fee"]},
            )
            for index, (chunk_id, excerpt) in enumerate(excerpts.items())
        ]

        field = _extract_from_matches(
            context=context,
            field_name="monthly_fee",
            matches=matches,
            candidate_map=candidate_map,
        )

        self.assertIsNotNone(field)
        assert field is not None
        self.assertEqual(field.candidate_value, "17.95")
        self.assertEqual(field.evidence_chunk_id, "chunk-fee")

    def test_fee_extraction_does_not_treat_waiver_balance_as_monthly_fee(self) -> None:
        context = ExtractionDocumentContext(
            source_id="BMO-CHQ-005",
            parsed_document_id="parsed-premium",
            source_document_id="src-premium",
            snapshot_id="snap-premium",
            bank_code="BMO",
            country_code="CA",
            source_type="html",
            source_language="en",
            source_metadata={"product_type": "chequing"},
        )

        fee, *_ = _extract_candidate_value(
            context=context,
            field_name="monthly_fee",
            excerpt=(
                "BMO Premium Chequing Account. There is no minimum balance required. "
                "If you maintain at least $6,000 in the account, we will waive the monthly account fee."
            ),
            anchor_value="required-minimum-balance",
        )

        self.assertIsNone(fee)

    def test_no_required_minimum_does_not_capture_nearby_monthly_fee(self) -> None:
        context = ExtractionDocumentContext(
            source_id="BMO-CHQ-008",
            parsed_document_id="parsed-blue",
            source_document_id="src-blue",
            snapshot_id="snap-blue",
            bank_code="BMO",
            country_code="CA",
            source_type="html",
            source_language="en",
            source_metadata={"product_type": "chequing"},
        )

        balance, *_ = _extract_candidate_value(
            context=context,
            field_name="minimum_balance",
            excerpt=(
                "You do not need to keep a minimum balance in the account as long as you pay "
                "the monthly plan fee of $17.95. You can earn points with a $4,000 daily balance."
            ),
            anchor_value="required-minimum-balance",
        )

        self.assertEqual(balance, "0.00")

    def test_hyphenated_no_monthly_fee_beats_adjacent_cash_bonus_for_target_youth_account(self) -> None:
        context = ExtractionDocumentContext(
            source_id="AUTO-BANK-CHQ-YOUTH",
            parsed_document_id="parsed-youth",
            source_document_id="src-youth",
            snapshot_id="snap-youth",
            bank_code="BANK",
            country_code="CA",
            source_type="html",
            source_language="en",
            source_metadata={
                "product_type": "chequing",
                "discovery_metadata": {
                    "primary_heading": "A Bank Account for Youth Under 25",
                    "page_title": "A Bank Account for Youth Under 25 | Example Bank",
                },
            },
        )

        fee, *_ = _extract_candidate_value(
            context=context,
            field_name="monthly_fee",
            excerpt="Under 25? Enjoy no-monthly fee everyday banking. Get $175 Cash and a free membership.",
            anchor_value="youth-account",
        )

        self.assertEqual(fee, "0.00")

    def test_no_monthly_fees_beats_direct_deposit_offer_threshold(self) -> None:
        context = ExtractionDocumentContext(
            source_id="AUTO-SIMPLII-CHQ-NO-FEE",
            parsed_document_id="parsed-simplii-chequing",
            source_document_id="src-simplii-chequing",
            snapshot_id="snap-simplii-chequing",
            bank_code="SIMPLII",
            country_code="CA",
            source_type="html",
            source_language="en",
            source_metadata={
                "product_type": "chequing",
                "discovery_metadata": {"primary_heading": "No Fee Chequing Account"},
            },
        )

        fee, *_ = _extract_candidate_value(
            context=context,
            field_name="monthly_fee",
            excerpt=(
                "Earn $300 and a $50 gift card. Open a No Fee Chequing Account and set up an "
                "eligible direct deposit today of $100 or more for 3 straight months. Plus, "
                "you'll pay no monthly fees."
            ),
            anchor_value="earn-300",
        )

        self.assertEqual(fee, "0.00")

    def test_temporary_zero_fee_period_is_not_the_base_monthly_fee(self) -> None:
        context = ExtractionDocumentContext(
            source_id="AUTO-BANK-CHQ-NEWCOMER",
            parsed_document_id="parsed-newcomer",
            source_document_id="src-newcomer",
            snapshot_id="snap-newcomer",
            bank_code="BANK",
            country_code="CA",
            source_type="html",
            source_language="en",
            source_metadata={
                "product_type": "chequing",
                "discovery_metadata": {"primary_heading": "Smart Account for Newcomers"},
            },
        )

        fee, *_ = _extract_candidate_value(
            context=context,
            field_name="monthly_fee",
            excerpt="$0 monthly fee for 2 years when you start banking in Canada.",
            anchor_value="newcomer-offer",
        )

        self.assertIsNone(fee)

    def test_investment_cross_sell_does_not_supply_chequing_minimum_balance(self) -> None:
        context = ExtractionDocumentContext(
            source_id="AUTO-BANK-CHQ-YOUTH",
            parsed_document_id="parsed-youth-investing",
            source_document_id="src-youth-investing",
            snapshot_id="snap-youth-investing",
            bank_code="BANK",
            country_code="CA",
            source_type="html",
            source_language="en",
            source_metadata={"product_type": "chequing", "product_name": "Youth Chequing Account"},
        )

        balance, *_ = _extract_candidate_value(
            context=context,
            field_name="minimum_balance",
            excerpt=(
                "Trade your way to the future with free stock and ETF trading through Investor's Edge. "
                "There is no minimum balance and no annual fee."
            ),
            anchor_value="investing-offer",
        )

        self.assertIsNone(balance)

    def test_unlimited_e_transfers_do_not_mean_unlimited_debit_transactions(self) -> None:
        context = ExtractionDocumentContext(
            source_id="AUTO-BANK-CHQ-DAY",
            parsed_document_id="parsed-day",
            source_document_id="src-day",
            snapshot_id="snap-day",
            bank_code="BANK",
            country_code="CA",
            source_type="html",
            source_language="en",
            source_metadata={"product_type": "chequing"},
        )
        value, *_ = _extract_candidate_value(
            context=context,
            field_name="unlimited_transactions_flag",
            excerpt="Includes 12 debit transactions and unlimited Interac e-Transfer transactions.",
            anchor_value="features",
        )
        self.assertFalse(value)

    def test_audience_cross_sell_does_not_set_product_flag(self) -> None:
        context = ExtractionDocumentContext(
            source_id="AUTO-BANK-CHQ-001",
            parsed_document_id="parsed-audience-cross-sell",
            source_document_id="src-audience-cross-sell",
            snapshot_id="snap-audience-cross-sell",
            bank_code="BANK",
            country_code="CA",
            source_type="html",
            source_language="en",
            source_metadata={"product_type": "chequing", "product_name": "Smart Account", "source_name": "Smart Account"},
        )

        student, *_ = _extract_candidate_value(
            context=context,
            field_name="student_plan_flag",
            excerpt="Explore our student chequing account.",
            anchor_value="Other accounts",
        )

        student_section, *_ = _extract_candidate_value(
            context=context,
            field_name="student_plan_flag",
            excerpt="Students age 25 and up Unlimited everyday banking for full-time students.",
            anchor_value="students-age-25-and-up",
        )
        newcomer_section, *_ = _extract_candidate_value(
            context=context,
            field_name="newcomer_plan_flag",
            excerpt="New to Canada Pay no monthly fee for 2 years.",
            anchor_value="new-to-canada",
        )

        self.assertIsNone(student)
        self.assertIsNone(student_section)
        self.assertIsNone(newcomer_section)
        self.assertTrue(_looks_like_navigation_description("Chequing Accounts"))
        self.assertTrue(_looks_like_navigation_description("OverviewFees and details"))
        self.assertEqual(
            _extract_eligibility_text(
                "You're a Canadian resident and you've reached the age omajority in your province or territory "
                "Regular Interest rate 0.05% to 0.25%."
            ),
            "You're a Canadian resident and you've reached the age of majority in your province or territory",
        )
        self.assertIsNone(_extract_deposit_insurance("Corporation (CDIC)."))
        self.assertEqual(
            _extract_deposit_insurance("Eligible deposits are insured by CDIC."),
            "Eligible deposits are insured by CDIC.",
        )
        self.assertEqual(
            _extract_included_transactions(
                "For a low monthly fee, you'll get 18 transactionsⓘ, ⓘ included each month."
            ),
            18,
        )
        self.assertIsNone(
            _extract_application_method(
                "Apply now Get more savings with your cash back gift certificate. "
                "Redeem your annual gift certificate using the mobile app."
            )
        )
        self.assertEqual(
            _extract_application_method("Apply online, by phone, or book an appointment at a branch."),
            "Apply online, by phone, or book an appointment at a branch.",
        )

    def test_current_product_audience_entitlements_set_flags_without_cross_sell_leakage(self) -> None:
        context = ExtractionDocumentContext(
            source_id="AUTO-BANK-CHQ-ADV",
            parsed_document_id="parsed-adv",
            source_document_id="src-adv",
            snapshot_id="snap-adv",
            bank_code="BANK",
            country_code="CA",
            source_type="html",
            source_language="en",
            source_metadata={
                "product_type": "chequing",
                "discovery_metadata": {
                    "page_title": "Advantage Banking Account | Example Bank",
                    "primary_heading": "Advantage Banking Account",
                },
            },
        )
        excerpt = (
            "The Advantage Banking Account has no monthly fees for eligible full-time students and anyone "
            "24 and younger, as well as eligible newcomers for their first year."
        )

        student, *_ = _extract_candidate_value(
            context=context, field_name="student_plan_flag", excerpt=excerpt, anchor_value="frequently-asked-questions"
        )
        newcomer, *_ = _extract_candidate_value(
            context=context, field_name="newcomer_plan_flag", excerpt=excerpt, anchor_value="frequently-asked-questions"
        )

        self.assertTrue(student)
        self.assertTrue(newcomer)

    def test_legal_account_enumeration_does_not_set_audience_flag(self) -> None:
        context = ExtractionDocumentContext(
            source_id="AUTO-SCOTIA-CHQ-ULTIMATE",
            parsed_document_id="parsed-ultimate",
            source_document_id="src-ultimate",
            snapshot_id="snap-ultimate",
            bank_code="SCOTIA",
            country_code="CA",
            source_type="html",
            source_language="en",
            source_metadata={
                "product_type": "chequing",
                "product_name": "Ultimate Package",
                "page_title": "Ultimate Package | Scotiabank Canada",
                "primary_heading": "Ultimate Package",
            },
        )
        excerpt = (
            "Offer Eligibility and Exclusions. Scotiabank Chequing Account means any of the following "
            "accounts: Ultimate Package, Preferred Package, Basic Bank Account, and Student Banking "
            "Advantage Plan. These accounts may be eligible for the package bonus."
        )

        student, *_ = _extract_candidate_value(
            context=context,
            field_name="student_plan_flag",
            excerpt=excerpt,
            anchor_value="legal-1",
        )

        self.assertIsNone(student)

        long_excerpt = (
            "Offer Eligibility and Exclusions. Scotiabank Chequing Account means any of the following accounts: "
            "Ultimate Package, Preferred Package, Scotia One Account, Basic Plus Bank Account, Basic Banking Plan. "
            + "Prior-holder and package-bonus conditions apply. " * 30
            + "Student Banking Advantage Plan."
        )
        student, *_ = _extract_candidate_value(
            context=context,
            field_name="student_plan_flag",
            excerpt=long_excerpt,
            anchor_value="legal-7",
        )
        self.assertIsNone(student)

    def test_eligibility_rejects_application_channels_fee_rebates_and_shared_disclosures(self) -> None:
        self.assertIsNone(
            _extract_eligibility_text(
                "You can open this account online via Online Banking or the mobile app, or in person at a branch."
            )
        )
        self.assertIsNone(
            _extract_eligibility_text(
                "You may be eligible to receive a full rebate on your monthly fee through the Value Program Rebate."
            )
        )
        self.assertIsNone(
            _extract_eligibility_text(
                "The account owner must provide proof of eligibility under the Commitment on Low-Cost and No-Cost Accounts."
            )
        )
        self.assertIsNone(
            _extract_eligibility_text(
                "Subject to approval. A customer must apply for an Overdraft Protection Plan to determine if they qualify."
            )
        )
        self.assertIsNone(
            _extract_eligibility_text(
                "To qualify for these offers, open a new credit card account between July 2 and November 1 and make eligible purchases."
            )
        )
        self.assertIsNone(
            _extract_eligibility_text(
                "Cardholders who link their card and Scene account to a Shell Go+ Account can get fuel discounts."
            )
        )
        self.assertIsNone(
            _extract_eligibility_text(
                "Benefits: 18 free transactions per month, free Interac e-Transfer transactions, "
                "eligible for overdraft protection, and fuel savings."
            )
        )
        self.assertIsNone(
            _extract_eligibility_text(
                "The Cash Bonus Bundle Offer is available during the Offer Period when clients open "
                "a chequing account and complete certain qualifying transactions."
            )
        )
        self.assertIsNone(
            _extract_eligibility_text(
                "Account holders receive a waiver of commission on eligible commissionable trades."
            )
        )
        self.assertIsNone(
            _extract_eligibility_text(
                "To qualify for these offers make sure to open a new Example Rewards credit card account "
                "between July 2, 2026 and November 1, 2026."
            )
        )
        self.assertIsNone(
            _extract_application_method(
                "Questions: To activate a Visa or American Express card, use the online activation page or insert your card and enter your PIN."
            )
        )
        self.assertTrue(_looks_like_navigation_description("Special offer"))

    def test_slash_month_debit_count_is_extracted(self) -> None:
        self.assertEqual(_extract_included_transactions("6 Debits / Month. $1.25 each thereafter."), 6)

    def test_fee_only_label_is_not_a_short_description(self) -> None:
        self.assertTrue(_looks_like_navigation_description("Monthly Fee: $30"))

    def test_legal_offer_and_application_copy_are_not_product_descriptions(self) -> None:
        context = ExtractionDocumentContext(
            source_id="AUTO-BANK-CHQ-001",
            parsed_document_id="parsed-description-noise",
            source_document_id="src-description-noise",
            snapshot_id="snap-description-noise",
            bank_code="BANK",
            country_code="CA",
            source_type="html",
            source_language="en",
            source_metadata={"product_type": "chequing", "product_name": "Preferred Package"},
        )
        self.assertTrue(
            _looks_like_non_product_summary(
                context=context,
                value="Symbol optional Legal Text Additional fees apply for shared ABM services.",
            )
        )
        self.assertTrue(
            _looks_like_non_product_summary(
                context=context,
                value=(
                    "Set up and make one eligible pre-authorized transaction of at least $50, "
                    "that recurs for at least 6 months in a row."
                ),
            )
        )
        self.assertTrue(
            _looks_like_non_product_summary(
                context=context,
                value="You can open your account online or in branch.",
            )
        )

    def test_free_if_balanced_disclosure_preserves_base_fee_and_waiver_threshold(self) -> None:
        context = ExtractionDocumentContext(
            source_id="AUTO-BANK-CHQ-001",
            parsed_document_id="parsed-fee-waiver",
            source_document_id="src-fee-waiver",
            snapshot_id="snap-fee-waiver",
            bank_code="BANK",
            country_code="CA",
            source_type="html",
            source_language="en",
            source_metadata={"product_type": "chequing"},
        )
        excerpt = "No monthly fee with a minimum daily closing balance of $3,000 ($5 monthly fee if not maintained)."

        monthly_fee, *_ = _extract_candidate_value(context=context, field_name="monthly_fee", excerpt=excerpt, anchor_value="fees")
        minimum_balance, *_ = _extract_candidate_value(context=context, field_name="minimum_balance", excerpt=excerpt, anchor_value="fees")
        waiver, *_ = _extract_candidate_value(context=context, field_name="fee_waiver_condition", excerpt=excerpt, anchor_value="fees")

        self.assertEqual(monthly_fee, "5.00")
        self.assertEqual(minimum_balance, "3000.00")
        self.assertEqual(waiver, "Monthly fee 5.00 is waived to 0.00 with a 3000.00 minimum balance.")

    def test_navigation_and_disclosure_noise_does_not_create_semantic_fields(self) -> None:
        context = ExtractionDocumentContext(
            source_id="AUTO-BANK-SAV-001",
            parsed_document_id="parsed-noise",
            source_document_id="src-noise",
            snapshot_id="snap-noise",
            bank_code="BANK",
            country_code="CA",
            source_type="html",
            source_language="en",
            source_metadata={"product_type": "savings", "product_name": "High Interest Savings"},
        )

        registered, *_ = _extract_candidate_value(
            context=context,
            field_name="registered_flag",
            excerpt="Other accounts: TFSA eSavings and RRSP eSavings.",
            anchor_value="accounts",
        )
        eligibility, *_ = _extract_candidate_value(
            context=context,
            field_name="eligibility_text",
            excerpt="Eligible deposits are insured by CDIC up to applicable limits.",
            anchor_value="deposit-insurance",
        )
        application, *_ = _extract_candidate_value(
            context=context,
            field_name="application_method",
            excerpt="Online banking is available 24 hours a day.",
            anchor_value="online-banking",
        )
        tax_benefits, *_ = _extract_candidate_value(
            context=context,
            field_name="tax_benefits",
            excerpt="Other accounts: TFSA eSavings and RRSP eSavings may offer tax benefits.",
            anchor_value="accounts",
        )

        self.assertIsNone(registered)
        self.assertIsNone(eligibility)
        self.assertIsNone(application)
        self.assertIsNone(tax_benefits)

    def test_document_breadcrumb_is_not_a_product_description(self) -> None:
        self.assertTrue(
            _looks_like_navigation_description(
                "Document Investments Guaranteed Investment Certificates (GICs) Non-redeemable GIC"
            )
        )

    def test_cashable_only_at_maturity_is_not_early_redeemable(self) -> None:
        context = ExtractionDocumentContext(
            source_id="AUTO-BANK-GIC-001",
            parsed_document_id="parsed-gic-maturity",
            source_document_id="src-gic-maturity",
            snapshot_id="snap-gic-maturity",
            bank_code="BANK",
            country_code="CA",
            source_type="html",
            source_language="en",
            source_metadata={"product_type": "gic"},
        )
        excerpt = "The term deposit is cashable upon maturity only."

        redeemable, *_ = _extract_candidate_value(context=context, field_name="redeemable_flag", excerpt=excerpt, anchor_value="terms")
        non_redeemable, *_ = _extract_candidate_value(context=context, field_name="non_redeemable_flag", excerpt=excerpt, anchor_value="terms")

        self.assertFalse(redeemable)
        self.assertTrue(non_redeemable)

    def test_gic_placeholders_and_navigation_do_not_create_false_product_fields(self) -> None:
        context = ExtractionDocumentContext(
            source_id="AUTO-ALTERNA-GIC-001",
            parsed_document_id="parsed-gic-placeholder",
            source_document_id="src-gic-placeholder",
            snapshot_id="snap-gic-placeholder",
            bank_code="ALTERNA",
            country_code="CA",
            source_type="html",
            source_language="en",
            source_metadata={"product_type": "gic", "product_name": "Alterna Bank - eTerm Deposits"},
        )
        rate_excerpt = (
            "Our current eTerm Deposit Rates 1 year eTerm deposit Minimum $500 Maximum $500,000 % * "
            "2 year eTerm deposit Minimum $500 Maximum $500,000 % *"
        )
        legal_excerpt = (
            "Special promotional rates may be changed or withdrawn at any time without notice. "
            "Cashable upon maturity only."
        )

        base_rate, *_ = _extract_candidate_value(
            context=context, field_name="base_12_month_rate", excerpt=rate_excerpt, anchor_value="rates"
        )
        term_table, *_ = _extract_candidate_value(
            context=context, field_name="term_rate_table", excerpt=rate_excerpt, anchor_value="rates"
        )
        introductory, *_ = _extract_candidate_value(
            context=context, field_name="introductory_rate_flag", excerpt=legal_excerpt, anchor_value="legal"
        )
        registered, *_ = _extract_candidate_value(
            context=context,
            field_name="registered_plan_supported",
            excerpt="eTerm Deposits Overview Registered Plans",
            anchor_value="eterm-deposits",
        )
        post_maturity, *_ = _extract_candidate_value(
            context=context, field_name="post_maturity_interest_rate", excerpt=legal_excerpt, anchor_value="legal"
        )

        self.assertIsNone(base_rate)
        self.assertIsNone(term_table)
        self.assertIsNone(introductory)
        self.assertIsNone(registered)
        self.assertIsNone(post_maturity)

    def test_extracts_requested_deposit_detail_fields(self) -> None:
        context = ExtractionDocumentContext(
            source_id="BMO-GIC-001",
            parsed_document_id="parsed-detail-fields",
            source_document_id="src-detail-fields",
            snapshot_id="snap-detail-fields",
            bank_code="BMO",
            country_code="CA",
            source_type="html",
            source_language="en",
            source_metadata={"product_type": "gic"},
        )
        text = (
            "BMO GIC rates: 6 months 4.10%, 12 months 4.50%, 2 years 4.25%. "
            "Apply online or in branch. At maturity, renewal rates may apply. "
            "TFSA and RRSP options may provide tax benefits. Eligible deposits are protected by CDIC limits."
        )

        term_table, term_type, _, _ = _extract_candidate_value(
            context=context,
            field_name="term_rate_table",
            excerpt=text,
            anchor_value="gic-rates",
        )
        base_rate, _, _, _ = _extract_candidate_value(
            context=context,
            field_name="base_12_month_rate",
            excerpt=text,
            anchor_value="gic-rates",
        )
        application_method, _, _, _ = _extract_candidate_value(
            context=context,
            field_name="application_method",
            excerpt=text,
            anchor_value="apply",
        )
        deposit_insurance, _, _, _ = _extract_candidate_value(
            context=context,
            field_name="deposit_insurance",
            excerpt=text,
            anchor_value="insurance",
        )
        unrelated_application_method, _, _, _ = _extract_candidate_value(
            context=context,
            field_name="application_method",
            excerpt="Interest rate: 1.10%. Interest is paid monthly.",
            anchor_value="rates",
        )
        registration_navigation, _, _, _ = _extract_candidate_value(
            context=context,
            field_name="application_method",
            excerpt="Apply for a bank account. You must be registered for Online and Mobile Banking. Need to register?",
            anchor_value="apply",
        )

        self.assertEqual(term_type, "json")
        self.assertEqual(term_table[1]["term_label"], "12 months")
        self.assertEqual(term_table[1]["rate"], "4.50")
        self.assertEqual(base_rate, "4.50")
        self.assertEqual(application_method, "Apply online or in branch.")
        self.assertEqual(deposit_insurance, "Eligible deposits are protected by CDIC limits.")
        self.assertIsNone(unrelated_application_method)
        self.assertIsNone(registration_navigation)

    def test_extracts_sparse_draft_and_evidence_links(self) -> None:
        temp_path = _prepare_workspace_temp_dir("extraction-service")
        try:
            context = ExtractionDocumentContext(
                source_id="TD-SAV-002",
                parsed_document_id="parsed-001",
                source_document_id="src-001",
                snapshot_id="snap-001",
                bank_code="TD",
                country_code="CA",
                source_type="html",
                source_language="en",
                source_metadata={
                    "product_type": "savings",
                    "expected_fields": [
                        "monthly_fee",
                        "fee_waiver_condition",
                        "standard_rate",
                        "interest_payment_frequency",
                    ],
                },
            )
            candidates = [
                EvidenceChunkCandidate(
                    evidence_chunk_id="chunk-001",
                    parsed_document_id="parsed-001",
                    chunk_index=0,
                    anchor_type="section",
                    anchor_value="every-day-savings-account",
                    page_no=None,
                    source_language="en",
                    evidence_excerpt="Every Day Savings Account\nA simple savings account with no monthly fee.",
                    retrieval_metadata={},
                    source_document_id="src-001",
                    source_snapshot_id="snap-001",
                    bank_code="TD",
                    country_code="CA",
                    source_type="html",
                ),
                EvidenceChunkCandidate(
                    evidence_chunk_id="chunk-002",
                    parsed_document_id="parsed-001",
                    chunk_index=1,
                    anchor_type="section",
                    anchor_value="fees",
                    page_no=None,
                    source_language="en",
                    evidence_excerpt="Monthly fee: $0. Maintain a $5,000 minimum daily balance to waive additional service charges.",
                    retrieval_metadata={},
                    source_document_id="src-001",
                    source_snapshot_id="snap-001",
                    bank_code="TD",
                    country_code="CA",
                    source_type="html",
                ),
                EvidenceChunkCandidate(
                    evidence_chunk_id="chunk-003",
                    parsed_document_id="parsed-001",
                    chunk_index=2,
                    anchor_type="section",
                    anchor_value="interest",
                    page_no=None,
                    source_language="en",
                    evidence_excerpt="Earn 1.25% interest. Interest is calculated daily and paid monthly.",
                    retrieval_metadata={},
                    source_document_id="src-001",
                    source_snapshot_id="snap-001",
                    bank_code="TD",
                    country_code="CA",
                    source_type="html",
                ),
            ]
            storage_config = ExtractionStorageConfig(
                driver="filesystem",
                env_prefix="dev",
                extraction_object_prefix="extracted",
                retention_class="hot",
                filesystem_root=str(temp_path),
            )
            service = ExtractionService(
                storage_config=storage_config,
                object_store=build_object_store(storage_config),
            )

            result = service.extract_documents(
                run_id="run-001",
                correlation_id="corr-001",
                request_id="req-001",
                inputs=[ExtractionInput(context=context, candidates=candidates)],
            )

            self.assertFalse(result.partial_completion_flag)
            source_result = result.source_results[0]
            self.assertEqual(source_result.extraction_action, "stored")
            extracted_by_field = {item.field_name: item for item in source_result.extracted_fields}
            self.assertEqual(extracted_by_field["product_type"].candidate_value, "savings")
            self.assertEqual(extracted_by_field["currency"].candidate_value, "CAD")
            self.assertEqual(extracted_by_field["product_name"].candidate_value, "Every Day Savings Account")
            self.assertEqual(extracted_by_field["monthly_fee"].candidate_value, "0.00")
            self.assertEqual(extracted_by_field["standard_rate"].candidate_value, "1.25")
            self.assertEqual(extracted_by_field["interest_payment_frequency"].candidate_value, "monthly")
            self.assertGreaterEqual(len(source_result.evidence_links), 3)

            extracted_path = temp_path / Path(str(source_result.extracted_storage_key).replace("/", "\\"))
            metadata_path = temp_path / Path(str(source_result.metadata_storage_key).replace("/", "\\"))
            self.assertTrue(extracted_path.exists())
            self.assertTrue(metadata_path.exists())
            payload = json.loads(extracted_path.read_text(encoding="utf-8"))
            self.assertEqual(payload["parsed_document_id"], "parsed-001")
        finally:
            rmtree(temp_path, ignore_errors=True)

    def test_lending_source_metadata_sets_product_family_in_artifact(self) -> None:
        temp_path = _prepare_workspace_temp_dir("extraction-lending-family")
        try:
            context = ExtractionDocumentContext(
                source_id="RBC-CC-001",
                parsed_document_id="parsed-cc-001",
                source_document_id="src-cc-001",
                snapshot_id="snap-cc-001",
                bank_code="RBC",
                country_code="CA",
                source_type="html",
                source_language="en",
                source_metadata={
                    "product_type": "credit-card",
                    "product_family": "lending",
                    "product_type_dynamic": True,
                    "product_type_name": "Credit Card",
                    "product_type_description": "Canadian retail credit cards.",
                    "expected_fields": ["product_name", "annual_fee", "purchase_interest_rate"],
                },
            )
            candidates = [
                EvidenceChunkCandidate(
                    evidence_chunk_id="chunk-cc-001",
                    parsed_document_id="parsed-cc-001",
                    chunk_index=0,
                    anchor_type="section",
                    anchor_value="cash-back-credit-card",
                    page_no=None,
                    source_language="en",
                    evidence_excerpt="Cash Back Credit Card\nAnnual fee: $0. Purchase interest rate: 20.99%.",
                    retrieval_metadata={},
                    source_document_id="src-cc-001",
                    source_snapshot_id="snap-cc-001",
                    bank_code="RBC",
                    country_code="CA",
                    source_type="html",
                )
            ]
            storage_config = ExtractionStorageConfig(
                driver="filesystem",
                env_prefix="dev",
                extraction_object_prefix="extracted",
                retention_class="hot",
                filesystem_root=str(temp_path),
            )
            service = ExtractionService(storage_config=storage_config, object_store=build_object_store(storage_config))

            result = service.extract_documents(
                run_id="run-cc-001",
                correlation_id="corr-cc-001",
                request_id="req-cc-001",
                inputs=[ExtractionInput(context=context, candidates=candidates)],
            )

            source_result = result.source_results[0]
            extracted_by_field = {item.field_name: item for item in source_result.extracted_fields}
            self.assertEqual(extracted_by_field["product_family"].candidate_value, "lending")
            extracted_path = temp_path / Path(str(source_result.extracted_storage_key).replace("/", "\\"))
            payload = json.loads(extracted_path.read_text(encoding="utf-8"))
            self.assertEqual(payload["schema_context"]["product_family"], "lending")
            self.assertEqual(payload["schema_context"]["product_type"], "credit-card")
        finally:
            rmtree(temp_path, ignore_errors=True)

    def test_rate_fallback_scans_product_rate_chunk_when_field_match_missed(self) -> None:
        context = ExtractionDocumentContext(
            source_id="AUTO-RBC-SAV-hisa",
            parsed_document_id="parsed-rate-fallback",
            source_document_id="src-rate-fallback",
            snapshot_id="snap-rate-fallback",
            bank_code="RBC",
            country_code="CA",
            source_type="html",
            source_language="en",
            source_metadata={"product_type": "savings"},
        )
        extracted_fields = [
            _extracted_field("product_type", "savings"),
            _extracted_field("product_name", "High Interest Savings Account"),
        ]
        candidates = [
            EvidenceChunkCandidate(
                evidence_chunk_id="chunk-rate-fallback",
                parsed_document_id="parsed-rate-fallback",
                chunk_index=2,
                anchor_type="section",
                anchor_value="earn-4-60-interest-for-3-months",
                page_no=None,
                source_language="en",
                evidence_excerpt=(
                    "Earn 4.60% interest for 3 Months when you open your first "
                    "RBC High Interest eSavings account."
                ),
                retrieval_metadata={},
                source_document_id="src-rate-fallback",
                source_snapshot_id="snap-rate-fallback",
                bank_code="RBC",
                country_code="CA",
                source_type="html",
            )
        ]

        _append_rate_fallback_fields(context=context, candidates=candidates, extracted_fields=extracted_fields)

        fields_by_name = {field.field_name: field for field in extracted_fields}
        self.assertEqual(fields_by_name["public_display_rate"].candidate_value, "4.60")
        self.assertEqual(fields_by_name["promotional_rate"].candidate_value, "4.60")
        self.assertNotIn("standard_rate", fields_by_name)
        self.assertEqual(fields_by_name["public_display_rate"].extraction_method, "heuristic_rate_context_fallback")

    def test_rate_fallback_supplements_labeled_thereafter_rate_after_promo_found(self) -> None:
        context = ExtractionDocumentContext(
            source_id="AUTO-BANK-SAV-hisa",
            parsed_document_id="parsed-hisa-rates",
            source_document_id="src-hisa-rates",
            snapshot_id="snap-hisa-rates",
            bank_code="BANK",
            country_code="CA",
            source_type="html",
            source_language="en",
            source_metadata={"product_type": "savings", "product_name": "High Interest Savings Account"},
        )
        candidate = EvidenceChunkCandidate(
            evidence_chunk_id="chunk-hisa-rates",
            parsed_document_id="parsed-hisa-rates",
            chunk_index=2,
            anchor_type="section",
            anchor_value="interest-rates",
            page_no=None,
            source_language="en",
            evidence_excerpt=(
                "High Interest Savings Account Interest Rates Time Rate "
                "First 3 months 4.60% Thereafter 0.550%"
            ),
            retrieval_metadata={},
            source_document_id="src-hisa-rates",
            source_snapshot_id="snap-hisa-rates",
            bank_code="BANK",
            country_code="CA",
            source_type="html",
        )
        extracted_fields = [
            _extracted_field("product_name", "High Interest Savings Account"),
            _extracted_field("promotional_rate", "4.60"),
            _extracted_field("public_display_rate", "4.60"),
        ]

        _append_rate_fallback_fields(
            context=context,
            candidates=[candidate],
            requested_fields={"standard_rate", "promotional_rate", "public_display_rate"},
            extracted_fields=extracted_fields,
        )

        fields_by_name = {field.field_name: field for field in extracted_fields}
        self.assertEqual(fields_by_name["standard_rate"].candidate_value, "0.55")
        self.assertEqual(
            fields_by_name["standard_rate"].extraction_method,
            "heuristic_labeled_standard_rate_fallback",
        )

    def test_rate_fallback_replaces_promo_misclassified_as_standard_with_thereafter_rate(self) -> None:
        context = ExtractionDocumentContext(
            source_id="AUTO-BANK-SAV-hisa",
            parsed_document_id="parsed-hisa-rates",
            source_document_id="src-hisa-rates",
            snapshot_id="snap-hisa-rates",
            bank_code="BANK",
            country_code="CA",
            source_type="html",
            source_language="en",
            source_metadata={"product_type": "savings", "product_name": "High Interest Savings Account"},
        )
        promo_chunk = EvidenceChunkCandidate(
            evidence_chunk_id="chunk-hisa-offer",
            parsed_document_id="parsed-hisa-rates",
            chunk_index=1,
            anchor_type="section",
            anchor_value="offer",
            page_no=None,
            source_language="en",
            evidence_excerpt="Earn 4.60% interest for 3 months when you open your first account.",
            retrieval_metadata={},
            source_document_id="src-hisa-rates",
            source_snapshot_id="snap-hisa-rates",
            bank_code="BANK",
            country_code="CA",
            source_type="html",
        )
        rate_chunk = EvidenceChunkCandidate(
            evidence_chunk_id="chunk-hisa-rates",
            parsed_document_id="parsed-hisa-rates",
            chunk_index=2,
            anchor_type="section",
            anchor_value="interest-rates",
            page_no=None,
            source_language="en",
            evidence_excerpt=(
                "High Interest Savings Account Interest Rates Time Rate "
                "First 3 months 4.60% Thereafter 0.550%"
            ),
            retrieval_metadata={},
            source_document_id="src-hisa-rates",
            source_snapshot_id="snap-hisa-rates",
            bank_code="BANK",
            country_code="CA",
            source_type="html",
        )
        extracted_fields = [
            _extracted_field("standard_rate", "4.60", evidence_text_excerpt=promo_chunk.evidence_excerpt),
            _extracted_field("promotional_rate", "4.60"),
            _extracted_field("public_display_rate", "4.60"),
        ]

        _append_rate_fallback_fields(
            context=context,
            candidates=[promo_chunk, rate_chunk],
            requested_fields={"standard_rate", "promotional_rate", "public_display_rate"},
            extracted_fields=extracted_fields,
        )

        standard_fields = [field for field in extracted_fields if field.field_name == "standard_rate"]
        self.assertEqual(len(standard_fields), 1)
        self.assertEqual(standard_fields[0].candidate_value, "0.55")
        self.assertEqual(standard_fields[0].evidence_chunk_id, "chunk-hisa-rates")

    def test_rate_fallback_ignores_market_linked_return_cap_context(self) -> None:
        context = ExtractionDocumentContext(
            source_id="AUTO-SCOTIA-GIC-market-linked",
            parsed_document_id="parsed-market-linked-rate-cap",
            source_document_id="src-market-linked-rate-cap",
            snapshot_id="snap-market-linked-rate-cap",
            bank_code="SCOTIA",
            country_code="CA",
            source_type="html",
            source_language="en",
            source_metadata={"product_type": "gic"},
        )
        extracted_fields = [
            _extracted_field("product_type", "gic"),
            _extracted_field("product_name", "Scotiabank Market Linked GICs"),
        ]
        return_cap_excerpt = (
            "Return: The Index Return payable, if any, is based on the performance of the Underlying Index. "
            "Your Scotiabank Market Linked GIC principal is unconditionally guaranteed. "
            "Limitation on interest: by law, the total return you receive cannot exceed an average of "
            "60% per year, regardless of the performance of the Underlying Index."
        )
        candidates = [
            EvidenceChunkCandidate(
                evidence_chunk_id="chunk-market-linked-rate-cap",
                parsed_document_id="parsed-market-linked-rate-cap",
                chunk_index=16,
                anchor_type="section",
                anchor_value="by-phone",
                page_no=None,
                source_language="en",
                evidence_excerpt=return_cap_excerpt,
                retrieval_metadata={},
                source_document_id="src-market-linked-rate-cap",
                source_snapshot_id="snap-market-linked-rate-cap",
                bank_code="SCOTIA",
                country_code="CA",
                source_type="html",
            )
        ]

        _append_rate_fallback_fields(context=context, candidates=candidates, extracted_fields=extracted_fields)
        public_rate, _, _, _ = _extract_candidate_value(
            context=context,
            field_name="public_display_rate",
            excerpt=return_cap_excerpt,
            anchor_value="by-phone",
        )

        fields_by_name = {field.field_name: field for field in extracted_fields}
        self.assertNotIn("public_display_rate", fields_by_name)
        self.assertNotIn("standard_rate", fields_by_name)
        self.assertIsNone(public_rate)

    def test_extracts_chequing_specific_fields(self) -> None:
        temp_path = _prepare_workspace_temp_dir("extraction-chequing-service")
        try:
            context = ExtractionDocumentContext(
                source_id="TD-CHQ-002",
                parsed_document_id="parsed-chq-001",
                source_document_id="src-chq-001",
                snapshot_id="snap-chq-001",
                bank_code="TD",
                country_code="CA",
                source_type="html",
                source_language="en",
                source_metadata={
                    "product_type": "chequing",
                    "expected_fields": [
                        "monthly_fee",
                        "included_transactions",
                        "interac_e_transfer_included",
                        "overdraft_available",
                        "cheque_book_info",
                        "student_plan_flag",
                        "newcomer_plan_flag",
                    ],
                },
            )
            candidates = [
                EvidenceChunkCandidate(
                    evidence_chunk_id="chunk-chq-001",
                    parsed_document_id="parsed-chq-001",
                    chunk_index=0,
                    anchor_type="section",
                    anchor_value="student-banking-package",
                    page_no=None,
                    source_language="en",
                    evidence_excerpt="TD Student Banking Package\nChequing account for students and newcomers to Canada.",
                    retrieval_metadata={},
                    source_document_id="src-chq-001",
                    source_snapshot_id="snap-chq-001",
                    bank_code="TD",
                    country_code="CA",
                    source_type="html",
                ),
                EvidenceChunkCandidate(
                    evidence_chunk_id="chunk-chq-002",
                    parsed_document_id="parsed-chq-001",
                    chunk_index=1,
                    anchor_type="section",
                    anchor_value="account-fees",
                    page_no=None,
                    source_language="en",
                    evidence_excerpt="Monthly fee: $0. Includes 25 debits per month.",
                    retrieval_metadata={},
                    source_document_id="src-chq-001",
                    source_snapshot_id="snap-chq-001",
                    bank_code="TD",
                    country_code="CA",
                    source_type="html",
                ),
                EvidenceChunkCandidate(
                    evidence_chunk_id="chunk-chq-003",
                    parsed_document_id="parsed-chq-001",
                    chunk_index=2,
                    anchor_type="section",
                    anchor_value="account-benefits",
                    page_no=None,
                    source_language="en",
                    evidence_excerpt=(
                        "Unlimited Interac e-Transfers are included. Overdraft protection available. "
                        "One free cheque book when you open the account."
                    ),
                    retrieval_metadata={},
                    source_document_id="src-chq-001",
                    source_snapshot_id="snap-chq-001",
                    bank_code="TD",
                    country_code="CA",
                    source_type="html",
                ),
            ]
            storage_config = ExtractionStorageConfig(
                driver="filesystem",
                env_prefix="dev",
                extraction_object_prefix="extracted",
                retention_class="hot",
                filesystem_root=str(temp_path),
            )
            service = ExtractionService(
                storage_config=storage_config,
                object_store=build_object_store(storage_config),
            )

            result = service.extract_documents(
                run_id="run-chq-001",
                correlation_id="corr-chq-001",
                request_id="req-chq-001",
                inputs=[ExtractionInput(context=context, candidates=candidates)],
            )

            self.assertFalse(result.partial_completion_flag)
            source_result = result.source_results[0]
            extracted_by_field = {item.field_name: item for item in source_result.extracted_fields}
            self.assertEqual(extracted_by_field["product_type"].candidate_value, "chequing")
            self.assertEqual(extracted_by_field["monthly_fee"].candidate_value, "0.00")
            self.assertEqual(extracted_by_field["included_transactions"].candidate_value, 25)
            self.assertTrue(extracted_by_field["interac_e_transfer_included"].candidate_value)
            self.assertTrue(extracted_by_field["overdraft_available"].candidate_value)
            self.assertTrue(extracted_by_field["student_plan_flag"].candidate_value)
            self.assertNotIn("newcomer_plan_flag", extracted_by_field)
            self.assertIn("cheque book", extracted_by_field["cheque_book_info"].candidate_value.lower())
            self.assertGreaterEqual(len(source_result.evidence_links), 6)
        finally:
            rmtree(temp_path, ignore_errors=True)

    def test_bmo_plus_chequing_fee_waiver_phrase_maps_fee_and_balance(self) -> None:
        temp_path = _prepare_workspace_temp_dir("extraction-bmo-plus-chequing")
        try:
            context = ExtractionDocumentContext(
                source_id="BMO-CHQ-003",
                parsed_document_id="parsed-bmo-chq-plus",
                source_document_id="src-bmo-chq-plus",
                snapshot_id="snap-bmo-chq-plus",
                bank_code="BMO",
                country_code="CA",
                source_type="html",
                source_language="en",
                source_metadata={
                    "product_type": "chequing",
                    "expected_fields": [
                        "monthly_fee",
                        "public_display_fee",
                        "minimum_balance",
                        "fee_waiver_condition",
                        "included_transactions",
                        "interac_e_transfer_included",
                        "student_plan_flag",
                        "newcomer_plan_flag",
                    ],
                },
            )
            candidates = [
                EvidenceChunkCandidate(
                    evidence_chunk_id="chunk-bmo-plus-title",
                    parsed_document_id="parsed-bmo-chq-plus",
                    chunk_index=0,
                    anchor_type="section",
                    anchor_value="plus-chequing-account",
                    page_no=None,
                    source_language="en",
                    evidence_excerpt="Plus Chequing Account\nGet budget-friendly flexible banking.",
                    retrieval_metadata={},
                    source_document_id="src-bmo-chq-plus",
                    source_snapshot_id="snap-bmo-chq-plus",
                    bank_code="BMO",
                    country_code="CA",
                    source_type="html",
                ),
                EvidenceChunkCandidate(
                    evidence_chunk_id="chunk-bmo-plus-fee",
                    parsed_document_id="parsed-bmo-chq-plus",
                    chunk_index=1,
                    anchor_type="section",
                    anchor_value="rates-and-fees",
                    page_no=None,
                    source_language="en",
                    evidence_excerpt=(
                        "Plus $12.95 per month or $0 with a $3,000 minimum balance. "
                        "Enjoy up to 25 everyday banking transactions and INTERAC e-Transfer transactions per month."
                    ),
                    retrieval_metadata={},
                    source_document_id="src-bmo-chq-plus",
                    source_snapshot_id="snap-bmo-chq-plus",
                    bank_code="BMO",
                    country_code="CA",
                    source_type="html",
                ),
                EvidenceChunkCandidate(
                    evidence_chunk_id="chunk-bmo-plus-savings-benefit",
                    parsed_document_id="parsed-bmo-chq-plus",
                    chunk_index=2,
                    anchor_type="section",
                    anchor_value="canadian-and-u-s-dollar-savings-account",
                    page_no=None,
                    source_language="en",
                    evidence_excerpt=(
                        "Canadian and U.S. dollar Savings Account at no additional cost. "
                        "Interest is calculated on savings balances and paid monthly."
                    ),
                    retrieval_metadata={},
                    source_document_id="src-bmo-chq-plus",
                    source_snapshot_id="snap-bmo-chq-plus",
                    bank_code="BMO",
                    country_code="CA",
                    source_type="html",
                ),
                EvidenceChunkCandidate(
                    evidence_chunk_id="chunk-bmo-plus-nav-offers",
                    parsed_document_id="parsed-bmo-chq-plus",
                    chunk_index=3,
                    anchor_type="section",
                    anchor_value="student-newcomer-offers",
                    page_no=None,
                    source_language="en",
                    evidence_excerpt=(
                        "Explore student banking, newcomer offers, savings accounts, and registered plans. "
                        "These offers are described in other account sections."
                    ),
                    retrieval_metadata={},
                    source_document_id="src-bmo-chq-plus",
                    source_snapshot_id="snap-bmo-chq-plus",
                    bank_code="BMO",
                    country_code="CA",
                    source_type="html",
                ),
            ]
            storage_config = ExtractionStorageConfig(
                driver="filesystem",
                env_prefix="dev",
                extraction_object_prefix="extracted",
                retention_class="hot",
                filesystem_root=str(temp_path),
            )
            service = ExtractionService(
                storage_config=storage_config,
                object_store=build_object_store(storage_config),
            )

            result = service.extract_documents(
                run_id="run-bmo-plus-chq",
                correlation_id="corr-bmo-plus-chq",
                request_id="req-bmo-plus-chq",
                inputs=[ExtractionInput(context=context, candidates=candidates)],
            )

            extracted_by_field = {item.field_name: item for item in result.source_results[0].extracted_fields}
            self.assertEqual(extracted_by_field["product_name"].candidate_value, "Plus Chequing Account")
            self.assertEqual(extracted_by_field["monthly_fee"].candidate_value, "12.95")
            self.assertEqual(extracted_by_field["public_display_fee"].candidate_value, "12.95")
            self.assertEqual(extracted_by_field["minimum_balance"].candidate_value, "3000.00")
            self.assertIn("3000.00 minimum balance", extracted_by_field["fee_waiver_condition"].candidate_value)
            self.assertEqual(extracted_by_field["included_transactions"].candidate_value, 25)
            self.assertTrue(extracted_by_field["interac_e_transfer_included"].candidate_value)
            self.assertNotIn("interest_payment_frequency", extracted_by_field)
            self.assertNotIn("interest_calculation_method", extracted_by_field)
            self.assertNotIn("student_plan_flag", extracted_by_field)
            self.assertNotIn("newcomer_plan_flag", extracted_by_field)
        finally:
            rmtree(temp_path, ignore_errors=True)

    def test_bmo_performance_chequing_comparison_fee_phrase_maps_fee_and_balance(self) -> None:
        temp_path = _prepare_workspace_temp_dir("extraction-bmo-performance-chequing")
        try:
            context = ExtractionDocumentContext(
                source_id="BMO-CHQ-004",
                parsed_document_id="parsed-bmo-chq-performance",
                source_document_id="src-bmo-chq-performance",
                snapshot_id="snap-bmo-chq-performance",
                bank_code="BMO",
                country_code="CA",
                source_type="html",
                source_language="en",
                source_metadata={
                    "product_type": "chequing",
                    "expected_fields": [
                        "monthly_fee",
                        "public_display_fee",
                        "minimum_balance",
                        "fee_waiver_condition",
                        "included_transactions",
                        "interac_e_transfer_included",
                        "credit_card_rebate",
                    ],
                },
            )
            candidates = [
                EvidenceChunkCandidate(
                    evidence_chunk_id="chunk-bmo-performance-title",
                    parsed_document_id="parsed-bmo-chq-performance",
                    chunk_index=0,
                    anchor_type="section",
                    anchor_value="performance-chequing-account",
                    page_no=None,
                    source_language="en",
                    evidence_excerpt=(
                        "Performance Chequing Account\n"
                        "Our everyday chequing account for all your banking needs."
                    ),
                    retrieval_metadata={},
                    source_document_id="src-bmo-chq-performance",
                    source_snapshot_id="snap-bmo-chq-performance",
                    bank_code="BMO",
                    country_code="CA",
                    source_type="html",
                ),
                EvidenceChunkCandidate(
                    evidence_chunk_id="chunk-bmo-performance-fees",
                    parsed_document_id="parsed-bmo-chq-performance",
                    chunk_index=1,
                    anchor_type="section",
                    anchor_value="explore-the-bonuses-features-and-fees-for-our-chequing-accounts",
                    page_no=None,
                    source_language="en",
                    evidence_excerpt=(
                        "Fees Monthly plan fee *4 $17.95 OR $0/month with min. $4,000 balance. "
                        "Unlimited transactions and INTERAC e-Transfer transactions. "
                        "Additional features - No fee for select Cheques *54 No fee for Stop Payments. "
                        "Premium $30.95 OR $0/month with min. $6,000 balance."
                    ),
                    retrieval_metadata={},
                    source_document_id="src-bmo-chq-performance",
                    source_snapshot_id="snap-bmo-chq-performance",
                    bank_code="BMO",
                    country_code="CA",
                    source_type="html",
                ),
                EvidenceChunkCandidate(
                    evidence_chunk_id="chunk-bmo-performance-nav",
                    parsed_document_id="parsed-bmo-chq-performance",
                    chunk_index=2,
                    anchor_type="section",
                    anchor_value="other-products",
                    page_no=None,
                    source_language="en",
                    evidence_excerpt=(
                        "Explore student banking, newcomer offers, savings accounts, and registered plans."
                    ),
                    retrieval_metadata={},
                    source_document_id="src-bmo-chq-performance",
                    source_snapshot_id="snap-bmo-chq-performance",
                    bank_code="BMO",
                    country_code="CA",
                    source_type="html",
                ),
            ]
            storage_config = ExtractionStorageConfig(
                driver="filesystem",
                env_prefix="dev",
                extraction_object_prefix="extracted",
                retention_class="hot",
                filesystem_root=str(temp_path),
            )
            service = ExtractionService(
                storage_config=storage_config,
                object_store=build_object_store(storage_config),
            )

            result = service.extract_documents(
                run_id="run-bmo-performance-chq",
                correlation_id="corr-bmo-performance-chq",
                request_id="req-bmo-performance-chq",
                inputs=[ExtractionInput(context=context, candidates=candidates)],
            )

            extracted_by_field = {item.field_name: item for item in result.source_results[0].extracted_fields}
            self.assertEqual(extracted_by_field["product_name"].candidate_value, "Performance Chequing Account")
            self.assertEqual(extracted_by_field["monthly_fee"].candidate_value, "17.95")
            self.assertEqual(extracted_by_field["public_display_fee"].candidate_value, "17.95")
            self.assertEqual(extracted_by_field["minimum_balance"].candidate_value, "4000.00")
            self.assertIn("4000.00 minimum balance", extracted_by_field["fee_waiver_condition"].candidate_value)
            self.assertTrue(extracted_by_field["unlimited_transactions_flag"].candidate_value)
            self.assertTrue(extracted_by_field["interac_e_transfer_included"].candidate_value)
            self.assertEqual(extracted_by_field["cheque_book_info"].candidate_value, "No fee for select Cheques.")
            self.assertNotIn("credit_card_rebate", extracted_by_field)
            self.assertNotIn("student_plan_flag", extracted_by_field)
            self.assertNotIn("newcomer_plan_flag", extracted_by_field)
            self.assertNotIn("registered_flag", extracted_by_field)
        finally:
            rmtree(temp_path, ignore_errors=True)

    def test_bmo_practical_chequing_suppresses_cross_product_fee_and_field_noise(self) -> None:
        temp_path = _prepare_workspace_temp_dir("extraction-bmo-practical-chequing")
        try:
            context = ExtractionDocumentContext(
                source_id="BMO-CHQ-002",
                parsed_document_id="parsed-bmo-chq-practical",
                source_document_id="src-bmo-chq-practical",
                snapshot_id="snap-bmo-chq-practical",
                bank_code="BMO",
                country_code="CA",
                source_type="html",
                source_language="en",
                source_metadata={
                    "product_type": "chequing",
                    "expected_fields": [
                        "monthly_fee",
                        "public_display_fee",
                        "minimum_balance",
                        "fee_waiver_condition",
                        "cheque_book_info",
                        "interest_calculation_method",
                        "registered_flag",
                        "student_plan_flag",
                        "newcomer_plan_flag",
                    ],
                },
            )
            candidates = [
                EvidenceChunkCandidate(
                    evidence_chunk_id="chunk-bmo-practical-title",
                    parsed_document_id="parsed-bmo-chq-practical",
                    chunk_index=0,
                    anchor_type="section",
                    anchor_value="practical-chequing-account",
                    page_no=None,
                    source_language="en",
                    evidence_excerpt=(
                        "Practical Chequing Account\n"
                        "A low-fee option for your everyday banking needs."
                    ),
                    retrieval_metadata={},
                    source_document_id="src-bmo-chq-practical",
                    source_snapshot_id="snap-bmo-chq-practical",
                    bank_code="BMO",
                    country_code="CA",
                    source_type="html",
                ),
                EvidenceChunkCandidate(
                    evidence_chunk_id="chunk-bmo-practical-fees",
                    parsed_document_id="parsed-bmo-chq-practical",
                    chunk_index=1,
                    anchor_type="section",
                    anchor_value="explore-the-bonuses-features-and-fees-for-our-chequing-accounts",
                    page_no=None,
                    source_language="en",
                    evidence_excerpt=(
                        "Explore the bonuses, features, and fees for our chequing accounts. "
                        "Practical $4 per month. "
                        "Plus $12.95 per month or $0 with a $3,000 minimum balance. "
                        "Performance $17.95 OR $0/month with min. $4,000 balance. "
                        "Students, newcomers, registered savings plans, and bonus interest are described elsewhere."
                    ),
                    retrieval_metadata={},
                    source_document_id="src-bmo-chq-practical",
                    source_snapshot_id="snap-bmo-chq-practical",
                    bank_code="BMO",
                    country_code="CA",
                    source_type="html",
                ),
                EvidenceChunkCandidate(
                    evidence_chunk_id="chunk-bmo-practical-funding",
                    parsed_document_id="parsed-bmo-chq-practical",
                    chunk_index=2,
                    anchor_type="section",
                    anchor_value="how-do-i-open-a-low-fee-chequing-account-at-bmo",
                    page_no=None,
                    source_language="en",
                    evidence_excerpt=(
                        "How do I add money to my BMO Practical Chequing Account? "
                        "At a branch or ATM: Visit your nearest branch or ATM to deposit cash and cheques. "
                        "Mobile deposit: Use the BMO Mobile Banking App to deposit cheques instantly."
                    ),
                    retrieval_metadata={},
                    source_document_id="src-bmo-chq-practical",
                    source_snapshot_id="snap-bmo-chq-practical",
                    bank_code="BMO",
                    country_code="CA",
                    source_type="html",
                ),
            ]
            storage_config = ExtractionStorageConfig(
                driver="filesystem",
                env_prefix="dev",
                extraction_object_prefix="extracted",
                retention_class="hot",
                filesystem_root=str(temp_path),
            )
            service = ExtractionService(
                storage_config=storage_config,
                object_store=build_object_store(storage_config),
            )

            result = service.extract_documents(
                run_id="run-bmo-practical-chq",
                correlation_id="corr-bmo-practical-chq",
                request_id="req-bmo-practical-chq",
                inputs=[ExtractionInput(context=context, candidates=candidates)],
            )

            extracted_by_field = {item.field_name: item for item in result.source_results[0].extracted_fields}
            self.assertEqual(extracted_by_field["product_name"].candidate_value, "Practical Chequing Account")
            self.assertEqual(extracted_by_field["monthly_fee"].candidate_value, "4.00")
            self.assertEqual(extracted_by_field["public_display_fee"].candidate_value, "4.00")
            self.assertNotIn("minimum_balance", extracted_by_field)
            self.assertNotIn("fee_waiver_condition", extracted_by_field)
            self.assertNotIn("cheque_book_info", extracted_by_field)
            self.assertNotIn("interest_calculation_method", extracted_by_field)
            self.assertNotIn("registered_flag", extracted_by_field)
            self.assertNotIn("student_plan_flag", extracted_by_field)
            self.assertNotIn("newcomer_plan_flag", extracted_by_field)
        finally:
            rmtree(temp_path, ignore_errors=True)

    def test_bmo_air_miles_chequing_maps_own_fee_and_balance_without_nav_noise(self) -> None:
        temp_path = _prepare_workspace_temp_dir("extraction-bmo-air-miles-chequing")
        try:
            context = ExtractionDocumentContext(
                source_id="BMO-CHQ-008",
                parsed_document_id="parsed-bmo-chq-air-miles",
                source_document_id="src-bmo-chq-air-miles",
                snapshot_id="snap-bmo-chq-air-miles",
                bank_code="BMO",
                country_code="CA",
                source_type="html",
                source_language="en",
                source_metadata={
                    "product_type": "chequing",
                    "expected_fields": [
                        "monthly_fee",
                        "public_display_fee",
                        "minimum_balance",
                        "fee_waiver_condition",
                        "eligibility_text",
                        "cheque_book_info",
                        "student_plan_flag",
                        "newcomer_plan_flag",
                        "rewards_benefits",
                    ],
                },
            )
            candidates = [
                EvidenceChunkCandidate(
                    evidence_chunk_id="chunk-bmo-air-miles-title",
                    parsed_document_id="parsed-bmo-chq-air-miles",
                    chunk_index=0,
                    anchor_type="section",
                    anchor_value="air-miles-chequing-account",
                    page_no=None,
                    source_language="en",
                    evidence_excerpt=(
                        "AIR MILES Chequing Account\n"
                        "Enjoy AIR MILES rewards with unlimited banking transactions."
                    ),
                    retrieval_metadata={},
                    source_document_id="src-bmo-chq-air-miles",
                    source_snapshot_id="snap-bmo-chq-air-miles",
                    bank_code="BMO",
                    country_code="CA",
                    source_type="html",
                ),
                EvidenceChunkCandidate(
                    evidence_chunk_id="chunk-bmo-air-miles-fees",
                    parsed_document_id="parsed-bmo-chq-air-miles",
                    chunk_index=1,
                    anchor_type="section",
                    anchor_value="explore-the-bonuses-features-and-fees-for-our-chequing-accounts",
                    page_no=None,
                    source_language="en",
                    evidence_excerpt=(
                        "Explore the bonuses, features and fees for our chequing accounts. "
                        "AIR MILES $17.95 per month plus get 50 bonus miles /month with a $4,000 minimum daily balance. "
                        "Unlimited transactions and INTERAC e-Transfer transactions. "
                        "Performance $17.95 per month or $0 with a $4,000 minimum balance. "
                        "Important banking info Report a lost or stolen card Interest rates Banking services Banking agreements. "
                        "Student banking Newcomer offers."
                    ),
                    retrieval_metadata={},
                    source_document_id="src-bmo-chq-air-miles",
                    source_snapshot_id="snap-bmo-chq-air-miles",
                    bank_code="BMO",
                    country_code="CA",
                    source_type="html",
                ),
                EvidenceChunkCandidate(
                    evidence_chunk_id="chunk-bmo-air-miles-eligibility",
                    parsed_document_id="parsed-bmo-chq-air-miles",
                    chunk_index=2,
                    anchor_type="section",
                    anchor_value="what-is-an-air-miles-chequing-account",
                    page_no=None,
                    source_language="en",
                    evidence_excerpt=(
                        "What is an AIR MILES Chequing account? An AIR MILES chequing account is a bank account "
                        "that allows you to collect AIR MILES points on every transaction you make with the account. "
                        "The amount of AIR MILES points you earn per transaction depends on the terms and conditions "
                        "of the chequing account, as well as any offers or promotions related to the account. "
                        "How do I open an AIR MILES Chequing account at BMO? You can open an BMO AIR MILES Chequing "
                        "Account online. You do not need an existing BMO chequing or savings account to apply."
                    ),
                    retrieval_metadata={},
                    source_document_id="src-bmo-chq-air-miles",
                    source_snapshot_id="snap-bmo-chq-air-miles",
                    bank_code="BMO",
                    country_code="CA",
                    source_type="html",
                ),
            ]
            storage_config = ExtractionStorageConfig(
                driver="filesystem",
                env_prefix="dev",
                extraction_object_prefix="extracted",
                retention_class="hot",
                filesystem_root=str(temp_path),
            )
            service = ExtractionService(
                storage_config=storage_config,
                object_store=build_object_store(storage_config),
            )

            result = service.extract_documents(
                run_id="run-bmo-air-miles-chq",
                correlation_id="corr-bmo-air-miles-chq",
                request_id="req-bmo-air-miles-chq",
                inputs=[ExtractionInput(context=context, candidates=candidates)],
            )

            extracted_by_field = {item.field_name: item for item in result.source_results[0].extracted_fields}
            self.assertEqual(extracted_by_field["product_name"].candidate_value, "AIR MILES Chequing Account")
            self.assertEqual(extracted_by_field["monthly_fee"].candidate_value, "17.95")
            self.assertEqual(extracted_by_field["public_display_fee"].candidate_value, "17.95")
            self.assertEqual(extracted_by_field["minimum_balance"].candidate_value, "4000.00")
            self.assertEqual(
                extracted_by_field["eligibility_text"].candidate_value,
                "You do not need an existing BMO chequing or savings account to apply",
            )
            self.assertNotIn("offers or promotions", extracted_by_field["eligibility_text"].candidate_value.lower())
            self.assertTrue(extracted_by_field["unlimited_transactions_flag"].candidate_value)
            self.assertTrue(extracted_by_field["interac_e_transfer_included"].candidate_value)
            self.assertNotIn("fee_waiver_condition", extracted_by_field)
            self.assertNotIn("cheque_book_info", extracted_by_field)
            self.assertNotIn("student_plan_flag", extracted_by_field)
            self.assertNotIn("newcomer_plan_flag", extracted_by_field)
            self.assertNotIn("interest_calculation_method", extracted_by_field)
            self.assertNotIn("interest_payment_frequency", extracted_by_field)
            self.assertNotIn("compounding_frequency", extracted_by_field)
            self.assertNotIn("rewards_benefits", extracted_by_field)
        finally:
            rmtree(temp_path, ignore_errors=True)

    def test_bmo_premium_chequing_maps_own_fee_and_balance_without_cross_product_noise(self) -> None:
        temp_path = _prepare_workspace_temp_dir("extraction-bmo-premium-chequing")
        try:
            context = ExtractionDocumentContext(
                source_id="BMO-CHQ-005",
                parsed_document_id="parsed-bmo-chq-premium",
                source_document_id="src-bmo-chq-premium",
                snapshot_id="snap-bmo-chq-premium",
                bank_code="BMO",
                country_code="CA",
                source_type="html",
                source_language="en",
                source_metadata={
                    "product_type": "chequing",
                    "expected_fields": [
                        "monthly_fee",
                        "public_display_fee",
                        "minimum_balance",
                        "fee_waiver_condition",
                        "cheque_book_info",
                        "student_plan_flag",
                        "newcomer_plan_flag",
                        "interest_calculation_method",
                        "interest_payment_frequency",
                        "tier_definition_text",
                        "withdrawal_limit_text",
                        "family_bundle_benefits",
                    ],
                },
            )
            candidates = [
                EvidenceChunkCandidate(
                    evidence_chunk_id="chunk-bmo-premium-title",
                    parsed_document_id="parsed-bmo-chq-premium",
                    chunk_index=0,
                    anchor_type="section",
                    anchor_value="premium-chequing-account",
                    page_no=None,
                    source_language="en",
                    evidence_excerpt=(
                        "Premium Chequing Account\n"
                        "Be in control of your finances and enjoy exclusive perks."
                    ),
                    retrieval_metadata={},
                    source_document_id="src-bmo-chq-premium",
                    source_snapshot_id="snap-bmo-chq-premium",
                    bank_code="BMO",
                    country_code="CA",
                    source_type="html",
                ),
                EvidenceChunkCandidate(
                    evidence_chunk_id="chunk-bmo-premium-fees",
                    parsed_document_id="parsed-bmo-chq-premium",
                    chunk_index=1,
                    anchor_type="section",
                    anchor_value="explore-the-bonuses-features-and-fees-for-our-chequing-accounts",
                    page_no=None,
                    source_language="en",
                    evidence_excerpt=(
                        "Explore the bonuses, features and fees for our chequing accounts. "
                        "Premium $30.95 per month or $0 with a $6,000 minimum balance. "
                        "Unlimited transactions and INTERAC e-Transfer transactions. "
                        "Additional features No fee for select Cheques No fee for Stop Payments. "
                        "Savings Amplifier Account promotional interest rate. "
                        "Performance $17.95 per month or $0 with a $4,000 minimum balance. "
                        "Plus $12.95 per month or $0 with a $3,000 minimum balance. "
                        "Student banking Newcomer offers Important banking info Interest rates Banking agreements."
                    ),
                    retrieval_metadata={},
                    source_document_id="src-bmo-chq-premium",
                    source_snapshot_id="snap-bmo-chq-premium",
                    bank_code="BMO",
                    country_code="CA",
                    source_type="html",
                ),
            ]
            storage_config = ExtractionStorageConfig(
                driver="filesystem",
                env_prefix="dev",
                extraction_object_prefix="extracted",
                retention_class="hot",
                filesystem_root=str(temp_path),
            )
            service = ExtractionService(
                storage_config=storage_config,
                object_store=build_object_store(storage_config),
            )

            result = service.extract_documents(
                run_id="run-bmo-premium-chq",
                correlation_id="corr-bmo-premium-chq",
                request_id="req-bmo-premium-chq",
                inputs=[ExtractionInput(context=context, candidates=candidates)],
            )

            extracted_by_field = {item.field_name: item for item in result.source_results[0].extracted_fields}
            self.assertEqual(extracted_by_field["product_name"].candidate_value, "Premium Chequing Account")
            self.assertEqual(extracted_by_field["monthly_fee"].candidate_value, "30.95")
            self.assertEqual(extracted_by_field["public_display_fee"].candidate_value, "30.95")
            self.assertEqual(extracted_by_field["minimum_balance"].candidate_value, "6000.00")
            self.assertIn("6000.00 minimum balance", extracted_by_field["fee_waiver_condition"].candidate_value)
            self.assertTrue(extracted_by_field["unlimited_transactions_flag"].candidate_value)
            self.assertTrue(extracted_by_field["interac_e_transfer_included"].candidate_value)
            self.assertEqual(extracted_by_field["cheque_book_info"].candidate_value, "No fee for select Cheques.")
            self.assertNotIn("student_plan_flag", extracted_by_field)
            self.assertNotIn("newcomer_plan_flag", extracted_by_field)
            self.assertNotIn("interest_calculation_method", extracted_by_field)
            self.assertNotIn("interest_payment_frequency", extracted_by_field)
            self.assertNotIn("tier_definition_text", extracted_by_field)
            self.assertNotIn("withdrawal_limit_text", extracted_by_field)
            self.assertNotIn("family_bundle_benefits", extracted_by_field)
        finally:
            rmtree(temp_path, ignore_errors=True)

    def test_extracts_savings_specific_fields(self) -> None:
        temp_path = _prepare_workspace_temp_dir("extraction-savings-service")
        try:
            context = ExtractionDocumentContext(
                source_id="RBC-SAV-004",
                parsed_document_id="parsed-sav-001",
                source_document_id="src-sav-001",
                snapshot_id="snap-sav-001",
                bank_code="RBC",
                country_code="CA",
                source_type="html",
                source_language="en",
                source_metadata={
                    "product_type": "savings",
                    "expected_fields": [
                        "standard_rate",
                        "interest_calculation_method",
                        "interest_payment_frequency",
                        "tiered_rate_flag",
                        "tier_definition_text",
                        "withdrawal_limit_text",
                        "registered_flag",
                    ],
                },
            )
            candidates = [
                EvidenceChunkCandidate(
                    evidence_chunk_id="chunk-sav-001",
                    parsed_document_id="parsed-sav-001",
                    chunk_index=0,
                    anchor_type="section",
                    anchor_value="high-interest-esavings",
                    page_no=None,
                    source_language="en",
                    evidence_excerpt="RBC High Interest eSavings\nA high-interest savings account with no monthly fee.",
                    retrieval_metadata={},
                    source_document_id="src-sav-001",
                    source_snapshot_id="snap-sav-001",
                    bank_code="RBC",
                    country_code="CA",
                    source_type="html",
                ),
                EvidenceChunkCandidate(
                    evidence_chunk_id="chunk-sav-002",
                    parsed_document_id="parsed-sav-001",
                    chunk_index=1,
                    anchor_type="section",
                    anchor_value="interest-rates",
                    page_no=None,
                    source_language="en",
                    evidence_excerpt=(
                        "Earn 1.60% interest. Interest is calculated on the daily closing balance and paid monthly. "
                        "Tiered interest rates apply: balances of $0 to $4,999.99 earn 1.60%; $5,000 and over earn 1.80%."
                    ),
                    retrieval_metadata={},
                    source_document_id="src-sav-001",
                    source_snapshot_id="snap-sav-001",
                    bank_code="RBC",
                    country_code="CA",
                    source_type="html",
                ),
                EvidenceChunkCandidate(
                    evidence_chunk_id="chunk-sav-003",
                    parsed_document_id="parsed-sav-001",
                    chunk_index=2,
                    anchor_type="section",
                    anchor_value="account-details",
                    page_no=None,
                    source_language="en",
                    evidence_excerpt="One debit transaction per month is included. Additional withdrawals cost $5 each.",
                    retrieval_metadata={},
                    source_document_id="src-sav-001",
                    source_snapshot_id="snap-sav-001",
                    bank_code="RBC",
                    country_code="CA",
                    source_type="html",
                ),
                EvidenceChunkCandidate(
                    evidence_chunk_id="chunk-sav-004",
                    parsed_document_id="parsed-sav-001",
                    chunk_index=3,
                    anchor_type="section",
                    anchor_value="registered-options",
                    page_no=None,
                    source_language="en",
                    evidence_excerpt="Also available as a TFSA savings option.",
                    retrieval_metadata={},
                    source_document_id="src-sav-001",
                    source_snapshot_id="snap-sav-001",
                    bank_code="RBC",
                    country_code="CA",
                    source_type="html",
                ),
            ]
            storage_config = ExtractionStorageConfig(
                driver="filesystem",
                env_prefix="dev",
                extraction_object_prefix="extracted",
                retention_class="hot",
                filesystem_root=str(temp_path),
            )
            service = ExtractionService(
                storage_config=storage_config,
                object_store=build_object_store(storage_config),
            )

            result = service.extract_documents(
                run_id="run-sav-001",
                correlation_id="corr-sav-001",
                request_id="req-sav-001",
                inputs=[ExtractionInput(context=context, candidates=candidates)],
            )

            source_result = result.source_results[0]
            extracted_by_field = {item.field_name: item for item in source_result.extracted_fields}
            self.assertEqual(extracted_by_field["product_type"].candidate_value, "savings")
            self.assertEqual(extracted_by_field["standard_rate"].candidate_value, "1.60")
            self.assertEqual(
                extracted_by_field["interest_calculation_method"].candidate_value,
                "Interest is calculated on the daily closing balance and paid monthly.",
            )
            self.assertEqual(extracted_by_field["interest_payment_frequency"].candidate_value, "monthly")
            self.assertTrue(extracted_by_field["tiered_rate_flag"].candidate_value)
            self.assertIn("Tiered interest rates apply", extracted_by_field["tier_definition_text"].candidate_value)
            self.assertIn("withdrawals cost $5 each", extracted_by_field["withdrawal_limit_text"].candidate_value)
            self.assertTrue(extracted_by_field["registered_flag"].candidate_value)
        finally:
            rmtree(temp_path, ignore_errors=True)

    def test_bmo_us_dollar_savings_extracts_foreign_currency_fields_without_table_noise(self) -> None:
        temp_path = _prepare_workspace_temp_dir("extraction-bmo-usd-savings")
        try:
            context = ExtractionDocumentContext(
                source_id="BMO-SAV-005",
                parsed_document_id="parsed-bmo-usd-sav",
                source_document_id="src-bmo-usd-sav",
                snapshot_id="snap-bmo-usd-sav",
                bank_code="BMO",
                country_code="CA",
                source_type="html",
                source_language="en",
                source_metadata={
                    "product_type": "savings",
                    "expected_fields": [
                        "standard_rate",
                        "public_display_rate",
                        "promotional_rate",
                        "introductory_rate_flag",
                        "interest_calculation_method",
                        "interest_payment_frequency",
                        "eligibility_text",
                        "tier_definition_text",
                        "withdrawal_limit_text",
                        "notes",
                    ],
                },
            )
            candidates = [
                EvidenceChunkCandidate(
                    evidence_chunk_id="chunk-bmo-usd-title",
                    parsed_document_id="parsed-bmo-usd-sav",
                    chunk_index=0,
                    anchor_type="section",
                    anchor_value="u-s-dollar-premium-rate-savings-account",
                    page_no=None,
                    source_language="en",
                    evidence_excerpt=(
                        "U S Dollar Premium Rate Savings Account\n"
                        "Save your U.S. dollars with the flexibility to exchange them whenever you need it."
                    ),
                    retrieval_metadata={},
                    source_document_id="src-bmo-usd-sav",
                    source_snapshot_id="snap-bmo-usd-sav",
                    bank_code="BMO",
                    country_code="CA",
                    source_type="html",
                ),
                EvidenceChunkCandidate(
                    evidence_chunk_id="chunk-bmo-usd-fees",
                    parsed_document_id="parsed-bmo-usd-sav",
                    chunk_index=1,
                    anchor_type="section",
                    anchor_value="explore-the-fees-for-the-u-s-dollar-premium-rate-savings-account",
                    page_no=None,
                    source_language="en",
                    evidence_excerpt=(
                        "Explore the fees for the U.S. Dollar Premium Rate Savings Account Features Details "
                        "Monthly account fee Fee based on Plan limits Interest rate 0.050% interest rate *12 "
                        "Monthly savings requirement $0 Number of transactions per month Transactions based on Plan limits *7, *25 "
                        "Maximum number of accounts 1 with Practical Plan 20 with all other Plans *1, *3 "
                        "Eligibility with Plans *3 Can be included in any Bank Plan "
                        "Full disclosure for the BMO U.S. dollar Premium Rate Savings account"
                    ),
                    retrieval_metadata={},
                    source_document_id="src-bmo-usd-sav",
                    source_snapshot_id="snap-bmo-usd-sav",
                    bank_code="BMO",
                    country_code="CA",
                    source_type="html",
                ),
                EvidenceChunkCandidate(
                    evidence_chunk_id="chunk-bmo-usd-interest",
                    parsed_document_id="parsed-bmo-usd-sav",
                    chunk_index=2,
                    anchor_type="section",
                    anchor_value="earn-interest",
                    page_no=None,
                    source_language="en",
                    evidence_excerpt="Earn interest on your U.S. dollars and more. 0.050% interest rate *12. Earn daily interest on every dollar.",
                    retrieval_metadata={},
                    source_document_id="src-bmo-usd-sav",
                    source_snapshot_id="snap-bmo-usd-sav",
                    bank_code="BMO",
                    country_code="CA",
                    source_type="html",
                ),
                EvidenceChunkCandidate(
                    evidence_chunk_id="chunk-bmo-usd-faq",
                    parsed_document_id="parsed-bmo-usd-sav",
                    chunk_index=3,
                    anchor_type="section",
                    anchor_value="faqs",
                    page_no=None,
                    source_language="en",
                    evidence_excerpt="What are the transaction limits of a U.S. Dollar Premium Rate Savings Account?",
                    retrieval_metadata={},
                    source_document_id="src-bmo-usd-sav",
                    source_snapshot_id="snap-bmo-usd-sav",
                    bank_code="BMO",
                    country_code="CA",
                    source_type="html",
                ),
            ]
            storage_config = ExtractionStorageConfig(
                driver="filesystem",
                env_prefix="dev",
                extraction_object_prefix="extracted",
                retention_class="hot",
                filesystem_root=str(temp_path),
            )
            service = ExtractionService(
                storage_config=storage_config,
                object_store=build_object_store(storage_config),
            )

            result = service.extract_documents(
                run_id="run-bmo-usd-sav",
                correlation_id="corr-bmo-usd-sav",
                request_id="req-bmo-usd-sav",
                inputs=[ExtractionInput(context=context, candidates=candidates)],
            )

            extracted_by_field = {item.field_name: item for item in result.source_results[0].extracted_fields}
            self.assertEqual(extracted_by_field["product_name"].candidate_value, "U.S. Dollar Premium Rate Savings Account")
            self.assertEqual(extracted_by_field["currency"].candidate_value, "USD")
            self.assertEqual(extracted_by_field["standard_rate"].candidate_value, "0.05")
            self.assertEqual(extracted_by_field["public_display_rate"].candidate_value, "0.05")
            self.assertEqual(extracted_by_field["interest_calculation_method"].candidate_value, "Earn daily interest on every dollar")
            self.assertEqual(extracted_by_field["eligibility_text"].candidate_value, "Can be included in any bank plan")
            self.assertEqual(
                extracted_by_field["withdrawal_limit_text"].candidate_value,
                "Number of transactions per month: Transactions based on Plan limits.",
            )
            self.assertNotIn("promotional_rate", extracted_by_field)
            self.assertNotIn("introductory_rate_flag", extracted_by_field)
            self.assertNotIn("interest_payment_frequency", extracted_by_field)
            self.assertNotIn("tier_definition_text", extracted_by_field)
            self.assertNotIn("notes", extracted_by_field)
        finally:
            rmtree(temp_path, ignore_errors=True)

    def test_bmo_premium_rate_savings_extracts_plan_fields_without_faq_noise(self) -> None:
        temp_path = _prepare_workspace_temp_dir("extraction-bmo-premium-rate-savings")
        try:
            context = ExtractionDocumentContext(
                source_id="BMO-SAV-004",
                parsed_document_id="parsed-bmo-premium-rate-sav",
                source_document_id="src-bmo-premium-rate-sav",
                snapshot_id="snap-bmo-premium-rate-sav",
                bank_code="BMO",
                country_code="CA",
                source_type="html",
                source_language="en",
                source_metadata={
                    "product_type": "savings",
                    "expected_fields": [
                        "standard_rate",
                        "public_display_rate",
                        "promotional_rate",
                        "introductory_rate_flag",
                        "interest_calculation_method",
                        "interest_payment_frequency",
                        "eligibility_text",
                        "tier_definition_text",
                        "withdrawal_limit_text",
                        "notes",
                    ],
                },
            )
            candidates = [
                EvidenceChunkCandidate(
                    evidence_chunk_id="chunk-bmo-premium-rate-title",
                    parsed_document_id="parsed-bmo-premium-rate-sav",
                    chunk_index=0,
                    anchor_type="section",
                    anchor_value="premium-rate-savings-account",
                    page_no=None,
                    source_language="en",
                    evidence_excerpt=(
                        "Premium Rate Savings Account\n"
                        "A flexible, convenient account that pairs seamlessly with a chequing account in one plan."
                    ),
                    retrieval_metadata={},
                    source_document_id="src-bmo-premium-rate-sav",
                    source_snapshot_id="snap-bmo-premium-rate-sav",
                    bank_code="BMO",
                    country_code="CA",
                    source_type="html",
                ),
                EvidenceChunkCandidate(
                    evidence_chunk_id="chunk-bmo-premium-rate-features",
                    parsed_document_id="parsed-bmo-premium-rate-sav",
                    chunk_index=1,
                    anchor_type="section",
                    anchor_value="explore-the-features-of-the-premium-rate-savings-account",
                    page_no=None,
                    source_language="en",
                    evidence_excerpt=(
                        "Explore the features of the Premium Rate Savings Account Features Details "
                        "Monthly account fee Fee based on Plan limits Interest rate 0.010% interest rate *12 "
                        "Monthly savings requirement $0 Number of transactions per month Transactions based on Plan limits *7, *105 "
                        "Maximum number of accounts 1 with Practical Plan 20 with all other Plans *1, *3 "
                        "Eligibility with Plans *3 Can be included in any Bank Plan "
                        "Full disclosure for the BMO Premium Rate Savings account."
                    ),
                    retrieval_metadata={},
                    source_document_id="src-bmo-premium-rate-sav",
                    source_snapshot_id="snap-bmo-premium-rate-sav",
                    bank_code="BMO",
                    country_code="CA",
                    source_type="html",
                ),
                EvidenceChunkCandidate(
                    evidence_chunk_id="chunk-bmo-premium-rate-faq",
                    parsed_document_id="parsed-bmo-premium-rate-sav",
                    chunk_index=2,
                    anchor_type="section",
                    anchor_value="premium-rate-savings-account-faqs",
                    page_no=None,
                    source_language="en",
                    evidence_excerpt=(
                        "Premium Rate Savings Account FAQs What is a Premium Rate Savings Account? "
                        "A Premium Rate Savings Account functions like a regular savings account where you can store your money "
                        "and earn interest, but with added perks. "
                        "What are the transaction limits of a Premium Savings Account?"
                    ),
                    retrieval_metadata={},
                    source_document_id="src-bmo-premium-rate-sav",
                    source_snapshot_id="snap-bmo-premium-rate-sav",
                    bank_code="BMO",
                    country_code="CA",
                    source_type="html",
                ),
            ]
            storage_config = ExtractionStorageConfig(
                driver="filesystem",
                env_prefix="dev",
                extraction_object_prefix="extracted",
                retention_class="hot",
                filesystem_root=str(temp_path),
            )
            service = ExtractionService(
                storage_config=storage_config,
                object_store=build_object_store(storage_config),
            )

            result = service.extract_documents(
                run_id="run-bmo-premium-rate-sav",
                correlation_id="corr-bmo-premium-rate-sav",
                request_id="req-bmo-premium-rate-sav",
                inputs=[ExtractionInput(context=context, candidates=candidates)],
            )

            extracted_by_field = {item.field_name: item for item in result.source_results[0].extracted_fields}
            self.assertEqual(extracted_by_field["product_name"].candidate_value, "Premium Rate Savings Account")
            self.assertEqual(extracted_by_field["currency"].candidate_value, "CAD")
            self.assertEqual(extracted_by_field["standard_rate"].candidate_value, "0.01")
            self.assertEqual(extracted_by_field["public_display_rate"].candidate_value, "0.01")
            self.assertEqual(extracted_by_field["eligibility_text"].candidate_value, "Can be included in any bank plan")
            self.assertEqual(
                extracted_by_field["withdrawal_limit_text"].candidate_value,
                "Number of transactions per month: Transactions based on Plan limits.",
            )
            self.assertNotIn("promotional_rate", extracted_by_field)
            self.assertNotIn("introductory_rate_flag", extracted_by_field)
            self.assertNotIn("interest_calculation_method", extracted_by_field)
            self.assertNotIn("interest_payment_frequency", extracted_by_field)
            self.assertNotIn("tier_definition_text", extracted_by_field)
            self.assertNotIn("notes", extracted_by_field)
        finally:
            rmtree(temp_path, ignore_errors=True)

    def test_savings_defaults_ignore_chequing_noise_and_cross_product_usd(self) -> None:
        temp_path = _prepare_workspace_temp_dir("extraction-bmo-savings-noise")
        try:
            context = ExtractionDocumentContext(
                source_id="BMO-SAV-002",
                parsed_document_id="parsed-bmo-sav-noise",
                source_document_id="src-bmo-sav-noise",
                snapshot_id="snap-bmo-sav-noise",
                bank_code="BMO",
                country_code="CA",
                source_type="html",
                source_language="en",
                source_metadata={
                    "product_type": "savings",
                    "product_name": "Savings Amplifier Account",
                    "expected_fields": ["minimum_deposit"],
                },
            )
            candidates = [
                EvidenceChunkCandidate(
                    evidence_chunk_id="chunk-bmo-noise-001",
                    parsed_document_id="parsed-bmo-sav-noise",
                    chunk_index=0,
                    anchor_type="section",
                    anchor_value="rates-and-fees",
                    page_no=None,
                    source_language="en",
                    evidence_excerpt=(
                        "Savings Amplifier Account\n"
                        "Monthly fee $0. $0 minimum opening deposit. "
                        "A $5 fee applies to selected assisted transactions."
                    ),
                    retrieval_metadata={},
                    source_document_id="src-bmo-sav-noise",
                    source_snapshot_id="snap-bmo-sav-noise",
                    bank_code="BMO",
                    country_code="CA",
                    source_type="html",
                ),
                EvidenceChunkCandidate(
                    evidence_chunk_id="chunk-bmo-noise-002",
                    parsed_document_id="parsed-bmo-sav-noise",
                    chunk_index=1,
                    anchor_type="section",
                    anchor_value="important-banking-info",
                    page_no=None,
                    source_language="en",
                    evidence_excerpt="Important banking info Report a lost or stolen card Interest rates Banking services Banking agreements Cross border banking",
                    retrieval_metadata={},
                    source_document_id="src-bmo-sav-noise",
                    source_snapshot_id="snap-bmo-sav-noise",
                    bank_code="BMO",
                    country_code="CA",
                    source_type="html",
                ),
                EvidenceChunkCandidate(
                    evidence_chunk_id="chunk-bmo-noise-003",
                    parsed_document_id="parsed-bmo-sav-noise",
                    chunk_index=2,
                    anchor_type="section",
                    anchor_value="faq",
                    page_no=None,
                    source_language="en",
                    evidence_excerpt="BMO also offers a U.S. Dollar Premium Rate Savings account for customers who save in U.S. dollars.",
                    retrieval_metadata={},
                    source_document_id="src-bmo-sav-noise",
                    source_snapshot_id="snap-bmo-sav-noise",
                    bank_code="BMO",
                    country_code="CA",
                    source_type="html",
                ),
            ]
            storage_config = ExtractionStorageConfig(
                driver="filesystem",
                env_prefix="dev",
                extraction_object_prefix="extracted",
                retention_class="hot",
                filesystem_root=str(temp_path),
            )
            service = ExtractionService(storage_config=storage_config, object_store=build_object_store(storage_config))

            result = service.extract_documents(
                run_id="run-bmo-sav-noise",
                correlation_id="corr-bmo-sav-noise",
                request_id="req-bmo-sav-noise",
                inputs=[ExtractionInput(context=context, candidates=candidates)],
            )

            extracted_by_field = {item.field_name: item for item in result.source_results[0].extracted_fields}
            self.assertEqual(extracted_by_field["currency"].candidate_value, "CAD")
            self.assertEqual(extracted_by_field["minimum_deposit"].candidate_value, "0.00")
            self.assertNotIn("cheque_book_info", extracted_by_field)
            self.assertNotIn("Important banking info", str(extracted_by_field.get("notes", "")))
            self.assertNotIn("Important banking info", str(extracted_by_field.get("interest_calculation_method", "")))
        finally:
            rmtree(temp_path, ignore_errors=True)

    def test_extracts_bmo_product_name_from_noisy_pdf_candidates(self) -> None:
        temp_path = _prepare_workspace_temp_dir("extraction-bmo-pdf-title")
        try:
            context = ExtractionDocumentContext(
                source_id="BMO-SAV-002",
                parsed_document_id="parsed-bmo-sav-001",
                source_document_id="src-bmo-sav-001",
                snapshot_id="snap-bmo-sav-001",
                bank_code="BMO",
                country_code="CA",
                source_type="pdf",
                source_language="en",
                source_metadata={
                    "product_type": "savings",
                    "expected_fields": ["product_name", "monthly_fee"],
                },
            )
            candidates = [
                EvidenceChunkCandidate(
                    evidence_chunk_id="chunk-bmo-001",
                    parsed_document_id="parsed-bmo-sav-001",
                    chunk_index=0,
                    anchor_type="page",
                    anchor_value="page-1",
                    page_no=1,
                    source_language="en",
                    evidence_excerpt=(
                        "B E N E F I T S\n"
                        "Get a high interest rate, pay no monthly plan fee, and more\n"
                        "Earn a 0.50% savings interest rate or a promotional rate of 4.50%\n"
                        "Benefits Rates and Fees Mobile FAQs"
                    ),
                    retrieval_metadata={},
                    source_document_id="src-bmo-sav-001",
                    source_snapshot_id="snap-bmo-sav-001",
                    bank_code="BMO",
                    country_code="CA",
                    source_type="pdf",
                ),
                EvidenceChunkCandidate(
                    evidence_chunk_id="chunk-bmo-002",
                    parsed_document_id="parsed-bmo-sav-001",
                    chunk_index=1,
                    anchor_type="page",
                    anchor_value="page-2",
                    page_no=2,
                    source_language="en",
                    evidence_excerpt=(
                        "Sign up for BMO Online Banking\n"
                        "Savings Amplifier Account FAQs\n"
                        "What is a savings account?"
                    ),
                    retrieval_metadata={},
                    source_document_id="src-bmo-sav-001",
                    source_snapshot_id="snap-bmo-sav-001",
                    bank_code="BMO",
                    country_code="CA",
                    source_type="pdf",
                ),
                EvidenceChunkCandidate(
                    evidence_chunk_id="chunk-bmo-003",
                    parsed_document_id="parsed-bmo-sav-001",
                    chunk_index=2,
                    anchor_type="page",
                    anchor_value="page-3",
                    page_no=3,
                    source_language="en",
                    evidence_excerpt=(
                        "R A T E S A N D F E E S\n"
                        "Explore the features of the Savings Amplifier Account\n"
                        "Monthly fee $0"
                    ),
                    retrieval_metadata={},
                    source_document_id="src-bmo-sav-001",
                    source_snapshot_id="snap-bmo-sav-001",
                    bank_code="BMO",
                    country_code="CA",
                    source_type="pdf",
                ),
            ]
            storage_config = ExtractionStorageConfig(
                driver="filesystem",
                env_prefix="dev",
                extraction_object_prefix="extracted",
                retention_class="hot",
                filesystem_root=str(temp_path),
            )
            service = ExtractionService(
                storage_config=storage_config,
                object_store=build_object_store(storage_config),
            )

            result = service.extract_documents(
                run_id="run-bmo-sav-001",
                correlation_id="corr-bmo-sav-001",
                request_id="req-bmo-sav-001",
                inputs=[ExtractionInput(context=context, candidates=candidates)],
            )

            extracted_by_field = {item.field_name: item for item in result.source_results[0].extracted_fields}
            self.assertEqual(extracted_by_field["product_name"].candidate_value, "Savings Amplifier Account")
            self.assertEqual(extracted_by_field["monthly_fee"].candidate_value, "0.00")
        finally:
            rmtree(temp_path, ignore_errors=True)

    def test_extracts_product_name_from_marketing_wrapper_headings(self) -> None:
        temp_path = _prepare_workspace_temp_dir("extraction-wrapper-title")
        try:
            context = ExtractionDocumentContext(
                source_id="TD-GIC-003",
                parsed_document_id="parsed-td-gic-003",
                source_document_id="src-td-gic-003",
                snapshot_id="snap-td-gic-003",
                bank_code="TD",
                country_code="CA",
                source_type="html",
                source_language="en",
                source_metadata={"product_type": "gic", "expected_fields": ["product_name"]},
            )
            candidates = [
                EvidenceChunkCandidate(
                    evidence_chunk_id="chunk-wrapper-001",
                    parsed_document_id="parsed-td-gic-003",
                    chunk_index=0,
                    anchor_type="section",
                    anchor_value="benefits-of-td-special-offer-gics",
                    page_no=None,
                    source_language="en",
                    evidence_excerpt=(
                        "Benefits of TD Special Offer GICs\n"
                        "Potentially earn a higher rate than traditional GICs."
                    ),
                    retrieval_metadata={},
                    source_document_id="src-td-gic-003",
                    source_snapshot_id="snap-td-gic-003",
                    bank_code="TD",
                    country_code="CA",
                    source_type="html",
                )
            ]
            storage_config = ExtractionStorageConfig(
                driver="filesystem",
                env_prefix="dev",
                extraction_object_prefix="extracted",
                retention_class="hot",
                filesystem_root=str(temp_path),
            )
            service = ExtractionService(storage_config=storage_config, object_store=build_object_store(storage_config))

            result = service.extract_documents(
                run_id="run-wrapper-001",
                correlation_id="corr-wrapper-001",
                request_id="req-wrapper-001",
                inputs=[ExtractionInput(context=context, candidates=candidates)],
            )

            extracted_by_field = {item.field_name: item for item in result.source_results[0].extracted_fields}
            self.assertEqual(extracted_by_field["product_name"].candidate_value, "TD Special Offer GICs")
        finally:
            rmtree(temp_path, ignore_errors=True)

    def test_product_title_rejects_embedded_legal_document_heading(self) -> None:
        context = ExtractionDocumentContext(
            source_id="AUTO-BOAN-CHE-001",
            parsed_document_id="parsed-boan-che-001",
            source_document_id="src-boan-che-001",
            snapshot_id="snap-boan-che-001",
            bank_code="BOAN",
            country_code="US",
            source_type="html",
            source_language="en",
            source_metadata={
                "product_type": "chequing",
                "discovery_metadata": {
                    "page_title": "Bank of America Advantage Banking: Open a Checking Account Today",
                    "primary_heading": "Please select your county",
                    "candidate_origin": "homepage_or_hub_link",
                    "ai_parallel_score": 9.5,
                    "ai_predicted_role": "detail",
                    "ai_confidence_band": "high",
                    "page_evidence_reason_codes": [
                        "product_identity_signal",
                        "structured_component_evidence",
                        "location_access_gate",
                        "title_semantic_match",
                    ],
                },
            },
        )
        candidate = EvidenceChunkCandidate(
            evidence_chunk_id="chunk-boan-legal",
            parsed_document_id="parsed-boan-che-001",
            chunk_index=0,
            anchor_type="structured_component",
            anchor_value="structured-component-1",
            page_no=None,
            source_language="en",
            evidence_excerpt=(
                "Deposit Agreement and Disclosures\n"
                "Online Banking Service Agreement\n"
                "Enroll now in online banking\n"
                "Bank of America Advantage Banking gives customers checking account options."
            ),
            retrieval_metadata={},
            source_document_id="src-boan-che-001",
            source_snapshot_id="snap-boan-che-001",
            bank_code="BOAN",
            country_code="US",
            source_type="html",
        )

        self.assertEqual(
            _extract_document_title(context=context, candidates=[candidate]),
            "Bank of America Advantage Banking",
        )
        self.assertEqual(_clean_title_candidate("Online Banking Service Agreement"), "")
        self.assertEqual(_clean_title_candidate("Deposit Agreement and Disclosures"), "")
        self.assertEqual(_clean_title_candidate("Credit Card Agreement & Disclosure"), "")
        self.assertEqual(_clean_title_candidate("Privacy Notice"), "")
        self.assertEqual(
            _clean_title_candidate("Bank of America Advantage Banking: Open a Checking Account Today"),
            "Bank of America Advantage Banking",
        )
        self.assertEqual(
            _clean_title_candidate("Certificate of Deposit - View CD Rates and Account Options"),
            "Certificate of Deposit",
        )
        self.assertEqual(
            _clean_title_candidate("Open a Bank of America Advantage Savings Account Online"),
            "Bank of America Advantage Savings Account",
        )
        self.assertEqual(_clean_title_candidate("Enroll now in online banking"), "")
        self.assertEqual(_clean_title_candidate("Account options made simple"), "")
        self.assertEqual(_clean_title_candidate("Try the Savings Goal Calculator"), "")

    def test_extracts_product_name_prefers_real_account_name_over_feature_heading(self) -> None:
        temp_path = _prepare_workspace_temp_dir("extraction-feature-title")
        try:
            context = ExtractionDocumentContext(
                source_id="RBC-SAV-002",
                parsed_document_id="parsed-rbc-sav-002",
                source_document_id="src-rbc-sav-002",
                snapshot_id="snap-rbc-sav-002",
                bank_code="RBC",
                country_code="CA",
                source_type="html",
                source_language="en",
                source_metadata={"product_type": "savings", "expected_fields": ["product_name"]},
            )
            candidates = [
                EvidenceChunkCandidate(
                    evidence_chunk_id="chunk-feature-001",
                    parsed_document_id="parsed-rbc-sav-002",
                    chunk_index=0,
                    anchor_type="section",
                    anchor_value="more-great-account-features",
                    page_no=None,
                    source_language="en",
                    evidence_excerpt=(
                        "More Great Account Features\n"
                        "RBC High Interest eSavings Account\n"
                        "Earn interest daily and pay no monthly fee."
                    ),
                    retrieval_metadata={},
                    source_document_id="src-rbc-sav-002",
                    source_snapshot_id="snap-rbc-sav-002",
                    bank_code="RBC",
                    country_code="CA",
                    source_type="html",
                )
            ]
            storage_config = ExtractionStorageConfig(
                driver="filesystem",
                env_prefix="dev",
                extraction_object_prefix="extracted",
                retention_class="hot",
                filesystem_root=str(temp_path),
            )
            service = ExtractionService(storage_config=storage_config, object_store=build_object_store(storage_config))

            result = service.extract_documents(
                run_id="run-feature-001",
                correlation_id="corr-feature-001",
                request_id="req-feature-001",
                inputs=[ExtractionInput(context=context, candidates=candidates)],
            )

            extracted_by_field = {item.field_name: item for item in result.source_results[0].extracted_fields}
            self.assertEqual(extracted_by_field["product_name"].candidate_value, "RBC High Interest eSavings Account")
        finally:
            rmtree(temp_path, ignore_errors=True)

    def test_bmo_us_dollar_savings_uses_source_product_title_not_feature_heading(self) -> None:
        temp_path = _prepare_workspace_temp_dir("extraction-bmo-us-title")
        try:
            context = ExtractionDocumentContext(
                source_id="BMO-SAV-005",
                parsed_document_id="parsed-bmo-us-sav",
                source_document_id="src-bmo-us-sav",
                snapshot_id="snap-bmo-us-sav",
                bank_code="BMO",
                country_code="CA",
                source_type="html",
                source_language="en",
                source_metadata={"product_type": "savings"},
            )
            candidates = [
                EvidenceChunkCandidate(
                    evidence_chunk_id="chunk-bmo-us-rate",
                    parsed_document_id="parsed-bmo-us-sav",
                    chunk_index=0,
                    anchor_type="section",
                    anchor_value="0-050-interest-rate-12",
                    page_no=None,
                    source_language="en",
                    evidence_excerpt=(
                        "0.050% interest rate *12\n"
                        "Earn daily interest on every dollar\n"
                        "Include in any bank plan Include this account with any chequing account and pay one monthly Plan fee *1, *3"
                    ),
                    retrieval_metadata={},
                    source_document_id="src-bmo-us-sav",
                    source_snapshot_id="snap-bmo-us-sav",
                    bank_code="BMO",
                    country_code="CA",
                    source_type="html",
                ),
                EvidenceChunkCandidate(
                    evidence_chunk_id="chunk-bmo-us-cross-product-promo",
                    parsed_document_id="parsed-bmo-us-sav",
                    chunk_index=1,
                    anchor_type="section",
                    anchor_value="what-type-of-savings-accounts-does-bmo-offer",
                    page_no=None,
                    source_language="en",
                    evidence_excerpt=(
                        "What type of savings accounts does BMO offer? Savings Amplifier: You can earn a promotional "
                        "interest rate when you open a Savings Amplifier Account and a BMO chequing account. "
                        "U.S. Dollar Premium Rate Savings: Save in U.S. dollars and earn interest."
                    ),
                    retrieval_metadata={},
                    source_document_id="src-bmo-us-sav",
                    source_snapshot_id="snap-bmo-us-sav",
                    bank_code="BMO",
                    country_code="CA",
                    source_type="html",
                ),
            ]
            storage_config = ExtractionStorageConfig(
                driver="filesystem",
                env_prefix="dev",
                extraction_object_prefix="extracted",
                retention_class="hot",
                filesystem_root=str(temp_path),
            )
            service = ExtractionService(storage_config=storage_config, object_store=build_object_store(storage_config))

            result = service.extract_documents(
                run_id="run-bmo-us-title",
                correlation_id="corr-bmo-us-title",
                request_id="req-bmo-us-title",
                inputs=[ExtractionInput(context=context, candidates=candidates)],
            )

            extracted_by_field = {item.field_name: item for item in result.source_results[0].extracted_fields}
            self.assertEqual(extracted_by_field["product_name"].candidate_value, "U.S. Dollar Premium Rate Savings Account")
            self.assertNotEqual(extracted_by_field["product_name"].candidate_value, "Include in any bank plan")
            self.assertNotIn("introductory_rate_flag", extracted_by_field)
            self.assertNotIn("promotional_period_text", extracted_by_field)
        finally:
            rmtree(temp_path, ignore_errors=True)

    def test_bmo_savings_supporting_rate_page_keeps_expected_rate_field(self) -> None:
        temp_path = _prepare_workspace_temp_dir("extraction-bmo-support-rates")
        try:
            context = ExtractionDocumentContext(
                source_id="BMO-SAV-006",
                parsed_document_id="parsed-bmo-support-rates",
                source_document_id="src-bmo-support-rates",
                snapshot_id="snap-bmo-support-rates",
                bank_code="BMO",
                country_code="CA",
                source_type="html",
                source_language="en",
                source_metadata={
                    "product_type": "savings",
                    "discovery_role": "supporting_html",
                    "expected_fields": ["savings_account_rates"],
                },
            )
            candidates = [
                EvidenceChunkCandidate(
                    evidence_chunk_id="chunk-bmo-support-amplifier",
                    parsed_document_id="parsed-bmo-support-rates",
                    chunk_index=0,
                    anchor_type="section",
                    anchor_value="savings-amplifier-account",
                    page_no=None,
                    source_language="en",
                    evidence_excerpt="Savings Amplifier Account\nBalance Interest Rate\n$0 and over\n0.500%",
                    retrieval_metadata={},
                    source_document_id="src-bmo-support-rates",
                    source_snapshot_id="snap-bmo-support-rates",
                    bank_code="BMO",
                    country_code="CA",
                    source_type="html",
                )
            ]
            storage_config = ExtractionStorageConfig(
                driver="filesystem",
                env_prefix="dev",
                extraction_object_prefix="extracted",
                retention_class="hot",
                filesystem_root=str(temp_path),
            )
            service = ExtractionService(storage_config=storage_config, object_store=build_object_store(storage_config))

            result = service.extract_documents(
                run_id="run-bmo-support-rates",
                correlation_id="corr-bmo-support-rates",
                request_id="req-bmo-support-rates",
                inputs=[ExtractionInput(context=context, candidates=candidates)],
            )

            source_result = result.source_results[0]
            requested_fields = source_result.model_execution_record["execution_metadata"]["requested_fields"]
            self.assertIn("savings_account_rates", requested_fields)
            self.assertTrue(any(link.field_name == "savings_account_rates" for link in source_result.evidence_links))
            retrieval_matches = source_result.model_execution_record["execution_metadata"]["retrieval_mode"]
            self.assertEqual(retrieval_matches, "metadata-only")
        finally:
            rmtree(temp_path, ignore_errors=True)

    def test_money_extraction_prefers_fee_label_over_unrelated_amounts(self) -> None:
        temp_path = _prepare_workspace_temp_dir("extraction-money-labels")
        try:
            context = ExtractionDocumentContext(
                source_id="CIBC-SAV-002",
                parsed_document_id="parsed-cibc-sav-002",
                source_document_id="src-cibc-sav-002",
                snapshot_id="snap-cibc-sav-002",
                bank_code="CIBC",
                country_code="CA",
                source_type="html",
                source_language="en",
                source_metadata={
                    "product_type": "savings",
                    "expected_fields": ["monthly_fee", "public_display_fee"],
                },
            )
            candidates = [
                EvidenceChunkCandidate(
                    evidence_chunk_id="chunk-cibc-fee-001",
                    parsed_document_id="parsed-cibc-sav-002",
                    chunk_index=0,
                    anchor_type="section",
                    anchor_value="rates-and-fees",
                    page_no=None,
                    source_language="en",
                    evidence_excerpt=(
                        "Rates and fees\n"
                        "Earned on balances up to $200,000 when you save $200 or more in any month. Limits apply.\n"
                        "Monthly fee\n"
                        "$0\n"
                        "Transactions\n"
                        "$5.00 each"
                    ),
                    retrieval_metadata={},
                    source_document_id="src-cibc-sav-002",
                    source_snapshot_id="snap-cibc-sav-002",
                    bank_code="CIBC",
                    country_code="CA",
                    source_type="html",
                )
            ]
            storage_config = ExtractionStorageConfig(
                driver="filesystem",
                env_prefix="dev",
                extraction_object_prefix="extracted",
                retention_class="hot",
                filesystem_root=str(temp_path),
            )
            service = ExtractionService(
                storage_config=storage_config,
                object_store=build_object_store(storage_config),
            )

            result = service.extract_documents(
                run_id="run-cibc-fee-001",
                correlation_id="corr-cibc-fee-001",
                request_id="req-cibc-fee-001",
                inputs=[ExtractionInput(context=context, candidates=candidates)],
            )

            extracted_by_field = {item.field_name: item for item in result.source_results[0].extracted_fields}
            self.assertEqual(extracted_by_field["monthly_fee"].candidate_value, "0.00")
            self.assertEqual(extracted_by_field["public_display_fee"].candidate_value, "0.00")
        finally:
            rmtree(temp_path, ignore_errors=True)

    def test_cibc_us_personal_extracts_title_and_eligibility_without_travel_noise(self) -> None:
        temp_path = _prepare_workspace_temp_dir("extraction-cibc-us-personal")
        try:
            context = ExtractionDocumentContext(
                source_id="CIBC-SAV-003",
                parsed_document_id="parsed-cibc-us-personal",
                source_document_id="src-cibc-us-personal",
                snapshot_id="snap-cibc-us-personal",
                bank_code="CIBC",
                country_code="CA",
                source_type="html",
                source_language="en",
                source_metadata={
                    "product_type": "savings",
                    "expected_fields": ["product_name", "eligibility_text", "tier_definition_text"],
                },
            )
            candidates = [
                EvidenceChunkCandidate(
                    evidence_chunk_id="chunk-cibc-us-rate-placeholder",
                    parsed_document_id="parsed-cibc-us-personal",
                    chunk_index=0,
                    anchor_type="section",
                    anchor_value="rates-and-fees",
                    page_no=None,
                    source_language="en",
                    evidence_excerpt=(
                        "CIBC US$ Personal Account at a glance\n"
                        "Regular Interest rate\n"
                        "RDS%rate[3].CUPA.rate(null,0.0_up to_2999.99_CAD_Balance,1,1)(#O2#)% to "
                        "RDS%rate[3].CUPA.rate(null,60000.0_and over_0.0_CAD_Portion,1,1)(#O2#)%\n"
                        "Regular interest rates are tiered."
                    ),
                    retrieval_metadata={},
                    source_document_id="src-cibc-us-personal",
                    source_snapshot_id="snap-cibc-us-personal",
                    bank_code="CIBC",
                    country_code="CA",
                    source_type="html",
                ),
                EvidenceChunkCandidate(
                    evidence_chunk_id="chunk-cibc-us-eligibility",
                    parsed_document_id="parsed-cibc-us-personal",
                    chunk_index=1,
                    anchor_type="section",
                    anchor_value="how-do-i-qualify",
                    page_no=None,
                    source_language="en",
                    evidence_excerpt=(
                        "How do I qualify?\n"
                        "CIBC US$ Personal Account:\n"
                        "You're a Canadian resident and you've reached the age of majority in your province or territory."
                    ),
                    retrieval_metadata={},
                    source_document_id="src-cibc-us-personal",
                    source_snapshot_id="snap-cibc-us-personal",
                    bank_code="CIBC",
                    country_code="CA",
                    source_type="html",
                ),
                EvidenceChunkCandidate(
                    evidence_chunk_id="chunk-cibc-us-cross-border-noise",
                    parsed_document_id="parsed-cibc-us-personal",
                    chunk_index=2,
                    anchor_type="section",
                    anchor_value="other-u-s-banking-services-for-canadians",
                    page_no=None,
                    source_language="en",
                    evidence_excerpt=(
                        "Other U.S. banking services for Canadians\n"
                        "We know there's lots to think about when you're heading south of the border. "
                        "Our tools and resources provide the information you need so you can travel with ease."
                    ),
                    retrieval_metadata={},
                    source_document_id="src-cibc-us-personal",
                    source_snapshot_id="snap-cibc-us-personal",
                    bank_code="CIBC",
                    country_code="CA",
                    source_type="html",
                ),
            ]
            storage_config = ExtractionStorageConfig(
                driver="filesystem",
                env_prefix="dev",
                extraction_object_prefix="extracted",
                retention_class="hot",
                filesystem_root=str(temp_path),
            )
            service = ExtractionService(
                storage_config=storage_config,
                object_store=build_object_store(storage_config),
            )

            result = service.extract_documents(
                run_id="run-cibc-us-personal",
                correlation_id="corr-cibc-us-personal",
                request_id="req-cibc-us-personal",
                inputs=[ExtractionInput(context=context, candidates=candidates)],
            )

            extracted_by_field = {item.field_name: item for item in result.source_results[0].extracted_fields}
            self.assertEqual(extracted_by_field["product_name"].candidate_value, "CIBC US$ Personal Account")
            self.assertEqual(
                extracted_by_field["eligibility_text"].candidate_value,
                "You're a Canadian resident and you've reached the age of majority in your province or territory",
            )
            self.assertNotIn("tier_definition_text", extracted_by_field)
        finally:
            rmtree(temp_path, ignore_errors=True)

    def test_cibc_eadvantage_prefers_primary_residency_eligibility(self) -> None:
        temp_path = _prepare_workspace_temp_dir("extraction-cibc-eadvantage-eligibility")
        try:
            context = ExtractionDocumentContext(
                source_id="CIBC-SAV-002",
                parsed_document_id="parsed-cibc-eadvantage",
                source_document_id="src-cibc-eadvantage",
                snapshot_id="snap-cibc-eadvantage",
                bank_code="CIBC",
                country_code="CA",
                source_type="html",
                source_language="en",
                source_metadata={
                    "product_type": "savings",
                    "expected_fields": ["product_name", "eligibility_text", "tier_definition_text"],
                },
            )
            candidates = [
                EvidenceChunkCandidate(
                    evidence_chunk_id="chunk-cibc-eadvantage-rates",
                    parsed_document_id="parsed-cibc-eadvantage",
                    chunk_index=0,
                    anchor_type="section",
                    anchor_value="rates-and-fees",
                    page_no=None,
                    source_language="en",
                    evidence_excerpt=(
                        "CIBC eAdvantage Savings Account at a glance\n"
                        "Regular Interest\n"
                        "RDS%rate[3].CESA.Published(null,0.0_-_9999.99_CAD_Balance,1,1)(#O2#)% to "
                        "RDS%rate[3].CESA.Published(null,500000.0_and over_0.0_CAD_Balance,1,1)(#O2#)%\n"
                        "Tiered regular interest with rates that increase as your savings grow."
                    ),
                    retrieval_metadata={},
                    source_document_id="src-cibc-eadvantage",
                    source_snapshot_id="snap-cibc-eadvantage",
                    bank_code="CIBC",
                    country_code="CA",
                    source_type="html",
                ),
                EvidenceChunkCandidate(
                    evidence_chunk_id="chunk-cibc-eadvantage-eligibility",
                    parsed_document_id="parsed-cibc-eadvantage",
                    chunk_index=1,
                    anchor_type="section",
                    anchor_value="how-do-i-qualify",
                    page_no=None,
                    source_language="en",
                    evidence_excerpt=(
                        "How do I qualify?\n"
                        "CIBC eAdvantage Savings Account:\n"
                        "You're a Canadian resident and you've reached the age of majority in your province or territory. "
                        "Learn about the age of majority. Opens a popup.\n"
                        "If you're under the age of majority, you can apply for an account by visiting a CIBC Banking Centre "
                        "Opens in a new window. or calling 1-800-465-2422 Opens your phone app."
                    ),
                    retrieval_metadata={},
                    source_document_id="src-cibc-eadvantage",
                    source_snapshot_id="snap-cibc-eadvantage",
                    bank_code="CIBC",
                    country_code="CA",
                    source_type="html",
                ),
            ]
            storage_config = ExtractionStorageConfig(
                driver="filesystem",
                env_prefix="dev",
                extraction_object_prefix="extracted",
                retention_class="hot",
                filesystem_root=str(temp_path),
            )
            service = ExtractionService(
                storage_config=storage_config,
                object_store=build_object_store(storage_config),
            )

            result = service.extract_documents(
                run_id="run-cibc-eadvantage",
                correlation_id="corr-cibc-eadvantage",
                request_id="req-cibc-eadvantage",
                inputs=[ExtractionInput(context=context, candidates=candidates)],
            )

            extracted_by_field = {item.field_name: item for item in result.source_results[0].extracted_fields}
            self.assertEqual(extracted_by_field["product_name"].candidate_value, "CIBC eAdvantage Savings Account")
            self.assertEqual(
                extracted_by_field["eligibility_text"].candidate_value,
                "You're a Canadian resident and you've reached the age of majority in your province or territory",
            )
            self.assertNotIn("tier_definition_text", extracted_by_field)
        finally:
            rmtree(temp_path, ignore_errors=True)

    def test_money_extraction_treats_free_fee_labels_as_zero(self) -> None:
        temp_path = _prepare_workspace_temp_dir("extraction-money-free-labels")
        try:
            context = ExtractionDocumentContext(
                source_id="RBC-SAV-004",
                parsed_document_id="parsed-rbc-sav-004",
                source_document_id="src-rbc-sav-004",
                snapshot_id="snap-rbc-sav-004",
                bank_code="RBC",
                country_code="CA",
                source_type="html",
                source_language="en",
                source_metadata={"product_type": "savings", "expected_fields": ["monthly_fee", "public_display_fee"]},
            )
            candidates = [
                EvidenceChunkCandidate(
                    evidence_chunk_id="chunk-rbc-fee-001",
                    parsed_document_id="parsed-rbc-sav-004",
                    chunk_index=0,
                    anchor_type="section",
                    anchor_value="fees",
                    page_no=None,
                    source_language="en",
                    evidence_excerpt=(
                        "More Great Features Details Fees Monthly Fee Free Currency Canadian "
                        "Monthly Debits included 1 per monthly cycle Additional debits $2.00 each "
                        "Balances of $5,000 or more earn premium interest rates."
                    ),
                    retrieval_metadata={},
                    source_document_id="src-rbc-sav-004",
                    source_snapshot_id="snap-rbc-sav-004",
                    bank_code="RBC",
                    country_code="CA",
                    source_type="html",
                )
            ]
            storage_config = ExtractionStorageConfig(
                driver="filesystem",
                env_prefix="dev",
                extraction_object_prefix="extracted",
                retention_class="hot",
                filesystem_root=str(temp_path),
            )
            service = ExtractionService(storage_config=storage_config, object_store=build_object_store(storage_config))

            result = service.extract_documents(
                run_id="run-free-fee-001",
                correlation_id="corr-free-fee-001",
                request_id="req-free-fee-001",
                inputs=[ExtractionInput(context=context, candidates=candidates)],
            )

            extracted_by_field = {item.field_name: item for item in result.source_results[0].extracted_fields}
            self.assertEqual(extracted_by_field["monthly_fee"].candidate_value, "0.00")
            self.assertEqual(extracted_by_field["public_display_fee"].candidate_value, "0.00")
        finally:
            rmtree(temp_path, ignore_errors=True)

    def test_money_extraction_requires_minimum_labels(self) -> None:
        temp_path = _prepare_workspace_temp_dir("extraction-money-minimums")
        try:
            context = ExtractionDocumentContext(
                source_id="CIBC-SAV-002",
                parsed_document_id="parsed-cibc-sav-003",
                source_document_id="src-cibc-sav-003",
                snapshot_id="snap-cibc-sav-003",
                bank_code="CIBC",
                country_code="CA",
                source_type="html",
                source_language="en",
                source_metadata={
                    "product_type": "savings",
                    "expected_fields": ["minimum_balance", "minimum_deposit"],
                },
            )
            candidates = [
                EvidenceChunkCandidate(
                    evidence_chunk_id="chunk-cibc-minimum-001",
                    parsed_document_id="parsed-cibc-sav-003",
                    chunk_index=0,
                    anchor_type="section",
                    anchor_value="rates-and-fees",
                    page_no=None,
                    source_language="en",
                    evidence_excerpt="Earned on balances up to $200,000 when you save $200 or more in any month. Limits apply.",
                    retrieval_metadata={},
                    source_document_id="src-cibc-sav-003",
                    source_snapshot_id="snap-cibc-sav-003",
                    bank_code="CIBC",
                    country_code="CA",
                    source_type="html",
                ),
                EvidenceChunkCandidate(
                    evidence_chunk_id="chunk-cibc-minimum-002",
                    parsed_document_id="parsed-cibc-sav-003",
                    chunk_index=1,
                    anchor_type="section",
                    anchor_value="eligibility",
                    page_no=None,
                    source_language="en",
                    evidence_excerpt="No minimum balance required. No minimum opening deposit required.",
                    retrieval_metadata={},
                    source_document_id="src-cibc-sav-003",
                    source_snapshot_id="snap-cibc-sav-003",
                    bank_code="CIBC",
                    country_code="CA",
                    source_type="html",
                ),
            ]
            storage_config = ExtractionStorageConfig(
                driver="filesystem",
                env_prefix="dev",
                extraction_object_prefix="extracted",
                retention_class="hot",
                filesystem_root=str(temp_path),
            )
            service = ExtractionService(
                storage_config=storage_config,
                object_store=build_object_store(storage_config),
            )

            result = service.extract_documents(
                run_id="run-cibc-minimum-001",
                correlation_id="corr-cibc-minimum-001",
                request_id="req-cibc-minimum-001",
                inputs=[ExtractionInput(context=context, candidates=candidates)],
            )

            extracted_by_field = {item.field_name: item for item in result.source_results[0].extracted_fields}
            self.assertEqual(extracted_by_field["minimum_balance"].candidate_value, "0.00")
            self.assertEqual(extracted_by_field["minimum_deposit"].candidate_value, "0.00")
        finally:
            rmtree(temp_path, ignore_errors=True)

    def test_term_extraction_ignores_non_term_day_counts_without_term_context(self) -> None:
        temp_path = _prepare_workspace_temp_dir("extraction-term-context")
        try:
            context = ExtractionDocumentContext(
                source_id="RBC-SAV-999",
                parsed_document_id="parsed-rbc-sav-999",
                source_document_id="src-rbc-sav-999",
                snapshot_id="snap-rbc-sav-999",
                bank_code="RBC",
                country_code="CA",
                source_type="html",
                source_language="en",
                source_metadata={"product_type": "savings", "expected_fields": ["term_length_text", "term_length_days"]},
            )
            candidates = [
                EvidenceChunkCandidate(
                    evidence_chunk_id="chunk-term-001",
                    parsed_document_id="parsed-rbc-sav-999",
                    chunk_index=0,
                    anchor_type="section",
                    anchor_value="mobile-deposit",
                    page_no=None,
                    source_language="en",
                    evidence_excerpt="Cheque images can be viewed online for less than 90 days old in the mobile app.",
                    retrieval_metadata={},
                    source_document_id="src-rbc-sav-999",
                    source_snapshot_id="snap-rbc-sav-999",
                    bank_code="RBC",
                    country_code="CA",
                    source_type="html",
                )
            ]
            storage_config = ExtractionStorageConfig(
                driver="filesystem",
                env_prefix="dev",
                extraction_object_prefix="extracted",
                retention_class="hot",
                filesystem_root=str(temp_path),
            )
            service = ExtractionService(storage_config=storage_config, object_store=build_object_store(storage_config))

            result = service.extract_documents(
                run_id="run-term-001",
                correlation_id="corr-term-001",
                request_id="req-term-001",
                inputs=[ExtractionInput(context=context, candidates=candidates)],
            )

            extracted_by_field = {item.field_name: item for item in result.source_results[0].extracted_fields}
            self.assertNotIn("term_length_text", extracted_by_field)
            self.assertNotIn("term_length_days", extracted_by_field)
        finally:
            rmtree(temp_path, ignore_errors=True)

    def test_standard_product_type_uses_official_web_grounding_when_configured(self) -> None:
        temp_path = _prepare_workspace_temp_dir("extraction-standard-official-grounding")
        try:
            context = ExtractionDocumentContext(
                source_id="TD-SAV-001",
                parsed_document_id="parsed-standard-grounding-001",
                source_document_id="src-standard-grounding-001",
                snapshot_id="snap-standard-grounding-001",
                bank_code="TD",
                country_code="CA",
                source_type="html",
                source_language="en",
                source_metadata={
                    "product_type": "savings",
                    "discovery_role": "detail",
                    "expected_fields": ["product_name", "eligibility_text"],
                    "normalized_source_url": "https://www.td.com/ca/en/personal-banking/products/saving-investing/every-day-savings-account",
                    "official_domain_allowlist": ["td.com"],
                },
            )
            candidates = [
                EvidenceChunkCandidate(
                    evidence_chunk_id="chunk-standard-grounding-001",
                    parsed_document_id=context.parsed_document_id,
                    chunk_index=0,
                    anchor_type="section",
                    anchor_value="td-every-day-savings-account",
                    page_no=None,
                    source_language="en",
                    evidence_excerpt=(
                        "TD Every Day Savings Account\n"
                        "Available to Canadian residents who meet TD account-opening requirements."
                    ),
                    retrieval_metadata={},
                    source_document_id=context.source_document_id,
                    source_snapshot_id=context.snapshot_id,
                    bank_code="TD",
                    country_code="CA",
                    source_type="html",
                )
            ]
            storage_config = ExtractionStorageConfig(
                driver="filesystem",
                env_prefix="dev",
                extraction_object_prefix="extracted",
                retention_class="hot",
                filesystem_root=str(temp_path),
            )
            service = ExtractionService(
                storage_config=storage_config,
                object_store=build_object_store(storage_config),
            )
            official_url = context.source_metadata["normalized_source_url"]
            with (
                patch("worker.pipeline.fpds_extraction.service.llm_provider_configured", return_value=True),
                patch("worker.pipeline.fpds_extraction.service.configured_model_id", return_value="gpt-5.6-luna"),
                patch(
                    "worker.pipeline.fpds_extraction.service.invoke_openai_json_schema",
                    return_value=(
                        {
                            "summary": "Current official product evidence confirms the eligibility field.",
                            "fields": [
                                {
                                    "field_name": "eligibility_text",
                                    "status": "mismatch",
                                    "has_verified_value": True,
                                    "verified_value_json": '"Canadian residents who meet TD account-opening requirements."',
                                    "evidence_chunk_id": "chunk-standard-grounding-001",
                                    "evidence_quote": "Available to Canadian residents who meet TD account-opening requirements.",
                                    "confidence": 0.91,
                                    "rationale": "The exact product page states the requirement.",
                                    "sources": [{"url": official_url, "title": "TD Every Day Savings Account"}],
                                }
                            ],
                        },
                        {
                            "model_id": "gpt-5.6-luna",
                            "prompt_tokens": 140,
                            "completion_tokens": 38,
                            "provider_request_id": "resp-standard-grounding-001",
                            "web_search_sources": [
                                {"url": official_url, "title": "TD Every Day Savings Account"}
                            ],
                        },
                    ),
                ) as invoke_model,
            ):
                result = service.extract_documents(
                    run_id="run-standard-grounding-001",
                    inputs=[ExtractionInput(context=context, candidates=candidates)],
                )

            source_result = result.source_results[0]
            fields_by_name = {item.field_name: item for item in source_result.extracted_fields}
            self.assertEqual(source_result.model_execution_record["agent_name"], "fpds-official-product-grounding-agent")
            self.assertEqual(fields_by_name["eligibility_text"].extraction_method, "openai_official_grounding")
            self.assertEqual(
                fields_by_name["eligibility_text"].field_metadata["official_web_sources"][0]["url"],
                official_url,
            )
            call = invoke_model.call_args.kwargs
            self.assertTrue(call["require_web_search"])
            self.assertEqual(call["web_search_allowed_domains"], ["td.com"])
            self.assertIn("monthly_fee", call["payload"]["requested_fields"])
            self.assertEqual(
                source_result.model_execution_record["execution_metadata"]["official_grounding_contract_version"],
                "collection-official-grounding-v1",
            )
        finally:
            rmtree(temp_path, ignore_errors=True)

    def test_dynamic_product_type_uses_ai_fallback_when_configured(self) -> None:
        temp_path = _prepare_workspace_temp_dir("extraction-dynamic-service")
        try:
            context = ExtractionDocumentContext(
                source_id="TD-TFSA-001",
                parsed_document_id="parsed-dyn-001",
                source_document_id="src-dyn-001",
                snapshot_id="snap-dyn-001",
                bank_code="TD",
                country_code="CA",
                source_type="html",
                source_language="en",
                source_metadata={
                    "product_type": "tfsa-savings",
                    "product_type_dynamic": True,
                    "product_type_name": "TFSA Savings",
                    "product_type_description": "Tax-free savings deposit account for retail customers.",
                    "expected_fields": ["product_name", "minimum_deposit", "eligibility_text"],
                    "fallback_policy": "generic_ai_review",
                    "normalized_source_url": "https://www.td.com/ca/en/personal-banking/products/tfsa-savings",
                    "official_domain_allowlist": ["td.com"],
                },
            )
            candidates = [
                EvidenceChunkCandidate(
                    evidence_chunk_id="chunk-dyn-001",
                    parsed_document_id="parsed-dyn-001",
                    chunk_index=0,
                    anchor_type="section",
                    anchor_value="tfsa-overview",
                    page_no=None,
                    source_language="en",
                    evidence_excerpt=(
                        "TD TFSA Savings Account\n"
                        "Minimum deposit: $100. Available to Canadian residents aged 18 or older."
                    ),
                    retrieval_metadata={},
                    source_document_id="src-dyn-001",
                    source_snapshot_id="snap-dyn-001",
                    bank_code="TD",
                    country_code="CA",
                    source_type="html",
                )
            ]
            storage_config = ExtractionStorageConfig(
                driver="filesystem",
                env_prefix="dev",
                extraction_object_prefix="extracted",
                retention_class="hot",
                filesystem_root=str(temp_path),
            )
            service = ExtractionService(
                storage_config=storage_config,
                object_store=build_object_store(storage_config),
            )

            with (
                patch("worker.pipeline.fpds_extraction.service.llm_provider_configured", return_value=True),
                patch("worker.pipeline.fpds_extraction.service.configured_model_id", return_value="gpt-5.6-luna"),
                patch(
                    "worker.pipeline.fpds_extraction.service.invoke_openai_json_schema",
                    return_value=(
                        {
                            "summary": "Official TD evidence confirms the eligibility field.",
                            "fields": [
                                {
                                    "field_name": "eligibility_text",
                                    "status": "mismatch",
                                    "has_verified_value": True,
                                    "verified_value_json": '"Canadian residents aged 18 or older."',
                                    "evidence_chunk_id": "chunk-dyn-001",
                                    "evidence_quote": "Available to Canadian residents aged 18 or older.",
                                    "confidence": 0.83,
                                    "rationale": "The current official product page states the eligibility directly.",
                                    "sources": [
                                        {
                                            "url": "https://www.td.com/ca/en/personal-banking/products/tfsa-savings",
                                            "title": "TD TFSA Savings Account",
                                        }
                                    ],
                                }
                            ],
                        },
                        {
                            "model_id": "gpt-5.6-luna",
                            "prompt_tokens": 120,
                            "completion_tokens": 34,
                            "provider_request_id": "resp-dyn-001",
                            "web_search_sources": [
                                {
                                    "url": "https://www.td.com/ca/en/personal-banking/products/tfsa-savings",
                                    "title": "TD TFSA Savings Account",
                                }
                            ],
                        },
                    ),
                ),
            ):
                result = service.extract_documents(
                    run_id="run-dyn-001",
                    correlation_id="corr-dyn-001",
                    request_id="req-dyn-001",
                    inputs=[ExtractionInput(context=context, candidates=candidates)],
                )

            source_result = result.source_results[0]
            extracted_by_field = {item.field_name: item for item in source_result.extracted_fields}
            self.assertEqual(source_result.model_execution_record["agent_name"], "fpds-official-product-grounding-agent")
            self.assertEqual(source_result.usage_record["usage_metadata"]["usage_mode"], "openai-official-product-grounding")
            self.assertEqual(extracted_by_field["eligibility_text"].candidate_value, "Canadian residents aged 18 or older.")
            self.assertEqual(extracted_by_field["eligibility_text"].extraction_method, "openai_official_grounding")
            self.assertIn("Official TD evidence confirms the eligibility field.", source_result.runtime_notes)
        finally:
            rmtree(temp_path, ignore_errors=True)

    def test_dynamic_gic_term_deposit_suppresses_cross_product_navigation_noise(self) -> None:
        temp_path = _prepare_workspace_temp_dir("extraction-dynamic-bmo-gic-navigation")
        try:
            context = ExtractionDocumentContext(
                source_id="BMO-GIC-003",
                parsed_document_id="parsed-bmo-gic-dynamic",
                source_document_id="src-bmo-gic-dynamic",
                snapshot_id="snap-bmo-gic-dynamic",
                bank_code="BMO",
                country_code="CA",
                source_type="html",
                source_language="en",
                source_metadata={
                    "product_type": "gic-term-deposit",
                    "product_type_dynamic": True,
                    "product_type_name": "GIC / Term Deposit",
                    "product_type_description": (
                        "A deposit product where money is placed for a fixed term at a guaranteed interest rate."
                    ),
                    "discovery_keywords": ["gic", "term deposit", "guaranteed investment certificate"],
                    "expected_fields": ["product_name", "return_structure", "term_options", "principal_protection"],
                    "fallback_policy": "generic_ai_review",
                    "discovery_metadata": {"page_title": "Progressive GIC Search Tool - BMO"},
                    "normalized_source_url": "https://www.bmo.com/main/personal/investments/gic/progressive-gic-search",
                    "official_domain_allowlist": ["bmo.com"],
                },
            )
            candidates = [
                EvidenceChunkCandidate(
                    evidence_chunk_id="chunk-bmo-gic-nav",
                    parsed_document_id="parsed-bmo-gic-dynamic",
                    chunk_index=1,
                    anchor_type="section",
                    anchor_value="document",
                    page_no=None,
                    source_language="en",
                    evidence_excerpt=(
                        "Personal\n"
                        "Chequing Practical Chequing Premium Chequing AIR MILES Chequing\n"
                        "All chequing accounts\n"
                        "Plus Chequing\n"
                        "Performance Chequing\n"
                        "Savings Accounts All savings accounts Premium Rate Savings Savings Amplifier U.S. Dollar Premium Rate Savings\n"
                        "Credit Cards Credit Cards Overview Card Types Cash Back Low Interest Rate Rewards Travel Visa No Fee All cards\n"
                        "Mortgages Overview Mortgage Rates Loans Overview Banking fees and agreements Book an appointment"
                    ),
                    retrieval_metadata={},
                    source_document_id="src-bmo-gic-dynamic",
                    source_snapshot_id="snap-bmo-gic-dynamic",
                    bank_code="BMO",
                    country_code="CA",
                    source_type="html",
                )
            ]
            storage_config = ExtractionStorageConfig(
                driver="filesystem",
                env_prefix="dev",
                extraction_object_prefix="extracted",
                retention_class="hot",
                filesystem_root=str(temp_path),
            )
            service = ExtractionService(
                storage_config=storage_config,
                object_store=build_object_store(storage_config),
            )

            with (
                patch("worker.pipeline.fpds_extraction.service.llm_provider_configured", return_value=True),
                patch("worker.pipeline.fpds_extraction.service.configured_model_id", return_value="gpt-5.6-luna"),
                patch(
                    "worker.pipeline.fpds_extraction.service.invoke_openai_json_schema",
                    return_value=(
                        {
                            "summary": "No grounded GIC product details were present in the evidence chunks.",
                            "fields": [],
                        },
                        {
                            "model_id": "gpt-5.6-luna",
                            "prompt_tokens": 160,
                            "completion_tokens": 18,
                            "provider_request_id": "resp-bmo-gic-nav",
                            "web_search_sources": [
                                {
                                    "url": "https://www.bmo.com/main/personal/investments/gic/progressive-gic-search",
                                    "title": "Progressive GIC Search Tool",
                                }
                            ],
                        },
                    ),
                ),
            ):
                result = service.extract_documents(
                    run_id="run-bmo-gic-dynamic",
                    correlation_id="corr-bmo-gic-dynamic",
                    request_id="req-bmo-gic-dynamic",
                    inputs=[ExtractionInput(context=context, candidates=candidates)],
                )

            source_result = result.source_results[0]
            extracted_by_field = {item.field_name: item for item in source_result.extracted_fields}
            self.assertEqual(extracted_by_field["product_name"].candidate_value, "Progressive GIC Search Tool - BMO")
            self.assertNotEqual(extracted_by_field["product_name"].candidate_value, "All chequing accounts")
            self.assertNotIn("description_short", extracted_by_field)
            self.assertNotIn("fee_waiver_condition", extracted_by_field)
            self.assertNotIn("eligibility_text", extracted_by_field)
            self.assertNotIn("term_options", extracted_by_field)
            self.assertNotIn("return_structure", extracted_by_field)
            self.assertNotIn("principal_protection", extracted_by_field)
            self.assertIn("No grounded GIC product details were present in the evidence chunks.", source_result.runtime_notes)
            self.assertEqual(len(source_result.evidence_links), 0)
            requested_fields = source_result.model_execution_record["execution_metadata"]["requested_fields"]
            self.assertIn("standard_rate", requested_fields)
            self.assertIn("public_display_rate", requested_fields)
            self.assertIn("minimum_deposit", requested_fields)
            self.assertIn("term_length_text", requested_fields)
            self.assertIn("term_length_days", requested_fields)
        finally:
            rmtree(temp_path, ignore_errors=True)

    def test_extracts_gic_specific_fields(self) -> None:
        temp_path = _prepare_workspace_temp_dir("extraction-gic-service")
        try:
            context = ExtractionDocumentContext(
                source_id="RBC-GIC-002",
                parsed_document_id="parsed-gic-001",
                source_document_id="src-gic-001",
                snapshot_id="snap-gic-001",
                bank_code="RBC",
                country_code="CA",
                source_type="html",
                source_language="en",
                source_metadata={
                    "product_type": "gic",
                    "expected_fields": [
                        "standard_rate",
                        "minimum_deposit",
                        "term_length_text",
                        "term_length_days",
                        "redeemable_flag",
                        "non_redeemable_flag",
                        "compounding_frequency",
                        "payout_option",
                        "registered_plan_supported",
                    ],
                },
            )
            candidates = [
                EvidenceChunkCandidate(
                    evidence_chunk_id="chunk-gic-001",
                    parsed_document_id="parsed-gic-001",
                    chunk_index=0,
                    anchor_type="section",
                    anchor_value="1-year-cashable-gic",
                    page_no=None,
                    source_language="en",
                    evidence_excerpt="RBC 1 Year Cashable GIC\nA guaranteed investment with flexible access.",
                    retrieval_metadata={},
                    source_document_id="src-gic-001",
                    source_snapshot_id="snap-gic-001",
                    bank_code="RBC",
                    country_code="CA",
                    source_type="html",
                ),
                EvidenceChunkCandidate(
                    evidence_chunk_id="chunk-gic-002",
                    parsed_document_id="parsed-gic-001",
                    chunk_index=1,
                    anchor_type="section",
                    anchor_value="rate-and-term",
                    page_no=None,
                    source_language="en",
                    evidence_excerpt="Earn 3.80% interest on a 1-year term. Minimum deposit: $500.",
                    retrieval_metadata={},
                    source_document_id="src-gic-001",
                    source_snapshot_id="snap-gic-001",
                    bank_code="RBC",
                    country_code="CA",
                    source_type="html",
                ),
                EvidenceChunkCandidate(
                    evidence_chunk_id="chunk-gic-003",
                    parsed_document_id="parsed-gic-001",
                    chunk_index=2,
                    anchor_type="section",
                    anchor_value="interest-options",
                    page_no=None,
                    source_language="en",
                    evidence_excerpt="Interest can be compounded annually and paid at maturity.",
                    retrieval_metadata={},
                    source_document_id="src-gic-001",
                    source_snapshot_id="snap-gic-001",
                    bank_code="RBC",
                    country_code="CA",
                    source_type="html",
                ),
                EvidenceChunkCandidate(
                    evidence_chunk_id="chunk-gic-004",
                    parsed_document_id="parsed-gic-001",
                    chunk_index=3,
                    anchor_type="section",
                    anchor_value="registered-options",
                    page_no=None,
                    source_language="en",
                    evidence_excerpt="Available for TFSA, RRSP and RRIF plans.",
                    retrieval_metadata={},
                    source_document_id="src-gic-001",
                    source_snapshot_id="snap-gic-001",
                    bank_code="RBC",
                    country_code="CA",
                    source_type="html",
                ),
            ]
            storage_config = ExtractionStorageConfig(
                driver="filesystem",
                env_prefix="dev",
                extraction_object_prefix="extracted",
                retention_class="hot",
                filesystem_root=str(temp_path),
            )
            service = ExtractionService(
                storage_config=storage_config,
                object_store=build_object_store(storage_config),
            )

            result = service.extract_documents(
                run_id="run-gic-001",
                correlation_id="corr-gic-001",
                request_id="req-gic-001",
                inputs=[ExtractionInput(context=context, candidates=candidates)],
            )

            source_result = result.source_results[0]
            extracted_by_field = {item.field_name: item for item in source_result.extracted_fields}
            self.assertEqual(extracted_by_field["product_type"].candidate_value, "gic")
            self.assertEqual(extracted_by_field["standard_rate"].candidate_value, "3.80")
            self.assertEqual(extracted_by_field["minimum_deposit"].candidate_value, "500.00")
            self.assertEqual(extracted_by_field["term_length_text"].candidate_value, "1 year")
            self.assertEqual(extracted_by_field["term_length_days"].candidate_value, 365)
            self.assertTrue(extracted_by_field["redeemable_flag"].candidate_value)
            self.assertFalse(extracted_by_field["non_redeemable_flag"].candidate_value)
            self.assertEqual(extracted_by_field["compounding_frequency"].candidate_value, "annually")
            self.assertEqual(extracted_by_field["payout_option"].candidate_value, "at_maturity")
            self.assertTrue(extracted_by_field["registered_plan_supported"].candidate_value)
        finally:
            rmtree(temp_path, ignore_errors=True)

    def test_cibc_flexible_gic_filters_cross_product_description_and_extracts_minimum_investment(self) -> None:
        temp_path = _prepare_workspace_temp_dir("extraction-cibc-flexible-gic")
        try:
            context = ExtractionDocumentContext(
                source_id="CIBC-GIC-002",
                parsed_document_id="parsed-cibc-flex-gic",
                source_document_id="src-cibc-flex-gic",
                snapshot_id="snap-cibc-flex-gic",
                bank_code="CIBC",
                country_code="CA",
                source_type="html",
                source_language="en",
                source_metadata={
                    "product_type": "gic-term-deposit",
                    "product_type_dynamic": True,
                    "product_type_name": "GIC / Term Deposit",
                    "product_type_description": "A guaranteed investment certificate or term deposit.",
                    "page_title": "CIBC Flexible GIC | CIBC",
                    "expected_fields": ["product_name", "description_short", "minimum_deposit", "eligibility_text"],
                },
            )
            candidates = [
                EvidenceChunkCandidate(
                    evidence_chunk_id="chunk-cibc-mutual-noise",
                    parsed_document_id="parsed-cibc-flex-gic",
                    chunk_index=0,
                    anchor_type="section",
                    anchor_value="learn-about-cibc-mutual-fund-account-conversion",
                    page_no=None,
                    source_language="en",
                    evidence_excerpt="Learn\nLearn About CIBC Mutual Fund Account Conversion",
                    retrieval_metadata={},
                    source_document_id="src-cibc-flex-gic",
                    source_snapshot_id="snap-cibc-flex-gic",
                    bank_code="CIBC",
                    country_code="CA",
                    source_type="html",
                ),
                EvidenceChunkCandidate(
                    evidence_chunk_id="chunk-cibc-flex-hero",
                    parsed_document_id="parsed-cibc-flex-gic",
                    chunk_index=1,
                    anchor_type="section",
                    anchor_value="why-choose-a-cibc-flexible-gic",
                    page_no=None,
                    source_language="en",
                    evidence_excerpt=(
                        "Why choose a CIBC Flexible GIC?\n"
                        "This 1-year GIC is right for you if you're saving for a short-term goal or want a place to park your money."
                    ),
                    retrieval_metadata={},
                    source_document_id="src-cibc-flex-gic",
                    source_snapshot_id="snap-cibc-flex-gic",
                    bank_code="CIBC",
                    country_code="CA",
                    source_type="html",
                ),
                EvidenceChunkCandidate(
                    evidence_chunk_id="chunk-cibc-flex-rate",
                    parsed_document_id="parsed-cibc-flex-gic",
                    chunk_index=2,
                    anchor_type="section",
                    anchor_value="non-registered",
                    page_no=None,
                    source_language="en",
                    evidence_excerpt="Non-registered\nMinimum investment of $1,000\nTerm and rate\n1 year RDS%rate[4].FLGIC.Published(...)%",
                    retrieval_metadata={},
                    source_document_id="src-cibc-flex-gic",
                    source_snapshot_id="snap-cibc-flex-gic",
                    bank_code="CIBC",
                    country_code="CA",
                    source_type="html",
                ),
                EvidenceChunkCandidate(
                    evidence_chunk_id="chunk-cibc-flex-access",
                    parsed_document_id="parsed-cibc-flex-gic",
                    chunk_index=3,
                    anchor_type="section",
                    anchor_value="what-you-need-to-know",
                    page_no=None,
                    source_language="en",
                    evidence_excerpt=(
                        "What you need to know\n"
                        "Type\n"
                        "Cashable\n"
                        "Access\n"
                        "Access your money at any time. Depending on how much you invest, there's a minimum withdrawal amount."
                    ),
                    retrieval_metadata={},
                    source_document_id="src-cibc-flex-gic",
                    source_snapshot_id="snap-cibc-flex-gic",
                    bank_code="CIBC",
                    country_code="CA",
                    source_type="html",
                ),
            ]
            storage_config = ExtractionStorageConfig(
                driver="filesystem",
                env_prefix="dev",
                extraction_object_prefix="extracted",
                retention_class="hot",
                filesystem_root=str(temp_path),
            )
            service = ExtractionService(
                storage_config=storage_config,
                object_store=build_object_store(storage_config),
            )

            result = service.extract_documents(
                run_id="run-cibc-flex-gic",
                correlation_id="corr-cibc-flex-gic",
                request_id="req-cibc-flex-gic",
                inputs=[ExtractionInput(context=context, candidates=candidates)],
            )

            source_result = result.source_results[0]
            extracted_by_field = {item.field_name: item for item in source_result.extracted_fields}
            self.assertEqual(extracted_by_field["product_name"].candidate_value, "CIBC Flexible GIC")
            self.assertEqual(
                extracted_by_field["description_short"].candidate_value,
                "This 1-year GIC is right for you if you're saving for a short-term goal or want a place to park your money.",
            )
            self.assertNotIn("Mutual Fund Account Conversion", extracted_by_field["description_short"].candidate_value)
            self.assertEqual(extracted_by_field["minimum_deposit"].candidate_value, "1000.00")
            self.assertNotIn("eligibility_text", extracted_by_field)
        finally:
            rmtree(temp_path, ignore_errors=True)


class ExtractionPersistenceTests(unittest.TestCase):
    def test_registry_metadata_overrides_shared_source_document_product_type(self) -> None:
        context = ExtractionDocumentContext(
            source_id="BMO-CHQ-006",
            parsed_document_id="parsed-shared-rate-page",
            source_document_id="src-bmo-shared-rates",
            snapshot_id="snap-shared-rate-page",
            bank_code="BMO",
            country_code="CA",
            source_type="html",
            source_language="en",
            source_metadata={
                "source_id": "BMO-CHQ-006",
                "product_type": "chequing",
                "expected_fields": ["monthly_fee"],
            },
        )
        registry_source = _FakeRegistrySource(
            {
                "source_id": "BMO-SAV-006",
                "product_type": "savings",
                "expected_fields": ["savings_account_rates"],
                "product_type_name": "Savings",
            }
        )

        updated = _context_with_registry_metadata(
            context=context,
            registry_source=registry_source,
            source_id="BMO-SAV-006",
        )

        self.assertEqual(updated.source_id, "BMO-SAV-006")
        self.assertEqual(updated.source_metadata["source_id"], "BMO-SAV-006")
        self.assertEqual(updated.source_metadata["product_type"], "savings")
        self.assertEqual(updated.source_metadata["expected_fields"], ["savings_account_rates"])

    def test_load_latest_document_contexts_reads_joined_rows(self) -> None:
        runner = _FakeRunner(
            outputs=[
                "public",
                json.dumps(
                    [
                        {
                            "parsed_document_id": "parsed-001",
                            "snapshot_id": "snap-001",
                            "source_document_id": "src-001",
                            "bank_code": "TD",
                            "country_code": "CA",
                            "source_type": "html",
                            "source_language": "en",
                            "source_metadata": {"product_type": "savings"},
                        }
                    ]
                ),
            ]
        )
        repository = PsqlExtractionRepository(
            ExtractionDatabaseConfig(database_url="postgres://example", schema="public"),
            command_runner=runner,
        )

        result = repository.load_latest_document_contexts(source_document_ids=["src-001"])

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].parsed_document_id, "parsed-001")
        self.assertEqual(json.loads(runner.last_variables()["source_document_ids_json"]), ["src-001"])

    def test_persist_extraction_result_updates_model_usage_and_run(self) -> None:
        runner = _FakeRunner(outputs=["public", ""])
        repository = PsqlExtractionRepository(
            ExtractionDatabaseConfig(database_url="postgres://example", schema="public"),
            command_runner=runner,
        )
        extraction_result = _build_extraction_result_stub()

        result = repository.persist_extraction_result(
            run_id="run-001",
            extraction_result=extraction_result,
            trigger_type="manual",
            triggered_by="codex",
            completed_at="2026-04-10T12:00:00+00:00",
        )

        self.assertEqual(result.run_state, "completed")
        self.assertEqual(result.model_execution_count, 1)
        self.assertEqual(result.usage_record_count, 1)
        self.assertEqual(result.extracted_draft_count, 1)
        self.assertEqual(runner.last_variables()["candidate_count"], "1")


class _FakeRunner:
    def __init__(self, *, outputs: list[str]) -> None:
        self.outputs = outputs
        self.calls: list[tuple[list[str], str]] = []

    def __call__(self, command: list[str], sql: str) -> str:
        self.calls.append((list(command), sql))
        return self.outputs.pop(0)

    def last_variables(self) -> dict[str, str]:
        command = self.calls[-1][0]
        variables: dict[str, str] = {}
        for index, token in enumerate(command):
            if token != "-v":
                continue
            key, value = command[index + 1].split("=", 1)
            variables[key] = value
        return variables


class _FakeRegistrySource:
    def __init__(self, source_metadata: dict[str, object]) -> None:
        self.source_metadata = source_metadata

    def to_source_document_record(self) -> dict[str, object]:
        return {"source_metadata": self.source_metadata}


def _prepare_workspace_temp_dir(name: str) -> Path:
    temp_path = Path("tmp") / name
    rmtree(temp_path, ignore_errors=True)
    temp_path.mkdir(parents=True, exist_ok=True)
    return temp_path.resolve()


def _extracted_field(
    field_name: str,
    candidate_value: object,
    *,
    evidence_text_excerpt: str | None = None,
) -> ExtractedFieldCandidate:
    return ExtractedFieldCandidate(
        field_name=field_name,
        candidate_value=candidate_value,
        value_type="string",
        confidence=0.9,
        extraction_method="test",
        source_document_id="src-test",
        source_snapshot_id="snap-test",
        evidence_chunk_id=None,
        evidence_text_excerpt=evidence_text_excerpt,
        anchor_type=None,
        anchor_value=None,
        page_no=None,
        chunk_index=None,
        field_metadata={},
    )


def _build_extraction_result_stub():
    temp_path = _prepare_workspace_temp_dir("extraction-persist")
    context = ExtractionDocumentContext(
        source_id="TD-SAV-002",
        parsed_document_id="parsed-001",
        source_document_id="src-001",
        snapshot_id="snap-001",
        bank_code="TD",
        country_code="CA",
        source_type="html",
        source_language="en",
        source_metadata={"product_type": "savings"},
    )
    storage_config = ExtractionStorageConfig(
        driver="filesystem",
        env_prefix="dev",
        extraction_object_prefix="extracted",
        retention_class="hot",
        filesystem_root=str(temp_path),
    )
    service = ExtractionService(
        storage_config=storage_config,
        object_store=build_object_store(storage_config),
    )
    return service.extract_documents(
        run_id="run-001",
        inputs=[
            ExtractionInput(
                context=context,
                candidates=[
                    EvidenceChunkCandidate(
                        evidence_chunk_id="chunk-001",
                        parsed_document_id="parsed-001",
                        chunk_index=0,
                        anchor_type="section",
                        anchor_value="rates",
                        page_no=None,
                        source_language="en",
                        evidence_excerpt="Interest rate: 1.10%. Interest is paid monthly.",
                        retrieval_metadata={},
                        source_document_id="src-001",
                        source_snapshot_id="snap-001",
                        bank_code="TD",
                        country_code="CA",
                        source_type="html",
                    )
                ],
            )
        ],
    )


if __name__ == "__main__":
    unittest.main()
