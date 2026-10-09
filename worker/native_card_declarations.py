"""Literal card price declarations, owned hero labels and complete local notes."""
import re
from worker.native_dom_ownership import unique_heading, owns_label, local_notes
from worker.native_owned_account_records import _account_notes


def card_owner(soup):
    root = soup.find("main") or soup.body or soup
    heading = unique_heading(root)
    if heading is None:
        return None
    literal = heading.get_text(" ", strip=True)
    if not re.match(r"(?:enjoy|earn|get|discover|open|a fee-free)\b", literal, re.I):
        return heading
    # An isolated literal hero label immediately before the marketing H1 is
    # independently corroborated by the captured SEO title. Never use a
    # recommendation, a hidden label or an unbounded component attribute.
    label = heading.find_previous_sibling()
    if label is None or label.find_parent(["nav", "aside", "footer"]):
        return None
    if not re.search(r"(?:^|[ _-])(?:eyebrow|tagbrow|product-name|account-name)(?:$|[ _-])", " ".join(label.get("class", [])), re.I):
        return None
    name = " ".join(label.get_text(" ", strip=True).split())
    core = re.split(r"\s+from\s+", name, flags=re.I)[0]
    title = soup.title.get_text(" ", strip=True) if soup.title else ""
    words = re.findall(r"[a-z0-9]+", core.casefold())
    title_words = re.findall(r"[a-z0-9]+", title.casefold())
    if (not 2 <= len(words) <= 10 or re.search(r"[$%]|\b(?:if|when|only|eligible|first|bonus)\b", name, re.I)
            or not set(words) <= set(title_words) or len(name) > 180
            or label.get("hidden") is not None or str(label.get("aria-hidden", "")).lower() == "true"):
        return None
    return label


def card_declarations(soup):
    root = soup.find("main") or soup.body or soup
    heading = card_owner(soup)
    if heading is None:
        return []
    owner = " ".join(heading.get_text(" ", strip=True).split())
    title = soup.title.get_text(" ", strip=True) if soup.title else ""
    output = []
    output.append(("owned_product_label", owner, owner))
    for node in root.find_all(["h2", "h3", "h4", "h5", "p"])[:2048]:
        text = " ".join(node.get_text(" ", strip=True).split())
        fee = re.fullmatch(r"(?:No|\$\d+(?:\.\d+)?) annual fee", text, re.I)
        apr_label = re.fullmatch(r"(?:Purchase rate|Purchase APR|Low intro APR)", text, re.I)
        if not (fee or apr_label) or node.find_parent(["aside", "nav", "form", "table", "footer"]):
            continue
        block = node.parent
        if (block is root or len(block.get_text()) > 1600
                or len(block.find_all(["h1", "h2", "h3", "h4", "h5"])) != 1
                or block.select('input:not([type="hidden"]), select, textarea, [role="slider"]')
                or not owns_label(block, root, owner)):
            continue
        notes = _account_notes(soup, block)
        if notes is None:
            continue
        literal = block.get_text("\n", strip=True)
        # Price conditions in the owned block and every uniquely referenced
        # note stay intact. References are not interpreted as source code.
        quote = "\n".join([owner, literal, *notes])
        if len(quote) > 6400:
            continue
        if fee:
            output.append(("labelled_financial_record", owner, quote))
        if ((apr_label and re.search(r"\d+(?:\.\d+)?%.*\bAPR\b", literal, re.I | re.S))
                or any(re.search(r"Purchase APR\s*:\s*\d+(?:\.\d+)?%", note, re.I) for note in notes)):
            output.append(("owned_card_apr_offer", owner, quote))
    output.extend(named_pricing_disclosures(soup, root, owner))
    return list(dict.fromkeys(output))


def declaration_fee_value(quote):
    """A literal fee heading, with independently labelled shared card prices."""
    from decimal import Decimal
    from worker.pipeline.fpds_collection_accuracy import _money_has_condition
    pricing_fee = pricing_disclosure_fee(quote)
    if pricing_fee is not None:
        return pricing_fee
    lines = [line.strip() for line in str(quote).splitlines() if line.strip()]
    if len(lines) < 2:
        return None
    heading = re.fullmatch(r"(?:No|\$(\d+(?:\.\d+)?)) annual fee", lines[1], re.I)
    if not heading:
        return None
    value = Decimal(heading[1] or "0")
    # Conflicting restated fees or an explicit explanatory amount cannot be
    # hidden by the first zero-fee heading.
    restated = re.findall(r"Annual Fee\s*:\s*\$(\d+(?:\.\d+)?)|\$(\d+(?:\.\d+)?) annual fee", " ".join(lines[1:]), re.I)
    if any(Decimal(a or b) != value for a, b in restated):
        return None
    for line in lines[2:]:
        amount = re.fullmatch(r"That(?:['\u2019]s| is) \$(\d+(?:\.\d+)?)[.]?", line, re.I)
        if amount and Decimal(amount[1]) != value:
            return None
    if value and re.search(r"\bNo annual fee\b", " ".join(lines[1:]), re.I):
        return None
    context = "\n".join(lines[1:])
    # A complete semicolon-labelled card disclosure keeps APR/transfer fees
    # separate from its annual price. Unknown or added fee conditions remain
    # blocking. Keep the entire original note in field evidence and summary.
    rate = r"\d+(?:\.\d+)?% variable APR"
    shared = (r"[^\n:]{1,180}: Purchase APR: " + rate
        + r"; Balance Transfer APR: " + rate + r"; Cash Advance APR: " + rate
        + r"[.] Cash Advance Fee: Either \$\d+(?:\.\d+)? or \d+(?:\.\d+)?% of the amount of each cash advance, whichever is greater; "
        + r"Annual Fee: \$(\d+(?:\.\d+)?); Balance Transfer Fee: "
        + r"\d+(?:\.\d+)?% transfer fee on the amount of each transfer balance that posts to your account at a Promotional APR that we may offer you[.]{1,2} "
        + r"Subject to credit approval; based on your creditworthiness, some options may not be available and other terms may apply[.]")
    for line in lines[2:]:
        match = re.fullmatch(shared, " ".join(line.split()), re.I)
        if match:
            if Decimal(match[1]) != value:
                return None
            context = context.replace(line, "Separate complete labelled card APR and transfer prices; Annual Fee: $" + match[1])
    return None if _money_has_condition(context, "annual_fee") else value


def pricing_disclosure_fee(quote):
    """Only a separately labelled unconditional annual price in a named record."""
    from decimal import Decimal
    from worker.native_information_records import names_match
    lines = [line.strip() for line in str(quote).splitlines() if line.strip()]
    if len(lines) < 3:
        return None
    heading = re.fullmatch(r"(?:\d+\s*)?(.+?) Pricing Details", lines[1], re.I)
    if not heading or not names_match(heading[1], lines[0]):
        return None
    context = " ".join(lines[2:])
    # The entire annual-price sentence must be literal. Other labelled APR,
    # transfer and cash-advance conditions are retained but cannot set this fee.
    fees = re.findall(r"Annual Fee\s*[:–—-]\s*(None|\$\s*\d+(?:\.\d+)?)(?=\s*[.;])", context, re.I)
    if not fees or len(re.findall(r"\bannual fee\b", context, re.I)) != len(fees):
        return None
    if re.search(r"\b(?:waiv\w*|first year|annual fee discount|annual fee reduction|only for|provided that|maintain a balance)\b", context, re.I):
        return None
    values = {Decimal("0" if f.lower() == "none" else f.replace("$", "").strip()) for f in fees}
    return next(iter(values)) if len(values) == 1 else None


def named_pricing_disclosures(soup, root, owner):
    from worker.native_information_records import names_match
    output = []
    for heading in root.find_all(["h2", "h3", "h4"])[:256]:
        title = " ".join(heading.get_text(" ", strip=True).split())
        name = re.fullmatch(r"(?:\d+\s*)?(.+?) Pricing Details", title, re.I)
        if not name or not names_match(name[1], owner):
            continue
        block = heading.parent
        if block is root or block.find_parent(["nav", "aside", "footer", "form", "table"]) or not owns_label(block, root, owner):
            continue
        if len(block.find_all(["h1", "h2", "h3", "h4"])) != 1:
            continue
        literal = " ".join(block.get_text(" ", strip=True).split())
        if len(literal) > 6000 or block.select('input:not([type="hidden"]), select, textarea, [role="slider"]'):
            continue
        # Empty pricing bindings cannot become a complete disclosure even if
        # another labelled percentage or price is already populated.
        if any(not span.get_text(strip=True) for span in block.select('span[data-id], span[data-field], span[data-bind]')):
            continue
        rate = r"\d+(?:\.\d+)?\s*%\s*(?:[-–]|to)\s*\d+(?:\.\d+)?\s*%"
        basis = r",? based on (?:your )?creditworthiness"
        purchase_clauses = (
            r"(?:The )?(?:standard )?variable APR for purchases(?:,? (?:and )?balance transfers)? is " + rate + basis + r"[.]",
            r"A variable APR of " + rate + basis + r", applies to purchases, balance transfers, and [^.]{1,100}[.]",
            r"variable APR for unpaid promotional balances, new purchases, and new balance transfers is " + rate + basis + r"[.]",
            r"a variable APR of " + rate + basis + r", applies to unpaid promotional balances, new purchases and new balance transfers[.]",
            r"Variable APR for purchases, balance transfers, and [^.]{1,100} APR: " + rate + r"(?: variable APR)?" + basis + r"[.]",
        )
        if not any(re.search(pattern, literal, re.I) for pattern in purchase_clauses) or not re.search(r"Subject to credit approval[.]", literal, re.I):
            continue
        notes = local_notes(soup, block)
        if notes is None:
            continue
        # Keep all paragraphs, including default triggers and new-cardmember
        # qualifications. Only the heading is separated for ownership checks.
        body = literal[len(title):].strip()
        quote = "\n".join([owner, title, body, *notes])
        if len(quote) > 6400:
            continue
        output.append(("owned_card_apr_offer", owner, quote))
        if pricing_disclosure_fee(quote) is not None:
            output.append(("labelled_financial_record", owner, quote))
    return output
