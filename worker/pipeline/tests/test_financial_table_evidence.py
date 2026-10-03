"""Explicit product/financial column bindings survive HTML capture and grounding."""
from dataclasses import replace
import json
from pathlib import Path
import unittest
from unittest.mock import patch

from worker.pipeline.fpds_collection_accuracy import sanitize_candidate
from worker.pipeline.fpds_evidence_retrieval.models import EvidenceChunkCandidate
from worker.pipeline.fpds_extraction.service import _extract_official_fields_with_ai, _select_official_grounding_chunks
from worker.pipeline.fpds_parse_chunk.parser import parse_snapshot_bytes
from worker.pipeline.tests import test_captured_evidence_grounding as fixtures

FIXTURE = Path(__file__).parent / 'fixtures/golden/bmo_performance_comparison_dom.html'


class FinancialTableEvidenceTests(unittest.TestCase):
    def parse_cells(self, html):
        return [s for s in parse_snapshot_bytes(body=html.encode('utf8'), content_type='text/html').segments
                if s.anchor_type == 'financial_table_cell']

    def test_actual_bmo_product_column_retains_fee_and_waiver_without_neighbors(self):
        cells = self.parse_cells(FIXTURE.read_text(encoding='utf8'))
        fee = next(s for s in cells if s.text.startswith('Performance\n') and 'Monthly plan fee' in s.text)
        self.assertIn('$17.95', fee.text)
        self.assertIn('$4,000', fee.text)
        self.assertIn('$0/month with min.', fee.text)
        for foreign in ('$30.95', '$6,000', '$12.95', 'US dollar'):
            self.assertNotIn(foreign, fee.text)
        ctx, chunk = fixtures.CapturedGroundingTests().context_and_chunk(bank='BMO', product='chequing', url='https://www.bmo.com/en-ca/performance')
        ctx = replace(ctx, source_metadata={**ctx.source_metadata, 'official_domain_allowlist': ['bmo.com'],
            'discovery_metadata': {'primary_heading': 'Performance Chequing Account'}})
        chunks = [replace(chunk, evidence_chunk_id='name', evidence_excerpt='Performance Chequing Account'),
            replace(chunk, evidence_chunk_id='fee', anchor_type=fee.anchor_type, anchor_value=fee.anchor_value, evidence_excerpt=fee.text)]
        entries = [{'field_name':name, 'status':'match', 'has_verified_value':True, 'verified_value_json':json.dumps(value),
                    'evidence_chunk_id':chunk_id, 'evidence_quote':quote, 'confidence':.99,
                    'sources':[{'url':ctx.source_metadata['normalized_source_url']}]} for name,value,chunk_id,quote in (
            ('product_name','Performance Chequing Account','name','Performance Chequing Account'),
            ('monthly_fee',17.95,'fee',fee.text),
            ('fee_waiver_condition',fee.text,'fee',fee.text))]
        with patch('worker.pipeline.fpds_extraction.service.invoke_openai_json_schema',return_value=({'fields':entries},{})) as model:
            fields, _, _ = _extract_official_fields_with_ai(context=ctx, candidates=chunks, requested_fields=['monthly_fee'], collected_fields=[])
        model.assert_called_once()
        values = {f.field_name: float(f.candidate_value) if f.value_type=='decimal' else f.candidate_value for f in fields}
        self.assertEqual(values['monthly_fee'],17.95)
        self.assertIn('$4,000', values['fee_waiver_condition'])
        record = {'country_code':'CA', 'bank_code':'BMO', 'product_type':'chequing', 'product_name':values['product_name'], 'currency':'CAD',
            'candidate_payload':values, 'field_mapping_metadata':{f.field_name:{**f.field_metadata,'normalized_value':values[f.field_name],
                'official_evidence_quote':f.field_metadata['evidence_quote'],'evidence_chunk_id':f.evidence_chunk_id} for f in fields}}
        evidence = [{'evidence_chunk_id':c.evidence_chunk_id,'evidence_excerpt':c.evidence_excerpt,'source_url':ctx.source_metadata['normalized_source_url']} for c in chunks]
        _, receipt = sanitize_candidate(record, source_metadata=ctx.source_metadata, evidence=evidence)
        self.assertIn('monthly_fee',receipt['verified_fields'],receipt)
        self.assertFalse(receipt['accepted'])  # Missing transaction essentials remain excluded.
        record['candidate_payload']['monthly_fee']=0
        record['field_mapping_metadata']['monthly_fee']['normalized_value']=0
        _, receipt = sanitize_candidate(record, source_metadata=ctx.source_metadata, evidence=evidence)
        self.assertNotIn('monthly_fee',receipt['verified_fields'])

    def test_independent_bank_column_links_preserve_all_local_conditions(self):
        html = '''<main><table><tr><th id="a" scope="col">Everyday Savings</th><th id="b" scope="col">Premium Savings</th></tr>
        <tr><th id="fee" scope="row">Monthly fee <a href="#note">1</a></th>
        <td headers="fee a">USD $0</td><td headers="fee b">USD $8</td></tr></table>
        <p id="note">Fee is waived only if the daily balance remains USD $5,000.</p></main>'''
        cells=self.parse_cells(html)
        self.assertEqual(len(cells),2)
        self.assertIn('USD $0',cells[0].text)
        self.assertNotIn('USD $8',cells[0].text)
        self.assertIn('daily balance remains USD $5,000',cells[0].text)
        for broken in (html.replace('fee a','absent a'), html.replace('id="a"','id="fee"'),
                       html.replace('id="note"','id="unknown"'),html.replace('scope="col"','scope="row"'),
                       html.replace('</main>','<p id="a">Other product</p></main>'),
                       html.replace('Fee is waived only if', 'x'*6500+'Fee is waived only if')):
            with self.subTest(broken=broken[:40]):
                actual=self.parse_cells(broken)
                self.assertFalse(any(s.text.startswith('Everyday Savings') for s in actual))

    def test_linked_conditions_remain_atomic_during_chunking(self):
        from worker.pipeline.fpds_parse_chunk.service import _build_evidence_chunks
        html = '<main><table><th id="a" scope="col">Everyday Savings</th><th id="fee" scope="row">Monthly fee <a href="#note">1</a></th><td headers="fee a">$0</td></table><p id="note">'+('Condition. '*250)+'Minimum daily balance $5,000.</p></main>'
        artifact = parse_snapshot_bytes(body=html.encode(), content_type='text/html')
        chunks = _build_evidence_chunks(parsed_document_id='parsed', source_language='en', artifact=artifact, max_chars=1800, overlap_chars=100)
        cells = [c for c in chunks if c.anchor_type == 'financial_table_cell']
        self.assertEqual(len(cells), 1)
        self.assertGreater(len(cells[0].evidence_excerpt), 1800)
        self.assertIn('Minimum daily balance $5,000.', cells[0].evidence_excerpt)

    def test_explicit_columns_are_selected_before_noise_without_budget_growth(self):
        ctx, base = fixtures.CapturedGroundingTests().context_and_chunk()
        noise = [replace(base,evidence_chunk_id='noise-'+str(i),evidence_excerpt='Unrelated navigation.') for i in range(40)]
        owned = replace(base,evidence_chunk_id='fee',anchor_type='financial_table_cell',evidence_excerpt='Everyday Savings\nMonthly fee CAD $0')
        foreign = replace(owned,evidence_chunk_id='foreign',evidence_excerpt='Premium Savings\nMonthly fee CAD $8')
        selected = _select_official_grounding_chunks(candidates=[*noise,foreign,owned],collected_fields=[],product_name='Everyday Savings Account')
        self.assertEqual(selected[0].evidence_chunk_id,'fee')
        self.assertNotIn('foreign',[c.evidence_chunk_id for c in selected])
        self.assertLessEqual(len(selected),24)
        self.assertLessEqual(sum(len(c.evidence_excerpt) for c in selected),43200)


if __name__ == '__main__':
    unittest.main()
