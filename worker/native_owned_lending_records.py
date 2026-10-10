"""Complete literal owned lending declarations; no rate or security inference."""
import re
from worker.native_dom_ownership import unique_heading, owns_label, local_notes


def lending_records(soup):
    root=soup.find('main') or soup.body or soup
    heading=unique_heading(root)
    if heading is None:
        return []
    owner=heading.get_text(' ',strip=True)
    if not re.search(r'line of credit|loan',owner,re.I):
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
        if not (security or rate or qualified):
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
    return list(dict.fromkeys(output))
