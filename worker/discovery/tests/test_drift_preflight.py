from __future__ import annotations

import unittest

from worker.discovery.fpds_discovery.drift import RegistryPreflightDriftService
from worker.discovery.fpds_discovery.fetch import DiscoveryFetchPolicy, FetchedResponse
from worker.discovery.fpds_discovery.registry import DEFAULT_REGISTRY_PATH, load_registry
from worker.discovery.fpds_snapshot.capture import CaptureSource


class RegistryPreflightDriftTests(unittest.TestCase):
    def setUp(self) -> None:
        self.registry = load_registry(DEFAULT_REGISTRY_PATH)
        self.fetch_policy = DiscoveryFetchPolicy(allowed_domains=("td.com",), block_private_networks=False)

    def test_preflight_flags_final_url_change(self) -> None:
        source = CaptureSource.from_registry_source(self.registry.by_source_id("TD-SAV-007"))
        service = RegistryPreflightDriftService(
            fetch_policy=self.fetch_policy,
            fetcher=lambda url, policy: _fetched_response(
                final_url="https://www.td.com/content/dam/tdct/document/pdf/econsent/accounts/513796.pdf",
                content_type="application/pdf",
            ),
        )

        result = service.check_sources(run_id="run_preflight_001", sources=[source])

        check = result.checks[0]
        self.assertEqual(check.status, "warning")
        self.assertEqual(check.issues[0].issue_code, "final_url_changed")

    def test_preflight_flags_content_type_change(self) -> None:
        source = CaptureSource.from_registry_source(self.registry.by_source_id("TD-SAV-007"))
        service = RegistryPreflightDriftService(
            fetch_policy=self.fetch_policy,
            fetcher=lambda url, policy: _fetched_response(
                final_url=source.resolved_url,
                content_type="text/html",
            ),
        )

        result = service.check_sources(run_id="run_preflight_002", sources=[source])

        check = result.checks[0]
        self.assertEqual(check.status, "warning")
        self.assertEqual(check.issues[0].issue_code, "content_type_changed")

    def test_preflight_marks_fetch_failure_as_error(self) -> None:
        source = CaptureSource.from_registry_source(self.registry.by_source_id("TD-SAV-004"))
        service = RegistryPreflightDriftService(
            fetch_policy=self.fetch_policy,
            fetcher=lambda url, policy: (_ for _ in ()).throw(RuntimeError("simulated preflight failure")),
        )

        result = service.check_sources(run_id="run_preflight_003", sources=[source])

        check = result.checks[0]
        self.assertEqual(check.status, "error")
        self.assertEqual(check.issues[0].issue_code, "fetch_failed")


def _fetched_response(*, final_url: str, content_type: str) -> FetchedResponse:
    return FetchedResponse(
        body=b"payload",
        final_url=final_url,
        content_type=content_type,
        status_code=200,
        headers={},
        fetched_at="2026-04-10T00:00:00+00:00",
        redirect_count=0,
    )


if __name__ == "__main__":
    unittest.main()
