from __future__ import annotations

import json
from pathlib import Path
from shutil import rmtree
import unittest

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
