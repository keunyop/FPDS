from __future__ import annotations

import json
from pathlib import Path
from shutil import rmtree
import unittest

from worker.pipeline.fpds_validation_routing.models import (
    ValidationEvidenceLink,
    ValidationInput,
    ValidationRoutingConfig,
)
from worker.pipeline.fpds_validation_routing.persistence import (
    PsqlValidationRoutingRepository,
    ValidationRoutingDatabaseConfig,
)
from worker.pipeline.fpds_validation_routing.service import ValidationRoutingService
from worker.pipeline.fpds_validation_routing.storage import (
    ValidationRoutingStorageConfig,
    build_object_store,
)

_GOLDEN_FIXTURE_PATH = Path(__file__).parent / "fixtures" / "golden" / "canada_big5_deposit_products_golden_2026-05-23.json"


class ValidationRoutingServiceTests(unittest.TestCase):
    def test_prototype_routes_candidate_to_review_task(self) -> None:
        temp_path = _prepare_workspace_temp_dir("validation-routing-service")
        try:
            storage_config = ValidationRoutingStorageConfig(
                driver="filesystem",
                env_prefix="dev",
                validation_object_prefix="validated",
                retention_class="hot",
                filesystem_root=str(temp_path),
            )
            service = ValidationRoutingService(
                storage_config=storage_config,
                object_store=build_object_store(storage_config),
            )
            result = service.validate_and_route_inputs(
                run_id="run-001",
                inputs=[_build_input()],
                taxonomy_registry={"savings": {"standard", "high_interest", "youth", "foreign_currency", "other"}},
                routing_config=ValidationRoutingConfig(
                    routing_mode="prototype",
                    auto_approve_min_confidence=1.0,
                    review_warning_confidence_floor=0.0,
                    force_review_issue_codes={"required_field_missing", "conflicting_evidence"},
                ),
                correlation_id="corr-001",
                request_id="req-001",
            )

            self.assertFalse(result.partial_completion_flag)
            source_result = result.source_results[0]
            self.assertEqual(source_result.validation_action, "review_queued")
            self.assertEqual(source_result.validation_status, "pass")
            self.assertEqual(source_result.candidate_state, "in_review")
            self.assertEqual(source_result.review_reason_code, "manual_sampling_review")
            self.assertIsNotNone(source_result.review_task_record)

            artifact_path = temp_path / Path(str(source_result.validation_storage_key).replace("/", "\\"))
            self.assertTrue(artifact_path.exists())
            payload = json.loads(artifact_path.read_text(encoding="utf-8"))
            self.assertEqual(payload["candidate_after"]["candidate_state"], "in_review")
            self.assertEqual(payload["review_task_id"], source_result.review_task_id)
        finally:
            rmtree(temp_path, ignore_errors=True)

    def test_missing_required_rate_stays_error_and_queues_reason(self) -> None:
        temp_path = _prepare_workspace_temp_dir("validation-routing-error")
        try:
            storage_config = ValidationRoutingStorageConfig(
                driver="filesystem",
                env_prefix="dev",
                validation_object_prefix="validated",
                retention_class="hot",
                filesystem_root=str(temp_path),
            )
            service = ValidationRoutingService(
                storage_config=storage_config,
                object_store=build_object_store(storage_config),
            )
            input_item = _build_input()
            broken_candidate = dict(input_item.normalized_candidate_record)
            broken_payload = dict(broken_candidate["candidate_payload"])
            broken_payload.pop("standard_rate", None)
            broken_candidate["candidate_payload"] = broken_payload
            input_item = ValidationInput(
                **{
                    **input_item.__dict__,
                    "normalized_candidate_record": broken_candidate,
                    "field_evidence_links": [link for link in input_item.field_evidence_links if link.field_name != "standard_rate"],
                    "runtime_notes": ["No evidence-linked field candidates were extracted for one expected field."],
                }
            )

            result = service.validate_and_route_inputs(
                run_id="run-002",
                inputs=[input_item],
                taxonomy_registry={"savings": {"standard", "high_interest", "youth", "foreign_currency", "other"}},
                routing_config=ValidationRoutingConfig(
                    routing_mode="prototype",
                    auto_approve_min_confidence=1.0,
                    review_warning_confidence_floor=0.0,
                    force_review_issue_codes={"required_field_missing", "conflicting_evidence", "partial_source_failure"},
                ),
            )

            source_result = result.source_results[0]
            self.assertEqual(source_result.validation_status, "error")
            self.assertIn("required_field_missing", source_result.validation_issue_codes)
            self.assertIn("validation_error", source_result.queue_reason_codes)
            self.assertIn("partial_source_failure", source_result.queue_reason_codes)
        finally:
            rmtree(temp_path, ignore_errors=True)

    def test_chequing_package_subtype_passes_when_registry_contains_package(self) -> None:
        temp_path = _prepare_workspace_temp_dir("validation-routing-chequing-package")
        try:
            storage_config = ValidationRoutingStorageConfig(
                driver="filesystem",
                env_prefix="dev",
                validation_object_prefix="validated",
                retention_class="hot",
                filesystem_root=str(temp_path),
            )
            service = ValidationRoutingService(
                storage_config=storage_config,
                object_store=build_object_store(storage_config),
            )
            input_item = _build_chequing_input()

            result = service.validate_and_route_inputs(
                run_id="run-chq-001",
                inputs=[input_item],
                taxonomy_registry={"chequing": {"standard", "package", "interest_bearing", "premium", "other"}},
                routing_config=ValidationRoutingConfig(
                    routing_mode="phase1",
                    auto_approve_min_confidence=0.5,
                    review_warning_confidence_floor=0.0,
                    force_review_issue_codes={"required_field_missing", "conflicting_evidence"},
                ),
            )

            source_result = result.source_results[0]
            self.assertEqual(source_result.validation_status, "pass")
            self.assertNotIn("invalid_taxonomy_code", source_result.validation_issue_codes)
            self.assertEqual(source_result.validation_action, "auto_validated")
        finally:
            rmtree(temp_path, ignore_errors=True)

    def test_canonical_subtype_missing_from_active_registry_adds_operator_sync_context(self) -> None:
        temp_path = _prepare_workspace_temp_dir("validation-routing-chequing-package-missing-registry")
        try:
            storage_config = ValidationRoutingStorageConfig(
                driver="filesystem",
                env_prefix="dev",
                validation_object_prefix="validated",
                retention_class="hot",
                filesystem_root=str(temp_path),
            )
            service = ValidationRoutingService(
                storage_config=storage_config,
                object_store=build_object_store(storage_config),
            )
            input_item = _build_chequing_input()

            result = service.validate_and_route_inputs(
                run_id="run-chq-001",
                inputs=[input_item],
                taxonomy_registry={"chequing": {"standard", "other"}},
                routing_config=ValidationRoutingConfig(
                    routing_mode="phase1",
                    auto_approve_min_confidence=0.95,
                    review_warning_confidence_floor=0.0,
                    force_review_issue_codes={"required_field_missing", "conflicting_evidence"},
                ),
            )

            source_result = result.source_results[0]
            self.assertEqual(source_result.validation_status, "error")
            self.assertIn("invalid_taxonomy_code", source_result.validation_issue_codes)
            self.assertIn("chequing/package", " ".join(source_result.runtime_notes))
            issue_codes = {item["code"] for item in source_result.review_task_record["issue_summary"]}
            self.assertIn("taxonomy_registry_sync_missing", issue_codes)
        finally:
            rmtree(temp_path, ignore_errors=True)

    def test_gic_cross_field_issue_stays_error_and_queues_reason(self) -> None:
        temp_path = _prepare_workspace_temp_dir("validation-routing-gic-error")
        try:
            storage_config = ValidationRoutingStorageConfig(
                driver="filesystem",
                env_prefix="dev",
                validation_object_prefix="validated",
                retention_class="hot",
                filesystem_root=str(temp_path),
            )
            service = ValidationRoutingService(
                storage_config=storage_config,
                object_store=build_object_store(storage_config),
            )
            input_item = _build_gic_input()

            result = service.validate_and_route_inputs(
                run_id="run-gic-001",
                inputs=[input_item],
                taxonomy_registry={"gic": {"redeemable", "non_redeemable", "market_linked", "other"}},
                routing_config=ValidationRoutingConfig(
                    routing_mode="prototype",
                    auto_approve_min_confidence=1.0,
                    review_warning_confidence_floor=0.0,
                    force_review_issue_codes={"required_field_missing", "conflicting_evidence", "inconsistent_cross_field_logic"},
                ),
            )

            source_result = result.source_results[0]
            self.assertEqual(source_result.validation_status, "error")
            self.assertIn("inconsistent_cross_field_logic", source_result.validation_issue_codes)
            self.assertIn("validation_error", source_result.queue_reason_codes)
        finally:
            rmtree(temp_path, ignore_errors=True)

    def test_dynamic_product_type_stays_in_review_even_in_phase1_mode(self) -> None:
        temp_path = _prepare_workspace_temp_dir("validation-routing-dynamic")
        try:
            storage_config = ValidationRoutingStorageConfig(
                driver="filesystem",
                env_prefix="dev",
                validation_object_prefix="validated",
                retention_class="hot",
                filesystem_root=str(temp_path),
            )
            service = ValidationRoutingService(
                storage_config=storage_config,
                object_store=build_object_store(storage_config),
            )
            input_item = _build_input()
            dynamic_candidate = dict(input_item.normalized_candidate_record)
            dynamic_candidate["product_type"] = "tfsa-savings"
            dynamic_candidate["subtype_code"] = "other"
            input_item = ValidationInput(
                **{
                    **input_item.__dict__,
                    "source_id": "TD-TFSA-001",
                    "source_metadata": {
                        "product_type": "tfsa-savings",
                        "product_type_dynamic": True,
                        "fallback_policy": "generic_ai_review",
                    },
                    "normalized_candidate_record": dynamic_candidate,
                }
            )

            result = service.validate_and_route_inputs(
                run_id="run-dyn-001",
                inputs=[input_item],
                taxonomy_registry={},
                routing_config=ValidationRoutingConfig(
                    routing_mode="phase1",
                    auto_approve_min_confidence=0.5,
                    review_warning_confidence_floor=0.0,
                    force_review_issue_codes={"required_field_missing", "conflicting_evidence"},
                ),
            )

            source_result = result.source_results[0]
            self.assertEqual(source_result.validation_action, "review_queued")
            self.assertEqual(source_result.candidate_state, "in_review")
            self.assertEqual(source_result.review_reason_code, "manual_sampling_review")
            self.assertIn("manual_sampling_review", source_result.queue_reason_codes)
        finally:
            rmtree(temp_path, ignore_errors=True)

    def test_dynamic_product_type_no_grounded_detail_routes_as_partial_source_failure(self) -> None:
        temp_path = _prepare_workspace_temp_dir("validation-routing-dynamic-no-grounded-detail")
        try:
            storage_config = ValidationRoutingStorageConfig(
                driver="filesystem",
                env_prefix="dev",
                validation_object_prefix="validated",
                retention_class="hot",
                filesystem_root=str(temp_path),
            )
            service = ValidationRoutingService(
                storage_config=storage_config,
                object_store=build_object_store(storage_config),
            )
            input_item = _build_input()
            dynamic_candidate = dict(input_item.normalized_candidate_record)
            dynamic_candidate["product_type"] = "gic-term-deposit"
            dynamic_candidate["subtype_code"] = "other"
            dynamic_candidate["product_name"] = "Progressive GIC Search Tool - BMO"
            dynamic_payload = {
                "status": "active",
                "last_verified_at": "2026-04-29T06:15:11+00:00",
                "bank_name": "BMO",
                "product_name": "Progressive GIC Search Tool - BMO",
                "source_subtype_label": "Progressive GIC Search Tool - BMO",
                "subtype_code": "other",
            }
            dynamic_candidate["candidate_payload"] = dynamic_payload
            dynamic_candidate["validation_issue_codes"] = []
            input_item = ValidationInput(
                **{
                    **input_item.__dict__,
                    "source_id": "BMO-GIC-003",
                    "source_metadata": {
                        "product_type": "gic-term-deposit",
                        "product_type_dynamic": True,
                        "fallback_policy": "generic_ai_review",
                    },
                    "normalized_candidate_record": dynamic_candidate,
                    "field_evidence_links": [],
                    "runtime_notes": ["No grounded GIC product details were present in the evidence chunks."],
                }
            )

            result = service.validate_and_route_inputs(
                run_id="run-bmo-gic-dynamic",
                inputs=[input_item],
                taxonomy_registry={},
                routing_config=ValidationRoutingConfig(
                    routing_mode="phase1",
                    auto_approve_min_confidence=0.5,
                    review_warning_confidence_floor=0.0,
                    force_review_issue_codes={"required_field_missing", "conflicting_evidence", "partial_source_failure"},
                ),
            )

            source_result = result.source_results[0]
            self.assertEqual(source_result.validation_action, "review_queued")
            self.assertEqual(source_result.validation_status, "error")
            self.assertEqual(source_result.review_reason_code, "validation_error")
            self.assertIn("required_field_missing", source_result.validation_issue_codes)
            self.assertIn("partial_source_failure", source_result.validation_issue_codes)
            self.assertIn("required_field_missing", source_result.queue_reason_codes)
            self.assertIn("partial_source_failure", source_result.queue_reason_codes)
        finally:
            rmtree(temp_path, ignore_errors=True)

    def test_dynamic_gic_term_deposit_requires_rate_and_minimum_deposit(self) -> None:
        temp_path = _prepare_workspace_temp_dir("validation-routing-dynamic-gic-requiredness")
        try:
            storage_config = ValidationRoutingStorageConfig(
                driver="filesystem",
                env_prefix="dev",
                validation_object_prefix="validated",
                retention_class="hot",
                filesystem_root=str(temp_path),
            )
            service = ValidationRoutingService(
                storage_config=storage_config,
                object_store=build_object_store(storage_config),
            )
            input_item = _build_input()
            dynamic_candidate = dict(input_item.normalized_candidate_record)
            dynamic_candidate["product_type"] = "gic-term-deposit"
            dynamic_candidate["subtype_code"] = "redeemable"
            dynamic_candidate["product_name"] = "CIBC Flexible GIC"
            dynamic_candidate["candidate_payload"] = {
                "status": "active",
                "last_verified_at": "2026-05-01T22:47:52+00:00",
                "bank_name": "CIBC",
                "product_name": "CIBC Flexible GIC",
                "cashability": "Cashable",
                "term_length_text": "1 year",
                "term_length_days": 365,
                "redeemable_flag": True,
                "non_redeemable_flag": False,
                "source_subtype_label": "Cashable GIC / Flexible GIC",
                "subtype_code": "redeemable",
            }
            dynamic_candidate["validation_issue_codes"] = []
            input_item = ValidationInput(
                **{
                    **input_item.__dict__,
                    "source_id": "CIBC-GIC-002",
                    "source_metadata": {
                        "product_type": "gic-term-deposit",
                        "product_type_dynamic": True,
                        "fallback_policy": "generic_ai_review",
                    },
                    "normalized_candidate_record": dynamic_candidate,
                    "field_evidence_links": [
                        _evidence("cashability", "Cashable", "chunk-cibc-flex-access"),
                        _evidence("term_length_text", "1 year", "chunk-cibc-flex-term"),
                    ],
                }
            )

            result = service.validate_and_route_inputs(
                run_id="run-dyn-gic-requiredness",
                inputs=[input_item],
                taxonomy_registry={},
                routing_config=ValidationRoutingConfig(
                    routing_mode="phase1",
                    auto_approve_min_confidence=0.5,
                    review_warning_confidence_floor=0.0,
                    force_review_issue_codes={"required_field_missing", "conflicting_evidence"},
                ),
            )

            source_result = result.source_results[0]
            self.assertEqual(source_result.validation_action, "review_queued")
            self.assertEqual(source_result.validation_status, "error")
            self.assertEqual(source_result.review_reason_code, "validation_error")
            self.assertIn("required_field_missing", source_result.validation_issue_codes)
            self.assertIn("required_field_missing", source_result.queue_reason_codes)
        finally:
            rmtree(temp_path, ignore_errors=True)

    def test_validation_routing_rejects_display_strings_for_canonical_numeric_fields(self) -> None:
        temp_path = _prepare_workspace_temp_dir("validation-routing-display-money")
        try:
            storage_config = ValidationRoutingStorageConfig(
                driver="filesystem",
                env_prefix="dev",
                validation_object_prefix="validated",
                retention_class="hot",
                filesystem_root=str(temp_path),
            )
            service = ValidationRoutingService(
                storage_config=storage_config,
                object_store=build_object_store(storage_config),
            )
            input_item = _build_gic_input()
            candidate = dict(input_item.normalized_candidate_record)
            payload = dict(candidate["candidate_payload"])
            payload["minimum_deposit"] = "$1,000"
            payload["monthly_fee"] = "No fees"
            payload["public_display_fee"] = "No fees"
            payload["public_display_rate"] = "4.25%"
            payload["redeemable_flag"] = False
            payload["non_redeemable_flag"] = True
            candidate["candidate_payload"] = payload
            input_item = ValidationInput(**{**input_item.__dict__, "normalized_candidate_record": candidate})

            result = service.validate_and_route_inputs(
                run_id="run-gic-display-money",
                inputs=[input_item],
                taxonomy_registry={"gic": {"redeemable", "non_redeemable", "market_linked", "other"}},
                routing_config=ValidationRoutingConfig(
                    routing_mode="phase1",
                    auto_approve_min_confidence=0.5,
                    review_warning_confidence_floor=0.0,
                    force_review_issue_codes={"required_field_missing", "conflicting_evidence"},
                ),
            )

            source_result = result.source_results[0]
            self.assertNotIn("invalid_numeric_range", source_result.validation_issue_codes)
            self.assertIn("invalid_field_type", source_result.validation_issue_codes)
            self.assertEqual(source_result.validation_status, "error")
        finally:
            rmtree(temp_path, ignore_errors=True)

    def test_implausible_deposit_rate_is_invalid_numeric_range(self) -> None:
        temp_path = _prepare_workspace_temp_dir("validation-routing-implausible-rate")
        try:
            storage_config = ValidationRoutingStorageConfig(
                driver="filesystem",
                env_prefix="dev",
                validation_object_prefix="validated",
                retention_class="hot",
                filesystem_root=str(temp_path),
            )
            service = ValidationRoutingService(
                storage_config=storage_config,
                object_store=build_object_store(storage_config),
            )
            input_item = _build_gic_input()
            candidate = dict(input_item.normalized_candidate_record)
            payload = dict(candidate["candidate_payload"])
            payload["standard_rate"] = 60.0
            payload["public_display_rate"] = 60.0
            payload["redeemable_flag"] = False
            payload["non_redeemable_flag"] = True
            candidate["candidate_payload"] = payload
            input_item = ValidationInput(
                **{
                    **input_item.__dict__,
                    "normalized_candidate_record": candidate,
                    "field_evidence_links": [
                        _evidence("standard_rate", "60.0", "chunk-gic-rate"),
                        _evidence("public_display_rate", "60.0", "chunk-gic-rate"),
                        _evidence("minimum_deposit", "500.0", "chunk-gic-rate"),
                        _evidence("term_length_days", "365", "chunk-gic-rate"),
                        _evidence("non_redeemable_flag", "true", "chunk-gic-flags"),
                    ],
                }
            )

            result = service.validate_and_route_inputs(
                run_id="run-implausible-rate",
                inputs=[input_item],
                taxonomy_registry={"gic": {"redeemable", "non_redeemable", "market_linked", "other"}},
                routing_config=ValidationRoutingConfig(
                    routing_mode="phase1",
                    auto_approve_min_confidence=0.5,
                    review_warning_confidence_floor=0.0,
                    force_review_issue_codes={"required_field_missing", "conflicting_evidence", "invalid_numeric_range"},
                ),
            )

            source_result = result.source_results[0]
            self.assertEqual(source_result.validation_status, "error")
            self.assertIn("invalid_numeric_range", source_result.validation_issue_codes)
            self.assertEqual(source_result.validation_action, "review_queued")
        finally:
            rmtree(temp_path, ignore_errors=True)

    def test_legacy_profile_candidate_does_not_bypass_source_conflict_or_type_contract(self) -> None:
        temp_path = _prepare_workspace_temp_dir("validation-routing-golden-contract")
        try:
            storage_config = ValidationRoutingStorageConfig(
                driver="filesystem",
                env_prefix="dev",
                validation_object_prefix="validated",
                retention_class="hot",
                filesystem_root=str(temp_path),
            )
            service = ValidationRoutingService(
                storage_config=storage_config,
                object_store=build_object_store(storage_config),
            )
            input_item = _build_golden_contract_gic_input()

            result = service.validate_and_route_inputs(
                run_id="run-golden-contract",
                inputs=[input_item],
                taxonomy_registry={"gic": {"redeemable", "non_redeemable", "market_linked", "other"}},
                routing_config=ValidationRoutingConfig(
                    routing_mode="phase1",
                    auto_approve_min_confidence=0.82,
                    review_warning_confidence_floor=0.0,
                    force_review_issue_codes={"required_field_missing", "conflicting_evidence"},
                ),
            )

            source_result = result.source_results[0]
            self.assertEqual(source_result.validation_action, "review_queued")
            self.assertEqual(source_result.validation_status, "error")
            self.assertIn("invalid_field_type", source_result.validation_issue_codes)
            self.assertIn("conflicting_evidence", source_result.validation_issue_codes)
            self.assertEqual(source_result.candidate_state, "in_review")
            self.assertIsNotNone(source_result.review_task_record)
        finally:
            rmtree(temp_path, ignore_errors=True)

    def test_legacy_big5_fixture_rows_cannot_all_auto_validate_as_live_candidates(self) -> None:
        temp_path = _prepare_workspace_temp_dir("validation-routing-golden-fixture")
        try:
            storage_config = ValidationRoutingStorageConfig(
                driver="filesystem",
                env_prefix="dev",
                validation_object_prefix="validated",
                retention_class="hot",
                filesystem_root=str(temp_path),
            )
            service = ValidationRoutingService(
                storage_config=storage_config,
                object_store=build_object_store(storage_config),
            )

            result = service.validate_and_route_inputs(
                run_id="run-golden-fixture",
                inputs=_build_golden_fixture_inputs(),
                taxonomy_registry={
                    "chequing": {"standard", "package", "interest_bearing", "premium", "other"},
                    "savings": {"standard", "high_interest", "youth", "foreign_currency", "other"},
                    "gic": {"redeemable", "non_redeemable", "market_linked", "other"},
                },
                routing_config=ValidationRoutingConfig(
                    routing_mode="phase1",
                    auto_approve_min_confidence=0.82,
                    review_warning_confidence_floor=0.0,
                    force_review_issue_codes={"required_field_missing", "conflicting_evidence"},
                ),
            )

            self.assertEqual(len(result.source_results), 98)
            self.assertTrue(any(item.validation_action == "review_queued" for item in result.source_results))
            self.assertTrue(any(item.validation_status == "error" for item in result.source_results))
            self.assertTrue(any("invalid_field_type" in item.validation_issue_codes for item in result.source_results))
        finally:
            rmtree(temp_path, ignore_errors=True)

    def test_non_golden_contract_evidence_conflict_still_routes_to_review(self) -> None:
        temp_path = _prepare_workspace_temp_dir("validation-routing-non-golden-conflict")
        try:
            storage_config = ValidationRoutingStorageConfig(
                driver="filesystem",
                env_prefix="dev",
                validation_object_prefix="validated",
                retention_class="hot",
                filesystem_root=str(temp_path),
            )
            service = ValidationRoutingService(
                storage_config=storage_config,
                object_store=build_object_store(storage_config),
            )
            input_item = _build_input()
            input_item = ValidationInput(
                **{
                    **input_item.__dict__,
                    "field_evidence_links": [
                        *input_item.field_evidence_links,
                        _evidence("standard_rate", "1.35", "chunk-rate-conflict"),
                    ],
                }
            )

            result = service.validate_and_route_inputs(
                run_id="run-non-golden-conflict",
                inputs=[input_item],
                taxonomy_registry={"savings": {"standard", "high_interest", "youth", "foreign_currency", "other"}},
                routing_config=ValidationRoutingConfig(
                    routing_mode="phase1",
                    auto_approve_min_confidence=0.5,
                    review_warning_confidence_floor=0.0,
                    force_review_issue_codes={"conflicting_evidence"},
                ),
            )

            source_result = result.source_results[0]
            self.assertEqual(source_result.validation_action, "review_queued")
            self.assertEqual(source_result.validation_status, "warning")
            self.assertIn("conflicting_evidence", source_result.validation_issue_codes)
            self.assertEqual(source_result.review_reason_code, "conflicting_evidence")
            self.assertIsNotNone(source_result.review_task_record)
        finally:
            rmtree(temp_path, ignore_errors=True)


class ValidationRoutingPersistenceTests(unittest.TestCase):
    def test_load_policies_and_persist_queue(self) -> None:
        runner = _FakeRunner(
            outputs=[
                "public",
                json.dumps(
                    [
                        {
                            "source_document_id": "src-001",
                            "snapshot_id": "snap-001",
                            "parsed_document_id": "parsed-001",
                            "normalization_model_execution_id": "modelexec-normalize-001",
                            "normalized_storage_key": "dev/normalized/CA/TD/src-001/cand-001/normalized.json",
                            "normalization_metadata_storage_key": "dev/normalized/CA/TD/src-001/cand-001/metadata.json",
                            "bank_code": "TD",
                            "country_code": "CA",
                            "source_type": "html",
                            "source_language": "en",
                            "source_metadata": {"product_type": "savings"},
                        }
                    ]
                ),
                json.dumps({"savings": ["standard", "high_interest", "other"]}),
                json.dumps(
                    [
                        {"policy_key": "AUTO_APPROVE_MIN_CONFIDENCE", "policy_value": {"value": 0.95}},
                        {"policy_key": "REVIEW_WARNING_CONFIDENCE_FLOOR", "policy_value": {"value": 0.7}},
                        {"policy_key": "FORCE_REVIEW_ISSUE_CODES", "policy_value": ["required_field_missing", "conflicting_evidence"]},
                    ]
                ),
                "",
            ]
        )
        repository = PsqlValidationRoutingRepository(
            ValidationRoutingDatabaseConfig(database_url="postgres://example", schema="public"),
            command_runner=runner,
        )

        artifacts = repository.load_latest_normalization_artifacts(source_document_ids=["src-001"])
        taxonomy = repository.load_taxonomy_registry()
        config = repository.load_routing_config(routing_mode="phase1")
        validation_result = _build_validation_result_stub()
        persist_result = repository.persist_validation_result(
            run_id="run-001",
            validation_result=validation_result,
            trigger_type="manual",
            triggered_by="codex",
            completed_at="2026-04-10T13:00:00+00:00",
        )

        self.assertEqual(len(artifacts), 1)
        self.assertEqual(taxonomy["savings"], {"standard", "high_interest", "other"})
        self.assertEqual(config.auto_approve_min_confidence, 0.95)
        self.assertEqual(persist_result.review_task_count, 1)
        self.assertEqual(runner.last_variables()["review_queued_count"], "1")


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


def _build_input() -> ValidationInput:
    candidate_record = {
        "candidate_id": "cand-001",
        "run_id": "run-3603",
        "source_document_id": "src-001",
        "model_execution_id": "modelexec-normalize-001",
        "candidate_state": "draft",
        "validation_status": "pass",
        "source_confidence": 0.81,
        "review_reason_code": None,
        "country_code": "CA",
        "bank_code": "TD",
        "product_family": "deposit",
        "product_type": "savings",
        "subtype_code": "high_interest",
        "product_name": "TD ePremium Savings Account",
        "source_language": "en",
        "currency": "CAD",
        "validation_issue_codes": [],
        "candidate_payload": {
            "status": "active",
            "last_verified_at": "2026-04-10T12:00:00+00:00",
            "bank_name": "TD Bank",
            "product_name": "TD ePremium Savings Account",
            "standard_rate": 1.25,
            "monthly_fee": 0.0,
            "interest_payment_frequency": "monthly",
        },
        "field_mapping_metadata": {},
    }
    return ValidationInput(
        source_id="TD-SAV-004",
        source_document_id="src-001",
        snapshot_id="snap-001",
        parsed_document_id="parsed-001",
        candidate_id="cand-001",
        candidate_run_id="run-3603",
        normalization_model_execution_id="modelexec-normalize-001",
        normalized_storage_key="dev/normalized/CA/TD/src-001/cand-001/normalized.json",
        metadata_storage_key="dev/normalized/CA/TD/src-001/cand-001/metadata.json",
        bank_code="TD",
        country_code="CA",
        source_type="html",
        source_language="en",
        source_metadata={"product_type": "savings"},
        normalized_candidate_record=candidate_record,
        field_evidence_links=[
            _evidence("monthly_fee", "0.0", "chunk-fee"),
            _evidence("standard_rate", "1.25", "chunk-rate"),
            _evidence("interest_payment_frequency", "monthly", "chunk-frequency"),
        ],
        runtime_notes=[],
    )


def _build_gic_input() -> ValidationInput:
    candidate_record = {
        "candidate_id": "cand-gic-001",
        "run_id": "run-gic-3603",
        "source_document_id": "src-gic-001",
        "model_execution_id": "modelexec-normalize-gic-001",
        "candidate_state": "draft",
        "validation_status": "pass",
        "source_confidence": 0.86,
        "review_reason_code": None,
        "country_code": "CA",
        "bank_code": "RBC",
        "product_family": "deposit",
        "product_type": "gic",
        "subtype_code": "non_redeemable",
        "product_name": "RBC 1 Year Non-Redeemable GIC",
        "source_language": "en",
        "currency": "CAD",
        "validation_issue_codes": [],
        "candidate_payload": {
            "status": "active",
            "last_verified_at": "2026-04-10T12:00:00+00:00",
            "bank_name": "RBC",
            "product_name": "RBC 1 Year Non-Redeemable GIC",
            "standard_rate": 3.8,
            "minimum_deposit": 500.0,
            "term_length_text": "1 year",
            "term_length_days": 365,
            "redeemable_flag": True,
            "non_redeemable_flag": True,
        },
        "field_mapping_metadata": {},
    }
    return ValidationInput(
        source_id="RBC-GIC-002",
        source_document_id="src-gic-001",
        snapshot_id="snap-gic-001",
        parsed_document_id="parsed-gic-001",
        candidate_id="cand-gic-001",
        candidate_run_id="run-gic-3603",
        normalization_model_execution_id="modelexec-normalize-gic-001",
        normalized_storage_key="dev/normalized/CA/RBC/src-gic-001/cand-gic-001/normalized.json",
        metadata_storage_key="dev/normalized/CA/RBC/src-gic-001/cand-gic-001/metadata.json",
        bank_code="RBC",
        country_code="CA",
        source_type="html",
        source_language="en",
        source_metadata={"product_type": "gic"},
        normalized_candidate_record=candidate_record,
        field_evidence_links=[
            _evidence("standard_rate", "3.8", "chunk-gic-rate"),
            _evidence("minimum_deposit", "500.0", "chunk-gic-rate"),
            _evidence("term_length_days", "365", "chunk-gic-rate"),
            _evidence("redeemable_flag", "true", "chunk-gic-flags"),
            _evidence("non_redeemable_flag", "true", "chunk-gic-flags"),
        ],
        runtime_notes=[],
    )


def _build_chequing_input() -> ValidationInput:
    candidate_record = {
        "candidate_id": "cand-chq-001",
        "run_id": "run-chq-3603",
        "source_document_id": "src-chq-001",
        "model_execution_id": "modelexec-normalize-chq-001",
        "candidate_state": "draft",
        "validation_status": "pass",
        "source_confidence": 0.86,
        "review_reason_code": None,
        "country_code": "CA",
        "bank_code": "BMO",
        "product_family": "deposit",
        "product_type": "chequing",
        "subtype_code": "package",
        "product_name": "Plus Chequing Account",
        "source_language": "en",
        "currency": "CAD",
        "validation_issue_codes": [],
        "candidate_payload": {
            "status": "active",
            "last_verified_at": "2026-04-28T20:42:48+00:00",
            "bank_name": "BMO",
            "product_name": "Plus Chequing Account",
            "monthly_fee": 12.95,
            "public_display_fee": 12.95,
            "minimum_balance": 3000.0,
            "fee_waiver_condition": "Monthly fee 12.95 is waived to 0.00 with a 3000.00 minimum balance.",
            "included_transactions": 25,
            "interac_e_transfer_included": True,
        },
        "field_mapping_metadata": {},
    }
    return ValidationInput(
        source_id="BMO-CHQ-003",
        source_document_id="src-chq-001",
        snapshot_id="snap-chq-001",
        parsed_document_id="parsed-chq-001",
        candidate_id="cand-chq-001",
        candidate_run_id="run-chq-3603",
        normalization_model_execution_id="modelexec-normalize-chq-001",
        normalized_storage_key="dev/normalized/CA/BMO/src-chq-001/cand-chq-001/normalized.json",
        metadata_storage_key="dev/normalized/CA/BMO/src-chq-001/cand-chq-001/metadata.json",
        bank_code="BMO",
        country_code="CA",
        source_type="html",
        source_language="en",
        source_metadata={"product_type": "chequing"},
        normalized_candidate_record=candidate_record,
        field_evidence_links=[
            _evidence("monthly_fee", "12.95", "chunk-chq-fee"),
            _evidence("minimum_balance", "3000.0", "chunk-chq-fee"),
            _evidence("included_transactions", "25", "chunk-chq-fee"),
            _evidence("interac_e_transfer_included", "true", "chunk-chq-benefits"),
        ],
        runtime_notes=[],
    )


def _build_golden_contract_gic_input() -> ValidationInput:
    input_item = _build_gic_input()
    candidate = dict(input_item.normalized_candidate_record)
    candidate["product_name"] = "BMO AIR MILES GIC"
    candidate["subtype_code"] = "other"
    candidate["validation_issue_codes"] = ["required_field_missing", "conflicting_evidence"]
    candidate["candidate_payload"] = {
        "status": "active",
        "last_verified_at": "2026-05-23T00:00:00+00:00",
        "bank_name": "BMO",
        "product_name": "BMO AIR MILES GIC",
        "highest_rate": "0.250%",
        "base_12_month_rate": None,
        "tags": ["cad", "rewards", "gic"],
        "product_page_url": "https://www.bmo.com/main/personal/investments/gic/gic-rates/",
        "signup_amount": "Minimum investment disclosed on the official product or rates page.",
        "eligibility": "Personal banking customers in Canada.",
        "application_method": "Apply online, by phone, or at a branch.",
        "post_maturity_interest_rate": None,
        "tax_benefits": None,
        "deposit_insurance": "Eligible deposits are protected by CDIC limits.",
        "term_rates": [
            {
                "term": "364 days",
                "highest_rate": "0.250%",
                "base_rate": None,
            }
        ],
    }
    return ValidationInput(
        **{
            **input_item.__dict__,
            "source_id": "BMO-GIC-002",
            "bank_code": "BMO",
            "source_metadata": {
                "product_type": "gic",
                "product_profile_id": "bmo-air-miles-gic",
                "discovery_role": "supporting_html",
            },
            "normalized_candidate_record": candidate,
            "field_evidence_links": [
                _evidence("product_name", "GIC rates", "chunk-gic-list"),
                _evidence("product_name", "BMO AIR MILES GIC", "chunk-gic-profile"),
                _evidence("highest_rate", "0.250%", "chunk-gic-profile"),
                _evidence("product_page_url", "https://www.bmo.com/main/personal/investments/gic/gic-rates/", "chunk-gic-profile"),
                _evidence("signup_amount", "Minimum investment disclosed on the official product or rates page.", "chunk-gic-profile"),
                _evidence("eligibility", "Personal banking customers in Canada.", "chunk-gic-profile"),
                _evidence("application_method", "Apply online, by phone, or at a branch.", "chunk-gic-profile"),
                _evidence("deposit_insurance", "Eligible deposits are protected by CDIC limits.", "chunk-gic-profile"),
                _evidence("tags", "['cad', 'rewards', 'gic']", "chunk-gic-profile"),
                _evidence("term_rates", "[{'term': '364 days', 'highest_rate': '0.250%', 'base_rate': None}]", "chunk-gic-profile"),
            ],
        }
    )


def _build_golden_fixture_inputs() -> list[ValidationInput]:
    payload = json.loads(_GOLDEN_FIXTURE_PATH.read_text(encoding="utf-8"))
    rows = list(payload["products"])
    return [_build_golden_fixture_input(row=row, index=index) for index, row in enumerate(rows)]


def _build_golden_fixture_input(*, row: dict[str, object], index: int) -> ValidationInput:
    candidate_id = f"cand-golden-{index:03d}"
    bank_code = str(row["bank_code"])
    product_type = str(row["product_type"])
    product_name = str(row["product_name"])
    candidate_payload = {
        "status": "active",
        "last_verified_at": "2026-05-23T00:00:00+00:00",
        "bank_name": row["bank_name"],
        "product_name": product_name,
        "highest_rate": row.get("highest_rate"),
        "base_12_month_rate": row.get("base_12_month_rate"),
        "tags": row.get("tags"),
        "product_page_url": row.get("product_page_url"),
        "signup_amount": row.get("signup_amount"),
        "eligibility": row.get("eligibility"),
        "application_method": row.get("application_method"),
        "post_maturity_interest_rate": row.get("post_maturity_interest_rate"),
        "tax_benefits": row.get("tax_benefits"),
        "deposit_insurance": row.get("deposit_insurance"),
        "term_rates": row.get("term_rates"),
    }
    candidate_record = {
        "candidate_id": candidate_id,
        "run_id": "run-golden-fixture",
        "source_document_id": f"src-golden-{index:03d}",
        "model_execution_id": f"modelexec-normalize-golden-{index:03d}",
        "candidate_state": "draft",
        "validation_status": "pass",
        "source_confidence": 0.9,
        "review_reason_code": None,
        "country_code": "CA",
        "bank_code": bank_code,
        "product_family": "deposit",
        "product_type": product_type,
        "subtype_code": "other",
        "product_name": product_name,
        "source_language": "en",
        "currency": "CAD",
        "validation_issue_codes": ["required_field_missing", "conflicting_evidence"],
        "candidate_payload": candidate_payload,
        "field_mapping_metadata": {},
    }
    source_document_id = f"src-golden-{index:03d}"
    return ValidationInput(
        source_id=f"golden-{index:03d}",
        source_document_id=source_document_id,
        snapshot_id=f"snap-golden-{index:03d}",
        parsed_document_id=f"parsed-golden-{index:03d}",
        candidate_id=candidate_id,
        candidate_run_id="run-golden-fixture",
        normalization_model_execution_id=f"modelexec-normalize-golden-{index:03d}",
        normalized_storage_key=f"dev/normalized/CA/{bank_code}/{source_document_id}/{candidate_id}/normalized.json",
        metadata_storage_key=f"dev/normalized/CA/{bank_code}/{source_document_id}/{candidate_id}/metadata.json",
        bank_code=bank_code,
        country_code="CA",
        source_type="html",
        source_language="en",
        source_metadata={"product_type": product_type, "product_profile_id": f"golden-{index:03d}"},
        normalized_candidate_record=candidate_record,
        field_evidence_links=[
            _golden_evidence(
                candidate_id=candidate_id,
                source_document_id=source_document_id,
                field_name=field_name,
                value=value,
                index=index,
            )
            for field_name, value in candidate_payload.items()
            if field_name not in {"status", "last_verified_at"} and value is not None
        ],
        runtime_notes=[],
    )


def _golden_evidence(
    *,
    candidate_id: str,
    source_document_id: str,
    field_name: str,
    value: object,
    index: int,
) -> ValidationEvidenceLink:
    if isinstance(value, list | dict):
        candidate_value = json.dumps(value, ensure_ascii=True, sort_keys=True)
    else:
        candidate_value = str(value)
    return ValidationEvidenceLink(
        field_evidence_link_id=f"fel-golden-{index:03d}-{field_name}",
        candidate_id=candidate_id,
        product_version_id=None,
        evidence_chunk_id=f"chunk-golden-{index:03d}",
        source_document_id=source_document_id,
        field_name=field_name,
        candidate_value=candidate_value,
        citation_confidence=0.9,
    )


def _evidence(field_name: str, candidate_value: str, evidence_chunk_id: str) -> ValidationEvidenceLink:
    return ValidationEvidenceLink(
        field_evidence_link_id=f"fel-{field_name}",
        candidate_id="cand-001",
        product_version_id=None,
        evidence_chunk_id=evidence_chunk_id,
        source_document_id="src-001",
        field_name=field_name,
        candidate_value=candidate_value,
        citation_confidence=0.8,
    )


def _build_validation_result_stub():
    temp_path = _prepare_workspace_temp_dir("validation-routing-persist")
    storage_config = ValidationRoutingStorageConfig(
        driver="filesystem",
        env_prefix="dev",
        validation_object_prefix="validated",
        retention_class="hot",
        filesystem_root=str(temp_path),
    )
    service = ValidationRoutingService(
        storage_config=storage_config,
        object_store=build_object_store(storage_config),
    )
    return service.validate_and_route_inputs(
        run_id="run-001",
        inputs=[_build_input()],
        taxonomy_registry={"savings": {"standard", "high_interest", "youth", "foreign_currency", "other"}},
        routing_config=ValidationRoutingConfig(
            routing_mode="prototype",
            auto_approve_min_confidence=1.0,
            review_warning_confidence_floor=0.0,
            force_review_issue_codes={"required_field_missing", "conflicting_evidence"},
        ),
    )


if __name__ == "__main__":
    unittest.main()
