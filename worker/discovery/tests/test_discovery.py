from __future__ import annotations

import json
import unittest
from pathlib import Path

from worker.discovery.fpds_discovery.discovery import SourceDiscoveryService
from worker.discovery.fpds_discovery.fetch import DiscoveryFetchPolicy, validate_fetch_url
from worker.discovery.fpds_discovery.registry import DEFAULT_REGISTRY_PATH, load_registry
from worker.discovery.fpds_discovery.url_utils import (
    build_source_document_id,
    build_source_identity,
    normalize_source_url,
)

FIXTURE_DIR = Path(__file__).resolve().parent / "fixtures"


def read_fixture(name: str) -> str:
    return (FIXTURE_DIR / name).read_text(encoding="utf-8")


class UrlUtilsTests(unittest.TestCase):
    def test_normalize_source_url_removes_query_fragment_and_trailing_slash(self) -> None:
        url = "https://www.td.com/ca/en/path/?utm_source=test#top"
        self.assertEqual(normalize_source_url(url), "https://www.td.com/ca/en/path")

    def test_build_source_identity_and_id_are_stable(self) -> None:
        normalized = "https://www.td.com/ca/en/test"
        identity = build_source_identity("TD", normalized, "html")
        document_id = build_source_document_id("TD", normalized, "html")
        self.assertEqual(identity, "TD|https://www.td.com/ca/en/test|html")
        self.assertEqual(document_id, build_source_document_id("TD", normalized, "html"))


class FetchPolicyTests(unittest.TestCase):
    def test_validate_fetch_url_allows_td_https_urls(self) -> None:
        policy = DiscoveryFetchPolicy(allowed_domains=("td.com",), block_private_networks=False)
        validate_fetch_url("https://www.td.com/ca/en/personal-banking/products/bank-accounts/account-rates", policy)

    def test_validate_fetch_url_rejects_non_https(self) -> None:
        policy = DiscoveryFetchPolicy(allowed_domains=("td.com",), block_private_networks=False)
        with self.assertRaises(ValueError):
            validate_fetch_url("http://www.td.com/ca/en/personal-banking/products/bank-accounts/account-rates", policy)

    def test_validate_fetch_url_rejects_unapproved_domains(self) -> None:
        policy = DiscoveryFetchPolicy(allowed_domains=("td.com",), block_private_networks=False)
        with self.assertRaises(ValueError):
            validate_fetch_url("https://www.example.com/unapproved", policy)


class DiscoveryServiceTests(unittest.TestCase):
    def test_discovery_output_covers_registry_and_expected_warnings(self) -> None:
        registry = load_registry(DEFAULT_REGISTRY_PATH)
        service = SourceDiscoveryService(registry)
        entry_html = read_fixture("td_savings_entry.html")
        html_overrides = {
            normalize_source_url(registry.by_source_id("TD-SAV-002").url): read_fixture("td_every_day_detail.html"),
            normalize_source_url(registry.by_source_id("TD-SAV-003").url): read_fixture("td_epremium_detail.html"),
            normalize_source_url(registry.by_source_id("TD-SAV-004").url): read_fixture("td_growth_detail.html"),
            normalize_source_url(registry.by_source_id("TD-SAV-005").url): read_fixture("td_account_rates.html"),
            normalize_source_url(registry.by_source_id("TD-SAV-006").url): read_fixture("td_fee_summary.html"),
        }

        result = service.discover(
            entry_html=entry_html,
            html_overrides=html_overrides,
            run_id="run_20260409_0001",
            correlation_id="corr_20260409_0001",
            discovery_mode="manual",
        )

        self.assertEqual(len(result.selected_sources), 12)
        selected_by_id = {item.source_id: item for item in result.selected_sources}
        self.assertEqual(selected_by_id["TD-SAV-001"].selection_mode, "entry_seed")
        self.assertEqual(selected_by_id["TD-SAV-002"].selection_mode, "discovered_from_entry")
        self.assertEqual(selected_by_id["TD-SAV-003"].selection_mode, "discovered_from_entry")
        self.assertEqual(selected_by_id["TD-SAV-004"].selection_mode, "discovered_from_entry")
        self.assertEqual(selected_by_id["TD-SAV-007"].selection_mode, "discovered_from_linked_pdf")
        self.assertEqual(selected_by_id["TD-SAV-008"].selection_mode, "discovered_from_linked_pdf")
        self.assertEqual(selected_by_id["TD-SAV-012"].selection_mode, "discovered_from_linked_pdf")
        self.assertEqual(selected_by_id["TD-SAV-009"].discovery_status, "discovered")

        warning_codes = {warning.warning_code for warning in result.warnings}
        self.assertIn("compare_flow_link", warning_codes)
        self.assertIn("personalized_discovery_link", warning_codes)
        self.assertIn("cross_domain_link", warning_codes)
        self.assertIn("authenticated_flow_link", warning_codes)
        self.assertIn("out_of_registry_link", warning_codes)

        output = result.to_dict()
        self.assertEqual(output["run_id"], "run_20260409_0001")
        self.assertEqual(output["correlation_id"], "corr_20260409_0001")
        self.assertEqual(output["discovery_mode"], "manual")
        self.assertEqual(output["stats"]["selected_by_priority"]["P0"], 8)
        self.assertEqual(output["stats"]["selected_by_priority"]["P1"], 4)
        self.assertEqual(output["stats"]["selected_by_type"]["html"], 6)
        self.assertEqual(output["stats"]["selected_by_type"]["pdf"], 6)
        self.assertEqual(len(output["source_items"]), 12)

    def test_registry_json_is_loadable_and_ascii_serializable(self) -> None:
        registry = load_registry(DEFAULT_REGISTRY_PATH)
        payload = {
            "registry_version": registry.registry_version,
            "source_ids": [source.source_id for source in registry.sources],
        }
        encoded = json.dumps(payload, ensure_ascii=True)
        self.assertIn("TD-SAV-001", encoded)


if __name__ == "__main__":
    unittest.main()
