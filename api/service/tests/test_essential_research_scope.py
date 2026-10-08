import unittest
from api_service.collection_evidence_research import _link_relevance
from api_service.source_catalog import _url_locale_conflicts_source_language
from tests import test_collection_evidence_research as research_tests

class EssentialResearchScopeTests(unittest.TestCase):
 def test_business_rates_cannot_fill_consumer_essentials(self):
  for typ in ['savings','gic','credit-card']:
   self.assertEqual(_link_relevance(product_type=typ,url='https://examplebank.com/en/rates/business-'+typ+'-rates',label='Business '+typ+' rates',missing=['standard_rate']),0)
 def test_explicit_nested_asset_locale_cannot_be_relabelled(self):
  for path in ['/content/dam/bank/fr/pdfs/agreement.pdf','/assets/legal/fr-CA/agreement.pdf']:
   self.assertTrue(_url_locale_conflicts_source_language(normalized_url='https://examplebank.com'+path,source_language='en'))
  self.assertFalse(_url_locale_conflicts_source_language(normalized_url='https://examplebank.com/assets/legal/shared-agreement.pdf',source_language='en'))
 def test_actual_planner_only_selects_same_language_consumer_lead(self):
  helper=research_tests.EvidenceResearchTests();s=research_tests.source(product='savings',name='Everyday Savings Account')
  html='<main><a href="/en/rates/business-savings-rates">Business savings rates</a><a href="/content/dam/bank/fr/pdfs/account-rates.pdf">Account interest rates</a><a href="/en/rates/savings-account-rates">Savings Account rates</a></main>'
  plan=helper.plan(s,html=html)
  self.assertEqual([x['url'] for x in plan['sources']],['https://examplebank.com/en/rates/savings-account-rates'])
