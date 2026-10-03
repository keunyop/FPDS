"""Fail-closed, shared collection acceptance. No human decisions or model scores."""
from __future__ import annotations

from collections.abc import Mapping
from decimal import Decimal
from hashlib import sha256
import json
import re
from urllib.parse import urlsplit, urlunsplit

from worker.country_defaults import default_currency_for_country
from worker.pipeline.fpds_field_contract import field_contract, value_matches_contract
from worker.pipeline.fpds_approval_policy import comparison_quality, security_meaning, withdrawal_consequences_usable
from worker.pipeline.fpds_rate_safety import rate_component_only

ACCURACY_VERSION = "collection-accuracy-2026-10-01-cost-access"
# Earlier receipts retain digest compatibility, subject to the current comparison gate.
_COMPATIBLE_RECEIPT_VERSIONS = {ACCURACY_VERSION, "collection-accuracy-2026-10-01", "collection-accuracy-2026-09-30"}
RECEIPT_KEY = "_collection_accuracy"
# Registry/workflow metadata is not a collected financial attribute.
CONTEXT_FIELDS = {"status", "last_verified_at", "bank_name", "subtype_code"}
CURRENCY_PATTERNS = {"CAD": r"\bCAD\b|Canadian dollars?|\bC\$|\bCA\$", "USD": r"\bUSD\b|U\.?S\.? dollars?|\bUS\$", "EUR": r"\bEUR\b|euros?|\u20ac", "GBP": r"\bGBP\b|pounds? sterling|\u00a3"}
CURRENCY_PATTERNS.update({
    "JPY": r"\bJPY\b|Japanese yen|\byen\b|[\u00a5\uffe5]",
    "HKD": r"\bHKD\b|Hong Kong dollars?|\bHK\$",
    "CNY": r"\bCNY\b|\bRMB\b|Chinese yuan|renminbi",
    "AUD": r"\bAUD\b|Australian dollars?|\bA\$",
    "NZD": r"\bNZD\b|New Zealand dollars?|\bNZ\$",
    "CHF": r"\bCHF\b|Swiss francs?",
    "SGD": r"\bSGD\b|Singapore dollars?",
})
IDENTITY_FIELDS = ("country_code", "bank_code", "product_type", "product_name", "currency")
_NUMBER = r"(?<![\w.])(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?(?![\w.])"
_COUNT_WORDS = dict(zip(("zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten"), range(11)))
_ANNUAL_RATE_BASIS = re.compile(
    r"\bannual(?:ized)?\s+(?:(?:interest|percentage)\s+)?(?:rates?|yield)\b"
    r"|\binterest rates? (?:is|are) annualized\b"
    r"|\b(?:apr|apy|per annum|per year)\b|\bp\.?a\.?(?!\w)", re.I,
)


def _money_has_condition(quote: str, field_name: str) -> bool:
    # A standalone suitability heading is not a condition on a preceding fee.
    # Keep its following text, including any actual balance/waiver condition.
    context = re.sub(r"(?mi)^Great if[ \t]*\r?\n(?=You (?:want|prefer)\b)", "Suitability\n", quote)
    if re.search(r"\b(?:if|when|waived|waiver|provided|qualify|qualifying|maintain|introductory|promotional)\b"
        r"|subject to(?!\s+change(?:\s+without\s+(?:prior\s+)?notice)?(?:[.!](?:\s|$)|$))"
        r"|\bonly\s+for\b|\bfor\s+(?:eligible|selected|new)\s+(?:customers|cardholders)\b"
        r"|\bfirst\s+(?:year|month|\d+\s+(?:years?|months?))\b", context, re.I):
        return True
    if field_name in {"monthly_fee", "public_display_fee", "annual_fee", "transaction_fee", "additional_transaction_fee"} and re.search(
        r"\buntil\b|\baverage\s+(?:monthly|daily)\s+(?:closing\s+)?balance\b"
        r"|\b(?:for|first)\s+(?:(?:the|your)\s+)?(?:(?:first|next|initial)\s+)?"
        r"(?:\d+(?:\.\d+)?|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve)\s+(?:months?|years?)\b",
        context, re.I,
    ):
        return True
    # An explicitly absent balance requirement is not a fee-waiver threshold.
    # Remove only this exact negation for condition classification; retain the
    # complete quote and every surrounding qualifier for all other checks.
    if re.search(r"\b(?:not|does not mean|doesn't mean)\s+no minimum balance required\b", context, re.I):
        return True
    balance_context = re.sub(r"\bno minimum balance required\b", "no balance requirement", context, flags=re.I)
    return field_name in {"monthly_fee", "public_display_fee", "annual_fee", "transaction_fee"} and bool(
        re.search(r"minimum balance|at least", balance_context, re.I))


# Flattened official fee tables retain one label/value per line. Footnote markers
# belong to the label, never to the native count or price on the next line.
_COUNT_ROW_LABEL = r"Transactions? included per month(?:[ \t]+\d+(?:[ \t]*,[ \t]*\d+)*)?"
_EXCESS_ROW_LABEL = r"(?:Additional|Extra|Excess|Overage) transaction (?:fee|charge)s?(?:[ \t]+\d+)?"

_ORDINARY_UNLIMITED = r"\bunlimited\s+(?:(?:ordinary|free|no fee|debit|everyday|day-to-day|banking|monthly)\s+){0,3}transactions?\b"


def _checking_table_value(field_name: str, value: object, quote: str) -> bool | None:
    if field_name not in {"included_transactions", "additional_transaction_fee"}:
        return None
    debit_rows = list(re.finditer(
        r"(?mi)^[ \t]*(\d+)[ \t]+Debits(?:[ \t]+legal disclaimer[ \t]+\d+)?[ \t]*/[ \t]*Month[ \t]*\r?$",
        quote,
    ))
    if debit_rows:
        if len(debit_rows) != 1 or re.search(
            r"\b(?:if|when|provided|qualify|qualifying|waived|waiver|maintain|ATM|ABM|wire|foreign|international)\b|public transit",
            quote, re.I,
        ) or re.search(_ORDINARY_UNLIMITED, quote, re.I):
            return False
        if field_name == "included_transactions":
            return int(debit_rows[0][1]) == value
        tail = quote[debit_rows[0].end():]
        cost = re.match(r"\s*(?:legal disclaimer\s*)?\$(\d+(?:\.\d+)?)\s+each thereafter(?:\.|(?=\s|$))", tail, re.I)
        return bool(cost and Decimal(cost[1]) == Decimal(str(value))
                    and len(re.findall(r"\beach thereafter\b", quote, re.I)) == 1)
    label = _COUNT_ROW_LABEL if field_name == "included_transactions" else _EXCESS_ROW_LABEL
    labels = list(re.finditer(rf"(?mi)^[ \t]*(?:{label})[ \t]*\r?$", quote))
    if not labels:
        return None
    # Multiple rows may belong to different products; do not guess applicability.
    if len(labels) != 1 or re.search(r"\b(?:if|when|provided|qualify|qualifying|waived|waiver)\b", quote, re.I):
        return False
    if re.search(_ORDINARY_UNLIMITED, quote, re.I):
        return False
    tail = quote[labels[0].end():]
    if field_name == "included_transactions":
        match = re.match(r"[ \t]*\r?\n[ \t]*(\d+)[ \t]*(?:\r?\n|$)", tail)
        if not match or int(match[1]) != value:
            return False
        # Another ordinary count in the same retained context is a conflict.
        other = re.findall(r"(?<![\w.,−-])(\d+)\s+(?:(?:free|included|debit|everyday|monthly)\s+){0,3}transactions?\b", quote, re.I)
        return all(int(count) == value for count in other)
    match = re.match(r"[ \t]*\r?\n[ \t]*(?:CAD[ \t]*)?\$(\d+(?:\.\d+)?)(?:[ \t]+CAD)?[ \t]+each\.?[ \t]*(?:\r?\n|$)", tail, re.I)
    return bool(match and Decimal(match[1]) == Decimal(str(value)))


def _rate_from_is_condition(field_name: str, quote: str) -> bool:
    occurrences = list(re.finditer(r"\bfrom\b", quote, re.I))
    if not occurrences:
        return False
    # Only the demonstrated card-offer exclusion is separate from an explicit
    # current preferred annual declaration under its own Rates and Fees heading.
    # All other uses of "from", including temporal qualifiers, stay fail-closed.
    marker = re.search(r"(?mi)^[ \t]*Rates and Fees:", quote)
    if field_name not in {"purchase_interest_rate", "cash_advance_rate", "balance_transfer_rate"} or not marker:
        return True
    if not re.search(r"\bThe current preferred annual interest rates for (?:the|this) Account are:", quote[marker.end():]):
        return True
    rate_context = quote[marker.end():]
    if re.search(
        r"\b(?:provided|conditional|penalty|default)\b|\bonly\s+for\b"
        r"|\bfor\s+(?:new|selected|eligible)\s+(?:customers|cardholders)\b", rate_context, re.I,
    ):
        return True
    prefix = quote[:marker.start()]
    allowed = set()
    for switch in re.finditer(
        r"\bincluding those that switch\s+(from)\s+an existing\s+"
        r"(?:[^\W\d_]+[®™*†]?\s+){0,6}credit card\b", prefix, re.I,
    ):
        exclusion = re.match(r"[^.%]*?\bare not eligible for the Offer\.", prefix[switch.end():], re.I)
        if exclusion:
            allowed.add(switch.start(1))
    return any(occurrence.start() not in allowed for occurrence in occurrences)


def _labelled_current_card_rate(field_name: str, value: Decimal, quote: str) -> bool:
    if field_name not in {"purchase_interest_rate", "cash_advance_rate", "balance_transfer_rate"}:
        return False
    heading = quote.lower().find("rates and fees:")
    rate_context = quote[heading:] if heading >= 0 else quote
    if re.search(r"\b(?:provided|conditional|penalty|default|only|eligible)\b", rate_context, re.I):
        return False
    pattern = (
        r"\bThe current preferred annual interest rates for (?:the|this) Account are:\s*"
        r"(\d+(?:\.\d+)?)% on purchases and (\d+(?:\.\d+)?)% on cash advances"
        r"(\s*\(including balance transfers(?:, Scotia[\u00ae\u2122]? Credit Card Cheques)? and cash-like transactions\))?\."
    )
    matches = list(re.finditer(pattern, quote, re.I))
    if len(matches) != 1:
        return False
    match = matches[0]
    # Every percentage must belong to this complete, explicit declaration.
    percentages = list(re.finditer(r"\d+(?:\.\d+)?\s*%", quote))
    if len(percentages) != 2 or any(not (match.start() <= p.start() < match.end()) for p in percentages):
        return False
    if field_name == "balance_transfer_rate" and not match[3]:
        return False
    return value == Decimal(match[1 if field_name == "purchase_interest_rate" else 2])


def _rate_context_has_condition(field_name: str, value: Decimal, quote: str) -> bool:
    conditions = list(re.finditer(
        r"\b(?:up to|between|as low as|bonus|introductory|promotional|example|illustration|if|when|qualify|qualifying|depending)\b",
        quote, re.I,
    ))
    if not conditions:
        return False
    if field_name in {"standard_rate", "public_display_rate"}:
        # A separate deposit-insurance ceiling is not a payable-rate ceiling.
        # Require a complete, standalone annual deposit-rate declaration and
        # recognize only the exact insurance clause; keep all other conditions.
        declarations = re.finditer(
            r"(?mi)^[ \t]*(?:(?P<first>\d{1,2}(?:\.\d{1,4})?)\s*%\*?\s+"
            r"Annual (?:Interest Rate|Percentage Yield)|Annual (?:Interest Rate|Percentage Yield)"
            r"(?: \(APY\))?:[ \t]*(?P<last>\d{1,2}(?:\.\d{1,4})?)\s*%)[.]?[ \t]*$", quote,
        )
        if any(Decimal(m.group("first") or m.group("last")) == value for m in declarations):
            insurance_limits = {
                m.start("ceiling") for m in re.finditer(
                    r"(?mi)^[ \t]*(?:Safe and secure [\u2013-] )?(?:eligible )?deposits are insured "
                    r"(?P<ceiling>up to) (?:the maximum amount|\$\d[\d,]*(?:\.\d{2})?) "
                    r"(?:through|by) (?:the )?(?:Canada Deposit Insurance Corporation \(CDIC\)|"
                    r"Federal Deposit Insurance Corporation \(FDIC\)|FDIC)[.]?[ \t]*$", quote,
                )
            }
            conditions = [m for m in conditions if m.start() not in insurance_limits]
            if not conditions:
                return False
    heading = re.search(r"(?mi)^[ \t]*Rates and Fees:", quote)
    # This exact offer-revocation clause precedes a separately declared current
    # rate. Keep the complete evidence; no other condition can be disregarded.
    if not heading or not _labelled_current_card_rate(field_name, value, quote):
        return True
    allowed = set()
    for revocation in re.finditer(
        r"\bWe reserve the right to revoke this Offer at any time (if) we determine "
        r"you do not meet the Offer eligibility requirements, including after you "
        r"have accepted the Offer or been approved for the Account\.",
        quote[:heading.start()], re.I,
    ):
        allowed.add(revocation.start(1))
    # A later numbered transaction-fee note is a different charge, not a
    # condition on the preceding labelled annual interest declaration.
    cash_clause = re.search(r"\d+(?:\.\d+)?% on cash advances(?:\s*\([^)]*\))?\.", quote, re.I)
    for fee_note in re.finditer(
        r"(?m)^[ \t]*\d+[ \t]*\r?\nTransaction fees may apply (when)\b", quote,
    ):
        if cash_clause and fee_note.start() > cash_clause.end():
            allowed.add(fee_note.start(1))
    return any(condition.start() not in allowed for condition in conditions)


def _transaction_count_supported(value: int, quote: str) -> bool:
    if re.search(r"\b(?:if|when|provided|qualify|qualifying)\b", quote, re.I):
        return False
    # Do not read the final word/digits of an unsupported composite count.
    if re.search(r"\b(?:twenty|thirty|forty|fifty|sixty|seventy|eighty|ninety|hundred|thousand|million|point|plus)\b", quote, re.I):
        return False
    tokens = "|".join(_COUNT_WORDS)
    if re.search(rf"\b(?:up to|between)\s+(?:\d+|{tokens})\b|\b(?:\d+|{tokens})\s+(?:or|to)\s+(?:\d+|{tokens})\b|\b(?:minus|negative)\b", quote, re.I):
        return False
    matches = re.findall(rf"(?<![\w.,−-])(\d{{1,3}}(?:,\d{{3}})+|\d+|{tokens})\s+(?:(?:free|included|debit|everyday|monthly)\s+){{0,3}}transactions?\b", quote, re.I)
    counts = {_COUNT_WORDS[token.lower()] if token.lower() in _COUNT_WORDS else int(token.replace(",", "")) for token in matches}
    return counts == {value}



def text(value: object) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def exact_quote(quote: object, excerpt: object) -> bool:
    q = text(quote)
    return bool(q and "..." not in q and "…" not in q and q.casefold() in text(excerpt).casefold())


def _numbers(value: str) -> list[Decimal]:
    return [Decimal(m.group().replace(",", "")) for m in re.finditer(_NUMBER, value)]


def quote_supports_value(field_name: str, value: object, quote: str) -> bool:
    """Require field meaning as well as exact values; never strip units into numbers."""
    if value is None or not value_matches_contract(field_name, value):
        return False
    contract = field_contract(field_name)
    q = text(quote)
    if not contract or not q:
        return False
    if field_name == "currency":
        return value in CURRENCY_PATTERNS and bool(re.search(CURRENCY_PATTERNS[value], q, re.I)) and not any(
            code != value and re.search(pattern, q, re.I) for code, pattern in CURRENCY_PATTERNS.items())
    if contract.value_type == "string":
        if field_name in {"security_requirement", "collateral_text"}:
            return text(value).casefold() == q.casefold() and security_meaning(value) is not None
        if field_name == "early_withdrawal_penalty":
            return text(value).casefold() == q.casefold() and withdrawal_consequences_usable(value)
        if field_name in {"interest_rate_summary", "purchase_interest_rate_summary", "fee_waiver_condition", "early_withdrawal_penalty"}:
            return text(value).casefold() == q.casefold()
        return bool(text(value)) and text(value).casefold() in q.casefold()
    table_value = _checking_table_value(field_name, value, quote)
    if table_value is not None:
        return table_value
    if field_name in {"transaction_fee", "additional_transaction_fee", "unlimited_transactions_flag", "included_transactions"} and re.search(r"\b(?:ATM|ABM|wire|international|foreign|e[- ]?transfer)\s+(?:(?:additional|extra|excess|overage|debit|cash)\s+)*transactions?\b|\bunlimited\s+(?:ATM|ABM|wire|e[- ]?transfer)\b", q, re.I):
        # A charge/allowance for one special channel cannot prove general account pricing.
        return False
    if field_name == "transaction_fee" and re.search(r"\b(?:additional|extra|excess|overage)\s+transactions?", q, re.I):
        # Excess-only pricing must retain its distinct field; it is not per-use pricing.
        return False
    if contract.value_type == "boolean":
        if field_name == "unlimited_transactions_flag" and re.search(r"\b(?:if|when|provided|qualify|qualifying)\b", q, re.I):
            return False
        if field_name == "unlimited_transactions_flag" and re.search(
            r"\b(?:public transit|ATM|ABM|wire|e[- ]?transfer)(?: transactions?)?\s*[:–-]?\s*unlimited\b"
            r"|" + _ORDINARY_UNLIMITED + r"\s+(?:\d+\s+)?"
            r"(?:only\s+)?(?:for|on|at)\s+(?:public transit|ATMs?|ABMs?|wire|e[- ]?transfer)\b", q, re.I,
        ):
            return False
        if field_name == "unlimited_transactions_flag" and (
            re.search(r"\b(?:not|no)\s+unlimited\b", q, re.I)
            or (value is True and (re.search(r"\b\d+\s+(?:(?:free|included|debit|monthly)\s+)*transactions?\b", q, re.I)
                                   or re.search(r"(?mi)^" + _COUNT_ROW_LABEL + r"[ \t]*\r?$", quote)))
        ):
            return False
        if field_name == "secured_flag":
            return security_meaning(q) is value
        if field_name in {"redeemable_flag", "non_redeemable_flag"}:
            maturity_only = re.search(
                r"(?:^|[.!?]\s+)(?:Cashable|Redeemable) (?:upon|at) maturity only(?:[.](?:$|\s)|$)"
                r"|(?:^|[.!?]\s+)Can only be (?:redeemed|cashed) at maturity(?:[.](?:$|\s)|$)", q, re.I)
            if maturity_only:
                if re.search(r"\b(?:except|unless|however|but)\b.{0,100}\b(?:withdraw|redeem|cash|maturity)", q, re.I):
                    return False
                if re.search(r"(?:can be|may be|is) (?:redeemed|cashed) before maturity|early (?:withdrawal|redemption) (?:is )?(?:allowed|permitted)", q, re.I):
                    return False
                return value is (field_name == "non_redeemable_flag")
        # Absence of a positive statement never proves false.
        patterns = {
            "secured_flag": (r"(?<!un)\bsecured\b|\bcollateral (?:is )?required\b", r"\bunsecured\b|no collateral required|\bnot secured\b"),
            "unlimited_transactions_flag": (_ORDINARY_UNLIMITED, r"\b(?:limited to|maximum of) \d+.{0,20}transactions?"),
            "redeemable_flag": (r"(?<!non-)\bredeemable\b|can be (?:redeemed|cashed) before maturity", r"non[- ]redeemable|cannot be (?:redeemed|cashed) before maturity"),
            "non_redeemable_flag": (r"non[- ]redeemable|cannot be (?:redeemed|cashed) before maturity", r"(?<!non-)\bredeemable\b"),
        }
        pair = patterns.get(field_name)
        if re.search(r"\b(?:may|might|could|optional|depending)\b|not unsecured|not non[- ]redeemable", q, re.I):
            return False
        if not pair:
            return False
        yes, no = (bool(re.search(p, q, re.I)) for p in pair)
        # non-redeemable contains redeemable; resolve explicit negation first.
        if field_name == "redeemable_flag" and no:
            yes = False
        if field_name == "non_redeemable_flag" and yes:
            no = False
        return (yes and not no) if value is True else (no and not yes)
    if contract.value_type == "json":
        if field_name != "term_rate_table" or not isinstance(value, list) or not value:
            return False
        for row in value:
            label = text(row.get("term_label"))
            # Require a rate in the same row following this exact term. Never
            # accept merely finding every number somewhere in a large table.
            matches = list(re.finditer(r"(?<!\w)" + re.escape(label) + r"(?!\w)", q, re.I)) if label else []
            if len(matches) != 1:
                return False
            local = q[matches[0].end():matches[0].end() + 160]
            first_rate = re.search(r"(?<![\d.])(\d+(?:\.\d+)?)\s*%", local)
            if not first_rate or re.search(r"\b\d+\s*[- ]?\s*(?:days?|months?|years?)\b|[-−]\s*\d", local[:first_rate.end()], re.I):
                return False
            rates = [first_rate.group(1)]
            if not rates or Decimal(rates[0]) != Decimal(str(row["rate"])):
                return False
            days = row.get("term_length_days")
            if days is not None and not re.search(rf"(?<![\d.]){days}\s*days?\b", label, re.I):
                return False
            amount = row.get("minimum_deposit")
            if amount is not None and not quote_supports_value("minimum_deposit", amount, local):
                return False
            if row.get("notes") and not exact_quote(row["notes"], q):
                return False
        return True
    if re.search(r"[-−]\s*\d+(?:\.\d+)?\s*%", q):
        return False
    number = Decimal(str(value))
    if not number.is_finite() or number < 0:
        return False
    if contract.unit == "percentage_points":
        # Comparison benchmarks are not the named product's own payable rate.
        # Retained full context is screened by the same rule below grounding.
        if re.search(r"\b(?:national|industry|market)\s+average\b|\bcompetitor(?:s|'s)?\b", q, re.I):
            return False
        if rate_component_only(value=value, context=q):
            return False
        rates = re.findall(r"(?<![\d.])(\d+(?:\.\d+)?)\s*%", q)
        # A scalar cannot represent a tier, range, conditional offer or example.
        if _rate_context_has_condition(field_name, number, quote) or _rate_from_is_condition(field_name, quote):
            return False
        if len({Decimal(v) for v in rates}) != 1:
            return number < 100 and _labelled_current_card_rate(field_name, number, quote)
        rate_labels = {
            "purchase_interest_rate": r"purchase",
            "cash_advance_rate": r"cash advance",
            "balance_transfer_rate": r"balance transfer",
            "mortgage_rate": r"mortgage",
            "base_12_month_rate": r"12[- ]month|1[- ]year|one[- ]year",
        }
        meaning = rate_labels.get(field_name)
        if meaning and not re.search(meaning, q, re.I):
            return False
        return number < 100 and number in {Decimal(v) for v in rates} and bool(re.search(r"\b(?:rate|interest|apr|apy|yield)\b", q, re.I))
    labels = {
        "monthly_fee": r"monthly.{0,25}(?:fee|charge)|(?:fee|charge).{0,20}(?:monthly|per month)",
        "public_display_fee": r"monthly.{0,25}(?:fee|charge)|(?:fee|charge).{0,20}(?:monthly|per month)",
        "annual_fee": r"annual.{0,20}fee|fee.{0,20}(?:annual|per year)",
        "minimum_deposit": r"(?:minimum|initial|opening).{0,30}deposit|deposit.{0,30}(?:minimum|to open)|open.{0,25}(?:at least|minimum)",
        "minimum_balance": r"minimum.{0,25}balance|balance.{0,25}(?:at least|minimum)",
        "transaction_fee": r"transaction.{0,20}(?:fee|charge)|per transaction",
        "additional_transaction_fee": r"(?:additional|extra|excess|overage).{0,30}transactions?.{0,20}(?:fee|charge)?|(?:fee|charge).{0,25}(?:additional|extra|excess) transactions?",
        "included_transactions": r"transactions?",
        "term_length_days": r"days?",
    }
    label = labels.get(field_name)
    if not label or not re.search(label, q, re.I):
        return False
    if field_name == "included_transactions":
        return _transaction_count_supported(int(number), q)
    if field_name == "term_length_days":
        return bool(re.search(rf"(?<![\d.]){int(number)}\s*days?\b", q, re.I))
    if contract.unit == "currency_amount":
        # A waiver balance or example must not stand in for a fee.
        amounts = re.findall(r"(?:[$€£]|\b(?:CAD|USD|EUR|GBP)\s*)(\d[\d,]*(?:\.\d+)?)", q, re.I)
        amounts += re.findall(r"(\d[\d,]*(?:\.\d+)?)\s*(?:dollars?|CAD|USD|EUR|GBP)\b", q, re.I)
        matching = {Decimal(v.replace(",", "")) for v in amounts}
        if number == 0 and _money_has_condition(quote, field_name):
            return False
        # Zero must negate this attribute, not an unrelated fee/balance nearby.
        zero_labels = {
            "monthly_fee": r"monthly(?: account)? (?:fees?|charges?)",
            "public_display_fee": r"monthly(?: account)? (?:fees?|charges?)",
            "annual_fee": r"annual (?:fees?|charges?)",
            "transaction_fee": r"transaction (?:fees?|charges?)",
            "additional_transaction_fee": r"(?:additional|extra|excess) transaction (?:fees?|charges?)",
            "minimum_balance": r"minimum(?: daily(?: closing)?)? balance",
            "minimum_deposit": r"(?:minimum(?: opening)?|initial|opening) deposit",
        }
        zero_label = zero_labels.get(field_name)
        if number == 0 and zero_label and re.search(rf"\b(?:no|zero)\s+(?:{zero_label})\b", q, re.I):
            return True
        if number not in _numbers(q) or number not in matching:
            return False
        if field_name in {"monthly_fee", "public_display_fee", "annual_fee", "minimum_deposit", "minimum_balance", "transaction_fee", "additional_transaction_fee"}:
            label_match = re.search(label, q, re.I)
            local = q[label_match.end():label_match.end() + 90]
            local_amount = re.search(r"(?:[$€£]|\b(?:CAD|USD|EUR|GBP)\s*)(\d[\d,]*(?:\.\d+)?)", local, re.I)
            if local_amount:
                return Decimal(local_amount.group(1).replace(",", "")) == number
            # Amount-first labels are accepted only in a short single-amount quote.
            return len(matching) == 1 and len(q) <= 90
        return False
    return True


def canonical_url(value: object) -> str:
    try:
        u = urlsplit(str(value or ""))
        if u.scheme != "https" or not u.hostname or u.username or u.password or u.port not in (None, 443):
            return ""
        return urlunsplit(("https", u.hostname.lower().removeprefix("www."), u.path.rstrip("/") or "/", u.query, ""))
    except ValueError:
        return ""


def _official_url(url: str, domains: object) -> bool:
    host = urlsplit(url).hostname if url else None
    if not host or not isinstance(domains, (list, tuple)):
        return False
    for domain in domains:
        raw = str(domain or "").lower().strip().removeprefix("https://").removeprefix("http://").split("/")[0].removeprefix("www.")
        if "." in raw and (host == raw or host.endswith("." + raw)):
            return True
    return False


def payload_digest(record: Mapping, payload: Mapping) -> str:
    facts = {k: v for k, v in payload.items() if k != RECEIPT_KEY}
    data = {"identity": {k: record.get(k) for k in IDENTITY_FIELDS}, "payload": facts}
    try:
        return sha256(json.dumps(data, sort_keys=True, ensure_ascii=True, allow_nan=False, separators=(",", ":")).encode()).hexdigest()
    except (TypeError, ValueError):
        return ""


def acceptance_receipt_valid(record: Mapping, payload: Mapping | None = None) -> bool:
    p = payload if payload is not None else record.get("candidate_payload", {})
    receipt = p.get(RECEIPT_KEY, {}) if isinstance(p, Mapping) else {}
    if not isinstance(receipt, Mapping) or receipt.get("version") not in _COMPATIBLE_RECEIPT_VERSIONS:
        return False
    quality = comparison_quality(product_type=record.get("product_type"), country_code=record.get("country_code"), expected_fields=list(p), candidate_payload=p)
    if not quality.complete:
        return False
    digest = payload_digest(record, p)
    return bool(digest and receipt.get("accepted") is True and receipt.get("digest") == digest
                and all(value_matches_contract(k, v) for k, v in p.items() if k != RECEIPT_KEY))



def country_currency_fallback(record: Mapping, evidence: list[dict]) -> str | None:
    """Resolve undisclosed currency without discarding conflicting source context."""
    currency = default_currency_for_country(record.get("country_code"))
    if not currency:
        return None
    context = " ".join([str(record.get("product_name") or ""),
                        *(str(e.get("evidence_excerpt") or "") for e in evidence)])
    if any(re.search(pattern, context, re.I) for pattern in CURRENCY_PATTERNS.values()):
        return None
    declared = str(record.get("currency") or "")
    if re.fullmatch(r"[A-Z]{3}", declared) and declared != "XXX" and re.search(r"\b" + re.escape(declared) + r"\b", context):
        return None
    if re.search(r"\b(?:currency|denomination)\s*[:=]\s*[A-Z]{3}\b", context):
        return None
    if re.search(r"foreign[- ]currency|multi[- ]currency|other currenc|denominated in", context, re.I):
        return None
    return currency


def sanitize_candidate(record: dict, *, source_metadata: Mapping, evidence: list[dict]) -> tuple[dict, dict]:
    """Omit unproven fields and attach a content-bound acceptance result.

    Evidence must come from current-run extraction or DB joins, never model text.
    The returned exclusions contain field names/reasons only, not rejected values.
    """
    result = dict(record)
    payload = dict(record.get("candidate_payload") or {})
    mappings = dict(record.get("field_mapping_metadata") or {})
    fallback = country_currency_fallback(record, evidence)
    if fallback:
        result["currency"] = fallback
        mappings["currency"] = {"normalized_value": fallback,
            "extraction_method": "country_default", "country_code": record.get("country_code"),
            "policy_version": ACCURACY_VERSION}
        result["field_mapping_metadata"] = mappings
    record = result
    chunks = {str(e.get("evidence_chunk_id")): e for e in evidence}
    omitted = {}
    verified = []
    for name, value in list(payload.items()):
        if name == RECEIPT_KEY:
            payload.pop(name)
            continue
        if name in CONTEXT_FIELDS:
            continue
        if value is None or value == "" or value == [] or value == {}:
            payload.pop(name)
            continue
        m = mappings.get(name, {})
        e = chunks.get(str(m.get("evidence_chunk_id")), {})
        quote = m.get("official_evidence_quote")
        origin = canonical_url(e.get("source_url"))
        sources = m.get("official_web_sources") or []
        reason = None
        if not field_contract(name) or not value_matches_contract(name, value):
            reason = "invalid_or_undefined_field_type"
        elif m.get("normalized_value") != value:
            reason = "value_changed_after_grounding"
        elif m.get("official_grounding_contract_version") != "collection-official-grounding-v2" or m.get("official_verification_status") not in ("match", "mismatch"):
            reason = "official_grounding_missing"
        elif not _official_url(origin, source_metadata.get("official_domain_allowlist")) or not any(isinstance(s, dict) and canonical_url(s.get("url")) == origin for s in sources):
            reason = "evidence_source_mismatch"
        elif not exact_quote(quote, e.get("evidence_excerpt")):
            reason = "exact_evidence_missing"
        elif field_contract(name).unit in {"currency_amount", "percentage_points", "structured_rows"} and (
            any(code != record.get("currency") and re.search(pattern, str(e.get("evidence_excerpt") or ""), re.I)
                for code, pattern in CURRENCY_PATTERNS.items())
            or ("€" in str(quote) and record.get("currency") != "EUR")
            or ("£" in str(quote) and record.get("currency") != "GBP")
        ):
            reason = "field_currency_mismatch"
        elif (field_contract(name).unit == "percentage_points" or name == "term_rate_table") and not _ANNUAL_RATE_BASIS.search(str(e.get("evidence_excerpt") or "")):
            reason = "annual_rate_basis_unproven"
        elif name == "minimum_balance" and re.search(
            r"balance.{0,40}(?:no|waiv\w*|avoid|free).{0,25}transaction|"
            r"transaction.{0,25}(?:fee|charge).{0,25}(?:waiv\w*|avoid|free)",
            text(quote) + " " + text(e.get("evidence_excerpt")), re.I,
        ):
            # A balance that waives transaction charges is not an opening or
            # general minimum balance, nor a monthly-account-fee threshold.
            reason = "transaction_waiver_balance_not_minimum"
        elif not quote_supports_value(name, value, str(quote)):
            reason = "field_meaning_unproven"
        elif field_contract(name).value_type in {"decimal", "integer", "boolean"} and not quote_supports_value(name, value, str(e.get("evidence_excerpt") or "")):
            # Check the retained context too: a model may quote only the number
            # and omit an adjacent tier, condition, negation or conflicting rate.
            reason = "evidence_context_ambiguous"
        if reason:
            payload.pop(name)
            omitted[name] = reason
        else:
            verified.append(name)
    # Derived display aliases may only copy an accepted field of the same meaning.
    if "monthly_fee" in verified:
        payload["public_display_fee"] = payload["monthly_fee"]
        verified.append("public_display_fee")
    identity_verified = "product_name" in verified and payload.get("product_name") == record.get("product_name")
    reasons = []
    from worker.product_source_policy import non_product_identity_reason
    identity_metadata = source_metadata.get("discovery_metadata") or {}
    identity_reason = non_product_identity_reason(
        product_type=str(record.get("product_type") or ""),
        primary_heading=str(identity_metadata.get("primary_heading") or "") if isinstance(identity_metadata, Mapping) else "",
        page_title=str(record.get("product_name") or ""),
    )
    if identity_reason:
        reasons.append(identity_reason)
    if not identity_verified:
        reasons.append("product_identity_unverified")
    if source_metadata.get("discovery_role") != "detail":
        reasons.append("source_is_not_product_detail")
    # Explicit official evidence takes precedence over a traced country default.
    currency = str(record.get("currency") or "")
    currency_verified = any(
        quote_supports_value("currency", currency, str(mappings.get(name, {}).get("official_evidence_quote") or ""))
        for name in verified
    )
    currency_mapping = mappings.get("currency", {})
    currency_evidence = chunks.get(str(currency_mapping.get("evidence_chunk_id")), {})
    currency_origin = canonical_url(currency_evidence.get("source_url"))
    if (currency_mapping.get("official_grounding_contract_version") == "collection-official-grounding-v2"
        and currency_mapping.get("official_verification_status") in ("match", "mismatch")
        and currency_mapping.get("normalized_value") == currency
        and _official_url(currency_origin, source_metadata.get("official_domain_allowlist"))
        and any(isinstance(source, dict) and canonical_url(source.get("url")) == currency_origin for source in currency_mapping.get("official_web_sources", []))
        and exact_quote(currency_mapping.get("official_evidence_quote"), currency_evidence.get("evidence_excerpt"))
        and quote_supports_value("currency", currency, str(currency_mapping.get("official_evidence_quote") or ""))):
        currency_verified = True
    currency_verified = currency_verified or bool(fallback)
    if not currency_verified:
        reasons.append("product_currency_unverified")
    else:
        verified.append("currency")
    quality = comparison_quality(product_type=record.get("product_type"), country_code=record.get("country_code"), expected_fields=source_metadata.get("expected_fields", []), candidate_payload=payload)
    if not quality.applicable or not quality.contract_defined or not quality.complete:
        reasons.append("essential_fields_missing")
    receipt = {"version": ACCURACY_VERSION, "accepted": not reasons, "verified_fields": sorted(set(verified)), "omitted_fields": omitted, "reasons": reasons, "missing_fields": list(quality.missing_fields)}
    receipt["currency_basis"] = "country_default" if fallback else "official_evidence" if currency_verified else "unverified"
    receipt["digest"] = payload_digest(record, payload)
    payload[RECEIPT_KEY] = receipt
    result["candidate_payload"] = payload
    return result, receipt
