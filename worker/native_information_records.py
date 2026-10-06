"""Literal, bounded financial records from native information boxes and grids."""
from __future__ import annotations
import re
from decimal import Decimal
from bs4 import BeautifulSoup, Tag

TERM = re.compile(r'^\d+\s*[- ]?\s*(?:months?|years?)\s+(?:open|closed)(?:\s*\([^\n]+\))?$', re.I)
RATE = re.compile(r'^\d+(?:\.\d+)?%$')


def name_key(value):
    return ' '.join(re.findall(r'[a-z0-9]+', str(value).casefold().replace('\u00ad', '')))


def names_match(left, right):
    def key(value):
        return tuple(t for t in name_key(value).split() if t not in {'card', 'cards', 'r', 'tm'})
    return bool(key(left)) and key(left) == key(right)


def _note(soup, target_id):
    targets = soup.find_all(id=target_id)
    if len(targets) != 1:
        return None
    target = targets[0]
    if target.find_parent('table') is not None:
        return None
    # A numeric return anchor owns the following prose only until the next
    # explicit note anchor. Copy literal strings; do not import sibling notes.
    if len(target.get_text(' ', strip=True)) <= 4:
        container = target.find_parent(['p', 'li'])
        if container is None:
            return None
        parts, started = [], False
        for node in container.descendants:
            if node is target:
                started = True
            elif started and isinstance(node, Tag) and node.get('id') and node.get('id') != target_id:
                break
            if started and isinstance(node, str) and node.strip():
                parts.append(node.strip())
        value = ' '.join(parts)
    else:
        value = target.get_text('\n', strip=True)
    return value if len(value) > 15 and len(value) <= 3000 else None


def record_notes(soup, scope):
    notes = []
    for link in scope.select('a[href^="#"]'):
        href = link.get('href', '')
        if href == '#' and link.get('data-toggle') == 'popover' and link.get('data-content'):
            note = BeautifulSoup(link['data-content'], 'html.parser').get_text(' ', strip=True)
        else:
            note = _note(soup, href[1:]) if len(href) > 1 else None
        if not note:
            return None
        if note not in notes:
            notes.append(note)
    return notes


def mortgage_terms(quote):
    lines = [line.strip() for line in str(quote).splitlines() if line.strip()]
    return [lines[i] for i in range(len(lines)-1) if TERM.fullmatch(lines[i]) and RATE.fullmatch(lines[i+1])]


def html_information_records(soup):
    result = []
    for table in soup.find_all('table')[:64]:
        rows = table.find_all('tr')
        if not rows:
            continue
        heads = rows[0].find_all(['th', 'td'], recursive=False)
        if len(heads) != 2:
            continue
        owner = heads[0].get_text(' ', strip=True)
        # An exact product-name header plus inner Fixed/Variable term/APR
        # subheaders binds the loan rows. Reference/positive-balance rows are
        # outside these subgroups and cannot become borrowing facts.
        if heads[1].get_text(' ', strip=True).casefold() == 'rate':
            records, mode, invalid = [], None, False
            for row in rows[1:]:
                cells = row.find_all(['td', 'th'], recursive=False)
                if len(cells) != 2:
                    invalid = True; break
                label = cells[0].get_text(' ', strip=True)
                value = cells[1].get_text(' ', strip=True)
                if re.match(r'^(?:Fixed|Variable)[- ]rate (?:sub-account )?terms\b', label, re.I):
                    if not re.search(r'\bAPR\s*\(\s*%\s*\)', value, re.I):
                        invalid = True; break
                    notes = record_notes(soup, row)
                    if notes is None:
                        invalid = True; break
                    mode = [label, value, *notes]
                    records.extend(mode)
                elif TERM.fullmatch(label):
                    if mode is None or not RATE.fullmatch(value):
                        invalid = True; break
                    notes = record_notes(soup, row)
                    if notes is None:
                        invalid = True; break
                    records.extend([label, value, *notes])
                else:
                    mode = None
            quote = '\n'.join([owner, *records])
            terms = mortgage_terms(quote)
            if not invalid and terms and len(terms) == len(set(terms)) and len(quote) <= 6400:
                result.append(('named_mortgage_rate_schedule', owner, quote))
                # Literal term cells are a separate bounded field record. The
                # complete rate schedule above retains all APR conditions.
                result.append(('named_mortgage_term_schedule', owner, '\n'.join(terms)))
        if name_key(owner) == 'credit limit' and name_key(heads[1].get_text()) in {'interest', 'interest rate', 'annual interest rate'}:
            scope = table.find_parent('section') or table
            notes = record_notes(soup, scope)
            # Some tables refer to their annual-unit note in the adjacent owned
            # headline rate. Only an explicit link in the same rate component
            # establishes that relation, never a document-wide annual assertion.
            if notes == []:
                parent = scope.parent
                for _ in range(3):
                    if parent is None or len(parent.find_all('table')) != 1:
                        break
                    candidates = record_notes(soup, parent)
                    if candidates:
                        notes = candidates; break
                    parent = parent.parent
            if not notes and len(soup.find_all('h1')) == 1:
                for link in soup.select('a[href^="#"]'):
                    for block in list(link.parents)[:4]:
                        label = block.get_text(' ', strip=True)
                        if len(label) > 350:
                            break
                        if re.search(r'\bline of credit rate\b', label, re.I) and re.search(r'\d+(?:\.\d+)?\s*%',label):
                            candidates = record_notes(soup, block)
                            if candidates and any(re.search(r'all rates are annual rates',n,re.I) for n in candidates):
                                notes = candidates
                            break
                    if notes:
                        break
            grid = table.get_text('\n', strip=True)
            quote = '\n'.join([grid, *(notes or [])])
            if notes is not None and re.search(r'all rates are annual rates|annual interest rate', quote, re.I) and re.search(r'\d+(?:\.\d+)?%', grid) and len(quote) <= 6400:
                result.append(('credit_limit_rate_schedule', owner, quote))
    return result


def pdf_information_records(page_text, *, page_no):
    lines = str(page_text).splitlines()
    names = [line.strip() for line in lines if re.fullmatch(r'.+?\bCard Information Box', line.strip(), re.I)]
    if len(names) != 1:
        return []
    owner = re.sub(r'\s+Information Box$', '', names[0], flags=re.I)
    start = re.search(r'(?mi)^Annual Interest\s*\nRates\s*\n', page_text)
    end = re.search(r'(?mi)^Interest-free\s*\nGrace Period\b', page_text)
    output = []
    if start and end and start.end() < end.start():
        quote = '\n'.join([owner, page_text[start.start():end.start()].strip()])
        if information_card_rates(quote) and len(quote) <= 6400:
            output.append(('card_information_rate', owner, quote))
    fee = re.search(r'(?mi)^Annual Fees\s+\$[^\n]+(?:\n(?!\d+\s*$|Installment Fee\b|Other Fees\b)[^\n]+)*', page_text)
    if fee and len(fee[0]) <= 1500:
        output.append(('card_information_fee', owner, '\n'.join([owner, fee[0]])))
    return output


def information_card_rates(quote):
    """Explicit ordinary labelled AIRs; preserve a separate complete default rule."""
    match = re.search(r'Annual Interest\s+Rates\s+These interest rates are in effect the day your account is opened \(whether or not your card is activated\)\.\s+Purchases, fees,? and other charges:\s*(\d+(?:\.\d+)?)%\s+Cash Advances and Balance Transfers:\s*(\d+(?:\.\d+)?)%', str(quote), re.I)
    if not match or len(re.findall(r'Purchases, fees,? and other charges:\s*\d',str(quote),re.I)) != 1:
        return None
    tail = str(quote)[match.end():].strip()
    if tail:
        if not re.fullmatch(r'If you do not make your minimum payment by the payment due date \d+ or more times in any \d+-month period,\s+your annual interest rates will increase to standard rates of \d+(?:\.\d+)?% on Purchases, fees,? and other charges\s+and \d+(?:\.\d+)?% for Cash Advances and Balance Transfers, including those done under any previous rate\.\s+This increase will take effect in the third statement period following the missed payment that caused the rate\s+to\s+increase\. The increased rates will remain in effect until you make your minimum payments by the due date for\s+\d+ consecutive months\.', tail, re.I):
            return None
    values = tuple(Decimal(v) for v in match.groups())
    return values if all(v.is_finite() and 0 <= v < 100 for v in values) else None
