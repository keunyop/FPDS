from pathlib import Path
import gzip
import hashlib
import json
import unittest
from dataclasses import replace, fields
from worker.pipeline.fpds_parse_chunk.service import _build_evidence_chunks
from worker.pipeline.fpds_evidence_retrieval.models import EvidenceChunkCandidate
from worker.pipeline.fpds_parse_chunk.parser import parse_snapshot_bytes
from worker.pipeline.tests.test_admin_collection_parity import input_from_segments, run_services

FIX = Path(__file__).parent / 'fixtures/explicit-market-currency'
EXPECTED = {'foodpanda-visa':1200, 'platinum-mastercard':0, 'priority-visa-infinite':0, 'visa-platinum':4000, 'eastwest-jcb-gold':2500, 'eastwest-puregold-always-panalo-visa':1200, 'everyday-titanium-mastercard':2800}


class NamedCardCostTableTests(unittest.TestCase):
    def test_official_named_tables_keep_annual_and_monthly_units(self):
        for source in json.loads((FIX/'cards.json').read_text()):
            slug = source['url'].split('/')[-1]
            raw = gzip.decompress((FIX/source['file']).read_bytes())
            self.assertEqual(hashlib.sha256(raw).hexdigest(), source['sha256'])
            parsed = parse_snapshot_bytes(body=raw, content_type='text/html')
            item = input_from_segments(bank='EB', url=source['url'], product='credit-card', name='unverified discovery', segments=parsed.segments, country='PH')
            # Use the ordinary chunk service; segment-only fixtures would hide
            # a split between the price and its applicability/payment conditions.
            keys = {f.name for f in fields(EvidenceChunkCandidate)}
            chunks = _build_evidence_chunks(parsed_document_id=item.context.parsed_document_id, source_language='en', artifact=parsed, max_chars=900, overlap_chars=120)
            candidates = [EvidenceChunkCandidate(**{k:v for k,v in c.to_record().items() if k in keys}, source_document_id=item.context.source_document_id, source_snapshot_id=item.context.snapshot_id, bank_code='EB', country_code='PH', source_type='html') for c in chunks]
            item = replace(item, candidates=candidates)
            for segment in parsed.segments:
                if segment.anchor_type == 'named_card_cost_table':
                    self.assertEqual([c.evidence_excerpt for c in chunks if c.anchor_type == segment.anchor_type and c.anchor_value == segment.anchor_value], [segment.text])
            record, validation, _ = run_services([item])
            payload = record['candidate_payload']
            with self.subTest(slug=slug):
                if slug in ['dolce-vita-titanium-mastercard', 'foodpanda-visa']:
                    self.assertEqual(validation.validation_action, 'excluded')
                    self.assertNotIn('annual_fee', payload)
                    continue
                self.assertEqual(validation.validation_action, 'auto_validated', payload['_collection_accuracy'])
                self.assertEqual(payload['annual_fee'], EXPECTED[slug])
                self.assertEqual(record['currency'], 'PHP')
                self.assertIn('3% per month or 36% effective rate annually', payload['purchase_interest_rate_summary'])
                self.assertIn('Cash Advance Service Fee', payload['purchase_interest_rate_summary'])
                self.assertNotIn('purchase_interest_rate', payload)
                if slug in ['visa-platinum', 'eastwest-puregold-always-panalo-visa', 'eastwest-jcb-gold']:
                    self.assertTrue(payload.get('fee_waiver_condition'))

    def test_table_scope_conditions_and_other_issuer_are_preserved(self):
        from bs4 import BeautifulSoup
        from worker.native_named_card_cost_table import named_card_cost_tables, annual_fee_value
        source = next(s for s in json.loads((FIX/'cards.json').read_text()) if '/platinum-mastercard' in s['url'])
        raw = gzip.decompress((FIX/source['file']).read_bytes()).decode('utf8')
        html = raw.replace('EastWest', 'ExampleBank').replace('eastwestbanker', 'examplebank')
        records = named_card_cost_tables(BeautifulSoup(html, 'html.parser'))
        self.assertTrue(records)
        quote = records[0][2]
        self.assertEqual(annual_fee_value(quote), 0)
        for bad in [quote.replace('Principal Card: Waived Perpetually', 'Principal Card: Waived for first year'), quote.replace('Principal Card: Waived Perpetually', 'Principal Card: Waived Perpetually if you spend PHP100,000')]:
            self.assertIsNone(annual_fee_value(bad))
        for old, new in [('36%', 'XX.XX%'), ('Cash Advance Service Fee and Interest Charge', 'Unlabelled price'), ('An Interest Charge will be billed if', 'A reward will be given if')]:
            self.assertFalse(named_card_cost_tables(BeautifulSoup(html.replace(old, new), 'html.parser')), old)
        monthly_only = BeautifulSoup(html, 'html.parser')
        for row in monthly_only.find_all('tr'):
            cells = row.find_all('td', recursive=False)
            if len(cells) == 2 and cells[0].get_text(' ', strip=True) == 'Interest Charge':
                cells[1].clear()
                cells[1].append('3% per month')
        self.assertFalse(named_card_cost_tables(monthly_only))
        competing = BeautifulSoup(html, 'html.parser')
        heading = competing.new_tag('h1')
        heading.append('Other Platinum Mastercard')
        competing.find('main').append(heading)
        self.assertFalse(named_card_cost_tables(competing))

        parsed = parse_snapshot_bytes(body=html.encode(), content_type='text/html')
        item = input_from_segments(bank='EXAMPLE', url='https://www.examplebank.com/cards/creditcards/platinum-mastercard', product='credit-card', name='unverified', segments=parsed.segments, country='PH')
        _, validation, _ = run_services([item])
        self.assertEqual(validation.validation_action, 'auto_validated')
        item.context.source_metadata['normalized_source_url'] = 'https://foreignbank.com/cards/creditcards/platinum-mastercard'
        _, validation, _ = run_services([item])
        self.assertEqual(validation.validation_action, 'excluded')
