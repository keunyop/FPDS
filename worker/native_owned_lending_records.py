"""Complete literal owned lending declarations; no rate or security inference."""
import re
from worker.native_dom_ownership import unique_heading, owns_label, local_notes


def lending_records(soup):
    root=soup.find('main') or soup.body or soup
    heading=unique_heading(root)
    if heading is None:
        return []
    owner=heading.get_text(' ',strip=True)
    literal_owner = None
    if re.search(r'\bapply for\b', owner, re.I):
        # A literal introductory name needs independently agreeing captured
        # SEO/route plus its own complete price record at extraction time.
        names = set()
        for p in root.find_all('p')[:256]:
            previous = p.find_previous(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
            if previous is not heading or p.find_parent(['nav', 'aside', 'form', 'table']):
                continue
            paragraph = p.get_text(' ', strip=True)
            match = re.search(r'\bGet (?:a|an|the) ([A-Z][A-Za-z0-9 &-]{2,100} (?:Loan|Mortgage|Line of Credit)) (?:designed|that|to)\b', paragraph)
            if match and len(paragraph) <= 400:
                names.add(match[1])
        if len(names) != 1:
            return []
        owner = literal_owner = next(iter(names))
    if not re.search(r'line of credit|loan|mortgage',owner,re.I):
        return []
    output=[]
    for p in root.find_all('p'):
        literal=' '.join(p.get_text(' ',strip=True).split())
        if not 30<len(literal)<=6000 or not owns_label(p,root,owner) or p.find_parent(['nav','aside','table','form']):
            continue
        security=bool(re.search(r'\byou can borrow money by using (?:that|your|the) equity as collateral[.]|\bInsurance must be carried on the real property securing (?:the|your) account[,\.]',literal,re.I))
        rate=bool(re.match(r'For a '+re.escape(owner)+r', the annual percentage rate \(APR\) is a variable rate\b',literal,re.I)
                  and re.search(r'Rates vary from \d+(?:\.\d+)?% APR to \d+(?:\.\d+)?% APR',literal)
                  and literal.endswith('.'))
        # A full APR interval is independent of an explicitly labelled payment
        # example later in the same complete disclosure. Preserve every word.
        qualified = bool(re.search(r"Your APR may be as low as \d+(?:\.\d+)?% or as high as \d+(?:\.\d+)?% for the term of your loan[.]", literal, re.I)
                         and re.search(r"Your APR will depend on", literal, re.I)
                         and re.search(r"Rates subject to change without notice[.]", literal, re.I))
        if not (security or rate or qualified or dated_loan_range(literal, owner) is not None):
            continue
        notes=local_notes(soup,p)
        if notes is None:
            continue
        quote='\n'.join([owner,literal,*notes])
        if len(quote)<=6400:
            output.append(('owned_lending_terms',owner,quote))
    # An independently displayed current offer rate and its complete scenario
    # assumptions are one financial record, not an unconditional scalar.
    for p in root.find_all('p'):
        literal = ' '.join(p.get_text(' ', strip=True).split())
        if not re.fullmatch(r'Variable rate of \d+(?:\.\d+)?% in ZIP code \d{5} as of .{6,80}', literal):
            continue
        block = p.parent
        whole = ' '.join(block.get_text(' ', strip=True).split())
        if (block is root or block.name in {'form','table','aside','nav'} or len(whole) > 2400 or block.find(['h1','h2','h3','form','table','input'])
                or block.find_parent(['nav','aside','form','table']) or not owns_label(block,root,owner)
                or any(re.search(r'calculator', ' '.join(a.get('class',[])),re.I) for a in [block,*list(block.parents)[:6]])
                or len(re.findall(r'Variable rate of',whole)) != 1
                or not re.search(r'Sample variable APR assumes ',whole)
                or not re.search(r'The actual APR may vary and be higher or lower than the rate shown[.]',whole)
                or not re.search(r'APR is based on the Prime Rate',whole) or not whole.endswith('.')):
            continue
        notes = local_notes(soup,block)
        if notes is not None:
            output.append(('owned_lending_terms',owner,'\n'.join([owner,block.get_text(' ',strip=True),*notes])))
    # Explicit collateral definitions are separate from application eligibility.
    # Keep the whole locally bounded paragraph/list, including every condition.
    for p in root.find_all('p'):
        literal = ' '.join(p.get_text(' ', strip=True).split())
        if not re.match(r'A home equity line of credit \(HELOC\) is a form of credit that allows you to use the equity in your home as collateral[.]', literal, re.I):
            continue
        block = p.parent
        if (block is root or block.name in {'form','table','aside','nav'} or not owns_label(block, root, owner)
                or block.find_parent(['nav', 'aside', 'table', 'form'])
                or block.find(['h1', 'h2', 'h3', 'h4']) or len(block.get_text()) > 2400):
            continue
        notes = local_notes(soup, block)
        if notes is None:
            continue
        quote = '\n'.join([owner, block.get_text(' ', strip=True), *notes])
        output.append(('owned_lending_terms', owner, quote))
    # Keep explicitly published annual APR bounds, the payment example, fees,
    # and repayment bounds in one literal record. No example becomes a scalar.
    for p in root.find_all('p'):
        if not re.search(r'\bMinimum APR is \d', p.get_text(' ', strip=True), re.I):
            continue
        for block in [p, *list(p.parents)[:4]]:
            if block is root or block.name in {'form', 'table', 'nav', 'aside'}:
                break
            literal = block.get_text(' ', strip=True)
            if len(literal) > 6000:
                break
            if (block.find(['input', 'select', 'textarea', 'table', 'h1', 'h2', 'h3'])
                    or block.find_parent(['nav', 'aside', 'form', 'table'])
                    or not owns_label(block, root, owner)):
                continue
            if complete_loan_cost_range(literal) is None:
                continue
            notes = local_notes(soup, block)
            if notes is not None:
                quote = '\n'.join([owner, literal, *notes])
                if len(quote) <= 6400:
                    output.append(('owned_lending_terms', owner, quote))
            break
    if literal_owner and any(kind == 'owned_lending_terms' and complete_loan_cost_range(quote) is not None
                             for kind, _, quote in output):
        output.append(('owned_product_label', literal_owner, literal_owner))
    return list(dict.fromkeys(output))


def dated_loan_range(literal, owner):
    """One complete owned dated APR interval; keep all customer term limits."""
    from worker.pipeline.fpds_rate_safety import contains_unresolved_financial_placeholder
    from decimal import Decimal
    body = " ".join(str(literal).split())
    # Atomic records have a separate literal owner line; raw DOM paragraphs do not.
    body = re.sub(r"^" + re.escape(str(owner)) + r"\s+(?=" + re.escape(str(owner)) + r"\s*:)", "", body, flags=re.I)
    pattern = (re.escape(str(owner)) + r"\s*:\s*As of [A-Za-z]+ \d{1,2}, \d{4} the (?:fixed|variable) "
               r"Annual Percentage Rate \(APR\) ranged from (\d+(?:\.\d+)?)% APR to (\d+(?:\.\d+)?)% APR,")
    rate = re.match(pattern, body, re.I)
    if (not rate or not 0 <= Decimal(rate[1]) <= Decimal(rate[2]) < 100
            or contains_unresolved_financial_placeholder(body)
            or not body.endswith("Interest rates and program terms are subject to change without notice.")
            or len(re.findall(r"Annual Percentage Rate \(APR\) ranged from", body, re.I)) != 1):
        return None
    terms = re.findall(r"[^.!?]*\bloan terms range from \d+ to \d+ months(?: \([^()]+\))?[.]", body, re.I)
    if len(terms) != 1 or not re.search(r"varies based on|lowest APR in the range", body, re.I):
        return None
    return terms[0].strip()


def complete_loan_cost_range(literal):
    """Explicit annual APR/repayment bounds in a complete price declaration."""
    from decimal import Decimal
    from worker.pipeline.fpds_rate_safety import contains_unresolved_financial_placeholder
    body = ' '.join(str(literal).split())
    rates = list(re.finditer(r'\bMinimum APR is (\d+(?:\.\d+)?)% and maximum APR is (\d+(?:\.\d+)?)%[.]', body, re.I))
    terms = list(re.finditer(r'\bMinimum repayment period is (\d+) months and maximum repayment period is (\d+) months[.]', body, re.I))
    if (len(rates) != 1 or len(terms) != 1
            or not 0 <= Decimal(rates[0][1]) <= Decimal(rates[0][2]) < 100
            or not 0 < int(terms[0][1]) <= int(terms[0][2])
            or contains_unresolved_financial_placeholder(body)
            or not re.search(r'APR \(Annual Percentage Rate(?: or Effective Interest Rate)?\)', body, re.I)
            or not re.search(r'Rates and applicable fees will depend on your loan amount and loan tenor[.] Applicable fees and charges:', body, re.I)
            or not re.search(r'Example: For a .+? loan with a .+? repayment period of \d+ months', body, re.I)
            or not body.endswith('Rates and fees are subject to change.')):
        return None
    return terms[0][0]
