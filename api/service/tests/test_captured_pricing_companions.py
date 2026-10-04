import unittest
from api_service.source_catalog import _detail_companion_link_score

class CapturedPricingCompanionTests(unittest.TestCase):
    def test_core_price_disclosure_beats_insurance_or_benefits(self):
        for kind in ['credit-card','mortgage','personal-loan','line-of-credit']:
            with self.subTest(kind=kind):
                self.assertEqual(_detail_companion_link_score(product_type=kind,normalized_url='https://examplebank.com/insurance/product-summary.pdf',anchor_text='Insurance agreement'),0)
        self.assertGreater(_detail_companion_link_score(product_type='credit-card',normalized_url='https://examplebank.com/agreements_and_insurance/cardholder-agreement.pdf',anchor_text='Cardholder Agreement'),0)
        for url,label in [('https://examplebank.com/annual-rates-n-fees.html','Summary of Annual Interest Rates and Fees'),('https://examplebank.com/account/fees-and-details.html','Fees and details')]:
            self.assertGreater(_detail_companion_link_score(product_type='credit-card' if 'annual' in url else 'chequing',normalized_url=url,anchor_text=label),0)

    def test_shared_disclosure_retains_all_selected_product_parents(self):
        from api_service.source_catalog import _discover_detail_companion_links
        from worker.discovery.fpds_discovery.fetch import DiscoveryFetchPolicy
        parents=['https://examplebank.com/card-a','https://examplebank.com/card-b']
        disclosure='https://examplebank.com/rates-n-fees.html'
        html='<main><a href="'+disclosure+'">Summary of Annual Interest Rates and Fees</a><a href="https://examplebank.com/insurance.pdf">Insurance agreement</a></main>'
        rows=[{'normalized_url':u,'raw_url':u} for u in parents]
        links,notes=_discover_detail_companion_links(detail_rows=rows,country_code='CA',product_type='credit-card',fetch_policy=DiscoveryFetchPolicy(allowed_domains=('examplebank.com',)),hostname='examplebank.com',allowed_domains=('examplebank.com',),page_html_by_url={u:html for u in parents})
        self.assertEqual(len(links),1)
        self.assertEqual(links[0].link.normalized_url,disclosure)
        self.assertEqual(set(links[0].parent_detail_urls),set(parents))

    def test_current_pdf_summary_is_discovered_after_navigation_cap(self):
        from pathlib import Path
        from api_service.source_catalog import _discover_detail_companion_links
        from worker.discovery.fpds_discovery.fetch import DiscoveryFetchPolicy
        fixture=Path(__file__).resolve().parents[3]/'worker/pipeline/tests/fixtures/golden/cibc_card_pricing_companion_dom.html'
        nav='<nav>'+''.join(f'<a href="/menu/{i}">Menu {i}</a>' for i in range(300))+'</nav>'
        parents=['https://www.cibc.com/card-a','https://www.cibc.com/card-b']
        links,_=_discover_detail_companion_links(detail_rows=[{'normalized_url':u} for u in parents],country_code='CA',product_type='credit-card',fetch_policy=DiscoveryFetchPolicy(allowed_domains=('cibc.com',)),hostname='www.cibc.com',allowed_domains=('cibc.com',),page_html_by_url={u:nav+fixture.read_text(encoding='utf8')+'<main><a href="https://www.cibc.com/agreements_and_insurance/cardholder-agreement.pdf">Cardholder Agreement</a><a href="https://www.cibc.com/privacy-disclosures.pdf">Credit Card Privacy Disclosures, Terms and Conditions</a></main>' for u in parents})
        self.assertEqual(len(links),2)
        rate=next(x for x in links if 'annual-interest-rate-fees' in x.link.normalized_url)
        self.assertEqual(len(links),2)
        self.assertEqual(set(rate.parent_detail_urls),set(parents))
