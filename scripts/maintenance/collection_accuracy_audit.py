"""Read-only evidence audit. No collection, AI requests or database mutations."""
from __future__ import annotations
import argparse
import hashlib
from collections import Counter
from datetime import datetime, UTC
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "api/service")]
from api_service.config import Settings
from api_service.db import open_connection
from worker.pipeline.fpds_collection_accuracy import sanitize_candidate


def audit(connection):
    rows = connection.execute("""
        SELECT cp.product_id, cp.current_version_no, cp.country_code, cp.bank_code,
               cp.product_type, cp.product_name, cp.currency, cp.current_snapshot_payload,
               pv.product_version_id, pv.approved_candidate_id, nc.field_mapping_metadata,
               sd.source_metadata, sd.normalized_source_url, nc.source_document_id,
               cp.last_verified_at
        FROM canonical_product cp
        JOIN product_version pv ON pv.product_id=cp.product_id AND pv.version_no=cp.current_version_no
        LEFT JOIN normalized_candidate nc ON nc.candidate_id=pv.approved_candidate_id
        LEFT JOIN source_document sd ON sd.source_document_id=nc.source_document_id
        WHERE cp.status='active' ORDER BY cp.country_code,cp.product_id
    """).fetchall()
    items = []
    for row in rows:
        evidence = connection.execute("""
            SELECT DISTINCT ec.evidence_chunk_id, ec.evidence_excerpt, sd.normalized_source_url AS source_url,
                   ss.source_document_id
            FROM field_evidence_link fel JOIN evidence_chunk ec USING(evidence_chunk_id)
            JOIN parsed_document pd USING(parsed_document_id)
            JOIN source_snapshot ss ON ss.snapshot_id=pd.snapshot_id
            JOIN source_document sd ON sd.source_document_id=ss.source_document_id
            WHERE fel.product_version_id=%s OR fel.candidate_id=%s
        """, (row["product_version_id"], row["approved_candidate_id"])).fetchall()
        candidate = {**row, "candidate_payload": row["current_snapshot_payload"]}
        sanitized, receipt = sanitize_candidate(candidate, source_metadata=row["source_metadata"] or {}, evidence=list(evidence))
        items.append({"product_id":row["product_id"], "version_no":row["current_version_no"],
                      "country_code":row["country_code"], "bank_code":row["bank_code"],
                      "product_type":row["product_type"], "product_name":row["product_name"],
                      "evidence_count":len(evidence), "assessment":receipt,
                      "before_sha256":hashlib.sha256(json.dumps(row["current_snapshot_payload"],sort_keys=True,separators=(",", ":")).encode()).hexdigest(),
                      "product_version_id":row["product_version_id"],
                      "proposed_action":"retain_verified_fields" if receipt["accepted"] else "deactivate_preserving_history",
                      "before":row["current_snapshot_payload"], "after":sanitized["candidate_payload"]})
    legacy_review_tasks = connection.execute("""
        SELECT rt.review_task_id, rt.candidate_id, rt.run_id, rt.review_state, rt.updated_at,
               nc.country_code, nc.bank_code, nc.product_type, nc.product_name
        FROM review_task rt JOIN normalized_candidate nc USING(candidate_id)
        WHERE rt.review_state IN ('queued','deferred')
          AND NOT (nc.candidate_payload ? '_collection_accuracy')
        ORDER BY rt.review_task_id
    """).fetchall()
    return {"checked_at":datetime.now(UTC).isoformat(), "mode":"read_only", "model_calls":0,
            "legacy_review_count":len(legacy_review_tasks), "legacy_review_tasks":list(legacy_review_tasks),
            "count":len(items), "accepted_count":sum(i["assessment"]["accepted"] for i in items),
            "exclusion_reasons":dict(Counter(r for i in items for r in i["assessment"]["reasons"])),
            "omission_reasons":dict(Counter(r for i in items for r in i["assessment"]["omitted_fields"].values())),
            "items":items}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--env-file",default=str(ROOT / ".env.dev"))
    parser.add_argument("--output",required=True)
    args=parser.parse_args()
    with open_connection(Settings.from_env(args.env_file)) as c:
        c.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY")
        report=audit(c)
    Path(args.output).write_text(json.dumps(report,indent=2,ensure_ascii=False,default=str)+"\n",encoding="utf8")
    print(json.dumps({k:v for k,v in report.items() if k not in {"items", "legacy_review_tasks"}}))

if __name__=="__main__":
    main()
