from pathlib import Path
import unittest
from worker.dynamic_pricing import has_empty_dynamic_rate_slot
from worker.discovery.fpds_discovery.fetch import FetchedResponse, _should_try_browser_rendered_rate_fallback
from worker.discovery.fpds_discovery.fetch import DiscoveryFetchPolicy


class EmptyDynamicRateTests(unittest.TestCase):
    def response(self, body, url='https://examplebank.ca/rates'):
        return FetchedResponse(body=body.encode(),final_url=url,content_type='text/html',status_code=200,headers={'content-type':'text/html; charset=utf-8'},fetched_at='2026-10-07T00:00:00+00:00',redirect_count=0)

    def test_actual_source_slots_need_rendering_even_with_legal_percentages(self):
        fixtures=Path(__file__).resolve().parents[2]/'pipeline/tests/fixtures/owned-native-records'
        for name in ['raw-card-rates.html','raw-deposit-rates.html']:
            self.assertTrue(has_empty_dynamic_rate_slot((fixtures/(name+'.bin')).read_text(encoding='utf8')))
        self.assertFalse(has_empty_dynamic_rate_slot((fixtures/'deposit-rates.html.bin').read_text(encoding='utf8')))
        # The official rendered card page still has two unresolved retired/business
        # rows; detecting them does not invent values or trigger a render loop.
        self.assertTrue(has_empty_dynamic_rate_slot((fixtures/'card-rates.html.bin').read_text(encoding='utf8')))

    def test_legal_percentage_does_not_mask_empty_rate_cell(self):
        html='<script src="/assets/rates.js"></script><table><tr><th>Purchases Interest Rate [%]</th></tr><tr id="rates_travel"><th>Example Travel Card</th></tr></table><p>Default increases by 5%</p>'
        self.assertTrue(has_empty_dynamic_rate_slot(html))
        policy=DiscoveryFetchPolicy(allowed_domains=('examplebank.ca',),browser_fallback_domains=())
        self.assertTrue(_should_try_browser_rendered_rate_fallback(self.response(html),policy))
        self.assertFalse(_should_try_browser_rendered_rate_fallback(self.response(html,'https://external.ca/rates'),policy))

    def test_empty_savings_slot_and_completed_or_unrelated_surface(self):
        html='<script src="/rates/account.js"></script><h1>Savings Interest Rates</h1><div class="table" id="rates_savings"></div><p>Offer 3%</p>'
        self.assertTrue(has_empty_dynamic_rate_slot(html))
        for completed in [html.replace('</div>','<table><tr><td>1.5</td></tr></table></div>'), html.replace('/rates/account.js','/navigation.js'), html.replace('Savings Interest Rates','Branch Locations')]:
            self.assertFalse(has_empty_dynamic_rate_slot(completed))


if __name__=='__main__':unittest.main()
