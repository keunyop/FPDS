from pathlib import Path
from dataclasses import replace
import json,hashlib,unittest
from worker.pipeline.fpds_parse_chunk.parser import parse_snapshot_bytes
from worker.pipeline.tests.test_evidence_research_parity import input_from_segments,run_services
from worker.pipeline.fpds_collection_accuracy import quote_supports_value

FIX=Path(__file__).parent/'fixtures/owned-native-records'

class OwnedNativeRecordsTests(unittest.TestCase):
 def item(self,fixture,product,name,role='detail',parent=None,ident='detail'):
  fixture=fixture+'.bin'
  receipt=next(r for r in json.loads((FIX/'sources.json').read_text(encoding='utf8')) if r['fixture']==fixture)
  item=input_from_segments(bank='RBC',url=receipt['url'],product=product,name=name,role=role,parent=parent,ident=ident,segments=parse_snapshot_bytes(body=(FIX/fixture).read_bytes(),content_type='text/html').segments)
  from worker.pipeline.fpds_parse_chunk.service import _build_evidence_chunks
  from worker.pipeline.fpds_evidence_retrieval.models import EvidenceChunkCandidate
  artifact=parse_snapshot_bytes(body=(FIX/fixture).read_bytes(),content_type='text/html')
  chunks=_build_evidence_chunks(parsed_document_id=item.context.parsed_document_id,source_language='en',artifact=artifact,max_chars=900,overlap_chars=120)
  candidates=[EvidenceChunkCandidate(c.evidence_chunk_id,c.parsed_document_id,c.chunk_index,c.anchor_type,c.anchor_value,c.page_no,'en',c.evidence_excerpt,c.retrieval_metadata,item.context.source_document_id,item.context.snapshot_id,'RBC','CA','html') for c in chunks]
  item=replace(item,candidates=candidates)
  metadata={**item.context.source_metadata,**receipt['source_metadata'],'discovery_role':role}
  if parent:metadata['discovery_metadata']={**metadata.get('discovery_metadata',{}),'parent_detail_url':parent}
  return replace(item,context=replace(item.context,source_metadata=metadata))
 def test_source_hashes_are_immutable(self):
  for r in json.loads((FIX/'sources.json').read_text(encoding='utf8')):self.assertEqual(hashlib.sha256((FIX/r['fixture']).read_bytes()).hexdigest(),r['sha256'])
 def test_actual_card_price_excludes_named_recommendation_prices(self):
  detail=self.item('card.html','credit-card','RBC Avion Visa Infinite')
  row,_,_=run_services([detail]);self.assertEqual(row['candidate_payload'].get('annual_fee'),120)
 def test_actual_checking_repeated_heading_and_complete_costs(self):
  detail=self.item('checking.html','chequing','RBC Day to Day Banking Account')
  row,v,_=run_services([detail]);p=row['candidate_payload']
  self.assertEqual(v.validation_action,'auto_validated',p['_collection_accuracy'])
  self.assertEqual((p['monthly_fee'],p['included_transactions'],p['additional_transaction_fee']),(4,12,1.25))
 def test_actual_css_rate_retains_linked_annual_note(self):
  detail=self.item('savings.html','savings','RBC U.S. High Interest eSavings account')
  row,v,_=run_services([detail]);p=row['candidate_payload']
  self.assertEqual(v.validation_action,'auto_validated',p['_collection_accuracy']);self.assertEqual(p['standard_rate'],.25);self.assertEqual(p['monthly_fee'],0);self.assertEqual(row['currency'],'USD')
 def test_actual_rendered_card_table_preserves_units_and_default_rule(self):
  detail=self.item('card.html','credit-card','RBC Avion Visa Infinite')
  rates=self.item('card-rates.html','credit-card','Credit Cards','supporting_html',detail.context.source_metadata['normalized_source_url'],'rates')
  row,v,e=run_services([detail,rates]);p=row['candidate_payload']
  self.assertEqual(v.validation_action,'auto_validated',p['_collection_accuracy']);self.assertEqual(p['purchase_interest_rate'],20.99);self.assertEqual(p['cash_advance_rate'],22.99)
  self.assertIn('third statement period',p['purchase_interest_rate_summary']);self.assertIn('increase by 5%',p['purchase_interest_rate_summary'])
  self.assertTrue(any(f.source_document_id==rates.context.source_document_id and f.field_name=='purchase_interest_rate' for f in e.extracted_fields))
 def test_card_names_preserve_plus_variant(self):
  from worker.native_information_records import names_match
  self.assertFalse(names_match('Example ION Visa','Example ION+ Visa'))

class NativeProofBoundaryTests(unittest.TestCase):
    def parse(self, html):
        return parse_snapshot_bytes(body=html.encode(), content_type='text/html').segments

    def test_generic_named_panels_never_donate_another_cards_price(self):
        html = '<main><h1>Example Travel Visa</h1><section><p>Annual fee</p><p>$90</p></section><div data-product-name="Example Premium Visa"><span class="product-name">Example Premium Visa</span><p>Annual fee</p><p>$500</p></div></main>'
        records = [c.text for c in self.parse(html) if c.anchor_type == 'labelled_financial_record']
        self.assertTrue(any('$90' in x for x in records))
        self.assertFalse(any('$500' in x for x in records))

    def test_conflicting_main_titles_block_native_owned_prices(self):
        records = self.parse('<main><h1>Example Account</h1><h1>Example Plus Account</h1><p>Monthly fee</p><p>$4</p></main>')
        self.assertFalse(any(c.anchor_type in {'labelled_financial_record', 'owned_account_assertion'} for c in records))

    def test_duplicate_or_missing_local_note_blocks_the_native_price(self):
        for notes in ['', '<p id="fee-note">First year only</p><p id="fee-note">Standard fee</p>']:
            html = '<main><h1>Example Account</h1><p>Monthly fee</p><p>$0<sup><a href="" data-target="#fee-note">1</a></sup></p>' + notes + '</main>'
            self.assertFalse(any(c.anchor_type == 'labelled_financial_record' for c in self.parse(html)))

    def test_conditional_free_and_channel_only_unlimited_are_not_ordinary_costs(self):
        for quote in ['Example Account\nNo monthly fee for eligible students', 'Example Account\nPay little to no monthly fees through rebates', 'Example Account\nMonthly fee\nFree for the first year']:
            self.assertFalse(quote_supports_value('monthly_fee', 0, quote))
        self.assertFalse(quote_supports_value('unlimited_transactions_flag', True, 'Example Account\nUnlimited ATM transactions'))

    def test_point_of_sale_does_not_hide_number_words_or_conditional_allowances(self):
        self.assertFalse(quote_supports_value('included_transactions', 12, 'Point of Sale: twelve transactions each month'))
        self.assertFalse(quote_supports_value('included_transactions', 12, '12 transactions each month if your balance is $3000'))
        self.assertFalse(quote_supports_value('included_transactions', 12, '12 Point of Sale transactions each month'))

    def test_multiline_generic_card_row_preserves_complete_annual_default_proof(self):
        from bs4 import BeautifulSoup
        from worker.native_named_rate_records import named_rate_records, card_rate_values, DEFAULT
        note = 'Interest rates are per annum and subject to change without notice.'
        html = '<main><table><tr><th>Credit Cards</th><th>Purchases Interest Rate [%]</th><th>Cash Advances / Cheques Interest Rate [%]</th></tr><tr><th><a href="/travel">Example\nTravel Visa</a></th><td>19.5</td><td>21.5</td></tr></table><p>NOTES</p><ul><li>'+note+'</li></ul></main>'
        records = named_rate_records(BeautifulSoup(html, 'html.parser'))
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0][1], 'Example Travel Visa')
        self.assertEqual(tuple(map(float, card_rate_values(records[0][2]))), (19.5, 21.5))
        for changed in [records[0][2].replace('per annum', 'monthly'), records[0][2].replace('per annum','not per annum'), records[0][2]+'\nPromotional rate if eligible', records[0][2]+'\nYour rate increases by 5% if a payment is missed']:
            self.assertIsNone(card_rate_values(changed))

    def test_all_balance_rate_requires_adjacent_owner_and_rejects_tiers_or_packages(self):
        from bs4 import BeautifulSoup
        from worker.native_named_rate_records import named_rate_records
        prefix = '<main><h2>Savings Rates</h2><p><a href="/savings">Example Savings</a></p><div>'
        table = '<table><tr><th>If Balance is</th><th>Interest Rate [%]</th></tr><tr><td>All balances</td><td>1.5</td></tr></table>'
        suffix = '</div><p>NOTES</p><ul><li>The interest rate is an annual interest rate.</li></ul></main>'
        self.assertEqual(len(named_rate_records(BeautifulSoup(prefix+table+suffix, 'html.parser'))), 1)
        for changed in [(prefix+table+suffix).replace('All balances', '$1000 and over'), (prefix+table+suffix).replace('Example Savings', 'Example Savings linked to Premium package'), (prefix+table+suffix).replace('</p><div>', '</p><p>Other scope</p><div>'), (prefix+table+suffix).replace('annual interest rate', 'monthly interest rate')]:
            self.assertFalse(named_rate_records(BeautifulSoup(changed, 'html.parser')))

    def test_literal_retirement_marker_cannot_disappear_from_rate_proof(self):
        from bs4 import BeautifulSoup
        from worker.native_named_rate_records import named_rate_records
        html='<main><table><tr><th>Credit Cards</th><th>Purchases Interest Rate [%]</th><th>Cash Advances / Cheques Interest Rate [%]</th></tr><tr><th>Example Legacy Visa<sup>***</sup></th><td>19.5</td><td>21.5</td></tr></table><p>NOTES</p><ul><li>Interest rates are per annum.</li><li id="retired">*** This product is no longer offered.</li></ul></main>'
        self.assertFalse(named_rate_records(BeautifulSoup(html,'html.parser')))
        self.assertFalse(named_rate_records(BeautifulSoup(html.replace('<li id="retired">*** This product is no longer offered.</li>',''),'html.parser')))

    def test_same_bank_other_product_rate_fails_the_final_gate_even_with_match_claim(self):
        from worker.pipeline.fpds_collection_accuracy import sanitize_candidate
        import copy
        owner='Example ION Visa'
        quote='\n'.join([owner,'Credit Cards','Purchases Interest Rate [%]','Cash Advances / Cheques Interest Rate [%]','19.5','21.5','NOTES','Interest rates are per annum.','/ion'])
        field={'normalized_value':19.5,'evidence_chunk_id':'rate','official_evidence_quote':quote,'official_grounding_contract_version':'collection-official-grounding-v2','official_verification_status':'match','official_web_sources':[{'url':'https://examplebank.ca/rates'}]}
        record={'product_name':'Example ION+ Visa','product_type':'credit-card','country_code':'CA','currency':'CAD','candidate_payload':{'purchase_interest_rate':19.5},'field_mapping_metadata':{'purchase_interest_rate':field}}
        evidence={'evidence_chunk_id':'rate','source_url':'https://examplebank.ca/rates','anchor_type':'named_card_rate_table','anchor_value':owner,'evidence_excerpt':quote}
        metadata={'normalized_source_url':'https://examplebank.ca/ion-plus','official_domain_allowlist':['examplebank.ca']}
        out,receipt=sanitize_candidate(record,source_metadata=metadata,evidence=[evidence])
        self.assertNotIn('purchase_interest_rate',out['candidate_payload'])
        self.assertEqual(receipt['omitted_fields']['purchase_interest_rate'],'native_product_mismatch')
        # A native exact detail link may establish an officially renamed row.
        linked_quote=quote.replace('/ion','/ion-plus')
        linked=copy.deepcopy(record);linked['field_mapping_metadata']['purchase_interest_rate']['official_evidence_quote']=linked_quote
        out,receipt=sanitize_candidate(linked,source_metadata=metadata,evidence=[{**evidence,'evidence_excerpt':linked_quote}])
        self.assertEqual(out['candidate_payload']['purchase_interest_rate'],19.5)
        self.assertNotIn('purchase_interest_rate',receipt['omitted_fields'])

    def test_explicit_currency_conflict_cannot_fall_back(self):
        from worker.pipeline.fpds_collection_accuracy import country_currency_fallback
        record={'country_code':'CA', 'product_name':'Example Travel Visa', 'field_mapping_metadata':{'product_name':{'captured_currency_conflict':True}}}
        self.assertIsNone(country_currency_fallback(record, []))

    def test_native_currency_scope_retains_full_owned_foreign_declaration(self):
        from worker.pipeline.fpds_collection_accuracy import country_currency_fallback
        note='Example Travel Visa annual fee $90 denominated in USD'
        mapping={'official_grounding_method':'deterministic_native', 'official_grounding_contract_version':'collection-official-grounding-v2','official_verification_status':'match','evidence_chunk_id':'owned','official_evidence_quote':note}
        record={'country_code':'CA','product_name':'Example Travel Visa','field_mapping_metadata':{'annual_fee':mapping}}
        self.assertIsNone(country_currency_fallback(record,[{'evidence_chunk_id':'owned','evidence_excerpt':note}]))

    def test_foreign_companion_origin_cannot_donate_rates(self):
        helper=OwnedNativeRecordsTests()
        detail=helper.item('card.html','credit-card','RBC Avion Visa Infinite')
        rates=helper.item('card-rates.html','credit-card','Credit Cards','supporting_html',ident='rates')
        rates=replace(rates,context=replace(rates.context,bank_code='OtherBank'))
        row,v,_=run_services([detail,rates])
        self.assertEqual(v.validation_action,'excluded')
        self.assertNotIn('purchase_interest_rate',row['candidate_payload'])


if __name__=='__main__':unittest.main()
