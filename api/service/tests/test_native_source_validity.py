import unittest
from unittest.mock import patch
from api_service.source_catalog import _score_page_evidence
from worker.discovery.fpds_discovery.fetch import DiscoveryFetchPolicy

class NativeSourceValidityTests(unittest.TestCase):
 def test_soft404_is_not_reachable_supporting_evidence(self):
  with patch('api_service.source_catalog.fetch_text',return_value='<title>Page introuvable</title><main><h1>Unavailable</h1></main>'):
   result=_score_page_evidence(raw_url='https://bank.example/rates',fetch_policy=DiscoveryFetchPolicy(allowed_domains=('bank.example',)),product_type='mortgage',product_type_definition={'discovery_keywords':['mortgage'],'expected_fields':[]})
  self.assertEqual(result.page_evidence_score,0)
  self.assertIn('soft_404',result.fetch_error)
