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
        security=bool(re.search(r'\byou can borrow money by using (?:that|your|the) equity as collateral[.]',literal,re.I))
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
    return list(dict.fromkeys(output))
