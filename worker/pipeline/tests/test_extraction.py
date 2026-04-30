from __future__ import annotations

import json
from pathlib import Path
from shutil import rmtree
import unittest
from unittest.mock import patch

from worker.pipeline.fpds_evidence_retrieval.models import EvidenceChunkCandidate
from worker.pipeline.fpds_extraction.models import ExtractionDocumentContext, ExtractionInput
from worker.pipeline.fpds_extraction.persistence import ExtractionDatabaseConfig, PsqlExtractionRepository
from worker.pipeline.fpds_extraction.service import ExtractionService
from worker.pipeline.fpds_extraction.storage import ExtractionStorageConfig, build_object_store


class ExtractionServiceTests(unittest.TestCase):
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
            self.assertTrue(extracted_by_field["newcomer_plan_flag"].candidate_value)
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
                patch("worker.pipeline.fpds_extraction.service.configured_model_id", return_value="gpt-5.4-mini"),
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
                            "model_id": "gpt-5.4-mini",
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


class ExtractionPersistenceTests(unittest.TestCase):
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


def _prepare_workspace_temp_dir(name: str) -> Path:
    temp_path = Path("tmp") / name
    rmtree(temp_path, ignore_errors=True)
    temp_path.mkdir(parents=True, exist_ok=True)
    return temp_path.resolve()


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
