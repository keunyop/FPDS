from pathlib import Path
import gzip
import hashlib
from types import SimpleNamespace
import unittest
from unittest.mock import Mock

from worker.discovery.fpds_discovery.discovery import extract_links
from worker.discovery.fpds_discovery.url_utils import url_country_scope_conflicts
from worker.source_content_validity import html_unavailable_reason
from worker.discovery.fpds_discovery.jp_disclosures import check_capture_listings, current_disclosures, listed_documents
from worker.discovery.fpds_snapshot.capture import _validate_fetched_payload
from worker.discovery.fpds_discovery.fetch import NonRetryableFetchError


ROOT = Path(__file__).parent / "fixtures"
KAGIN = "https://www.kagin.co.jp/kojin/savings/100_016.html"


class JapaneseDisclosureListTests(unittest.TestCase):
    def test_full_official_directory_retains_scoped_documents_after_navigation(self):
        body = gzip.decompress((ROOT / "kagin-disclosure-list.html.gz").read_bytes())
        self.assertEqual(hashlib.sha256(body).hexdigest(), "551f077f6d4bdd23190d0465a1b7946a3ff3d4d417ab7e87a2419b0f6b32b621")
        html = body.decode("utf-8")
        for kind, count in {"chequing": 3, "savings": 1, "gic": 9, "mortgage": 2,
                            "line-of-credit": 3, "personal-loan": 8}.items():
            selected = current_disclosures(bank_code="KAGOSHIMA", product_type=kind, index_url=KAGIN, html=html)
            expected = {(r["document_url"], r["listing_label_ja"]) for r in listed_documents()
                        if r["index_url"] == KAGIN and r["disposition"] == "listed" and r["discovery_type"] == kind}
            self.assertEqual(len(selected), count)
            self.assertEqual({(link.resolved_url, link.anchor_text) for link in selected}, expected)

    def test_changed_missing_closed_and_redirected_disclosures(self):
        html = (ROOT / "kagin-disclosure-row.html").read_text(encoding="utf-8")
        selected = current_disclosures(bank_code="KAGOSHIMA", product_type="line-of-credit", index_url=KAGIN, html=html)
        self.assertEqual(len(selected), 2)
        sources = [SimpleNamespace(
            bank_code="KAGOSHIMA", country_code="JP", source_language="ja", source_id=str(i), resolved_url=link.resolved_url,
            source_metadata={"product_type": "line-of-credit", "discovery_metadata": {"selection_path": "named_official_disclosure",
                             "listing_url": KAGIN, "listing_name": link.anchor_text}}) for i, link in enumerate(selected)]
        def response(body):
            return SimpleNamespace(final_url=KAGIN, status_code=200, content_type="text/html", body=body.encode())
        fetcher = Mock(return_value=response(html))
        self.assertEqual(check_capture_listings(sources, None, fetcher)[0], {})
        fetcher.assert_called_once_with(KAGIN, None)
        changed = html.replace("不要型", "別型")
        self.assertEqual(set(check_capture_listings(sources, None, Mock(return_value=response(changed)))[0]), {"0"})
        errors, _ = check_capture_listings(sources, None, Mock(side_effect=ValueError("HTTP 403")))
        self.assertIn("unavailable", errors["0"])
        with self.assertRaisesRegex(NonRetryableFetchError, "redirected"):
            _validate_fetched_payload(source=sources[0], fetched=SimpleNamespace(final_url=selected[1].resolved_url))
        sources[0].source_type = "pdf"
        with self.assertRaisesRegex(NonRetryableFetchError, "non-PDF"):
            _validate_fetched_payload(source=sources[0], fetched=SimpleNamespace(
                final_url=selected[0].resolved_url, content_type="text/html", body=b"<html>Unavailable</html>"))
        fresh = html.replace("cardloanS_huyo.pdf", "direct-cardloan-new.pdf").replace("不要型", "新型")
        self.assertEqual(len(current_disclosures(bank_code="KAGOSHIMA", product_type="line-of-credit", index_url=KAGIN, html=fresh)), 2)
    def test_repeated_product_columns_keep_each_pdf_with_its_own_name(self):
        html = (ROOT / "kagin-disclosure-row.html").read_text(encoding="utf-8")
        links = extract_links(html, base_url=KAGIN)
        self.assertEqual([(item.anchor_text, item.href) for item in links], [
            ("かぎんカードローンS（エス） （返済用口座不要型）", "/library/kojin/loan/pdf/2026/cardloanS_huyo.pdf"),
            ("かぎんカードローンS（エス） （返済用口座引落型）", "/library/kojin/loan/pdf/2026/cardloanS_hikiotoshi.pdf"),
            ("MOZECAローン ※新規申込受付終了", "/library/kojin/loan/pdf/2025/MOZECAloan.pdf"),
        ])
        self.assertTrue(all(item.source_type == "pdf" for item in links))
        navigation = ''.join(f'<a href="/menu/{i}">Menu</a>' for i in range(300))
        crowded = extract_links(navigation + html, base_url=KAGIN)
        self.assertLessEqual(len(crowded), 256)
        self.assertEqual([item.anchor_text for item in crowded if item.source_type == "pdf"],
                         [item.anchor_text for item in links])
        for changed in (html.replace("商品名", "別商品"), html.replace("<td>かぎん", "<td colspan='2'>かぎん")):
            self.assertEqual(extract_links(changed, base_url=KAGIN)[0].anchor_text, "238KB")

    def test_access_denied_response_and_real_product_help(self):
        denial = b'''<title>Access Denied</title><h1>Access Denied</h1>
You don't have permission to access "http://www.higobank.co.jp/individual/description.html" on this server.
<p>Reference #18.123</p><p>https://errors.edgesuite.net/18.123</p>'''
        self.assertEqual(html_unavailable_reason(denial), "access_denied")
        product = b"<title>Example Savings</title><h1>Example Savings</h1><p>Access Denied? Contact support.</p>"
        self.assertIsNone(html_unavailable_reason(product))

    def test_country_boundaries_include_japan(self):
        self.assertFalse(url_country_scope_conflicts(country_code="JP", normalized_url=KAGIN))
        for url in (KAGIN, "https://bank.example/ja-jp/products", "https://bank.example/rates?market=jp"):
            self.assertTrue(url_country_scope_conflicts(country_code="CA", normalized_url=url))
        self.assertTrue(url_country_scope_conflicts(country_code="JP", normalized_url="https://bank.example/en-us/deposits"))
