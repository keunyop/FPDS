from __future__ import annotations

import json
import os
import socket
import unittest
from pathlib import Path
from unittest.mock import patch

from worker.discovery.fpds_discovery.discovery import SourceDiscoveryService
from worker.discovery.fpds_discovery.fetch import DiscoveryFetchPolicy, FetchedResponse, fetch_response, fetch_text, validate_fetch_url
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
    def test_from_env_merges_extra_allowed_domains(self) -> None:
        with patch.dict(os.environ, {"FPDS_SOURCE_FETCH_ALLOWLIST": "td.com,tdcanadatrust.com"}, clear=False):
            policy = DiscoveryFetchPolicy.from_env(extra_allowed_domains=("bmo.com", "www.bmo.com"))

        self.assertEqual(policy.allowed_domains, ("td.com", "tdcanadatrust.com", "bmo.com", "www.bmo.com"))
        self.assertEqual(policy.timeout_seconds, 90)

    def test_from_env_reads_fetch_timeout_seconds(self) -> None:
        with patch.dict(
            os.environ,
            {
                "FPDS_SOURCE_FETCH_ALLOWLIST": "td.com",
                "FPDS_SOURCE_FETCH_TIMEOUT_SECONDS": "60",
            },
            clear=False,
        ):
            policy = DiscoveryFetchPolicy.from_env()

        self.assertEqual(policy.timeout_seconds, 60)

    def test_from_env_reads_browser_fallback_settings(self) -> None:
        with patch.dict(
            os.environ,
            {
                "FPDS_SOURCE_FETCH_ALLOWLIST": "bmo.com",
                "FPDS_SOURCE_BROWSER_FALLBACK_DOMAINS": "bmo.com,www.bmo.com",
                "FPDS_SOURCE_BROWSER_FALLBACK_TIMEOUT_SECONDS": "150",
                "FPDS_SOURCE_BROWSER_EXECUTABLE": r"C:\Browsers\msedge.exe",
            },
            clear=False,
        ):
            policy = DiscoveryFetchPolicy.from_env()

        self.assertEqual(policy.browser_fallback_domains, ("bmo.com", "www.bmo.com"))
        self.assertEqual(policy.browser_fallback_timeout_seconds, 150)
        self.assertEqual(policy.browser_executable, r"C:\Browsers\msedge.exe")

    def test_validate_fetch_url_allows_td_https_urls(self) -> None:
        policy = DiscoveryFetchPolicy(allowed_domains=("td.com",), block_private_networks=False)
        normalized = validate_fetch_url("https://www.td.com/ca/en/personal-banking/products/bank-accounts/account-rates", policy)
        self.assertEqual(normalized, "https://www.td.com/ca/en/personal-banking/products/bank-accounts/account-rates")

    def test_validate_fetch_url_upgrades_allowlisted_http_to_https(self) -> None:
        policy = DiscoveryFetchPolicy(allowed_domains=("td.com",), block_private_networks=False)
        normalized = validate_fetch_url("http://www.td.com/ca/en/personal-banking/products/bank-accounts/account-rates", policy)
        self.assertEqual(normalized, "https://www.td.com/ca/en/personal-banking/products/bank-accounts/account-rates")

    def test_validate_fetch_url_rejects_unapproved_domains(self) -> None:
        policy = DiscoveryFetchPolicy(allowed_domains=("td.com",), block_private_networks=False)
        with self.assertRaises(ValueError):
            validate_fetch_url("https://www.example.com/unapproved", policy)

    def test_fetch_response_uses_browser_pdf_fallback_for_eligible_timeout(self) -> None:
        policy = DiscoveryFetchPolicy(
            allowed_domains=("bmo.com",),
            block_private_networks=False,
            browser_fallback_domains=("bmo.com",),
            browser_fallback_timeout_seconds=30,
            browser_executable=r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        )
        temp_dir = _prepare_workspace_temp_dir("fetch-browser-fallback")

        class _FakeOpener:
            def open(self, request, timeout):
                raise socket.timeout("timed out")

        def fake_browser_run(command, capture_output, text, timeout, check, encoding, errors):
            del capture_output, text, timeout, check, encoding, errors
            output_flag = next(arg for arg in command if str(arg).startswith("--print-to-pdf="))
            output_path = Path(str(output_flag).split("=", 1)[1])
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_bytes(b"%PDF-1.4 browser fallback")
            return _CompletedProcess(returncode=0, stdout="", stderr="")

        with (
            patch("worker.discovery.fpds_discovery.fetch.urllib.request.build_opener", return_value=_FakeOpener()),
            patch("worker.discovery.fpds_discovery.fetch.tempfile.TemporaryDirectory", return_value=_TemporaryDirectoryStub(temp_dir)),
            patch("worker.discovery.fpds_discovery.fetch.subprocess.run", side_effect=fake_browser_run),
        ):
            response = fetch_response("https://www.bmo.com/main/personal/test/", policy)

        self.assertEqual(response.content_type, "application/pdf")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["x-fpds-fetch-method"], "browser_pdf_fallback")
        self.assertTrue(response.body.startswith(b"%PDF-1.4"))

    def test_fetch_text_rejects_non_html_fallback_payloads(self) -> None:
        policy = DiscoveryFetchPolicy(allowed_domains=("bmo.com",), block_private_networks=False)
        with patch(
            "worker.discovery.fpds_discovery.fetch.fetch_response",
            return_value=FetchedResponse(
                body=b"%PDF-1.4 browser fallback",
                final_url="https://www.bmo.com/main/personal/test/",
                content_type="application/pdf",
                status_code=200,
                headers={"content-type": "application/pdf"},
                fetched_at="2026-04-19T00:00:00+00:00",
                redirect_count=0,
            ),
        ):
            with self.assertRaises(ValueError):
                fetch_text("https://www.bmo.com/main/personal/test/", policy)


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


def _prepare_workspace_temp_dir(name: str) -> Path:
    root = Path("tmp") / name
    root.mkdir(parents=True, exist_ok=True)
    for child in root.iterdir():
        if child.is_file():
            child.unlink()
        elif child.is_dir():
            for nested in child.rglob("*"):
                if nested.is_file():
                    nested.unlink()
            for nested in sorted((item for item in child.rglob("*") if item.is_dir()), reverse=True):
                nested.rmdir()
            child.rmdir()
    return root.resolve()


class _TemporaryDirectoryStub:
    def __init__(self, path: Path) -> None:
        self.path = path

    def __enter__(self) -> str:
        self.path.mkdir(parents=True, exist_ok=True)
        return str(self.path)

    def __exit__(self, exc_type, exc, tb) -> None:
        return None


class _CompletedProcess:
    def __init__(self, *, returncode: int, stdout: str, stderr: str) -> None:
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr
