import io
import json
import socket
import unittest
from email.message import Message
from unittest.mock import patch
from scripts.maintenance.public_official_link_report import (
    MAX_BODY, load_products, markdown_report, probe, safe_destination,
)
from worker.discovery.fpds_discovery.fetch import DiscoveryFetchPolicy

PRODUCT = {"product_id": "p1", "country_code": "CA", "bank_name": "Bank",
           "product_name": "Everyday Savings", "product_url": "https://bank.ca/savings"}

class Response(io.BytesIO):
    def __init__(self, code=200, body=b"<title>Everyday Savings | Bank</title>", location=None, content_type="text/html"):
        super().__init__(body)
        self.code = code
        self.headers = Message()
        self.headers["Content-Type"] = content_type
        if location is not None:
            self.headers["Location"] = location

class Opener:
    def __init__(self, *responses):
        self.responses = list(responses)
        self.requests = []
    def open(self, request, timeout):
        self.requests.append(request.full_url)
        response = self.responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response

def check(*responses, product=None):
    opener = Opener(*responses)
    result = probe(product or PRODUCT, opener=opener, validator=lambda value, policy: value)
    return result, opener

class OfficialLinkTests(unittest.TestCase):
    def test_reachable_identity_is_an_observation(self):
        result, _ = check(Response())
        self.assertEqual(result["status"], "reachable_identity_observed")
        self.assertNotIn("body", result)
        self.assertNotIn("last_verified_at", result)

    def test_other_product_redirect_requires_review(self):
        result, _ = check(Response(302, location="/credit-card"), Response(body=b"<h1>Other Product</h1>"))
        self.assertEqual(result["status"], "redirect_review")
        self.assertEqual(result["final_url"], "https://bank.ca/credit-card")
        self.assertEqual(len(result["redirects"]), 1)

    def test_www_and_trailing_slash_keep_identity_but_other_host_is_not_fetched(self):
        result, _ = check(Response(301, location="https://www.bank.ca/savings/"), Response())
        self.assertEqual(result["status"], "reachable_identity_observed")
        for url in ["https://evil.com/x", "https://login.bank.ca/x", "http://127.0.0.1/", "https://bank.ca.evil.com/"]:
            result, opener = check(Response(302, location=url))
            self.assertEqual(result["status"], "external_redirect_review")
            self.assertEqual(len(opener.requests), 1)
            self.assertEqual(result["redirects"][0]["to"], url)

    def test_failures_challenges_and_missing_are_distinct(self):
        for response, status in [(Response(404), "http_failure"), (Response(500), "http_failure"),
                (Response(403), "access_unverified"), (Response(429), "access_unverified"),
                (Response(body=b"<title>Just a moment</title>"), "access_unverified"),
                (Response(body=b"<h1>Other product</h1>"), "identity_review"),
                (Response(content_type="application/pdf"), "content_review"),
                (TimeoutError(), "blocked_or_unreachable")]:
            self.assertEqual(check(response)[0]["status"], status)
        self.assertEqual(check(product={**PRODUCT, "product_url": None})[0]["status"], "missing_url")

    def test_loops_limit_meta_and_canonical(self):
        self.assertEqual(check(Response(302, location="/savings"))[0]["status"], "redirect_loop")
        responses = [Response(302, location="/p" + str(i)) for i in range(6)]
        self.assertEqual(check(*responses)[0]["status"], "redirect_limit")
        self.assertEqual(check(Response(body=b'<meta http-equiv="refresh" content="0;url=/other">'))[0]["status"], "client_redirect_review")
        self.assertEqual(check(Response(body=b'<link rel="canonical" href="/other"><h1>Everyday Savings</h1>'))[0]["status"], "canonical_review")

    def test_svg_titles_and_malformed_url_do_not_corrupt_report(self):
        result, _ = check(Response(body=b"<title>Everyday Savings</title><svg><title>Privacy Icon</title></svg>"))
        self.assertEqual(result["title"], "Everyday Savings")
        self.assertEqual(check(product={**PRODUCT, "product_url": "https://["})[0]["status"], "blocked_or_unreachable")

    def test_response_is_bounded(self):
        result, _ = check(Response(body=b"<title>Everyday Savings</title>" + b"x" * (MAX_BODY + 100)))
        self.assertTrue(result["body_truncated"])
        self.assertLess(len(json.dumps(result)), 3000)

    def test_safety_validates_scheme_credentials_ports_domains_and_private_dns(self):
        policy = DiscoveryFetchPolicy(allowed_domains=("bank.ca",))
        for url in ["http://bank.ca", "https://user:pass@bank.ca", "https://bank.ca:8080", "https://bank.ca/a b", "https://bank.ca\\evil"]:
            with self.assertRaises(ValueError):
                safe_destination(url, policy)
        with patch("socket.getaddrinfo", return_value=[(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("127.0.0.1", 443))]):
            with self.assertRaises(ValueError):
                safe_destination("https://bank.ca/savings", policy)
        with self.assertRaises(ValueError):
            safe_destination("https://evil.ca/savings", policy)

    def test_pagination_never_mixes_snapshot_or_country(self):
        p = {**PRODUCT, "status": "active"}
        first = {"items": [p], "page": 1, "has_next_page": True, "freshness": {"snapshot_id": "s1"}}
        second = {"items": [{**p, "product_id": "p2"}], "page": 2, "has_next_page": False, "freshness": {"snapshot_id": "s1"}}
        rows = iter([first, second])
        self.assertEqual(len(load_products("CA", read_json=lambda _: next(rows))[1]), 2)
        for changed in [{**second, "freshness": {"snapshot_id": "s2"}}, {**second, "items": [{**p, "country_code": "US"}]}, {**second, "items": [p]}]:
            rows = iter([first, changed])
            with self.assertRaises(ValueError):
                load_products("CA", read_json=lambda _: next(rows))

    def test_markdown_escapes_html_and_does_not_claim_fact_verification(self):
        result, _ = check(Response(body=b"<title>&lt;script&gt; | Other</title>"))
        report = markdown_report({"checked_at": "now", "country_code": "CA", "snapshot_id": "s1", "items": [result]})
        self.assertNotIn("<script>", report)
        self.assertIn("does not verify current financial terms", report)

if __name__ == "__main__":
    unittest.main()
