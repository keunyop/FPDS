"""Bounded, audited correction of the verified Vancity Prime spread.

Default is a full transaction rehearsal followed by rollback. --apply commits.
No collection, model calls, guessed prime value, or broad aggregate rebuild.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from worker.env import load_env_file  # noqa: E402

PRODUCT_ID = "prod_dGBpyMydkwGWu30L"
SOURCE_URL = "https://www.vancity.com/borrow/loans-lines-of-credit/planet-wise-renovation"
SUMMARY = (
    "Term loan: Vancity Prime + 0.75% for qualifying renovations. "
    "APR assumes no fees or charges; additional fees or charges increase "
    "the total cost of credit and APR."
)
CORRECTION_ID = "public-rate-semantics-2026-09-16-vancity"


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def run(connection):
    from psycopg.types.json import Jsonb
    now = datetime.now(UTC)
    # A serializable transaction plus row locks prevent a stale overwrite.
    connection.execute("SET TRANSACTION ISOLATION LEVEL SERIALIZABLE")
    connection.execute("SET LOCAL lock_timeout = '5s'")
    connection.execute("SET LOCAL statement_timeout = '30s'")
    previous = connection.execute(
        "SELECT 1 FROM change_event WHERE event_metadata->>'correction_id' = %s", (CORRECTION_ID,)
    ).fetchone()
    if previous:
        return {"status": "already_applied", "product_id": PRODUCT_ID}
    current = connection.execute(
        "SELECT * FROM canonical_product WHERE product_id = %s FOR UPDATE", (PRODUCT_ID,)
    ).fetchone()
    require(current is not None, "Expected product is absent; no changes made")
    require(current['country_code'] == 'CA' and current['product_type'] == 'personal-loan'
            and current['bank_code'].upper() == 'VANCITY' and current['status'] == 'active',
            "Product identity/status differs from reviewed record")
    before = current['current_snapshot_payload']
    require(current['current_version_no'] == 1 and Decimal(str(before.get('interest_rate'))) == Decimal('.75')
            and not before.get('interest_rate_summary'), "Rate/version changed since review")
    old_version = connection.execute(
        "SELECT * FROM product_version WHERE product_id = %s AND version_no = %s FOR UPDATE",
        (PRODUCT_ID, current['current_version_no'])
    ).fetchone()
    require(old_version is not None and old_version['version_status'] == 'approved'
            and old_version['normalized_payload'] == before, "Canonical/version mismatch")
    old_snapshot = connection.execute(
        "SELECT * FROM aggregate_refresh_run WHERE country_code = 'CA' AND refresh_status = 'completed' "
        "ORDER BY COALESCE(refreshed_at, attempted_at) DESC, attempted_at DESC, snapshot_id DESC LIMIT 1 FOR UPDATE"
    ).fetchone()
    require(old_snapshot is not None, "No completed CA snapshot")
    old_id = old_snapshot['snapshot_id']
    projection = connection.execute(
        "SELECT * FROM public_product_projection WHERE snapshot_id = %s AND product_id = %s FOR UPDATE",
        (old_id, PRODUCT_ID)
    ).fetchone()
    source = connection.execute(
        'SELECT sd.normalized_source_url FROM product_version pv '
        'JOIN normalized_candidate nc ON nc.candidate_id=pv.approved_candidate_id '
        'JOIN source_document sd ON sd.source_document_id=nc.source_document_id '
        'WHERE pv.product_version_id=%s', (old_version['product_version_id'],)
    ).fetchone()
    require(source is not None and source['normalized_source_url'].rstrip('/') == SOURCE_URL,
            'Approved candidate source does not match reviewed official page')
    require(projection is not None and projection['public_display_rate'] == Decimal('.75'),
            "Published source/rate differs from reviewed record")
    after = {**before, 'interest_rate': None, 'interest_rate_summary': SUMMARY}
    # A legacy explicit display override would survive the corrected scalar.
    require(before.get('public_display_rate') is None, "Unexpected canonical display override")
    version_id = 'pver_' + uuid4().hex
    snapshot_id = 'agg_ratefix_' + uuid4().hex
    event_id = 'chg_' + uuid4().hex
    connection.execute("UPDATE product_version SET version_status='superseded', superseded_at=%s WHERE product_version_id=%s", (now, old_version['product_version_id']))
    connection.execute(
        "INSERT INTO product_version (product_version_id, product_id, version_no, version_status, normalized_payload, approved_at) "
        "VALUES (%s,%s,%s,'approved',%s,%s)", (version_id, PRODUCT_ID, current['current_version_no']+1, Jsonb(after), now)
    )
    # Preserve existing evidence for unchanged fields; do not claim old numeric
    # rate evidence substantiates the correction. New evidence is in the event.
    connection.execute(
        "INSERT INTO field_evidence_link (field_evidence_link_id,product_version_id,evidence_chunk_id,source_document_id,field_name,candidate_value,citation_confidence) "
        "SELECT %s || row_number() OVER (), %s, evidence_chunk_id, source_document_id,field_name,candidate_value,citation_confidence "
        "FROM field_evidence_link WHERE product_version_id=%s AND field_name NOT IN ('interest_rate','interest_rate_summary')",
        ('fel_ratefix_' + uuid4().hex + '_', version_id, old_version['product_version_id'])
    )
    connection.execute(
        "UPDATE canonical_product SET current_version_no=current_version_no+1, current_snapshot_payload=%s, last_changed_at=%s, updated_at=%s WHERE product_id=%s",
        (Jsonb(after), now, now, PRODUCT_ID)
    )
    audit = {
        'correction_id': CORRECTION_ID, 'actor_type': 'service', 'actor_id': 'codex',
        'authorization': 'Product Owner requested separate self-review and approval of rate corrections on 2026-09-16',
        'source_url': SOURCE_URL, 'source_checked_at': now.isoformat(),
        'source_fact': 'Term loan: Vancity Prime + 0.75%; qualifying renovations; APR assumes no fees or charges.',
        'changed_field_names': ['interest_rate', 'interest_rate_summary'],
        'before': {'interest_rate': before['interest_rate'], 'interest_rate_summary': before.get('interest_rate_summary')},
        'after': {'interest_rate': None, 'interest_rate_summary': SUMMARY},
        'previous_version_id': old_version['product_version_id'], 'current_version_id': version_id,
        'previous_snapshot_id': old_id, 'current_snapshot_id': snapshot_id,
        'review': 'Verified against the official product table; 0.75 is a spread, not a full rate; no benchmark arithmetic.'
    }
    connection.execute(
        "INSERT INTO change_event (change_event_id,product_id,product_version_id,event_type,event_reason_code,event_metadata,detected_at) "
        "VALUES (%s,%s,%s,'ManualOverride','manual_override',%s,%s)", (event_id, PRODUCT_ID, version_id, Jsonb(audit), now)
    )
    # Clone the already approved snapshot, then amend this one product. Preserve
    # the source cutoff/refreshed_at so this correction cannot imply recollection.
    snapshot_patch = {'snapshot_id': snapshot_id, 'attempted_at': now.isoformat(), 'created_at': now.isoformat(),
                      'refresh_metadata': {**old_snapshot['refresh_metadata'], 'rate_correction': audit}}
    connection.execute(
        "INSERT INTO aggregate_refresh_run SELECT (jsonb_populate_record(NULL::aggregate_refresh_run, to_jsonb(r) || %s)).* "
        "FROM aggregate_refresh_run r WHERE snapshot_id=%s", (Jsonb(snapshot_patch), old_id)
    )
    connection.execute(
        "INSERT INTO public_product_projection SELECT (jsonb_populate_record(NULL::public_product_projection, to_jsonb(p) || %s)).* "
        "FROM public_product_projection p WHERE snapshot_id=%s", (Jsonb({'snapshot_id': snapshot_id}), old_id)
    )
    metadata = {**projection['refresh_metadata'], 'interest_rate_summary': SUMMARY, 'product_version_id': version_id, 'product_url': SOURCE_URL}
    metadata.pop('interest_rate', None)
    connection.execute(
        "UPDATE public_product_projection SET public_display_rate=NULL, refresh_metadata=%s, last_changed_at=%s "
        "WHERE snapshot_id=%s AND product_id=%s", (Jsonb(metadata), now, snapshot_id, PRODUCT_ID)
    )
    difference = connection.execute(
        "SELECT count(*) AS count FROM public_product_projection old FULL JOIN public_product_projection new "
        "ON new.product_id=old.product_id AND new.snapshot_id=%s "
        "WHERE old.snapshot_id=%s AND old.product_id<>%s "
        "AND (to_jsonb(old)-'snapshot_id') IS DISTINCT FROM (to_jsonb(new)-'snapshot_id')", (snapshot_id, old_id, PRODUCT_ID)
    ).fetchone()['count']
    counts = connection.execute(
        "SELECT snapshot_id,count(*) AS count FROM public_product_projection WHERE snapshot_id IN (%s,%s) GROUP BY snapshot_id", (old_id,snapshot_id)
    ).fetchall()
    require(difference == 0 and len(counts) == 2 and counts[0]['count'] == counts[1]['count'], "Unrelated projection changed")
    return {'status': 'verified', 'product_id': PRODUCT_ID, 'version_id': version_id, 'snapshot_id': snapshot_id,
            'previous_snapshot_id': old_id, 'unchanged_other_products': counts[0]['count']-1,
            'source_refreshed_at_preserved': str(old_snapshot['refreshed_at']), 'event_id': event_id}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--env-file', type=Path, default=ROOT / '.env.dev')
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    load_env_file(args.env_file)
    import psycopg
    from psycopg.rows import dict_row
    with psycopg.connect(os.environ['FPDS_DATABASE_URL'], row_factory=dict_row) as connection:
        result = run(connection)
        if args.apply:
            connection.commit()
        else:
            connection.rollback()
    print(json.dumps({**result, 'committed': args.apply and result['status']=='verified'}, ensure_ascii=True))


if __name__ == '__main__':
    main()
