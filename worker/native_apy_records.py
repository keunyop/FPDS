"""Literal named APY components and accessible semantic headings."""
import re
from decimal import Decimal
from urllib.parse import urlsplit
from worker.native_dom_ownership import local_notes

RATE = re.compile(r'^(\d+(?:\.\d+)?)\s*%(?: correct as of \d{1,2}/\d{1,2}/\d{2,4})?$', re.I)
BASIS = re.compile(r'\bAnnual Percentage Yield(?:s)?(?: \(APYs?\))?\b', re.I)
NO_MINIMUM = re.compile(r'No minimum balance required to open an account or earn APY[.]', re.I)


def preserve_accessible_headings(soup):
    for heading in soup.find_all(['h1','h2','h3','h4','h5','h6']):
        for graphic in heading.find_all('svg'):
            if graphic.get('role') not in (None, 'img') or str(graphic.get('aria-hidden','')).lower() == 'true':
                continue
            titles = graphic.find_all('title')
            if len(titles) != 1:
                continue
            title = ' '.join(titles[0].get_text(' ',strip=True).split())
            label = ' '.join(str(graphic.get('aria-label','')).split())
            if not title or len(title)>200 or (label and label != title):
                continue
            graphic.replace_with(title)


def apy_value(quote):
    lines = [x.strip() for x in str(quote).splitlines() if x.strip()]
    if len(lines)<6 or lines[1] != 'Annual Percentage Yield' or lines[3] != 'NOTES':
        return None
    match = RATE.fullmatch(lines[2])
    if not match or not lines[-1].startswith(('/', 'https://')):
        return None
    notes = ' '.join(lines[4:-1])
    if not BASIS.search(notes) or len(NO_MINIMUM.findall(notes)) != 1:
        return None
    remainder = NO_MINIMUM.sub('',notes)
    if re.search(r'%|\b(?:if|when|only|eligible|qualif\w*|tier\w*|bonus|introductory|promotional|up to|minimum|between|from|as low as|not annual|not an annual)\b',remainder,re.I):
        return None
    value = Decimal(match[1])
    return value if 0<=value<100 else None


def apy_records(soup):
    root = soup.find('main') or soup.body or soup
    annual = [p for p in root.find_all('p') if BASIS.search(p.get_text(' ',strip=True)) and NO_MINIMUM.search(p.get_text(' ',strip=True)) and len(p.get_text())<1000]
    if len(annual)!=1:
        return []
    shared = annual[0]
    shared_refs = local_notes(soup,shared)
    if shared_refs is None:
        return []
    output=[]
    for label in root.find_all('p'):
        if label.get_text(' ',strip=True).strip() != 'Annual Percentage Yield':
            continue
        component=label.parent
        if len(component.get_text())>500 or len(component.find_all('p'))!=1:
            continue
        values=[n.get_text(' ',strip=True) for n in component.find_all(['span','p']) if RATE.fullmatch(n.get_text(' ',strip=True))]
        component_refs = local_notes(soup, component)
        if len(values)!=1 or component_refs is None:
            continue
        for scope in list(component.parents)[:8]:
            if scope is root or len(scope.get_text())>12000:
                break
            headings=scope.find_all(['h1','h2','h3'])
            links=[a for a in scope.select('a[href]') if a.get_text(' ',strip=True)=='View Details']
            if len(headings)!=1 or len(links)!=1:
                continue
            owner=headings[0].get_text(' ',strip=True)
            href=str(links[0]['href'])
            if not owner or len(owner)>120 or not href.startswith(('/', 'https://')) or href.startswith('//') or re.search(r'/(?:apply|login|calculator)(?:/|$)',urlsplit(href).path,re.I):
                break
            local=list(component_refs);valid=True
            for paragraph in scope.find_all('p'):
                literal=paragraph.get_text(' ',strip=True)
                if paragraph is label or paragraph is shared or not re.search(r'\b(?:rates?|interest|yield|APY|balance|eligible|qualif\w*|promotional|introductory)\b',literal,re.I):
                    continue
                refs=local_notes(soup,paragraph)
                if refs is None or len(literal)>1000:
                    valid=False;break
                local.extend([literal,*refs])
            notes=list(dict.fromkeys([*local,shared.get_text(' ',strip=True),*shared_refs]))
            quote='\n'.join([owner,'Annual Percentage Yield',values[0],'NOTES',*notes,href])
            if valid and len(quote)<=6400 and apy_value(quote) is not None:
                output.append(('named_deposit_apy',owner,quote))
            break
    return list(dict.fromkeys(output))