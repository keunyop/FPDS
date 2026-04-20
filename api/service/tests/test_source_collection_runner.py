from __future__ import annotations

import subprocess
import shutil
import unittest
from pathlib import Path
from unittest.mock import patch

from api_service import source_collection_runner


class SourceCollectionRunnerTests(unittest.TestCase):
    def _workspace_temp_path(self, name: str) -> Path:
        path = Path.cwd() / "tmp" / "test-source-collection-runner" / name
        if path.exists():
            shutil.rmtree(path, ignore_errors=True)
        path.mkdir(parents=True, exist_ok=True)
        return path

    def test_run_group_filters_downstream_sources_to_snapshot_successes(self) -> None:
        plan = {
            "trigger_type": "admin_source_collection",
            "triggered_by": "admin@example.com",
        }
        group = {
            "run_id": "run-001",
            "bank_code": "BMO",
            "country_code": "CA",
            "product_type": "chequing",
            "source_language": "en",
            "included_source_ids": ["BMO-CHQ-002", "BMO-CHQ-006", "BMO-CHQ-007"],
            "target_source_ids": ["BMO-CHQ-002"],
            "included_sources": [
                {
                    "source_id": "BMO-CHQ-002",
                    "priority": "P0",
                    "seed_source_flag": True,
                    "source_type": "html",
                    "discovery_role": "detail",
                    "purpose": "detail",
                    "source_url": "https://www.bmo.com/practical",
                    "expected_fields": ["product_name"],
                    "source_language": "en",
                },
                {
                    "source_id": "BMO-CHQ-006",
                    "priority": "P0",
                    "seed_source_flag": True,
                    "source_type": "html",
                    "discovery_role": "supporting_html",
                    "purpose": "rates",
                    "source_url": "https://www.bmo.com/rates",
                    "expected_fields": ["monthly_fee"],
                    "source_language": "en",
                },
                {
                    "source_id": "BMO-CHQ-007",
                    "priority": "P0",
                    "seed_source_flag": True,
                    "source_type": "html",
                    "discovery_role": "supporting_html",
                    "purpose": "terms",
                    "source_url": "https://www.bmo.com/terms",
                    "expected_fields": ["monthly_fee"],
                    "source_language": "en",
                },
            ],
        }

        stage_calls: list[tuple[str, list[str]]] = []

        def fake_run_stage(module_name: str, args: list[str]) -> dict[str, object]:
            stage_calls.append((module_name, args))
            if module_name == "worker.discovery.fpds_snapshot":
                return {
                    "source_results": [
                        {"source_id": "BMO-CHQ-002", "snapshot_action": "stored"},
                        {"source_id": "BMO-CHQ-006", "snapshot_action": "reused"},
                        {"source_id": "BMO-CHQ-007", "snapshot_action": "failed"},
                    ]
                }
            return {}

        temp_dir = self._workspace_temp_path("filter-successes")
        with (
            patch("api_service.source_collection_runner.args_temp_dir", return_value=temp_dir),
            patch("api_service.source_collection_runner._resolve_env_file", return_value=None),
            patch("api_service.source_collection_runner._run_stage", side_effect=fake_run_stage),
        ):
            source_collection_runner._run_group(plan=plan, group=group)

        self.assertEqual(
            [module_name for module_name, _args in stage_calls],
            [
                "worker.discovery.fpds_snapshot",
                "worker.pipeline.fpds_parse_chunk",
                "worker.pipeline.fpds_extraction",
                "worker.pipeline.fpds_normalization",
                "worker.pipeline.fpds_validation_routing",
            ],
        )
        parse_args = stage_calls[1][1]
        extraction_args = stage_calls[2][1]
        normalization_args = stage_calls[3][1]
        validation_args = stage_calls[4][1]
        self.assertIn("BMO-CHQ-002", parse_args)
        self.assertIn("BMO-CHQ-006", parse_args)
        self.assertNotIn("BMO-CHQ-007", parse_args)
        self.assertEqual(parse_args, extraction_args)
        self.assertIn("BMO-CHQ-002", normalization_args)
        self.assertNotIn("BMO-CHQ-006", normalization_args)
        self.assertNotIn("BMO-CHQ-007", normalization_args)
        self.assertIn("BMO-CHQ-002", validation_args)

    def test_run_group_stops_when_snapshot_has_no_successes(self) -> None:
        plan = {"trigger_type": "admin_source_collection", "triggered_by": "admin@example.com"}
        group = {
            "run_id": "run-001",
            "bank_code": "BMO",
            "country_code": "CA",
            "product_type": "chequing",
            "source_language": "en",
            "included_source_ids": ["BMO-CHQ-002"],
            "target_source_ids": ["BMO-CHQ-002"],
            "included_sources": [
                {
                    "source_id": "BMO-CHQ-002",
                    "priority": "P0",
                    "seed_source_flag": True,
                    "source_type": "html",
                    "discovery_role": "detail",
                    "purpose": "detail",
                    "source_url": "https://www.bmo.com/practical",
                    "expected_fields": ["product_name"],
                    "source_language": "en",
                }
            ],
        }

        temp_dir = self._workspace_temp_path("snapshot-no-success")
        with (
            patch("api_service.source_collection_runner.args_temp_dir", return_value=temp_dir),
            patch("api_service.source_collection_runner._resolve_env_file", return_value=None),
            patch(
                "api_service.source_collection_runner._run_stage",
                return_value={"source_results": [{"source_id": "BMO-CHQ-002", "snapshot_action": "failed"}]},
            ) as run_stage,
        ):
            with self.assertRaisesRegex(RuntimeError, "Snapshot capture failed for all selected sources."):
                source_collection_runner._run_group(plan=plan, group=group)

        run_stage.assert_called_once()

    def test_successful_source_ids_ignores_failed_results(self) -> None:
        self.assertEqual(
            source_collection_runner._successful_source_ids(
                {
                    "source_results": [
                        {"source_id": "SRC-001", "snapshot_action": "stored"},
                        {"source_id": "SRC-002", "snapshot_action": "reused"},
                        {"source_id": "SRC-003", "snapshot_action": "failed"},
                    ]
                }
            ),
            ["SRC-001", "SRC-002"],
        )

    def test_run_stage_raises_clear_error_when_worker_stage_times_out(self) -> None:
        with (
            patch("api_service.source_collection_runner.shutil.which", return_value="uv"),
            patch(
                "api_service.source_collection_runner.subprocess.run",
                side_effect=subprocess.TimeoutExpired(cmd=["uv"], timeout=120),
            ),
            patch.dict("os.environ", {"FPDS_SOURCE_COLLECTION_STAGE_TIMEOUT_SECONDS": "120"}, clear=False),
        ):
            with self.assertRaisesRegex(RuntimeError, "fpds_snapshot timed out after 120 seconds."):
                source_collection_runner._run_stage("worker.discovery.fpds_snapshot", ["--run-id", "run-001"])

    def test_stage_timeout_seconds_from_env_uses_floor_and_default(self) -> None:
        with patch.dict("os.environ", {"FPDS_SOURCE_COLLECTION_STAGE_TIMEOUT_SECONDS": "45"}, clear=False):
            self.assertEqual(source_collection_runner._stage_timeout_seconds_from_env(), 60)
        with patch.dict("os.environ", {"FPDS_SOURCE_COLLECTION_STAGE_TIMEOUT_SECONDS": "bad"}, clear=False):
            self.assertEqual(source_collection_runner._stage_timeout_seconds_from_env(), 1800)


if __name__ == "__main__":
    unittest.main()
