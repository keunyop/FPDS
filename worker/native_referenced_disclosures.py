"""Owned literal rates with uniquely resolved typographic annual references."""
import re
from copy import deepcopy
from worker.native_dom_ownership import unique_heading, owns_label, local_notes


def typographic_notes(soup, block):
    notes = local_notes(soup, block)
    if notes is None:
        return None
    for marker in block.find_all(['sup', 'b']):
        if marker.find('a'):
            continue
        symbol = marker.get_text('', strip=True)
        if not re.fullmatch(r'[†‡*]+', symbol):
            continue
        matches = []
        for note in soup.find_all(['p', 'li']):
            first = next((s for s in note.stripped_strings), '')
            if first != symbol or note is block or block in note.parents:
                continue
            # The marker starts an actual note, not another rate's suffix.
            literal = note.get_text(' ', strip=True)
            if len(literal) > len(symbol) + 20 and len(literal) <= 6000:
                matches.append(literal)
        matches = list(dict.fromkeys(matches))
        if len(matches) != 1:
            return None
        notes.extend(matches)
    return list(dict.fromkeys(notes))


def _rate_heading_belongs(heading, owner):
    def key(value):
        value = re.sub(r'tax[- ]free(?: savings account)?', 'tfsa', value, flags=re.I)
        value = re.sub(r'guaranteed investments?', 'gic', value, flags=re.I)
        return set(re.findall(r'[a-z0-9]+', value.casefold())) - {'current', 'interest', 'rate', 'rates'}
    return bool(re.search(r'\brates?\b', heading, re.I)) and key(heading) <= key(owner)


def referenced_annual_records(soup):
    root = soup.find('main') or soup.body or soup
    head = unique_heading(root)
    if head is None:
        return []
    owner = head.get_text(' ', strip=True)
    if not re.search(r'savings account|\bGIC\b|guaranteed investment|certificate of deposit', owner, re.I):
        return []
    family = r'savings accounts?' if re.search(r'savings account', owner, re.I) else r'GICs?|guaranteed investments?|certificates? of deposit'
    output = []
    for node in root.find_all(['p', 'table']):
        if node.find_parent(['nav', 'aside', 'footer']) or not owns_label(node, root, owner):
            continue
        notes = typographic_notes(soup, node)
        if not notes or not any(re.search(r'interest rates?[^.!?]{0,130}\b(?:annual interest rates?|annualized)\b|per annum', n, re.I) for n in notes):
            continue
        if not any(re.search(r'(?:'+family+r')[^.!?]{0,150}interest rates?[^.!?]{0,130}(?:annual interest rates?|annualized)', n, re.I) for n in notes):
            continue
        if any(re.search(r'not (?:an? )?annual|not annualized', n, re.I) for n in notes):
            continue
        clone = deepcopy(node)
        for sup in clone.find_all(['sup', 'b']):
            if re.fullmatch(r'[†‡*]+', sup.get_text('', strip=True)):
                sup.decompose()
        if node.name == 'p':
            # Native two-label widget: percent and its literal interest label.
            parent = node.parent
            value = clone.get_text(' ', strip=True)
            if not re.fullmatch(r'\d+(?:\.\d+)?%', value):
                continue
            lines = list(parent.stripped_strings)
            if not any(x.casefold() == 'interest rate' for x in lines):
                continue
            if len(parent.get_text(' ', strip=True)) > 100:
                continue
            widget = deepcopy(parent)
            for sup in widget.find_all(['sup', 'b']):
                if re.fullmatch(r'[†‡*]+', sup.get_text('', strip=True)):sup.decompose()
            literal = widget.get_text('\n', strip=True)
            if len(re.findall(r'\d+(?:\.\d+)?%', literal)) != 1:continue
            record = '\n'.join([owner, literal, *notes])
            output.append(('linked_rate_record', owner, record))
            calculation = re.search(r'Interest is calculated daily and paid monthly on our Savings and Chequing Accounts[.]', '\n'.join(notes), re.I)
            if calculation and not re.search(r'\b(?:if|when|only|except|unless|provided|eligible|qualif\w*|bonus|promotional)\b', '\n'.join(notes), re.I):
                # Its explicitly named savings/chequing sentence is a separate
                # fact from the following GIC payment alternatives. Keep the
                # original complete sentence and real capture origin.
                output.append(('named_product_interest_terms', owner, owner+'\n'+calculation[0]))
        else:
            if node.find('table') or node.select('[rowspan], [colspan]'):continue
            rows = node.find_all('tr')
            headers = [c.get_text(' ', strip=True) for c in rows[0].find_all(['th','td'], recursive=False)] if rows else []
            if headers != ['Term', 'Rate']:continue
            previous = node.find_previous(['h1','h2','h3','h4'])
            if previous is None or (previous is not head and not _rate_heading_belongs(previous.get_text(' ',strip=True), owner)):
                continue
            # Preserve the whole local text container, not a selected cell.
            container = node.parent
            if len(container.get_text()) > 4000 or len(container.find_all('table')) != 1:continue
            literal = deepcopy(container)
            for sup in literal.find_all(['sup', 'b']):
                if re.fullmatch(r'[†‡*]+', sup.get_text('',strip=True)):sup.decompose()
            record = '\n'.join([owner,literal.get_text('\n',strip=True),*notes])
            from worker.native_rate_tables import rate_schedules
            if len(record)<=6400 and len(rate_schedules(record,annual_only=True))==1:
                output.append(('native_rate_table',owner,record))
    return list(dict.fromkeys(output))
