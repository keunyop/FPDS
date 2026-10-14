import gzip,json,unittest
from dataclasses import replace
from worker.pipeline.tests.test_current_account_features import FIX,MANIFEST,ordinary
from worker.pipeline.tests.test_admin_collection_parity import run_services

class LinkedAccountCategoryCostsTests(unittest.TestCase):
 def inputs(self,mutate=lambda t:t,bank='SECURITYBANK'):
  items=[]
  for suffix,role in [('easy-savings','detail'),('fees-charges/','supporting_html')]:
   row=next(x for x in MANIFEST if x['url'].endswith(suffix))
   raw=mutate(gzip.decompress((FIX/row['file']).read_bytes()).decode()).encode()
   url=row['url'].replace('securitybank.com','examplebank.com') if bank=='EXAMPLE' else row['url']
   item=ordinary(row,bank=bank,product='savings',raw=raw,url=url)
   ctx=replace(item.context,source_id=role,source_document_id='doc-'+role,snapshot_id='snap-'+role,parsed_document_id='parsed-'+role,source_metadata={**item.context.source_metadata,'discovery_role':role})
   items.append(replace(item,context=ctx,candidates=[replace(c,evidence_chunk_id=role+'-'+str(i),source_document_id=ctx.source_document_id,source_snapshot_id=ctx.snapshot_id,parsed_document_id=ctx.parsed_document_id) for i,c in enumerate(item.candidates)]))
  return items
 def test_current_own_features_and_exact_category_monthly_cost(self):
  r,v,_=run_services(self.inputs());p=r['candidate_payload']
  self.assertEqual(v.validation_action,'auto_validated',p['_collection_accuracy'])
  self.assertEqual(r['product_name'],'Easy Savings Account');self.assertEqual(r['currency'],'PHP')
  self.assertEqual(p['standard_rate'],0.05);self.assertEqual(p['monthly_fee'],300)
  self.assertEqual(p['minimum_balance'],3000);self.assertEqual(p['minimum_deposit'],0)
  self.assertIn('PHP100,000',p['interest_rate_summary']);self.assertIn('Minimum balance to earn interest:',p['interest_rate_summary'])
  self.assertIn('two (2) consecutive months',p['fee_waiver_condition'])
  self.assertNotIn('For All-Access Account',p['fee_waiver_condition'])
  from api_service.public_rates import public_rate
  self.assertEqual(public_rate({'product_family':'deposit','product_type':'savings','public_display_rate':0.05,'refresh_metadata':p})['kind'],'conditional')
 def test_other_issuer_uses_same_complete_source_contract(self):
  r,v,_=run_services(self.inputs(lambda t:t.replace('securitybank.com','examplebank.com').replace('Security Bank','Example Bank'),bank='EXAMPLE'))
  self.assertEqual(v.validation_action,'auto_validated')
 def test_missing_monthly_unit_wrong_product_or_annual_basis_exclude(self):
  for old,new in [('PHP300 per month','USD300 per month'),('PHP100,000','USD100,000'),('PHP300 per month','PHP300 annually'),('PESO SAVINGS ACCOUNT','PESO PREMIUM ACCOUNT'),('Interest rate (p.a.)','Interest rate (per month)'),('Easy Savings Account is a savings account','Other Savings Account is a savings account'),('/personal/accounts/savings-checking/easy-savings','/personal/accounts/savings-checking/easy-savings-plus')]:
   _,v,_=run_services(self.inputs(lambda t:t.replace(old,new)))
   self.assertEqual(v.validation_action,'excluded',old)
 def test_wrong_country_or_shortened_monthly_conditions_exclude(self):
  items=self.inputs();ctx=replace(items[1].context,country_code='US');items[1]=replace(items[1],context=ctx)
  _,v,_=run_services(items);self.assertEqual(v.validation_action,'excluded')
  _,v,_=run_services(self.inputs(lambda t:t.replace('for two (2) consecutive months','for unknown periods')));self.assertEqual(v.validation_action,'excluded')
