"""Private read-only PF preparation. Emit one current approved product per JSON line."""
import argparse
import json
import re
import sys
import unicodedata
from decimal import Decimal

from api_service.config import REPO_ROOT, Settings
from api_service.db import open_connection

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
from worker.native_japanese_disclosure import annual_limit_tiers
from worker.pipeline.fpds_field_contract import field_contract, value_matches_contract


def prepare_conditions(product, facts, definitions, choices):
    values = []

    def add(code, value, fields, **context):
        if code not in definitions:
            return
        definition = definitions[code]
        if definition["value_type"] != "L":
            if not definition["minimum_value"] <= Decimal(str(value)) <= definition["maximum_value"]:
                return
        values.append({"condition_code": code, "type": definition["value_type"], "value": value,
                       "unit": definition["unit"], "evidence_ids": sorted({
                           ref for field in fields for ref in facts[field]["evidence_ids"]}), **context})

    currency = product["currency"]
    if "currency" in facts and facts["currency"]["value"] == currency and currency in choices:
        add("L02", choices[currency], ["currency"])
    deposit = facts.get("minimum_deposit", {}).get("value")
    if type(deposit) in (int, float, Decimal):
        add("R01", deposit, ["minimum_deposit"], currency=currency)
    table = facts.get("term_rate_table", {}).get("value")
    if (product["template_code"] == "D03" and isinstance(table, list)
            and value_matches_contract("term_rate_table", table) and "I01" in definitions
            and all(definitions["I01"]["minimum_value"] <= row["rate"] <= definitions["I01"]["maximum_value"]
                    for row in table)):
        for row in table:
            qualifiers = {key: value for key, value in row.items() if key != "rate" and value is not None}
            add("I01", row["rate"], ["term_rate_table"], currency=currency, **qualifiers)

    # The first/last rate rows omit the contractual limit endpoints. Only join
    # them when the same approved version independently proves both fields.
    if product["institution_code"] == "KAGO" and product["template_code"] == "C03" and currency == "JPY":
        limit = facts.get("credit_limit_text", {}).get("value")
        schedule = facts.get("interest_rate_summary", {}).get("value")
        if isinstance(limit, str):
            bounds = re.findall(r"(\d[\d,]*)\s*万円以上\s*(\d[\d,]*)\s*万円以内",
                                unicodedata.normalize("NFKC", limit))
            if len(bounds) == 1:
                low, high = (int(n.replace(",", "")) * 10000 for n in bounds[0])
                tiers = annual_limit_tiers(schedule) if isinstance(schedule, str) else []
                if 0 < low <= high:
                    add("R09", low, ["credit_limit_text"], currency=currency, inclusive=True)
                    add("R10", high, ["credit_limit_text"], currency=currency, inclusive=True)
                    if (tiers and tiers[0][0] is None and tiers[-1][1] is None
                            and low <= tiers[0][1] and high > tiers[-1][0]
                            and "I02" in definitions and all(
                                definitions["I02"]["minimum_value"] <= Decimal(rate) <= definitions["I02"]["maximum_value"]
                                for _, _, rate in tiers)):
                        for lower, upper, rate in tiers:
                            add("I02", rate, ["credit_limit_text", "interest_rate_summary"],
                                basis="credit_limit", currency=currency,
                                lower=low if lower is None else lower, lower_inclusive=lower is None,
                                upper=high if upper is None else upper, upper_inclusive=True)
    return values


def read_products(connection, country, bank):
    if not connection.execute("SELECT 1 FROM pf_channel_institution WHERE country_code=%s AND bank_code=%s",
                              (country, bank)).fetchone():
        raise ValueError("Unknown PF channel bank for this country")
    definitions = {}
    for row in connection.execute("""
        SELECT tc.template_code, c.* FROM pf_channel_template_condition tc
        JOIN pf_channel_condition c USING (condition_code) ORDER BY tc.template_code, c.condition_code
    """):
        definitions.setdefault(row["template_code"], {})[row["condition_code"]] = row
    choices = {r["label"]: r["choice_code"] for r in connection.execute(
        "SELECT label, choice_code FROM pf_channel_choice WHERE condition_code='L02'")}
    for product in connection.execute("""
        SELECT * FROM pf_channel_product WHERE country_code=%s AND bank_code=%s ORDER BY product_id
    """, (country, bank)):
        facts = {}
        for row in connection.execute("""
            SELECT field_name, field_value::text AS json_value, evidence_ids
            FROM pf_channel_fact WHERE country_code=%s AND product_version_id=%s ORDER BY field_name
        """, (country, product["product_version_id"])):
            contract = field_contract(row["field_name"])
            facts[row["field_name"]] = {"value": json.loads(row["json_value"], parse_float=Decimal),
                                        "value_type": contract.value_type if contract else None,
                                        "unit": contract.unit if contract else None,
                                        "evidence_ids": row["evidence_ids"]}
        template = definitions[product["template_code"]]
        conditions = prepare_conditions(product, facts, template, choices)
        yield {**product, "contract_version": 1, "conditions": conditions, "source_facts": facts,
               "conditions_without_value": sorted(set(template) - {r["condition_code"] for r in conditions})}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--env-file", required=True)
    parser.add_argument("--country", required=True)
    parser.add_argument("--bank", required=True, help="FPDS bank code")
    args = parser.parse_args()
    with open_connection(Settings.from_env(args.env_file), read_only=True) as connection:
        # A single snapshot keeps definitions, versions and evidence aligned.
        connection.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY")
        for product in read_products(connection, args.country, args.bank):
            print(json.dumps(product, default=str, ensure_ascii=True, allow_nan=False))


if __name__ == "__main__":
    main()
