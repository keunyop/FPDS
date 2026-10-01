import unittest
from copy import deepcopy
from worker.pipeline.fpds_approval_policy import comparison_quality
from worker.pipeline.fpds_collection_accuracy import quote_supports_value, sanitize_candidate, acceptance_receipt_valid, RECEIPT_KEY, payload_digest
from worker.pipeline.tests.test_collection_accuracy import candidate_fixture

class EssentialCostAccessTests(unittest.TestCase):
 def quality(self, kind, payload, country='CA'):
  return comparison_quality(product_type=kind,country_code=country,expected_fields=[],candidate_payload=payload)
 def test_checking_structures(self):
  for country in ['CA','US']:
   for extra,valid in [({},False),({'unlimited_transactions_flag':False},False),({'unlimited_transactions_flag':True},True),({'included_transactions':12},False),({'included_transactions':'12','additional_transaction_fee':1},False),({'included_transactions':12,'additional_transaction_fee':1.25},True),({'included_transactions':0,'transaction_fee':1},True),({'transaction_fee':1},True),({'additional_transaction_fee':1},False),({'unlimited_transactions_flag':True,'included_transactions':12},False)]:
    with self.subTest(country=country,extra=extra): self.assertEqual(self.quality('chequing',{'monthly_fee':0,**extra},country).complete,valid)
 def test_withdrawal_structures(self):
  base={'standard_rate':3,'term_length_text':'1 year'}
  for country in ['CA','US']:
   for extra,valid in [({},False),({'non_redeemable_flag':True},True),({'redeemable_flag':False},True),({'redeemable_flag':True},False),({'non_redeemable_flag':False},False),({'redeemable_flag':True,'early_withdrawal_penalty':'Early withdrawal costs 90 days of interest.'},True),({'redeemable_flag':True,'early_withdrawal_penalty':'Early redemption without penalty after 30 days.'},True),({'early_withdrawal_penalty':'Early withdrawal costs 90 days of interest.'},False),({'redeemable_flag':True,'non_redeemable_flag':True},False),({'redeemable_flag':True,'early_withdrawal_penalty':'See terms.'},False),({'redeemable_flag':True,'early_withdrawal_penalty':'Earn 90 days of interest before withdrawal.'},False),({'redeemable_flag':True,'early_withdrawal_penalty':'Withdraw after 30 days; a penalty may apply.'},False)]:
    with self.subTest(extra=extra,country=country):self.assertEqual(self.quality('gic',{**base,**extra},country).complete,valid)
 def test_security(self):
  for extra,valid in [({},False),({'secured_flag':False},True),({'secured_flag':True},True),({'secured_flag':'false'},False),({'security_requirement':'Subject to approval'},False),({'security_requirement':'Unsecured line of credit.'},True),({'security_requirement':'No collateral is required.'},True),({'security_requirement':'Not secured, but collateral is required.'},False),({'security_requirement':'Collateral may be required.'},False),({'secured_flag':False,'security_requirement':'Collateral is required.'},False)]:
   with self.subTest(extra=extra):self.assertEqual(self.quality('line-of-credit',{'interest_rate':8,**extra}).complete,valid)
 def test_field_evidence(self):
  for field,value,quote,valid in [('additional_transaction_fee',1.25,'Additional transaction fee $1.25 CAD each.',True),('additional_transaction_fee',1.25,'Monthly fee $1.25 CAD.',False),('transaction_fee',3,'ATM transaction fee $3.',False),('transaction_fee',1,'Additional transaction fee $1 each.',False),('unlimited_transactions_flag',True,'Unlimited e-transfer transactions.',False),('secured_flag',False,'This is an unsecured line of credit.',True),('security_requirement','Subject to approval','Subject to approval',False),('early_withdrawal_penalty','See bank for details.','See bank for details.',False)]:
   with self.subTest(field=field,quote=quote):self.assertEqual(quote_supports_value(field,value,quote),valid)
 def test_previous_receipt_cannot_bypass_new_gate(self):
  row,meta,ev=candidate_fixture();cleaned,r=sanitize_candidate(row,source_metadata=meta,evidence=ev)
  self.assertTrue(r['accepted'])
  cleaned['candidate_payload'][RECEIPT_KEY]['version']='collection-accuracy-2026-10-01'
  self.assertTrue(acceptance_receipt_valid(cleaned))
  cleaned['product_type']='chequing';p=cleaned['candidate_payload'];p[RECEIPT_KEY]['digest']=payload_digest(cleaned,p)
  self.assertFalse(acceptance_receipt_valid(cleaned))
  p['unlimited_transactions_flag']=True;p[RECEIPT_KEY]['digest']=payload_digest(cleaned,p)
  self.assertTrue(acceptance_receipt_valid(cleaned))
if __name__=='__main__':unittest.main()
