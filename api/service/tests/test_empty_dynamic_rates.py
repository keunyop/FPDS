import unittest
from api_service.collection_evidence_research import _has_required_dynamic_lead


class DynamicRateResearchTests(unittest.TestCase):
    def test_empty_rate_cells_remain_essential_leads_despite_note_percentages(self):
        html='<script src="/assets/rates.js"></script><p>Interest Rate [%]</p><div id="rates_savings"></div><p>Welcome offer 5%</p>'
        self.assertTrue(_has_required_dynamic_lead(html, ['standard_rate']))
        self.assertTrue(_has_required_dynamic_lead(html, ['purchase_interest_rate']))
        self.assertFalse(_has_required_dynamic_lead(html, ['monthly_fee']))
        self.assertFalse(_has_required_dynamic_lead(html.replace('</div>','<p>1.5%</p></div>'), ['standard_rate']))


if __name__=='__main__':unittest.main()
