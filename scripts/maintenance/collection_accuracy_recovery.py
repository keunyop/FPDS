"""Manifest-scoped read-only recovery diagnosis. Never calls a model or writes DB."""
from __future__ import annotations
import argparse
from collections import Counter
from datetime import UTC, datetime
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "api/service")]
from api_service.config import Settings
from api_service.db import open_connection
from scripts.maintenance.collection_accuracy_cutover import load_manifest
from worker.pipeline.fpds_collection_accuracy import sanitize_candidate


def classify(product, candidates, evidence_by_candidate):
    assessments = []
    for candidate in candidates:
        # Exact identity only: never borrow another product's evidence on a shared page.
        if any(candidate.get(k) != product.get(k) for k in
               ("country_code", "bank_code", "product_type", "product_name", "currency")):
            continue
        _, receipt = sanitize_candidate(candidate,
            source_metadata=candidate.get("source_metadata") or {},
            evidence=evidence_by_candidate.get(candidate["candidate_id"], []))
        assessments.append({"candidate_id": candidate["candidate_id"],
            "run_id": candidate["run_id"], "source_document_id": candidate["source_document_id"],
            "source_id": (candidate.get("source_metadata") or {}).get("source_id"),
            "source_url": candidate.get("normalized_source_url"), "assessment": receipt})
    assessments.sort(key=lambda a: (not a["assessment"]["accepted"],
        len(a["assessment"]["reasons"]), len(a["assessment"]["missing_fields"]),
        -len(a["assessment"]["verified_fields"])))
    best = assessments[0] if assessments else None
    category = "recollection_required"
    if product["status"] == "active":
        category = "already_active"
    elif best and best["assessment"]["accepted"]:
        category = "current_source_check_required"
    elif not best or not best["source_id"] or not best["source_url"]:
        category = "excluded_no_resolved_source"
    return {**{k: product[k] for k in ("product_id", "country_code", "bank_code",
            "product_type", "product_name", "currency", "status", "current_version_no")},
            "category": category, "candidate_count": len(assessments), "best": best}


def diagnose(connection, manifest):
    ids = [i["product_id"] for i in manifest["items"]]
    products = connection.execute("SELECT * FROM canonical_product WHERE product_id=ANY(%s) ORDER BY country_code,product_id", (ids,)).fetchall()
    if len(products) != len(ids):
        raise RuntimeError("Manifest product missing")
    candidates = connection.execute("""
      SELECT DISTINCT nc.*, sd.source_metadata, sd.normalized_source_url
      FROM normalized_candidate nc JOIN source_document sd USING(source_document_id)
      JOIN canonical_product cp ON cp.bank_code=nc.bank_code AND cp.country_code=nc.country_code
        AND cp.product_type=nc.product_type AND cp.product_name=nc.product_name AND cp.currency=nc.currency
      WHERE cp.product_id=ANY(%s) ORDER BY nc.created_at DESC
    """, (ids,)).fetchall()
    candidate_ids = [r["candidate_id"] for r in candidates]
    links = connection.execute("""
      SELECT DISTINCT fel.candidate_id, ec.evidence_chunk_id,ec.evidence_excerpt,
        sd.normalized_source_url source_url,ss.snapshot_id,ss.checksum,ss.fetched_at,ss.source_document_id
      FROM field_evidence_link fel JOIN evidence_chunk ec USING(evidence_chunk_id)
      JOIN parsed_document pd USING(parsed_document_id) JOIN source_snapshot ss USING(snapshot_id)
      JOIN source_document sd ON sd.source_document_id=ss.source_document_id
      WHERE fel.candidate_id=ANY(%s)
    """, (candidate_ids,)).fetchall()
    evidence = {}
    for link in links:
        evidence.setdefault(link["candidate_id"], []).append(link)
    items = [classify(p, candidates, evidence) for p in products]
    active_runs = connection.execute("SELECT run_id FROM ingestion_run WHERE run_state='started'").fetchall()
    return {"checked_at": datetime.now(UTC).isoformat(), "mode": "read_only", "model_calls": 0,
        "active_runs": active_runs, "count": len(items),
        "categories": dict(Counter(i["category"] for i in items)),
        "reasons": dict(Counter(r for i in items if i["status"] != "active" and i["best"]
                               for r in i["best"]["assessment"]["reasons"])),
        "items": items}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--env-file", default=str(ROOT / ".env.dev"))
    parser.add_argument("--manifest", default=str(ROOT / "tmp/collection-accuracy-audit.json"))
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    manifest = load_manifest(args.manifest)
    with open_connection(Settings.from_env(args.env_file)) as c:
        c.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY")
        report = diagnose(c, manifest)
    with Path(args.output).open("x", encoding="utf8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False, default=str)
        f.write("\n")
    print(json.dumps({k:v for k,v in report.items() if k != "items"}, default=str))

if __name__ == "__main__":
    main()
