from __future__ import annotations

import json
import os
import unittest
from pathlib import Path
from shutil import rmtree

from worker.discovery.env import load_env_file, resolve_default_env_file
from worker.discovery.fpds_discovery.fetch import DiscoveryFetchPolicy, FetchedResponse
from worker.discovery.fpds_discovery.registry import DEFAULT_REGISTRY_PATH, load_registry
from worker.discovery.fpds_snapshot.capture import CaptureSource, SnapshotCaptureService
from worker.discovery.fpds_snapshot.persistence import (
    PsqlSnapshotRepository,
    SnapshotDatabaseConfig,
)
from worker.discovery.fpds_snapshot.storage import SnapshotStorageConfig


class SnapshotPersistenceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.registry = load_registry(DEFAULT_REGISTRY_PATH)
        self.fetch_policy = DiscoveryFetchPolicy(allowed_domains=("td.com",), block_private_networks=False)

    def test_load_existing_snapshots_reads_json_rows_from_psql_output(self) -> None:
        source = CaptureSource.from_registry_source(self.registry.by_source_id("TD-SAV-007"))
        runner = _FakeRunner(
            outputs=[
                "public",
                json.dumps(
                    [
                        {
                            "snapshot_id": "snap-existing-001",
                            "source_document_id": source.source_document_id,
                            "object_storage_key": "dev/snapshots/CA/TD/source/snap-existing-001/raw",
                            "content_type": "application/pdf",
                            "checksum": "abc",
                            "fingerprint": "def",
                            "fetch_status": "fetched",
                            "response_metadata": {"status_code": 200},
                            "retention_class": "hot",
                            "fetched_at": "2026-04-09T00:00:00+00:00",
                        }
                    ]
                )
            ]
        )
        repository = PsqlSnapshotRepository(
            SnapshotDatabaseConfig(database_url="postgres://example", schema="public"),
            command_runner=runner,
        )

        records = repository.load_existing_snapshots(source_document_ids=[source.source_document_id])

        self.assertEqual(len(records), 1)
        self.assertEqual(records[0].snapshot_id, "snap-existing-001")
        variables = runner.last_variables()
        self.assertEqual(
            json.loads(variables["source_document_ids_json"]),
            [source.source_document_id],
        )

    def test_persist_capture_result_batches_source_documents_snapshots_and_run_items(self) -> None:
        stored_source = CaptureSource.from_registry_source(self.registry.by_source_id("TD-SAV-002"))
        failed_source = CaptureSource.from_registry_source(self.registry.by_source_id("TD-SAV-004"))
        object_store = _RecordingObjectStore()
        responses = {
            stored_source.resolved_url: _fetched_response(
                body=b"<html><body>stored</body></html>",
                content_type="text/html",
                final_url=stored_source.resolved_url,
            ),
        }

        def fetcher(url: str, policy: DiscoveryFetchPolicy) -> FetchedResponse:
            if url in responses:
                return responses[url]
            raise RuntimeError("simulated failure")

        capture_service = SnapshotCaptureService(
            fetch_policy=self.fetch_policy,
            storage_config=SnapshotStorageConfig(
                driver="filesystem",
                env_prefix="dev",
                snapshot_object_prefix="snapshots",
                retention_class="hot",
                filesystem_root="ignored-for-tests",
            ),
            object_store=object_store,
            fetcher=fetcher,
            max_attempts=2,
        )
        capture_result = capture_service.capture_sources(
            run_id="run_20260409_0200",
            correlation_id="corr_20260409_0200",
            request_id="req_20260409_0200",
            sources=[stored_source, failed_source],
        )

        runner = _FakeRunner(outputs=["public", ""])
        repository = PsqlSnapshotRepository(
            SnapshotDatabaseConfig(database_url="postgres://example", schema="public"),
            command_runner=runner,
        )

        persisted = repository.persist_capture_result(
            run_id="run_20260409_0200",
            sources=[stored_source, failed_source],
            capture_result=capture_result,
            trigger_type="manual",
            triggered_by="codex",
            started_at="2026-04-09T00:00:00+00:00",
            completed_at="2026-04-09T00:01:00+00:00",
        )

        self.assertEqual(persisted.run_state, "completed")
        self.assertTrue(persisted.partial_completion_flag)
        self.assertEqual(persisted.source_document_count, 2)
        self.assertEqual(persisted.stored_snapshot_count, 1)
        self.assertEqual(persisted.run_source_item_count, 2)

        variables = runner.last_variables()
        source_documents = json.loads(variables["source_documents_json"])
        self.assertEqual(len(source_documents), 2)
        self.assertTrue(source_documents[0]["registry_managed_flag"])
        self.assertIn("source_id", source_documents[0]["source_metadata"])

        run_source_items = json.loads(variables["run_source_items_json"])
        self.assertEqual(len(run_source_items), 2)
        self.assertTrue(run_source_items[0]["run_source_item_id"].startswith("rsi-"))
        self.assertEqual(variables["run_state"], "completed")
        self.assertEqual(variables["source_failure_count"], "1")


class EnvLoaderTests(unittest.TestCase):
    def test_load_env_file_sets_values_without_overwriting_existing_env(self) -> None:
        temp_path = _prepare_workspace_temp_dir("env-loader-a")
        try:
            path = temp_path / ".env.dev"
            path.write_text(
                "\n".join(
                    [
                        "# comment",
                        "FPDS_ENV=dev",
                        "FPDS_RUNTIME_LABEL='local-dev'",
                    ]
                ),
                encoding="utf-8",
            )
            original = os.environ.get("FPDS_ENV")
            os.environ["FPDS_ENV"] = "preexisting"
            try:
                loaded = load_env_file(path)
                self.assertEqual(loaded["FPDS_RUNTIME_LABEL"], "local-dev")
                self.assertEqual(os.environ["FPDS_ENV"], "preexisting")
            finally:
                if original is None:
                    os.environ.pop("FPDS_ENV", None)
                else:
                    os.environ["FPDS_ENV"] = original
        finally:
            rmtree(temp_path, ignore_errors=True)

    def test_load_env_file_can_override_existing_env_when_requested(self) -> None:
        temp_path = _prepare_workspace_temp_dir("env-loader-c")
        try:
            path = temp_path / ".env.dev"
            path.write_text("FPDS_ENV=dev\n", encoding="utf-8")
            original = os.environ.get("FPDS_ENV")
            os.environ["FPDS_ENV"] = "preexisting"
            try:
                load_env_file(path, override=True)
                self.assertEqual(os.environ["FPDS_ENV"], "dev")
            finally:
                if original is None:
                    os.environ.pop("FPDS_ENV", None)
                else:
                    os.environ["FPDS_ENV"] = original
        finally:
            rmtree(temp_path, ignore_errors=True)

    def test_resolve_default_env_file_prefers_dot_env_dev(self) -> None:
        current = Path.cwd()
        temp_path = _prepare_workspace_temp_dir("env-loader-b")
        try:
            (temp_path / ".env.dev").write_text("FPDS_ENV=dev\n", encoding="utf-8")
            (temp_path / ".env").write_text("FPDS_ENV=fallback\n", encoding="utf-8")
            os.chdir(temp_path)
            try:
                self.assertEqual(resolve_default_env_file(), Path(".env.dev"))
            finally:
                os.chdir(current)
        finally:
            rmtree(temp_path, ignore_errors=True)


def _fetched_response(*, body: bytes, content_type: str, final_url: str) -> FetchedResponse:
    return FetchedResponse(
        body=body,
        final_url=final_url,
        content_type=content_type,
        status_code=200,
        headers={},
        fetched_at="2026-04-09T00:00:00+00:00",
        redirect_count=0,
    )


class _RecordingObjectStore:
    def put_object(self, *, object_key: str, data: bytes, content_type: str) -> None:
        return None


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
    path = Path("worker/discovery/tests/.tmp") / name
    rmtree(path, ignore_errors=True)
    path.mkdir(parents=True, exist_ok=True)
    return path


if __name__ == "__main__":
    unittest.main()
