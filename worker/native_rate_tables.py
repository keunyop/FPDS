"""Literal native rate headers/rows. No generated units, rates or source text."""
from decimal import Decimal
import re
from bs4 import BeautifulSoup

_HEADER = re.compile(r"^(?:(?:Annual|Fixed|Variable|Minimum|Interest)\s+)*(?:%\s*)?(?:rate|yield)s?\s*(?:\(%\)|%)?$|^AP[RY]\s*(?:\(%\)|%)?$", re.I)
_TERM = re.compile(r"^\d+(?:\.\d+)?(?:\s*[-–]\s*\d+)?\s*[- ]?\s*(?:days?|months?|years?)$", re.I)
_NUMBER = re.compile(r"^\d+(?:\.\d+)?%?$" )

def rate_schedules(quote, *, annual_only=False):
    """Read literal Term/rate or explicit interest-payment columns.

    Repeated identical responsive copies are harmless; conflicting repeats
    are not proof. Qualified rows remain in summaries, never scalar facts.
    """
    lines=[x.strip() for x in str(quote).splitlines() if x.strip()]
    found=[]
    for i in range(len(lines)-2):
        payment_columns = lines[i+1:i+4] == ["Annual (%)", "Semi Annual (%)", "Monthly (%)"]
        if lines[i].casefold()!='term' or (not payment_columns and not _HEADER.fullmatch(lines[i+1])):
            continue
        explicit_basis = bool(re.search(r'interest (?:is )?calculated per annum|interest rates? (?:is|are) annualized|interest rates?[^.!?]{0,130} are annual interest rates', str(quote), re.I))
        if annual_only and (payment_columns and not explicit_basis or not payment_columns and not (re.search(r'\bannual\b|\bAP[RY]\b',lines[i+1],re.I) or explicit_basis)):
            continue
        rows=[];j=i+4 if payment_columns else i+2
        while j+1<len(lines) and _TERM.fullmatch(lines[j]):
            offset = 2 if lines[j+1] == lines[i+1] else 1
            if j+offset >= len(lines) or not _NUMBER.fullmatch(lines[j+offset]):return []
            if payment_columns and (j+3 >= len(lines) or not all(_NUMBER.fullmatch(v) and 0<=Decimal(v.removesuffix("%"))<100 for v in lines[j+1:j+4])):
                return []
            if not payment_columns and '%' not in lines[i+1] and not lines[j+offset].endswith('%'):return []
            number=Decimal(lines[j+offset].removesuffix('%'))
            if not number.is_finite() or not 0<=number<100:return []
            rows.append({'term_label':lines[j],'rate':float(number)});j+=4 if payment_columns else offset+1
        if not rows:continue
        if len({r['term_label'].casefold() for r in rows})!=len(rows):return []
        # A qualified/non-term row is a part of the table, not a terminator
        # that permits treating a partial grid as a complete schedule.
        if annual_only and j<len(lines) and (_TERM.fullmatch(lines[j]) or (j+1<len(lines) and _NUMBER.fullmatch(lines[j+1]))):
            return []
        if rows not in found:found.append(rows)
    return found

def has_native_rate_grid(quote):
    return bool(rate_schedules(quote) or native_variable_rows(quote))

def _local_notes(soup, scope):
    notes=[]
    for a in scope.select('a[href^="#"]'):
        href=a.get('href','');matches=soup.find_all(id=href[1:])
        if not matches:
            # Literal #legal-N plus label N can identify one numbered Legal
            # disclosure even when the site omits HTML IDs. Require one list,
            # its actual start index and exact heading; no invented target.
            ref=re.fullmatch(r'#([a-z][a-z-]*)-(\d+)',href,re.I)
            lists=[]
            if ref and a.get_text(' ',strip=True)==ref[2]:
                for heading in soup.find_all(['button','summary','h2','h3','h4']):
                    if heading.get_text(' ',strip=True).casefold().replace(' ','-')!=ref[1].casefold():continue
                    if heading.find_parent('button') is not None:continue
                    target=soup.find(id=heading.get('aria-controls')) if heading.get('aria-controls') else heading.find_next_sibling()
                    if target is not None:lists.extend(target.find_all('ol'))
                # Nested heading/button matches cannot double-bind a note.
                lists=list({id(x):x for x in lists}.values())
                if len(lists)==1:
                    try:index=int(ref[2])-int(lists[0].get('start',1))
                    except (TypeError,ValueError):return None
                    items=lists[0].find_all('li',recursive=False)
                    if 0<=index<len(items):matches=[items[index]]
        if len(matches)!=1:return None
        target=matches[0]
        if target.find_parent('table') is not None:return None
        note=target.get_text('\n',strip=True)
        if note and note not in notes:notes.append(note)
    return notes

_VARIABLE_HEADER='Type\nDetails\nConvertible closed term\nVariable rate (%)'

def native_variable_rows(quote):
    if _VARIABLE_HEADER not in str(quote):return []
    return [(m[1],float(m[2])) for m in re.finditer(r'(?m)^(\d+ years?)\n(\d+(?:\.\d+)?)\n',str(quote))]

def _variable_records(soup, scope):
    rows={};conflicts=set()
    intro=BeautifulSoup(str(scope),'html.parser')
    for t in intro.find_all('table'):t.decompose()
    prefix=intro.get_text('\n',strip=True)
    for table in scope.find_all('table'):
        head=table.find('thead')
        if head is None or head.get_text('\n',strip=True)!=_VARIABLE_HEADER:continue
        for row in table.find_all('tr')[1:]:
            cells=row.find_all('td',recursive=False)
            if len(cells)!=4:continue
            term=cells[2].get_text(' ',strip=True);rate=cells[3].get_text(' ',strip=True)
            if not _TERM.fullmatch(term) or not _NUMBER.fullmatch(rate):continue
            key=(cells[0].get_text(' ',strip=True),term)
            notes=_local_notes(soup,row)
            if notes is None:conflicts.add(key);continue
            details=cells[1].get_text(' ',strip=True)
            margin=re.search(r'prime rate\s*([+-])\s*(\d+(?:\.\d+)?)%',details,re.I)
            note_margins=[(m[1],Decimal(m[2])) for n in notes for m in re.finditer(r'prime rate.{0,140}?([+-])\s*(\d+(?:\.\d+)?)% applicable',n,re.I)]
            if margin and note_margins and any((margin[1],Decimal(margin[2]))!=m for m in note_margins):
                conflicts.add(key);continue
            record='\n'.join([prefix,_VARIABLE_HEADER,*[c.get_text('\n',strip=True) for c in cells],*notes])
            if key in rows and rows[key]!=record:conflicts.add(key)
            else:rows[key]=record
    records=[value for key,value in rows.items() if key not in conflicts]
    record='\n'.join(records)
    return record if record and len(record)<=6400 else None

def _legal_sections(soup):
    result=[]
    for button in soup.find_all(['button','summary']):
        if button.get_text(' ',strip=True).casefold() not in {'legal','terms and conditions','rate notes','rate disclosures'}:continue
        target=soup.find(id=button.get('aria-controls')) if button.get('aria-controls') else button.find_next_sibling()
        if target is not None and target.find('table') is None:
            result.append(target.get_text('\n',strip=True))
    return list(dict.fromkeys(x for x in result if x))

def native_financial_sections(soup):
    """Return (kind, owner, literal record) for bounded owned DOM sections.

    Complete section text keeps table captions, headers, pricing alternatives
    and local conditions. All linked notes must resolve uniquely. Repeated DOM
    tables are deduplicated only after complete cell/header equality. No JS.
    """
    main=soup.find('main') or soup.body or soup
    output=[];seen=set()
    for table in main.find_all('table')[:64]:
        scope=table.find_parent('section')
        if scope is None:continue
        heading=scope.find(['h1','h2','h3','h4'])
        if heading is None or heading.find_parent('table') is not None:continue
        owner=heading.get_text(' ',strip=True)
        if owner in seen:continue
        seen.add(owner)
        if any(t.find('thead') is not None and t.find('thead').get_text('\n',strip=True)==_VARIABLE_HEADER for t in scope.find_all('table')):
            record=_variable_records(soup,scope)
            if record:output.append(('native_rate_table',owner,record))
            continue
        clone=BeautifulSoup(str(scope),'html.parser')
        signatures=set()
        for t in list(clone.find_all('table')):
            rows=t.find_all('tr');header=rows[0].find_all(['th','td'],recursive=False) if rows else []
            headers=[h.get_text(' ',strip=True) for h in header]
            # Explicit percent unit on a rate column is mandatory.
            if not any(_HEADER.fullmatch(h) and '%' in h for h in headers):
                continue
            signature=[]
            for row in rows[1:]:
                cells=[]
                for col,c in enumerate(row.find_all(['th','td'],recursive=False)):
                    value=c.get_text('\n',strip=True)
                    # Responsive cells repeat their own header literally.
                    if col<len(headers) and value.startswith(headers[col]+'\n'):
                        value=value[len(headers[col])+1:]
                    cells.append(value)
                if cells:signature.append(tuple(cells))
            signature=(tuple(headers),tuple(signature))
            if signature in signatures:t.decompose()
            else:signatures.add(signature)
        if not signatures:continue
        notes=_local_notes(soup,scope)
        if notes is None:continue
        parts=[clone.get_text('\n',strip=True),*notes]
        # A single product's annual maturity table may share the detail's
        # complete Legal section. Never append family-page global notes.
        h1s=main.find_all('h1')
        annual_tables=rate_schedules(parts[0],annual_only=True)
        if len(h1s)==1 and annual_tables and re.search(r'\bgic\b|\bcertificate(?:s)?(?: of deposit)?\b',h1s[0].get_text(' ',strip=True),re.I):
            parts.extend(_legal_sections(soup))
        record='\n'.join(dict.fromkeys(x for x in parts if x))
        if len(record)<=6400:output.append(('native_rate_table',owner,record))
    # Identity stays separate. Owned detail terms contain complete Features,
    # term declarations and Legal; related-product recommendations are excluded.
    h1s=main.find_all('h1')
    if len(h1s)==1:
        owner=h1s[0].get_text(' ',strip=True)
        sections=[]
        for head in main.find_all(['h2','h3','h4'])[:256]:
            label=head.get_text(' ',strip=True).strip('.').casefold()
            if label not in {'features','the benefits','benefits','terms','our offer','our terms'}:continue
            for scope in head.parents:
                if scope is main:break
                if scope.find('table') is not None:break
                if len(scope.find_all(head.name))>1:break
                record=scope.get_text('\n',strip=True)
                if len(record)>len(head.get_text())+40:
                    notes=_local_notes(soup,scope)
                    if notes is not None:sections.append('\n'.join([record,*notes]))
                    break
        if sections:
            parts=[owner,*sections,*_legal_sections(soup)]
            record='\n'.join(dict.fromkeys(x for x in parts if x))
            if len(record)<=6400:output.append(('native_product_terms',owner,record))
    return output
