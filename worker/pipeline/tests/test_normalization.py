from __future__ import annotations

import json
from pathlib import Path
from shutil import rmtree
import unittest

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
from worker.pipeline.fpds_normalization.service import NormalizationService
from worker.pipeline.fpds_normalization.storage import (
    NormalizationStorageConfig,
    build_object_store,
)
from worker.pipeline.fpds_normalization.supporting_merge import (
    merge_supporting_artifacts,
    supporting_source_ids_for_target,
)


class NormalizationServiceTests(unittest.TestCase):
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


class SupportingMergeTests(unittest.TestCase):
    def test_supporting_source_ids_for_td_targets(self) -> None:
        self.assertEqual(supporting_source_ids_for_target("TD-SAV-002"), ("TD-SAV-005", "TD-SAV-007", "TD-SAV-008"))
        self.assertEqual(supporting_source_ids_for_target("TD-SAV-003"), ("TD-SAV-005", "TD-SAV-007", "TD-SAV-008"))
        self.assertEqual(supporting_source_ids_for_target("TD-SAV-004"), ("TD-SAV-005", "TD-SAV-007", "TD-SAV-008"))
        self.assertEqual(supporting_source_ids_for_target("TD-SAV-999"), ())

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

        result = repository.load_latest_extraction_artifacts(source_document_ids=["src-001"])

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].parsed_document_id, "parsed-001")
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
