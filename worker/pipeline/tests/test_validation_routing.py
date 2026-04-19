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
