import gzip,json,unittest
from pathlib import Path
from unittest.mock import patch
from api_service.source_catalog import _score_page_evidence
from api_service.collection_evidence_research import _link_relevance
ROOT=Path(__file__).resolve().parents[3]
FIX=ROOT/'worker/pipeline/tests/fixtures/current-ph-companions'
class NativeEssentialDiscoveryTests(unittest.TestCase):
 def test_actual_brand_heading_is_a_detail_lead_with_corroborated_route(self):
  row=next(r for r in json.loads((FIX/'sources.json').read_text()) if r['url'].endswith('/loans-homeplus'))
  raw=gzip.decompress((FIX/row['file']).read_bytes()).decode()
  with patch('api_service.source_catalog.fetch_text',return_value=raw):
   actual=_score_page_evidence(raw_url=row['url'],fetch_policy=None,product_type='mortgage',product_type_definition={})
  self.assertTrue(actual.product_identity_match)
  self.assertEqual(actual.primary_heading,'Chinabank HomePlus')
  self.assertGreaterEqual(actual.page_evidence_score,6)
 def test_information_faq_leads_are_bounded_to_missing_essentials(self):
  missing=['interest_rate_summary','term_length_text']
  score=lambda url,label,fields=missing:_link_relevance(product_type='mortgage',url='https://examplebank.com/'+url,label=label,missing=fields)
  self.assertGreater(score('loans-faqs','Visit our FAQs Page'),0)
  self.assertGreater(score('loans-faqs-homeplus-application','HomePlus Application'),0)
  self.assertEqual(score('loans-faqs','Visit our FAQs Page',[]),0)
  self.assertEqual(score('login','Login'),0)
  self.assertEqual(score('loans-faqs-client-servicing','Client Servicing'),0)


 def test_compact_account_definition_and_features_are_an_actual_detail_lead(self):
  row=next(r for r in json.loads((FIX/'sources.json').read_text()) if r['url'].endswith('/easy-savings'))
  raw=gzip.decompress((FIX/row['file']).read_bytes()).decode()
  with patch('api_service.source_catalog.fetch_text',return_value=raw):
   actual=_score_page_evidence(raw_url=row['url'],fetch_policy=None,product_type='savings',product_type_definition={})
  self.assertTrue(actual.product_identity_match);self.assertEqual(actual.primary_heading,'Easy Savings Account');self.assertGreaterEqual(actual.page_evidence_score,6)
