"""Synthetic complete snapshot versions for Public sorting/filtering fixtures."""
from worker.pipeline.fpds_collection_accuracy import RECEIPT_KEY,payload_digest

def with_approved_version(row):
 row=dict(row)
 kind=row['product_type']
 if kind not in {'chequing','gic','line-of-credit'}:return row
 payload={'product_name':row['product_name']}
 if kind=='chequing':payload.update(monthly_fee=float(row.get('monthly_fee') or 0),unlimited_transactions_flag=True)
 elif kind=='gic':payload.update(standard_rate=float(row.get('public_display_rate') or 3),term_length_days=row.get('term_length_days') or 365,non_redeemable_flag=True,redeemable_flag=False)
 else:payload.update(interest_rate_summary=row.get('refresh_metadata',{}).get('interest_rate_summary','Annual rate 8%'),secured_flag=False)
 payload[RECEIPT_KEY]={'version':'collection-accuracy-2026-10-01','accepted':True,'digest':payload_digest(row,payload)}
 row['approved_collection_payload']=payload
 return row
