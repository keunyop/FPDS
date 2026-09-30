"""Approved D-090 cutover: 355 products, 470 reviews, atomic CA/US projections.

Default executes and verifies the complete transaction, then rolls it back.
--apply commits. The original approved manifest is hash-pinned. No collection,
model call, hard deletion, account mutation or new financial assertion occurs.
"""
from __future__ import annotations

import argparse
from datetime import UTC, datetime
from hashlib import sha256
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "api/service")]
from api_service.config import Settings
from api_service.db import open_connection
from api_service.public_products import load_public_products, normalize_public_products_query
from worker.pipeline.fpds_aggregate_refresh.service import AggregateRefreshService
from worker.pipeline.fpds_collection_accuracy import ACCURACY_VERSION, RECEIPT_KEY, payload_digest

OPERATION = "collection_accuracy_cutover_20260930"
APPROVED_MANIFEST_SHA256 = "1f79a61b737b1e25d35c94253b8f98e19135dcdb480034e3c499e234d0204f1c"
AUTHORIZATION = "Product Owner explicitly authorized 355 history-preserving product deactivations, 470 automatic review closures and legacy manual product-review API retirement on 2026-09-30, accepting an empty Public catalogue."


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def digest(value):
    return sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def load_manifest(path):
    raw = Path(path).read_bytes()
    require(sha256(raw).hexdigest() == APPROVED_MANIFEST_SHA256, "The approved manifest changed")
    manifest = json.loads(raw)
    require(manifest["count"] == 355 and manifest["accepted_count"] == 0, "Unexpected product scope")
    require(len(manifest["items"]) == len({i["product_id"] for i in manifest["items"]}) == 355, "Duplicate or missing product")
    reviews = manifest["legacy_review_tasks"]
    require(len(reviews) == len({i["review_task_id"] for i in reviews}) == 470, "Unexpected review scope")
    require({i["country_code"] for i in manifest["items"]} == {"CA", "US"}, "Unexpected country")
    require(all(i["assessment"]["accepted"] is False for i in manifest["items"]), "Accepted product included")
    return manifest


def prepare_product(cp, previous, item):
    require(cp["status"] == "active", "Product is no longer active: " + cp["product_id"])
    require(cp["current_version_no"] == item["version_no"] and digest(cp["current_snapshot_payload"]) == item["before_sha256"], "Stale canonical manifest: " + cp["product_id"])
    require(previous["product_version_id"] == item["product_version_id"] and previous["version_status"] == "approved", "Current version changed")
    require(previous["normalized_payload"] == cp["current_snapshot_payload"], "Canonical and current version disagree")
    require(all(cp[k] == item[k] for k in ("country_code", "bank_code", "product_type", "product_name")), "Identity changed")
    after = {**item["after"], "status": "inactive"}
    receipt = {**after[RECEIPT_KEY], "accepted": False, "operation_id": OPERATION,
               "reasons": sorted(set(item["assessment"]["reasons"] + ["legacy_collection_retired"]))}
    receipt["digest"] = payload_digest(cp, after)
    after[RECEIPT_KEY] = receipt
    version = "pver_accuracy_" + sha256(cp["product_id"].encode()).hexdigest()[:24]
    return {"product_id": cp["product_id"], "version_no": cp["current_version_no"] + 1,
            "product_version_id": version, "previous_version_id": previous["product_version_id"], "after": after,
            "event_metadata": {"operation_id": OPERATION, "authorization": AUTHORIZATION,
                "actor_type": "service", "actor_id": "accuracy-policy-cutover", "country_code": cp["country_code"],
                "previous_version_id": previous["product_version_id"], "current_version_id": version,
                "before_sha256": item["before_sha256"], "after_sha256": digest(after),
                "changed_field_names": sorted(k for k in set(cp["current_snapshot_payload"]) | set(after) if cp["current_snapshot_payload"].get(k) != after.get(k)),
                "exclusion_reasons": receipt["reasons"], "status_before": "active", "status_after": "inactive",
                "verification_timestamp_preserved": True}}


def public_readback(connection):
    result = {}
    for country in ("CA", "US"):
        query = normalize_public_products_query(locale="en", country_code=country, bank_codes=None,
            product_types=None, subtype_codes=None, target_customer_tags=None, fee_bucket=None,
            minimum_balance_bucket=None, minimum_deposit_bucket=None, term_bucket=None,
            search_query=None, product_name_query=None, sort_by="default", sort_order="asc", page=1, page_size=20)
        data = load_public_products(connection, query=query)
        result[country] = {"total_items": data["total_items"], "snapshot_id": data["freshness"]["snapshot_id"]}
    return result


def verify_applied(connection, manifest):
    products = [i["product_id"] for i in manifest["items"]]
    reviews = [i["review_task_id"] for i in manifest["legacy_review_tasks"]]
    rows = connection.execute("SELECT product_id, status, current_version_no FROM canonical_product WHERE product_id=ANY(%s)", (products,)).fetchall()
    require(len(rows) == 355 and all(r["status"] == "inactive" for r in rows), "Canonical readback failed")
    for row in rows:
        expected = next(i for i in manifest["items"] if i["product_id"] == row["product_id"])
        require(row["current_version_no"] == expected["version_no"] + 1, "Unexpected version count")
    decisions = connection.execute("SELECT count(*) AS n FROM review_decision WHERE reason_code=%s AND review_task_id=ANY(%s)", (OPERATION, reviews)).fetchone()["n"]
    closed = connection.execute("SELECT count(*) AS n FROM review_task rt JOIN normalized_candidate nc USING(candidate_id) WHERE rt.review_task_id=ANY(%s) AND rt.review_state='rejected' AND nc.candidate_state='rejected'", (reviews,)).fetchone()["n"]
    require(decisions == closed == 470, "Review closure/readback failed")
    changes = connection.execute("SELECT count(*) AS n FROM change_event WHERE event_metadata->>'operation_id'=%s", (OPERATION,)).fetchone()["n"]
    require(changes == 355, "Change history incomplete")
    result = public_readback(connection)
    require(all(r["total_items"] == 0 and r["snapshot_id"] == f"agg_accuracy_cutover_20260930_{country}" for country, r in result.items()), "Public did not select the empty cutover snapshot")
    pending = connection.execute("SELECT count(*) AS n FROM review_task WHERE review_state IN ('queued','deferred')").fetchone()["n"]
    require(pending == 0, "Unexpected pending review")
    return {"deactivated_products": len(rows), "closed_reviews": closed, "change_events": changes,
            "review_decisions": decisions, "pending_reviews": pending, "public": result}


def run(connection, manifest, backup_path):
    from psycopg.types.json import Jsonb
    connection.execute("SET TRANSACTION ISOLATION LEVEL SERIALIZABLE")
    connection.execute("SET LOCAL lock_timeout='5s'")
    connection.execute("SET LOCAL statement_timeout='45s'")
    connection.execute("SELECT pg_advisory_xact_lock(hashtext(%s))", (OPERATION,))
    prior = connection.execute("SELECT count(*) AS n FROM change_event WHERE event_metadata->>'operation_id'=%s", (OPERATION,)).fetchone()["n"]
    if prior:
        require(prior == 355, "Partial prior cutover")
        return {"status": "already_applied", **verify_applied(connection, manifest)}
    # Reads stay available. Prevent concurrent ingestion, approval and projection
    # writers from racing the exact preconditions and this one atomic cutover.
    connection.execute("LOCK TABLE ingestion_run IN SHARE MODE")
    connection.execute("LOCK TABLE canonical_product, product_version, normalized_candidate, review_task, review_decision, change_event, aggregate_refresh_run, public_product_projection IN SHARE ROW EXCLUSIVE MODE")
    require(connection.execute("SELECT count(*) AS n FROM ingestion_run WHERE run_state='started'").fetchone()["n"] == 0, "An ingestion run is active")
    require(connection.execute("SELECT count(*) AS n FROM aggregate_refresh_run WHERE refresh_status='started'").fetchone()["n"] == 0, "An aggregate refresh is active")
    products = [i["product_id"] for i in manifest["items"]]
    review_ids = [i["review_task_id"] for i in manifest["legacy_review_tasks"]]
    canonical = connection.execute("SELECT * FROM canonical_product WHERE product_id=ANY(%s) ORDER BY product_id", (products,)).fetchall()
    active = connection.execute("SELECT product_id FROM canonical_product WHERE status='active' ORDER BY product_id").fetchall()
    require({r["product_id"] for r in active} == set(products), "The active-product scope changed")
    previous = connection.execute("SELECT pv.* FROM product_version pv JOIN canonical_product cp ON cp.product_id=pv.product_id AND cp.current_version_no=pv.version_no WHERE cp.product_id=ANY(%s) ORDER BY cp.product_id", (products,)).fetchall()
    previous_by_id = {r["product_id"]: r for r in previous}
    expected = {i["product_id"]: i for i in manifest["items"]}
    patches = [prepare_product(cp, previous_by_id[cp["product_id"]], expected[cp["product_id"]]) for cp in canonical]
    tasks = connection.execute("SELECT * FROM review_task WHERE review_task_id=ANY(%s) ORDER BY review_task_id", (review_ids,)).fetchall()
    pending = connection.execute("SELECT review_task_id FROM review_task WHERE review_state IN ('queued','deferred')").fetchall()
    require({r["review_task_id"] for r in pending} == set(review_ids), "The pending-review scope changed")
    expected_tasks = {r["review_task_id"]: r for r in manifest["legacy_review_tasks"]}
    for row in tasks:
        item = expected_tasks[row["review_task_id"]]
        require(all(row[k] == item[k] for k in ("candidate_id", "run_id", "review_state")) and row["updated_at"] == datetime.fromisoformat(item["updated_at"]), "Review changed since approval")
    candidates = connection.execute("SELECT nc.* FROM normalized_candidate nc JOIN review_task rt USING(candidate_id) WHERE rt.review_task_id=ANY(%s) ORDER BY nc.candidate_id", (review_ids,)).fetchall()
    snapshots = connection.execute("SELECT DISTINCT ON(country_code) * FROM aggregate_refresh_run WHERE country_code IN ('CA','US') AND refresh_status='completed' ORDER BY country_code,COALESCE(refreshed_at,attempted_at) DESC,attempted_at DESC,snapshot_id DESC").fetchall()
    require(len(snapshots) == 2, "Missing previous country snapshot")
    old_snapshot_ids = [r["snapshot_id"] for r in snapshots]
    projections = connection.execute("SELECT * FROM public_product_projection WHERE snapshot_id=ANY(%s) ORDER BY snapshot_id,product_id", (old_snapshot_ids,)).fetchall()
    old_decisions = connection.execute("SELECT * FROM review_decision WHERE review_task_id=ANY(%s) ORDER BY review_decision_id", (review_ids,)).fetchall()
    evidence_count = connection.execute("SELECT count(*) AS n FROM field_evidence_link").fetchone()["n"]
    # An immutable local before-image is saved before any data write.
    backup = {"operation_id": OPERATION, "manifest_sha256": APPROVED_MANIFEST_SHA256,
              "canonical_product": canonical, "product_version": previous, "review_task": tasks,
              "normalized_candidate": candidates, "review_decision": old_decisions,
              "aggregate_refresh_run": snapshots, "public_product_projection": projections,
              "field_evidence_link_count": evidence_count}
    serialized = json.dumps(backup, ensure_ascii=False, sort_keys=True, indent=2, default=lambda v: v.isoformat() if isinstance(v, datetime) else str(v)) + "\n"
    backup_path = Path(backup_path)
    if backup_path.exists():
        require(backup_path.read_text(encoding="utf8") == serialized, "Existing before-image differs")
    else:
        backup_path.parent.mkdir(parents=True, exist_ok=True)
        with backup_path.open("x", encoding="utf8", newline="\n") as f:
            f.write(serialized)
    now = datetime.now(UTC)
    old_versions = [r["product_version_id"] for r in previous]
    require(connection.execute("UPDATE product_version SET version_status='superseded',superseded_at=%s WHERE product_version_id=ANY(%s)", (now, old_versions)).rowcount == 355, "Old version count mismatch")
    connection.execute("INSERT INTO product_version(product_version_id,product_id,version_no,version_status,normalized_payload,approved_at) SELECT r->>'product_version_id',r->>'product_id',(r->>'version_no')::integer,'approved',r->'after',%s FROM jsonb_array_elements(%s) r", (now, Jsonb(patches)))
    require(connection.execute("UPDATE canonical_product cp SET status='inactive',current_version_no=(r->>'version_no')::integer,current_snapshot_payload=r->'after',last_changed_at=%s,updated_at=%s FROM jsonb_array_elements(%s) r WHERE cp.product_id=r->>'product_id'", (now, now, Jsonb(patches))).rowcount == 355, "Canonical update count mismatch")
    connection.execute("INSERT INTO change_event(change_event_id,product_id,product_version_id,event_type,event_reason_code,event_metadata,detected_at) SELECT 'chg_accuracy_'||md5(r->>'product_id'),r->>'product_id',r->>'product_version_id','Updated',%s,r->'event_metadata',%s FROM jsonb_array_elements(%s) r", (OPERATION, now, Jsonb(patches)))
    # This negative receipt marks a policy exclusion, never an AI verification.
    candidate_patches = []
    for row in candidates:
        payload = dict(row["candidate_payload"])
        payload[RECEIPT_KEY] = {"version": ACCURACY_VERSION, "accepted": False, "operation_id": OPERATION,
            "reasons": ["legacy_collection_retired"], "verified_fields": [], "digest": payload_digest(row, payload)}
        candidate_patches.append({"candidate_id":row["candidate_id"], "payload":payload})
    require(connection.execute("UPDATE normalized_candidate nc SET candidate_state='rejected',review_reason_code=%s,candidate_payload=r->'payload',updated_at=%s FROM jsonb_array_elements(%s) r WHERE nc.candidate_id=r->>'candidate_id'", (OPERATION, now, Jsonb(candidate_patches))).rowcount == 470, "Candidate update count mismatch")
    require(connection.execute("UPDATE review_task SET review_state='rejected',updated_at=%s WHERE review_task_id=ANY(%s)", (now, review_ids)).rowcount == 470, "Review update count mismatch")
    decision_rows = [{"review_task_id":r["review_task_id"], "diff_summary":r["review_state"] + " -> rejected; automatic accuracy policy cutover"} for r in tasks]
    connection.execute("INSERT INTO review_decision(review_decision_id,review_task_id,actor_user_id,action_type,reason_code,reason_text,diff_summary,override_payload,decided_at) SELECT 'rdec_accuracy_'||md5(r->>'review_task_id'),r->>'review_task_id',NULL,'reject',%s,%s,r->>'diff_summary','{}'::jsonb,%s FROM jsonb_array_elements(%s) r", (OPERATION, AUTHORIZATION + " No product fact was manually approved.", now, Jsonb(decision_rows)))
    for country in ("CA", "US"):
        snapshot_id = f"agg_accuracy_cutover_20260930_{country}"
        result = AggregateRefreshService().build_snapshot(snapshot_id=snapshot_id, refresh_scope="phase1_public", country_code=country, canonical_rows=[], refreshed_at=now.isoformat())
        require(not result.projection_rows, "Unexpected empty-snapshot projection")
        metadata = {**result.refresh_metadata, "accuracy_cutover": {"operation_id": OPERATION, "previous_snapshot_id": next(r["snapshot_id"] for r in snapshots if r["country_code"] == country)}}
        connection.execute("INSERT INTO aggregate_refresh_run(snapshot_id,refresh_scope,country_code,filter_scope,refresh_status,source_change_cutoff_at,attempted_at,refreshed_at,stale_flag,refresh_metadata) VALUES(%s,'phase1_public',%s,%s,'completed',%s,%s,%s,false,%s)", (snapshot_id, country, Jsonb(result.filter_scope), now, now, now, Jsonb(metadata)))
    require(connection.execute("SELECT count(*) AS n FROM field_evidence_link").fetchone()["n"] == evidence_count, "Evidence links changed")
    require(connection.execute("SELECT count(*) AS n FROM product_version WHERE product_version_id=ANY(%s)", (old_versions,)).fetchone()["n"] == 355, "Old versions lost")
    saved_rows = connection.execute("SELECT product_id,last_verified_at,current_snapshot_payload FROM canonical_product WHERE product_id=ANY(%s)", (products,)).fetchall()
    saved_by_id = {r["product_id"]: r for r in saved_rows}
    after_by_id = {r["product_id"]: r["after"] for r in patches}
    for cp in canonical:
        saved = saved_by_id[cp["product_id"]]
        require(saved["last_verified_at"] == cp["last_verified_at"], "Fact verification timestamp changed")
        require(saved["current_snapshot_payload"] == after_by_id[cp["product_id"]], "Payload readback differs")
    return {"status": "verified", "operation_id": OPERATION, "backup_sha256": sha256(backup_path.read_bytes()).hexdigest(), **verify_applied(connection, manifest)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", default=str(ROOT / "tmp/collection-accuracy-audit.json"))
    parser.add_argument("--backup", default=str(ROOT / "tmp/collection-accuracy-cutover-before.json"))
    parser.add_argument("--env-file", default=str(ROOT / ".env.dev"))
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--report", required=True)
    args = parser.parse_args()
    manifest = load_manifest(args.manifest)
    with open_connection(Settings.from_env(args.env_file)) as connection:
        result = run(connection, manifest, args.backup)
        if args.apply:
            connection.commit()
        else:
            connection.rollback()
    report = {**result, "committed": args.apply and result["status"] == "verified", "checked_at":datetime.now(UTC).isoformat()}
    Path(args.report).write_text(json.dumps(report, indent=2) + "\n", encoding="utf8")
    print(json.dumps(report))


if __name__ == "__main__":
    main()
