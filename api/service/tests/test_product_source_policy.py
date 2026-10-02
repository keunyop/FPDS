"""Shared source policy must run in the independent API environment."""
import subprocess
import sys
import unittest
from datetime import date
from pathlib import Path

from worker.product_source_policy import unavailable_for_new_customers


class ProductSourcePolicyTests(unittest.TestCase):
    def test_shared_policy_has_no_worker_only_dependencies(self):
        script = """
import importlib.abc
import sys
class BlockWorkerLibraries(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname.split('.')[0] in {'bs4', 'pypdf', 'lxml'}:
            raise ImportError('Worker-only dependency imported: ' + fullname)
sys.meta_path.insert(0, BlockWorkerLibraries())
from worker.product_source_policy import unavailable_for_new_customers
assert unavailable_for_new_customers('<p>Checking accounts are no longer available to new customers.</p>', product_type='chequing')
"""
        result = subprocess.run([sys.executable, '-c', script], cwd=Path(__file__).resolve().parents[3], capture_output=True, text=True, timeout=15)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_nested_inline_notice_and_first_heading_identity(self):
        html = '<h1>Example <span>Checking</span></h1><p>Example Checking is <strong>no longer available</strong> to new customers.</p>'
        self.assertTrue(unavailable_for_new_customers(html, product_type='chequing'))
        self.assertFalse(unavailable_for_new_customers(html, product_type='savings'))

    def test_ignored_markup_cannot_prove_closure(self):
        for tag in ['script', 'style', 'noscript', 'nav', 'title', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
            with self.subTest(tag=tag):
                html = f'<{tag}><span>Checking accounts are no longer available to new customers.</span></{tag}><p>Checking accounts are available.</p>'
                self.assertFalse(unavailable_for_new_customers(html, product_type='chequing'))

    def test_separate_blocks_do_not_combine_product_and_closure(self):
        for separator in ['</p><p>', '<br>', '<hr>', '</div><div>']:
            with self.subTest(separator=separator):
                html = '<div><p>Checking accounts' + separator + 'Savings accounts are no longer available to new customers.</p></div>'
                self.assertFalse(unavailable_for_new_customers(html, product_type='chequing'))

    def test_entities_self_closing_tags_and_comments(self):
        html = '<nav/><h1>Example Checking</h1><p>Example&nbsp;Checking is no longer available <!-- comment --> to new customers.</p>'
        self.assertTrue(unavailable_for_new_customers(html, product_type='chequing'))

    def test_named_sibling_and_future_notice_remain_ineligible(self):
        for notice in ['Legacy Checking is no longer available to new customers.', 'As of August 6, 2099, bank has discontinued the opening of new Checking Accounts.']:
            self.assertFalse(unavailable_for_new_customers('<h1>Current Checking</h1><p>' + notice + '</p>', product_type='chequing', today=date(2026, 10, 2)))


if __name__ == '__main__':
    unittest.main()
