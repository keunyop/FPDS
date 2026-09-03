from __future__ import annotations

import http.client
import json
import os
import socket
import unittest
import urllib.error
from pathlib import Path
from unittest.mock import patch

from worker.discovery.fpds_discovery.discovery import (
    SourceDiscoveryService,
    extract_links,
    extract_structured_text_sections,
)
from worker.discovery.fpds_discovery.fetch import (
    DiscoveryFetchPolicy,
    FetchedResponse,
    NonRetryableFetchError,
    _should_try_browser_rendered_rate_fallback,
    fetch_response,
    fetch_text,
    validate_fetch_url,
)
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

    def test_normalize_source_url_preserves_disclosure_document_identity(self) -> None:
        url = (
            "https://www.bankofamerica.com/salesservices/getDisclosurePDFInline"
            "?cId=4076236&isMobile=true&locale=en_US&poCd=D7&utm_source=test"
        )
        self.assertEqual(
            normalize_source_url(url),
            "https://www.bankofamerica.com/salesservices/getDisclosurePDFInline?cid=4076236&pocd=D7",
        )

    def test_normalize_source_url_preserves_market_identity_but_not_campaign_id(self) -> None:
        self.assertEqual(
            normalize_source_url(
                "https://www.wellsfargo.com/savings-cds/platinum/?zipCode=98101&cid=campaign#rates"
            ),
            "https://www.wellsfargo.com/savings-cds/platinum?zipcode=98101",
        )

    def test_build_source_identity_and_id_are_stable(self) -> None:
        normalized = "https://www.td.com/ca/en/test"
        identity = build_source_identity("TD", normalized, "html")
        document_id = build_source_document_id("TD", normalized, "html")
        self.assertEqual(identity, "TD|https://www.td.com/ca/en/test|html")
        self.assertEqual(document_id, build_source_document_id("TD", normalized, "html"))

    def test_extract_links_reads_bounded_json_component_links(self) -> None:
        payload = {
            "products": [
                {
                    "name": "Customized Cash Rewards",
                    "learnMore": {"path": "products/cash-back-credit-card/"},
                },
                {
                    "title": "Travel Rewards",
                    "url": "https://www.bank.example/credit-cards/products/travel-rewards/",
                },
                {
                    "title": "Travel Rewards Pricing and Terms",
                    "disclosureUrl": "/disclosures/card?offerId=travel-42&locale=en_US",
                },
                {"title": "Template", "href": "/products/{productId}/"},
            ]
        }
        html = f"<div data-product-catalog='{json.dumps(payload)}'></div>"

        links = extract_links(html, base_url="https://www.bank.example/credit-cards/")

        self.assertEqual(
            [(link.normalized_url, link.anchor_text) for link in links],
            [
                (
                    "https://www.bank.example/credit-cards/products/cash-back-credit-card",
                    "Customized Cash Rewards",
                ),
                (
                    "https://www.bank.example/credit-cards/products/travel-rewards",
                    "Travel Rewards",
                ),
                (
                    "https://www.bank.example/disclosures/card?offerid=travel-42",
                    "Travel Rewards Pricing and Terms",
                ),
            ],
        )

    def test_extract_links_reads_td_aem_card_description_route(self) -> None:
        html = """
        <div
          data-cardName="TD Cash Back Visa Infinite* Card"
          data-cardDescriptionUrl="/content/tdcom/ca/en/personal-banking/products/credit-cards/cash-back/cash-back-visa-infinite-card.html"
          data-cardType="cc"
        ></div>
        """

        links = extract_links(
            html,
            base_url="https://www.td.com/ca/en/personal-banking/products/credit-cards/cash-back",
        )

        self.assertEqual(
            [(link.normalized_url, link.anchor_text) for link in links],
            [
                (
                    "https://www.td.com/ca/en/personal-banking/products/credit-cards/cash-back/cash-back-visa-infinite-card",
                    "TD Cash Back Visa Infinite* Card",
                )
            ],
        )

    def test_td_aem_card_description_route_survives_ordinary_link_cap(self) -> None:
        ordinary_links = "".join(
            f'<a href="/navigation/{index}">Navigation {index}</a>'
            for index in range(300)
        )
        html = ordinary_links + """
        <div
          data-cardName="TD Cash Back Visa Infinite* Card"
          data-cardDescriptionUrl="/content/tdcom/ca/en/personal-banking/products/credit-cards/cash-back/cash-back-visa-infinite-card.html"
        ></div>
        """

        links = extract_links(html, base_url="https://www.td.com/")

        self.assertLessEqual(len(links), 256)
        self.assertIn(
            (
                "https://www.td.com/ca/en/personal-banking/products/credit-cards/cash-back/cash-back-visa-infinite-card",
                "TD Cash Back Visa Infinite* Card",
            ),
            [(link.normalized_url, link.anchor_text) for link in links],
        )

    def test_extract_links_reads_bounded_json_script_routes(self) -> None:
        payload = {
            "products": [
                {
                    "title": "Atlas High Interest Savings",
                    "url": "https://www.atlas.example/banking/savings-account/",
                },
                {
                    "headline": "Harbor Fixed Mortgage",
                    "cta": {"targetUrl": "/mortgages/fixed-rate/"},
                },
                {"title": "Template", "targetUrl": "/products/{productId}/"},
                {"title": "Decorative asset", "_path": "/assets/product-card.png"},
            ]
        }
        html = (
            f'<script type="application/json" id="ssr-state">{json.dumps(payload)}</script>'
            '<script>{"title":"Executable config","url":"/must-not-run"}</script>'
        )

        links = extract_links(html, base_url="https://www.atlas.example/")

        self.assertEqual(
            [(link.normalized_url, link.anchor_text) for link in links],
            [
                (
                    "https://www.atlas.example/banking/savings-account",
                    "Atlas High Interest Savings",
                ),
                (
                    "https://www.atlas.example/mortgages/fixed-rate",
                    "Harbor Fixed Mortgage",
                ),
            ],
        )

    def test_extract_links_associates_sitecore_wrapped_product_title_with_details_link(self) -> None:
        payload = {
            "componentName": "ProductCard",
            "fields": {
                "Title": {"jsonValue": {"value": "Essential Chequing"}},
                "Link": {
                    "jsonValue": {
                        "value": {
                            "text": "Details",
                            "url": "/public-sites/www/Home/Bank/Accounts/Essential",
                            "href": "/bank/accounts/essential",
                        }
                    }
                },
            },
        }
        html = f'<script type="application/json">{json.dumps(payload)}</script>'

        links = extract_links(html, base_url="https://www.vancity.com/bank/accounts")

        self.assertIn(
            (
                "https://www.vancity.com/bank/accounts/essential",
                "Essential Chequing",
            ),
            [(link.normalized_url, link.anchor_text) for link in links],
        )
        self.assertNotIn(
            "https://www.vancity.com/public-sites/www/Home/Bank/Accounts/Essential",
            [link.normalized_url for link in links],
        )

    def test_extract_structured_text_sections_reads_component_copy(self) -> None:
        payload = {
            "title": "Advantage Savings",
            "content": "<p>$8 monthly fee, waived with an eligible balance.</p>",
            "config": {"endpoint": "https://api.bank.example/internal"},
        }
        html = f"<div data-product='{json.dumps(payload)}'></div>"

        self.assertEqual(
            extract_structured_text_sections(html),
            [
                "Advantage Savings",
                "$8 monthly fee, waived with an eligible balance.",
            ],
        )

    def test_extract_structured_text_sections_reads_json_script_copy(self) -> None:
        payload = {
            "title": "Harbor Fixed Mortgage",
            "description": "A five-year fixed mortgage with monthly payment options.",
            "config": {"endpoint": "https://api.harbor.example/internal"},
        }
        html = f'<script type="application/ld+json">{json.dumps(payload)}</script>'

        self.assertEqual(
            extract_structured_text_sections(html),
            [
                "Harbor Fixed Mortgage",
                "A five-year fixed mortgage with monthly payment options.",
            ],
        )

    def test_extract_structured_text_sections_preserves_embedded_us_pricing_fields(self) -> None:
        payload = {
            "productName": "Travel Rewards Credit Card",
            "purchaseApr": "19.49% to 29.49% variable APR",
            "annualFee": "$0",
            "rateCard": {"label": "Savings APY", "value": "4.10%"},
        }
        html = f"<div data-product='{json.dumps(payload)}'></div>"

        self.assertEqual(
            extract_structured_text_sections(html),
            [
                "Travel Rewards Credit Card",
                "purchase Apr: 19.49% to 29.49% variable APR",
                "annual Fee: $0",
                "Savings APY",
                "Savings APY: 4.10%",
            ],
        )

    def test_extract_structured_text_sections_preserves_sitecore_product_condition_context(self) -> None:
        payload = {
            "__typename": "AccountProduct",
            "Title": {"jsonValue": {"value": "Essential"}},
            "Description": {"jsonValue": {"value": "Get 25 Everyday Transactions per month."}},
            "MonthlyFee": {"jsonValue": {"value": 9.75}},
            "MinBalanceForFeeWaiver": {"jsonValue": {"value": 1500}},
            "IncludedTransactions": {"jsonValue": {"value": 25}},
            "PerTransactionFee": {"jsonValue": {"value": 1.25}},
        }
        html = f'<script type="application/json">{json.dumps(payload)}</script>'

        self.assertEqual(
            extract_structured_text_sections(html),
            [
                "Essential",
                "Essential - Description: Get 25 Everyday Transactions per month.",
                "Essential - Monthly Fee: 9.75",
                "Essential - Min Balance For Fee Waiver: 1500",
                "Essential - Included Transactions: 25",
                "Essential - Per Transaction Fee: 1.25",
            ],
        )


class FetchPolicyTests(unittest.TestCase):
    def test_from_env_default_browser_allowlist_covers_known_dynamic_rate_hosts(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            policy = DiscoveryFetchPolicy.from_env()

        self.assertEqual(
            policy.browser_fallback_domains,
            (
                "bmo.com",
                "www.bmo.com",
                "cibc.com",
                "www.cibc.com",
                "rbcroyalbank.com",
                "www.rbcroyalbank.com",
                "simplii.com",
                "www.simplii.com",
                "tangerine.ca",
                "www.tangerine.ca",
                "vancity.com",
                "www.vancity.com",
                "bankofamerica.com",
                "capitalone.com",
                "chase.com",
                "citi.com",
                "marcus.com",
                "pnc.com",
                "td.com",
                "truist.com",
                "usbank.com",
                "wellsfargo.com",
            ),
        )
        self.assertEqual(
            policy.browser_dom_snapshot_domains,
            ("vancity.com", "www.vancity.com"),
        )

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
                "FPDS_SOURCE_BROWSER_DOM_SNAPSHOT_DOMAINS": "vancity.com,www.vancity.com",
                "FPDS_SOURCE_BROWSER_EXECUTABLE": r"C:\Browsers\msedge.exe",
            },
            clear=False,
        ):
            policy = DiscoveryFetchPolicy.from_env()

        self.assertEqual(policy.browser_fallback_domains, ("bmo.com", "www.bmo.com"))
        self.assertEqual(policy.browser_fallback_timeout_seconds, 150)
        self.assertEqual(policy.browser_dom_snapshot_domains, ("vancity.com", "www.vancity.com"))
        self.assertEqual(policy.browser_executable, r"C:\Browsers\msedge.exe")

    def test_from_env_preserves_explicit_bank_fetch_boundary_with_browser_policy(self) -> None:
        with patch.dict(
            os.environ,
            {
                "FPDS_SOURCE_FETCH_ALLOWLIST": "td.com,tdcanadatrust.com",
                "FPDS_SOURCE_BROWSER_FALLBACK_DOMAINS": "vancity.com,www.vancity.com",
            },
            clear=False,
        ):
            policy = DiscoveryFetchPolicy.from_env(allowed_domains=("Vancity.com",))

        self.assertEqual(policy.allowed_domains, ("vancity.com",))
        self.assertEqual(policy.browser_fallback_domains, ("vancity.com", "www.vancity.com"))

    def test_default_browser_fallback_covers_observed_dynamic_rate_domains(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            policy = DiscoveryFetchPolicy.from_env()

        self.assertEqual(
            policy.browser_fallback_domains,
            (
                "bmo.com",
                "www.bmo.com",
                "cibc.com",
                "www.cibc.com",
                "rbcroyalbank.com",
                "www.rbcroyalbank.com",
                "simplii.com",
                "www.simplii.com",
                "tangerine.ca",
                "www.tangerine.ca",
                "vancity.com",
                "www.vancity.com",
                "bankofamerica.com",
                "capitalone.com",
                "chase.com",
                "citi.com",
                "marcus.com",
                "pnc.com",
                "td.com",
                "truist.com",
                "usbank.com",
                "wellsfargo.com",
            ),
        )

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

    def test_transport_failure_uses_browser_dom_on_any_official_domain(self) -> None:
        url = "https://www.examplebank.ca/accounts/savings"
        policy = DiscoveryFetchPolicy(
            allowed_domains=("examplebank.ca",),
            block_private_networks=False,
            browser_fallback_domains=(),
        )
        rendered = FetchedResponse(
            body=b"<html><h1>Everyday Savings</h1></html>",
            final_url=url,
            content_type="text/html",
            status_code=200,
            headers={"content-type": "text/html; charset=utf-8"},
            fetched_at="2026-09-02T00:00:00+00:00",
            redirect_count=0,
        )
        for failure in (
            socket.timeout("timed out"),
            ConnectionResetError("connection reset"),
            http.client.RemoteDisconnected("remote end closed connection without response"),
        ):
            with self.subTest(failure=type(failure).__name__):
                opener = type(
                    "Opener",
                    (),
                    {"open": lambda self, request, timeout, error=failure: (_ for _ in ()).throw(error)},
                )()
                with (
                    patch("worker.discovery.fpds_discovery.fetch.urllib.request.build_opener", return_value=opener),
                    patch(
                        "worker.discovery.fpds_discovery.fetch._fetch_response_via_browser",
                        return_value=rendered,
                    ) as browser,
                ):
                    response = fetch_response(url, policy)

                self.assertEqual(response.body, rendered.body)
                self.assertEqual(response.headers["x-fpds-browser-fallback-reason"], "direct_transport_failure")
                self.assertEqual(browser.call_args.kwargs["output_format"], "html")

    def test_transport_fallback_rejects_browser_access_challenge(self) -> None:
        url = "https://www.examplebank.ca/accounts/savings"
        policy = DiscoveryFetchPolicy(
            allowed_domains=("examplebank.ca",),
            block_private_networks=False,
            browser_fallback_domains=(),
        )
        opener = type(
            "Opener",
            (),
            {"open": lambda self, request, timeout: (_ for _ in ()).throw(socket.timeout("timed out"))},
        )()
        rendered_challenge = FetchedResponse(
            body=(
                b"<html><title>Pardon Our Interruption</title>"
                b"<h1>Security check: JavaScript disabled</h1>"
                b"<script>window.reeseSkipExpirationCheck=true;</script></html>"
            ),
            final_url=url,
            content_type="text/html",
            status_code=200,
            headers={"content-type": "text/html; charset=utf-8"},
            fetched_at="2026-09-02T00:00:00+00:00",
            redirect_count=0,
        )
        with (
            patch("worker.discovery.fpds_discovery.fetch.urllib.request.build_opener", return_value=opener),
            patch(
                "worker.discovery.fpds_discovery.fetch._fetch_response_via_browser",
                return_value=rendered_challenge,
            ),
        ):
            with self.assertRaisesRegex(NonRetryableFetchError, "remained after bounded browser fallback"):
                fetch_response(url, policy)

    def test_fetch_response_uses_browser_fallback_for_403_on_any_allowlisted_official_domain(self) -> None:
        policy = DiscoveryFetchPolicy(
            allowed_domains=("examplebank.ca",),
            block_private_networks=False,
            browser_fallback_domains=(),
        )

        class _FakeOpener:
            def open(self, request, timeout):
                del timeout
                raise urllib.error.HTTPError(request.full_url, 403, "Forbidden", None, None)

        rendered = FetchedResponse(
            body=b"%PDF-1.4 allowlisted 403 fallback",
            final_url="https://www.examplebank.ca/products/gic",
            content_type="application/pdf",
            status_code=200,
            headers={"x-fpds-fetch-method": "browser_pdf_fallback"},
            fetched_at="2026-08-26T00:00:00+00:00",
            redirect_count=0,
        )
        with (
            patch(
                "worker.discovery.fpds_discovery.fetch.urllib.request.build_opener",
                return_value=_FakeOpener(),
            ),
            patch(
                "worker.discovery.fpds_discovery.fetch._fetch_response_via_browser",
                return_value=rendered,
            ) as browser,
        ):
            response = fetch_response(
                "https://www.examplebank.ca/products/gic",
                policy,
            )

        self.assertEqual(response, rendered)
        browser.assert_called_once()

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

    def test_http_200_access_challenge_uses_browser_dom_on_any_official_domain(self) -> None:
        url = "https://www.examplebank.ca/accounts/savings"
        policy = DiscoveryFetchPolicy(
            allowed_domains=("examplebank.ca",),
            block_private_networks=False,
            browser_fallback_domains=(),
        )
        challenge = (
            b"<html><title>Pardon Our Interruption</title>"
            b"<h1>Security check: JavaScript disabled</h1>"
            b"<script>window.reeseSkipExpirationCheck=true;</script></html>"
        )
        rendered = FetchedResponse(
            body=b"<html><h1>Everyday Savings Account</h1><p>APY 2.00%</p></html>",
            final_url=url,
            content_type="text/html",
            status_code=200,
            headers={"content-type": "text/html; charset=utf-8"},
            fetched_at="2026-09-02T00:00:00+00:00",
            redirect_count=0,
        )
        opener = type("Opener", (), {"open": lambda self, request, timeout: _DirectHtmlResponse(body=challenge, url=url)})()
        with (
            patch("worker.discovery.fpds_discovery.fetch.urllib.request.build_opener", return_value=opener),
            patch("worker.discovery.fpds_discovery.fetch._fetch_response_via_browser", return_value=rendered) as browser,
        ):
            response = fetch_response(url, policy)

        self.assertIn(b"Everyday Savings Account", response.body)
        self.assertEqual(response.headers["x-fpds-browser-fallback-reason"], "html_access_challenge")
        self.assertEqual(browser.call_args.kwargs["output_format"], "html")

    def test_http_200_access_challenge_never_returns_an_unresolved_shell(self) -> None:
        url = "https://www.examplebank.ca/accounts/savings"
        policy = DiscoveryFetchPolicy(
            allowed_domains=("examplebank.ca",),
            block_private_networks=False,
            browser_fallback_domains=(),
        )
        challenge = (
            b"<html><title>Pardon Our Interruption</title>"
            b"<h1>Security check: JavaScript disabled</h1>"
            b"<script>window.reeseSkipExpirationCheck=true;</script></html>"
        )
        opener = type("Opener", (), {"open": lambda self, request, timeout: _DirectHtmlResponse(body=challenge, url=url)})()
        rendered_challenge = FetchedResponse(
            body=challenge,
            final_url=url,
            content_type="text/html",
            status_code=200,
            headers={"content-type": "text/html; charset=utf-8"},
            fetched_at="2026-09-02T00:00:00+00:00",
            redirect_count=0,
        )
        with (
            patch("worker.discovery.fpds_discovery.fetch.urllib.request.build_opener", return_value=opener),
            patch(
                "worker.discovery.fpds_discovery.fetch._fetch_response_via_browser",
                side_effect=[rendered_challenge, RuntimeError("browser timed out")],
            ),
        ):
            with self.assertRaisesRegex(NonRetryableFetchError, "remained after bounded browser fallback"):
                fetch_response(url, policy)
            with self.assertRaisesRegex(NonRetryableFetchError, "browser fallback was unavailable"):
                fetch_response(url, policy)

    def test_fetch_text_uses_browser_html_fallback_for_eligible_429(self) -> None:
        policy = DiscoveryFetchPolicy(
            allowed_domains=("vancity.com",),
            block_private_networks=False,
            browser_fallback_domains=("vancity.com",),
            browser_fallback_timeout_seconds=30,
            browser_executable=r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        )
        temp_dir = _prepare_workspace_temp_dir("fetch-browser-html-fallback")

        class _FakeOpener:
            def open(self, request, timeout):
                del timeout
                raise urllib.error.HTTPError(request.full_url, 429, "Too Many Requests", None, None)

        def fake_browser_run(command, capture_output, text, timeout, check, encoding, errors):
            del capture_output, text, timeout, check, encoding, errors
            self.assertIn("--dump-dom", command)
            self.assertFalse(any(str(arg).startswith("--print-to-pdf=") for arg in command))
            return _CompletedProcess(
                returncode=0,
                stdout="<!doctype html><html><body><a href='/bank/accounts'>Accounts</a></body></html>",
                stderr="",
            )

        with (
            patch("worker.discovery.fpds_discovery.fetch.urllib.request.build_opener", return_value=_FakeOpener()),
            patch(
                "worker.discovery.fpds_discovery.fetch.tempfile.TemporaryDirectory",
                return_value=_TemporaryDirectoryStub(temp_dir),
            ),
            patch("worker.discovery.fpds_discovery.fetch.subprocess.run", side_effect=fake_browser_run),
        ):
            html = fetch_text("https://www.vancity.com/", policy)

        self.assertIn("/bank/accounts", html)

    def test_fetch_response_uses_configured_browser_dom_for_vancity_snapshot(self) -> None:
        policy = DiscoveryFetchPolicy(
            allowed_domains=("vancity.com",),
            block_private_networks=False,
            browser_fallback_domains=("vancity.com",),
            browser_dom_snapshot_domains=("vancity.com",),
        )

        class _FakeOpener:
            def open(self, request, timeout):
                del timeout
                raise urllib.error.HTTPError(request.full_url, 429, "Too Many Requests", None, None)

        rendered = FetchedResponse(
            body=b"<html><body>Essential - minimum balance 1500</body></html>",
            final_url="https://www.vancity.com/bank/accounts/essential",
            content_type="text/html",
            status_code=200,
            headers={"content-type": "text/html", "x-fpds-fetch-method": "browser_html_fallback"},
            fetched_at="2026-08-15T00:00:00+00:00",
            redirect_count=0,
        )
        with (
            patch("worker.discovery.fpds_discovery.fetch.urllib.request.build_opener", return_value=_FakeOpener()),
            patch("worker.discovery.fpds_discovery.fetch._fetch_response_via_browser", return_value=rendered) as browser,
        ):
            response = fetch_response("https://www.vancity.com/bank/accounts/essential", policy)

        self.assertEqual(response.content_type, "text/html")
        self.assertEqual(browser.call_args.kwargs["output_format"], "html")

    def test_rate_page_without_numeric_rates_requests_bounded_browser_rendering(self) -> None:
        policy = DiscoveryFetchPolicy(
            allowed_domains=("examplebank.ca",),
            block_private_networks=False,
            browser_fallback_domains=("examplebank.ca",),
        )
        shell = FetchedResponse(
            body=b"<html><title>Interest Rates</title><body><div id='rate-app'></div></body></html>",
            final_url="https://www.examplebank.ca/accounts/interest-rates/",
            content_type="text/html",
            status_code=200,
            headers={"content-type": "text/html; charset=utf-8"},
            fetched_at="2026-07-22T00:00:00+00:00",
            redirect_count=0,
        )
        rendered = FetchedResponse(
            **{
                **shell.__dict__,
                "body": b"<html><body>Interest Rate 0.50%</body></html>",
            }
        )

        self.assertTrue(_should_try_browser_rendered_rate_fallback(shell, policy))
        self.assertFalse(_should_try_browser_rendered_rate_fallback(rendered, policy))

    def test_non_rate_page_does_not_request_browser_rendering_for_missing_percentages(self) -> None:
        policy = DiscoveryFetchPolicy(
            allowed_domains=("examplebank.ca",),
            block_private_networks=False,
            browser_fallback_domains=("examplebank.ca",),
        )
        response = FetchedResponse(
            body=b"<html><body>Open a savings account today.</body></html>",
            final_url="https://www.examplebank.ca/accounts/savings/",
            content_type="text/html",
            status_code=200,
            headers={"content-type": "text/html"},
            fetched_at="2026-07-22T00:00:00+00:00",
            redirect_count=0,
        )

        self.assertFalse(_should_try_browser_rendered_rate_fallback(response, policy))

    def test_product_page_with_unresolved_rate_placeholder_requests_browser_rendering(self) -> None:
        policy = DiscoveryFetchPolicy(
            allowed_domains=("examplebank.ca",),
            block_private_networks=False,
            browser_fallback_domains=("examplebank.ca",),
        )
        response = FetchedResponse(
            body=(
                b"<html><body>Annual fee $0 Purchase interest rate "
                b"RDS%rate[2].CARD.Published(null,null,6,null)(#O2#)%</body></html>"
            ),
            final_url="https://www.examplebank.ca/credit-cards/cash-back-card.html",
            content_type="text/html",
            status_code=200,
            headers={"content-type": "text/html; charset=utf-8"},
            fetched_at="2026-07-22T00:00:00+00:00",
            redirect_count=0,
        )

        self.assertTrue(_should_try_browser_rendered_rate_fallback(response, policy))

    def test_us_product_pages_with_masked_or_location_gated_pricing_request_browser_rendering(self) -> None:
        policy = DiscoveryFetchPolicy(
            allowed_domains=("bankofamerica.com", "wellsfargo.com"),
            block_private_networks=False,
            browser_fallback_domains=("bankofamerica.com", "wellsfargo.com"),
        )
        masked_fee = FetchedResponse(
            body=b"<h1>Advantage Checking</h1><p>Monthly maintenance fee $XXXX or $0</p>",
            final_url="https://www.bankofamerica.com/deposits/checking/advantage-banking/",
            content_type="text/html",
            status_code=200,
            headers={"content-type": "text/html; charset=utf-8"},
            fetched_at="2026-08-12T00:00:00+00:00",
            redirect_count=0,
        )
        location_rate = FetchedResponse(
            body=(
                b"<h1>Premier Checking</h1><h2>Checking Interest Rates</h2>"
                b"<p>Annual Percentage Yield (APY)</p><p>Change location</p>"
            ),
            final_url="https://www.wellsfargo.com/checking/premier/",
            content_type="text/html",
            status_code=200,
            headers={"content-type": "text/html; charset=utf-8"},
            fetched_at="2026-08-12T00:00:00+00:00",
            redirect_count=0,
        )
        unresolved_card_fee = FetchedResponse(
            body=(
                b"<h1>Travel Rewards Credit Card</h1>"
                b"<p>Annual Percentage Rate: 18.24% - 28.24%</p>"
                b"{{{htmlEscaper INTEREST_RATES_FEES_STANDARD_ANNUAL_FEE_RESEARCH}}}"
            ),
            final_url="https://www.bankofamerica.com/credit-cards/products/travel-rewards-credit-card/",
            content_type="text/html",
            status_code=200,
            headers={"content-type": "text/html; charset=utf-8"},
            fetched_at="2026-08-12T00:00:00+00:00",
            redirect_count=0,
        )

        self.assertTrue(_should_try_browser_rendered_rate_fallback(masked_fee, policy))
        self.assertTrue(_should_try_browser_rendered_rate_fallback(location_rate, policy))
        self.assertTrue(_should_try_browser_rendered_rate_fallback(unresolved_card_fee, policy))

    def test_failed_rendered_rate_fallback_keeps_direct_snapshot_with_diagnostics(self) -> None:
        policy = DiscoveryFetchPolicy(
            allowed_domains=("examplebank.ca",),
            block_private_networks=False,
            browser_fallback_domains=("examplebank.ca",),
        )

        class _DirectHeaders(dict):
            def get_content_type(self):
                return "text/html"

        class _DirectPlaceholderResponse:
            status = 200
            headers = _DirectHeaders({"content-type": "text/html; charset=utf-8"})

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, traceback):
                return False

            def geturl(self):
                return "https://www.examplebank.ca/investments/gic.html"

            def read(self):
                return b"<html>1 year RDS%rate[5].GIC.Published(1_year)(#O3#)%</html>"

        class _FakeOpener:
            def open(self, request, timeout):
                del request, timeout
                return _DirectPlaceholderResponse()

        with (
            patch("worker.discovery.fpds_discovery.fetch.urllib.request.build_opener", return_value=_FakeOpener()),
            patch(
                "worker.discovery.fpds_discovery.fetch._fetch_response_via_browser",
                side_effect=RuntimeError("render timed out\nwith details"),
            ),
        ):
            response = fetch_response("https://www.examplebank.ca/investments/gic.html", policy)

        self.assertEqual(response.content_type, "text/html")
        self.assertEqual(response.headers["x-fpds-browser-fallback-attempted"], "true")
        self.assertEqual(response.headers["x-fpds-browser-fallback-error-type"], "RuntimeError")
        self.assertEqual(response.headers["x-fpds-browser-fallback-error"], "render timed out with details")

    def test_product_page_with_unresolved_datacode_rate_requests_browser_rendering(self) -> None:
        policy = DiscoveryFetchPolicy(
            allowed_domains=("examplebank.ca",),
            block_private_networks=False,
            browser_fallback_domains=("examplebank.ca",),
        )
        response = FetchedResponse(
            body=(
                b"<html><body>Earn a savings interest rate of "
                b"<datacode data-code='savingsAccount.segments.default.totalRate'></datacode>"
                b" while another account earns 0.10%.</body></html>"
            ),
            final_url="https://www.examplebank.ca/accounts/savings-amplifier/",
            content_type="text/html",
            status_code=200,
            headers={"content-type": "text/html; charset=utf-8"},
            fetched_at="2026-07-22T00:00:00+00:00",
            redirect_count=0,
        )

        self.assertTrue(_should_try_browser_rendered_rate_fallback(response, policy))

        escaped_response = FetchedResponse(
            **{
                **response.__dict__,
                "body": (
                    b'{"markup":"\\u003cdatacode data-code=\\"savingsAccount.segments.default.totalRate\\" '
                    b'data-format=\\"Percent (0.00%)\\"\\u003e"}'
                ),
            }
        )
        self.assertTrue(_should_try_browser_rendered_rate_fallback(escaped_response, policy))

    def test_product_page_with_double_bracket_rate_placeholder_requests_browser_rendering(self) -> None:
        policy = DiscoveryFetchPolicy(
            allowed_domains=("examplebank.ca",),
            block_private_networks=False,
            browser_fallback_domains=("examplebank.ca",),
        )
        response = FetchedResponse(
            body=(
                b"<html><body>Current GIC interest rates "
                b"90 Day [[GIC.RATE.90_DAY]] 1 Year [[GIC.RATE.1_YEAR]]</body></html>"
            ),
            final_url="https://www.examplebank.ca/rates/gic-rates",
            content_type="text/html",
            status_code=200,
            headers={"content-type": "text/html; charset=utf-8"},
            fetched_at="2026-07-22T00:00:00+00:00",
            redirect_count=0,
        )

        self.assertTrue(_should_try_browser_rendered_rate_fallback(response, policy))

    def test_product_page_with_resolved_rate_does_not_request_browser_rendering(self) -> None:
        policy = DiscoveryFetchPolicy(
            allowed_domains=("examplebank.ca",),
            block_private_networks=False,
            browser_fallback_domains=("examplebank.ca",),
        )
        response = FetchedResponse(
            body=b"<html><body>Annual fee $0 Purchase interest rate 21.75%</body></html>",
            final_url="https://www.examplebank.ca/credit-cards/cash-back-card.html",
            content_type="text/html",
            status_code=200,
            headers={"content-type": "text/html; charset=utf-8"},
            fetched_at="2026-07-22T00:00:00+00:00",
            redirect_count=0,
        )

        self.assertFalse(_should_try_browser_rendered_rate_fallback(response, policy))


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


class _ContentTypeHeaders(dict):
    def get_content_type(self) -> str:
        return "text/html"


class _DirectHtmlResponse:
    status = 200

    def __init__(self, *, body: bytes, url: str) -> None:
        self._body = body
        self._url = url
        self.headers = _ContentTypeHeaders({"content-type": "text/html; charset=utf-8"})

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return False

    def geturl(self) -> str:
        return self._url

    def read(self) -> bytes:
        return self._body
