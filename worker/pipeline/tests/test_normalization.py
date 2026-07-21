from __future__ import annotations

import json
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
    _build_field_evidence_link_records,
    _clean_product_context_fields,
    _extract_rate_percentages,
    _normalize_term_rate_table,
    _rate_evidence_is_account_context,
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
    def test_term_rate_text_normalizes_to_typed_rows(self) -> None:
        rows = _normalize_term_rate_table("1 Year 3.30%, 5 Years 4.00%")

        self.assertEqual(
            rows,
            [
                {"term_label": "1 Year", "term_length_days": 365, "rate": 3.3, "minimum_deposit": None, "notes": None},
                {"term_label": "5 Years", "term_length_days": 1825, "rate": 4.0, "minimum_deposit": None, "notes": None},
            ],
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
        self.assertIn("incorrectly mapped as product data", notes[0])

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
            self.assertEqual(len(source_result.field_evidence_link_records), 3)

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
                            "Savings Account\n2.80\nTFSA Savings Account\n2.80\n"
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
                        excerpt="Basic Plus Bank Account Monthly fee $11.95 Included transactions 25",
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
                            "Cashable GICs require a minimum deposit of $1,000."
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
        rows = fields_by_name["term_rate_table"]["candidate_value"]
        self.assertEqual(len(rows), 13)
        self.assertEqual(rows[0]["notes"], "Long-term GIC annual interest rate")
        self.assertEqual(rows[-1]["rate"], "2.25")
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
        self.assertEqual(result.field_evidence_link_count, 3)
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
