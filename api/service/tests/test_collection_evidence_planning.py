from pathlib import Path
import unittest
from api_service.source_catalog import _discover_detail_companion_links, _extract_allowed_links
from worker.discovery.fpds_discovery.fetch import DiscoveryFetchPolicy

ROOT = Path(__file__).resolve().parents[3]

class CollectionEvidencePlanningTests(unittest.TestCase):
    def test_selected_gic_details_keep_family_terms_with_actual_parent_links(self):
        urls = ["https://www.coastcapitalsavings.com/investments/gics/1-year-better-than-cash-gic",
                "https://www.coastcapitalsavings.com/investments/gics/1-year-redeemable-gic"]
        html = '<main><a href="/service-fees">Service fees</a><a href="/investments/gics">See more GICs</a><a href="/privacy">Privacy policy</a></main>'
        companions, _ = _discover_detail_companion_links(detail_rows=[{"normalized_url":u,"raw_url":u} for u in urls],
            country_code="CA", product_type="gic", fetch_policy=DiscoveryFetchPolicy(allowed_domains=("coastcapitalsavings.com",)),
            hostname="www.coastcapitalsavings.com", allowed_domains=("coastcapitalsavings.com",), page_html_by_url={u:html for u in urls})
        item = next(c for c in companions if c.link.normalized_url.endswith("/investments/gics"))
        self.assertEqual(set(item.parent_detail_urls),set(urls))
        self.assertLessEqual(len(companions),2)

    def test_static_card_destination_obeys_approved_domain_boundary(self):
        raw = (ROOT/"worker/pipeline/tests/fixtures/golden/coast_card_modal_dom.html").read_text(encoding="utf8")
        args = dict(html_text=raw, base_url="https://www.coastcapitalsavings.com/everyday-banking/credit-cards", hostname="www.coastcapitalsavings.com")
        confined = _extract_allowed_links(**args, allowed_domains=("coastcapitalsavings.com",))
        self.assertFalse(any("collabriacreditcards.ca" in l.normalized_url for l in confined))
        verified = _extract_allowed_links(**args, allowed_domains=("coastcapitalsavings.com","collabriacreditcards.ca"))
        self.assertTrue(any("card_national-centra-gold-mastercard" in l.normalized_url for l in verified))
        evil = raw.replace("collabriacreditcards.ca","evil.test")
        self.assertFalse(_extract_allowed_links(**{**args,"html_text":evil}, allowed_domains=("coastcapitalsavings.com","collabriacreditcards.ca")))
