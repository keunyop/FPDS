from __future__ import annotations

import json
from pathlib import Path
from shutil import rmtree
import unittest
from unittest.mock import patch

from worker.pipeline.fpds_evidence_retrieval.models import EvidenceChunkCandidate, EvidenceMatch
from worker.pipeline.fpds_extraction.__main__ import _context_with_registry_metadata
from worker.pipeline.fpds_extraction.models import ExtractedFieldCandidate, ExtractionDocumentContext, ExtractionInput
from worker.pipeline.fpds_extraction.persistence import ExtractionDatabaseConfig, PsqlExtractionRepository
from worker.pipeline.fpds_extraction.service import (
    ExtractionService,
    _append_rate_fallback_fields,
    _extract_candidate_value,
    _extract_from_matches,
    _uses_dynamic_product_type,
)
from worker.pipeline.fpds_extraction.storage import ExtractionStorageConfig, build_object_store


class ExtractionServiceTests(unittest.TestCase):
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

        self.assertIsNone(student)

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
                            "summary": "AI mapped one dynamic product eligibility field.",
                            "field_candidates": [
                                {
                                    "field_name": "eligibility_text",
                                    "candidate_value": "Canadian residents aged 18 or older.",
                                    "value_type": "string",
                                    "evidence_chunk_id": "chunk-dyn-001",
                                    "confidence": 0.83,
                                }
                            ],
                        },
                        {
                            "model_id": "gpt-5.6-luna",
                            "prompt_tokens": 120,
                            "completion_tokens": 34,
                            "provider_request_id": "resp-dyn-001",
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
            self.assertEqual(source_result.model_execution_record["agent_name"], "fpds-dynamic-product-extractor")
            self.assertEqual(source_result.usage_record["usage_metadata"]["usage_mode"], "openai-dynamic-product-extraction")
            self.assertEqual(extracted_by_field["eligibility_text"].candidate_value, "Canadian residents aged 18 or older.")
            self.assertEqual(extracted_by_field["eligibility_text"].extraction_method, "openai_dynamic_extractor")
            self.assertIn("AI mapped one dynamic product eligibility field.", source_result.runtime_notes)
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
                            "field_candidates": [],
                        },
                        {
                            "model_id": "gpt-5.6-luna",
                            "prompt_tokens": 160,
                            "completion_tokens": 18,
                            "provider_request_id": "resp-bmo-gic-nav",
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


def _extracted_field(field_name: str, candidate_value: object) -> ExtractedFieldCandidate:
    return ExtractedFieldCandidate(
        field_name=field_name,
        candidate_value=candidate_value,
        value_type="string",
        confidence=0.9,
        extraction_method="test",
        source_document_id="src-test",
        source_snapshot_id="snap-test",
        evidence_chunk_id=None,
        evidence_text_excerpt=None,
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
