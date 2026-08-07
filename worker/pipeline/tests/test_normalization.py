from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path
from shutil import rmtree
import unittest
from unittest.mock import patch

from worker.pipeline.fpds_normalization.models import (
    NormalizationArtifactLookup,
    NormalizationEvidenceLink,
    NormalizationExtractedField,
    NormalizationInput,
)
from worker.pipeline.fpds_normalization.persistence import (
    NormalizationDatabaseConfig,
    PsqlNormalizationRepository,
)
from worker.pipeline.fpds_normalization.service import (
    NormalizationService,
    _apply_credit_card_labeled_fallback,
    _align_advertised_promotional_total,
    _align_gic_representative_rates_from_term_table,
    _align_savings_labeled_header_standard_rate,
    _align_gic_labeled_posted_and_promotional_rates,
    _align_minimum_balance_to_fee_waiver,
    _align_public_display_fee,
    _align_public_display_rate,
    _align_promotional_period_from_evidence,
    _align_ongoing_additive_bonus_total,
    _build_field_evidence_link_records,
    _clean_chequing_fee_waiver_consistency,
    _clean_deposit_insurance_value,
    _complete_gic_term_rate_table_from_split_evidence,
    _clean_product_context_fields,
    _compute_validation_issue_codes,
    _extract_rate_percentages,
    _find_dynamic_numeric_evidence_context,
    _infer_target_customer_tags,
    _dynamic_numeric_value_is_ungrounded,
    _field_is_comparison_calculator_copy,
    _infer_subtype_code,
    _looks_like_invalid_application_method,
    _looks_like_broad_page_copy,
    _looks_like_non_rate_numeric_context,
    _looks_like_non_value_description,
    _looks_like_non_value_eligibility,
    _looks_like_non_value_rewards,
    _looks_like_expired_promotional_customer_field,
    _normalize_term_rate_table,
    _official_grounding_mapping_metadata,
    _percentage_value_absent_from_evidence,
    _rate_field_suppression_reason,
    _rate_evidence_is_account_context,
    _refine_product_name_from_source_metadata,
    _suppress_unverified_dynamic_fields,
    _suppress_uncombined_savings_rate_boost,
)
from worker.pipeline.fpds_normalization.storage import (
    NormalizationStorageConfig,
    build_object_store,
)
from worker.pipeline.fpds_normalization.supporting_merge import (
    merge_supporting_artifacts,
    supporting_source_ids_for_target,
)


class NormalizationServiceTests(unittest.TestCase):
    def test_unverified_lending_copy_is_omitted_while_official_fact_is_kept(self) -> None:
        payload = {
            "status": "active",
            "product_name": "Example Card",
            "annual_fee": 0.0,
            "credit_limit_text": "Automatic account alerts",
        }
        normalized_values = {
            "annual_fee": 0.0,
            "credit_limit_text": "Automatic account alerts",
        }
        mappings = {
            "annual_fee": {
                "official_grounding_contract_version": "collection-official-grounding-v1",
                "official_verification_status": "match",
                "official_evidence_quote": "$0 annual fee",
                "official_web_sources": [{"url": "https://bank.example/card"}],
            },
            "credit_limit_text": {"normalization_method": "dynamic_ai_canonical_mapping"},
        }
        notes: list[str] = []

        _suppress_unverified_dynamic_fields(
            candidate_payload=payload,
            normalized_values_for_links=normalized_values,
            field_mapping_metadata=mappings,
            runtime_notes=notes,
        )

        self.assertEqual(payload["annual_fee"], 0.0)
        self.assertNotIn("credit_limit_text", payload)
        self.assertEqual(mappings["credit_limit_text"]["suppressed_reason"], "official_grounding_missing")
        self.assertTrue(any("credit_limit_text" in note for note in notes))

    def test_official_grounding_metadata_is_preserved_for_review_trace(self) -> None:
        field = NormalizationExtractedField(
            field_name="standard_rate",
            candidate_value=3.25,
            value_type="decimal",
            confidence=0.93,
            extraction_method="openai_official_grounding",
            source_document_id="src-001",
            source_snapshot_id="snap-001",
            evidence_chunk_id="chunk-001",
            evidence_text_excerpt="Current annual interest rate is 3.25%.",
            anchor_type="section",
            anchor_value="rates",
            page_no=None,
            chunk_index=1,
            field_metadata={
                "official_grounding_contract_version": "collection-official-grounding-v1",
                "official_grounding_method": "deterministic_labeled_origin",
                "official_verification_status": "mismatch",
                "official_web_sources": [
                    {"url": "https://bank.example/product", "title": "Official product"}
                ],
                "evidence_quote": "Current annual interest rate is 3.25%.",
                "rationale": "Current official detail confirms the rate.",
            },
        )

        metadata = _official_grounding_mapping_metadata(field)

        self.assertEqual(metadata["official_verification_status"], "mismatch")
        self.assertEqual(metadata["official_grounding_method"], "deterministic_labeled_origin")
        self.assertEqual(metadata["official_web_sources"][0]["url"], "https://bank.example/product")
        self.assertEqual(metadata["official_evidence_quote"], "Current annual interest rate is 3.25%.")

    def test_incomplete_description_lead_in_is_rejected(self) -> None:
        self.assertTrue(
            _looks_like_non_value_description(
                field_name="description_short",
                value="With this savings account, your kids have the opportunity to:",
                product_type_family="savings",
                product_name="Children's Savings Account",
            )
        )

    def test_contact_cta_and_flattened_feature_headings_are_not_descriptions(self) -> None:
        for value in (
            "Book now Call us Our banking specialists are ready to answer your questions and can assist you in opening an account 1-866-222-3456.",
            (
                "Monthly account fee Enjoy no monthly fee with this account Earn Interest on every U.S. dollar "
                "Interest calculated daily on every U.S. dollar Foreign Currency Services Competitive exchange rates on U.S."
            ),
        ):
            with self.subTest(value=value):
                self.assertTrue(
                    _looks_like_non_value_description(
                        field_name="description_short",
                        value=value,
                        product_type_family="chequing",
                    )
                )

    def test_cross_sell_audience_and_account_switching_copy_are_not_descriptions(self) -> None:
        product_name = "Performance Chequing Account"
        for value in (
            "EXPLORE OFFERS Kids & teens Provide kids and teens with financial independence by opening a chequing account with no monthly fees.",
            (
                "Manage your pre-authorized payments with a switching service. We make switching to the bank easy. "
                "Transfer your pre-authorized payments from another financial institution to your new bank account."
            ),
        ):
            with self.subTest(value=value):
                self.assertTrue(
                    _looks_like_non_value_description(
                        field_name="description_short",
                        value=value,
                        product_type_family="chequing",
                        product_name=product_name,
                    )
                )

    def test_scotia_legal_offer_and_feature_copy_is_not_customer_value(self) -> None:
        for value in (
            "Symbol optional Legal Text Additional fees apply for shared ABM services.",
            "Set up and make one eligible pre-authorized transaction of at least $50, that recurs for at least 6 months in a row.",
            "You can open your account online or in branch.",
        ):
            self.assertTrue(
                _looks_like_non_value_description(
                    field_name="description_short",
                    value=value,
                    product_type_family="chequing",
                )
            )
        for value in (
            "Earn up to $1,000 when you bundle an eligible banking package, savings account, and credit card. Review offer details.",
            "Open your first Momentum PLUS Savings Account Make a deposit into your account. Additional terms apply. See Welcome Bonus Offer Terms.",
            "Do not need to save Euros Need an account for everyday banking services in currency other than Euros.",
            "Cash in while you can. Open a No Fee Chequing Account and set up an eligible direct deposit today of $100 or more for 3 straight months.",
        ):
            self.assertTrue(
                _looks_like_non_value_description(
                    field_name="description_short",
                    value=value,
                    product_type_family="savings",
                )
            )
        self.assertTrue(
            _looks_like_non_value_description(
                field_name="description_short",
                value=(
                    "Our International student GIC Program is designed to help you fund your GIC program "
                    "account before you arrive in Canada and meet visa requirements."
                ),
                product_type_family="gic",
                product_name="Guaranteed Investment Certificates (GIC)",
            )
        )
        self.assertFalse(
            _looks_like_non_value_description(
                field_name="description_short",
                value=(
                    "Our International student GIC Program helps you fund your account before you arrive "
                    "in Canada and meet visa requirements."
                ),
                product_type_family="gic",
                product_name="International Student GIC Program",
            )
        )
        for value in (
            "Money Master Account holders in the six months preceding the Offer Period are not eligible for this Bonus.",
            (
                "You’re able to earn a guaranteed rate for your entire term. Your interest can compound automatically. "
                "Eligible for both registered and non-registered plans. Your principal is always guaranteed."
            ),
            "You haven’t had a Scotia HISA or Momentum PLUS Savings Account within the last two years. The Promotional Rate applies.",
        ):
            self.assertTrue(
                _looks_like_non_value_eligibility(
                    field_name="eligibility_text",
                    value=value,
                    product_name="Savings Account",
                )
            )
        self.assertTrue(
            _looks_like_non_value_description(
                field_name="description_short",
                value=(
                    "To qualify for this Offer make sure to open a new Platinum credit card account "
                    "between July 2, 2026 and November 1, 2026."
                ),
                product_type_family="credit-card",
            )
        )
        self.assertTrue(
            _looks_like_non_value_eligibility(
                field_name="eligibility_text",
                value=(
                    "To qualify, open a new No-Fee credit card account between October 31, 2025 "
                    "and April 30, 2026."
                ),
                product_name="No-Fee Credit Card",
            )
        )
        self.assertTrue(
            _looks_like_non_value_rewards(
                field_name="rewards_summary",
                value="Earn up to $3,000 in value in the first 14 months, including 100,000 bonus points.",
            )
        )
        self.assertFalse(
            _looks_like_non_value_rewards(
                field_name="rewards_summary",
                value="Earn 2 points per $1 on eligible purchases, plus a welcome offer.",
            )
        )
        self.assertTrue(
            _looks_like_expired_promotional_customer_field(
                field_name="notes",
                value="The introductory balance-transfer rate is 0.99% for the first 9 months.",
                context="Special offer: introductory balance-transfer rate.",
                expired_offer_present=True,
            )
        )
        for value in (
            "Benefits include free transfers and eligible for overdraft protection.",
            "The Cash Bonus Bundle Offer applies when clients complete certain qualifying transactions during the Offer Period.",
            "Account holders receive a waiver of commission on eligible commissionable trades.",
        ):
            self.assertTrue(
                _looks_like_non_value_eligibility(
                    field_name="eligibility_text",
                    value=value,
                    product_name="Preferred Package",
                )
            )

    def test_product_context_semantics_reject_recommender_cross_sell_reward_and_footnote_noise(self) -> None:
        self.assertTrue(
            _looks_like_non_value_description(
                field_name="description_short",
                value="Still not sure? Let us help you decide. Answer a few quick questions and we'll recommend the best account.",
                product_type_family="chequing",
            )
        )
        self.assertTrue(
            _looks_like_non_value_description(
                field_name="description_short",
                value="account fees Learn tips to ensure you find the right account and reduce everyday banking fees.",
                product_type_family="chequing",
            )
        )
        self.assertTrue(
            _looks_like_non_value_description(
                field_name="description_short",
                value=(
                    "Learn tips to ensure you find the right account, including options to help you reduce "
                    "your everyday banking fees."
                ),
                product_type_family="chequing",
            )
        )
        self.assertTrue(
            _looks_like_non_value_eligibility(
                field_name="eligibility_text",
                value="Start with an account, then apply and get approved for any eligible credit card.",
                product_name="Banking for Foreign Workers",
            )
        )
        self.assertTrue(
            _looks_like_non_value_description(
                field_name="description_short",
                value="Features Details Monthly fee $0 Interest rate 0.550% Monthly savings requirement $200 Eligibility with Plans.",
                product_type_family="savings",
            )
        )
        self.assertTrue(
            _looks_like_non_value_description(
                field_name="description_short",
                value="High interest savings accounts explained in 2025. We take a deeper look at the benefits and limitations of this account.",
                product_type_family="savings",
            )
        )
        self.assertTrue(
            _looks_like_non_value_description(
                field_name="description_short",
                value="Earn a 0.50% savings interest rate or a promotional rate when you also open a chequing account.",
                product_type_family="savings",
            )
        )
        self.assertTrue(
            _looks_like_non_value_description(
                field_name="description_short",
                value="Get a Canadian and U.S. dollar Savings Account to use at no additional cost.",
                product_type_family="chequing",
            )
        )
        self.assertTrue(
            _looks_like_non_value_eligibility(
                field_name="eligibility_text",
                value="For example, earn 2x the Points on eligible grocery and gas purchases.",
                product_name="Blue Rewards Chequing Account",
            )
        )
        self.assertTrue(
            _looks_like_broad_page_copy(
                field_name="notes",
                value="Legal Footnote 1 details Standard daily Points usage limits and terms apply.",
            )
        )
        for value in (
            "No. You can only receive one monthly fee rebate per bank account.",
            "legal disclaimer Avion points Earn points once your account is enrolled in a rewards program.",
            "Your high interest account features Save without the effort.",
            "An easy way to manage funds Account at a glance Open an account for Canadians.",
            "With a rewards program, enjoy benefits when you open an eligible bank account.",
            "Funds are available after redemption, or in the case of Another Income Builder GIC, after its payment date.",
            "Legal Bug Ability to set up automatic savings and other generic account tools.",
            "Find a Branch Come see us anytime to open your account.",
            "Earn 4.60% interest for 3 months. Offer expires October 27, 2026.",
        ):
            self.assertTrue(
                _looks_like_non_value_description(
                    field_name="description_short",
                    value=value,
                    product_type_family="chequing",
                )
            )
        for value in (
            "To apply, you’ll need: A valid ID and your personal information.",
            "RBC will automatically apply the highest value rebate you are eligible for each month.",
            "If you already have an eligible account, sign in to activate the Value Program.",
            "Each account owner is eligible for one fee-waiver.",
        ):
            self.assertTrue(
                _looks_like_non_value_eligibility(
                    field_name="eligibility_text",
                    value=value,
                    product_name="Example Account",
                )
            )
        self.assertTrue(
            _looks_like_broad_page_copy(
                field_name="notes",
                value="Other conditions and exceptions may apply; refer to the account disclosures for full details.",
            )
        )
        self.assertTrue(
            _looks_like_broad_page_copy(
                field_name="notes",
                value="Legal Disclaimer footnote Some limitations apply.",
            )
        )

    def test_savings_promotion_without_ongoing_rate_requires_review(self) -> None:
        issues = _compute_validation_issue_codes(
            product_type="savings",
            product_type_family=None,
            subtype_code="standard",
            product_name="Promotional Savings Account",
            country_code="CA",
            bank_code="BANK",
            product_family="deposit",
            source_language="en",
            currency="CAD",
            candidate_payload={"promotional_rate": 4.6, "public_display_rate": 4.6},
            evidence_links=[],
        )

        self.assertIn("required_field_missing", issues)

    def test_dynamic_gic_rate_mechanism_satisfies_rate_requiredness_without_numeric_guess(self) -> None:
        issues = _compute_validation_issue_codes(
            product_type="gic",
            product_type_family=None,
            subtype_code="redeemable",
            product_name="Prime-Linked GIC",
            country_code="CA",
            bank_code="BANK",
            product_family="deposit",
            source_language="en",
            currency="CAD",
            candidate_payload={
                "minimum_deposit": 5000,
                "term_length_text": "1 year",
                "interest_rate_summary": "Variable interest rate linked to changes in Prime.",
            },
            evidence_links=[],
        )

        self.assertNotIn("required_field_missing", issues)

    def test_multi_term_gic_table_satisfies_term_requiredness_without_scalar_term(self) -> None:
        issues = _compute_validation_issue_codes(
            product_type="gic",
            product_type_family=None,
            subtype_code="non_redeemable",
            product_name="Multi-Term GIC",
            country_code="CA",
            bank_code="BANK",
            product_family="deposit",
            source_language="en",
            currency="CAD",
            candidate_payload={
                "minimum_deposit": 1000,
                "standard_rate": 2.7,
                "term_rate_table": [
                    {"term_label": "1 year", "term_length_days": 365, "rate": 2.7},
                    {"term_label": "2 years", "term_length_days": 730, "rate": 2.8},
                ],
            },
            evidence_links=[],
        )

        self.assertNotIn("required_field_missing", issues)

    def test_generic_gic_rate_marketing_copy_does_not_satisfy_rate_requiredness(self) -> None:
        issues = _compute_validation_issue_codes(
            product_type="gic",
            product_type_family=None,
            subtype_code="other",
            product_name="Special GIC",
            country_code="CA",
            bank_code="BANK",
            product_family="deposit",
            source_language="en",
            currency="CAD",
            candidate_payload={
                "minimum_deposit": 1000,
                "term_length_text": "1 year",
                "interest_rate_summary": "Enjoy a competitive interest rate.",
            },
            evidence_links=[],
        )

        self.assertIn("required_field_missing", issues)

    def test_product_name_restores_official_acronym_and_punctuation_formatting(self) -> None:
        notes: list[str] = []
        value = _refine_product_name_from_source_metadata(
            product_name="Rbc U S Personal Account",
            source_metadata={
                "discovery_metadata": {
                    "primary_heading": "RBC U.S. Personal Account",
                    "page_title": "U.S. Dollar Chequing Account | Example Bank",
                }
            },
            runtime_notes=notes,
        )

        self.assertEqual(value, "RBC U.S. Personal Account")
        self.assertIn("Restored official product_name formatting", " ".join(notes))

        notes = []
        value = _refine_product_name_from_source_metadata(
            product_name="Example Non-Redeemable GIC",
            source_metadata={
                "discovery_metadata": {
                    "primary_heading": "Example Non-Redeemable GIC ⓘ",
                    "page_title": "Example Non-Redeemable GIC | Example Bank",
                }
            },
            runtime_notes=notes,
        )
        self.assertEqual(value, "Example Non-Redeemable GIC")

    def test_widget_product_name_uses_official_discovery_heading(self) -> None:
        notes: list[str] = []

        value = _refine_product_name_from_source_metadata(
            product_name="GIC Tab le",
            source_metadata={
                "discovery_metadata": {
                    "primary_heading": "Tax-Free Guaranteed Investment",
                    "page_title": "Tax-Free Guaranteed Investment | Example Bank",
                }
            },
            runtime_notes=notes,
        )

        self.assertEqual(value, "Tax-Free Guaranteed Investment")
        self.assertIn("Replaced generic product_name", " ".join(notes))

        notes = []
        value = _refine_product_name_from_source_metadata(
            product_name="Current GIC interest rates",
            source_metadata={
                "discovery_metadata": {
                    "primary_heading": "Tax-Free Guaranteed Investment",
                    "page_title": "Tax-Free Guaranteed Investment | Example Bank",
                }
            },
            runtime_notes=notes,
        )
        self.assertEqual(value, "Tax-Free Guaranteed Investment")

    def test_marketing_section_product_name_uses_official_discovery_heading(self) -> None:
        notes: list[str] = []
        value = _refine_product_name_from_source_metadata(
            product_name="Benefits Of Banking With TD",
            source_metadata={
                "discovery_metadata": {
                    "primary_heading": "U.S. Daily Interest Chequing Account",
                    "page_title": "Open a TD U.S. Dollar Account | TD Canada Trust",
                }
            },
            runtime_notes=notes,
        )

        self.assertEqual(value, "U.S. Daily Interest Chequing Account")

    def test_ongoing_extra_bonus_adds_to_regular_public_rate_without_marking_promo(self) -> None:
        payload: dict[str, object] = {"standard_rate": 0.01, "public_display_rate": 0.01}
        metadata: dict[str, object] = {}
        normalized_values: dict[str, object] = dict(payload)
        links = [
            NormalizationEvidenceLink(
                field_name="public_display_rate",
                candidate_value="0.01",
                evidence_chunk_id="chunk-smart-savings",
                evidence_text_excerpt=(
                    "Monthly account fee $0. Regular interest rate 0.01%. "
                    "Bonus interest rate - Earn an extra 0.49% interest if enrolled in a Smart Savings Tool."
                ),
                source_document_id="src-001",
                source_snapshot_id="snap-001",
                citation_confidence=0.99,
                model_execution_id=None,
                anchor_type="section",
                anchor_value="At a glance",
                page_no=None,
                chunk_index=1,
            )
        ]
        notes: list[str] = []

        _align_ongoing_additive_bonus_total(
            product_type_family="savings",
            candidate_payload=payload,
            field_mapping_metadata=metadata,
            normalized_values_for_links=normalized_values,
            evidence_links_for_output=links,
            runtime_notes=notes,
        )

        self.assertEqual(payload["standard_rate"], 0.01)
        self.assertEqual(payload["public_display_rate"], 0.5)
        self.assertNotIn("promotional_rate", payload)
        self.assertEqual(metadata["public_display_rate"]["normalization_method"], "ongoing_additive_bonus_total_alignment")

    def test_gic_exact_posted_and_promotional_labels_repair_truncated_rate(self) -> None:
        payload: dict[str, object] = {
            "standard_rate": 0.0,
            "public_display_rate": 0.0,
            "term_rate_table": [
                {"term_label": "1 year", "term_length_days": 365, "rate": 2.0}
            ],
        }
        metadata: dict[str, object] = {}
        normalized_values: dict[str, object] = dict(payload)
        source_link = NormalizationEvidenceLink(
            field_name="standard_rate",
            candidate_value="0.0",
            evidence_chunk_id="chunk-variable-gic",
            evidence_text_excerpt=(
                "CIBC Variable Rate GIC Promotional Rate 00% on a 1-year GIC. "
                "2.00% 1-year CIBC Variable Rate GIC. Posted rate: 1.75%."
            ),
            source_document_id="src-variable-gic",
            source_snapshot_id="snap-variable-gic",
            citation_confidence=0.9,
            model_execution_id=None,
            anchor_type="section",
            anchor_value="rates",
            page_no=None,
            chunk_index=2,
        )
        links = [source_link]

        _align_gic_labeled_posted_and_promotional_rates(
            product_type_family="gic",
            candidate_payload=payload,
            field_mapping_metadata=metadata,
            normalized_values_for_links=normalized_values,
            evidence_links_for_output=links,
            runtime_notes=[],
        )

        self.assertEqual(payload["standard_rate"], 1.75)
        self.assertEqual(payload["promotional_rate"], 2.0)
        self.assertEqual(payload["public_display_rate"], 2.0)
        self.assertTrue(payload["introductory_rate_flag"])

    def test_cleaner_removes_promotion_mapped_as_standard_rate(self) -> None:
        payload: dict[str, object] = {
            "standard_rate": 4.5,
            "promotional_rate": 4.5,
            "public_display_rate": 4.5,
        }
        normalized_values = dict(payload)
        mapping = {field_name: {"normalized_value": value} for field_name, value in payload.items()}
        evidence = "Earn 4.50% for 5 months with this New Client offer."

        _clean_product_context_fields(
            product_type_family="savings",
            candidate_payload=payload,
            normalized_values_for_links=normalized_values,
            field_mapping_metadata=mapping,
            evidence_context_by_field={field_name: evidence for field_name in payload},
            evidence_excerpt_by_field={field_name: evidence for field_name in payload},
        )

        self.assertNotIn("standard_rate", payload)
        self.assertEqual(payload["promotional_rate"], 4.5)
        self.assertEqual(payload["public_display_rate"], 4.5)

    def test_product_header_standard_rate_survives_adjacent_promotional_offer(self) -> None:
        evidence = (
            "Savings Account 0.30% Interest rate $0 Monthly fee $0 Minimum balance "
            "Limited-time offer Earn 4.50% for 5 months."
        )
        payload: dict[str, object] = {
            "standard_rate": 0.3,
            "promotional_rate": 4.5,
            "public_display_rate": 4.5,
        }

        _clean_product_context_fields(
            product_type_family="savings",
            candidate_payload=payload,
            evidence_context_by_field={field_name: evidence for field_name in payload},
            evidence_excerpt_by_field={
                "standard_rate": evidence,
                "promotional_rate": evidence,
                "public_display_rate": evidence,
            },
        )

        self.assertEqual(payload["standard_rate"], 0.3)
        self.assertEqual(payload["promotional_rate"], 4.5)

    def test_account_copy_cleanup_keeps_only_decision_ready_channels_and_transaction_rule(self) -> None:
        payload = {
            "product_name": "Example Every Day Savings Account",
            "description_short": (
                "No transfer fee to send money. Pay your friends back or chip in for pizza using a transfer. "
                "Additional account benefits Enjoy online statements."
            ),
            "withdrawal_limit_text": (
                "Account Fees Monthly Fee $0 Transactions included per month 2 1 "
                "Additional Transactions 2 $3.00 each Free Transfers Unlimited Foreign ATM Fee $5.00 each"
            ),
            "application_method": (
                "Secure Open online Get account Book an appointment Meet with a banking specialist in person "
                "at the branch closest to you."
            ),
        }
        normalized_values = dict(payload)
        metadata = {field_name: {} for field_name in payload}

        _clean_product_context_fields(
            product_type_family="savings",
            candidate_payload=payload,
            normalized_values_for_links=normalized_values,
            field_mapping_metadata=metadata,
            runtime_notes=[],
            evidence_context_by_field={},
            evidence_excerpt_by_field={},
        )

        self.assertNotIn("description_short", payload)
        self.assertEqual(
            payload["withdrawal_limit_text"],
            "1 transaction per month included; additional transactions cost $3.00 each.",
        )
        self.assertEqual(payload["application_method"], "Online or at a branch.")

    def test_savings_cleanup_removes_offer_eligibility_award_copy_and_calculator_prose(self) -> None:
        payload: dict[str, object] = {
            "description_short": "Confidently save with Ratehub's best RRSP savings account.",
            "eligibility_text": (
                "The Tangerine New Client Two Rate Savings Offer is available to new clients who have a "
                "Client Number created during the offer period and open an Eligible Savings Account within 60 days."
            ),
            "interest_calculation_method": (
                "Estimator only. Calculations are estimates based on the current interest rate of 0.30%, "
                "based on interest calculated daily and paid monthly, assuming no withdrawals."
            ),
        }
        normalized_values = dict(payload)
        metadata = {field_name: {"normalized_value": value} for field_name, value in payload.items()}

        _clean_product_context_fields(
            product_type_family="savings",
            candidate_payload=payload,
            normalized_values_for_links=normalized_values,
            field_mapping_metadata=metadata,
        )

        self.assertEqual(
            payload,
            {"interest_calculation_method": "Interest is calculated daily and paid monthly."},
        )
        self.assertEqual(
            metadata["interest_calculation_method"]["normalization_method"],
            "daily_monthly_interest_method_cleanup",
        )

    def test_cleaner_rejects_direct_deposit_threshold_mapped_as_monthly_fee(self) -> None:
        payload: dict[str, object] = {"monthly_fee": 100.0, "public_display_fee": 100.0}
        normalized_values = dict(payload)
        mapping = {field_name: {"normalized_value": value} for field_name, value in payload.items()}
        evidence = (
            "Open a No Fee Chequing Account and set up an eligible direct deposit today of "
            "$100 or more for 3 straight months. Plus, you'll pay no monthly fees."
        )

        _clean_product_context_fields(
            product_type_family="chequing",
            candidate_payload=payload,
            normalized_values_for_links=normalized_values,
            field_mapping_metadata=mapping,
            evidence_context_by_field={field_name: evidence for field_name in payload},
            evidence_excerpt_by_field={field_name: evidence for field_name in payload},
        )

        self.assertNotIn("monthly_fee", payload)
        self.assertNotIn("public_display_fee", payload)

    def test_percentage_value_requires_exact_grounding_in_its_evidence(self) -> None:
        self.assertTrue(
            _percentage_value_absent_from_evidence(
                field_name="interest_rate",
                value=20.0,
                context="Very competitive secured rates. Minimum payments could be as low as interest only 2.",
            )
        )
        for value, context in (
            (1.0, "Get a lower interest rate of Prime + 1% for your line of credit."),
            (0.5, "Interest at Scotiabank prime plus 0.50% will accrue monthly."),
            (0.0, "No interest is payable on this chequing account."),
        ):
            with self.subTest(value=value):
                self.assertFalse(
                    _percentage_value_absent_from_evidence(
                        field_name="interest_rate",
                        value=value,
                        context=context,
                    )
                )

    def test_dynamic_numeric_fields_require_exact_unit_bearing_evidence(self) -> None:
        prime_margin_link = NormalizationEvidenceLink(
            field_name="interest_rate_summary",
            candidate_value="Scotiabank Prime + 1%",
            evidence_chunk_id="chunk-prime-margin",
            evidence_text_excerpt="Get a lower interest rate of Scotiabank Prime + 1% for your line of credit.",
            source_document_id="doc-loc",
            source_snapshot_id="snap-loc",
            citation_confidence=0.95,
            model_execution_id=None,
            anchor_type="heading",
            anchor_value="Interest rate",
            page_no=None,
            chunk_index=0,
        )
        margin_context = _find_dynamic_numeric_evidence_context(
            field_name="interest_rate",
            value=1.0,
            evidence_links=[prime_margin_link],
        )

        self.assertIn("Prime + 1%", margin_context)
        self.assertTrue(
            _looks_like_non_rate_numeric_context(
                field_name="interest_rate",
                value=1.0,
                context=margin_context,
            )
        )
        self.assertTrue(
            _dynamic_numeric_value_is_ungrounded(
                field_name="interest_rate",
                value=20.0,
                context="",
                dynamic_field_names={"interest_rate"},
            )
        )

        deposit_link = NormalizationEvidenceLink(
            **{
                **prime_margin_link.__dict__,
                "field_name": "minimum_deposit",
                "candidate_value": "$1,000",
                "evidence_chunk_id": "chunk-minimum-deposit",
                "evidence_text_excerpt": "A minimum deposit of $1,000 is required.",
            }
        )
        self.assertIn(
            "$1,000",
            _find_dynamic_numeric_evidence_context(
                field_name="minimum_deposit",
                value=1000,
                evidence_links=[deposit_link],
            ),
        )

    def test_cleaner_removes_ungrounded_percentage_value(self) -> None:
        payload: dict[str, object] = {"interest_rate": 20.0}
        normalized_values: dict[str, object] = dict(payload)
        mapping = {"interest_rate": {"normalized_value": 20.0}}
        notes: list[str] = []

        _clean_product_context_fields(
            product_type_family="line-of-credit",
            candidate_payload=payload,
            normalized_values_for_links=normalized_values,
            field_mapping_metadata=mapping,
            runtime_notes=notes,
            evidence_context_by_field={
                "interest_rate": "Very competitive secured rates. Minimum payments could be as low as interest only 2."
            },
            evidence_excerpt_by_field={
                "interest_rate": "Very competitive secured rates. Minimum payments could be as low as interest only 2."
            },
        )

        self.assertNotIn("interest_rate", payload)
        self.assertNotIn("interest_rate", normalized_values)
        self.assertNotIn("interest_rate", mapping)
        self.assertTrue(any("ungrounded" in note for note in notes))

    def test_dynamic_numeric_field_without_direct_evidence_is_removed_even_without_percentage_check(self) -> None:
        payload: dict[str, object] = {"interest_rate": 20.0}
        _clean_product_context_fields(
            product_type_family="line-of-credit",
            candidate_payload=payload,
            evidence_context_by_field={"interest_rate": ""},
            evidence_excerpt_by_field={"interest_rate": ""},
            dynamic_field_names={"interest_rate"},
            enforce_percentage_evidence_grounding=False,
        )
        self.assertNotIn("interest_rate", payload)

    def test_implausible_monthly_account_fee_routes_to_validation_error(self) -> None:
        issues = _compute_validation_issue_codes(
            product_type="chequing",
            product_type_family="chequing",
            subtype_code="standard",
            product_name="Basic Bank Account",
            country_code="CA",
            bank_code="BANK",
            product_family="deposit",
            source_language="en",
            currency="CAD",
            candidate_payload={"monthly_fee": 4000.0},
            evidence_links=[],
        )
        self.assertIn("invalid_numeric_range", issues)

    def test_premium_credit_card_annual_fee_uses_an_annual_not_monthly_limit(self) -> None:
        issues = _compute_validation_issue_codes(
            product_type="credit-card",
            product_type_family="credit-card",
            subtype_code="premium",
            product_name="Example Infinite Privilege Card",
            country_code="CA",
            bank_code="BANK",
            product_family="credit",
            source_language="en",
            currency="CAD",
            candidate_payload={"annual_fee": 599.0},
            evidence_links=[],
        )
        self.assertNotIn("invalid_numeric_range", issues)

    def test_profile_specific_numeric_extensions_share_rate_and_fee_range_guards(self) -> None:
        common = {
            "product_type": "savings",
            "product_type_family": "savings",
            "subtype_code": "high_interest",
            "product_name": "High Interest Savings Account",
            "country_code": "CA",
            "bank_code": "BANK",
            "product_family": "deposit",
            "source_language": "en",
            "currency": "CAD",
            "evidence_links": [],
        }
        for payload in ({"regular_interest_rate": 60.0}, {"transaction_fee": 500.0}):
            with self.subTest(payload=payload):
                issues = _compute_validation_issue_codes(candidate_payload=payload, **common)
                self.assertIn("invalid_numeric_range", issues)

    def test_term_rate_text_normalizes_to_typed_rows(self) -> None:
        rows = _normalize_term_rate_table("1 Year 3.30%, 5 Years 4.00%")

        self.assertEqual(
            rows,
            [
                {"term_label": "1 Year", "term_length_days": 365, "rate": 3.3, "minimum_deposit": None, "notes": None},
                {"term_label": "5 Years", "term_length_days": 1825, "rate": 4.0, "minimum_deposit": None, "notes": None},
            ],
        )

    def test_multi_term_gic_uses_disclosed_one_year_rate_as_standard_comparison(self) -> None:
        payload = {
            "standard_rate": 2.55,
            "base_12_month_rate": 3.65,
            "public_display_rate": 3.65,
            "term_rate_table": [
                {"term_label": "90 Day", "term_length_days": 90, "rate": 2.55},
                {"term_label": "1 Year", "term_length_days": 365, "rate": 3.15},
                {"term_label": "5 Year", "term_length_days": 1825, "rate": 3.65},
            ],
        }
        metadata: dict[str, object] = {}
        values: dict[str, object] = {}
        notes: list[str] = []

        _align_gic_representative_rates_from_term_table(
            product_type_family="gic",
            candidate_payload=payload,
            field_mapping_metadata=metadata,
            normalized_values_for_links=values,
            evidence_links_for_output=[],
            runtime_notes=notes,
        )

        self.assertEqual(payload["standard_rate"], 3.15)
        self.assertEqual(payload["base_12_month_rate"], 3.15)
        self.assertEqual(payload["public_display_rate"], 3.65)
        self.assertTrue(any("12-month" in note for note in notes))

    def test_savings_header_rate_replaces_unrelated_prime_rate(self) -> None:
        payload = {"standard_rate": 4.45, "promotional_rate": 4.6, "public_display_rate": 4.6}
        metadata: dict[str, object] = {}
        values: dict[str, object] = {}
        notes: list[str] = []
        links = [
            NormalizationEvidenceLink(
                field_name="monthly_fee",
                candidate_value="0",
                evidence_chunk_id="chunk-header",
                evidence_text_excerpt=(
                    "RSP Savings Account Save for retirement. 0.30% Interest rate "
                    "$0 Monthly fee $0 Minimum balance Limited-time offer Earn 4.60% for 5 months."
                ),
                source_document_id="source-detail",
                source_snapshot_id="snapshot-detail",
                citation_confidence=0.95,
                model_execution_id=None,
                anchor_type="heading",
                anchor_value="RSP Savings Account",
                page_no=None,
                chunk_index=0,
            )
        ]

        _align_savings_labeled_header_standard_rate(
            product_type_family="savings",
            candidate_payload=payload,
            field_mapping_metadata=metadata,
            normalized_values_for_links=values,
            evidence_links_for_output=links,
            runtime_notes=notes,
        )

        self.assertEqual(payload["standard_rate"], 0.3)
        self.assertEqual(payload["promotional_rate"], 4.6)
        self.assertEqual(payload["public_display_rate"], 4.6)
        self.assertEqual(metadata["standard_rate"]["normalization_method"], "savings_labeled_header_standard_rate_alignment")

    def test_savings_apy_header_survives_separate_referral_rate_boost(self) -> None:
        excerpt = (
            "Online Savings Account 3.40% Annual Percentage Yield. No fees. No minimum deposit. "
            "Refer a friend and you both could earn a 1.00% APY rate boost for 3 months."
        )
        link = NormalizationEvidenceLink(
            field_name="promotional_rate",
            candidate_value="3.40",
            evidence_chunk_id="chunk-marcus-header",
            evidence_text_excerpt=excerpt,
            source_document_id="source-marcus-savings",
            source_snapshot_id="snapshot-marcus-savings",
            citation_confidence=0.95,
            model_execution_id=None,
            anchor_type="document",
            anchor_value="Document",
            page_no=None,
            chunk_index=0,
        )
        payload = {
            "promotional_rate": 3.4,
            "public_display_rate": 3.4,
            "promotional_period_text": "3 months",
            "introductory_rate_flag": True,
        }
        metadata: dict[str, object] = {}
        values: dict[str, object] = dict(payload)
        links = [link]
        notes: list[str] = []

        _align_savings_labeled_header_standard_rate(
            product_type_family="savings",
            candidate_payload=payload,
            field_mapping_metadata=metadata,
            normalized_values_for_links=values,
            evidence_links_for_output=links,
            runtime_notes=notes,
        )
        _suppress_uncombined_savings_rate_boost(
            product_type_family="savings",
            candidate_payload=payload,
            field_mapping_metadata=metadata,
            normalized_values_for_links=values,
            evidence_links_for_output=links,
            runtime_notes=notes,
        )

        self.assertEqual(payload["standard_rate"], 3.4)
        self.assertEqual(payload["public_display_rate"], 3.4)
        self.assertNotIn("promotional_rate", payload)
        self.assertNotIn("promotional_period_text", payload)
        self.assertNotIn("introductory_rate_flag", payload)
        self.assertEqual(
            metadata["promotional_rate"]["suppressed_reason"],
            "incremental_rate_boost_not_total_apy",
        )

    def test_savings_subtype_uses_country_domestic_currency(self) -> None:
        us_subtype, _ = _infer_subtype_code(
            product_type="savings",
            country_code="US",
            currency="USD",
            candidate_payload={"product_name": "Online Savings Account"},
        )
        canadian_usd_subtype, _ = _infer_subtype_code(
            product_type="savings",
            country_code="CA",
            currency="USD",
            candidate_payload={"product_name": "U.S. Dollar Savings Account"},
        )

        self.assertEqual(us_subtype, "standard")
        self.assertEqual(canadian_usd_subtype, "foreign_currency")

    def test_comparison_calculator_values_do_not_become_product_terms(self) -> None:
        context = (
            "Choose up to 4 banks to compare. This calculator is for illustrative purposes only. "
            "Rates of the selected banks reflect similar products with a minimum balance of $2,500. "
            "Calculated values assume principal and interest remain on deposit."
        )

        self.assertTrue(
            _field_is_comparison_calculator_copy(
                field_name="minimum_balance",
                value=2500,
                context=context,
            )
        )
        self.assertTrue(
            _field_is_comparison_calculator_copy(
                field_name="interest_calculation_method",
                value="Calculated values assume principal remains on deposit.",
                context=context,
            )
        )
        self.assertFalse(
            _field_is_comparison_calculator_copy(
                field_name="minimum_deposit",
                value=0,
                context="No minimum deposit.",
            )
        )

    def test_fractional_year_term_normalizes_without_becoming_five_year(self) -> None:
        rows = _normalize_term_rate_table("1 Year 3.15%, 1.5 Year 3.25%, 5 Years 3.65%")

        self.assertEqual(
            [(row["term_label"], row["term_length_days"], row["rate"]) for row in rows],
            [("1 Year", 365, 3.15), ("1.5 Year", 548, 3.25), ("5 Years", 1825, 3.65)],
        )

    def test_term_rate_range_does_not_collapse_to_range_end(self) -> None:
        rows = _normalize_term_rate_table(
            [{"term_label": "30-59 days", "term_length_days": None, "rate": "1.00", "notes": "Short-term GIC"}]
        )

        self.assertEqual(rows[0]["term_label"], "30-59 days")
        self.assertIsNone(rows[0]["term_length_days"])
        self.assertEqual(rows[0]["rate"], 1.0)

    def test_evidence_link_keeps_supporting_source_document(self) -> None:
        link = NormalizationEvidenceLink(
            field_name="standard_rate",
            candidate_value="3.30",
            evidence_chunk_id="chunk-support",
            evidence_text_excerpt="1 Year 3.30%",
            source_document_id="source-support",
            source_snapshot_id="snapshot-support",
            citation_confidence=0.9,
            model_execution_id=None,
            anchor_type="heading",
            anchor_value="Rates",
            page_no=None,
            chunk_index=1,
        )

        records = _build_field_evidence_link_records(
            candidate_id="candidate-target",
            normalized_values_for_links={"standard_rate": 3.3},
            source_document_id="source-target",
            evidence_links=[link],
        )

        self.assertEqual(records[0]["source_document_id"], "source-support")

    def test_gic_rate_rejects_nearby_personal_account_direct_deposit_rate(self) -> None:
        context = (
            "Everyday Banking Personal Account Rates Earn 2.75% interest. "
            "Boost your interest rate in your Personal Account when you set up direct deposit. "
            "Investing GICs RRSP."
        )

        self.assertTrue(_rate_evidence_is_account_context(value="2.75", context=context))
        self.assertFalse(_rate_evidence_is_account_context(value="4.10", context="1 year GIC rate 4.10%"))
        self.assertEqual(_extract_rate_percentages(context, product_type_family="gic"), [])
        self.assertEqual([float(value) for value in _extract_rate_percentages(context, product_type_family="savings")], [2.75])

    def test_rate_fallback_rejects_market_scenario_return_with_distant_context_marker(self) -> None:
        context = (
            "RBC Equity-Linked GIC Scenario 1: Market is Up. The reference value of the underlying index "
            "is measured at the start and end of the five-year term. In this illustrative example, the "
            "index moves from 100 to 120 and the depositor receives the original principal plus a 20% "
            "return on the investment at maturity."
        )

        self.assertGreater(context.index("20%") - context.index("Scenario 1"), 90)
        self.assertEqual(_extract_rate_percentages(context, product_type_family="gic"), [])

    def test_public_display_rate_uses_total_promo_instead_of_bonus_component(self) -> None:
        promo_link = NormalizationEvidenceLink(
            field_name="promotional_rate",
            candidate_value="4.6",
            evidence_chunk_id="chunk-promo",
            evidence_text_excerpt=(
                "Regular Interest Rate 0.55% plus Bonus Interest Rate 4.05%; "
                "the Promotional Interest Rate would be 4.60% per annum."
            ),
            source_document_id="source-promo",
            source_snapshot_id="snapshot-promo",
            citation_confidence=0.9,
            model_execution_id=None,
            anchor_type="heading",
            anchor_value="Offer",
            page_no=None,
            chunk_index=2,
        )
        stale_display_link = NormalizationEvidenceLink(
            field_name="public_display_rate",
            candidate_value="4.05",
            evidence_chunk_id="chunk-bonus",
            evidence_text_excerpt="The Bonus Interest Rate is 4.05% per annum.",
            source_document_id="source-bonus",
            source_snapshot_id="snapshot-bonus",
            citation_confidence=0.8,
            model_execution_id=None,
            anchor_type="heading",
            anchor_value="Legal",
            page_no=None,
            chunk_index=3,
        )
        payload: dict[str, object] = {"promotional_rate": 4.6, "public_display_rate": 4.05}
        links = [promo_link, stale_display_link]

        _align_public_display_rate(
            product_type_family="savings",
            candidate_payload=payload,
            field_mapping_metadata={},
            normalized_values_for_links={},
            evidence_links_for_output=links,
            runtime_notes=[],
        )

        self.assertEqual(payload["public_display_rate"], 4.6)
        display_links = [link for link in links if link.field_name == "public_display_rate"]
        self.assertEqual(len(display_links), 1)
        self.assertEqual(display_links[0].evidence_chunk_id, "chunk-promo")

    def test_split_gic_page_row_completes_table_and_drives_highest_display_rate(self) -> None:
        first_page = NormalizationEvidenceLink(
            field_name="standard_rate",
            candidate_value="2.55",
            evidence_chunk_id="chunk-page-2",
            evidence_text_excerpt="Current GIC interest rates Term Rate 90 Day 2.55%",
            source_document_id="source-gic",
            source_snapshot_id="snapshot-gic",
            citation_confidence=0.98,
            model_execution_id=None,
            anchor_type="page",
            anchor_value="page-2",
            page_no=2,
            chunk_index=2,
        )
        remaining_page = NormalizationEvidenceLink(
            field_name="term_rate_table",
            candidate_value="table",
            evidence_chunk_id="chunk-page-3",
            evidence_text_excerpt="180 Day 2.65% 1 Year 3.15% 1.5 Year 3.25% 5 Year 3.65%",
            source_document_id="source-gic",
            source_snapshot_id="snapshot-gic",
            citation_confidence=0.9,
            model_execution_id=None,
            anchor_type="page",
            anchor_value="page-3",
            page_no=3,
            chunk_index=3,
        )
        payload: dict[str, object] = {
            "standard_rate": 2.55,
            "public_display_rate": 2.55,
            "term_rate_table": [
                {"term_label": "180 day", "term_length_days": 180, "rate": 2.65},
                {"term_label": "1 year", "term_length_days": 365, "rate": 3.15},
                {"term_label": "1.5 year", "term_length_days": 548, "rate": 3.25},
                {"term_label": "5 year", "term_length_days": 1825, "rate": 3.65},
            ],
        }
        normalized_values = dict(payload)
        metadata: dict[str, object] = {}
        links = [first_page, remaining_page]
        notes: list[str] = []

        _complete_gic_term_rate_table_from_split_evidence(
            product_type_family="gic",
            candidate_payload=payload,
            field_mapping_metadata=metadata,
            normalized_values_for_links=normalized_values,
            evidence_links_for_output=links,
            runtime_notes=notes,
        )
        _align_public_display_rate(
            product_type_family="gic",
            candidate_payload=payload,
            field_mapping_metadata=metadata,
            normalized_values_for_links=normalized_values,
            evidence_links_for_output=links,
            runtime_notes=notes,
        )

        self.assertEqual(payload["term_rate_table"][0]["term_label"], "90 day")
        self.assertEqual(payload["term_rate_table"][2]["term_label"], "1 year")
        self.assertEqual(payload["public_display_rate"], 3.65)
        self.assertEqual(metadata["term_rate_table"]["normalization_method"], "split_evidence_term_table_completion")
        self.assertEqual(
            {link.evidence_chunk_id for link in links if link.field_name == "term_rate_table"},
            {"chunk-page-2", "chunk-page-3"},
        )

    def test_missing_gic_table_is_recovered_only_from_exact_product_evidence(self) -> None:
        target_link = NormalizationEvidenceLink(
            field_name="minimum_deposit",
            candidate_value="500",
            evidence_chunk_id="chunk-target-table",
            evidence_text_excerpt=(
                "Example Non-Redeemable GIC Terms and rates Minimum investment of $500 "
                "Term Rate 1 year 2.70% 2 years 2.75% 3 years 2.85% 4 years 3.00% 5 years 3.10%"
            ),
            source_document_id="source-target",
            source_snapshot_id="snapshot-target",
            citation_confidence=0.98,
            model_execution_id=None,
            anchor_type="section",
            anchor_value="terms-and-rates",
            page_no=None,
            chunk_index=3,
        )
        sibling_link = NormalizationEvidenceLink(
            field_name="standard_rate",
            candidate_value="4.10",
            evidence_chunk_id="chunk-sibling-table",
            evidence_text_excerpt="Example USD GIC Term Rate 1 year 3.90% 5 years 4.10%",
            source_document_id="source-sibling",
            source_snapshot_id="snapshot-sibling",
            citation_confidence=0.95,
            model_execution_id=None,
            anchor_type="section",
            anchor_value="terms-and-rates",
            page_no=None,
            chunk_index=4,
        )
        payload: dict[str, object] = {
            "product_name": "Example Non-Redeemable GIC ⓘ",
            "standard_rate": 2.7,
            "minimum_deposit": 500,
        }
        normalized_values = dict(payload)
        metadata: dict[str, object] = {}
        links = [target_link, sibling_link]
        notes: list[str] = []

        _complete_gic_term_rate_table_from_split_evidence(
            product_type_family="gic",
            candidate_payload=payload,
            field_mapping_metadata=metadata,
            normalized_values_for_links=normalized_values,
            evidence_links_for_output=links,
            runtime_notes=notes,
        )

        self.assertEqual([row["rate"] for row in payload["term_rate_table"]], [2.7, 2.75, 2.85, 3.0, 3.1])
        self.assertEqual(
            {link.evidence_chunk_id for link in links if link.field_name == "term_rate_table"},
            {"chunk-target-table"},
        )

    def test_gic_legal_fee_and_rate_calculator_copy_are_not_descriptions(self) -> None:
        for description in (
            (
                "Fair fees mean they are disclosed in advance. Registered Accounts have no fees while your funds "
                "are with us. If you transfer your funds, a fee will apply."
            ),
            (
                "180 Day 2.65% 270 Day 3.00% 1 Year 3.15% 1.5 Year 3.25% 5 Year 3.65% "
                "GIC Interest Calculator See how much interest you'll earn in your GIC."
            ),
            "You may provide us with instructions as to what to do with your GIC proceeds upon maturity.",
        ):
            payload = {"product_name": "Example GIC", "description_short": description}
            _clean_product_context_fields(product_type_family="gic", candidate_payload=payload)
            self.assertNotIn("description_short", payload)

        acquisition = {
            "product_name": "Example Non-Redeemable GIC",
            "description_short": (
                "A personal bank account to fund your Investment Account Need an account? "
                "Apply for a personal bank account Meet with us or call us."
            ),
            "deposit_insurance": (
                "Get started Meet with us Call us Find a banking centre "
                "Example Bank is a member of Canada Deposit Insurance Corporation (CDIC)."
            ),
        }
        _clean_product_context_fields(product_type_family="gic", candidate_payload=acquisition)
        self.assertNotIn("description_short", acquisition)
        self.assertEqual(
            acquisition["deposit_insurance"],
            "Example Bank is a member of Canada Deposit Insurance Corporation (CDIC).",
        )

        flattened = {
            "product_name": "Example Savings Account",
            "description_short": (
                "Open an Accountfor Canadians. Set up an account that makes iteasier to save, "
                "and enjoy thechance to growand manage funds atany time."
            ),
        }
        _clean_product_context_fields(product_type_family="savings", candidate_payload=flattened)
        self.assertEqual(
            flattened["description_short"],
            "Open an Account for Canadians. Set up an account that makes it easier to save, "
            "and enjoy the chance to grow and manage funds at any time.",
        )

        channel_and_offer_copy = (
            "You can open this account online via Online Banking or in person at a branch. "
            "If you open it online, the bank may ask you to verify your ID at a branch."
        )
        current_acquisition_offer = (
            "Open an Unlimited Banking Account and Get a New Tablet. Offer Ends November 2, 2026. "
            "Qualifying Criteria and other Conditions Apply."
        )
        for description in (channel_and_offer_copy, current_acquisition_offer):
            payload = {"product_name": "Example Banking Account", "description_short": description}
            _clean_product_context_fields(product_type_family="chequing", candidate_payload=payload)
            self.assertNotIn("description_short", payload)

        truncated_eligibility = {
            "product_name": "Example Banking Account",
            "eligibility_text": (
                "Example Benefits is the way we describe all of the powerful benefits you can get just by having an eligible"
            ),
        }
        _clean_product_context_fields(product_type_family="chequing", candidate_payload=truncated_eligibility)
        self.assertNotIn("eligibility_text", truncated_eligibility)

        sibling_audience = {
            "product_name": "High Interest Savings Account",
            "description_short": (
                "Savings Accounts for Kids. It’s never too early for kids to start saving. "
                "A children’s savings account can help kids develop smart money habits."
            ),
        }
        _clean_product_context_fields(product_type_family="savings", candidate_payload=sibling_audience)
        self.assertNotIn("description_short", sibling_audience)

    def test_public_display_fee_uses_directly_grounded_monthly_fee(self) -> None:
        monthly_link = NormalizationEvidenceLink(
            field_name="monthly_fee",
            candidate_value="4.0",
            evidence_chunk_id="chunk-target-fee",
            evidence_text_excerpt="Practical Chequing Account $4 per month. Includes 12 transactions.",
            source_document_id="source-practical",
            source_snapshot_id="snapshot-practical",
            citation_confidence=0.9,
            model_execution_id=None,
            anchor_type="section",
            anchor_value="fees",
            page_no=None,
            chunk_index=2,
        )
        wrong_display_link = NormalizationEvidenceLink(
            field_name="public_display_fee",
            candidate_value="17.95",
            evidence_chunk_id="chunk-comparison",
            evidence_text_excerpt="Performance Chequing Account $17.95 per month.",
            source_document_id="source-practical",
            source_snapshot_id="snapshot-practical",
            citation_confidence=0.7,
            model_execution_id=None,
            anchor_type="section",
            anchor_value="comparison",
            page_no=None,
            chunk_index=5,
        )
        payload: dict[str, object] = {"monthly_fee": 4.0, "public_display_fee": 17.95}
        links = [monthly_link, wrong_display_link]

        _align_public_display_fee(
            product_type_family="chequing",
            candidate_payload=payload,
            field_mapping_metadata={},
            normalized_values_for_links={},
            evidence_links_for_output=links,
            runtime_notes=[],
        )

        self.assertEqual(payload["public_display_fee"], 4.0)
        display_links = [link for link in links if link.field_name == "public_display_fee"]
        self.assertEqual(len(display_links), 1)
        self.assertEqual(display_links[0].evidence_chunk_id, "chunk-target-fee")

    def test_adjacent_plan_fee_waiver_cannot_set_target_minimum_balance(self) -> None:
        payload: dict[str, object] = {
            "monthly_fee": 4.0,
            "minimum_balance": 4000.0,
            "fee_waiver_condition": (
                "Monthly fee 17.95 is waived to 0.00 with a 4000.00 minimum balance."
            ),
        }
        links = [
            NormalizationEvidenceLink(
                field_name=field_name,
                candidate_value=str(value),
                evidence_chunk_id="chunk-comparison",
                evidence_text_excerpt=(
                    "Practical $4 per month. Performance $17.95 or $0 with a $4,000 minimum balance."
                ),
                source_document_id="source-practical",
                source_snapshot_id="snapshot-practical",
                citation_confidence=0.75,
                model_execution_id=None,
                anchor_type="section",
                anchor_value="comparison",
                page_no=None,
                chunk_index=5,
            )
            for field_name, value in (
                ("minimum_balance", 4000.0),
                ("fee_waiver_condition", payload["fee_waiver_condition"]),
            )
        ]

        _clean_chequing_fee_waiver_consistency(
            product_type_family="chequing",
            candidate_payload=payload,
            field_mapping_metadata={
                "minimum_balance": {},
                "fee_waiver_condition": {},
            },
            normalized_values_for_links={
                "minimum_balance": 4000.0,
                "fee_waiver_condition": payload["fee_waiver_condition"],
            },
            evidence_links_for_output=links,
            runtime_notes=[],
        )

        self.assertNotIn("minimum_balance", payload)
        self.assertNotIn("fee_waiver_condition", payload)
        self.assertEqual(links, [])

    def test_conditional_zero_is_aligned_to_waiver_disclosures_positive_base_fee(self) -> None:
        payload: dict[str, object] = {
            "monthly_fee": 0.0,
            "public_display_fee": 0.0,
            "minimum_balance": 6000.0,
            "fee_waiver_condition": (
                "Monthly fee 30.95 is waived to 0.00 with a 6000.00 minimum balance."
            ),
        }
        waiver_link = NormalizationEvidenceLink(
            field_name="fee_waiver_condition",
            candidate_value=str(payload["fee_waiver_condition"]),
            evidence_chunk_id="chunk-fee-table",
            evidence_text_excerpt=(
                "Monthly fee $30.95 or $0 with a minimum daily account balance of $6,000."
            ),
            source_document_id="source-fees",
            source_snapshot_id="snapshot-fees",
            citation_confidence=0.82,
            model_execution_id=None,
            anchor_type="section",
            anchor_value="fees",
            page_no=None,
            chunk_index=2,
        )
        metadata = {"monthly_fee": {}, "public_display_fee": {}}
        normalized_values = {"monthly_fee": 0.0, "public_display_fee": 0.0}
        links = [waiver_link]

        _clean_chequing_fee_waiver_consistency(
            product_type_family="chequing",
            candidate_payload=payload,
            field_mapping_metadata=metadata,
            normalized_values_for_links=normalized_values,
            evidence_links_for_output=links,
            runtime_notes=[],
        )

        self.assertEqual(payload["monthly_fee"], 30.95)
        self.assertEqual(payload["public_display_fee"], 30.95)
        self.assertEqual(metadata["monthly_fee"]["normalization_method"], "conditional_zero_base_fee_alignment")
        self.assertEqual(
            {link.field_name for link in links},
            {"fee_waiver_condition", "monthly_fee", "public_display_fee"},
        )

    def test_fee_waiver_threshold_repairs_zero_balance_and_audience_copy_does_not_tag_product(self) -> None:
        payload: dict[str, object] = {
            "product_name": "CIBC Smart Account",
            "monthly_fee": 16.95,
            "minimum_balance": 0.0,
            "fee_waiver_condition": (
                "Monthly fee 16.95 is waived to 0.00 with a 4000.00 minimum balance."
            ),
            "eligibility_text": "Students and newcomers can receive separate account benefits.",
        }
        normalized_values = {"minimum_balance": 0.0}
        metadata = {"minimum_balance": {}}
        notes: list[str] = []

        _align_minimum_balance_to_fee_waiver(
            product_type_family="chequing",
            candidate_payload=payload,
            field_mapping_metadata=metadata,
            normalized_values_for_links=normalized_values,
            evidence_links_for_output=[],
            runtime_notes=notes,
        )

        self.assertEqual(payload["minimum_balance"], 4000.0)
        self.assertEqual(normalized_values["minimum_balance"], 4000.0)
        self.assertEqual(_infer_target_customer_tags(payload), [])
        self.assertTrue(
            _looks_like_non_value_eligibility(
                field_name="eligibility_text",
                value="Skilled trades Take advantage of offers and perks for eligible tradespeople",
            )
        )
        self.assertTrue(
            _looks_like_non_value_eligibility(
                field_name="eligibility_text",
                value="Qualifying actions apply",
            )
        )
        for non_eligibility in (
            "Give us a call Eligible for CDIC Insurance 1 Regular Interest is calculated daily",
            "How to apply Talk to an advisor",
            (
                "Open a Money Master Savings Account and/or a new eligible Credit Card Account "
                "and complete certain qualifying transactions/conditions"
            ),
            "Open a No Fee Chequing Account and set up an eligible direct deposit of $100 for 3 straight months",
        ):
            with self.subTest(non_eligibility=non_eligibility):
                self.assertTrue(
                    _looks_like_non_value_eligibility(
                        field_name="eligibility_text",
                        value=non_eligibility,
                    )
                )

        payload = {
            "description_short": (
                "Accounts No Fee Chequing Account Accounts No Fee Chequing Account Welcome Offer"
            )
        }
        _clean_product_context_fields(product_type_family="chequing", candidate_payload=payload)
        self.assertEqual(payload, {})
        for breadcrumb in (
            "Accounts High Interest Savings Account Accounts Savings Account",
            "Accounts Simplii Financial USD Savings Account Accounts Simplii Financial USD Savings Account",
        ):
            payload = {"description_short": breadcrumb}
            _clean_product_context_fields(product_type_family="savings", candidate_payload=payload)
            self.assertEqual(payload, {})

    def test_advertised_promotional_total_outranks_additive_components(self) -> None:
        total_link = NormalizationEvidenceLink(
            field_name="interest_rate_summary",
            candidate_value="Earn up to 5.00% for the first 3 months.",
            evidence_chunk_id="chunk-total",
            evidence_text_excerpt=(
                "Scotia High Interest Savings Account. Special offer. "
                "You can earn up to 5.00% for the first 3 months."
            ),
            source_document_id="source-hisa",
            source_snapshot_id="snapshot-hisa",
            citation_confidence=0.92,
            model_execution_id=None,
            anchor_type="heading",
            anchor_value="Special offer",
            page_no=None,
            chunk_index=1,
        )
        component_link = NormalizationEvidenceLink(
            field_name="promotional_rate",
            candidate_value="2.8",
            evidence_chunk_id="chunk-components",
            evidence_text_excerpt=(
                "For the first 3 months you'll earn both the Promotional rate of 2.80% "
                "and Regular interest rate of up to 2.20%."
            ),
            source_document_id="source-hisa",
            source_snapshot_id="snapshot-hisa",
            citation_confidence=0.9,
            model_execution_id=None,
            anchor_type="section",
            anchor_value="About the offer",
            page_no=None,
            chunk_index=2,
        )
        payload: dict[str, object] = {"promotional_rate": 2.8, "public_display_rate": 2.8}
        links = [total_link, component_link]

        _align_advertised_promotional_total(
            product_type_family="savings",
            candidate_payload=payload,
            field_mapping_metadata={},
            normalized_values_for_links={},
            evidence_links_for_output=links,
            runtime_notes=[],
        )

        self.assertEqual(payload["standard_rate"], 2.2)
        self.assertEqual(payload["promotional_rate"], 5.0)
        self.assertEqual(payload["public_display_rate"], 5.0)
        linked = {link.field_name: link for link in links}
        self.assertEqual(linked["standard_rate"].evidence_chunk_id, "chunk-components")
        self.assertEqual(linked["promotional_rate"].evidence_chunk_id, "chunk-total")
        self.assertEqual(linked["public_display_rate"].evidence_chunk_id, "chunk-total")

    def test_additive_promotional_components_form_grounded_total_without_total_copy(self) -> None:
        component_link = NormalizationEvidenceLink(
            field_name="promotional_rate",
            candidate_value="2.80",
            evidence_chunk_id="chunk-components-only",
            evidence_text_excerpt=(
                "For the first 3 months you'll earn both the Promotional rate of 2.80% "
                "and Regular interest rate of up to 2.20%. The promo rate is on top of the regular rate."
            ),
            source_document_id="source-hisa",
            source_snapshot_id="snapshot-hisa",
            citation_confidence=0.93,
            model_execution_id=None,
            anchor_type="section",
            anchor_value="About the offer",
            page_no=None,
            chunk_index=2,
        )
        payload: dict[str, object] = {"standard_rate": 2.2, "promotional_rate": 2.8, "public_display_rate": 2.8}
        links = [component_link]

        _align_advertised_promotional_total(
            product_type_family="savings",
            candidate_payload=payload,
            field_mapping_metadata={},
            normalized_values_for_links={},
            evidence_links_for_output=links,
            runtime_notes=[],
        )

        self.assertEqual(payload["standard_rate"], 2.2)
        self.assertEqual(payload["promotional_rate"], 5.0)
        self.assertEqual(payload["public_display_rate"], 5.0)

    def test_promotional_total_does_not_remain_as_savings_standard_rate(self) -> None:
        promotional_link = NormalizationEvidenceLink(
            field_name="promotional_rate",
            candidate_value="4.75",
            evidence_chunk_id="chunk-promotional-only",
            evidence_text_excerpt="Limited time offer. Earn up to 4.75% for the first 3 months.",
            source_document_id="source-promotional-only",
            source_snapshot_id="snapshot-promotional-only",
            citation_confidence=0.94,
            model_execution_id=None,
            anchor_type="heading",
            anchor_value="Limited time offer",
            page_no=None,
            chunk_index=1,
        )
        standard_link = replace(promotional_link, field_name="standard_rate")
        payload: dict[str, object] = {
            "standard_rate": 4.75,
            "promotional_rate": 4.75,
            "public_display_rate": 4.75,
        }
        normalized_values = dict(payload)
        mapping = {"standard_rate": {"normalized_value": 4.75}}
        links = [standard_link, promotional_link]

        _align_advertised_promotional_total(
            product_type_family="savings",
            candidate_payload=payload,
            field_mapping_metadata=mapping,
            normalized_values_for_links=normalized_values,
            evidence_links_for_output=links,
            runtime_notes=[],
        )

        self.assertNotIn("standard_rate", payload)
        self.assertNotIn("standard_rate", normalized_values)
        self.assertNotIn("standard_rate", {link.field_name for link in links})
        self.assertEqual(mapping["standard_rate"]["suppressed_reason"], "promotional_rate_not_ongoing_rate")

    def test_savings_customer_copy_cleanup_keeps_only_explicit_withdrawal_charge(self) -> None:
        payload: dict[str, object] = {
            "deposit_insurance": (
                "More account information Summary of account fees Savings account interest rates "
                "Canada Deposit Insurance Corporation Regulatory information"
            ),
            "notes": "For alternate solutions to help you with everyday banking, ask us or visit our website.",
            "withdrawal_limit_text": (
                "benefits No monthly account fees No-fee transfers Earn interest on every dollar "
                "Access money anytime - $5 service charge per debit transaction"
            ),
        }

        _clean_product_context_fields(product_type_family="savings", candidate_payload=payload)

        self.assertEqual(payload, {"withdrawal_limit_text": "$5 service charge per debit transaction."})

    def test_repeated_application_cta_is_reduced_to_channel_and_phone(self) -> None:
        payload: dict[str, object] = {
            "application_method": (
                "Apply by signing on to online banking or calling us at 1-888-723-8881 Opens your phone app. "
                "Apply by signing on to online banking or calling us at Opens your phone app. Sign on"
            )
        }

        _clean_product_context_fields(product_type_family="gic", candidate_payload=payload)

        self.assertEqual(
            payload["application_method"],
            "Apply by signing on to online banking or calling us at 1-888-723-8881.",
        )

    def test_promotional_rate_uses_registered_or_non_registered_labeled_value(self) -> None:
        evidence = (
            "The 4.60% Registered Promotional Rate will apply to Applicable Registered Savings Accounts "
            "for 153 days (5 months). The 4.50% Non-Registered Promotional Rate will apply to Eligible "
            "Savings Accounts for 153 days (5 months)."
        )
        for product_name, expected in (
            ("RIF Savings Account", 4.6),
            ("RSP Savings Account", 4.6),
            ("Savings Account", 4.5),
            ("U.S. Dollar Savings Account", 4.5),
        ):
            with self.subTest(product_name=product_name):
                link = NormalizationEvidenceLink(
                    field_name="promotional_rate",
                    candidate_value="4.6",
                    evidence_chunk_id="chunk-two-rates",
                    evidence_text_excerpt=evidence,
                    source_document_id="source-savings",
                    source_snapshot_id="snapshot-savings",
                    citation_confidence=0.9,
                    model_execution_id=None,
                    anchor_type="section",
                    anchor_value="Legal Stuff",
                    page_no=None,
                    chunk_index=5,
                )
                payload: dict[str, object] = {
                    "product_name": product_name,
                    "promotional_rate": 4.6,
                    "public_display_rate": 4.6,
                }
                links = [link]

                _align_advertised_promotional_total(
                    product_type_family="savings",
                    candidate_payload=payload,
                    field_mapping_metadata={},
                    normalized_values_for_links={},
                    evidence_links_for_output=links,
                    runtime_notes=[],
                )

                self.assertEqual(payload["promotional_rate"], expected)
                self.assertEqual(payload["public_display_rate"], expected)

    def test_savings_welcome_offer_is_not_a_term_rate_table(self) -> None:
        field = NormalizationExtractedField(
            field_name="term_rate_table",
            candidate_value=[{"term_label": "3 months", "term_length_days": 90, "rate": 2.8}],
            value_type="json",
            confidence=0.9,
            extraction_method="heuristic",
            source_document_id="source-hisa",
            source_snapshot_id="snapshot-hisa",
            evidence_chunk_id="chunk-components",
            evidence_text_excerpt=(
                "Earn 4.50% for 5 months. New Client offer terms apply."
            ),
            anchor_type="section",
            anchor_value="Offer",
            page_no=None,
            chunk_index=2,
            field_metadata={},
        )

        self.assertEqual(
            _rate_field_suppression_reason(
                field_name="term_rate_table",
                field=field,
                product_type_family="savings",
            ),
            "savings_promotional_period_not_term_rate",
        )

    def test_prime_margin_is_not_normalized_as_complete_lending_rate(self) -> None:
        field = NormalizationExtractedField(
            field_name="interest_rate",
            candidate_value="1.0",
            value_type="decimal",
            confidence=0.9,
            extraction_method="ai_schema",
            source_document_id="source-loc",
            source_snapshot_id="snapshot-loc",
            evidence_chunk_id="chunk-loc-rate",
            evidence_text_excerpt="A lower interest rate of Prime + 1%.",
            anchor_type="section",
            anchor_value="rates",
            page_no=None,
            chunk_index=2,
            field_metadata={},
        )

        self.assertEqual(
            _rate_field_suppression_reason(
                field_name="interest_rate",
                field=field,
                product_type_family=None,
            ),
            "reference_rate_margin_not_total_rate",
        )

    def test_product_context_cleanup_suppresses_navigation_and_marketing_rate_copy(self) -> None:
        payload: dict[str, object] = {
            "product_name": "Example Mortgage",
            "description_short": "Go to main content",
            "summary_text": "Home",
            "eligibility_text": "And we understand that you sometimes need to make adjustments",
            "application_method": (
                "Main navigation Online banking Find an ATM Find a branch About us Contact us "
                "Credit cards Chequing accounts Savings accounts Personal loans Mortgages Calculators "
                "Apply online after reviewing the product details."
            ),
            "mortgage_rate": "Competitive mortgage rates help you choose a solution that suits your financial goals.",
            "deposit_insurance": (
                "FAQs Automated property valuation Calculators Mortgage loan calculator Get Started Mortgage rates "
                "Workflows Find your BDM Tools and Support Advisor Access Marketing material."
            ),
            "post_maturity_interest_rate": (
                "Interest payments can be deposited into a Canadian bank account. For terms of 2 to 5 years, "
                "interest is compounded and paid at maturity, and payments can be sent to the client or advisor."
            ),
            "prepayment_privileges": "Prepay up to 20% of the original principal each year.",
            "secured_flag": "Unsecured or secured variants are available.",
            "credit_limit_text": "Your limit is RDS%rate_placeholder% and subject to approval.",
            "term_length_text": "Terms from 12 months to 96 months.",
            "term_length_days": 30,
            "fees_text": "A broad product page section " + "with repeated marketing details " * 8,
            "minimum_payment_text": "A broad product page section " + "with repeated marketing details " * 8,
            "withdrawal_limit_text": (
                "The smart way to save with automatic contributions, one free withdrawal a month and easy access."
            ),
        }
        normalized_values = dict(payload)
        mapping_metadata = {field_name: {"normalized_value": value} for field_name, value in payload.items()}
        notes: list[str] = []

        _clean_product_context_fields(
            product_type_family=None,
            candidate_payload=payload,
            normalized_values_for_links=normalized_values,
            field_mapping_metadata=mapping_metadata,
            runtime_notes=notes,
        )

        self.assertNotIn("description_short", payload)
        self.assertNotIn("summary_text", payload)
        self.assertNotIn("application_method", payload)
        self.assertNotIn("mortgage_rate", payload)
        self.assertNotIn("deposit_insurance", payload)
        self.assertNotIn("post_maturity_interest_rate", payload)
        self.assertNotIn("eligibility_text", payload)
        self.assertEqual(payload["withdrawal_limit_text"], "One free withdrawal a month.")
        self.assertEqual(normalized_values["withdrawal_limit_text"], "One free withdrawal a month.")
        self.assertEqual(payload["prepayment_privileges"], "Prepay up to 20% of the original principal each year.")
        self.assertNotIn("secured_flag", payload)
        self.assertNotIn("credit_limit_text", payload)
        self.assertNotIn("term_length_days", payload)
        self.assertNotIn("fees_text", payload)
        self.assertNotIn("minimum_payment_text", payload)
        self.assertNotIn("mortgage_rate", normalized_values)
        self.assertNotIn("application_method", mapping_metadata)
        self.assertIn("ungrounded", notes[0])

    def test_gic_context_cleanup_suppresses_cross_product_account_application(self) -> None:
        payload: dict[str, object] = {
            "product_name": "Example GIC",
            "application_method": "Apply for a bank account. You must be registered for Online Banking. Need to register?",
        }
        normalized_values = dict(payload)
        mapping_metadata = {field_name: {"normalized_value": value} for field_name, value in payload.items()}

        _clean_product_context_fields(
            product_type_family="gic",
            candidate_payload=payload,
            normalized_values_for_links=normalized_values,
            field_mapping_metadata=mapping_metadata,
        )

        self.assertNotIn("application_method", payload)
        self.assertNotIn("application_method", normalized_values)
        self.assertNotIn("application_method", mapping_metadata)

    def test_chequing_cleanup_rejects_compare_label_expired_offer_and_comparison_table_as_copy(self) -> None:
        payload: dict[str, object] = {
            "description_short": "Compare Account",
            "application_method": (
                "Monthly fee $0 Transactions included per month Unlimited Interest calculated on Every dollar "
                "Paper or Online Statement Free Secure Open account Compare Account"
            ),
        }
        _clean_product_context_fields(product_type_family="chequing", candidate_payload=payload)
        self.assertEqual(payload, {})

        expired = {
            "description_short": (
                "The Student Banking Package is extended until June 29, 2026 and no longer requires auto-deposit."
            )
        }
        _clean_product_context_fields(product_type_family="chequing", candidate_payload=expired)
        self.assertEqual(expired, {})

    def test_multi_term_gic_cleanup_rejects_sibling_audience_and_single_term_scalar(self) -> None:
        payload: dict[str, object] = {
            "product_name": "Guaranteed Investment Certificates (GIC)",
            "eligibility_text": "Arrive in Canada and meet visa requirements",
            "application_method": (
                "Interest rates GIC/RGIC term Rate (%) APY (%) 1 year 2.90% 2 year 3.00% "
                "3 year 3.20% Resources Sign on About our GICs About our registered GICs Legal "
                "How to apply for this account Apply by signing on to online banking"
            ),
            "term_length_days": 365,
            "term_length_text": "1 year",
            "term_rate_table": [
                {"term_label": "1 year", "term_length_days": 365, "rate": 2.9},
                {"term_label": "2 years", "term_length_days": 730, "rate": 3.0},
            ],
        }

        _clean_product_context_fields(product_type_family="gic", candidate_payload=payload)

        self.assertNotIn("eligibility_text", payload)
        self.assertNotIn("application_method", payload)
        self.assertNotIn("term_length_days", payload)
        self.assertNotIn("term_length_text", payload)
        self.assertEqual(len(payload["term_rate_table"]), 2)

        student_payload = {
            "product_name": "International Student GIC Program",
            "eligibility_text": "Arrive in Canada and meet visa requirements",
        }
        _clean_product_context_fields(product_type_family="gic", candidate_payload=student_payload)
        self.assertIn("eligibility_text", student_payload)

    def test_gic_cleanup_rejects_transaction_account_fields_fragments_and_sibling_tax_copy(self) -> None:
        payload: dict[str, object] = {
            "product_name": "RSP Guaranteed Investment",
            "monthly_fee": 0,
            "public_display_fee": 0,
            "withdrawal_limit_text": "Unlimited withdrawals",
            "description_short": "(GIC)",
            "tax_benefits": "Earn tax-free interest in a TFSA without paying tax on withdrawals.",
        }

        _clean_product_context_fields(product_type_family="gic", candidate_payload=payload)

        self.assertEqual(
            payload,
            {
                "product_name": "RSP Guaranteed Investment",
                "monthly_fee": 0,
                "public_display_fee": 0,
            },
        )

        truncated = {"description_short": "Grow your savings safely and predictably. With a"}
        _clean_product_context_fields(product_type_family="gic", candidate_payload=truncated)
        self.assertEqual(truncated, {})

        savings_noise = {
            "product_name": "RIF Savings Account",
            "eligibility_text": "The Offer is only applicable where the eligible new Client is the Primary Account Holder.",
            "tax_benefits": "Try a 4.60% promotional rate boost for five months.",
            "deposit_insurance": "Contact us ABM locator Rates Careers Community Get our app Example Bank is a CDIC member.",
        }
        _clean_product_context_fields(product_type_family="savings", candidate_payload=savings_noise)
        self.assertEqual(savings_noise, {"product_name": "RIF Savings Account"})

    def test_duplicate_marketing_copy_is_kept_only_as_description(self) -> None:
        sentence = (
            "Get a savings account that offers tiered interest rates for higher balances and helps you earn more as you save."
        )
        payload = {
            "description_short": sentence,
            "eligibility_text": sentence,
            "tier_definition_text": sentence + ".",
        }

        _clean_product_context_fields(product_type_family="savings", candidate_payload=payload)

        self.assertEqual(payload, {"description_short": sentence})

    def test_savings_description_cleanup_suppresses_offer_copy_and_trims_cross_sell(self) -> None:
        offer_only = {
            "product_name": "High Interest Savings Account",
            "description_short": (
                "New to Example Bank? Open a savings account and get this special interest rate for 5 months. "
                "Already a client? You can still get this offer during your first 60 days."
            ),
        }
        _clean_product_context_fields(product_type_family="savings", candidate_payload=offer_only)
        self.assertNotIn("description_short", offer_only)

        limitation = (
            "You can't make cash deposits or withdrawals, and there is no ATM or point-of-sale access. "
            "Try our No Fee Chequing Account for day-to-day banking."
        )
        payload = {"product_name": "USD Savings Account", "description_short": limitation}
        normalized_values = dict(payload)
        mapping_metadata = {"description_short": {"normalized_value": limitation}}
        notes: list[str] = []

        _clean_product_context_fields(
            product_type_family="savings",
            candidate_payload=payload,
            normalized_values_for_links=normalized_values,
            field_mapping_metadata=mapping_metadata,
            runtime_notes=notes,
        )

        expected = "You can't make cash deposits or withdrawals, and there is no ATM or point-of-sale access."
        self.assertEqual(payload["description_short"], expected)
        self.assertEqual(normalized_values["description_short"], expected)
        self.assertEqual(mapping_metadata["description_short"]["normalization_method"], "cross_product_description_cleanup")
        self.assertIn("cross-product", " ".join(notes))

    def test_savings_cleanup_rejects_application_faq_description_and_compacts_online_channel(self) -> None:
        description = (
            "Yes, you can. If you’re an existing bank customer, you can sign in to Online Banking "
            "to add the Premium Savings Account."
        )
        application = (
            "Open an account online If you already have a chequing account, you can apply for an "
            "account online in as little as 7 minutes."
        )
        payload: dict[str, object] = {
            "product_name": "Premium Savings Account",
            "description_short": description,
            "application_method": application,
        }

        _clean_product_context_fields(product_type_family="savings", candidate_payload=payload)

        self.assertNotIn("description_short", payload)
        self.assertEqual(payload["application_method"], "Online.")

    def test_application_channel_cleanup_recognizes_online_and_banking_centre(self) -> None:
        payload = {
            "application_method": "How to open an account: Online or at a CIBC Banking Centre Opens a new window."
        }

        _clean_product_context_fields(product_type_family="chequing", candidate_payload=payload)

        self.assertEqual(payload["application_method"], "Online or at a branch.")

    def test_application_channel_cleanup_compacts_short_single_channel_ctas(self) -> None:
        online_payload = {
            "application_method": "Open an account online Apply for an account online in as little as 7 minutes."
        }
        branch_payload = {
            "application_method": "You can also apply for the account in person at your nearest branch."
        }

        _clean_product_context_fields(product_type_family="chequing", candidate_payload=online_payload)
        _clean_product_context_fields(product_type_family="chequing", candidate_payload=branch_payload)

        self.assertEqual(online_payload["application_method"], "Online.")
        self.assertEqual(branch_payload["application_method"], "At a branch.")

    def test_plan_dependent_account_fee_is_not_normalized_as_zero(self) -> None:
        payload: dict[str, object] = {
            "product_name": "Premium Savings Account",
            "monthly_fee": 0.0,
            "public_display_fee": 0.0,
        }
        evidence = (
            "What are the fees for the Premium Savings Account? This will depend on the bank Plan "
            "for the paired chequing account. What type of savings accounts does the bank offer? "
            "Basic Savings has no monthly fees."
        )

        _clean_product_context_fields(
            product_type_family="savings",
            candidate_payload=payload,
            evidence_context_by_field={"monthly_fee": evidence, "public_display_fee": evidence},
        )

        self.assertEqual(payload, {"product_name": "Premium Savings Account"})

    def test_savings_cleanup_rejects_hard_limit_truncated_description(self) -> None:
        payload = {
            "product_name": "Builder Savings Account",
            "description_short": (
                "Get a bonus interest rate for adding funds every month and enjoy one eligible debit transaction "
                "at no cost while using transfers to another account and several other account features that are "
                "flattened from a comparison card before the parser cuts the final Intera"
            ),
        }

        _clean_product_context_fields(product_type_family="savings", candidate_payload=payload)

        self.assertEqual(payload, {"product_name": "Builder Savings Account"})

    def test_promotional_period_is_recovered_only_from_rate_linked_evidence(self) -> None:
        evidence = NormalizationEvidenceLink(
            field_name="promotional_rate",
            candidate_value="4.6",
            evidence_chunk_id="chunk-promo",
            evidence_text_excerpt=(
                "Earn 4.60% interest on eligible deposits. Open an account and get this special interest rate "
                "for 5 months. Existing clients qualify only in their first 60 days."
            ),
            source_document_id="source-promo",
            source_snapshot_id="snapshot-promo",
            citation_confidence=0.9,
            model_execution_id="model-promo",
            anchor_type="section",
            anchor_value="welcome-offer",
            page_no=None,
            chunk_index=3,
        )
        payload: dict[str, object] = {"promotional_rate": 4.6}
        normalized_values = dict(payload)
        mapping_metadata: dict[str, object] = {}
        links = [evidence]
        notes: list[str] = []

        _align_promotional_period_from_evidence(
            candidate_payload=payload,
            field_mapping_metadata=mapping_metadata,
            normalized_values_for_links=normalized_values,
            evidence_links_for_output=links,
            runtime_notes=notes,
        )

        self.assertEqual(payload["promotional_period_text"], "5 months")
        self.assertIs(payload["introductory_rate_flag"], True)
        self.assertEqual(normalized_values["promotional_period_text"], "5 months")
        self.assertEqual(mapping_metadata["promotional_period_text"]["evidence_chunk_id"], "chunk-promo")
        self.assertEqual(
            {link.field_name for link in links},
            {"promotional_rate", "promotional_period_text", "introductory_rate_flag"},
        )

    def test_lending_cleanup_suppresses_adjacent_ctas_slogans_and_offer_end_dates(self) -> None:
        cases = (
            (
                "line-of-credit",
                {"application_method": "Steps to follow Apply online with the Ministère."},
                {"application_method": "government-guaranteed-student-loans Student aid office Steps to follow"},
            ),
            (
                "mortgage",
                {"application_method": "You're in business now. Open an account online."},
                {"application_method": "Business accounts Open an account online"},
            ),
            (
                "personal-loan",
                {
                    "application_method": "Car loans Apply for a car loan online.",
                    "security_requirement": "Car loans Hit the road with hassle-free financing",
                    "monthly_payment_text": "Pay less interest with a variable rate adjusted monthly.",
                    "fees_text": "We'll donate $25 to a conservation charity.",
                    "effective_date": "2026-11-04",
                },
                {
                    "application_method": "Car loans Apply online",
                    "security_requirement": "Car loans Hit the road with hassle-free financing",
                    "monthly_payment_text": "Variable interest rate adjusted monthly",
                    "fees_text": "Donate $25 to a conservation charity",
                    "effective_date": "Offer valid until November 4, 2026",
                },
            ),
        )

        for product_type_family, payload, contexts in cases:
            with self.subTest(product_type_family=product_type_family):
                _clean_product_context_fields(
                    product_type_family=product_type_family,
                    candidate_payload=payload,
                    evidence_context_by_field=contexts,
                )
                self.assertEqual(payload, {})

    def test_gic_cleanup_suppresses_rate_card_eligibility_and_multi_option_scalars(self) -> None:
        payload: dict[str, object] = {
            "eligibility_text": "3.65% 2-Year GIC Eligible for CDIC coverage",
            "compounding_frequency": "annually",
            "payout_option": "at_maturity",
        }
        option_context = "Interest may be paid monthly, semi-annually, annually or at maturity."

        _clean_product_context_fields(
            product_type_family="gic",
            candidate_payload=payload,
            evidence_context_by_field={
                "eligibility_text": "2-Year GIC rate card eligible for CDIC coverage",
                "compounding_frequency": option_context,
                "payout_option": option_context,
            },
        )

        self.assertEqual(payload, {})

    def test_term_days_must_match_a_declared_range_boundary(self) -> None:
        payload: dict[str, object] = {
            "term_length_text": "12-month minimum, up to 96 months",
            "term_length_days": 96,
        }

        _clean_product_context_fields(product_type_family="personal-loan", candidate_payload=payload)

        self.assertEqual(payload, {"term_length_text": "12-month minimum, up to 96 months"})

    def test_savings_cleanup_suppresses_navigation_and_other_product_section_fields(self) -> None:
        payload: dict[str, object] = {
            "product_name": "Example High Interest Savings Account",
            "description_short": "Go to page content",
            "standard_rate": 0.55,
            "tiered_rate_flag": True,
            "tier_definition_text": "Cash Advantage Solution tiers apply.",
        }
        normalized_values = dict(payload)
        mapping_metadata = {field_name: {"normalized_value": value} for field_name, value in payload.items()}

        _clean_product_context_fields(
            product_type_family="savings",
            candidate_payload=payload,
            normalized_values_for_links=normalized_values,
            field_mapping_metadata=mapping_metadata,
            evidence_context_by_field={
                "tiered_rate_flag": "our-other-investment-products Cash Advantage Solution tiers",
                "tier_definition_text": "our-other-investment-products Cash Advantage Solution tiers",
            },
        )

        self.assertEqual(
            payload,
            {"product_name": "Example High Interest Savings Account", "standard_rate": 0.55},
        )
        self.assertNotIn("tiered_rate_flag", normalized_values)
        self.assertNotIn("tier_definition_text", mapping_metadata)

    def test_credit_card_cleanup_rejects_secondary_fee_unlabeled_rate_and_offer_eligibility(self) -> None:
        payload: dict[str, object] = {
            "product_name": "Example Low Rate Mastercard",
            "annual_fee": 0.0,
            "purchase_interest_rate": 22.49,
            "rewards_summary": "Up to $900 in travel discounts.",
            "eligibility_text": (
                "Minimum annual income: $80,000. Subject to credit approval. "
                "To take advantage, you must not currently hold, or have held this card in the past 24 months."
            ),
        }
        contexts = {
            "annual_fee": "Annual fee ${price} Annual fee for the authorized cardholder $0",
            "purchase_interest_rate": "Annual interest rate example $500 $3,000 22.49% 20.99%",
            "rewards_summary": "Our lowest rate card helps you pay off your balance faster. Travel discount banner.",
        }

        _clean_product_context_fields(
            product_type_family="credit-card",
            candidate_payload=payload,
            evidence_context_by_field=contexts,
        )

        self.assertNotIn("annual_fee", payload)
        self.assertNotIn("purchase_interest_rate", payload)
        self.assertNotIn("rewards_summary", payload)
        self.assertEqual(
            payload["eligibility_text"],
            "Minimum annual income: $80,000. Subject to credit approval.",
        )

    def test_credit_card_fallback_uses_only_fixed_rates_adjacent_to_labels(self) -> None:
        excerpt = (
            "Annual fee for the cardholder $0 first year, $70/year thereafter. "
            "Purchase rate 20.99%. Balance transfers and cash advances 22.49%."
        )
        source_link = NormalizationEvidenceLink(
            field_name="annual_fee",
            candidate_value="70",
            evidence_chunk_id="chunk-card",
            evidence_text_excerpt=excerpt,
            source_document_id="source-card",
            source_snapshot_id="snapshot-card",
            citation_confidence=0.92,
            model_execution_id="model-card",
            anchor_type="section",
            anchor_value="card-at-a-glance",
            page_no=None,
            chunk_index=1,
        )
        payload: dict[str, object] = {"product_name": "Example Platinum Mastercard", "annual_fee": 70.0}
        normalized_values = dict(payload)
        mapping_metadata: dict[str, object] = {}
        evidence_links = [source_link]

        _apply_credit_card_labeled_fallback(
            product_type_family="credit-card",
            candidate_payload=payload,
            field_mapping_metadata=mapping_metadata,
            normalized_values_for_links=normalized_values,
            evidence_links_for_output=evidence_links,
            runtime_notes=[],
        )

        self.assertEqual(payload["purchase_interest_rate"], 20.99)
        self.assertEqual(payload["balance_transfer_rate"], 22.49)
        self.assertEqual(payload["cash_advance_rate"], 22.49)
        self.assertEqual(len(evidence_links), 4)

    def test_credit_card_fallback_accepts_cash_interest_rate_label(self) -> None:
        excerpt = "Purchase interest rate 21.75%. Cash interest rate 22.49% (21.99% for Quebec residents)."
        source_link = NormalizationEvidenceLink(
            field_name="product_name",
            candidate_value="Example Cashback Mastercard",
            evidence_chunk_id="chunk-card-rates",
            evidence_text_excerpt=excerpt,
            source_document_id="source-card",
            source_snapshot_id="snapshot-card",
            citation_confidence=0.96,
            model_execution_id="model-card",
            anchor_type="section",
            anchor_value="card-at-a-glance",
            page_no=1,
            chunk_index=0,
        )
        payload: dict[str, object] = {"product_name": "Example Cashback Mastercard"}
        normalized_values = dict(payload)
        mapping_metadata: dict[str, object] = {}
        evidence_links = [source_link]

        _apply_credit_card_labeled_fallback(
            product_type_family="credit-card",
            candidate_payload=payload,
            field_mapping_metadata=mapping_metadata,
            normalized_values_for_links=normalized_values,
            evidence_links_for_output=evidence_links,
            runtime_notes=[],
        )

        self.assertEqual(payload["purchase_interest_rate"], 21.75)
        self.assertEqual(payload["cash_advance_rate"], 22.49)

    def test_lending_cleanup_rejects_rate_and_term_fields_from_unrelated_context(self) -> None:
        payload: dict[str, object] = {
            "product_name": "Example Mortgage",
            "mortgage_rate": 20.0,
            "payment_frequency": (
                "Mortgage payment calculator Find out how changing your payment frequency and making prepayments can save you money."
            ),
            "amortization_text": (
                "Document Mortgages Manage My Mortgage Fixed Rate Mortgages Variable Rate Mortgages Mortgage Calculators"
            ),
            "eligibility_text": "Home equity calculator Calculate how much you may qualify to borrow through a mortgage.",
            "prepayment_privileges": "What flexible payment and prepayment options do I have? " + "Payment options and marketing copy. " * 8,
        }
        normalized_values = dict(payload)
        mapping_metadata = {field_name: {"normalized_value": value} for field_name, value in payload.items()}

        _clean_product_context_fields(
            product_type_family="mortgage",
            candidate_payload=payload,
            normalized_values_for_links=normalized_values,
            field_mapping_metadata=mapping_metadata,
            evidence_context_by_field={
                "mortgage_rate": "Pre-payment privileges of up to 20% of the original mortgage amount annually."
            },
        )

        self.assertEqual(payload, {"product_name": "Example Mortgage"})
        self.assertNotIn("mortgage_rate", normalized_values)

    def test_lending_cleanup_rejects_numeric_rate_derived_from_unresolved_template(self) -> None:
        payload: dict[str, object] = {
            "product_name": "Example Mortgage",
            "mortgage_rate": 5.25,
        }

        _clean_product_context_fields(
            product_type_family="mortgage",
            candidate_payload=payload,
            evidence_context_by_field={
                "mortgage_rate": "RDS%rate[5].5YRVARCLO.Published(3_null_null_Years_T,null,18,null)(#O2#)%"
            },
        )

        self.assertEqual(payload, {"product_name": "Example Mortgage"})

    def test_lending_cleanup_keeps_concise_supported_term_fields(self) -> None:
        payload: dict[str, object] = {
            "product_name": "Example Mortgage",
            "payment_frequency": "Monthly or accelerated bi-weekly",
            "amortization_text": "Up to 30 years",
            "eligibility_text": "Applicants must have at least 20% equity and qualifying income.",
        }

        _clean_product_context_fields(product_type_family="mortgage", candidate_payload=payload)

        self.assertEqual(payload["payment_frequency"], "Monthly or accelerated bi-weekly")
        self.assertEqual(payload["amortization_text"], "Up to 30 years")
        self.assertIn("must have at least 20% equity", str(payload["eligibility_text"]))

    def test_lending_cleanup_suppresses_cross_product_and_non_value_fields(self) -> None:
        payload: dict[str, object] = {
            "product_name": "Example Personal Loan",
            "fees_text": "Monthly fees Free",
            "monthly_payment_text": "Monthly fees Free",
            "loan_amount_text": "Home renovations can make your space work better for your family and help you plan for future projects.",
            "security_requirement": "Document Rates Contact us Search Login Go to homepage",
            "prepayment_privileges": "CHIP Reverse Mortgage",
            "collateral_text": "What collateral is required",
            "application_method": "Open a bank account online",
            "monthly_payment_text": "Calculate your payment",
        }
        normalized_values = dict(payload)
        mapping_metadata = {field_name: {"normalized_value": value} for field_name, value in payload.items()}

        _clean_product_context_fields(
            product_type_family="personal-loan",
            candidate_payload=payload,
            normalized_values_for_links=normalized_values,
            field_mapping_metadata=mapping_metadata,
        )

        self.assertEqual(payload, {"product_name": "Example Personal Loan"})
        self.assertEqual(normalized_values, {"product_name": "Example Personal Loan"})
        self.assertEqual(mapping_metadata, {"product_name": {"normalized_value": "Example Personal Loan"}})

    def test_line_of_credit_cleanup_requires_payment_semantics_for_minimum_payment_text(self) -> None:
        payload: dict[str, object] = {
            "product_name": "Example Student Line of Credit",
            "minimum_payment_text": "Student lines of credit",
        }

        _clean_product_context_fields(product_type_family="line-of-credit", candidate_payload=payload)

        self.assertEqual(payload, {"product_name": "Example Student Line of Credit"})

        supported: dict[str, object] = {
            "minimum_payment_text": "Make interest-only payments while you are in school.",
        }
        _clean_product_context_fields(product_type_family="line-of-credit", candidate_payload=supported)
        self.assertEqual(
            supported["minimum_payment_text"],
            "Make interest-only payments while you are in school.",
        )

    def test_normalizes_candidate_and_field_evidence_links(self) -> None:
        temp_path = _prepare_workspace_temp_dir("normalization-service")
        try:
            storage_config = NormalizationStorageConfig(
                driver="filesystem",
                env_prefix="dev",
                normalization_object_prefix="normalized",
                retention_class="hot",
                filesystem_root=str(temp_path),
            )
            service = NormalizationService(
                storage_config=storage_config,
                object_store=build_object_store(storage_config),
            )
            result = service.normalize_inputs(
                run_id="run-001",
                inputs=[_build_input()],
                correlation_id="corr-001",
                request_id="req-001",
            )

            self.assertFalse(result.partial_completion_flag)
            source_result = result.source_results[0]
            self.assertEqual(source_result.normalization_action, "stored")
            self.assertEqual(source_result.validation_status, "pass")
            self.assertGreater(source_result.source_confidence or 0, 0.7)
            candidate = source_result.normalized_candidate_record
            self.assertIsNotNone(candidate)
            self.assertEqual(candidate["product_type"], "savings")
            self.assertEqual(candidate["subtype_code"], "high_interest")
            self.assertEqual(candidate["candidate_payload"]["monthly_fee"], 0.0)
            self.assertEqual(candidate["candidate_payload"]["standard_rate"], 1.25)
            self.assertEqual(candidate["candidate_payload"]["public_display_rate"], 1.25)
            self.assertEqual(len(source_result.field_evidence_link_records), 4)

            normalized_path = temp_path / Path(str(source_result.normalized_storage_key).replace("/", "\\"))
            metadata_path = temp_path / Path(str(source_result.metadata_storage_key).replace("/", "\\"))
            self.assertTrue(normalized_path.exists())
            self.assertTrue(metadata_path.exists())
            artifact = json.loads(normalized_path.read_text(encoding="utf-8"))
            self.assertEqual(artifact["normalized_candidate"]["product_name"], "TD ePremium Savings Account")
        finally:
            rmtree(temp_path, ignore_errors=True)

    def test_normalizes_missing_rate_from_rate_summary_evidence(self) -> None:
        temp_path = _prepare_workspace_temp_dir("normalization-rate-fallback")
        try:
            base_input = _build_input()
            extracted_fields = [
                field for field in base_input.extracted_fields if field.field_name != "standard_rate"
            ]
            extracted_fields.append(
                _field(
                    "interest_rate_summary",
                    "RBC Enhanced Savings account Interest Rate 1.600%",
                    "string",
                    0.82,
                    evidence_chunk_id="chunk-rate-summary",
                )
            )
            evidence_links = [
                link for link in base_input.evidence_links if link.field_name != "standard_rate"
            ]
            evidence_links.append(
                NormalizationEvidenceLink(
                    field_name="interest_rate_summary",
                    candidate_value="RBC Enhanced Savings account Interest Rate 1.600%",
                    evidence_chunk_id="chunk-rate-summary",
                    evidence_text_excerpt="RBC Enhanced Savings account Interest Rate 1.600%",
                    source_document_id="src-001",
                    source_snapshot_id="snap-001",
                    citation_confidence=0.82,
                    model_execution_id="modelexec-extract-001",
                    anchor_type="section",
                    anchor_value="savings-rate-table",
                    page_no=None,
                    chunk_index=0,
                )
            )
            item = NormalizationInput(
                **{
                    **base_input.__dict__,
                    "source_id": "AUTO-RBC-SAV-rate",
                    "bank_code": "RBC",
                    "extracted_fields": extracted_fields,
                    "evidence_links": evidence_links,
                }
            )
            storage_config = NormalizationStorageConfig(
                driver="filesystem",
                env_prefix="dev",
                normalization_object_prefix="normalized",
                retention_class="hot",
                filesystem_root=str(temp_path),
            )
            service = NormalizationService(
                storage_config=storage_config,
                object_store=build_object_store(storage_config),
            )
            result = service.normalize_inputs(run_id="run-rate-fallback", inputs=[item])

            source_result = result.source_results[0]
            self.assertEqual(source_result.validation_status, "pass")
            candidate = source_result.normalized_candidate_record
            self.assertIsNotNone(candidate)
            self.assertEqual(candidate["candidate_payload"]["standard_rate"], 1.6)
            self.assertEqual(candidate["candidate_payload"]["public_display_rate"], 1.6)
            linked_fields = {record["field_name"] for record in source_result.field_evidence_link_records}
            self.assertIn("standard_rate", linked_fields)
            self.assertIn("public_display_rate", linked_fields)
        finally:
            rmtree(temp_path, ignore_errors=True)

    def test_suppresses_market_linked_return_cap_as_canonical_rate(self) -> None:
        temp_path = _prepare_workspace_temp_dir("normalization-market-linked-rate-cap")
        try:
            return_cap_excerpt = (
                "Return: The Index Return payable, if any, is based on the performance of the Underlying Index. "
                "Your Scotiabank Market Linked GIC principal is unconditionally guaranteed. "
                "Limitation on interest: by law, the total return you receive cannot exceed an average of "
                "60% per year, regardless of the performance of the Underlying Index."
            )
            base_input = _build_gic_input()
            unsafe_fields: list[NormalizationExtractedField] = []
            for field in base_input.extracted_fields:
                if field.field_name == "product_name":
                    unsafe_fields.append(NormalizationExtractedField(**{**field.__dict__, "candidate_value": "Scotiabank Market Linked GICs"}))
                    continue
                if field.field_name == "standard_rate":
                    unsafe_fields.append(
                        NormalizationExtractedField(
                            **{
                                **field.__dict__,
                                "candidate_value": "60.00",
                                "extraction_method": "heuristic_rate_context_fallback",
                                "evidence_text_excerpt": return_cap_excerpt,
                            }
                        )
                    )
                    unsafe_fields.append(
                        NormalizationExtractedField(
                            **{
                                **field.__dict__,
                                "field_name": "public_display_rate",
                                "candidate_value": "60.00",
                                "extraction_method": "heuristic_rate_context_fallback",
                                "evidence_text_excerpt": return_cap_excerpt,
                            }
                        )
                    )
                    continue
                unsafe_fields.append(field)
            input_item = NormalizationInput(
                **{
                    **base_input.__dict__,
                    "source_id": "AUTO-SCOTIA-GIC-market-linked",
                    "bank_code": "SCOTIA",
                    "source_metadata": {"product_type": "gic"},
                    "extracted_fields": unsafe_fields,
                    "evidence_links": [
                        link for link in base_input.evidence_links if link.field_name != "standard_rate"
                    ]
                    + [
                        NormalizationEvidenceLink(
                            field_name="standard_rate",
                            candidate_value="60.00",
                            evidence_chunk_id="chunk-market-linked-rate-cap",
                            evidence_text_excerpt=return_cap_excerpt,
                            source_document_id="src-001",
                            source_snapshot_id="snap-001",
                            citation_confidence=0.78,
                            model_execution_id="modelexec-extract-001",
                            anchor_type="section",
                            anchor_value="by-phone",
                            page_no=None,
                            chunk_index=16,
                        ),
                        NormalizationEvidenceLink(
                            field_name="public_display_rate",
                            candidate_value="60.00",
                            evidence_chunk_id="chunk-market-linked-rate-cap",
                            evidence_text_excerpt=return_cap_excerpt,
                            source_document_id="src-001",
                            source_snapshot_id="snap-001",
                            citation_confidence=0.78,
                            model_execution_id="modelexec-extract-001",
                            anchor_type="section",
                            anchor_value="by-phone",
                            page_no=None,
                            chunk_index=16,
                        ),
                    ],
                }
            )
            storage_config = NormalizationStorageConfig(
                driver="filesystem",
                env_prefix="dev",
                normalization_object_prefix="normalized",
                retention_class="hot",
                filesystem_root=str(temp_path),
            )
            service = NormalizationService(
                storage_config=storage_config,
                object_store=build_object_store(storage_config),
            )

            result = service.normalize_inputs(run_id="run-market-linked-rate-cap", inputs=[input_item])

            source_result = result.source_results[0]
            candidate = source_result.normalized_candidate_record
            self.assertIsNotNone(candidate)
            payload = candidate["candidate_payload"]
            self.assertNotIn("standard_rate", payload)
            self.assertNotIn("public_display_rate", payload)
            self.assertEqual(source_result.validation_status, "error")
            self.assertIn("required_field_missing", source_result.validation_issue_codes)
            linked_fields = {record["field_name"] for record in source_result.field_evidence_link_records}
            self.assertNotIn("standard_rate", linked_fields)
            self.assertNotIn("public_display_rate", linked_fields)
            self.assertIn("Suppressed `standard_rate`", " ".join(source_result.runtime_notes))
        finally:
            rmtree(temp_path, ignore_errors=True)

    def test_normalizes_chequing_candidate_with_package_subtype_and_flags(self) -> None:
        temp_path = _prepare_workspace_temp_dir("normalization-chequing-service")
        try:
            storage_config = NormalizationStorageConfig(
                driver="filesystem",
                env_prefix="dev",
                normalization_object_prefix="normalized",
                retention_class="hot",
                filesystem_root=str(temp_path),
            )
            service = NormalizationService(
                storage_config=storage_config,
                object_store=build_object_store(storage_config),
            )
            result = service.normalize_inputs(
                run_id="run-chq-001",
                inputs=[_build_chequing_input()],
            )

            source_result = result.source_results[0]
            self.assertEqual(source_result.normalization_action, "stored")
            self.assertEqual(source_result.validation_status, "pass")
            candidate = source_result.normalized_candidate_record
            self.assertIsNotNone(candidate)
            self.assertEqual(candidate["product_type"], "chequing")
            self.assertEqual(candidate["subtype_code"], "package")
            self.assertEqual(candidate["candidate_payload"]["monthly_fee"], 0.0)
            self.assertEqual(candidate["candidate_payload"]["included_transactions"], 25)
            self.assertTrue(candidate["candidate_payload"]["interac_e_transfer_included"])
            self.assertTrue(candidate["candidate_payload"]["student_plan_flag"])
            self.assertTrue(candidate["candidate_payload"]["newcomer_plan_flag"])
            self.assertIn("student", candidate["candidate_payload"]["target_customer_tags"])
            self.assertIn("newcomer", candidate["candidate_payload"]["target_customer_tags"])
            self.assertGreater(source_result.source_confidence or 0, 0.7)
        finally:
            rmtree(temp_path, ignore_errors=True)

    def test_normalizes_performance_chequing_as_package_despite_comparison_table_premium_text(self) -> None:
        temp_path = _prepare_workspace_temp_dir("normalization-performance-chequing")
        try:
            item = NormalizationInput(
                source_id="BMO-CHQ-004",
                source_document_id="src-bmo-chq-performance",
                snapshot_id="snap-bmo-chq-performance",
                parsed_document_id="parsed-bmo-chq-performance",
                extraction_model_execution_id="modelexec-extract-bmo-performance",
                extracted_storage_key="dev/extracted/CA/BMO/src-bmo-chq-performance/parsed-bmo-chq-performance/extracted.json",
                metadata_storage_key="dev/extracted/CA/BMO/src-bmo-chq-performance/parsed-bmo-chq-performance/metadata.json",
                bank_code="BMO",
                country_code="CA",
                source_type="html",
                source_language="en",
                source_metadata={"product_type": "chequing"},
                schema_context={"product_family": "deposit", "product_type": "chequing"},
                extracted_fields=[
                    _field("product_family", "deposit", "string", 0.99),
                    _field("product_type", "chequing", "string", 0.99),
                    _field("country_code", "CA", "string", 0.99),
                    _field("bank_code", "BMO", "string", 0.99),
                    _field("source_language", "en", "string", 0.99),
                    _field("currency", "CAD", "string", 0.99),
                    _field("product_name", "Performance Chequing Account", "string", 0.88),
                    _field("description_short", "Our everyday chequing account for all your banking needs.", "string", 0.7),
                    _field("monthly_fee", "17.95", "decimal", 0.86, evidence_chunk_id="chunk-fee"),
                    _field("public_display_fee", "17.95", "decimal", 0.86, evidence_chunk_id="chunk-fee"),
                    _field("minimum_balance", "4000.00", "decimal", 0.86, evidence_chunk_id="chunk-fee"),
                    _field("fee_waiver_condition", "Monthly fee 17.95 is waived to 0.00 with a 4000.00 minimum balance.", "string", 0.86, evidence_chunk_id="chunk-fee"),
                    _field("unlimited_transactions_flag", True, "boolean", 0.81, evidence_chunk_id="chunk-fee"),
                    _field("interac_e_transfer_included", True, "boolean", 0.81, evidence_chunk_id="chunk-fee"),
                    _field("cheque_book_info", "No fee for select Cheques.", "string", 0.77, evidence_chunk_id="chunk-fee"),
                    _field("notes", "Premium $30.95 OR $0/month with min. $6,000 balance.", "string", 0.7, evidence_chunk_id="chunk-fee"),
                ],
                evidence_links=[
                    _evidence("monthly_fee", "17.95", "chunk-fee"),
                    _evidence("public_display_fee", "17.95", "chunk-fee"),
                    _evidence("minimum_balance", "4000.00", "chunk-fee"),
                    _evidence("fee_waiver_condition", "Monthly fee 17.95 is waived to 0.00 with a 4000.00 minimum balance.", "chunk-fee"),
                    _evidence("unlimited_transactions_flag", "true", "chunk-fee"),
                    _evidence("interac_e_transfer_included", "true", "chunk-fee"),
                    _evidence("cheque_book_info", "No fee for select Cheques.", "chunk-fee"),
                ],
                runtime_notes=[],
            )
            storage_config = NormalizationStorageConfig(
                driver="filesystem",
                env_prefix="dev",
                normalization_object_prefix="normalized",
                retention_class="hot",
                filesystem_root=str(temp_path),
            )
            service = NormalizationService(
                storage_config=storage_config,
                object_store=build_object_store(storage_config),
            )

            result = service.normalize_inputs(
                run_id="run-bmo-performance-chq",
                correlation_id="corr-bmo-performance-chq",
                request_id="req-bmo-performance-chq",
                inputs=[item],
            )

            candidate = result.source_results[0].normalized_candidate_record
            self.assertEqual(candidate["subtype_code"], "package")
            self.assertEqual(candidate["validation_status"], "pass")
            self.assertEqual(candidate["candidate_payload"]["monthly_fee"], 17.95)
            self.assertEqual(candidate["candidate_payload"]["minimum_balance"], 4000.0)
            self.assertEqual(candidate["candidate_payload"]["target_customer_tags"], [])
        finally:
            rmtree(temp_path, ignore_errors=True)

    def test_normalizes_savings_specific_fields(self) -> None:
        temp_path = _prepare_workspace_temp_dir("normalization-savings-detail")
        try:
            storage_config = NormalizationStorageConfig(
                driver="filesystem",
                env_prefix="dev",
                normalization_object_prefix="normalized",
                retention_class="hot",
                filesystem_root=str(temp_path),
            )
            service = NormalizationService(
                storage_config=storage_config,
                object_store=build_object_store(storage_config),
            )
            result = service.normalize_inputs(
                run_id="run-sav-001",
                inputs=[_build_savings_detail_input()],
            )

            source_result = result.source_results[0]
            self.assertEqual(source_result.validation_status, "pass")
            candidate = source_result.normalized_candidate_record
            self.assertIsNotNone(candidate)
            payload = candidate["candidate_payload"]
            self.assertEqual(candidate["subtype_code"], "high_interest")
            self.assertTrue(payload["tiered_rate_flag"])
            self.assertEqual(payload["interest_payment_frequency"], "monthly")
            self.assertIn("daily closing balance", payload["interest_calculation_method"].lower())
            self.assertIn("$5,000", payload["tier_definition_text"])
            self.assertIn("withdrawal", payload["withdrawal_limit_text"].lower())
            self.assertTrue(payload["registered_flag"])
        finally:
            rmtree(temp_path, ignore_errors=True)

    def test_generic_product_name_uses_specific_discovery_heading(self) -> None:
        temp_path = _prepare_workspace_temp_dir("normalization-product-name-heading")
        try:
            storage_config = NormalizationStorageConfig(
                driver="filesystem",
                env_prefix="dev",
                normalization_object_prefix="normalized",
                retention_class="hot",
                filesystem_root=str(temp_path),
            )
            service = NormalizationService(
                storage_config=storage_config,
                object_store=build_object_store(storage_config),
            )
            input_item = _build_savings_detail_input()
            input_item = NormalizationInput(
                **{
                    **input_item.__dict__,
                    "source_metadata": {
                        **input_item.source_metadata,
                        "discovery_metadata": {
                            "primary_heading": "Scotia U.S. Dollar Daily Interest Account",
                            "page_title": "Scotia U.S. Dollar Daily Interest Account | Scotiabank Canada",
                        },
                    },
                    "extracted_fields": [
                        NormalizationExtractedField(**{**field.__dict__, "candidate_value": "Bank Accounts"})
                        if field.field_name == "product_name"
                        else field
                        for field in input_item.extracted_fields
                    ],
                }
            )

            result = service.normalize_inputs(run_id="run-product-name-heading", inputs=[input_item])

            source_result = result.source_results[0]
            candidate = source_result.normalized_candidate_record
            self.assertEqual(candidate["product_name"], "Scotia U.S. Dollar Daily Interest Account")
            self.assertIn("Replaced generic product_name", " ".join(source_result.runtime_notes))
        finally:
            rmtree(temp_path, ignore_errors=True)

    def test_normalizes_gic_candidate_with_non_redeemable_subtype(self) -> None:
        temp_path = _prepare_workspace_temp_dir("normalization-gic-service")
        try:
            storage_config = NormalizationStorageConfig(
                driver="filesystem",
                env_prefix="dev",
                normalization_object_prefix="normalized",
                retention_class="hot",
                filesystem_root=str(temp_path),
            )
            service = NormalizationService(
                storage_config=storage_config,
                object_store=build_object_store(storage_config),
            )
            result = service.normalize_inputs(
                run_id="run-gic-001",
                inputs=[_build_gic_input()],
            )

            source_result = result.source_results[0]
            self.assertEqual(source_result.normalization_action, "stored")
            self.assertEqual(source_result.validation_status, "pass")
            candidate = source_result.normalized_candidate_record
            self.assertIsNotNone(candidate)
            self.assertEqual(candidate["product_type"], "gic")
            self.assertEqual(candidate["subtype_code"], "non_redeemable")
            payload = candidate["candidate_payload"]
            self.assertEqual(payload["term_length_text"], "1 year")
            self.assertEqual(payload["term_length_days"], 365)
            self.assertEqual(payload["minimum_deposit"], 500.0)
            self.assertEqual(payload["standard_rate"], 3.8)
            self.assertFalse(payload["redeemable_flag"])
            self.assertTrue(payload["non_redeemable_flag"])
            self.assertEqual(payload["compounding_frequency"], "annually")
            self.assertEqual(payload["payout_option"], "at_maturity")
            self.assertTrue(payload["registered_plan_supported"])
        finally:
            rmtree(temp_path, ignore_errors=True)

    def test_expands_gic_rate_source_into_multiple_product_candidates(self) -> None:
        temp_path = _prepare_workspace_temp_dir("normalization-gic-expansion")
        try:
            storage_config = NormalizationStorageConfig(
                driver="filesystem",
                env_prefix="dev",
                normalization_object_prefix="normalized",
                retention_class="hot",
                filesystem_root=str(temp_path),
            )
            service = NormalizationService(
                storage_config=storage_config,
                object_store=build_object_store(storage_config),
            )
            input_item = _build_gic_input()
            input_item = NormalizationInput(
                **{
                    **input_item.__dict__,
                    "source_id": "BMO-GIC-002",
                    "bank_code": "BMO",
                    "normalized_source_url": "https://www.bmo.com/main/personal/investments/gic/gic-rates/",
                    "source_metadata": {
                        **input_item.source_metadata,
                        "source_id": "BMO-GIC-002",
                        "product_type": "gic",
                        "discovery_role": "supporting_html",
                        "product_profile_expansion_mode": "fixture",
                    },
                }
            )

            result = service.normalize_inputs(run_id="run-bmo-gic-expansion", inputs=[input_item])

            self.assertGreaterEqual(len(result.source_results), 10)
            product_names = {
                item.normalized_candidate_record["product_name"]
                for item in result.source_results
                if item.normalized_candidate_record is not None
            }
            self.assertIn("BMO AIR MILES GIC", product_names)
            self.assertIn("BMO Guaranteed Investment Certificate (GIC)", product_names)
            profile_result = next(
                item
                for item in result.source_results
                if item.normalized_candidate_record is not None
                and item.normalized_candidate_record["product_name"] == "BMO AIR MILES GIC"
            )
            profile_candidate = profile_result.normalized_candidate_record
            self.assertEqual(profile_candidate["candidate_payload"]["highest_rate"], 0.25)
            self.assertEqual(profile_candidate["candidate_payload"]["term_rates"][0]["term"], "364 days")
            self.assertEqual(profile_result.validation_status, "pass")
            self.assertNotIn("required_field_missing", profile_result.validation_issue_codes)
            self.assertNotIn("conflicting_evidence", profile_result.validation_issue_codes)
            self.assertGreaterEqual(profile_result.source_confidence, 0.82)
        finally:
            rmtree(temp_path, ignore_errors=True)

    def test_live_admin_source_does_not_expand_dated_fixture_profiles(self) -> None:
        temp_path = _prepare_workspace_temp_dir("normalization-live-profile-disabled")
        try:
            storage_config = NormalizationStorageConfig(
                driver="filesystem",
                env_prefix="dev",
                normalization_object_prefix="normalized",
                retention_class="hot",
                filesystem_root=str(temp_path),
            )
            service = NormalizationService(storage_config=storage_config, object_store=build_object_store(storage_config))
            input_item = _build_gic_input()
            input_item = NormalizationInput(
                **{
                    **input_item.__dict__,
                    "source_id": "BMO-GIC-002",
                    "bank_code": "BMO",
                    "normalized_source_url": "https://www.bmo.com/main/personal/investments/gic/gic-rates/",
                    "source_metadata": {
                        **input_item.source_metadata,
                        "source_id": "BMO-GIC-002",
                        "product_type": "gic",
                        "discovery_role": "detail",
                    },
                }
            )

            result = service.normalize_inputs(run_id="run-live-profile-disabled", inputs=[input_item])

            self.assertEqual(len(result.source_results), 1)
            self.assertNotIn("Expanded deposit product profile", " ".join(result.source_results[0].runtime_notes))
        finally:
            rmtree(temp_path, ignore_errors=True)

    def test_profile_gic_expansion_resolves_conflicting_redeemability_flags(self) -> None:
        temp_path = _prepare_workspace_temp_dir("normalization-gic-profile-redeemability")
        try:
            storage_config = NormalizationStorageConfig(
                driver="filesystem",
                env_prefix="dev",
                normalization_object_prefix="normalized",
                retention_class="hot",
                filesystem_root=str(temp_path),
            )
            service = NormalizationService(
                storage_config=storage_config,
                object_store=build_object_store(storage_config),
            )
            input_item = _build_gic_input()
            extracted_fields = [
                NormalizationExtractedField(**{**field.__dict__, "candidate_value": True})
                if field.field_name == "redeemable_flag"
                else field
                for field in input_item.extracted_fields
            ]
            evidence_links = [
                NormalizationEvidenceLink(**{**link.__dict__, "candidate_value": "true"})
                if link.field_name == "redeemable_flag"
                else link
                for link in input_item.evidence_links
            ]
            input_item = NormalizationInput(
                **{
                    **input_item.__dict__,
                    "source_id": "RBC-GIC-003",
                    "bank_code": "RBC",
                    "normalized_source_url": "https://www.rbcroyalbank.com/investments/guaranteed-return-gics.html",
                    "source_metadata": {
                        **input_item.source_metadata,
                        "source_id": "RBC-GIC-003",
                        "product_type": "gic",
                        "discovery_role": "detail",
                        "product_type_name": "GIC",
                        "product_profile_expansion_mode": "fixture",
                    },
                    "extracted_fields": extracted_fields,
                    "evidence_links": evidence_links,
                }
            )

            result = service.normalize_inputs(run_id="run-rbc-gic-profile-flags", inputs=[input_item])

            candidates_by_name = {
                item.normalized_candidate_record["product_name"]: item
                for item in result.source_results
                if item.normalized_candidate_record is not None
            }
            cashable_payload = candidates_by_name["One-Year Cashable GIC"].normalized_candidate_record["candidate_payload"]
            self.assertTrue(cashable_payload["redeemable_flag"])
            self.assertFalse(cashable_payload["non_redeemable_flag"])
            non_redeemable_payload = candidates_by_name["Non-Redeemable GIC"].normalized_candidate_record["candidate_payload"]
            self.assertFalse(non_redeemable_payload["redeemable_flag"])
            self.assertTrue(non_redeemable_payload["non_redeemable_flag"])
            mixed_payload = candidates_by_name["RateAdvantage GIC"].normalized_candidate_record["candidate_payload"]
            self.assertNotIn("redeemable_flag", mixed_payload)
            self.assertNotIn("non_redeemable_flag", mixed_payload)
            self.assertTrue(
                all("inconsistent_cross_field_logic" not in item.validation_issue_codes for item in result.source_results)
            )
            self.assertIn("Resolved conflicting GIC redeemability flags", " ".join(candidates_by_name["One-Year Cashable GIC"].runtime_notes))
        finally:
            rmtree(temp_path, ignore_errors=True)

    def test_suppresses_unprofiled_admin_gic_supporting_sources(self) -> None:
        temp_path = _prepare_workspace_temp_dir("normalization-gic-support-suppression")
        try:
            storage_config = NormalizationStorageConfig(
                driver="filesystem",
                env_prefix="dev",
                normalization_object_prefix="normalized",
                retention_class="hot",
                filesystem_root=str(temp_path),
            )
            service = NormalizationService(
                storage_config=storage_config,
                object_store=build_object_store(storage_config),
            )
            input_item = _build_gic_input()
            input_item = NormalizationInput(
                **{
                    **input_item.__dict__,
                    "source_id": "AUTO-BMO-CHE-069e973445",
                    "bank_code": "BMO",
                    "source_metadata": {
                        **input_item.source_metadata,
                        "source_id": "AUTO-BMO-CHE-069e973445",
                        "product_type": "gic",
                        "discovery_role": "supporting_html",
                        "expected_fields": ["fee_schedule"],
                        "product_profile_expansion_mode": "fixture",
                    },
                }
            )

            result = service.normalize_inputs(run_id="run-bmo-gic-support-suppression", inputs=[input_item])

            self.assertEqual(result.source_results, [])
        finally:
            rmtree(temp_path, ignore_errors=True)

    def test_profile_url_tokens_do_not_prefix_match_supporting_rate_pages(self) -> None:
        temp_path = _prepare_workspace_temp_dir("normalization-profile-url-exact-match")
        try:
            storage_config = NormalizationStorageConfig(
                driver="filesystem",
                env_prefix="dev",
                normalization_object_prefix="normalized",
                retention_class="hot",
                filesystem_root=str(temp_path),
            )
            service = NormalizationService(
                storage_config=storage_config,
                object_store=build_object_store(storage_config),
            )
            input_item = _build_gic_input()
            input_item = NormalizationInput(
                **{
                    **input_item.__dict__,
                    "source_id": "TD-GIC-006",
                    "bank_code": "TD",
                    "normalized_source_url": "https://www.td.com/ca/en/personal-banking/personal-investing/products/gic/market-growth-gic-rates",
                    "source_metadata": {
                        **input_item.source_metadata,
                        "source_id": "TD-GIC-006",
                        "product_type": "gic",
                        "discovery_role": "supporting_html",
                        "expected_fields": ["product_variants", "minimum_guaranteed_return", "maximum_return"],
                        "product_type_name": "GIC",
                        "product_profile_expansion_mode": "fixture",
                    },
                }
            )

            result = service.normalize_inputs(run_id="run-td-gic-rate-support-suppression", inputs=[input_item])

            self.assertEqual(result.source_results, [])
        finally:
            rmtree(temp_path, ignore_errors=True)

    def test_expands_chequing_source_into_multiple_profile_candidates(self) -> None:
        temp_path = _prepare_workspace_temp_dir("normalization-chequing-expansion")
        try:
            storage_config = NormalizationStorageConfig(
                driver="filesystem",
                env_prefix="dev",
                normalization_object_prefix="normalized",
                retention_class="hot",
                filesystem_root=str(temp_path),
            )
            service = NormalizationService(
                storage_config=storage_config,
                object_store=build_object_store(storage_config),
            )
            input_item = _build_chequing_input()
            input_item = NormalizationInput(
                **{
                    **input_item.__dict__,
                    "source_id": "RBC-CHQ-003",
                    "bank_code": "RBC",
                    "normalized_source_url": "https://www.rbcroyalbank.com/bank-accounts/chequing-accounts/advantage-banking.html",
                    "source_metadata": {
                        **input_item.source_metadata,
                        "source_id": "RBC-CHQ-003",
                        "product_type": "chequing",
                        "discovery_role": "detail",
                        "expected_fields": ["product_name", "monthly_fee"],
                        "product_profile_expansion_mode": "fixture",
                    },
                    "extracted_fields": [
                        NormalizationExtractedField(**{**field.__dict__, "candidate_value": "RBC"})
                        if field.field_name == "bank_code"
                        else field
                        for field in input_item.extracted_fields
                    ],
                }
            )

            result = service.normalize_inputs(run_id="run-rbc-chequing-expansion", inputs=[input_item])

            product_names = {
                item.normalized_candidate_record["product_name"]
                for item in result.source_results
                if item.normalized_candidate_record is not None
            }
            self.assertEqual(product_names, {"RBC Advantage Banking", "RBC Advantage Banking for students"})
        finally:
            rmtree(temp_path, ignore_errors=True)

    def test_normalizes_deposit_detail_fields_and_term_rate_table(self) -> None:
        temp_path = _prepare_workspace_temp_dir("normalization-deposit-detail-fields")
        try:
            input_item = _build_gic_input()
            term_rate_table = [
                {"term_label": "6 months", "rate": "4.10", "minimum_deposit": "500.00"},
                {"term_label": "12 months", "rate": "4.50", "minimum_deposit": "500.00"},
            ]
            input_item = NormalizationInput(
                **{
                    **input_item.__dict__,
                    "extracted_fields": [
                        *input_item.extracted_fields,
                        _field("base_12_month_rate", "4.50", "decimal", 0.84, evidence_chunk_id="chunk-gic-rate"),
                        _field("application_method", "Apply online or in branch.", "string", 0.8, evidence_chunk_id="chunk-apply"),
                        _field("post_maturity_interest_rate", "At maturity, renewal rates may apply.", "string", 0.8, evidence_chunk_id="chunk-maturity"),
                        _field("tax_benefits", "TFSA and RRSP options may provide tax benefits.", "string", 0.78, evidence_chunk_id="chunk-tax"),
                        _field("deposit_insurance", "Eligible deposits are protected by CDIC limits.", "string", 0.82, evidence_chunk_id="chunk-insurance"),
                        _field("term_rate_table", term_rate_table, "json", 0.86, evidence_chunk_id="chunk-term-table"),
                    ],
                    "evidence_links": [
                        *input_item.evidence_links,
                        _evidence("base_12_month_rate", "4.50", "chunk-gic-rate"),
                        _evidence("application_method", "Apply online or in branch.", "chunk-apply"),
                        _evidence("post_maturity_interest_rate", "At maturity, renewal rates may apply.", "chunk-maturity"),
                        _evidence("tax_benefits", "TFSA and RRSP options may provide tax benefits.", "chunk-tax"),
                        _evidence("deposit_insurance", "Eligible deposits are protected by CDIC limits.", "chunk-insurance"),
                        _evidence("term_rate_table", json.dumps(term_rate_table), "chunk-term-table"),
                    ],
                }
            )
            storage_config = NormalizationStorageConfig(
                driver="filesystem",
                env_prefix="dev",
                normalization_object_prefix="normalized",
                retention_class="hot",
                filesystem_root=str(temp_path),
            )
            service = NormalizationService(
                storage_config=storage_config,
                object_store=build_object_store(storage_config),
            )

            result = service.normalize_inputs(run_id="run-gic-detail-fields", inputs=[input_item])

            candidate = result.source_results[0].normalized_candidate_record
            self.assertIsNotNone(candidate)
            payload = candidate["candidate_payload"]
            self.assertEqual(payload["base_12_month_rate"], 4.5)
            self.assertEqual(payload["application_method"], "Apply online or in branch.")
            self.assertEqual(payload["post_maturity_interest_rate"], "At maturity, renewal rates may apply.")
            self.assertEqual(payload["tax_benefits"], "TFSA and RRSP options may provide tax benefits.")
            self.assertEqual(payload["deposit_insurance"], "Eligible deposits are protected by CDIC limits.")
            self.assertEqual(payload["term_rate_table"][1]["term_length_days"], 360)
            self.assertEqual(payload["term_rate_table"][1]["rate"], 4.5)
        finally:
            rmtree(temp_path, ignore_errors=True)

    def test_normalizes_gic_subtype_from_cashability_context_when_title_is_generic(self) -> None:
        temp_path = _prepare_workspace_temp_dir("normalization-gic-context-subtype")
        try:
            storage_config = NormalizationStorageConfig(
                driver="filesystem",
                env_prefix="dev",
                normalization_object_prefix="normalized",
                retention_class="hot",
                filesystem_root=str(temp_path),
            )
            service = NormalizationService(
                storage_config=storage_config,
                object_store=build_object_store(storage_config),
            )
            input_item = _build_gic_input()
            context_fields = []
            for field in input_item.extracted_fields:
                if field.field_name == "product_name":
                    context_fields.append(NormalizationExtractedField(**{**field.__dict__, "candidate_value": "Guaranteed Investment Certificates (GICs)"}))
                    continue
                context_fields.append(field)
            context_fields.append(
                _field(
                    "cashability",
                    "Document Investments Guaranteed Investment Certificates (GICs) Non-redeemable GIC",
                    "string",
                    0.72,
                    evidence_chunk_id="chunk-gic-context",
                )
            )
            input_item = NormalizationInput(
                **{
                    **input_item.__dict__,
                    "extracted_fields": context_fields,
                    "evidence_links": [
                        *input_item.evidence_links,
                        _evidence(
                            "cashability",
                            "Document Investments Guaranteed Investment Certificates (GICs) Non-redeemable GIC",
                            "chunk-gic-context",
                        ),
                    ],
                }
            )

            result = service.normalize_inputs(run_id="run-gic-context-001", inputs=[input_item])

            source_result = result.source_results[0]
            candidate = source_result.normalized_candidate_record
            self.assertIsNotNone(candidate)
            self.assertEqual(candidate["subtype_code"], "non_redeemable")
            self.assertNotIn("ambiguous_mapping", source_result.validation_issue_codes)
        finally:
            rmtree(temp_path, ignore_errors=True)

    def test_missing_rate_sets_error_status(self) -> None:
        temp_path = _prepare_workspace_temp_dir("normalization-error")
        try:
            storage_config = NormalizationStorageConfig(
                driver="filesystem",
                env_prefix="dev",
                normalization_object_prefix="normalized",
                retention_class="hot",
                filesystem_root=str(temp_path),
            )
            service = NormalizationService(
                storage_config=storage_config,
                object_store=build_object_store(storage_config),
            )
            input_item = _build_input()
            input_item = NormalizationInput(
                **{
                    **input_item.__dict__,
                    "extracted_fields": [field for field in input_item.extracted_fields if field.field_name != "standard_rate"],
                    "evidence_links": [link for link in input_item.evidence_links if link.field_name != "standard_rate"],
                }
            )

            result = service.normalize_inputs(run_id="run-002", inputs=[input_item])

            source_result = result.source_results[0]
            self.assertEqual(source_result.validation_status, "error")
            self.assertIn("required_field_missing", source_result.validation_issue_codes)
        finally:
            rmtree(temp_path, ignore_errors=True)

    def test_business_tag_ignores_business_day_phrases(self) -> None:
        temp_path = _prepare_workspace_temp_dir("normalization-business-day")
        try:
            storage_config = NormalizationStorageConfig(
                driver="filesystem",
                env_prefix="dev",
                normalization_object_prefix="normalized",
                retention_class="hot",
                filesystem_root=str(temp_path),
            )
            service = NormalizationService(
                storage_config=storage_config,
                object_store=build_object_store(storage_config),
            )
            input_item = _build_gic_input()
            notes_fields = []
            for field in input_item.extracted_fields:
                if field.field_name == "notes":
                    continue
                notes_fields.append(field)
            notes_fields.append(
                _field(
                    "notes",
                    "Funds will be available on the next business day following redemption.",
                    "string",
                    0.7,
                    evidence_chunk_id="chunk-business-day",
                )
            )
            input_item = NormalizationInput(
                **{
                    **input_item.__dict__,
                    "extracted_fields": notes_fields,
                    "evidence_links": [
                        *input_item.evidence_links,
                        _evidence(
                            "notes",
                            "Funds will be available on the next business day following redemption.",
                            "chunk-business-day",
                        ),
                    ],
                }
            )

            result = service.normalize_inputs(run_id="run-business-day-001", inputs=[input_item])

            source_result = result.source_results[0]
            candidate = source_result.normalized_candidate_record
            self.assertIsNotNone(candidate)
            self.assertNotIn("business", candidate["candidate_payload"]["target_customer_tags"])
        finally:
            rmtree(temp_path, ignore_errors=True)

    def test_gic_missing_minimum_deposit_sets_error_status(self) -> None:
        temp_path = _prepare_workspace_temp_dir("normalization-gic-error")
        try:
            storage_config = NormalizationStorageConfig(
                driver="filesystem",
                env_prefix="dev",
                normalization_object_prefix="normalized",
                retention_class="hot",
                filesystem_root=str(temp_path),
            )
            service = NormalizationService(
                storage_config=storage_config,
                object_store=build_object_store(storage_config),
            )
            input_item = _build_gic_input()
            input_item = NormalizationInput(
                **{
                    **input_item.__dict__,
                    "extracted_fields": [field for field in input_item.extracted_fields if field.field_name != "minimum_deposit"],
                    "evidence_links": [link for link in input_item.evidence_links if link.field_name != "minimum_deposit"],
                }
            )

            result = service.normalize_inputs(run_id="run-gic-002", inputs=[input_item])

            source_result = result.source_results[0]
            self.assertEqual(source_result.validation_status, "error")
            self.assertIn("required_field_missing", source_result.validation_issue_codes)
        finally:
            rmtree(temp_path, ignore_errors=True)

    def test_gic_minimum_balance_alias_satisfies_minimum_deposit_requiredness(self) -> None:
        temp_path = _prepare_workspace_temp_dir("normalization-gic-minimum-balance-alias")
        try:
            storage_config = NormalizationStorageConfig(
                driver="filesystem",
                env_prefix="dev",
                normalization_object_prefix="normalized",
                retention_class="hot",
                filesystem_root=str(temp_path),
            )
            service = NormalizationService(
                storage_config=storage_config,
                object_store=build_object_store(storage_config),
            )
            input_item = _build_gic_input()
            extracted_fields = []
            for field in input_item.extracted_fields:
                if field.field_name == "minimum_deposit":
                    extracted_fields.append(NormalizationExtractedField(**{**field.__dict__, "field_name": "minimum_balance"}))
                    continue
                extracted_fields.append(field)
            evidence_links = []
            for link in input_item.evidence_links:
                if link.field_name == "minimum_deposit":
                    evidence_links.append(NormalizationEvidenceLink(**{**link.__dict__, "field_name": "minimum_balance"}))
                    continue
                evidence_links.append(link)
            input_item = NormalizationInput(
                **{
                    **input_item.__dict__,
                    "extracted_fields": extracted_fields,
                    "evidence_links": evidence_links,
                }
            )

            result = service.normalize_inputs(run_id="run-gic-minimum-balance-alias", inputs=[input_item])

            source_result = result.source_results[0]
            candidate = source_result.normalized_candidate_record
            self.assertIsNotNone(candidate)
            self.assertEqual(source_result.validation_status, "pass")
            self.assertEqual(candidate["candidate_payload"]["minimum_deposit"], 500.0)
            self.assertIn("minimum_deposit", {item["field_name"] for item in source_result.field_evidence_link_records})
        finally:
            rmtree(temp_path, ignore_errors=True)

    def test_dynamic_product_type_uses_ai_normalization_fallback(self) -> None:
        temp_path = _prepare_workspace_temp_dir("normalization-dynamic-service")
        try:
            storage_config = NormalizationStorageConfig(
                driver="filesystem",
                env_prefix="dev",
                normalization_object_prefix="normalized",
                retention_class="hot",
                filesystem_root=str(temp_path),
            )
            service = NormalizationService(
                storage_config=storage_config,
                object_store=build_object_store(storage_config),
            )
            input_item = _build_input()
            dynamic_fields = []
            for field in input_item.extracted_fields:
                if field.field_name == "product_type":
                    dynamic_fields.append(
                        NormalizationExtractedField(**{**field.__dict__, "candidate_value": "tfsa-savings"})
                    )
                else:
                    dynamic_fields.append(field)
            input_item = NormalizationInput(
                **{
                    **input_item.__dict__,
                    "source_id": "TD-TFSA-001",
                    "source_metadata": {
                        "product_type": "tfsa-savings",
                        "product_type_dynamic": True,
                        "product_type_name": "TFSA Savings",
                        "product_type_description": "Tax-free savings deposit account for retail customers.",
                        "fallback_policy": "generic_ai_review",
                    },
                    "schema_context": {"product_family": "deposit", "product_type": "tfsa-savings"},
                    "extracted_fields": dynamic_fields,
                }
            )

            with (
                patch("worker.pipeline.fpds_normalization.service.llm_provider_configured", return_value=True),
                patch("worker.pipeline.fpds_normalization.service.configured_model_id", return_value="gpt-5.6-luna"),
                patch(
                    "worker.pipeline.fpds_normalization.service.invoke_openai_json_schema",
                    return_value=(
                        {
                            "summary": "AI normalized TFSA-specific eligibility and subtype.",
                            "product_name": "TD TFSA Savings Account",
                            "subtype_code": "other",
                            "source_subtype_label": "tax-free savings",
                            "normalized_fields": [
                                {
                                    "field_name": "eligibility_text",
                                    "value_type": "string",
                                    "candidate_value": "Available to Canadian residents aged 18 or older.",
                                }
                            ],
                        },
                        {
                            "model_id": "gpt-5.6-luna",
                            "prompt_tokens": 140,
                            "completion_tokens": 42,
                            "provider_request_id": "resp-norm-dyn-001",
                        },
                    ),
                ),
            ):
                result = service.normalize_inputs(
                    run_id="run-dyn-001",
                    inputs=[input_item],
                )

            source_result = result.source_results[0]
            candidate = source_result.normalized_candidate_record
            self.assertEqual(source_result.model_execution_record["agent_name"], "fpds-dynamic-product-normalizer")
            self.assertEqual(source_result.usage_record["usage_metadata"]["usage_mode"], "openai-dynamic-product-normalization")
            self.assertEqual(candidate["product_type"], "tfsa-savings")
            self.assertEqual(candidate["subtype_code"], "other")
            self.assertEqual(candidate["candidate_payload"]["eligibility_text"], "Available to Canadian residents aged 18 or older.")
            self.assertLess(source_result.source_confidence or 1.0, 0.75)
            self.assertIn("AI normalized TFSA-specific eligibility and subtype.", source_result.runtime_notes)
        finally:
            rmtree(temp_path, ignore_errors=True)

    def test_dynamic_lending_service_omits_unofficial_values_before_validation(self) -> None:
        temp_path = _prepare_workspace_temp_dir("normalization-dynamic-lending-grounding-filter")
        try:
            storage_config = NormalizationStorageConfig(
                driver="filesystem",
                env_prefix="dev",
                normalization_object_prefix="normalized",
                retention_class="hot",
                filesystem_root=str(temp_path),
            )
            service = NormalizationService(
                storage_config=storage_config,
                object_store=build_object_store(storage_config),
            )
            base = _build_input()
            input_item = NormalizationInput(
                **{
                    **base.__dict__,
                    "source_id": "BANK-CARD-001",
                    "source_metadata": {
                        "product_type": "credit-card",
                        "product_type_dynamic": True,
                        "expected_fields": [
                            "product_name",
                            "annual_fee",
                            "purchase_interest_rate",
                            "rewards_summary",
                        ],
                    },
                    "schema_context": {"product_family": "lending", "product_type": "credit-card"},
                    "extracted_fields": [
                        _field("product_family", "lending", "string", 0.99),
                        _field("product_type", "credit-card", "string", 0.99),
                        _field("country_code", "CA", "string", 0.99),
                        _field("bank_code", "TD", "string", 0.99),
                        _field("source_language", "en", "string", 0.99),
                        _field("currency", "CAD", "string", 0.99),
                        _field("product_name", "Example Card", "string", 0.88),
                        _field("annual_fee", "0.00", "decimal", 0.86, evidence_chunk_id="chunk-card-fee"),
                        _field(
                            "rewards_summary",
                            "Earn 2 points per $1 on eligible purchases.",
                            "string",
                            0.82,
                            evidence_chunk_id="chunk-card-rewards",
                        ),
                    ],
                    "evidence_links": [
                        _evidence("annual_fee", "0.00", "chunk-card-fee"),
                        _evidence(
                            "rewards_summary",
                            "Earn 2 points per $1 on eligible purchases.",
                            "chunk-card-rewards",
                        ),
                    ],
                }
            )

            with patch("worker.pipeline.fpds_normalization.service.llm_provider_configured", return_value=False):
                result = service.normalize_inputs(
                    run_id="run-dynamic-lending-grounding-filter",
                    inputs=[input_item],
                )

            source_result = result.source_results[0]
            candidate = source_result.normalized_candidate_record
            self.assertNotIn("annual_fee", candidate["candidate_payload"])
            self.assertNotIn("rewards_summary", candidate["candidate_payload"])
            self.assertEqual(
                candidate["field_mapping_metadata"]["rewards_summary"]["suppressed_reason"],
                "official_grounding_missing",
            )
            self.assertIn("required_field_missing", candidate["validation_issue_codes"])
        finally:
            rmtree(temp_path, ignore_errors=True)

    def test_dynamic_gic_normalization_coerces_display_money_values(self) -> None:
        temp_path = _prepare_workspace_temp_dir("normalization-dynamic-gic-money")
        try:
            storage_config = NormalizationStorageConfig(
                driver="filesystem",
                env_prefix="dev",
                normalization_object_prefix="normalized",
                retention_class="hot",
                filesystem_root=str(temp_path),
            )
            service = NormalizationService(
                storage_config=storage_config,
                object_store=build_object_store(storage_config),
            )
            input_item = _build_gic_input()
            dynamic_fields = []
            for field in input_item.extracted_fields:
                if field.field_name == "product_type":
                    dynamic_fields.append(
                        NormalizationExtractedField(**{**field.__dict__, "candidate_value": "gic-term-deposit"})
                    )
                else:
                    dynamic_fields.append(field)
            input_item = NormalizationInput(
                **{
                    **input_item.__dict__,
                    "source_id": "CIBC-GIC-003",
                    "source_metadata": {
                        "product_type": "gic-term-deposit",
                        "product_type_dynamic": True,
                        "product_type_name": "GIC / Term Deposit",
                        "product_type_description": "A fixed-term guaranteed investment certificate.",
                        "fallback_policy": "generic_ai_review",
                    },
                    "schema_context": {"product_family": "deposit", "product_type": "gic-term-deposit"},
                    "extracted_fields": dynamic_fields,
                    "evidence_links": [
                        NormalizationEvidenceLink(
                            **{
                                **link.__dict__,
                                "candidate_value": candidate_value,
                                "evidence_text_excerpt": evidence_text_excerpt,
                            }
                        )
                        for link, candidate_value, evidence_text_excerpt in (
                            (
                                _evidence("minimum_deposit", "$1,000", "chunk-gic-minimum"),
                                "$1,000",
                                "The minimum investment is $1,000.",
                            ),
                            (
                                _evidence("monthly_fee", "No fees", "chunk-gic-fee"),
                                "No fees",
                                "No monthly fees apply.",
                            ),
                            (
                                _evidence("public_display_fee", "No fees", "chunk-gic-fee"),
                                "No fees",
                                "No monthly fees apply.",
                            ),
                            (
                                _evidence("public_display_rate", "4.25%", "chunk-gic-rate"),
                                "4.25%",
                                "Earn 4.25% annually.",
                            ),
                        )
                    ],
                }
            )

            with (
                patch("worker.pipeline.fpds_normalization.service.llm_provider_configured", return_value=True),
                patch("worker.pipeline.fpds_normalization.service.configured_model_id", return_value="gpt-5.6-luna"),
                patch(
                    "worker.pipeline.fpds_normalization.service.invoke_openai_json_schema",
                    return_value=(
                        {
                            "summary": "AI normalized CIBC Bonus Rate GIC fields.",
                            "product_name": "CIBC Bonus Rate GIC",
                            "subtype_code": "other",
                            "source_subtype_label": "GIC / Term Deposit",
                            "normalized_fields": [
                                {"field_name": "minimum_deposit", "value_type": "string", "candidate_value": "$1,000"},
                                {"field_name": "monthly_fee", "value_type": "string", "candidate_value": "No fees"},
                                {"field_name": "public_display_fee", "value_type": "string", "candidate_value": "No fees"},
                                {"field_name": "public_display_rate", "value_type": "string", "candidate_value": "4.25%"},
                                {
                                    "field_name": "promotional_period_text",
                                    "value_type": "string",
                                    "candidate_value": "Why choose a CIBC Bonus Rate GIC? Predictable earnings.",
                                },
                            ],
                        },
                        {
                            "model_id": "gpt-5.6-luna",
                            "prompt_tokens": 170,
                            "completion_tokens": 55,
                            "provider_request_id": "resp-norm-dyn-gic-001",
                        },
                    ),
                ),
            ):
                result = service.normalize_inputs(run_id="run-dyn-gic-001", inputs=[input_item])

            source_result = result.source_results[0]
            payload = source_result.normalized_candidate_record["candidate_payload"]
            self.assertEqual(payload["minimum_deposit"], 1000.0)
            self.assertEqual(payload["monthly_fee"], 0.0)
            self.assertEqual(payload["public_display_fee"], 0.0)
            self.assertEqual(payload["public_display_rate"], 4.25)
            self.assertNotIn("promotional_period_text", payload)
            self.assertNotIn("invalid_numeric_range", source_result.validation_issue_codes)
        finally:
            rmtree(temp_path, ignore_errors=True)

    def test_dynamic_gic_term_deposit_cleans_off_context_fields_and_requires_rate(self) -> None:
        temp_path = _prepare_workspace_temp_dir("normalization-dynamic-gic-requiredness")
        try:
            storage_config = NormalizationStorageConfig(
                driver="filesystem",
                env_prefix="dev",
                normalization_object_prefix="normalized",
                retention_class="hot",
                filesystem_root=str(temp_path),
            )
            service = NormalizationService(
                storage_config=storage_config,
                object_store=build_object_store(storage_config),
            )
            input_item = _build_gic_input()
            dynamic_fields = []
            for field in input_item.extracted_fields:
                if field.field_name == "product_type":
                    dynamic_fields.append(NormalizationExtractedField(**{**field.__dict__, "candidate_value": "gic-term-deposit"}))
                elif field.field_name == "standard_rate":
                    continue
                else:
                    dynamic_fields.append(field)
            dynamic_fields.extend(
                [
                    _field("description_short", "Learn About CIBC Mutual Fund Account Conversion", "string", 0.7),
                    _field("eligibility_text", "What you need to know Type Cashable Access Access your money at any time", "string", 0.55),
                    _field(
                        "interest_calculation_method",
                        (
                            "Otherwise, you have to cash out the full balance Interest Simple interest is calculated and paid at maturity "
                            "If you cash out in the first 29 days, you're not paid interest"
                        ),
                        "string",
                        0.71,
                    ),
                ]
            )
            input_item = NormalizationInput(
                **{
                    **input_item.__dict__,
                    "source_id": "CIBC-GIC-002",
                    "source_metadata": {
                        "product_type": "gic-term-deposit",
                        "product_type_dynamic": True,
                        "product_type_name": "GIC / Term Deposit",
                        "product_type_description": "A fixed-term guaranteed investment certificate.",
                        "fallback_policy": "generic_ai_review",
                    },
                    "schema_context": {"product_family": "deposit", "product_type": "gic-term-deposit"},
                    "extracted_fields": dynamic_fields,
                    "evidence_links": [link for link in input_item.evidence_links if link.field_name != "standard_rate"],
                }
            )

            result = service.normalize_inputs(run_id="run-dyn-gic-requiredness", inputs=[input_item])

            source_result = result.source_results[0]
            payload = source_result.normalized_candidate_record["candidate_payload"]
            self.assertNotIn("description_short", payload)
            self.assertNotIn("eligibility_text", payload)
            self.assertEqual(payload["interest_calculation_method"], "Simple interest is calculated and paid at maturity")
            self.assertEqual(source_result.validation_status, "error")
            self.assertIn("required_field_missing", source_result.validation_issue_codes)
        finally:
            rmtree(temp_path, ignore_errors=True)


class SupportingMergeTests(unittest.TestCase):
    def test_generic_gic_support_rejects_bank_only_ownership_percentage_match(self) -> None:
        base_artifact = {
            "schema_context": {"product_type": "gic"},
            "extracted_fields": [
                _field_dict(
                    "product_name",
                    "Long-Term Guaranteed Investment Certificates (GICs) | B2B Bank",
                    "string",
                    0.88,
                ),
            ],
            "evidence_links": [],
            "runtime_notes": [],
        }
        supporting_artifact = {
            "retrieval_result": {
                "matches": [
                    _match_dict(
                        field_name="standard_rate",
                        anchor_value="corporate-ownership",
                        excerpt=(
                            "B2B Bank Non-Registered GIC Schedule A. List each person who owns or controls "
                            "25% or more of the voting shares of the corporation."
                        ),
                    )
                ]
            }
        }

        merged = merge_supporting_artifacts(
            target_source_id="AUTO-B2B-GIC-long-term",
            base_artifact=base_artifact,
            supporting_artifacts={"AUTO-B2B-GIC-corporate-form": supporting_artifact},
        )

        fields_by_name = {item["field_name"]: item for item in merged["extracted_fields"]}
        self.assertNotIn("standard_rate", fields_by_name)
        self.assertNotIn("public_display_rate", fields_by_name)

    def test_supporting_source_ids_for_td_targets(self) -> None:
        self.assertEqual(supporting_source_ids_for_target("BMO-SAV-002"), ("BMO-SAV-006",))
        self.assertEqual(supporting_source_ids_for_target("BMO-SAV-003"), ("BMO-SAV-006",))
        self.assertEqual(supporting_source_ids_for_target("BMO-SAV-004"), ("BMO-SAV-006",))
        self.assertEqual(supporting_source_ids_for_target("CIBC-SAV-002"), ("CIBC-SAV-004",))
        self.assertEqual(supporting_source_ids_for_target("CIBC-SAV-003"), ("CIBC-SAV-004",))
        self.assertEqual(supporting_source_ids_for_target("TD-SAV-002"), ("TD-SAV-005", "TD-SAV-007", "TD-SAV-008"))
        self.assertEqual(supporting_source_ids_for_target("TD-SAV-003"), ("TD-SAV-005", "TD-SAV-007", "TD-SAV-008"))
        self.assertEqual(supporting_source_ids_for_target("TD-SAV-004"), ("TD-SAV-005", "TD-SAV-007", "TD-SAV-008"))
        self.assertEqual(supporting_source_ids_for_target("SCOTIA-SAV-004"), ("SCOTIA-SAV-006",))
        self.assertEqual(supporting_source_ids_for_target("TD-SAV-999"), ())

    def test_generic_supporting_merge_handles_generated_savings_rate_source(self) -> None:
        base_artifact = {
            "schema_context": {"product_type": "savings"},
            "extracted_fields": [
                _field_dict("product_name", "TD Every Day Savings Account", "string", 0.88),
                _field_dict("monthly_fee", "0.00", "decimal", 0.83, evidence_chunk_id="chunk-detail-fee"),
            ],
            "evidence_links": [],
            "runtime_notes": [],
        }
        supporting_artifact = {
            "retrieval_result": {
                "matches": [
                    _match_dict(
                        field_name="rate_tiers",
                        anchor_value="td-every-day-savings-account",
                        excerpt="TD Every Day Savings Account Total Daily Closing Balance $0 to $999.99 0.010%",
                    )
                ]
            }
        }

        merged = merge_supporting_artifacts(
            target_source_id="AUTO-TB-SAV-82eb5b204c",
            base_artifact=base_artifact,
            supporting_artifacts={"AUTO-TB-SAV-c528b5abb8": supporting_artifact},
        )

        fields_by_name = {item["field_name"]: item for item in merged["extracted_fields"]}
        self.assertEqual(fields_by_name["standard_rate"]["candidate_value"], "0.01")
        self.assertEqual(fields_by_name["public_display_rate"]["candidate_value"], "0.01")
        self.assertTrue(fields_by_name["standard_rate"]["field_metadata"]["generic_supporting_merge"])

    def test_generic_savings_support_supplements_exact_product_monthly_fee(self) -> None:
        base_artifact = {
            "schema_context": {"product_type": "savings"},
            "extracted_fields": [
                _field_dict("product_name", "Example US Dollar Savings Account", "string", 0.9),
                _field_dict("standard_rate", "0.25", "decimal", 0.9),
                _field_dict("public_display_rate", "0.25", "decimal", 0.9),
            ],
            "evidence_links": [],
            "runtime_notes": [],
        }
        supporting_artifact = {
            "retrieval_result": {
                "matches": [
                    _match_dict(
                        field_name="fees_text",
                        anchor_value="fees-and-details",
                        excerpt=(
                            "Example US Dollar Savings Account earns interest on your balance "
                            "and has no monthly account fee."
                        ),
                    )
                ]
            }
        }

        merged = merge_supporting_artifacts(
            target_source_id="AUTO-EXAMPLE-SAV-usd",
            base_artifact=base_artifact,
            supporting_artifacts={"AUTO-EXAMPLE-SAV-fees": supporting_artifact},
        )

        fields_by_name = {item["field_name"]: item for item in merged["extracted_fields"]}
        self.assertEqual(fields_by_name["monthly_fee"]["candidate_value"], "0.00")
        self.assertEqual(fields_by_name["public_display_fee"]["candidate_value"], "0.00")
        self.assertIn("Supplemented missing savings fee fields", " ".join(merged["runtime_notes"]))

    def test_generic_savings_support_does_not_borrow_distant_sibling_fee(self) -> None:
        base_artifact = {
            "schema_context": {"product_type": "savings"},
            "extracted_fields": [
                _field_dict("product_name", "Premium Rate Savings Account", "string", 0.9),
                _field_dict("standard_rate", "0.01", "decimal", 0.9),
            ],
            "evidence_links": [],
            "runtime_notes": [],
        }
        supporting_artifact = {
            "retrieval_result": {
                "matches": [
                    _match_dict(
                        field_name="fees_text",
                        anchor_value="banking-agreements-and-fees",
                        excerpt=(
                            "Performance Chequing Account has a monthly fee of $17.95 and a $4,000 waiver. "
                            + "General plan information. " * 40
                            + "Interac transfers also extend to Premium Rate Savings Account customers."
                        ),
                    )
                ]
            }
        }

        merged = merge_supporting_artifacts(
            target_source_id="AUTO-EXAMPLE-SAV-premium",
            base_artifact=base_artifact,
            supporting_artifacts={"AUTO-EXAMPLE-SAV-fees": supporting_artifact},
        )

        fields_by_name = {item["field_name"]: item for item in merged["extracted_fields"]}
        self.assertNotIn("monthly_fee", fields_by_name)
        self.assertNotIn("public_display_fee", fields_by_name)

    def test_generic_supporting_merge_accepts_generated_savings_rate_table_fields(self) -> None:
        base_artifact = {
            "schema_context": {"product_type": "savings"},
            "extracted_fields": [
                _field_dict("product_name", "RBC Enhanced Savings account", "string", 0.88),
            ],
            "evidence_links": [],
            "runtime_notes": [],
        }
        supporting_artifact = {
            "retrieval_result": {
                "matches": [
                    _match_dict(
                        field_name="account_interest_rates",
                        anchor_value="savings-rate-table",
                        excerpt="RBC Enhanced Savings account Interest Rate 1.600%",
                    )
                ]
            }
        }

        merged = merge_supporting_artifacts(
            target_source_id="AUTO-RBOC-SAV-c94424a3cd",
            base_artifact=base_artifact,
            supporting_artifacts={"AUTO-RBOC-SAV-bec870fffd": supporting_artifact},
        )

        fields_by_name = {item["field_name"]: item for item in merged["extracted_fields"]}
        self.assertEqual(fields_by_name["standard_rate"]["candidate_value"], "1.60")
        self.assertEqual(fields_by_name["public_display_rate"]["candidate_value"], "1.60")

    def test_generic_supporting_merge_ignores_expired_offer_and_uses_current_rate_match(self) -> None:
        base_artifact = {
            "schema_context": {"product_type": "savings"},
            "extracted_fields": [
                _field_dict("product_name", "Example Savings Account", "string", 0.88),
            ],
            "evidence_links": [],
            "runtime_notes": [],
        }
        supporting_artifact = {
            "retrieval_result": {
                "matches": [
                    _match_dict(
                        field_name="promotional_rate",
                        anchor_value="old-offer",
                        excerpt=(
                            "Example Savings Account special rate 6.00%. "
                            "Offer valid from Nov 1 to Nov 30, 2023."
                        ),
                    ),
                    _match_dict(
                        field_name="account_interest_rates",
                        anchor_value="current-rates",
                        excerpt=(
                            "Savings account rates\nType\nCurrent rate (%)\n"
                            "Example Savings Account\n2.80\nTFSA Savings Account\n2.80\n"
                            "The rates in the table have been in effect since June 30, 2026."
                        ),
                    ),
                ]
            }
        }

        merged = merge_supporting_artifacts(
            target_source_id="AUTO-EXAMPLE-SAV-detail",
            base_artifact=base_artifact,
            supporting_artifacts={"AUTO-EXAMPLE-SAV-rates": supporting_artifact},
        )

        fields_by_name = {item["field_name"]: item for item in merged["extracted_fields"]}
        self.assertEqual(fields_by_name["standard_rate"]["candidate_value"], "2.80")
        self.assertEqual(fields_by_name["public_display_rate"]["candidate_value"], "2.80")

    def test_rate_fallback_does_not_reintroduce_expired_evidence(self) -> None:
        expired_link = NormalizationEvidenceLink(
            field_name="standard_rate",
            candidate_value="6.00",
            evidence_chunk_id="chunk-expired",
            evidence_text_excerpt=(
                "Special rate 6.00% for 1 Year GIC. "
                "Offer valid from Nov 1 to Nov 30, 2023."
            ),
            source_document_id="source-expired",
            source_snapshot_id="snapshot-expired",
            citation_confidence=0.9,
            model_execution_id=None,
            anchor_type="section",
            anchor_value="old-offer",
            page_no=None,
            chunk_index=1,
        )
        payload: dict[str, object] = {"product_name": "Example Savings Account"}

        from worker.pipeline.fpds_normalization.service import _apply_rate_evidence_fallback

        _apply_rate_evidence_fallback(
            product_type_family="savings",
            candidate_payload=payload,
            field_mapping_metadata={},
            normalized_values_for_links={},
            evidence_links_for_output=[expired_link],
            runtime_notes=[],
        )

        self.assertEqual(payload, {"product_name": "Example Savings Account"})

    def test_expired_detail_rates_are_removed_before_current_supporting_rate_merge(self) -> None:
        expired_excerpt = (
            "We're celebrating our anniversary with a special rate 6.00% for a 1 Year GIC. "
            "Offer valid from Nov 1 to Nov 30, 2023."
        )
        expired_fields = [
            _field_dict("standard_rate", "6.00", "decimal", 0.95),
            _field_dict("public_display_rate", "6.00", "decimal", 0.95),
            _field_dict("promotional_rate", "6.00", "decimal", 0.95),
            _field_dict(
                "term_rate_table",
                [{"term_label": "1 year", "term_length_days": 365, "rate": "6.00"}],
                "json",
                0.90,
            ),
            _field_dict("term_length_text", "1 year", "string", 0.90),
            _field_dict("term_length_days", 365, "integer", 0.90),
        ]
        for field in expired_fields:
            field["evidence_text_excerpt"] = expired_excerpt
        base_artifact = {
            "schema_context": {"product_type": "savings"},
            "extracted_fields": [
                _field_dict("product_name", "Example Savings Account", "string", 0.88),
                *expired_fields,
            ],
            "evidence_links": [],
            "runtime_notes": [],
        }
        supporting_artifact = {
            "retrieval_result": {
                "matches": [
                    _match_dict(
                        field_name="account_interest_rates",
                        anchor_value="current-rates",
                        excerpt="Example Savings Account current annual interest rate 2.80%",
                    )
                ]
            }
        }

        merged = merge_supporting_artifacts(
            target_source_id="AUTO-EXAMPLE-SAV-detail",
            base_artifact=base_artifact,
            supporting_artifacts={"AUTO-EXAMPLE-SAV-rates": supporting_artifact},
        )

        fields_by_name = {item["field_name"]: item for item in merged["extracted_fields"]}
        self.assertEqual(fields_by_name["standard_rate"]["candidate_value"], "2.80")
        self.assertEqual(fields_by_name["public_display_rate"]["candidate_value"], "2.80")
        self.assertNotIn("promotional_rate", fields_by_name)
        self.assertNotIn("term_rate_table", fields_by_name)
        self.assertNotIn("term_length_text", fields_by_name)
        self.assertNotIn("term_length_days", fields_by_name)
        self.assertIn("explicitly expired promotional offer", " ".join(merged["runtime_notes"]))

    def test_generic_supporting_merge_handles_generated_chequing_fee_source(self) -> None:
        base_artifact = {
            "schema_context": {"product_type": "chequing"},
            "extracted_fields": [
                _field_dict("product_name", "Basic Plus Bank Account", "string", 0.88),
            ],
            "evidence_links": [],
            "runtime_notes": [],
        }
        supporting_artifact = {
            "retrieval_result": {
                "matches": [
                    _match_dict(
                        field_name="monthly_fee",
                        anchor_value="basic-plus-bank-account",
                        excerpt=(
                            "Basic Plus Bank Account Monthly fee $11.95, waived with a $3,000 "
                            "minimum daily closing balance. Included transactions 25"
                        ),
                    )
                ]
            }
        }

        merged = merge_supporting_artifacts(
            target_source_id="AUTO-SCOTIABANK-CHE-42deb5bffb",
            base_artifact=base_artifact,
            supporting_artifacts={"AUTO-SCOTIABANK-CHE-c107b2ea47": supporting_artifact},
        )

        fields_by_name = {item["field_name"]: item for item in merged["extracted_fields"]}
        self.assertEqual(fields_by_name["monthly_fee"]["candidate_value"], "11.95")
        self.assertEqual(fields_by_name["public_display_fee"]["candidate_value"], "11.95")

    def test_generic_chequing_support_does_not_treat_waiver_balance_or_credit_as_fee(self) -> None:
        for excerpt in (
            "Basic Bank Account monthly account fee is waived with a minimum daily closing balance of $4,000.",
            "Student Banking Advantage Plan includes a $60 annual safety deposit box credit.",
        ):
            with self.subTest(excerpt=excerpt):
                base_artifact = {
                    "schema_context": {"product_type": "chequing"},
                    "extracted_fields": [_field_dict("product_name", "Basic Bank Account", "string", 0.88)],
                    "evidence_links": [],
                    "runtime_notes": [],
                }
                supporting_artifact = {
                    "retrieval_result": {
                        "matches": [
                            _match_dict(
                                field_name="account_comparison_rows",
                                anchor_value="basic-bank-account",
                                excerpt=excerpt,
                            )
                        ]
                    }
                }
                merged = merge_supporting_artifacts(
                    target_source_id="AUTO-BANK-CHE-basic",
                    base_artifact=base_artifact,
                    supporting_artifacts={"AUTO-BANK-CHE-comparison": supporting_artifact},
                )
                fields = {item["field_name"] for item in merged["extracted_fields"]}
                self.assertNotIn("monthly_fee", fields)
                self.assertNotIn("public_display_fee", fields)

    def test_generic_savings_rate_table_requires_target_product_identity(self) -> None:
        base_artifact = {
            "schema_context": {"product_type": "savings"},
            "extracted_fields": [_field_dict("product_name", "USD Savings Account", "string", 0.88)],
            "evidence_links": [],
            "runtime_notes": [],
        }
        supporting_artifact = {
            "retrieval_result": {
                "matches": [
                    _match_dict(
                        field_name="savings_account_rates",
                        anchor_value="current-rates",
                        excerpt="Regular Savings Account current annual interest rate 0.30%",
                    )
                ]
            }
        }
        merged = merge_supporting_artifacts(
            target_source_id="AUTO-BANK-SAV-usd",
            base_artifact=base_artifact,
            supporting_artifacts={"AUTO-BANK-SAV-rates": supporting_artifact},
        )
        fields = {item["field_name"] for item in merged["extracted_fields"]}
        self.assertNotIn("standard_rate", fields)
        self.assertNotIn("public_display_rate", fields)

    def test_generic_savings_support_rejects_explicit_foreign_currency_for_cad_target(self) -> None:
        base_artifact = {
            "schema_context": {"product_type": "savings"},
            "extracted_fields": [
                _field_dict("product_name", "Premium Rate Savings Account", "string", 0.88),
                _field_dict("currency", "CAD", "string", 0.99),
            ],
            "evidence_links": [],
            "runtime_notes": [],
        }
        supporting_artifact = {
            "retrieval_result": {
                "matches": [
                    _match_dict(
                        field_name="savings_account_rates",
                        anchor_value="u-s-dollar-premium-rate-savings-account",
                        excerpt=(
                            "U.S. Dollar Premium Rate Savings Account Balance Interest Rate "
                            "$0 and over 0.050%"
                        ),
                    )
                ]
            }
        }

        merged = merge_supporting_artifacts(
            target_source_id="AUTO-BANK-SAV-premium-cad",
            base_artifact=base_artifact,
            supporting_artifacts={"AUTO-BANK-SAV-premium-usd": supporting_artifact},
        )

        fields = {item["field_name"] for item in merged["extracted_fields"]}
        self.assertNotIn("standard_rate", fields)
        self.assertNotIn("public_display_rate", fields)

    def test_generic_savings_rate_table_scopes_regular_and_us_dollar_rows(self) -> None:
        supporting_artifact = {
            "retrieval_result": {
                "matches": [
                    _match_dict(
                        field_name="savings_account_rates",
                        anchor_value="current-rates",
                        excerpt=(
                            "Savings account rates\nType\nCurrent rate (%)\n"
                            "Savings Account\n0.30\nUS$ Savings Account\n0.10\nTFSA Savings Account\n0.30"
                        ),
                    )
                ]
            }
        }
        cases = (("Savings Account", "0.30"), ("U.S. Dollar Savings Account", "0.10"))
        for product_name, expected_rate in cases:
            with self.subTest(product_name=product_name):
                merged = merge_supporting_artifacts(
                    target_source_id=f"AUTO-BANK-SAV-{expected_rate}",
                    base_artifact={
                        "schema_context": {"product_type": "savings"},
                        "extracted_fields": [_field_dict("product_name", product_name, "string", 0.88)],
                        "evidence_links": [],
                        "runtime_notes": [],
                    },
                    supporting_artifacts={"AUTO-BANK-SAV-rates": supporting_artifact},
                )
                fields = {item["field_name"]: item for item in merged["extracted_fields"]}
                self.assertEqual(fields["standard_rate"]["candidate_value"], expected_rate)

    def test_generic_supporting_merge_handles_title_suffix_and_comparison_rows(self) -> None:
        base_artifact = {
            "schema_context": {"product_type": "chequing"},
            "extracted_fields": [
                _field_dict("product_name", "Ultimate Package | Scotiabank Canada", "string", 0.88),
            ],
            "evidence_links": [],
            "runtime_notes": [],
        }
        supporting_artifact = {
            "retrieval_result": {
                "matches": [
                    _match_dict(
                        field_name="account_comparison_rows",
                        anchor_value="chequing-account-comparison",
                        excerpt="Ultimate Package Monthly fee $30.95 Unlimited debit transactions",
                    )
                ]
            }
        }

        merged = merge_supporting_artifacts(
            target_source_id="AUTO-SCOTIABANK-CHE-3540807687",
            base_artifact=base_artifact,
            supporting_artifacts={"AUTO-SCOTIABANK-CHE-c107b2ea47": supporting_artifact},
        )

        fields_by_name = {item["field_name"]: item for item in merged["extracted_fields"]}
        self.assertEqual(fields_by_name["monthly_fee"]["candidate_value"], "30.95")
        self.assertEqual(fields_by_name["public_display_fee"]["candidate_value"], "30.95")

    def test_generic_chequing_comparison_restores_pdf_decimal_and_stops_before_next_row(self) -> None:
        base_artifact = {
            "schema_context": {"product_type": "chequing"},
            "extracted_fields": [_field_dict("product_name", "Ultimate Package", "string", 0.88)],
            "evidence_links": [],
            "runtime_notes": [],
        }
        supporting_artifact = {
            "retrieval_result": {
                "matches": [
                    _match_dict(
                        field_name="account_comparison_rows",
                        anchor_value="accounts-at-a-glance",
                        excerpt=(
                            "Basic Banking Account Basic Plus Bank Account Preferred Package Ultimate Package "
                            "Monthly Account Fee20 $3\ufffd95 $11\ufffd95 $16\ufffd95 $30\ufffd95 "
                            "Seniors' Discount ($3.95) ($4.00) ($4.00) ($7.00) "
                            "Minimum daily closing balance required for monthly account fee waiver21 "
                            "Not applicable $3,000 $4,0002 $6,0003"
                        ),
                    )
                ]
            }
        }

        merged = merge_supporting_artifacts(
            target_source_id="AUTO-BANK-CHE-ultimate",
            base_artifact=base_artifact,
            supporting_artifacts={"AUTO-BANK-CHE-fees-pdf": supporting_artifact},
        )

        fields_by_name = {item["field_name"]: item for item in merged["extracted_fields"]}
        self.assertEqual(fields_by_name["monthly_fee"]["candidate_value"], "30.95")
        self.assertEqual(fields_by_name["public_display_fee"]["candidate_value"], "30.95")

    def test_customer_field_cleanup_rejects_fee_waiver_and_ancillary_offer_copy(self) -> None:
        self.assertTrue(
            _looks_like_non_value_description(
                field_name="description_short",
                value=(
                    "A U.S. Dollar Premium Rate Savings Account functions like a regular savings account "
                    "where you can store money and earn interest, but with added perks. BMO’s U.S."
                ),
                product_type_family="savings",
                product_name="U.S. Dollar Premium Rate Savings Account",
            )
        )
        for description in (
            "Even though you don't need to maintain a minimum balance, you can waive the monthly account fee by holding a minimum balance.",
            "25 or over and can provide valid proof of enrolment for your Canadian post-secondary program.",
        ):
            with self.subTest(description=description):
                self.assertTrue(
                    _looks_like_non_value_description(
                        field_name="description_short",
                        value=description,
                        product_type_family="chequing",
                        product_name="Example Package",
                    )
                )

        for card_description in (
            "Credit card with a 7.99% introductory purchase rate for the first 6 months.",
            "Earn an additional 20,000 bonus Scene+ points when one purchase posts during the 14th month.",
            "Choose how to use your points. Your Scene+ account may be closed if you don't use your Scene+ membership for 24 consecutive months.",
            "Earn Scene+ points when you pay rent and condo fees online through the Casa platform.",
            "You can earn up to 5.00% for the first 3 months if you are not a current account holder and haven't held either account in the last two years.",
        ):
            with self.subTest(card_description=card_description):
                self.assertTrue(
                    _looks_like_non_value_description(
                        field_name="description_short",
                        value=card_description,
                        product_type_family="credit-card",
                        product_name="Example Card",
                    )
                )

        for eligibility in (
            "Only the following Visa Debit transaction types are eligible: online debit purchases. Click here for a list of eligible direct deposits and pre-authorized transactions.",
            "To qualify, the mortgage must be for a principal residence and the customer must set up preauthorized mortgage payments to receive preferred mortgage rates.",
            "The primary account holder qualifies for a monthly account fee waiver on a U.S. Dollar account. Both accounts must be in good standing to qualify.",
            "Offer Eligibility and Exclusions: individuals who were previously cardholders in the past 2 years are not eligible.",
            "Earn Scene+ points when you pay rent and housing-related bills through the Casa platform with your card.",
            "Right for you if you want credit for future needs, want to finance expenses, and want a rainy-day fund.",
        ):
            with self.subTest(eligibility=eligibility):
                self.assertTrue(
                    _looks_like_non_value_eligibility(
                        field_name="eligibility_text",
                        value=eligibility,
                        product_name="Example Package",
                    )
                )

        self.assertTrue(
            _looks_like_non_value_rewards(
                field_name="rewards_summary",
                value="Earn up to 1% cash back on eligible everyday purchases and 0.5% on all o",
            )
        )

        payload = {
            "withdrawal_limit_text": (
                "Legal 1 Symbol (optional) Legal Text Only teller-assisted debit and withdrawal "
                "transactions conducted at your branch of account are allowed on this account."
            )
        }
        _clean_product_context_fields(product_type_family="savings", candidate_payload=payload)
        self.assertEqual(
            payload["withdrawal_limit_text"],
            "Only teller-assisted debit and withdrawal transactions conducted at your branch of account are allowed on this account.",
        )
        self.assertEqual(
            _clean_deposit_insurance_value("Give us a call Eligible for CDIC Insurance 1 Regular Interest is paid monthly."),
            "Eligible for CDIC Insurance.",
        )
        self.assertEqual(
            _clean_deposit_insurance_value(
                "Simplii Financial is a division of CIBC, a CDIC member CDIC Deposit Insurance Information Opens a new window."
            ),
            "Simplii Financial is a division of CIBC, a CDIC member.",
        )
        self.assertEqual(
            _clean_deposit_insurance_value("GIC Simplii Financial is a division of CIBC, a CDIC member."),
            "Simplii Financial is a division of CIBC, a CDIC member.",
        )
        self.assertEqual(
            _clean_deposit_insurance_value(
                "Legal We are members of the Canada Deposit Insurance Corporation (CDIC) "
                "Explore our services Bank Accounts Credit Cards Mortgages Loans Investments"
            ),
            "We are members of the Canada Deposit Insurance Corporation (CDIC)",
        )
        self.assertEqual(
            _clean_deposit_insurance_value(
                "BOOK AN APPOINTMENT We are members of the Canada Deposit Insurance Corporation (CDIC) "
                "Explore our services Bank Accounts Credit Cards"
            ),
            "We are members of the Canada Deposit Insurance Corporation (CDIC)",
        )
        self.assertTrue(
            _looks_like_broad_page_copy(
                field_name="interest_calculation_method",
                value="Dollar Daily Interest Account A smart way to save your U.S.",
            )
        )
        self.assertTrue(
            _looks_like_broad_page_copy(
                field_name="tier_definition_text",
                value="Benefits Tiered interest up to 0.05% No monthly account fee for seniors Two free debit transactions per month No fee for U.S. drafts.",
            )
        )

        self.assertTrue(
            _looks_like_invalid_application_method(
                field_name="application_method",
                value="Mobile App, Online Banking, ABM, Access Card in-store, and cheques.",
                product_type_family="line-of-credit",
                context="Funds can be accessed through the Mobile App, Online Banking, ABM, Access Card, and cheques.",
            )
        )

    def test_generic_supporting_merge_handles_generated_gic_rate_source(self) -> None:
        base_artifact = {
            "schema_context": {"product_type": "gic-term-deposit"},
            "extracted_fields": [
                _field_dict("product_name", "Invest in Non-Cashable GICs", "string", 0.88),
                _field_dict("minimum_deposit", "1000.00", "decimal", 0.82, evidence_chunk_id="chunk-deposit"),
                _field_dict("term_length_text", "1 year", "string", 0.82, evidence_chunk_id="chunk-term"),
            ],
            "evidence_links": [],
            "runtime_notes": [],
        }
        supporting_artifact = {
            "retrieval_result": {
                "matches": [
                    _match_dict(
                        field_name="non_cashable_gic_rates",
                        anchor_value="non-cashable-gic-rates",
                        excerpt="Non-Cashable GICs 1 year 3.25%",
                    )
                ]
            }
        }

        merged = merge_supporting_artifacts(
            target_source_id="AUTO-TB-GIC-b04a2ca4b2",
            base_artifact=base_artifact,
            supporting_artifacts={"AUTO-TB-GIC-90ec9211ac": supporting_artifact},
        )

        fields_by_name = {item["field_name"]: item for item in merged["extracted_fields"]}
        self.assertEqual(fields_by_name["standard_rate"]["candidate_value"], "3.25")
        self.assertEqual(fields_by_name["public_display_rate"]["candidate_value"], "3.25")

    def test_generic_gic_family_support_merges_explicit_no_minimum_as_zero(self) -> None:
        base_artifact = {
            "schema_context": {"product_type": "gic"},
            "extracted_fields": [
                _field_dict("product_name", "RSP Guaranteed Investment", "string", 0.9),
                _field_dict("term_rate_table", [{"term_label": "1 Year", "rate": "3.15"}], "json", 0.9),
            ],
            "evidence_links": [],
            "runtime_notes": [],
        }
        supporting_artifact = {
            "retrieval_result": {
                "matches": [
                    _match_dict(
                        field_name="minimum_deposit",
                        anchor_value="gic-faq",
                        excerpt=(
                            "What's the minimum balance needed to open a GIC? "
                            "There's no minimum balance required to open an Example Bank GIC."
                        ),
                    )
                ]
            }
        }

        merged = merge_supporting_artifacts(
            target_source_id="AUTO-EXAMPLE-GIC-rsp",
            base_artifact=base_artifact,
            supporting_artifacts={"AUTO-EXAMPLE-GIC-overview": supporting_artifact},
        )

        fields_by_name = {item["field_name"]: item for item in merged["extracted_fields"]}
        self.assertEqual(fields_by_name["minimum_deposit"]["candidate_value"], "0.00")
        self.assertEqual(
            fields_by_name["minimum_deposit"]["extraction_method"],
            "generic_supporting_gic_minimum_merge",
        )

    def test_generic_gic_support_does_not_apply_variant_specific_minimum_to_other_products(self) -> None:
        base_artifact = {
            "schema_context": {"product_type": "gic"},
            "extracted_fields": [_field_dict("product_name", "RSP Guaranteed Investment", "string", 0.9)],
            "evidence_links": [],
            "runtime_notes": [],
        }
        supporting_artifact = {
            "retrieval_result": {
                "matches": [
                    _match_dict(
                        field_name="minimum_deposit",
                        anchor_value="special-gic",
                        excerpt="The 18 Month Special GIC has a minimum investment of $5,000.",
                    )
                ]
            }
        }

        merged = merge_supporting_artifacts(
            target_source_id="AUTO-EXAMPLE-GIC-rsp",
            base_artifact=base_artifact,
            supporting_artifacts={"AUTO-EXAMPLE-GIC-special": supporting_artifact},
        )

        self.assertNotIn("minimum_deposit", {item["field_name"] for item in merged["extracted_fields"]})

    def test_named_gic_ignores_unscoped_structured_table_for_another_product(self) -> None:
        base_artifact = {
            "schema_context": {"product_type": "gic"},
            "extracted_fields": [
                _field_dict("product_name", "Example Variable Rate GIC", "string", 0.92),
                _field_dict("term_length_text", "1 year", "string", 0.86, evidence_chunk_id="chunk-term"),
            ],
            "evidence_links": [],
            "runtime_notes": [],
        }
        supporting_artifact = {
            "retrieval_result": {
                "matches": [
                    _match_dict(
                        field_name="term_rate_table",
                        anchor_value="gic-calculator",
                        excerpt="Example Bonus Rate GIC Promotional Rate 1 year 2.70% Posted rate 2.45%.",
                    )
                ]
            }
        }

        merged = merge_supporting_artifacts(
            target_source_id="AUTO-EXAMPLE-GIC-variable",
            base_artifact=base_artifact,
            supporting_artifacts={"AUTO-EXAMPLE-GIC-calculator": supporting_artifact},
        )

        fields_by_name = {item["field_name"]: item for item in merged["extracted_fields"]}
        self.assertNotIn("standard_rate", fields_by_name)
        self.assertNotIn("public_display_rate", fields_by_name)
        self.assertNotIn("term_rate_table", fields_by_name)

    def test_generic_gic_family_page_accepts_scoped_structured_rate_table(self) -> None:
        unrelated_rate = _field_dict("standard_rate", "2.75", "decimal", 0.98, evidence_chunk_id="chunk-nav-rate")
        unrelated_rate["evidence_text_excerpt"] = "Personal Account bonus interest rate 2.75%"
        unrelated_display_rate = _field_dict("public_display_rate", "2.75", "decimal", 0.98, evidence_chunk_id="chunk-nav-rate")
        unrelated_display_rate["evidence_text_excerpt"] = "Personal Account bonus interest rate 2.75%"
        base_artifact = {
            "schema_context": {"product_type": "gic"},
            "extracted_fields": [
                _field_dict("product_name", "GICs | Example Bank", "string", 0.88),
                unrelated_rate,
                unrelated_display_rate,
            ],
            "evidence_links": [],
            "runtime_notes": [],
        }
        supporting_artifact = {
            "retrieval_result": {
                "matches": [
                    _match_dict(
                        field_name="term_rate_table",
                        anchor_value="notice-savings",
                        excerpt="10 Day Notice Savings Account 2.35% 30 Day Notice Savings Account 2.75%",
                    ),
                    _match_dict(
                        field_name="term_rate_table",
                        anchor_value="short-terms",
                        excerpt="Rate 3 Month 2.50% 6 Month 2.75% 9 Month 3.00%",
                    ),
                    _match_dict(
                        field_name="term_rate_table",
                        anchor_value="long-terms",
                        excerpt="Rate 1 Year 3.30% 2 Year 3.55% 5 Year 4.00% 5 Years 4.00%",
                    ),
                ]
            }
        }

        merged = merge_supporting_artifacts(
            target_source_id="AUTO-EXAMPLE-GIC-detail",
            base_artifact=base_artifact,
            supporting_artifacts={"AUTO-EXAMPLE-GIC-rates": supporting_artifact},
        )

        fields_by_name = {item["field_name"]: item for item in merged["extracted_fields"]}
        self.assertEqual(fields_by_name["standard_rate"]["candidate_value"], "3.30")
        self.assertEqual(fields_by_name["public_display_rate"]["candidate_value"], "3.30")
        self.assertEqual(fields_by_name["base_12_month_rate"]["candidate_value"], "3.30")
        self.assertEqual(
            [row["rate"] for row in fields_by_name["term_rate_table"]["candidate_value"]],
            ["2.50", "2.75", "3.00", "3.30", "3.55", "4.00"],
        )
        self.assertEqual(fields_by_name["term_rate_table"]["source_document_id"], "src-support-001")

    def test_generic_gic_family_page_parses_current_column_header_rate_table(self) -> None:
        expired_context = (
            "Special rate 6.00% 1 Year GIC. "
            "Offer valid from Nov 1 to Nov 30, 2023."
        )
        expired_rate = _field_dict("standard_rate", "6.00", "decimal", 0.91, evidence_chunk_id="chunk-expired")
        expired_rate["evidence_text_excerpt"] = expired_context
        expired_display = _field_dict("public_display_rate", "6.00", "decimal", 0.91, evidence_chunk_id="chunk-expired")
        expired_display["evidence_text_excerpt"] = expired_context
        base_artifact = {
            "schema_context": {"product_type": "gic"},
            "extracted_fields": [
                _field_dict("product_name", "Guaranteed Investment Certificates (GICs)", "string", 0.88),
                expired_rate,
                expired_display,
            ],
            "evidence_links": [],
            "runtime_notes": [],
        }
        supporting_artifact = {
            "retrieval_result": {
                "matches": [
                    _match_dict(
                        field_name="minimum_deposit",
                        anchor_value="our-gic-rates",
                        excerpt=(
                            "Our GIC rates\nYou'll find all of our current GIC rates here.\n"
                            "Long Term GICs\nTerm\nAnnual (%)\nSemi Annual (%)\nMonthly (%)\n"
                            "1 Year\n3.35\n3.30\n3.25\n18 Months\n3.45\n3.40\n3.35\n"
                            "2 Years\n3.65\n3.60\n3.55\n3 Years\n3.70\n3.65\n3.60\n"
                            "4 Years\n3.75\n3.70\n3.65\n5 Years\n4.00\n3.95\n3.90\n"
                            "Long-term GICs are non-redeemable and require a minimum deposit of $1,000.\n"
                            "Short Term GICs\nTerm\nRate (%)\n30-59 Days\n1.00\n60-89 Days\n1.00\n"
                            "90-119 Days\n1.00\n120-179 Days\n1.00\n180-269 Days\n2.25\n"
                            "270-364 Days\n2.70\nShort-term GICs are non-redeemable.\n"
                            "Cashable GICs\nTerm\nAfter 30 Days (%)\nAfter 90 Days (%)\n1 Year\n2.25\n"
                            "Cashable GICs require an initial investment of $1,000."
                        ),
                    )
                ]
            }
        }

        merged = merge_supporting_artifacts(
            target_source_id="AUTO-OAKEN-GIC-detail",
            base_artifact=base_artifact,
            supporting_artifacts={"AUTO-OAKEN-GIC-rates": supporting_artifact},
        )

        fields_by_name = {item["field_name"]: item for item in merged["extracted_fields"]}
        self.assertEqual(fields_by_name["standard_rate"]["candidate_value"], "3.35")
        self.assertEqual(fields_by_name["public_display_rate"]["candidate_value"], "3.35")
        self.assertEqual(fields_by_name["base_12_month_rate"]["candidate_value"], "3.35")
        self.assertEqual(fields_by_name["minimum_deposit"]["candidate_value"], "1000.00")
        rows = fields_by_name["term_rate_table"]["candidate_value"]
        self.assertEqual(len(rows), 13)
        self.assertEqual(rows[0]["notes"], "Long-term GIC annual interest rate")
        self.assertEqual(rows[0]["minimum_deposit"], "1000.00")
        self.assertEqual(rows[-1]["rate"], "2.25")
        self.assertEqual(rows[-1]["minimum_deposit"], "1000.00")
        self.assertIn("Cashable GIC", rows[-1]["notes"])

    def test_generic_gic_support_replaces_zero_placeholder_rates_for_bank_prefixed_title(self) -> None:
        zero_rows = [
            {
                "term_label": f"{year} year",
                "term_length_days": year * 365,
                "rate": "0.00",
                "minimum_deposit": "500.00",
                "notes": None,
            }
            for year in (1, 2, 3)
        ]
        base_artifact = {
            "schema_context": {"product_type": "gic-term-deposit"},
            "extracted_fields": [
                _field_dict("product_name", "Alterna Bank - eTerm Deposits", "string", 0.88),
                _field_dict("base_12_month_rate", "0.00", "decimal", 0.59, evidence_chunk_id="chunk-placeholder"),
                _field_dict("term_rate_table", zero_rows, "json", 0.55, evidence_chunk_id="chunk-placeholder"),
            ],
            "evidence_links": [],
            "runtime_notes": [],
        }
        supporting_artifact = {
            "retrieval_result": {
                "matches": [
                    _match_dict(
                        field_name="term_deposit_rates",
                        anchor_value="term-deposit-rates",
                        excerpt=(
                            "Term Deposit Rates eTerm Deposit Annual Interest Rates "
                            "1 Year 2.65% 2 Year 2.85% 3 Year 3.10% 4 Year 3.25% 5 Year 3.30%"
                        ),
                    )
                ]
            }
        }

        merged = merge_supporting_artifacts(
            target_source_id="AUTO-ALTERNA-GIC-5677039dfb",
            base_artifact=base_artifact,
            supporting_artifacts={"AUTO-ALTERNA-GIC-23f7460057": supporting_artifact},
        )

        fields_by_name = {item["field_name"]: item for item in merged["extracted_fields"]}
        self.assertEqual(fields_by_name["standard_rate"]["candidate_value"], "2.65")
        self.assertEqual(fields_by_name["public_display_rate"]["candidate_value"], "2.65")
        self.assertEqual(fields_by_name["base_12_month_rate"]["candidate_value"], "2.65")
        self.assertEqual(
            [row["rate"] for row in fields_by_name["term_rate_table"]["candidate_value"]],
            ["2.65", "2.85", "3.10", "3.25", "3.30"],
        )
        self.assertTrue(fields_by_name["term_rate_table"]["field_metadata"]["generic_supporting_merge"])

    def test_generic_supporting_merge_accepts_generated_gic_rate_table_fields(self) -> None:
        base_artifact = {
            "schema_context": {"product_type": "gic-term-deposit"},
            "extracted_fields": [
                _field_dict("product_name", "TD Special Offer GICs", "string", 0.88),
                _field_dict("minimum_deposit", "1000.00", "decimal", 0.82, evidence_chunk_id="chunk-deposit"),
                _field_dict("term_length_text", "100 days", "string", 0.82, evidence_chunk_id="chunk-term"),
            ],
            "evidence_links": [],
            "runtime_notes": [],
        }
        supporting_artifact = {
            "retrieval_result": {
                "matches": [
                    _match_dict(
                        field_name="gic_rates",
                        anchor_value="gic-rates-canada",
                        excerpt="TD Special Offer GICs 100 days 3.250%",
                    )
                ]
            }
        }

        merged = merge_supporting_artifacts(
            target_source_id="AUTO-TB-GIC-266530658a",
            base_artifact=base_artifact,
            supporting_artifacts={"AUTO-TB-GIC-90ec9211ac": supporting_artifact},
        )

        fields_by_name = {item["field_name"]: item for item in merged["extracted_fields"]}
        self.assertEqual(fields_by_name["standard_rate"]["candidate_value"], "3.25")
        self.assertEqual(fields_by_name["public_display_rate"]["candidate_value"], "3.25")

    def test_generic_supporting_merge_ignores_market_linked_return_cap_context(self) -> None:
        base_artifact = {
            "schema_context": {"product_type": "gic"},
            "extracted_fields": [
                _field_dict("product_name", "Scotiabank Market Linked GICs", "string", 0.88),
                _field_dict("minimum_deposit", "500.00", "decimal", 0.82, evidence_chunk_id="chunk-deposit"),
                _field_dict("term_length_text", "3 years", "string", 0.82, evidence_chunk_id="chunk-term"),
            ],
            "evidence_links": [],
            "runtime_notes": [],
        }
        supporting_artifact = {
            "retrieval_result": {
                "matches": [
                    _match_dict(
                        field_name="maximum_return",
                        anchor_value="market-linked-gic-returns",
                        excerpt=(
                            "Scotiabank Market Linked GICs principal is guaranteed and Index Return is based on "
                            "the performance of the Underlying Index. Limitation on interest: the total return "
                            "cannot exceed an average of 60% per year."
                        ),
                    )
                ]
            }
        }

        merged = merge_supporting_artifacts(
            target_source_id="AUTO-SCOTIA-GIC-market-linked",
            base_artifact=base_artifact,
            supporting_artifacts={"AUTO-SCOTIA-GIC-market-linked-support": supporting_artifact},
        )

        fields_by_name = {item["field_name"]: item for item in merged["extracted_fields"]}
        self.assertNotIn("standard_rate", fields_by_name)
        self.assertNotIn("public_display_rate", fields_by_name)

    def test_merge_supports_everyday_rate_fields_from_current_rates(self) -> None:
        base_artifact = {
            "extracted_fields": [
                _field_dict("product_name", "TD Every Day Savings Account", "string", 0.88),
                _field_dict("monthly_fee", "0.00", "decimal", 0.83, evidence_chunk_id="chunk-detail-fee"),
            ],
            "evidence_links": [],
            "runtime_notes": [],
        }
        supporting_artifact = {
            "retrieval_result": {
                "matches": [
                    _match_dict(
                        field_name="standard_rate",
                        anchor_value="td-every-day-savings-account-1",
                        excerpt=(
                            "TD Every Day Savings Account 1\n"
                            "Total Daily Closing Balance\n"
                            "Interest Rate\n"
                            "$0 to $999.99\n"
                            "0.010%\n"
                            "$1,000.00 to $4,999.99\n"
                            "0.010%"
                        ),
                    )
                ]
            }
        }

        merged = merge_supporting_artifacts(
            target_source_id="TD-SAV-002",
            base_artifact=base_artifact,
            supporting_artifacts={"TD-SAV-005": supporting_artifact},
        )

        fields_by_name = {item["field_name"]: item for item in merged["extracted_fields"]}
        self.assertEqual(fields_by_name["standard_rate"]["candidate_value"], "0.01")
        self.assertEqual(fields_by_name["public_display_rate"]["candidate_value"], "0.01")
        self.assertIn("Supplemented missing savings rate fields", " ".join(merged["runtime_notes"]))

    def test_merge_supports_bmo_savings_amplifier_rates_from_rate_page(self) -> None:
        base_artifact = {
            "extracted_fields": [
                _field_dict("product_name", "Savings Amplifier Account", "string", 0.88),
                _field_dict("monthly_fee", "0.00", "decimal", 0.83, evidence_chunk_id="chunk-detail-fee"),
            ],
            "evidence_links": [],
            "runtime_notes": [],
        }
        supporting_artifact = {
            "retrieval_result": {
                "matches": [
                    _match_dict(
                        field_name="savings_account_rates",
                        anchor_value="savings-amplifier-account",
                        excerpt=(
                            "Savings Amplifier Account\n"
                            "Balance Interest Rate\n"
                            "$0 and over\n"
                            "0.500%"
                        ),
                    )
                ]
            }
        }

        merged = merge_supporting_artifacts(
            target_source_id="BMO-SAV-002",
            base_artifact=base_artifact,
            supporting_artifacts={"BMO-SAV-006": supporting_artifact},
        )

        fields_by_name = {item["field_name"]: item for item in merged["extracted_fields"]}
        self.assertEqual(fields_by_name["standard_rate"]["candidate_value"], "0.50")
        self.assertEqual(fields_by_name["public_display_rate"]["candidate_value"], "0.50")
        self.assertEqual(fields_by_name["standard_rate"]["field_metadata"]["supporting_source_id"], "BMO-SAV-006")
        self.assertIn("BMO-SAV-006", " ".join(merged["runtime_notes"]))

    def test_merge_supports_bmo_savings_builder_rates_from_rate_page(self) -> None:
        base_artifact = {
            "extracted_fields": [
                _field_dict("product_name", "Savings Builder Account", "string", 0.88),
                _field_dict("monthly_fee", "0.00", "decimal", 0.83, evidence_chunk_id="chunk-detail-fee"),
                _field_dict(
                    "bonus_interest_rule",
                    "Get a bonus interest rate for adding $200 each month.",
                    "string",
                    0.55,
                    evidence_chunk_id="chunk-builder-bonus",
                ),
            ],
            "evidence_links": [],
            "runtime_notes": [],
        }
        supporting_artifact = {
            "retrieval_result": {
                "matches": [
                    _match_dict(
                        field_name="savings_account_rates",
                        anchor_value="savings-builder-account",
                        excerpt=(
                            "Savings Builder Account\n"
                            "Balance Interest Rate\n"
                            "$0 and over\n"
                            "0.500%"
                        ),
                    )
                ]
            }
        }

        merged = merge_supporting_artifacts(
            target_source_id="BMO-SAV-003",
            base_artifact=base_artifact,
            supporting_artifacts={"BMO-SAV-006": supporting_artifact},
        )

        fields_by_name = {item["field_name"]: item for item in merged["extracted_fields"]}
        self.assertEqual(fields_by_name["standard_rate"]["candidate_value"], "0.50")
        self.assertEqual(fields_by_name["public_display_rate"]["candidate_value"], "0.50")
        self.assertEqual(fields_by_name["standard_rate"]["field_metadata"]["supporting_source_id"], "BMO-SAV-006")
        self.assertEqual(fields_by_name["bonus_interest_rule"]["candidate_value"], "Get a bonus interest rate for adding $200 each month.")

    def test_bmo_supporting_rate_page_missing_numeric_rate_adds_operator_note(self) -> None:
        base_artifact = {
            "extracted_fields": [
                _field_dict("product_name", "Savings Amplifier Account", "string", 0.88),
                _field_dict("monthly_fee", "0.00", "decimal", 0.83, evidence_chunk_id="chunk-detail-fee"),
            ],
            "evidence_links": [],
            "runtime_notes": [],
        }
        supporting_artifact = {
            "retrieval_result": {
                "matches": [
                    _match_dict(
                        field_name="savings_account_rates",
                        anchor_value="savings-amplifier-account",
                        excerpt="Savings Amplifier Account\nBalance Interest Rate\nThe current interest rate is not displayed.",
                    )
                ]
            }
        }

        merged = merge_supporting_artifacts(
            target_source_id="BMO-SAV-002",
            base_artifact=base_artifact,
            supporting_artifacts={"BMO-SAV-006": supporting_artifact},
        )

        fields_by_name = {item["field_name"]: item for item in merged["extracted_fields"]}
        self.assertNotIn("standard_rate", fields_by_name)
        self.assertIn("did not contain a numeric percentage", " ".join(merged["runtime_notes"]))

    def test_merge_supports_bmo_premium_rate_savings_rates_from_rate_page(self) -> None:
        base_artifact = {
            "extracted_fields": [
                _field_dict("product_name", "Premium Rate Savings Account", "string", 0.88),
                _field_dict(
                    "withdrawal_limit_text",
                    "Transaction limits are shared with the linked BMO chequing plan.",
                    "string",
                    0.75,
                    evidence_chunk_id="chunk-detail-transactions",
                ),
            ],
            "evidence_links": [],
            "runtime_notes": [],
        }
        supporting_artifact = {
            "retrieval_result": {
                "matches": [
                    _match_dict(
                        field_name="savings_account_rates",
                        anchor_value="premium-rate-savings-account",
                        excerpt=(
                            "Premium Rate Savings Account\n"
                            "Balance Interest Rate\n"
                            "$0 and over\n"
                            "0.010%"
                        ),
                    )
                ]
            }
        }

        merged = merge_supporting_artifacts(
            target_source_id="BMO-SAV-004",
            base_artifact=base_artifact,
            supporting_artifacts={"BMO-SAV-006": supporting_artifact},
        )

        fields_by_name = {item["field_name"]: item for item in merged["extracted_fields"]}
        self.assertEqual(fields_by_name["standard_rate"]["candidate_value"], "0.01")
        self.assertEqual(fields_by_name["public_display_rate"]["candidate_value"], "0.01")
        self.assertEqual(fields_by_name["standard_rate"]["field_metadata"]["supporting_source_id"], "BMO-SAV-006")
        self.assertIn("BMO-SAV-006", " ".join(merged["runtime_notes"]))

    def test_merge_supports_cibc_us_personal_rates_from_rate_page(self) -> None:
        base_artifact = {
            "extracted_fields": [
                _field_dict("product_name", "CIBC US$ Personal Account", "string", 0.88),
                _field_dict("monthly_fee", "0.00", "decimal", 0.83, evidence_chunk_id="chunk-detail-fee"),
                _field_dict(
                    "eligibility_text",
                    "You're a Canadian resident and you've reached the age of majority in your province or territory",
                    "string",
                    0.72,
                    evidence_chunk_id="chunk-detail-eligibility",
                ),
            ],
            "evidence_links": [],
            "runtime_notes": [],
        }
        supporting_artifact = {
            "retrieval_result": {
                "matches": [
                    _match_dict(
                        field_name="savings_account_rates",
                        anchor_value="cibc-us-personal-account",
                        excerpt=(
                            "CIBC US$ Personal Account\n"
                            "Daily Closing Balance Regular Interest Rate\n"
                            "Balance up to $2,999.99 0.01%\n"
                            "Balance $3,000 to $9,999.99 0.05%\n"
                            "On portion of balances $60,000 and over 0.10%"
                        ),
                    )
                ]
            }
        }

        merged = merge_supporting_artifacts(
            target_source_id="CIBC-SAV-003",
            base_artifact=base_artifact,
            supporting_artifacts={"CIBC-SAV-004": supporting_artifact},
        )

        fields_by_name = {item["field_name"]: item for item in merged["extracted_fields"]}
        self.assertEqual(fields_by_name["standard_rate"]["candidate_value"], "0.10")
        self.assertEqual(fields_by_name["public_display_rate"]["candidate_value"], "0.10")
        self.assertEqual(fields_by_name["standard_rate"]["field_metadata"]["supporting_source_id"], "CIBC-SAV-004")
        self.assertIn("CIBC-SAV-004", " ".join(merged["runtime_notes"]))

    def test_cibc_eadvantage_supporting_rate_page_missing_numeric_rate_adds_operator_note(self) -> None:
        base_artifact = {
            "extracted_fields": [
                _field_dict("product_name", "CIBC eAdvantage Savings Account", "string", 0.88),
                _field_dict("monthly_fee", "0.00", "decimal", 0.83, evidence_chunk_id="chunk-detail-fee"),
                _field_dict(
                    "eligibility_text",
                    "You're a Canadian resident and you've reached the age of majority in your province or territory",
                    "string",
                    0.72,
                    evidence_chunk_id="chunk-detail-eligibility",
                ),
            ],
            "evidence_links": [],
            "runtime_notes": [],
        }
        supporting_artifact = {
            "retrieval_result": {
                "matches": [
                    _match_dict(
                        field_name="savings_account_rates",
                        anchor_value="cibc-eadvantage-savings-account",
                        excerpt=(
                            "CIBC eAdvantage Savings Account\n"
                            "Daily Closing Balance Regular Interest Rate\n"
                            "Balance up to $9,999.99 RDS%rate[3].CESA.Published(null,0.0_-_9999.99_CAD_Balance,1,1)(#O2#)%\n"
                            "Balance $500,000 and over RDS%rate[3].CESA.Published(null,500000.0_and over_0.0_CAD_Balance,1,1)(#O2#)%"
                        ),
                    )
                ]
            }
        }

        merged = merge_supporting_artifacts(
            target_source_id="CIBC-SAV-002",
            base_artifact=base_artifact,
            supporting_artifacts={"CIBC-SAV-004": supporting_artifact},
        )

        fields_by_name = {item["field_name"]: item for item in merged["extracted_fields"]}
        self.assertNotIn("standard_rate", fields_by_name)
        self.assertIn("did not contain a numeric percentage", " ".join(merged["runtime_notes"]))

    def test_cibc_supporting_rate_page_missing_numeric_rate_adds_operator_note(self) -> None:
        base_artifact = {
            "extracted_fields": [
                _field_dict("product_name", "CIBC US$ Personal Account", "string", 0.88),
                _field_dict("monthly_fee", "0.00", "decimal", 0.83, evidence_chunk_id="chunk-detail-fee"),
            ],
            "evidence_links": [],
            "runtime_notes": [],
        }
        supporting_artifact = {
            "retrieval_result": {
                "matches": [
                    _match_dict(
                        field_name="tier_definition_text",
                        anchor_value="cibc-us-personal-account",
                        excerpt=(
                            "CIBC US$ Personal Account\n"
                            "Daily Closing Balance Regular Interest Rate\n"
                            "Balance up to $2,999.99 RDS%rate[3].CUPA.rate(null,0.0_up to_2999.99_CAD_Balance,1,1)(#O2#)%"
                        ),
                    )
                ]
            }
        }

        merged = merge_supporting_artifacts(
            target_source_id="CIBC-SAV-003",
            base_artifact=base_artifact,
            supporting_artifacts={"CIBC-SAV-004": supporting_artifact},
        )

        fields_by_name = {item["field_name"]: item for item in merged["extracted_fields"]}
        self.assertNotIn("standard_rate", fields_by_name)
        self.assertIn("did not contain a numeric percentage", " ".join(merged["runtime_notes"]))

    def test_merge_supports_growth_rate_fields_from_current_rates(self) -> None:
        base_artifact = {
            "extracted_fields": [
                _field_dict("product_name", "TD Growth Savings Account", "string", 0.88),
            ],
            "evidence_links": [],
            "runtime_notes": [],
        }
        supporting_artifact = {
            "retrieval_result": {
                "matches": [
                    _match_dict(
                        field_name="rate_tiers",
                        anchor_value="td-growth-savings-account-6",
                        excerpt=(
                            "TD Growth Savings Account 6\n"
                            "Daily Closing Balance Tiers\n"
                            "Boosted Rate 6\n"
                            "Standard Posted Rate\n"
                            "$0 to $4,999.99\n"
                            "0.00%\n"
                            "$5,000.00 to $9,999.99\n"
                            "0.50%\n"
                            "0.00%\n"
                            "$10,000 to $99,999.99\n"
                            "1.00%\n"
                            "0.40%\n"
                            "$100,000.00 to $499,999.99\n"
                            "1.30%\n"
                            "0.55%\n"
                            "$500,000.00 and over\n"
                            "1.50%\n"
                            "0.65%"
                        ),
                    )
                ]
            }
        }

        merged = merge_supporting_artifacts(
            target_source_id="TD-SAV-004",
            base_artifact=base_artifact,
            supporting_artifacts={"TD-SAV-005": supporting_artifact},
        )

        fields_by_name = {item["field_name"]: item for item in merged["extracted_fields"]}
        self.assertEqual(fields_by_name["standard_rate"]["candidate_value"], "0.65")
        self.assertEqual(fields_by_name["public_display_rate"]["candidate_value"], "1.50")
        self.assertEqual(fields_by_name["promotional_rate"]["candidate_value"], "1.50")
        self.assertTrue(fields_by_name["tiered_rate_flag"]["candidate_value"])
        self.assertIn("$500,000.00 and over: 1.50% / 0.65%", fields_by_name["tier_definition_text"]["candidate_value"])

    def test_generic_chequing_comparison_maps_fee_and_waiver_to_target_column(self) -> None:
        comparison = (
            "What is the fee or rebate? "
            "TD All-Inclusive Banking Plan TD Unlimited Chequing Account "
            "TD Every Day Chequing Account TD Minimum Chequing Account TD Student Chequing Account "
            "Monthly fee $30.95 or $0 (with a minimum daily account balance of $6,000). "
            "$17.95 or $0 (with a minimum daily account balance of $4,000). "
            "$11.95 or $0 (with a minimum daily account balance of $3,000). "
            "$3.95 ($0 if you receive an eligible benefit) $0 "
            "Monthly Fee for Seniors over 60 $22.45 or $0."
        )
        supporting_artifact = {
            "retrieval_result": {
                "matches": [
                    _match_dict(
                        field_name="account_fee_table",
                        anchor_value="fees",
                        excerpt=comparison,
                    )
                ]
            }
        }
        cases = (
            ("TD All-Inclusive Banking Plan", "30.95", "6000"),
            ("TD Every Day Chequing Account", "11.95", "3000"),
            ("TD Student Chequing Account", "0", None),
        )
        for product_name, expected_fee, expected_balance in cases:
            with self.subTest(product_name=product_name):
                merged = merge_supporting_artifacts(
                    target_source_id=f"AUTO-{product_name}",
                    base_artifact={
                        "schema_context": {"product_type": "chequing"},
                        "extracted_fields": [_field_dict("product_name", product_name, "string", 0.88)],
                        "evidence_links": [],
                        "runtime_notes": [],
                    },
                    supporting_artifacts={"AUTO-FEES": supporting_artifact},
                )
                fields = {item["field_name"]: item["candidate_value"] for item in merged["extracted_fields"]}
                self.assertEqual(fields["monthly_fee"], expected_fee)
                self.assertEqual(fields["public_display_fee"], expected_fee)
                if expected_balance is None:
                    self.assertNotIn("minimum_balance", fields)
                    self.assertNotIn("fee_waiver_condition", fields)
                else:
                    self.assertEqual(fields["minimum_balance"], expected_balance)
                    self.assertIn(expected_balance, fields["fee_waiver_condition"])

    def test_generic_savings_rate_merge_preserves_material_balance_tiers(self) -> None:
        merged = merge_supporting_artifacts(
            target_source_id="AUTO-EPREMIUM",
            base_artifact={
                "schema_context": {"product_type": "savings"},
                "extracted_fields": [
                    _field_dict("product_name", "Example ePremium Savings Account", "string", 0.88),
                ],
                "evidence_links": [],
                "runtime_notes": [],
            },
            supporting_artifacts={
                "AUTO-RATES": {
                    "retrieval_result": {
                        "matches": [
                            _match_dict(
                                field_name="savings_rate_table",
                                anchor_value="example-epremium-savings-account",
                                excerpt=(
                                    "Example ePremium Savings Account Total Daily Closing Balance Interest Rate "
                                    "$0 to $9,999.99 0.000% $10,000.00 to $49,999.99 0.450% "
                                    "$50,000.00 to $99,999.99 0.450% $100,000.00 and over 0.450%"
                                ),
                            )
                        ]
                    }
                }
            },
        )

        fields = {item["field_name"]: item["candidate_value"] for item in merged["extracted_fields"]}
        self.assertEqual(fields["standard_rate"], "0.45")
        self.assertTrue(fields["tiered_rate_flag"])
        self.assertIn("$0 to $9,999.99: 0.000%", fields["tier_definition_text"])
        self.assertIn("$10,000.00 to $49,999.99: 0.450%", fields["tier_definition_text"])

    def test_generic_chequing_support_preserves_explicit_account_wide_unlimited_fact(self) -> None:
        merged = merge_supporting_artifacts(
            target_source_id="AUTO-PERFORMANCE",
            base_artifact={
                "schema_context": {"product_type": "chequing"},
                "extracted_fields": [
                    _field_dict("product_name", "Performance Chequing Account", "string", 0.88),
                    _field_dict("monthly_fee", "17.95", "decimal", 0.82),
                    _field_dict("public_display_fee", "17.95", "decimal", 0.82),
                    _field_dict("minimum_balance", "4000", "decimal", 0.82),
                    _field_dict(
                        "fee_waiver_condition",
                        "Monthly fee 17.95 is waived to 0.00 with a 4000 minimum balance.",
                        "string",
                        0.82,
                    ),
                ],
                "evidence_links": [],
                "runtime_notes": [],
            },
            supporting_artifacts={
                "AUTO-ACCOUNT-TERMS": {
                    "retrieval_result": {
                        "matches": [
                            _match_dict(
                                field_name="account_fee_table",
                                anchor_value="transactions",
                                excerpt=(
                                    "Get unlimited monthly transactions with the Premium Chequing Account, "
                                    "the Performance Chequing Account and the Blue Rewards Chequing Account."
                                ),
                            )
                        ]
                    }
                }
            },
        )

        fields = {item["field_name"]: item["candidate_value"] for item in merged["extracted_fields"]}
        self.assertTrue(fields["unlimited_transactions_flag"])

    def test_interest_pdf_replaces_noisy_detail_fields(self) -> None:
        base_artifact = {
            "extracted_fields": [
                _field_dict("product_name", "TD Every Day Savings Account", "string", 0.88),
                _field_dict(
                    "interest_calculation_method",
                    "Account Interest Rates How Our Interest is Calculated (PDF) Account and Other Related Service Fees (PDF)",
                    "string",
                    0.62,
                    evidence_chunk_id="chunk-detail-interest",
                ),
            ],
            "evidence_links": [
                _evidence(
                    "interest_calculation_method",
                    "Account Interest Rates How Our Interest is Calculated (PDF) Account and Other Related Service Fees (PDF)",
                    "chunk-detail-interest",
                ).__dict__.copy(),
            ],
            "runtime_notes": [],
        }
        supporting_artifact = {
            "retrieval_result": {
                "matches": [
                    _match_dict(
                        field_name="interest_calculation_method",
                        anchor_value="page-2",
                        excerpt="Interest will be calculated on the daily closing balance in your account.",
                    ),
                    _match_dict(
                        field_name="interest_payment_frequency",
                        anchor_value="page-8",
                        excerpt="Interest is paid monthly instead.",
                    ),
                ]
            }
        }

        merged = merge_supporting_artifacts(
            target_source_id="TD-SAV-002",
            base_artifact=base_artifact,
            supporting_artifacts={"TD-SAV-008": supporting_artifact},
        )

        fields_by_name = {item["field_name"]: item for item in merged["extracted_fields"]}
        self.assertEqual(fields_by_name["interest_calculation_method"]["candidate_value"], "Interest is calculated on the daily closing balance.")
        self.assertEqual(fields_by_name["interest_payment_frequency"]["candidate_value"], "monthly")
        self.assertIn("TD-SAV-008", " ".join(merged["runtime_notes"]))

    def test_fee_pdf_suppresses_zero_fee_savings_fee_waiver_text(self) -> None:
        base_artifact = {
            "extracted_fields": [
                _field_dict("product_name", "TD Every Day Savings Account", "string", 0.88),
                _field_dict("monthly_fee", "0.00", "decimal", 0.83, evidence_chunk_id="chunk-detail-fee"),
                _field_dict(
                    "fee_waiver_condition",
                    "Account Fees Monthly Fee $0 Transactions included per month 1 Additional Transactions $3.00 each Free Transfers to your other TD accounts Unlimited",
                    "string",
                    0.55,
                    evidence_chunk_id="chunk-detail-waiver",
                ),
            ],
            "evidence_links": [
                _evidence(
                    "fee_waiver_condition",
                    "Account Fees Monthly Fee $0 Transactions included per month 1 Additional Transactions $3.00 each Free Transfers to your other TD accounts Unlimited",
                    "chunk-detail-waiver",
                ).__dict__.copy(),
            ],
            "runtime_notes": [],
        }
        supporting_artifact = {
            "retrieval_result": {
                "matches": [
                    _match_dict(
                        field_name="fee_waiver_condition",
                        anchor_value="page-2",
                        excerpt=(
                            "For some of our accounts we will refund the fee if you maintain the required Daily Closing Balance "
                            "on each business day of the month."
                        ),
                    )
                ]
            }
        }

        merged = merge_supporting_artifacts(
            target_source_id="TD-SAV-002",
            base_artifact=base_artifact,
            supporting_artifacts={"TD-SAV-007": supporting_artifact},
        )

        fields_by_name = {item["field_name"]: item for item in merged["extracted_fields"]}
        self.assertNotIn("fee_waiver_condition", fields_by_name)
        self.assertIn("TD-SAV-007", " ".join(merged["runtime_notes"]))
        self.assertIn("already $0", " ".join(merged["runtime_notes"]))

    def test_growth_cleanup_splits_qualification_and_suppresses_marketing_copy(self) -> None:
        base_artifact = {
            "extracted_fields": [
                _field_dict("product_name", "TD Growth Savings Account", "string", 0.88),
                _field_dict(
                    "eligibility_text",
                    "Bank accounts and fees at a glance This is a simple overview of our most common fees.",
                    "string",
                    0.58,
                    evidence_chunk_id="chunk-generic-eligibility",
                ),
                _field_dict(
                    "promotional_period_text",
                    "Whether you're saving for the future or for a large purchase, we can help you achieve your goals.",
                    "string",
                    0.58,
                    evidence_chunk_id="chunk-marketing-promo",
                ),
                _field_dict(
                    "boosted_rate_eligibility",
                    "Boosted Rate Eligibility Earn the Boosted rate 1 on your savings for the next month! Here's how to qualify.",
                    "string",
                    0.76,
                    evidence_chunk_id="chunk-growth-qualification",
                ),
            ],
            "evidence_links": [],
            "runtime_notes": [],
        }
        base_artifact["extracted_fields"][3]["evidence_text_excerpt"] = (
            "Boosted Rate Eligibility\n"
            "Earn the Boosted rate on your savings for the next month! Here's how to qualify:\n"
            "1 Maintain an eligible TD Chequing Account\n"
            "2 Complete at least 2 out of the 3 Qualifying Monthly Transactions"
        )
        supporting_artifact = {
            "retrieval_result": {
                "matches": [
                    _match_dict(
                        field_name="interest_calculation_method",
                        anchor_value="page-2",
                        excerpt="Interest will be calculated on the daily closing balance in your account.",
                    ),
                    _match_dict(
                        field_name="tier_definition_text",
                        anchor_value="page-2",
                        excerpt="Interest is paid on each daily closing balance tier according to the applicable balance tier.",
                    ),
                ]
            }
        }

        merged = merge_supporting_artifacts(
            target_source_id="TD-SAV-004",
            base_artifact=base_artifact,
            supporting_artifacts={"TD-SAV-008": supporting_artifact},
        )

        fields_by_name = {item["field_name"]: item for item in merged["extracted_fields"]}
        self.assertEqual(
            fields_by_name["eligibility_text"]["candidate_value"],
            "Maintain an eligible TD Chequing Account and complete at least 2 of 3 qualifying monthly transactions.",
        )
        self.assertEqual(
            fields_by_name["boosted_rate_eligibility"]["candidate_value"],
            "Maintain an eligible TD Chequing Account and complete at least 2 of 3 qualifying monthly transactions to earn the Boosted rate for the next month.",
        )
        self.assertEqual(
            fields_by_name["promotional_period_text"]["candidate_value"],
            "Meeting the qualification criteria earns the Boosted rate for the next month.",
        )
        self.assertEqual(
            fields_by_name["interest_calculation_method"]["candidate_value"],
            "Interest is calculated on the daily closing balance.",
        )
        self.assertNotIn("notes", fields_by_name)

    def test_merge_supports_scotia_money_master_rates_from_rate_page(self) -> None:
        base_artifact = {
            "extracted_fields": [
                _field_dict("product_name", "Money Master Savings Account", "string", 0.88),
                _field_dict("monthly_fee", "0.00", "decimal", 0.84, evidence_chunk_id="chunk-detail-fee"),
            ],
            "evidence_links": [],
            "runtime_notes": [],
        }
        supporting_artifact = {
            "retrieval_result": {
                "matches": [
                    _match_dict(
                        field_name="savings_account_rates",
                        anchor_value="money-master-savings-account",
                        excerpt=(
                            "Money Master Savings Account\n"
                            "Annual Interest Rate\n"
                            "0.01%\n"
                            "Annual Interest Rate with Bonus Interest Rate if enrolled in Smart Savings tools\n"
                            "0.50%"
                        ),
                    )
                ]
            }
        }

        merged = merge_supporting_artifacts(
            target_source_id="SCOTIA-SAV-004",
            base_artifact=base_artifact,
            supporting_artifacts={"SCOTIA-SAV-006": supporting_artifact},
        )

        fields_by_name = {item["field_name"]: item for item in merged["extracted_fields"]}
        self.assertEqual(fields_by_name["standard_rate"]["candidate_value"], "0.01")
        self.assertEqual(fields_by_name["public_display_rate"]["candidate_value"], "0.50")
        self.assertIn("SCOTIA-SAV-006", " ".join(merged["runtime_notes"]))


class NormalizationPersistenceTests(unittest.TestCase):
    def test_load_latest_extraction_artifacts_reads_joined_rows(self) -> None:
        runner = _FakeRunner(
            outputs=[
                "public",
                json.dumps(
                    [
                        {
                            "source_document_id": "src-001",
                            "snapshot_id": "snap-001",
                            "parsed_document_id": "parsed-001",
                            "extraction_model_execution_id": "modelexec-extract-001",
                            "extracted_storage_key": "dev/extracted/CA/TD/src-001/parsed-001/extracted.json",
                            "extraction_metadata_storage_key": "dev/extracted/CA/TD/src-001/parsed-001/metadata.json",
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
        repository = PsqlNormalizationRepository(
            NormalizationDatabaseConfig(database_url="postgres://example", schema="public"),
            command_runner=runner,
        )

        result = repository.load_latest_extraction_artifacts(run_id="run-001", source_document_ids=["src-001"])

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].parsed_document_id, "parsed-001")
        self.assertEqual(runner.last_variables()["run_id"], "run-001")
        self.assertEqual(json.loads(runner.last_variables()["source_document_ids_json"]), ["src-001"])

    def test_persist_normalization_result_updates_candidate_and_links(self) -> None:
        runner = _FakeRunner(outputs=["public", ""])
        repository = PsqlNormalizationRepository(
            NormalizationDatabaseConfig(database_url="postgres://example", schema="public"),
            command_runner=runner,
        )
        normalization_result = _build_normalization_result_stub()

        result = repository.persist_normalization_result(
            run_id="run-001",
            normalization_result=normalization_result,
            trigger_type="manual",
            triggered_by="codex",
            completed_at="2026-04-10T12:00:00+00:00",
        )

        self.assertEqual(result.run_state, "completed")
        self.assertEqual(result.candidate_count, 1)
        self.assertEqual(result.field_evidence_link_count, 4)
        self.assertEqual(result.model_execution_count, 1)
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


def _prepare_workspace_temp_dir(name: str) -> Path:
    temp_path = Path("tmp") / name
    rmtree(temp_path, ignore_errors=True)
    temp_path.mkdir(parents=True, exist_ok=True)
    return temp_path.resolve()


def _build_input() -> NormalizationInput:
    return NormalizationInput(
        source_id="TD-SAV-004",
        source_document_id="src-001",
        snapshot_id="snap-001",
        parsed_document_id="parsed-001",
        extraction_model_execution_id="modelexec-extract-001",
        extracted_storage_key="dev/extracted/CA/TD/src-001/parsed-001/extracted.json",
        metadata_storage_key="dev/extracted/CA/TD/src-001/parsed-001/metadata.json",
        bank_code="TD",
        country_code="CA",
        source_type="html",
        source_language="en",
        source_metadata={"product_type": "savings"},
        schema_context={"product_family": "deposit", "product_type": "savings"},
        extracted_fields=[
            _field("product_family", "deposit", "string", 0.99),
            _field("product_type", "savings", "string", 0.99),
            _field("country_code", "CA", "string", 0.99),
            _field("bank_code", "TD", "string", 0.99),
            _field("source_language", "en", "string", 0.99),
            _field("currency", "CAD", "string", 0.99),
            _field("product_name", "TD ePremium Savings Account", "string", 0.88),
            _field("description_short", "High-interest savings account.", "string", 0.7),
            _field("monthly_fee", "0.00", "decimal", 0.86, evidence_chunk_id="chunk-fee"),
            _field("standard_rate", "1.25", "decimal", 0.81, evidence_chunk_id="chunk-rate"),
            _field("interest_payment_frequency", "monthly", "string", 0.72, evidence_chunk_id="chunk-frequency"),
        ],
        evidence_links=[
            _evidence("monthly_fee", "0.00", "chunk-fee"),
            _evidence("standard_rate", "1.25", "chunk-rate"),
            _evidence("interest_payment_frequency", "monthly", "chunk-frequency"),
        ],
        runtime_notes=[],
    )


def _build_chequing_input() -> NormalizationInput:
    return NormalizationInput(
        source_id="TD-CHQ-002",
        source_document_id="src-chq-001",
        snapshot_id="snap-chq-001",
        parsed_document_id="parsed-chq-001",
        extraction_model_execution_id="modelexec-extract-chq-001",
        extracted_storage_key="dev/extracted/CA/TD/src-chq-001/parsed-chq-001/extracted.json",
        metadata_storage_key="dev/extracted/CA/TD/src-chq-001/parsed-chq-001/metadata.json",
        bank_code="TD",
        country_code="CA",
        source_type="html",
        source_language="en",
        source_metadata={"product_type": "chequing"},
        schema_context={"product_family": "deposit", "product_type": "chequing"},
        extracted_fields=[
            _field("product_family", "deposit", "string", 0.99),
            _field("product_type", "chequing", "string", 0.99),
            _field("country_code", "CA", "string", 0.99),
            _field("bank_code", "TD", "string", 0.99),
            _field("source_language", "en", "string", 0.99),
            _field("currency", "CAD", "string", 0.99),
            _field("product_name", "TD Student Banking Package", "string", 0.88),
            _field("description_short", "Chequing account for students and newcomers to Canada.", "string", 0.74),
            _field("monthly_fee", "0.00", "decimal", 0.86, evidence_chunk_id="chunk-chq-fee"),
            _field("included_transactions", 25, "integer", 0.82, evidence_chunk_id="chunk-chq-fee"),
            _field("interac_e_transfer_included", True, "boolean", 0.81, evidence_chunk_id="chunk-chq-benefits"),
            _field("overdraft_available", True, "boolean", 0.78, evidence_chunk_id="chunk-chq-benefits"),
            _field("cheque_book_info", "One free cheque book when you open the account.", "string", 0.77, evidence_chunk_id="chunk-chq-benefits"),
            _field("student_plan_flag", True, "boolean", 0.8, evidence_chunk_id="chunk-chq-title"),
            _field("newcomer_plan_flag", True, "boolean", 0.8, evidence_chunk_id="chunk-chq-title"),
        ],
        evidence_links=[
            _evidence("monthly_fee", "0.00", "chunk-chq-fee"),
            _evidence("included_transactions", "25", "chunk-chq-fee"),
            _evidence("interac_e_transfer_included", "true", "chunk-chq-benefits"),
            _evidence("student_plan_flag", "true", "chunk-chq-title"),
            _evidence("newcomer_plan_flag", "true", "chunk-chq-title"),
        ],
        runtime_notes=[],
    )


def _build_savings_detail_input() -> NormalizationInput:
    return NormalizationInput(
        source_id="RBC-SAV-004",
        source_document_id="src-sav-001",
        snapshot_id="snap-sav-001",
        parsed_document_id="parsed-sav-001",
        extraction_model_execution_id="modelexec-extract-sav-001",
        extracted_storage_key="dev/extracted/CA/RBC/src-sav-001/parsed-sav-001/extracted.json",
        metadata_storage_key="dev/extracted/CA/RBC/src-sav-001/parsed-sav-001/metadata.json",
        bank_code="RBC",
        country_code="CA",
        source_type="html",
        source_language="en",
        source_metadata={"product_type": "savings"},
        schema_context={"product_family": "deposit", "product_type": "savings"},
        extracted_fields=[
            _field("product_family", "deposit", "string", 0.99),
            _field("product_type", "savings", "string", 0.99),
            _field("country_code", "CA", "string", 0.99),
            _field("bank_code", "RBC", "string", 0.99),
            _field("source_language", "en", "string", 0.99),
            _field("currency", "CAD", "string", 0.99),
            _field("product_name", "RBC High Interest eSavings", "string", 0.88),
            _field("standard_rate", "1.60", "decimal", 0.85, evidence_chunk_id="chunk-sav-rate"),
            _field(
                "interest_calculation_method",
                "Interest is calculated on the daily closing balance and paid monthly.",
                "string",
                0.79,
                evidence_chunk_id="chunk-sav-rate",
            ),
            _field("interest_payment_frequency", "monthly", "string", 0.8, evidence_chunk_id="chunk-sav-rate"),
            _field("tiered_rate_flag", True, "boolean", 0.82, evidence_chunk_id="chunk-sav-rate"),
            _field(
                "tier_definition_text",
                "Balances of $0 to $4,999.99 earn 1.60%; $5,000 and over earn 1.80%.",
                "string",
                0.77,
                evidence_chunk_id="chunk-sav-rate",
            ),
            _field(
                "withdrawal_limit_text",
                "One debit transaction per month is included. Additional withdrawals cost $5 each.",
                "string",
                0.75,
                evidence_chunk_id="chunk-sav-withdrawal",
            ),
            _field("registered_flag", True, "boolean", 0.76, evidence_chunk_id="chunk-sav-registered"),
        ],
        evidence_links=[
            _evidence("standard_rate", "1.60", "chunk-sav-rate"),
            _evidence("interest_calculation_method", "Interest is calculated on the daily closing balance and paid monthly.", "chunk-sav-rate"),
            _evidence("interest_payment_frequency", "monthly", "chunk-sav-rate"),
            _evidence("tiered_rate_flag", "true", "chunk-sav-rate"),
            _evidence("tier_definition_text", "Balances of $0 to $4,999.99 earn 1.60%; $5,000 and over earn 1.80%.", "chunk-sav-rate"),
            _evidence("withdrawal_limit_text", "One debit transaction per month is included. Additional withdrawals cost $5 each.", "chunk-sav-withdrawal"),
            _evidence("registered_flag", "true", "chunk-sav-registered"),
        ],
        runtime_notes=[],
    )


def _build_gic_input() -> NormalizationInput:
    return NormalizationInput(
        source_id="RBC-GIC-002",
        source_document_id="src-gic-001",
        snapshot_id="snap-gic-001",
        parsed_document_id="parsed-gic-001",
        extraction_model_execution_id="modelexec-extract-gic-001",
        extracted_storage_key="dev/extracted/CA/RBC/src-gic-001/parsed-gic-001/extracted.json",
        metadata_storage_key="dev/extracted/CA/RBC/src-gic-001/parsed-gic-001/metadata.json",
        bank_code="RBC",
        country_code="CA",
        source_type="html",
        source_language="en",
        source_metadata={"product_type": "gic"},
        schema_context={"product_family": "deposit", "product_type": "gic"},
        extracted_fields=[
            _field("product_family", "deposit", "string", 0.99),
            _field("product_type", "gic", "string", 0.99),
            _field("country_code", "CA", "string", 0.99),
            _field("bank_code", "RBC", "string", 0.99),
            _field("source_language", "en", "string", 0.99),
            _field("currency", "CAD", "string", 0.99),
            _field("product_name", "RBC 1 Year Non-Redeemable GIC", "string", 0.9),
            _field("standard_rate", "3.80", "decimal", 0.84, evidence_chunk_id="chunk-gic-rate"),
            _field("minimum_deposit", "500.00", "decimal", 0.82, evidence_chunk_id="chunk-gic-rate"),
            _field("term_length_text", "1 year", "string", 0.83, evidence_chunk_id="chunk-gic-rate"),
            _field("term_length_days", 365, "integer", 0.83, evidence_chunk_id="chunk-gic-rate"),
            _field("redeemable_flag", False, "boolean", 0.8, evidence_chunk_id="chunk-gic-title"),
            _field("non_redeemable_flag", True, "boolean", 0.86, evidence_chunk_id="chunk-gic-title"),
            _field("compounding_frequency", "annually", "string", 0.77, evidence_chunk_id="chunk-gic-interest"),
            _field("payout_option", "at_maturity", "string", 0.78, evidence_chunk_id="chunk-gic-interest"),
            _field("registered_plan_supported", True, "boolean", 0.79, evidence_chunk_id="chunk-gic-registered"),
        ],
        evidence_links=[
            _evidence("standard_rate", "3.80", "chunk-gic-rate"),
            _evidence("minimum_deposit", "500.00", "chunk-gic-rate"),
            _evidence("term_length_text", "1 year", "chunk-gic-rate"),
            _evidence("term_length_days", "365", "chunk-gic-rate"),
            _evidence("redeemable_flag", "false", "chunk-gic-title"),
            _evidence("non_redeemable_flag", "true", "chunk-gic-title"),
            _evidence("compounding_frequency", "annually", "chunk-gic-interest"),
            _evidence("payout_option", "at_maturity", "chunk-gic-interest"),
            _evidence("registered_plan_supported", "true", "chunk-gic-registered"),
        ],
        runtime_notes=[],
    )


def _field(
    field_name: str,
    candidate_value: object,
    value_type: str,
    confidence: float,
    *,
    evidence_chunk_id: str | None = None,
) -> NormalizationExtractedField:
    return NormalizationExtractedField(
        field_name=field_name,
        candidate_value=candidate_value,
        value_type=value_type,
        confidence=confidence,
        extraction_method="heuristic",
        source_document_id="src-001",
        source_snapshot_id="snap-001",
        evidence_chunk_id=evidence_chunk_id,
        evidence_text_excerpt=None,
        anchor_type="section" if evidence_chunk_id else None,
        anchor_value="anchor" if evidence_chunk_id else None,
        page_no=None,
        chunk_index=0 if evidence_chunk_id else None,
        field_metadata={},
    )


def _field_dict(
    field_name: str,
    candidate_value: object,
    value_type: str,
    confidence: float,
    *,
    evidence_chunk_id: str | None = None,
) -> dict[str, object]:
    return _field(
        field_name,
        candidate_value,
        value_type,
        confidence,
        evidence_chunk_id=evidence_chunk_id,
    ).__dict__.copy()


def _evidence(field_name: str, candidate_value: str, evidence_chunk_id: str) -> NormalizationEvidenceLink:
    return NormalizationEvidenceLink(
        field_name=field_name,
        candidate_value=candidate_value,
        evidence_chunk_id=evidence_chunk_id,
        evidence_text_excerpt=f"{field_name} excerpt",
        source_document_id="src-001",
        source_snapshot_id="snap-001",
        citation_confidence=0.8,
        model_execution_id="modelexec-extract-001",
        anchor_type="section",
        anchor_value="anchor",
        page_no=None,
        chunk_index=0,
    )


def _match_dict(*, field_name: str, anchor_value: str, excerpt: str) -> dict[str, object]:
    return {
        "evidence_chunk_id": f"chunk-{field_name}",
        "field_name": field_name,
        "score": 0.81,
        "retrieval_mode": "metadata-only",
        "evidence_text_excerpt": excerpt,
        "source_document_id": "src-support-001",
        "source_snapshot_id": "snap-support-001",
        "model_execution_id": "modelexec-support-001",
        "parsed_document_id": "parsed-support-001",
        "anchor_type": "section",
        "anchor_value": anchor_value,
        "page_no": None,
        "chunk_index": 1,
        "match_metadata": {"matched_keywords": ["interest", "rate"]},
    }


def _build_normalization_result_stub():
    temp_path = _prepare_workspace_temp_dir("normalization-persist")
    storage_config = NormalizationStorageConfig(
        driver="filesystem",
        env_prefix="dev",
        normalization_object_prefix="normalized",
        retention_class="hot",
        filesystem_root=str(temp_path),
    )
    service = NormalizationService(
        storage_config=storage_config,
        object_store=build_object_store(storage_config),
    )
    return service.normalize_inputs(run_id="run-001", inputs=[_build_input()])


if __name__ == "__main__":
    unittest.main()
