"""Rehearse or apply the two-bank reference configuration in the connected dev DB."""
import argparse
import json
from pathlib import Path
import sys
from uuid import uuid4

import psycopg
from psycopg.rows import dict_row

ROOT = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(ROOT), str(ROOT / "api/service")]

from api_service.source_catalog import create_source_catalog_item
from api_service.source_registry_utils import normalize_source_url
from worker.pipeline.fpds_approval_policy import collection_fields_for_product_type
from worker.pipeline.fpds_market_profile import country_product_profile


BANKS = (
    ("HIGO", "肥後銀行", "https://www.higobank.co.jp/", "individual/description.html", "business/service/funding/"),
    ("KAGOSHIMA", "鹿児島銀行", "https://www.kagin.co.jp/", "kojin/savings/100_016.html", "houjin/202_support.html"),
)
PRODUCTS = {
    "chequing": "deposit", "savings": "deposit", "gic": "deposit", "mortgage": "lending",
    "personal-loan": "lending", "line-of-credit": "lending",
    "business-loan": "lending", "business-line-of-credit": "lending",
}


def register(connection):
    connection.execute("SELECT pg_advisory_xact_lock(hashtext('fpds-jp-higo-kagoshima'))")
    changes = []
    request_id = "jp-bank-preparation-" + uuid4().hex
    actor = {"actor_type": "service", "user_id": "jp-bank-preparation", "role": "maintenance"}
    registration = connection.execute("""
        INSERT INTO country_registry (country_code,country_name,status,display_order)
        VALUES ('JP','Japan','active',1000) ON CONFLICT (country_code) DO UPDATE
        SET status='active',updated_at=now() WHERE country_registry.status='inactive'
    """)
    if registration.rowcount:
        changes.append("country/JP")
    for kind, family in PRODUCTS.items():
        profile = country_product_profile(country_code="JP", product_type=kind)
        if profile is None:
            raise ValueError(f"Missing JP market contract for {kind}")
        display = {"gic": "GIC / term deposit", "business-line-of-credit": "Business line of credit"}.get(
            kind, kind.replace("-", " ").capitalize())
        defaults = (profile.collection_fields if kind.startswith("business-")
                    else collection_fields_for_product_type(product_type=kind))
        inserted = connection.execute("""
            INSERT INTO product_type_registry
                (product_type_code,product_family,display_name,description,status,expected_fields)
            VALUES (%s,%s,%s,%s,'active',%s::jsonb) ON CONFLICT (product_type_code) DO NOTHING
        """, (kind, family, display, display, json.dumps(defaults)))
        if inserted.rowcount:
            changes.append("type/" + kind)
        existing = connection.execute("SELECT status,product_family FROM product_type_registry WHERE product_type_code=%s",
                                      (kind,)).fetchone()
        if not existing or existing["status"] != "active" or existing["product_family"] != family:
            raise ValueError(f"Incompatible registered product type {kind}")
        inserted = connection.execute("""
            INSERT INTO taxonomy_registry (taxonomy_id,country_code,product_family,product_type,subtype_code,display_order)
            VALUES (%s,'JP',%s,%s,'other',999)
            ON CONFLICT (country_code,product_family,product_type,subtype_code) DO NOTHING
        """, (f"tax-jp-{family}-{kind}-other", family, kind))
        if inserted.rowcount:
            changes.append("taxonomy/JP/" + kind)
        elif not connection.execute("""
            SELECT active_flag FROM taxonomy_registry WHERE country_code='JP' AND product_family=%s
                AND product_type=%s AND subtype_code='other'
        """, (family, kind)).fetchone()["active_flag"]:
            raise ValueError(f"Inactive JP taxonomy for {kind}")
    for code, name, homepage, personal, business in BANKS:
        inserted = connection.execute("""
            INSERT INTO bank (bank_code,country_code,bank_name,status,homepage_url,normalized_homepage_url,
                              source_language,managed_flag,change_reason)
            VALUES (%s,'JP',%s,'active',%s,%s,'ja',true,'JP official source preparation')
            ON CONFLICT (bank_code) DO NOTHING
        """, (code, name, homepage, normalize_source_url(homepage)))
        row = connection.execute("SELECT * FROM bank WHERE bank_code=%s FOR UPDATE", (code,)).fetchone()
        if (row["country_code"], row["bank_name"], row["normalized_homepage_url"], row["source_language"], row["status"]) != (
                "JP", name, normalize_source_url(homepage), "ja", "active"):
            raise ValueError(f"Existing bank identity or state conflicts with {code}")
        if inserted.rowcount:
            changes.append("bank/" + code)
        for kind in PRODUCTS:
            url = homepage + (business if kind.startswith("business-") else personal)
            existing = connection.execute("""
                SELECT status,normalized_coverage_source_url FROM source_registry_catalog_item
                WHERE country_code='JP' AND bank_code=%s AND product_type=%s
            """, (code, kind)).fetchone()
            if existing:
                if existing["status"] != "active" or existing["normalized_coverage_source_url"] != normalize_source_url(url):
                    raise ValueError(f"Existing coverage conflicts with {code}/{kind}")
                continue
            create_source_catalog_item(connection, payload={
                "bank_code": code, "product_type": kind, "coverage_source_url": url,
                "change_reason": "JP official source preparation",
            }, actor=actor, request_context={"request_id": request_id})
            changes.append("scope/" + code + "/" + kind)
    return changes


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true", help="Commit the rehearsed development configuration")
    args = parser.parse_args()
    # This one-off pack targets only the workspace's explicit dev connection.
    config = dict(line.split("=", 1) for line in (ROOT / ".env.dev").read_text(encoding="utf-8-sig").splitlines()
                  if "=" in line and not line.lstrip().startswith("#"))
    if config["FPDS_ENV"].strip().strip('"') != "dev":
        raise SystemExit("Expected FPDS_ENV=dev in .env.dev")
    with psycopg.connect(config["FPDS_DATABASE_URL"].strip().strip('"'), row_factory=dict_row,
                         connect_timeout=8, options="-c lock_timeout=5000 -c statement_timeout=20000") as connection:
        changed = register(connection)
        if not args.apply:
            connection.rollback()
    print(json.dumps({"committed": args.apply, "changes": changed}, ensure_ascii=True))
