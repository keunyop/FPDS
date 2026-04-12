from __future__ import annotations

import json
import unittest

from worker.pipeline.fpds_result_viewer.persistence import (
    PsqlResultViewerRepository,
    ResultViewerDatabaseConfig,
)
from worker.pipeline.fpds_result_viewer.service import ResultViewerPayloadService


class ResultViewerPayloadServiceTests(unittest.TestCase):
    def test_builds_payload_with_highlight_fields_and_registry_source_id(self) -> None:
        service = ResultViewerPayloadService()
        payload = service.build_payload(
            run_overview={
                "run_id": "run-3701",
                "run_state": "completed",
                "source_scope_count": 2,
                "source_success_count": 2,
                "source_failure_count": 0,
                "candidate_count": 2,
                "review_queued_count": 2,
                "partial_completion_flag": False,
                "started_at": "2026-04-10T18:00:00+00:00",
                "completed_at": "2026-04-10T18:05:00+00:00",
                "run_metadata": {"source_ids": ["TD-SAV-002", "TD-SAV-007"], "routing_mode": "prototype"},
                "stage_status_counts": {"completed": 2},
            },
            candidate_rows=[
                {
                    "candidate_id": "cand-001",
                    "review_task_id": "review-001",
                    "review_state": "queued",
                    "queue_reason_code": "validation_error",
                    "issue_summary": [{"code": "validation_error", "severity": "error", "summary": "Validation produced one or more error-level issues."}],
                    "run_id": "run-3701",
                    "source_document_id": "src-001",
                    "bank_code": "TD",
                    "bank_name": "TD Bank",
                    "country_code": "CA",
                    "product_family": "deposit",
                    "product_type": "savings",
                    "subtype_code": "high_interest",
                    "product_name": "TD ePremium Savings Account",
                    "source_language": "en",
                    "currency": "CAD",
                    "candidate_state": "in_review",
                    "validation_status": "error",
                    "source_confidence": 0.61,
                    "review_reason_code": "validation_error",
                    "validation_issue_codes": ["required_field_missing"],
                    "candidate_payload": {
                        "status": "active",
                        "standard_rate": 1.25,
                        "minimum_balance": 5000,
                        "eligibility_text": "Maintain a minimum balance each day.",
                    },
                    "field_mapping_metadata": {},
                    "source_url": "https://www.td.com/example",
                    "source_type": "html",
                    "source_metadata": {"source_id": "TD-SAV-007"},
                    "snapshot_id": "snap-001",
                    "fetched_at": "2026-04-10T17:59:00+00:00",
                    "parsed_document_id": "parsed-001",
                    "parse_quality_note": None,
                    "stage_status": "completed",
                    "warning_count": 1,
                    "error_count": 0,
                    "error_summary": None,
                    "runtime_notes": ["Candidate routed to review."],
                    "evidence_links": [
                        {
                            "field_name": "standard_rate",
                            "candidate_value": "1.25",
                            "citation_confidence": 0.82,
                            "evidence_chunk_id": "chunk-001",
                            "evidence_excerpt": "Earn 1.25% interest every month.",
                            "anchor_type": "section",
                            "anchor_value": "interest-rate",
                            "page_no": None,
                            "chunk_index": 2,
                            "anchor_label": "Section interest-rate",
                        }
                    ],
                }
            ],
            source_id_by_document_id={"src-001": "TD-SAV-007"},
            generated_at="2026-04-10T18:06:00+00:00",
        )

        self.assertEqual(payload["metrics"]["candidate_count"], 1)
        candidate = payload["candidates"][0]
        self.assertEqual(candidate["source_id"], "TD-SAV-007")
        self.assertEqual(candidate["highlight_fields"][0]["field_name"], "status")
        self.assertEqual(candidate["evidence_links"][0]["label"], "Standard Rate")

    def test_build_payload_js_assigns_window_global(self) -> None:
        service = ResultViewerPayloadService()
        js_text = service.build_payload_js(payload={"viewer_version": "v1", "generated_at": "now", "run": {}, "metrics": {}, "candidates": []})
        self.assertIn("window.FPDS_VIEWER_PAYLOAD", js_text)


class ResultViewerPersistenceTests(unittest.TestCase):
    def test_loads_overview_and_candidates_via_psql_runner(self) -> None:
        runner = _FakeRunner(
            outputs=[
                "public",
                json.dumps({"run_id": "run-3701", "run_state": "completed", "run_metadata": {"source_ids": ["TD-SAV-007"]}}),
                json.dumps([{"candidate_id": "cand-001", "source_document_id": "src-001", "candidate_payload": {}, "evidence_links": []}]),
            ]
        )
        repository = PsqlResultViewerRepository(
            ResultViewerDatabaseConfig(database_url="postgres://example", schema="public"),
            command_runner=runner,
        )

        overview = repository.load_run_overview(run_id="run-3701")
        candidates = repository.load_candidate_rows(run_id="run-3701")

        self.assertEqual(overview["run_id"], "run-3701")
        self.assertEqual(candidates[0]["candidate_id"], "cand-001")
        self.assertEqual(runner.last_variables()["run_id"], "run-3701")
        self.assertIn("validation_routing", runner.calls[-1][1])


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


if __name__ == "__main__":
    unittest.main()
