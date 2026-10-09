import hashlib,json,unittest
from pathlib import Path
from worker.pipeline.fpds_parse_chunk.parser import parse_snapshot_bytes
from worker.pipeline.fpds_collection_accuracy import quote_supports_value
FIX=Path(__file__).parent/'fixtures/labelled-list-records'
class LabelledListProofTests(unittest.TestCase):
 def parse(self,body):return parse_snapshot_bytes(body=body,content_type='text/html').segments
 def test_source_bytes_are_pinned(self):
  for r in json.loads((FIX/'sources.json').read_text(encoding='utf8')):
   self.assertEqual(hashlib.sha256((FIX/r['fixture']).read_bytes()).hexdigest(),r['sha256'])
 def test_actual_native_list_keeps_owned_fee_and_current_qualified_apr(self):
  segs=self.parse((FIX/'bmo-cash-back-credit-card.html.bin').read_bytes())
  self.assertTrue(any(s.anchor_type=='labelled_financial_record' and quote_supports_value('annual_fee',0,s.text) for s in segs))
  rates=[s.text for s in segs if s.anchor_type=='owned_card_apr_offer']
  self.assertTrue(any('19.49%' in r and '27.49%' in r and 'creditworthiness' in r for r in rates))
 def test_actual_card_passes_stored_artifact_origin_services_without_scalar(self):
  from worker.pipeline.tests.test_evidence_research_parity import input_from_segments,run_services
  segs=self.parse((FIX/'bmo-cash-back-credit-card.html.bin').read_bytes())
  item=input_from_segments(bank='BB',country='US',url='https://www.bmo.com/en-us/main/personal/credit-cards/bmo-cash-back-credit-card/',product='credit-card',name='BMO Cash Back Credit Card',segments=segs)
  record,val,ext=run_services([item]);self.assertEqual(val.validation_action,'auto_validated',record['candidate_payload']['_collection_accuracy'])
  payload=record['candidate_payload'];self.assertEqual(payload['annual_fee'],0);self.assertNotIn('purchase_interest_rate',payload)
  self.assertIn('creditworthiness',payload['purchase_interest_rate_summary'])
 def test_generic_other_bank_and_product_fee_list(self):
  for owner,label,field,amount in [('Example Credit Card','Annual fee','annual_fee',25),('Example Savings Account','Monthly fee','monthly_fee',4)]:
   html=f'<main><h1>{owner}</h1><ul><li><div><p>{label}</p></div><div><p>${amount}</p></div></li></ul></main>'
   self.assertTrue(any(s.anchor_type=='labelled_financial_record' and quote_supports_value(field,amount,s.text) for s in self.parse(html.encode())))
 def test_foreign_panel_and_unresolved_or_qualified_zero_fail(self):
  for extra in ['data-product-name="Other Credit Card"','']:
   html=f'<main><h1>Example Credit Card</h1><ul {extra}><li><div><p>Annual fee*</p></div><div><p>$0</p></div></li></ul></main>'
   self.assertFalse(any(s.anchor_type=='labelled_financial_record' for s in self.parse(html.encode())))
  html='<main><h1>Example Credit Card</h1><ul><li><div><p>Annual fee</p></div><div><p>$0 for the first year</p></div></li></ul></main>'
  self.assertFalse(any(s.anchor_type=='labelled_financial_record' and quote_supports_value('annual_fee',0,s.text) for s in self.parse(html.encode())))

 def test_numbered_atm_network_is_never_ordinary_unlimited(self):
  for context in ['ATM transactions \u2013 unlimited', 'Unlimited transactions 1 at ATMs', 'Unlimited transactions at Non-\nExample\nATMs', 'Unlimited Transactions at 40,000+ fee-free ATMs nationwide','Enjoy unlimited transactions at 40,000+\nATM\ns nationwide and at non-\nExample\nATM\ns']:
   self.assertFalse(quote_supports_value('unlimited_transactions_flag',True,context))
  self.assertTrue(quote_supports_value('unlimited_transactions_flag',True,'Unlimited transactions. Separate non-Example ATM fees apply.'))
 def test_all_actual_card_list_fees_survive_accessibility_markers(self):
  from worker.pipeline.tests.test_evidence_research_parity import input_from_segments,run_services
  for key,name,fee in [('platinum','BMO Platinum Credit Card',0),('platinum-rewards','BMO Platinum Rewards Credit Card',0),('premium-rewards','BMO Premium Rewards Credit Card',95)]:
   item=input_from_segments(bank='BB',country='US',url='https://www.bmo.com/en-us/main/personal/credit-cards/bmo-'+key+'-credit-card/',product='credit-card',name=name,segments=self.parse((FIX/('bmo-'+key+'-credit-card.html.bin')).read_bytes()))
   record,val,ext=run_services([item]);self.assertEqual(record['candidate_payload'].get('annual_fee'),fee,record['candidate_payload']['_collection_accuracy'])

 def test_linked_pdf_preserves_named_purchase_columns_and_intro_loss(self):
  segs=parse_snapshot_bytes(body=(FIX/'card-terms.pdf.bin').read_bytes(),content_type='application/pdf').segments
  records=[s for s in segs if s.anchor_type=='named_card_apr_terms']
  self.assertEqual({s.anchor_value for s in records},{'BMO Platinum Credit Card','BMO Platinum Rewards Credit Card','BMO Cash Back Credit Card'})
  platinum=next(s.text for s in records if s.anchor_value=='BMO Platinum Credit Card')
  for expected in ['0% introductory APR for 15','16.49%','26.49%','Loss of Introductory APR:','late payment','Prime Rate']:
   self.assertIn(expected,platinum)
  self.assertNotIn('19.49%',platinum)

 def test_actual_linked_terms_win_only_with_matching_owned_current_prices(self):
  from worker.pipeline.tests.test_evidence_research_parity import input_from_segments,run_services
  detail_url='https://www.bmo.com/en-us/main/personal/credit-cards/bmo-platinum-credit-card/'
  detail=input_from_segments(bank='BB',country='US',url=detail_url,product='credit-card',name='BMO Platinum Credit Card',segments=self.parse((FIX/'bmo-platinum-credit-card.html.bin').read_bytes()))
  terms=input_from_segments(bank='BB',country='US',url='https://www.bmo.com/en-us/pdf/credit/standardcreditcards.pdf',product='credit-card',name='Summary of Credit Terms',segments=parse_snapshot_bytes(body=(FIX/'card-terms.pdf.bin').read_bytes(),content_type='application/pdf').segments,role='supporting_pdf',parent=detail_url,ident='terms')
  record,val,ext=run_services([detail,terms]);self.assertEqual(val.validation_action,'auto_validated',record['candidate_payload']['_collection_accuracy'])
  summary=record['candidate_payload']['purchase_interest_rate_summary'];self.assertIn('late payment',summary);self.assertIn('15 months',summary)
  self.assertEqual(record['field_mapping_metadata']['purchase_interest_rate_summary']['official_web_sources'][0]['url'],'https://www.bmo.com/en-us/pdf/credit/standardcreditcards.pdf')
  self.assertNotIn('purchase_interest_rate',record['candidate_payload'])
 def test_older_receipt_cannot_hide_numbered_atm_scope_in_projection(self):
  from worker.pipeline.fpds_collection_accuracy import payload_digest,acceptance_receipt_valid,ACCURACY_VERSION
  from worker.pipeline.fpds_aggregate_refresh.models import CanonicalAggregateRow
  from worker.pipeline.fpds_aggregate_refresh.service import AggregateRefreshService
  row={'country_code':'US','bank_code':'EXAMPLE','product_type':'chequing','product_name':'Example Checking','currency':'USD'}
  payload={'product_name':'Example Checking','monthly_fee':0,'unlimited_transactions_flag':True}
  payload['_collection_accuracy']={'version':ACCURACY_VERSION,'accepted':True,'digest':payload_digest(row,payload),'verified_fields':list(payload)}
  mapping={'unlimited_transactions_flag':{'official_evidence_quote':'Unlimited Transactions at 40,000+ fee-free ATMs nationwide'}}
  self.assertFalse(acceptance_receipt_valid({**row,'field_mapping_metadata':mapping},payload))
  item=CanonicalAggregateRow(product_id='p',bank_name='Example',product_family='deposit',subtype_code=None,source_language='en',status='active',last_verified_at=None,last_changed_at=None,product_version_id='v',canonical_payload=payload,field_mapping_metadata=mapping,**row)
  snapshot=AggregateRefreshService().build_snapshot(snapshot_id='s',refresh_scope='phase1_public',country_code='US',canonical_rows=[item])
  self.assertEqual(snapshot.projection_rows,[])

 def test_explicit_equity_collateral_remains_required_despite_repayment_uncertainty(self):
  from worker.pipeline.fpds_approval_policy import security_meaning
  proof='If you have equity in your home, you can borrow money by using that equity as collateral. After that it is the repayment period, and your payments will include both principal and interest, and may be higher than during the first phase.'
  self.assertIs(security_meaning(proof),True)
  for condition in ['Collateral may be required.','Using your home equity as collateral is optional.','You can borrow money by using that equity as collateral, or choose an unsecured loan.']:
   self.assertIsNone(security_meaning(condition))
 def test_actual_owned_heloc_collateral_passes_full_services(self):
  from worker.pipeline.tests.test_evidence_research_parity import input_from_segments,run_services
  item=input_from_segments(bank='BB',country='US',url='https://www.bmo.com/en-us/main/personal/loans-and-lines-of-credit/home-equity-line-of-credit/',product='line-of-credit',name='Home Equity Line of Credit',segments=self.parse((FIX/'secured-line.html.bin').read_bytes()))
  record,val,ext=run_services([item]);self.assertEqual(val.validation_action,'auto_validated',record['candidate_payload']['_collection_accuracy'])
  self.assertIs(record['candidate_payload']['secured_flag'],True)
  self.assertNotIn('interest_rate',record['candidate_payload'])
  self.assertIn('collateral',record['candidate_payload']['security_requirement'])

 def test_incomplete_pdf_shared_conditions_or_duplicate_owners_fail(self):
  from io import BytesIO
  from pypdf import PdfReader
  from worker.native_labelled_lists import pdf_purchase_terms
  page=PdfReader(BytesIO((FIX/'card-terms.pdf.bin').read_bytes())).pages[0]
  layout=page.extract_text(extraction_mode='layout');plain=page.extract_text()
  self.assertEqual(len(pdf_purchase_terms(layout,plain)),3)
  self.assertEqual(pdf_purchase_terms(layout,plain.replace('Loss of Introductory APR:', 'Missing loss clause:')),[])
  self.assertEqual(pdf_purchase_terms(layout,plain+plain),[])
  self.assertEqual(pdf_purchase_terms(layout.replace('Prime Rate.', 'Missing basis.'),plain),[])
 def test_foreign_lending_panel_cannot_supply_collateral(self):
  html='<main><h1>Example Line of Credit</h1><section data-product-name="Other Loan"><p>You can borrow money by using that equity as collateral.</p></section></main>'
  self.assertFalse(any(s.anchor_type=='owned_lending_terms' for s in self.parse(html.encode())))
 def test_long_security_requires_verified_complete_quote_to_survive_copy_filter(self):
  from worker.pipeline.fpds_normalization.service import _looks_like_broad_page_copy
  quote='You can borrow money by using that equity as collateral. '+('This loan requires your home equity. '*9)
  meta={'official_grounding_contract_version':'collection-official-grounding-v2','official_verification_status':'match','official_evidence_quote':quote}
  self.assertFalse(_looks_like_broad_page_copy(field_name='security_requirement',value=quote,grounding_metadata=meta))
  self.assertTrue(_looks_like_broad_page_copy(field_name='security_requirement',value=quote))
  self.assertTrue(_looks_like_broad_page_copy(field_name='security_requirement',value=quote,grounding_metadata={**meta,'official_evidence_quote':quote[:80]}))

 def test_receipt_channel_recheck_preserves_independent_ordinary_and_fee_clauses(self):
  from worker.pipeline.fpds_collection_accuracy import _unlimited_is_channel_only
  for quote in ['Unlimited number of checking transactions. Monthly service charge of $10 waived for customers 55 or older, or for maintaining a daily balance of at least $1,500.', 'Transactions included per month 1 Unlimited Additional transactions 1 No Additional Fee Interac e-Transfer Free Non-Example ATM Fees $2.00 each', 'Unlimited debit 4 and Interac e-Transfer transactions. Withdraw from any ABM for free.']:
   self.assertFalse(_unlimited_is_channel_only(quote))

 def test_display_pdf_rate_or_intro_period_conflict_stays_excluded(self):
  from worker.pipeline.tests.test_evidence_research_parity import input_from_segments,run_services
  url='https://www.bmo.com/en-us/main/personal/credit-cards/bmo-platinum-credit-card/'
  original=(FIX/'bmo-platinum-credit-card.html.bin').read_bytes()
  for before,after in [(b'15 months from account opening date',b'12 months from account opening date'),(b'16.49%',b'17.49%')]:
   with self.subTest(change=after):
    self.assertIn(before,original)
    detail=input_from_segments(bank='BB',country='US',url=url,product='credit-card',name='BMO Platinum Credit Card',segments=self.parse(original.replace(before,after)))
    terms=input_from_segments(bank='BB',country='US',url='https://www.bmo.com/en-us/pdf/credit/standardcreditcards.pdf',product='credit-card',name='Summary of Credit Terms',segments=parse_snapshot_bytes(body=(FIX/'card-terms.pdf.bin').read_bytes(),content_type='application/pdf').segments,role='supporting_pdf',parent=url,ident='terms')
    record,val,ext=run_services([detail,terms])
    self.assertEqual(val.validation_action,'excluded')
    self.assertNotIn('purchase_interest_rate_summary',record['candidate_payload'])
