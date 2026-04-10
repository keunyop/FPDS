from __future__ import annotations

import unittest

from worker.discovery.fpds_discovery.fetch import DiscoveryFetchPolicy, FetchedResponse
from worker.discovery.fpds_discovery.registry import DEFAULT_REGISTRY_PATH, load_registry
from worker.discovery.fpds_snapshot.capture import (
    CaptureSource,
    ExistingSnapshotRecord,
    SnapshotCaptureService,
    _build_checksum,
    _build_fingerprint,
)
from worker.discovery.fpds_snapshot.storage import SnapshotStorageConfig


class SnapshotCaptureTests(unittest.TestCase):
    def setUp(self) -> None:
        self.registry = load_registry(DEFAULT_REGISTRY_PATH)
        self.fetch_policy = DiscoveryFetchPolicy(allowed_domains=("td.com",), block_private_networks=False)

    def test_capture_stores_html_and_pdf_snapshots_with_expected_metadata(self) -> None:
        html_source = CaptureSource.from_registry_source(self.registry.by_source_id("TD-SAV-002"))
        pdf_source = CaptureSource.from_registry_source(self.registry.by_source_id("TD-SAV-007"))

        responses = {
            html_source.resolved_url: _fetched_response(
                body=b"<html><body>Every Day Savings</body></html>",
                content_type="text/html",
                final_url=html_source.resolved_url,
            ),
            pdf_source.resolved_url: _fetched_response(
                body=b"%PDF-1.4 fake td fee schedule",
                content_type="application/pdf",
                final_url=pdf_source.resolved_url,
            ),
        }

        object_store = _RecordingObjectStore()
        service = SnapshotCaptureService(
            fetch_policy=self.fetch_policy,
            storage_config=SnapshotStorageConfig(
                driver="filesystem",
                env_prefix="dev",
                snapshot_object_prefix="snapshots",
                retention_class="hot",
                filesystem_root="ignored-for-tests",
            ),
            object_store=object_store,
            fetcher=lambda url, policy: responses[url],
        )

        result = service.capture_sources(
            run_id="run_20260409_0100",
            correlation_id="corr_20260409_0100",
            sources=[html_source, pdf_source],
        )

        self.assertFalse(result.partial_completion_flag)
        self.assertEqual(len(result.source_results), 2)
        stored_results = [item for item in result.source_results if item.snapshot_action == "stored"]
        self.assertEqual(len(stored_results), 2)
        self.assertEqual(len(object_store.writes), 2)

        for item in stored_results:
            self.assertIsNotNone(item.source_snapshot_record)
            self.assertEqual(item.run_source_item_record["stage_status"], "completed")
            self.assertTrue(str(item.run_source_item_record["run_source_item_id"]).startswith("rsi-"))
            self.assertTrue(str(item.object_storage_key).startswith("dev/snapshots/CA/TD/"))

    def test_capture_reuses_existing_snapshot_when_fingerprint_matches(self) -> None:
        source = CaptureSource.from_registry_source(self.registry.by_source_id("TD-SAV-007"))
        body = b"%PDF-1.4 reused fee schedule"
        fetched = _fetched_response(
            body=body,
            content_type="application/pdf",
            final_url=source.resolved_url,
        )

        existing = ExistingSnapshotRecord(
            snapshot_id="snap-existing-001",
            source_document_id=source.source_document_id,
            object_storage_key="dev/snapshots/CA/TD/source/snap-existing-001/raw",
            content_type="application/pdf",
            checksum=_build_checksum(body),
            fingerprint=_build_fingerprint(body, "application/pdf"),
            fetch_status="fetched",
            response_metadata={},
            retention_class="hot",
            fetched_at="2026-04-09T00:00:00+00:00",
        )

        object_store = _RecordingObjectStore()
        service = SnapshotCaptureService(
            fetch_policy=self.fetch_policy,
            storage_config=SnapshotStorageConfig(
                driver="filesystem",
                env_prefix="dev",
                snapshot_object_prefix="snapshots",
                retention_class="hot",
                filesystem_root="ignored-for-tests",
            ),
            object_store=object_store,
            fetcher=lambda url, policy: fetched,
        )

        result = service.capture_sources(
            run_id="run_20260409_0101",
            sources=[source],
            existing_snapshots=[existing],
        )

        item = result.source_results[0]
        self.assertEqual(item.snapshot_action, "reused")
        self.assertEqual(item.snapshot_id, existing.snapshot_id)
        self.assertIsNone(item.source_snapshot_record)
        self.assertEqual(item.run_source_item_record["stage_status"], "completed")
        self.assertEqual(object_store.writes, [])

    def test_capture_marks_partial_completion_when_source_fails_after_retries(self) -> None:
        source = CaptureSource.from_registry_source(self.registry.by_source_id("TD-SAV-004"))
        attempts = {"count": 0}

        def flaky_fetcher(url: str, policy: DiscoveryFetchPolicy) -> FetchedResponse:
            attempts["count"] += 1
            raise RuntimeError("simulated network failure")

        service = SnapshotCaptureService(
            fetch_policy=self.fetch_policy,
            storage_config=SnapshotStorageConfig(
                driver="filesystem",
                env_prefix="dev",
                snapshot_object_prefix="snapshots",
                retention_class="hot",
                filesystem_root="ignored-for-tests",
            ),
            object_store=_RecordingObjectStore(),
            fetcher=flaky_fetcher,
            max_attempts=3,
        )

        result = service.capture_sources(
            run_id="run_20260409_0102",
            sources=[source],
        )

        self.assertTrue(result.partial_completion_flag)
        item = result.source_results[0]
        self.assertEqual(item.snapshot_action, "failed")
        self.assertEqual(item.attempt_count, 3)
        self.assertEqual(item.run_source_item_record["stage_status"], "failed")


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
    def __init__(self) -> None:
        self.writes: list[tuple[str, bytes, str]] = []

    def put_object(self, *, object_key: str, data: bytes, content_type: str) -> None:
        self.writes.append((object_key, data, content_type))


if __name__ == "__main__":
    unittest.main()
