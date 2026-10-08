"""Named percent-header rate rows with explicit annual notes, never invented units."""
import re
from decimal import Decimal
from worker.native_dom_ownership import local_notes, without_reference_markers

CARD_HEADERS = ["Credit Cards", "Purchases Interest Rate [%]", "Cash Advances / Cheques Interest Rate [%]"]
NUMBER = re.compile(r"^\d+(?:\.\d+)?$")
ANNUAL = re.compile(r"per annum|(?:annual (?:interest )?rate|interest rate is an annual interest rate)", re.I)
DEFAULT = re.compile(r"Your interest rate will increase by \d+(?:\.\d+)?% on purchases and cash advances for at least \d+ months if you do not make your minimum payment by the payment due date and you have not paid it by the date we prepare your next statement \d+ or more times in any \d+-month period\. This will take effect in the third statement period following the missed payment that caused the rate to increase\. \(This does not apply to Commercial Cards\.\)", re.I)


def _lines(value):
    return [" ".join(x.split()) for x in str(value).splitlines() if x.strip()]


def _annual(notes):
    return bool(ANNUAL.search(notes)) and not re.search(r"not (?:an? )?annual|not (?:quoted )?per annum", notes, re.I)


def _marker_notes(block, scope):
    notes = []
    for marker in block.find_all("sup"):
        value = marker.get_text(" ", strip=True)
        if marker.find("a") is not None or not re.fullmatch(r"\*{1,6}", value):
            continue
        matching = [n.get_text(" ", strip=True) for n in scope.find_all("li", recursive=False)
                    if re.match(re.escape(value) + r"(?!\*)\s", n.get_text(" ", strip=True))]
        if len(matching) != 1:
            return None
        notes.extend(matching)
    return notes


def card_rate_values(quote):
    lines = _lines(quote)
    if len(lines) < 8 or lines[1:4] != CARD_HEADERS or not all(NUMBER.fullmatch(x) for x in lines[4:6]) or lines[6] != "NOTES":
        return None
    notes = " ".join(lines[7:])
    if not _annual(notes):
        return None
    # Only a complete separately declared payment-default change may accompany
    # an ordinary scalar. Unknown qualifications/extra percentages fail closed.
    if len(list(DEFAULT.finditer(notes))) > 1:
        return None
    ordinary_notes = DEFAULT.sub("", notes)
    if re.search(r"%|\b(?:if|when|provided|eligible|qualif\w*|first|introductory|promotional|minimum balance|up to)\b", ordinary_notes, re.I):
        return None
    values = tuple(Decimal(x) for x in lines[4:6])
    return values if all(0 <= x < 100 for x in values) else None


def balance_rate_value(quote):
    lines = _lines(quote)
    if len(lines) > 3 and lines[1] == lines[0]:
        lines = lines[1:]
    if len(lines) >= 4 and lines[1] == "Annual rate" and re.fullmatch(r"\d+(?:\.\d+)?%", lines[2]):
        notes = " ".join(lines[3:])
        if (not re.search(r"savings account", lines[0], re.I) or re.search(r"linked|package|not offered|no longer|discontinued|promotional|eligible|qualif\w*", lines[0], re.I) or not re.fullmatch(
                r"Interest is calculated on the daily closing balance and is paid into your account monthly[.] Rates subject to change[.]", notes, re.I)):
            return None
        value = Decimal(lines[2][:-1])
        return value if 0 <= value < 100 else None
    if len(lines) < 7 or lines[1:5] != ["If Balance is", "Interest Rate [%]", "All balances", lines[4]] or not NUMBER.fullmatch(lines[4]) or lines[5] != "NOTES":
        return None
    if re.search(r"linked|package|not offered|no longer|not payable|promotional|eligible|qualif\w*", lines[0], re.I):
        return None
    notes = " ".join(lines[6:])
    if not _annual(notes) or re.search(r"%|\b(?:if|when|provided|eligible|qualif\w*|first|introductory|promotional|bonus|tier|up to|minimum balance)\b", notes, re.I):
        return None
    value = Decimal(lines[4])
    return value if 0 <= value < 100 else None


def named_rate_records(soup):
    root = soup.find("main") or soup.body or soup
    note_heads = [n for n in root.find_all(["p", "h2", "h3", "h4"]) if n.get_text(" ", strip=True).casefold() == "notes"]
    if len(note_heads) != 1:
        return compact_annual_balance_records(soup)
    head = note_heads[0]
    scope = head.find_next_sibling("ul")
    if scope is None:
        return []
    global_notes = [li.get_text(" ", strip=True) for li in scope.find_all("li", recursive=False) if not li.get("id") and not li.find("sup")]
    if not global_notes or sum(map(len, global_notes)) > 6000:
        return []
    card_notes = [n for n in global_notes if not re.match(r"Our Prime Rate\b|(?:Registered )?trademark", n, re.I)]
    deposit_notes = [n for n in global_notes if not re.match(r"Foreign Currency Accounts:", n, re.I)]
    output = compact_annual_balance_records(soup)
    for table in root.find_all("table")[:64]:
        if table.find("table") or table.select("[rowspan]"):
            continue
        rows = table.find_all("tr")
        if not rows:
            continue
        headers = [" ".join(c.get_text(" ", strip=True).split()) for c in rows[0].find_all(["th", "td"], recursive=False)]
        if headers == CARD_HEADERS:
            for row in rows[1:]:
                cells = row.find_all(["th", "td"], recursive=False)
                if len(cells) != 3 or any(c.get("colspan") for c in cells):
                    continue
                owner = " ".join(without_reference_markers(cells[0]).split())
                values = [c.get_text(" ", strip=True) for c in cells[1:]]
                if not all(NUMBER.fullmatch(x) for x in values):
                    continue
                notes = local_notes(soup, row)
                markers = _marker_notes(row, scope)
                if notes is None or markers is None:
                    continue
                notes = list(dict.fromkeys([*notes, *markers]))
                if notes is None or any(re.search(r"no longer offered|not offered", n, re.I) for n in notes):
                    continue
                quote = "\n".join([owner, *headers, *values, "NOTES", *card_notes, *notes, *[a["href"] for a in cells[0].select("a[href]") if not a["href"].startswith("#")]])
                if len(quote) <= 6400 and card_rate_values(quote) is not None:
                    output.append(("named_card_rate_table", owner, quote))
        elif headers == ["If Balance is", "Interest Rate [%]"] and len(rows) == 2:
            cells = rows[1].find_all(["th", "td"], recursive=False)
            if len(cells) != 2 or cells[0].get_text(" ", strip=True) != "All balances":
                continue
            heading = table.parent.find_previous_sibling("p")
            if heading is None or not heading.find("a", href=True):
                continue
            if heading.find_next_sibling() is not table.parent:
                continue
            if re.search(r"not offered|no longer|discontinued", table.find_previous(["h2", "h3", "h4"]).get_text(" ", strip=True) if table.find_previous(["h2", "h3", "h4"]) else "", re.I):
                continue
            if heading is None or len(heading.get_text()) > 200:
                continue
            owner = " ".join(without_reference_markers(heading).split())
            notes = local_notes(soup, table)
            owner_notes = local_notes(soup, heading)
            if owner_notes is None:
                continue
            if notes is not None:
                notes = list(dict.fromkeys([*notes, *owner_notes]))
            quote = "\n".join([owner, *headers, *[c.get_text(" ", strip=True) for c in cells], "NOTES", *deposit_notes, *(notes or []), *[a["href"] for a in heading.select("a[href]") if not a["href"].startswith("#")]])
            if notes is not None and len(quote) <= 6400 and balance_rate_value(quote) is not None:
                output.append(("named_balance_rate", owner, quote))
    return list(dict.fromkeys(output))


def compact_annual_balance_records(soup):
    """An owned one-row annual table and complete local disclosure, unchanged."""
    from worker.native_dom_ownership import unique_heading, owns_label
    root = soup.find("main") or soup.body or soup
    heading = unique_heading(root)
    if heading is None:
        return []
    parts = _lines(heading.get_text("\n", strip=True))
    if len(parts) > 1 and parts[0] == "Accounts":
        parts = parts[1:]
    owner = " ".join(parts)
    if not re.search(r"savings account", owner, re.I):
        return []
    output = []
    for table in root.find_all("table")[:64]:
        if table.find("table") or table.select("[rowspan], [colspan]") or not owns_label(table, root, owner):
            continue
        rows = table.find_all("tr")
        if len(rows) != 1:
            continue
        cells = rows[0].find_all(["th", "td"], recursive=False)
        if len(cells) != 2:
            continue
        values = [" ".join(c.get_text(" ", strip=True).split()) for c in cells]
        if values[0] != "Annual rate" or not re.fullmatch(r"\d+(?:\.\d+)?%", values[1]):
            continue
        previous = table.find_previous(["h1", "h2", "h3", "h4", "h5", "h6"])
        if previous is not None and previous.name != "h1" and re.search(r"account|card|loan|GIC|certificate", previous.get_text(), re.I):
            continue
        for scope in list(table.parents)[:8]:
            if scope is root or len(scope.get_text()) > 1500 or len(scope.find_all("table")) != 1:
                break
            notes = [" ".join(p.get_text(" ", strip=True).split()) for p in scope.find_all("p")]
            if not notes:
                continue
            references = local_notes(soup, scope)
            if references is None or not owns_label(scope, root, owner):
                break
            quote = "\n".join([owner, *values, *notes, *references])
            if balance_rate_value(quote) is not None:
                output.append(("named_balance_rate", owner, quote))
            break
    return list(dict.fromkeys(output))
