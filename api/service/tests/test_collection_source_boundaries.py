"""Cross-bank source selection and content-format regressions."""
import unittest
from unittest.mock import patch
from datetime import date
from worker.discovery.fpds_discovery.fetch import DiscoveryFetchPolicy
from api_service.catalog_preparation import probe_sources
from api_service import source_catalog as catalog
from tests.test_catalog_preparation import source,response
from tests.test_source_catalog import _product_type_definition

class CollectionSourceBoundaryTests(unittest.TestCase):
    def test_explicit_discontinued_checking_is_skipped_but_savings_is_not(self):
        html=b'<h1>Chequing Account</h1><p>As of August 6, 2026, B2B Bank has discontinued the opening of new Chequing Accounts.</p>'
        for kind,expected in [('chequing',[]),('savings',['DETAIL'])]:
            row={**source(),'product_type':kind}
            with patch('worker.discovery.fpds_discovery.fetch.fetch_response',return_value=response(html)):
                available,excluded=probe_sources([row],policy=DiscoveryFetchPolicy(allowed_domains=('bank.example',)))
            self.assertEqual(available,expected)
            if excluded:self.assertEqual(excluded[0]['reason_code'],'product_unavailable_for_new_customers')

    def test_current_explicit_closure_blocks_discovery_even_with_high_score(self):
        html='<title>Example Checking</title><h1>Example Checking</h1><p>Example Checking is no longer available to new customers.</p><p>Monthly fee $0. Unlimited transactions.</p>'
        with patch.object(catalog,'fetch_text',return_value=html):
            result=catalog._score_page_evidence(raw_url='https://bank.example/checking',fetch_policy=DiscoveryFetchPolicy(allowed_domains=('bank.example',)),product_type='chequing',product_type_definition=_product_type_definition('chequing'))
        self.assertIn('product_unavailable_for_new_customers',result.page_evidence_reason_codes)
        self.assertTrue(catalog._seed_detail_has_hard_negative(result))

    def test_extensionless_pdf_response_is_not_an_html_failure(self):
        row={**source('FEES','supporting_html'),'source_url':'https://bank.example/download?documentid=2'}
        with patch('worker.discovery.fpds_discovery.fetch.fetch_response',return_value=response(b'%PDF-1.7 data','application/pdf')):
            available,excluded=probe_sources([row],policy=DiscoveryFetchPolicy(allowed_domains=('bank.example',)))
        self.assertEqual(available,['FEES'])
        self.assertEqual(excluded,[])

    def test_mortgage_service_paths_are_not_product_details(self):
        for path,label in [('/en/port-your-mortgage','Port your mortgage'),('/mortgage-renewal','Mortgage renewal'),('/mortgage-refinancing','Mortgage refinancing'),('/en/contacts/mortgage-broker-support.snc','Mortgage Broker Support')]:
            with self.subTest(path=path):
                self.assertEqual(catalog._source_scope_exclusion_reason(product_type='mortgage',fingerprint='https://bank.example'+path+' '+label),'non_product_service_flow')
        self.assertIsNone(catalog._source_scope_exclusion_reason(product_type='mortgage',fingerprint='https://bank.example/fixed-mortgage Example Fixed Mortgage'))

    def test_future_ambiguous_negated_and_other_product_notices_do_not_retire_scope(self):
        from worker.product_source_policy import unavailable_for_new_customers
        for notice in ['As of August 6, 2099, bank has discontinued the opening of new Checking Accounts.',
                       'Bank has not discontinued the opening of new Checking Accounts.',
                       'Checking Accounts may no longer be available.',
                       'Effective next year Checking Accounts are no longer available to new customers.',
                       'Savings Accounts are no longer available to new customers.']:
            self.assertFalse(unavailable_for_new_customers(notice,product_type='chequing',today=date(2026,10,2)))

    def test_availability_cache_is_product_scoped(self):
        cache={};html=b'<p>Checking Accounts are no longer available to new customers.</p>'
        with patch('worker.discovery.fpds_discovery.fetch.fetch_response',return_value=response(html)):
            for kind,want in [('chequing',[]),('savings',['DETAIL'])]:
                available,_=probe_sources([{**source(),'product_type':kind}],policy=DiscoveryFetchPolicy(allowed_domains=('bank.example',)),cache=cache)
                self.assertEqual(available,want)

    def test_same_captured_alias_content_deduplicates_without_an_h1(self):
        def row(url, digest):
            return {'bank_code':'BANK','country_code':'CA','product_type':'gic','source_language':'en','normalized_url':url,
                'source_url':url,'discovery_role':'detail','priority':'P1','discovery_metadata':{'page_title':'Short-Term GICs | Bank',
                'primary_heading':None,'product_identity_match':True,'attribute_signal_count':2,'negative_signal_count':0,
                'captured_content_fingerprint':digest}}
        a=row('https://bank.example/en/deposits/short-term-gics','same');b=row('https://www.bank.example/deposits/short-term-gics','same')
        rows,aliases=catalog._dedupe_detail_rows_by_product_identity([a,b])
        self.assertEqual(len(rows),1)
        self.assertEqual(len(aliases),1)
        for bad in [row(b['normalized_url'],'changed'),{**b,'country_code':'US'},row('https://other.example/deposits/short-term-gics','same'),row('https://bank.example/en/deposits/short-term-gics?productid=other','same')]:
            self.assertEqual(len(catalog._dedupe_detail_rows_by_product_identity([a,bad])[0]),2)

    def test_direct_shared_lending_rate_companion_kept_but_unrelated_brochure_not_kept(self):
        self.assertGreater(catalog._detail_companion_link_score(product_type='line-of-credit',normalized_url='https://bank.example/advisor-broker-rates/mortgage-rates',anchor_text='Mortgage rates'),0)
        self.assertEqual(catalog._detail_companion_link_score(product_type='line-of-credit',normalized_url='https://bank.example/investment-loans/brochure.pdf',anchor_text='Investment loan brochure'),0)

    def test_closed_sibling_of_same_type_does_not_close_current_product(self):
        from worker.product_source_policy import unavailable_for_new_customers
        for kind,name,old in [('chequing','Maple Plus Checking','Maple Legacy Checking'),('savings','Maple High Yield Savings','Maple Legacy Savings')]:
            html=f'<h1>{name}</h1><p>{old} is no longer available to new customers.</p>'
            self.assertFalse(unavailable_for_new_customers(html,product_type=kind))
            self.assertTrue(unavailable_for_new_customers(html.replace(old,name),product_type=kind))

    def test_only_repairable_old_pdf_format_failure_is_reprobed(self):
        from api_service.collection_preflight import source_block_reason
        row={**source('FEES','supporting_html'),'latest_stage_status':'failed'}
        self.assertIsNone(source_block_reason({**row,'latest_error_summary':'Text fetch expected HTML content but received application/pdf for https://bank.example/pdf?doc=21'}))
        for error in ['Text fetch expected HTML content but received image/png',
                      'Host not in discovery fetch allowlist: other.example',
                      'PDF source returned non-PDF content after bounded fetch recovery']:
            self.assertEqual(source_block_reason({**row,'latest_error_summary':error}),'terminal_source_failure')

    def test_may_effective_date_is_not_modal_uncertainty(self):
        from worker.product_source_policy import unavailable_for_new_customers
        self.assertTrue(unavailable_for_new_customers('As of May 6, 2026, bank has discontinued the opening of new Checking Accounts.',product_type='chequing',today=date(2026,10,2)))
