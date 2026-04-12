from __future__ import annotations

import unittest
from pathlib import Path

from worker.discovery.fpds_discovery.discovery import SelectedSource, SourceDiscoveryService
from worker.discovery.fpds_discovery.drift import DriftIssue, PreflightDriftResult, SourcePreflightCheck
from worker.discovery.fpds_discovery.fetch import DiscoveryFetchPolicy
from worker.discovery.fpds_discovery.registry import DEFAULT_REGISTRY_PATH, load_registry
from worker.discovery.fpds_discovery.url_utils import normalize_source_url
from worker.discovery.fpds_registry_refresh.service import RegistryRefreshService

FIXTURE_DIR = Path(__file__).resolve().parent / "fixtures"


def read_fixture(name: str) -> str:
    return (FIXTURE_DIR / name).read_text(encoding="utf-8")


class RegistryRefreshServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.registry = load_registry(DEFAULT_REGISTRY_PATH)
        self.fetch_policy = DiscoveryFetchPolicy(allowed_domains=("td.com",), block_private_networks=False)

    def test_refresh_builds_candidate_diffs_from_discovery_and_preflight(self) -> None:
        discovery_service = SourceDiscoveryService(self.registry)
        entry_html = read_fixture("td_savings_entry.html")
        html_overrides = {
            normalize_source_url(self.registry.by_source_id("TD-SAV-002").url): read_fixture("td_every_day_detail.html"),
            normalize_source_url(self.registry.by_source_id("TD-SAV-003").url): read_fixture("td_epremium_detail.html"),
            normalize_source_url(self.registry.by_source_id("TD-SAV-004").url): read_fixture("td_growth_detail.html"),
            normalize_source_url(self.registry.by_source_id("TD-SAV-005").url): read_fixture("td_account_rates.html"),
            normalize_source_url(self.registry.by_source_id("TD-SAV-006").url): read_fixture("td_fee_summary.html"),
        }
        discovery_result = discovery_service.discover(
            entry_html=entry_html,
            html_overrides=html_overrides,
            run_id="run_refresh_001",
            correlation_id="corr_refresh_001",
            discovery_mode="scheduled",
        )
        for index, item in enumerate(discovery_result.selected_sources):
            if item.source_id != "TD-SAV-004":
                continue
            discovery_result.selected_sources[index] = SelectedSource.from_registry_source(
                self.registry.by_source_id("TD-SAV-004"),
                selection_mode="seed_only",
                discovery_status="seed_only",
                discovery_notes=["forced missing discovery state for refresh test"],
            )
            break
        preflight_result = PreflightDriftResult(
            run_id="run_refresh_001",
            correlation_id="corr_refresh_001",
            request_id=None,
            checks=[
                SourcePreflightCheck(
                    source_id="TD-SAV-007",
                    source_document_id=self.registry.by_source_id("TD-SAV-007").source_document_id,
                    expected_url=self.registry.by_source_id("TD-SAV-007").normalized_url,
                    expected_source_type="pdf",
                    status="warning",
                    fetched_at="2026-04-10T00:00:00+00:00",
                    final_url="https://www.td.com/content/dam/tdct/document/pdf/econsent/accounts/513796.pdf",
                    normalized_final_url="https://www.td.com/content/dam/tdct/document/pdf/econsent/accounts/513796.pdf",
                    status_code=200,
                    content_type="application/pdf",
                    redirect_count=1,
                    error_summary=None,
                    issues=[
                        DriftIssue(
                            source_id="TD-SAV-007",
                            source_document_id=self.registry.by_source_id("TD-SAV-007").source_document_id,
                            issue_code="final_url_changed",
                            severity="warning",
                            expected_url=self.registry.by_source_id("TD-SAV-007").normalized_url,
                            detected_url="https://www.td.com/content/dam/tdct/document/pdf/econsent/accounts/513796.pdf",
                            expected_source_type="pdf",
                            detected_content_type="application/pdf",
                            message="Final fetched URL differs from the approved active registry URL.",
                        )
                    ],
                )
            ],
        )

        refresh_service = RegistryRefreshService(
            registry=self.registry,
            fetch_policy=self.fetch_policy,
            discovery_service=discovery_service,
        )
        result = refresh_service.build_result(
            run_id="run_refresh_001",
            correlation_id="corr_refresh_001",
            discovery_result=discovery_result,
            preflight_result=preflight_result,
        )

        change_types = {item.change_type for item in result.candidate_diffs}
        self.assertIn("new_source_candidate", change_types)
        self.assertIn("source_missing_from_discovery", change_types)
        self.assertIn("redirect_detected", change_types)


if __name__ == "__main__":
    unittest.main()
