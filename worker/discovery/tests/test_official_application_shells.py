from dataclasses import replace
import unittest
from worker.discovery.fpds_discovery.fetch import DiscoveryFetchPolicy,FetchedResponse,_should_try_browser_rendered_rate_fallback,BrowserRenderBudget,NonRetryableFetchError
class OfficialApplicationShellTests(unittest.TestCase):
 def test_only_empty_official_application_root_needs_one_render(self):
  policy=DiscoveryFetchPolicy(allowed_domains=('examplebank.com',))
  response=FetchedResponse(body=b'<html><body><div id="app" data-page="{}"></div><script src="/app.js"></script></body></html>',final_url='https://examplebank.com/savings',content_type='text/html',status_code=200,headers={},fetched_at='2026-10-14',redirect_count=0)
  self.assertTrue(_should_try_browser_rendered_rate_fallback(response,policy))
  for body in [b'<html><body><div id="app">Page Not Found</div><script src="/app.js"></script></body></html>',b'<html><body><div id="app">Savings annual rate 0.05%</div><script src="/app.js"></script></body></html>',b'<html><body><div id="app"></div></body></html>']:
   self.assertFalse(_should_try_browser_rendered_rate_fallback(replace(response,body=body),policy))
  self.assertFalse(_should_try_browser_rendered_rate_fallback(replace(response,final_url='https://other.com/savings'),policy))
  budget=BrowserRenderBudget(1);budget.consume(response.final_url)
  with self.assertRaises(NonRetryableFetchError):budget.consume(response.final_url)
