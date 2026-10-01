import json,unittest
from copy import deepcopy
from api_service.public_common import load_public_projection_rows
from api_service.public_products import _serialize_product_row
from worker.pipeline.fpds_collection_accuracy import RECEIPT_KEY,payload_digest
from tests.test_public_products import _projection_rows

class Result:
 def __init__(self,rows):self.rows=rows
 def fetchall(self):return self.rows
class Connection:
 def __init__(self,rows):self.rows=rows;self.sql=''
 def execute(self,sql,params):self.sql=sql;return Result(self.rows)

class CostAccessPublicTests(unittest.TestCase):
 def test_old_snapshot_and_old_receipt_recheck_conditional_essentials(self):
  row=next(r for r in _projection_rows() if r['product_type']=='chequing')
  p=row['approved_collection_payload'];p.pop('unlimited_transactions_flag');p.update(included_transactions=12,additional_transaction_fee=0)
  p[RECEIPT_KEY]['digest']=payload_digest(row,p)
  connection=Connection([row]);visible=load_public_projection_rows(connection,snapshot_id='old',country_code='CA')
  self.assertEqual(len(visible),1)
  self.assertIn('approved_version.product_version_id =',connection.sql)
  serialized=_serialize_product_row(visible[0],locale='en')
  self.assertEqual(serialized['additional_transaction_fee'],0)
  self.assertIsInstance(serialized['additional_transaction_fee'],(float,int))
  self.assertNotIn('approved_collection_payload',visible[0]);self.assertNotIn(RECEIPT_KEY,json.dumps(serialized))
  p.pop('additional_transaction_fee');p[RECEIPT_KEY]['digest']=payload_digest(row,p)
  self.assertEqual(load_public_projection_rows(Connection([row]),snapshot_id='old',country_code='CA'),[])
 def test_missing_or_tampered_pinned_version_is_not_public(self):
  row=next(r for r in _projection_rows() if r['product_type']=='chequing')
  for change in ('missing','tampered'):
   bad=deepcopy(row)
   if change=='missing':bad.pop('approved_collection_payload')
   else:bad['approved_collection_payload']['monthly_fee']=999
   self.assertEqual(load_public_projection_rows(Connection([bad]),snapshot_id='s',country_code='CA'),[])
if __name__=='__main__':unittest.main()
