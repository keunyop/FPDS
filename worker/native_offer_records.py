"""Owned complete qualified card offers and explicitly referenced current APYs."""
import re
from decimal import Decimal
from worker.native_dom_ownership import unique_heading,owns_label,local_notes

_SUPERSCRIPTS=str.maketrans('⁰¹²³⁴⁵⁶⁷⁸⁹','0123456789')


def symbol_note(soup,symbol,block):
    matches=[]
    for note in soup.find_all(['p','li']):
        if note is block or block in note.parents:
            continue
        first=next(iter(note.stripped_strings),'')
        first_text=next((x for x in note.find_all(string=True) if str(x).strip()),None)
        if symbol.isdigit() and (first_text is None or first_text.find_parent('sup') is None):
            continue
        literal=note.get_text(' ',strip=True)
        if first==symbol and 20<len(literal)<6000:
            matches.append(literal)
    matches=list(dict.fromkeys(matches))
    return matches[0] if len(matches)==1 else None


def referenced_apy_value(quote):
    lines=[x.strip() for x in str(quote).splitlines() if x.strip()]
    if len(lines)!=4 or lines[2]!='NOTES':return None
    rate=re.fullmatch(r'(\d+(?:\.\d+)?)% APY([¹²³⁴⁵⁶⁷⁸⁹])',lines[1])
    if not rate:return None
    note=lines[3]
    marker=rate[2].translate(_SUPERSCRIPTS)
    if not note.startswith(marker+' ') or not re.search(r'The Annual Percentage Yield \(APY\) as advertised is accurate as of \d{1,2}/\d{1,2}/\d{4}[.]',note):return None
    subject=re.search(r'before and after a (.+? Account) is opened[.]',note,re.I)
    if not subject or not lines[0].casefold().endswith(re.sub(r' Account$','',subject[1],flags=re.I).casefold()):return None
    if re.search(r'%|\b(?:if|when|provided|only|eligible|qualif\w*|tier\w*|bonus|introductory|promotional|minimum|up to|from|between)\b',note,re.I):return None
    value=Decimal(rate[1]);return value if 0<=value<100 else None


def owned_offer_records(soup):
    root=soup.find('main') or soup.body or soup
    heading=unique_heading(root)
    if heading is None:return []
    owner=heading.get_text(' ',strip=True);output=[]
    if re.search(r'\bsavings\b',owner,re.I):
        for rate in root.find_all(['h2','h3','h4']):
            literal=rate.get_text(' ',strip=True)
            match=re.fullmatch(r'\d+(?:\.\d+)?% APY([¹²³⁴⁵⁶⁷⁸⁹])',literal)
            if not match or not owns_label(rate,root,owner) or rate.find_parent(['form','table','aside','nav']):continue
            previous=rate.find_previous(['h1','h2','h3'])
            if previous is not None and previous.name!='h1' and re.search(r'\b(?:account|card|savings|loan|CD|GIC)\b',previous.get_text(),re.I):continue
            # A complete annual note does not cancel an adjacent qualification.
            # Inspect bounded local pricing containers as well as the heading;
            # uncertain qualified values remain excluded instead of truncated.
            scoped = [previous.get_text(' ',strip=True) if previous is not None else '']
            for panel in list(rate.parents)[:4]:
                if panel is root or len(panel.get_text()) > 1400:
                    break
                scoped.append(panel.get_text(' ',strip=True))
            qualification = re.sub(r"\bno minimum (?:deposit|balance)(?: required)?\b", "No requirement", ' '.join(scoped), flags=re.I)
            if re.search(r"\b(?:if|when|only|eligible|qualif\w*|tier\w*|bonus|introductory|promotional|minimum|at least|up to)\b", qualification, re.I):
                continue
            note=symbol_note(soup,match[1].translate(_SUPERSCRIPTS),rate)
            if note is None or local_notes(soup,rate) is None:continue
            quote='\n'.join([owner,literal,'NOTES',note])
            if referenced_apy_value(quote) is not None:output.append(('owned_referenced_apy',owner,quote))
    if re.search(r'\b(?:credit card|visa|mastercard)\b',owner,re.I):
        for paragraph in root.find_all('p'):
            literal=paragraph.get_text(' ',strip=True)
            if (len(literal)>2400 or not re.search(r'Intro APR for your first \d+ billing cycles for purchases',literal,re.I)
                    or not re.search(r"After the intro APR offer ends, a Variable APR that's currently \d+(?:\.\d+)?% to \d+(?:\.\d+)?% will apply[.]",literal,re.I)
                    or not owns_label(paragraph,root,owner) or paragraph.find_parent(['table','aside','nav','form'])):continue
            previous=paragraph.find_previous(['h1','h2','h3'])
            if previous is not None and previous.name!='h1' and re.search(r'\b(?:credit card|visa|mastercard)\b',previous.get_text(),re.I):continue
            notes=local_notes(soup,paragraph)
            if notes is None:continue
            symbols=set(p.get_text('',strip=True) for p in paragraph.find_all('sup'))
            if any(not re.fullmatch(r'[†‡*]+',x) for x in symbols):continue
            for symbol in symbols:
                note=symbol_note(soup,symbol,paragraph)
                if note is None:notes=None;break
                notes.append(note)
            if notes is None:continue
            quote='\n'.join([owner,paragraph.get_text('\n',strip=True),*dict.fromkeys(notes)])
            if len(quote)<=6400:output.append(('owned_card_apr_offer',owner,quote))
    return list(dict.fromkeys(output))