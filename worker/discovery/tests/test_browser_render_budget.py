from concurrent.futures import ThreadPoolExecutor
import unittest
from unittest.mock import patch
from worker.discovery.fpds_discovery.fetch import BrowserRenderBudget, DiscoveryFetchPolicy, NonRetryableFetchError, fetch_rendered_response


class BrowserRenderBudgetTests(unittest.TestCase):
    def test_failures_consume_once_and_global_allowance_is_atomic(self):
        budget = BrowserRenderBudget(2)
        def consume(url):
            try:
                budget.consume(url)
                return True
            except NonRetryableFetchError:
                return False
        with ThreadPoolExecutor(max_workers=8) as pool:
            results = list(pool.map(consume, [f"https://bank.test/{i}" for i in range(20)]))
        self.assertEqual(sum(results), 2)
        self.assertEqual(budget.used, 2)
        self.assertFalse(consume(next(iter(budget.urls))))

    def test_zero_and_oversized_limits(self):
        with self.assertRaises(NonRetryableFetchError):
            BrowserRenderBudget(0).consume("https://bank.test")
        with self.assertRaises(ValueError):
            BrowserRenderBudget(49)

    def test_unsafe_url_is_rejected_before_render(self):
        policy = DiscoveryFetchPolicy(allowed_domains=("bank.test",))
        with patch("worker.discovery.fpds_discovery.fetch._fetch_response_via_browser_bounded") as browser:
            for url in ("http://bank.test", "https://127.0.0.1", "https://evil.test"):
                with self.subTest(url=url), self.assertRaises(ValueError):
                    fetch_rendered_response(url, policy)
            browser.assert_not_called()
