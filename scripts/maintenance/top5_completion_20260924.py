"""Apply the reviewed, bounded Top 5 corrections; default rehearses and rolls back.

Only existing canonical products in the companion manifest may change. Immutable
versions and field-level source review are retained. Country snapshots are cloned
so unrelated Public projections and verification dates remain unchanged.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'api/service'))
from api_service.config import Settings
from api_service.db import open_connection
from api_service.public_products import _serialize_product_row
from api_service.review_detail import _normalize_override_payload
from worker.pipeline.fpds_approval_policy import comparison_quality
from worker.pipeline.fpds_aggregate_refresh.models import CanonicalAggregateRow
from worker.pipeline.fpds_aggregate_refresh.service import AggregateRefreshService

MANIFEST = Path(__file__).with_suffix('.json')
# Explicit, reviewed allowlist prevents turning this dated maintenance into an
# arbitrary canonical mutation tool by changing the manifest alone.
PRODUCTS = {
    'prod_3HAnWqgWvu4Wip5R': ('CA', 'ALTERNA', 'savings'),
    'prod_CI2SlegGKNETAwnN': ('CA', 'NATIONAL', 'savings'),
    'prod_E2dNwW86nFNJGtJZ': ('CA', 'RBC', 'savings'),
    'prod_gNB_lQy4Jda-lfk-': ('CA', 'TANGERINE', 'savings'),
    'prod_kJPYb0EzJ2uEVxQa': ('US', 'FCB', 'savings'),
    'prod_hiJANQ-L5-J0pziJ': ('US', 'GSBU', 'savings'),
    'prod_QSCmmE97KOSfGp_c': ('US', 'BOAN', 'mortgage'),
    'prod_44JlWqm4XAGyya64': ('CA', 'MANULIFE', 'line-of-credit'),
    'prod_ZuZIEkEnYFN0sQW8': ('US', 'USBN', 'personal-loan'),
}

def require(condition, message):
    if not condition:
        raise RuntimeError(message)

def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()

def check_public(row, expected):
    public = _serialize_product_row(row, locale='en')
    terms = public.get('deposit_terms') or {}
    if 'deposit_basis' in expected:
        require(terms.get('basis') == expected['deposit_basis'], f"Unexpected deposit basis: {terms}")
    if expected.get('deposit_eligible'):
        require(terms.get('reason') is None and bool(terms.get('options')), f"Deposit remains ineligible: {terms}")
    if 'comparable_rate' in expected:
        require(public['rate']['comparable_rate'] == expected['comparable_rate'], f"Unsafe rate: {public['rate']}")
    if 'secured_flag' in expected:
        require(public['secured_flag'] is expected['secured_flag'], 'Security flag did not reach Public')
    return {'product_id': public['product_id'], 'rate': public['rate'], 'deposit_terms': terms or None}

def run(connection, manifest):
    from psycopg.types.json import Jsonb
    from psycopg import sql
    now = datetime.now(UTC)
    operation = manifest['operation_id']
    items = manifest['items']
    require(len(items) == len(PRODUCTS) and {i['product_id'] for i in items} == set(PRODUCTS), 'Manifest scope changed')
    connection.execute('SET TRANSACTION ISOLATION LEVEL SERIALIZABLE')
    connection.execute("SET LOCAL lock_timeout='5s'")
    connection.execute("SET LOCAL statement_timeout='30s'")
    existing = connection.execute("SELECT product_id FROM change_event WHERE event_metadata->>'operation_id'=%s", (operation,)).fetchall()
    if existing:
        require({r['product_id'] for r in existing} == set(PRODUCTS), 'Partial prior application; inspect manually')
        return {'status':'already_applied', 'count':len(existing)}
    snapshots = {}
    for country in ('CA', 'US'):
        old = connection.execute("SELECT * FROM aggregate_refresh_run WHERE country_code=%s AND refresh_status='completed' ORDER BY COALESCE(refreshed_at,attempted_at) DESC,attempted_at DESC,snapshot_id DESC LIMIT 1 FOR UPDATE", (country,)).fetchone()
        require(old is not None, 'Completed snapshot required')
        new_id = 'agg_top5_' + uuid4().hex
        patch = {'snapshot_id':new_id, 'attempted_at':now.isoformat(), 'created_at':now.isoformat(),
                 'refresh_metadata':{**old['refresh_metadata'], 'bounded_correction':{'operation_id':operation, 'previous_snapshot_id':old['snapshot_id'], 'checked_at':now.isoformat()}}}
        connection.execute('INSERT INTO aggregate_refresh_run SELECT (jsonb_populate_record(NULL::aggregate_refresh_run,to_jsonb(r)||%s)).* FROM aggregate_refresh_run r WHERE snapshot_id=%s', (Jsonb(patch),old['snapshot_id']))
        connection.execute('INSERT INTO public_product_projection SELECT (jsonb_populate_record(NULL::public_product_projection,to_jsonb(p)||%s)).* FROM public_product_projection p WHERE snapshot_id=%s', (Jsonb({'snapshot_id':new_id}),old['snapshot_id']))
        snapshots[country] = (old['snapshot_id'],new_id)
    results=[]
    additions={"CA":0,"US":0}
    for item in items:
        pid=item['product_id']
        cp=connection.execute('SELECT cp.*,b.bank_name AS display_bank_name FROM canonical_product cp JOIN bank b ON b.bank_code=cp.bank_code AND b.country_code=cp.country_code WHERE product_id=%s FOR UPDATE OF cp',(pid,)).fetchone()
        require(cp is not None and cp['status']=='active', 'Expected active product missing')
        require((cp['country_code'],cp['bank_code'],cp['product_type'])==PRODUCTS[pid], 'Product identity changed')
        before=cp['current_snapshot_payload']
        require(cp['current_version_no']==item['expected_version'] and digest(before)==item['expected_payload_sha256'], f'Stale manifest for {pid}')
        previous=connection.execute('SELECT * FROM product_version WHERE product_id=%s AND version_no=%s FOR UPDATE',(pid,cp['current_version_no'])).fetchone()
        require(previous and previous['version_status']=='approved' and previous['normalized_payload']==before,'Version/canonical mismatch')
        changes=_normalize_override_payload(override_payload=item['changes'],base_payload=before)
        require(changes and all(changes[k]==item['changes'][k] for k in changes),'Invalid typed correction')
        evidenced={f for evidence in item['field_evidence'] for f in evidence['fields']}
        require(set(changes)<=evidenced,'Every changed field needs source evidence')
        for evidence in item['field_evidence']:
            require(evidence['source_url'].startswith('https://') and evidence['fact'] and evidence['checked_at'],'Incomplete source review')
        after={**before,**changes}
        quality=comparison_quality(product_type=cp['product_type'],country_code=cp['country_code'],expected_fields=[],candidate_payload=after)
        require(quality.complete or pid == 'prod_QSCmmE97KOSfGp_c',f'Essential fields missing: {quality.missing_fields}')
        version='pver_'+uuid4().hex
        old_snapshot,new_snapshot=snapshots[cp['country_code']]
        row=CanonicalAggregateRow(product_id=pid,bank_code=cp['bank_code'],bank_name=cp['display_bank_name'],country_code=cp['country_code'],product_family=cp['product_family'],product_type=cp['product_type'],subtype_code=cp['subtype_code'],product_name=cp['product_name'],source_language=cp['source_language'],currency=cp['currency'],status=cp['status'],last_verified_at=cp['last_verified_at'].isoformat(),last_changed_at=now.isoformat(),product_version_id=version,canonical_payload=after)
        projected=AggregateRefreshService()._build_projection_row(snapshot_id=new_snapshot,canonical_row=row)
        old_projection=connection.execute('SELECT * FROM public_product_projection WHERE snapshot_id=%s AND product_id=%s FOR UPDATE',(old_snapshot,pid)).fetchone()
        if old_projection is None:
            require(pid == 'prod_hiJANQ-L5-J0pziJ', 'Only the reviewed existing Marcus record may enter the snapshot')
            projected['refresh_metadata']['product_url']=item['field_evidence'][0]['source_url']
            names=sql.SQL(',').join(map(sql.Identifier,projected))
            connection.execute(sql.SQL('INSERT INTO public_product_projection ({}) SELECT {} FROM jsonb_populate_record(NULL::public_product_projection,%s)').format(names,names),(Jsonb(projected),))
            old_projection={**projected,'refresh_metadata':{}}
            additions[cp['country_code']]+=1
        # Preserve unrelated public fields, updating only fields the correction
        # actually changes plus necessary version/evidence metadata.
        public_patch={'last_changed_at':now.isoformat()}
        if not quality.complete: public_patch['status']='inactive'
        columns={'standard_rate':'public_display_rate','public_display_rate':'public_display_rate','interest_rate':'public_display_rate','mortgage_rate':'public_display_rate','monthly_fee':'monthly_fee','minimum_balance':'minimum_balance','minimum_deposit':'minimum_deposit'}
        for field,column in columns.items():
            if field in changes:public_patch[column]=projected[column]
        if {'monthly_fee','public_display_fee'} & set(changes):
            for key in ('monthly_fee','public_display_fee','effective_fee','fee_bucket'):public_patch[key]=projected[key]
        if 'minimum_balance' in changes:public_patch['minimum_balance_bucket']=projected['minimum_balance_bucket']
        metadata={**old_projection['refresh_metadata'],'product_version_id':version}
        for field in changes:
            if field in projected['refresh_metadata']:metadata[field]=projected['refresh_metadata'][field]
            else:metadata.pop(field,None)
        metadata['deposit_conditions']=projected['refresh_metadata'].get('deposit_conditions',{})
        if not metadata.get('product_url'):
            metadata['product_url']=item['field_evidence'][0]['source_url']
        if cp['product_type']=='savings' and not old_projection['status']=='active':
            # This is an existing approved canonical record omitted for an
            # essential-field gap, now verified complete by the same contract.
            public_patch['status']='active'
        public_patch['refresh_metadata']=metadata
        result_row={**old_projection,**public_patch,'approved_deposit_conditions':{},'product_url':metadata['product_url']}
        checked=check_public(result_row,item['expected_public'])
        connection.execute("UPDATE product_version SET version_status='superseded',superseded_at=%s WHERE product_version_id=%s",(now,previous['product_version_id']))
        connection.execute("INSERT INTO product_version(product_version_id,product_id,version_no,version_status,normalized_payload,approved_at) VALUES(%s,%s,%s,'approved',%s,%s)",(version,pid,cp['current_version_no']+1,Jsonb(after),now))
        connection.execute('INSERT INTO field_evidence_link(field_evidence_link_id,product_version_id,evidence_chunk_id,source_document_id,field_name,candidate_value,citation_confidence) SELECT %s||row_number() OVER(),%s,evidence_chunk_id,source_document_id,field_name,candidate_value,citation_confidence FROM field_evidence_link WHERE product_version_id=%s AND NOT(field_name=ANY(%s))',('fel_top5_'+uuid4().hex+'_',version,previous['product_version_id'],list(changes)))
        connection.execute('UPDATE canonical_product SET current_version_no=current_version_no+1,current_snapshot_payload=%s,last_changed_at=%s,updated_at=%s WHERE product_id=%s',(Jsonb(after),now,now,pid))
        event={'operation_id':operation,'actor_type':'service','actor_id':'codex','authorization':manifest['authorization'],'previous_version_id':previous['product_version_id'],'current_version_id':version,'previous_snapshot_id':old_snapshot,'current_snapshot_id':new_snapshot,'changed_field_names':sorted(changes),'before':{k:before.get(k) for k in changes},'after':changes,'field_evidence':item['field_evidence'],'review_note':'Bounded official-source correction; existing verification timestamp preserved because this is a field-level review.'}
        connection.execute("INSERT INTO change_event(change_event_id,product_id,product_version_id,event_type,event_reason_code,event_metadata,detected_at) VALUES(%s,%s,%s,'ManualOverride','manual_override',%s,%s)",('chg_'+uuid4().hex,pid,version,Jsonb(event),now))
        # Type-safe PostgreSQL record expansion; never interpolate field values.
        fields=list(public_patch)
        assignment=sql.SQL(',').join(sql.SQL('{}=r.{}').format(sql.Identifier(k),sql.Identifier(k)) for k in fields)
        query=sql.SQL('UPDATE public_product_projection p SET {} FROM jsonb_populate_record(NULL::public_product_projection,%s) r WHERE p.snapshot_id=%s AND p.product_id=%s').format(assignment)
        connection.execute(query,(Jsonb(public_patch),new_snapshot,pid))
        results.append({**checked,'version_id':version})
    for country,(old,new) in snapshots.items():
        selected=[pid for pid,identity in PRODUCTS.items() if identity[0]==country]
        diff=connection.execute("SELECT count(*) AS n FROM (SELECT to_jsonb(p)-'snapshot_id' AS row FROM public_product_projection p WHERE snapshot_id=%s AND NOT(product_id=ANY(%s)) EXCEPT SELECT to_jsonb(p)-'snapshot_id' AS row FROM public_product_projection p WHERE snapshot_id=%s AND NOT(product_id=ANY(%s))) d",(old,selected,new,selected)).fetchone()['n']
        counts=connection.execute('SELECT snapshot_id,count(*) AS n FROM public_product_projection WHERE snapshot_id IN (%s,%s) GROUP BY snapshot_id',(old,new)).fetchall()
        count_map={r['snapshot_id']:r['n'] for r in counts}
        require(diff==0 and count_map[new]==count_map[old]+additions[country],'Unrelated projections changed')
    return {'status':'verified','operation_id':operation,'snapshots':snapshots,'products':results}

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--env-file',default=str(ROOT/'.env.dev'))
    parser.add_argument('--apply',action='store_true')
    args=parser.parse_args()
    manifest=json.loads(MANIFEST.read_text(encoding='utf8'))
    with open_connection(Settings.from_env(args.env_file)) as connection:
        result=run(connection,manifest)
        if args.apply:connection.commit()
        else:connection.rollback()
    print(json.dumps({**result,'committed':args.apply and result['status']=='verified'},default=str))
if __name__=='__main__':main()
