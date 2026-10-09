"""Literal account cost/denomination assertions with complete local notes."""
import re
from worker.native_dom_ownership import unique_heading, owns_label, local_notes, without_reference_markers


def _account_notes(soup, block):
    notes = local_notes(soup, block)
    if notes is None:
        return None
    from worker.native_offer_records import symbol_note
    for marker in block.find_all("sup"):
        if marker.find("a") is not None:
            continue
        parent_ref = marker.find_parent("a")
        if parent_ref is not None and (parent_ref.get("data-scroll-target") or str(parent_ref.get("href", "")).startswith("#") or parent_ref.get("aria-describedby")):
            continue
        symbol = marker.get_text("", strip=True)
        if not re.fullmatch(r"[0-9]+|[\u2020\u2021*]", symbol):
            continue
        note = symbol_note(soup, symbol, block)
        if note is None:
            return None
        notes.append(note)
    return list(dict.fromkeys(notes))


def account_records(soup):
    root = soup.find("main") or soup.body or soup
    heading = unique_heading(root)
    if heading is None:
        return []
    owner = heading.get_text(" ", strip=True)
    output = []
    for node in root.find_all(["p", "li", "h2", "h3", "h4", "h5", "h6"])[:2048]:
        if node.find_parent(["nav", "aside", "footer", "table"]) or node.find(["p", "li"]):
            continue
        if not owns_label(node, root, owner):
            continue
        value = node.get_text(" ", strip=True)
        if not re.search(r"no monthly (?:(?:account|maintenance) )?fee|monthly (?:(?:account|maintenance) )?fee\s*:\s*\$|\b(?:unlimited|\d+)\s+(?:number of )?(?:daily |debit )?(?:transactions|purchases)|(?:U\.?S\.?|Canadian) dollars?|\b(?:CAD|USD|EUR|GBP)\b", value, re.I):
            continue
        if re.search(r"exchange rate|currency conversion|benchmark rate|reference rate", value, re.I):
            continue
        if len(value) > 700 or re.search(r"\b(?:looking for|consider|might|could|would you|try our|for example)\b", value, re.I):
            continue
        previous = node.find_previous(["h1", "h2", "h3", "h4", "h5", "h6"])
        scope = previous.get_text(" ", strip=True) if previous else ""
        if previous is not None and previous.name != "h1":
            if re.match(re.escape(owner.split()[0]) + r"\b", scope, re.I) and not scope.casefold() == owner.casefold():
                continue
            if re.search(r"ideal|if:|not be ideal|consider|you want", scope, re.I):
                continue
        disclosure = node
        if node.name.startswith("h") and re.search(r"\bunlimited\b", value, re.I):
            for scope_node in list(node.parents)[:4]:
                if scope_node is root or len(scope_node.get_text()) > 1400:
                    break
                if len(scope_node.find_all(["h1", "h2", "h3", "h4", "h5", "h6"])) != 1:
                    break
                if scope_node.find(["p", "li"]) is not None:
                    disclosure = scope_node
                    break
            if not owns_label(disclosure, root, owner):
                continue
        notes = _account_notes(soup, disclosure)
        if notes is None:
            continue
        section = node.find_parent("section")
        shared_scope = previous is not None and (node.parent is previous.parent or
            (section is not None and section is not root and previous.find_parent("section") is section))
        # A separately labelled cash reward has its own prerequisites. It
        # cannot qualify the following independently stated regular fee.
        bonus_scope = bool(re.match(r"Earn \$[\d,]+\b", scope, re.I) and not
            re.search(r"monthly|fees?|charges?|waiv\w*|discount", scope, re.I))
        if shared_scope and not bonus_scope and re.search(r"\b(?:first|eligible|if|when|waiv\w*|only|provided|maintain|qualif\w*)\b", scope, re.I):
            notes.append(scope)
        quote = "\n".join([owner, without_reference_markers(disclosure), *notes])
        if len(quote) <= 6400:
            output.append(("owned_account_assertion", owner, quote))
    for row in root.select('tr, [role="row"], .table-row')[:1024]:
        cells = row.find_all(["th", "td"], recursive=False) or row.find_all(attrs={"role": "cell"}, recursive=False) or row.find_all(class_="table-cell", recursive=False)
        if len(cells) != 2 or not owns_label(row, root, owner):
            continue
        label, value = [" ".join(without_reference_markers(c).split()) for c in cells]
        if not re.fullmatch(r"Monthly (?:(?:account|maintenance) )?fees?|Debits Exceeding Monthly Limit|Additional (?:debit )?transactions", label, re.I) or not re.fullmatch(r"\$\d+(?:\.\d+)?(?: each)?", value):
            continue
        previous = row.find_previous(["h1", "h2", "h3", "h4", "h5", "h6"])
        scope = previous.get_text(" ", strip=True) if previous else ""
        if previous is not None and previous.name != "h1" and re.search(r"\b(?:account|card|loan|mortgage|GIC|certificate)\b", scope, re.I) and re.search(r"\b(?:savings|checking|chequing|spending|premium|plus)\b", scope, re.I) and scope.casefold() != owner.casefold():
            continue
        notes = _account_notes(soup, row)
        if notes is None:
            continue
        table = row.find_parent("table")
        if table is not None:
            for header in table.find_all(["caption", "thead"]):
                refs = _account_notes(soup, header)
                if refs is None:
                    notes = None
                    break
                notes.extend(refs)
                if header.name == "caption":
                    notes.append(header.get_text(" ", strip=True))
            # A complete table-wide condition cannot disappear merely because
            # the price is in a row. Unrelated row references stay with that row.
            for sibling in table.next_siblings:
                if not getattr(sibling, "name", None):
                    continue
                if sibling.name != "p" or len(sibling.get_text()) > 1000:
                    break
                literal = sibling.get_text(" ", strip=True)
                if re.search(r"monthly|maintenance|fee|waiv|qualif|eligible|first", literal, re.I):
                    notes.append(literal)
        if notes is not None:
            if re.search(r"\b(?:first|eligible|if|when|waiv|only|provided)\b", scope, re.I):
                notes.append(scope)
            output.append(("owned_account_assertion", owner, "\n".join([owner, label, value, *dict.fromkeys(notes)])))
    return list(dict.fromkeys(output))
