"""Literal account cost/denomination assertions with complete local notes."""
import re
from worker.native_dom_ownership import unique_heading, owns_label, local_notes, without_reference_markers


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
        if not re.search(r"no monthly (?:account )?fee|monthly (?:account )?fee\s*:\s*\$|\b(?:unlimited|\d+)\s+(?:number of )?(?:daily |debit )?(?:transactions|purchases)|(?:U\.?S\.?|Canadian) dollars?|\b(?:CAD|USD|EUR|GBP)\b", value, re.I):
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
        notes = local_notes(soup, disclosure)
        if notes is None:
            continue
        quote = "\n".join([owner, without_reference_markers(disclosure), *notes])
        if len(quote) <= 6400:
            output.append(("owned_account_assertion", owner, quote))
    for row in root.select('tr, [role="row"], .table-row')[:1024]:
        cells = row.find_all(["th", "td"], recursive=False) or row.find_all(attrs={"role": "cell"}, recursive=False) or row.find_all(class_="table-cell", recursive=False)
        if len(cells) != 2 or not owns_label(row, root, owner):
            continue
        label, value = [c.get_text(" ", strip=True) for c in cells]
        if not re.fullmatch(r"Debits Exceeding Monthly Limit|Additional (?:debit )?transactions", label, re.I) or not re.fullmatch(r"\$\d+(?:\.\d+)?(?: each)?", value):
            continue
        notes = local_notes(soup, row)
        if notes is not None:
            output.append(("owned_account_assertion", owner, "\n".join([owner, label, value, *notes])))
    return list(dict.fromkeys(output))
