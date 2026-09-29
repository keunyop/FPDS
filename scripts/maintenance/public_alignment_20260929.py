"""Six reviewed CA/US corrections. Default rehearses one transaction and rolls back.

Scope and official facts are pinned by the companion manifest. Existing approved
products only: no candidate approval, collection, account change or deployment.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
import sys
from urllib.parse import urlparse
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "api/service"))
from api_service.config import Settings
from api_service.db import open_connection
from api_service.public_products import _serialize_product_row
from api_service.review_detail import _normalize_override_payload
from worker.pipeline.fpds_approval_policy import comparison_quality
from worker.pipeline.fpds_aggregate_refresh.models import CanonicalAggregateRow
from worker.pipeline.fpds_aggregate_refresh.service import AggregateRefreshService

MANIFEST = Path(__file__).with_suffix(".json")
PRODUCTS = {
    "prod_NH7Vb_SO1LC8Ll2c": ("CA", "VANCITY", "savings", "www.vancity.com"),
    "prod_qCwZrieZzPmZ3Xfs": ("CA", "EQBANK", "savings", "www.eqbank.ca"),
    "prod__my4qoaQjP-UpMZU": ("CA", "LAURENTIAN", "line-of-credit", "www.laurentianbank.ca"),
    "prod_3wkwO1IVQLo9MCUu": ("US", "RB", "savings", "www.regions.com"),
    "prod_hiJANQ-L5-J0pziJ": ("US", "GSBU", "savings", "www.marcus.com"),
    "prod_Kl8WVmRrIdr46cUq": ("US", "GSBU", "gic", "www.marcus.com"),
}


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def prepare_payload(cp, item):
    pid = item["product_id"]
    require(pid in PRODUCTS, "Unreviewed product")
    require(tuple(cp[k] for k in ("country_code", "bank_code", "product_type")) == PRODUCTS[pid][:3], "Identity mismatch")
    before = cp["current_snapshot_payload"]
    require(cp["current_version_no"] == item["expected_version"] and digest(before) == item["expected_payload_sha256"], "Stale manifest: " + pid)
    changes = _normalize_override_payload(override_payload=item["changes"], base_payload=before)
    require(changes == item["changes"] and bool(changes), "Unsafe or empty typed changes")
    evidence = item["field_evidence"]
    require(set(changes) <= {f for e in evidence for f in e["fields"]}, "Missing field evidence")
    for entry in evidence:
        url = urlparse(entry["source_url"])
        require(url.scheme == "https" and url.hostname == PRODUCTS[pid][3] and not url.username and not url.password and url.port in (None, 443), "Unapproved evidence domain")
        require(entry["fact"] and entry["checked_at"] == "2026-09-29", "Incomplete source review")
    after = {**before, **changes}
    quality = comparison_quality(product_type=cp["product_type"], country_code=cp["country_code"], expected_fields=[], candidate_payload=after)
    require(list(quality.missing_fields) == item["expected_public"].get("missing_fields", []), "Unexpected essential-field gaps")
    require(quality.complete == item["expected_public"]["active"], "Unexpected publication eligibility")
    return after, quality


def check_public(row, expected):
    public = _serialize_product_row(row, locale="en")
    terms = public.get("deposit_terms") or {}
    require((row["status"] == "active") == expected["active"], "Wrong projection status")
    for name in ("basis", "reason", "withdrawal"):
        if name in expected:
            require(terms.get(name) == expected[name], "Unexpected deposit " + name + ": " + str(terms))
    if "option_count" in expected:
        require(len(terms.get("options", [])) == expected["option_count"], "Incomplete term schedule")
    require(public["rate"]["comparable_rate"] == expected["comparable_rate"], "Unexpected comparable rate")
    return {"product_id": row["product_id"], "active": expected["active"], "rate": public["rate"], "deposit_terms": terms or None}


def run(connection, manifest):
    from psycopg import sql
    from psycopg.types.json import Jsonb
    operation = manifest["operation_id"]
    require(operation == "public-alignment-20260929", "Wrong operation")
    items = manifest["items"]
    require(len(items) == len(PRODUCTS) and {i["product_id"] for i in items} == set(PRODUCTS), "Manifest scope changed")
    connection.execute("SET TRANSACTION ISOLATION LEVEL SERIALIZABLE")
    connection.execute("SET LOCAL lock_timeout='5s'")
    connection.execute("SET LOCAL statement_timeout='30s'")
    existing = connection.execute("SELECT product_id FROM change_event WHERE event_metadata->>'operation_id'=%s", (operation,)).fetchall()
    if existing:
        require(len(existing) == len(PRODUCTS) and {r["product_id"] for r in existing} == set(PRODUCTS), "Partial prior operation")
        return {"status": "already_applied", "count": len(existing)}
    now = datetime.now(UTC)
    snapshots = {}
    for country in ("CA", "US"):
        old = connection.execute("SELECT * FROM aggregate_refresh_run WHERE country_code=%s AND refresh_status='completed' ORDER BY COALESCE(refreshed_at,attempted_at) DESC,attempted_at DESC,snapshot_id DESC LIMIT 1 FOR UPDATE", (country,)).fetchone()
        require(old is not None, "Completed snapshot required")
        new = "agg_alignment_" + uuid4().hex
        patch = {"snapshot_id": new, "attempted_at": now.isoformat(), "created_at": now.isoformat(), "refreshed_at": now.isoformat(),
                 "refresh_metadata": {**old["refresh_metadata"], "bounded_correction": {"operation_id": operation, "previous_snapshot_id": old["snapshot_id"]}}}
        connection.execute("INSERT INTO aggregate_refresh_run SELECT (jsonb_populate_record(NULL::aggregate_refresh_run,to_jsonb(r)||%s)).* FROM aggregate_refresh_run r WHERE snapshot_id=%s", (Jsonb(patch), old["snapshot_id"]))
        connection.execute("INSERT INTO public_product_projection SELECT (jsonb_populate_record(NULL::public_product_projection,to_jsonb(p)||%s)).* FROM public_product_projection p WHERE snapshot_id=%s", (Jsonb({"snapshot_id": new}), old["snapshot_id"]))
        snapshots[country] = (old["snapshot_id"], new)
    results = []
    for item in items:
        pid = item["product_id"]
        cp = connection.execute("SELECT cp.*, b.bank_name AS display_bank_name FROM canonical_product cp JOIN bank b ON b.bank_code=cp.bank_code AND b.country_code=cp.country_code WHERE cp.product_id=%s FOR UPDATE OF cp", (pid,)).fetchone()
        require(cp and cp["status"] == "active", "Expected active canonical product")
        after, quality = prepare_payload(cp, item)
        before = cp["current_snapshot_payload"]
        previous = connection.execute("SELECT * FROM product_version WHERE product_id=%s AND version_no=%s FOR UPDATE", (pid, cp["current_version_no"])).fetchone()
        require(previous and previous["version_status"] == "approved" and previous["normalized_payload"] == before, "Canonical/version mismatch")
        version = "pver_" + uuid4().hex
        old, new = snapshots[cp["country_code"]]
        old_projection = connection.execute("SELECT * FROM public_product_projection WHERE snapshot_id=%s AND product_id=%s", (old, pid)).fetchone()
        require(old_projection and old_projection["status"] == "active", "Expected published product")
        require(old_projection["refresh_metadata"].get("product_version_id") == previous["product_version_id"], "Snapshot/version mismatch")
        model = CanonicalAggregateRow(product_id=pid, bank_code=cp["bank_code"], bank_name=cp["display_bank_name"], country_code=cp["country_code"], product_family=cp["product_family"], product_type=cp["product_type"], subtype_code=cp["subtype_code"], product_name=cp["product_name"], source_language=cp["source_language"], currency=cp["currency"], status="active" if quality.complete else "inactive", last_verified_at=cp["last_verified_at"].isoformat() if cp["last_verified_at"] else None, last_changed_at=now.isoformat(), product_version_id=version, canonical_payload=after)
        projected = AggregateRefreshService()._build_projection_row(snapshot_id=new, canonical_row=model)
        projected["refresh_metadata"]["product_url"] = old_projection["refresh_metadata"].get("product_url") or item["field_evidence"][0]["source_url"]
        checked = check_public({**projected, "approved_deposit_conditions": {}, "product_url": projected["refresh_metadata"]["product_url"]}, item["expected_public"])
        connection.execute("UPDATE product_version SET version_status='superseded',superseded_at=%s WHERE product_version_id=%s", (now, previous["product_version_id"]))
        connection.execute("INSERT INTO product_version(product_version_id,product_id,version_no,version_status,normalized_payload,approved_at) VALUES(%s,%s,%s,'approved',%s,%s)", (version,pid,cp["current_version_no"]+1,Jsonb(after),now))
        changes = item["changes"]
        connection.execute("INSERT INTO field_evidence_link(field_evidence_link_id,product_version_id,evidence_chunk_id,source_document_id,field_name,candidate_value,citation_confidence) SELECT %s||row_number() OVER(),%s,evidence_chunk_id,source_document_id,field_name,candidate_value,citation_confidence FROM field_evidence_link WHERE product_version_id=%s AND NOT(field_name=ANY(%s))", ("fel_alignment_"+uuid4().hex+"_",version,previous["product_version_id"],list(changes)))
        connection.execute("UPDATE canonical_product SET current_version_no=current_version_no+1,current_snapshot_payload=%s,last_changed_at=%s,updated_at=%s WHERE product_id=%s", (Jsonb(after),now,now,pid))
        event = {"operation_id":operation,"actor_type":"service","actor_id":"codex","authorization":manifest["authorization"],"previous_version_id":previous["product_version_id"],"current_version_id":version,"previous_snapshot_id":old,"current_snapshot_id":new,"changed_field_names":sorted(changes),"before":{k:before.get(k) for k in changes},"after":changes,"field_evidence":item["field_evidence"],"review_note":"Bounded field correction; original product verification timestamp preserved. Incomplete essential rates remain non-public."}
        connection.execute("INSERT INTO change_event(change_event_id,product_id,product_version_id,event_type,event_reason_code,event_metadata,detected_at) VALUES(%s,%s,%s,'ManualOverride','manual_override',%s,%s)", ("chg_"+uuid4().hex,pid,version,Jsonb(event),now))
        columns = [key for key in projected if key not in ("snapshot_id", "product_id")]
        assignments = sql.SQL(",").join(sql.SQL("{}=r.{}").format(sql.Identifier(key), sql.Identifier(key)) for key in columns)
        connection.execute(sql.SQL("UPDATE public_product_projection p SET {} FROM jsonb_populate_record(NULL::public_product_projection,%s) r WHERE p.snapshot_id=%s AND p.product_id=%s").format(assignments), (Jsonb(projected),new,pid))
        persisted = connection.execute("SELECT current_snapshot_payload,last_verified_at FROM canonical_product WHERE product_id=%s", (pid,)).fetchone()
        require(persisted["current_snapshot_payload"] == after and persisted["last_verified_at"] == cp["last_verified_at"], "Failed canonical readback")
        saved_projection = connection.execute("SELECT * FROM public_product_projection WHERE snapshot_id=%s AND product_id=%s", (new,pid)).fetchone()
        check_public({**saved_projection, "approved_deposit_conditions": {}}, item["expected_public"])
        results.append(checked)
    for country, (old, new) in snapshots.items():
        selected = [pid for pid, identity in PRODUCTS.items() if identity[0] == country]
        # Both directions protect against lost and unexpectedly added rows.
        for a, b in ((old,new),(new,old)):
            diff = connection.execute("SELECT count(*) AS n FROM (SELECT to_jsonb(p)-'snapshot_id' AS row FROM public_product_projection p WHERE snapshot_id=%s AND NOT(product_id=ANY(%s)) EXCEPT SELECT to_jsonb(p)-'snapshot_id' AS row FROM public_product_projection p WHERE snapshot_id=%s AND NOT(product_id=ANY(%s))) d", (a,selected,b,selected)).fetchone()["n"]
            require(diff == 0, "Unrelated projection changed")
        counts = connection.execute("SELECT snapshot_id,count(*) AS n FROM public_product_projection WHERE snapshot_id IN (%s,%s) GROUP BY snapshot_id", (old,new)).fetchall()
        require(len(counts) == 2 and counts[0]["n"] == counts[1]["n"], "Projection rows lost or added")
        active = connection.execute("SELECT count(*) AS n FROM public_product_projection WHERE snapshot_id=%s AND status='active'", (new,)).fetchone()["n"]
        connection.execute("UPDATE aggregate_refresh_run SET refresh_metadata=jsonb_set(refresh_metadata,'{source_counts,active_rows}',%s) WHERE snapshot_id=%s", (Jsonb(active),new))
    return {"status":"verified","operation_id":operation,"snapshots":snapshots,"products":results}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--env-file", default=str(ROOT / ".env.dev"))
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    with open_connection(Settings.from_env(args.env_file)) as connection:
        result = run(connection, json.loads(MANIFEST.read_text(encoding="utf8")))
        if args.apply:
            connection.commit()
        else:
            connection.rollback()
    print(json.dumps({**result, "committed": args.apply and result["status"] == "verified"}, default=str))


if __name__ == "__main__":
    main()
