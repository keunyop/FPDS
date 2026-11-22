from pathlib import Path
import unittest
from unittest.mock import patch

from api_service import source_catalog
from api_service.config import REPO_ROOT


class JapaneseBankDiscoveryTests(unittest.TestCase):
    def test_admin_selects_distinct_current_credit_lines(self):
        index = "https://www.kagin.co.jp/kojin/savings/100_016.html"
        page = (Path(REPO_ROOT) / "worker/discovery/tests/fixtures/kagin-disclosure-row.html").read_text(encoding="utf-8")
        def fetch(url, policy):
            return page if url == index else "<html><h1>鹿児島銀行</h1></html>"

        with patch.object(source_catalog, "fetch_text", side_effect=fetch), patch.dict("os.environ", {"OPENAI_API_KEY": ""}):
            result = source_catalog._generate_sources_from_homepage(
                bank_code="KAGOSHIMA", bank_name="鹿児島銀行", country_code="JP", product_type="line-of-credit",
                product_type_definition={"product_type_code": "line-of-credit", "product_family": "lending"},
                homepage_url="https://www.kagin.co.jp/", coverage_source_url=index, source_language="ja")
        selected = {row["source_url"]: row["discovery_metadata"]["listing_name"] for row in result.rows
                    if row["discovery_metadata"].get("selection_path") == "named_official_disclosure"}
        self.assertEqual(len(selected), 2)
        self.assertTrue(all(row["source_id"] in result.detail_source_ids for row in result.rows if row["source_url"] in selected))
        self.assertIn("不要型", selected["https://www.kagin.co.jp/library/kojin/loan/pdf/2026/cardloanS_huyo.pdf"])
        self.assertIn("引落型", selected["https://www.kagin.co.jp/library/kojin/loan/pdf/2026/cardloanS_hikiotoshi.pdf"])
