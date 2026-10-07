"""Literal deposit row/group evidence. No bank names or generated financial units."""
import re
from decimal import Decimal
from bs4 import Tag

ANNUAL = re.compile(r'interest rates? (?:is|are) annualized|per annum|\bAPY\b|\bAPR\b', re.I)
ACCOUNT = re.compile(r'^(?:(?:non[- ]registered|TFSA|RSP|RRSP|Spousal RSP) )?Savings Account$', re.I)
BLANKET_FEE = re.compile(r'^With our (?P<name>(?:non[- ]registered )?(?:savings|chequing|checking) account),\s*(?:you[’\x27]ll enjoy |you will enjoy )?no fees(?: and no minimum balance requirements)?[.]$', re.I)


def named_account_rate(quote):
    lines=[x.strip() for x in str(quote).splitlines() if x.strip()]
    if (len(lines)<6 or not ACCOUNT.fullmatch(lines[0]) or lines[1]!='Type'
        or lines[2] not in {'Current rate (%)','Interest rate (%)','APY (%)'}
        or lines[3]!=lines[0] or not re.fullmatch(r'\d+(?:\.\d+)?',lines[4])
        or not ANNUAL.search(' '.join(lines[5:]))):
        return None
    # Current scalar rows cannot inherit a tier/introductory/eligibility note.
    if re.search(r'\b(?:if|when|provided|tier\w*|introductory|promotional|bonus|first|up to|minimum balance)\b', ' '.join(lines[5:]), re.I):
        return None
    value=Decimal(lines[4])
    return float(value) if 0<=value<100 else None


def deposit_table_records(soup):
    main=soup.find('main') or soup.body or soup
    output=[]
    # Literal observed links are retrieval associations, never financial facts.
    for a in main.select('a[href]')[:512]:
        href=str(a.get('href') or '')
        label=a.get_text(' ',strip=True)+' '+str(a.get('title') or '')
        if re.search(r'savings account|\bGICs?\b|certificates? of deposit',label,re.I):
            output.append(('captured_product_link',label,href))
    for table in main.find_all('table')[:64]:
        rows=table.find_all('tr')
        if not rows or table.find('table') or table.select('[rowspan], [colspan]'):
            continue
        headers=[c.get_text(' ',strip=True) for c in rows[0].find_all(['td','th'],recursive=False)]
        after=[]; oversized=False
        for sibling in table.next_siblings:
            if not isinstance(sibling,Tag):continue
            if sibling.name=='table' or sibling.find('table'):break
            literal=sibling.get_text('\n',strip=True)
            if not literal:continue
            if sibling.name in {'h1','h2','h3','h4'} or (len(literal)<120 and re.fullmatch(r'.*(?:GICs?|Certificates?)(?: \([^)]*\))?',literal,re.I)):
                break
            after.append(literal)
            if sum(map(len,after))>4000:
                oversized=True;break
        if oversized:continue
        if headers==['Type','Current rate (%)'] and len(after)==1 and ANNUAL.search(after[0]):
            for row in rows[1:]:
                cells=[c.get_text(' ',strip=True) for c in row.find_all(['td','th'],recursive=False)]
                if len(cells)!=2 or not ACCOUNT.fullmatch(cells[0]):continue
                record='\n'.join([cells[0],*headers,*cells,*after])
                if named_account_rate(record) is not None:
                    output.append(('named_deposit_rate',cells[0],record))
        if headers and headers[0]=='Term':
            before=table.find_previous_sibling()
            if before is None or before.find('table'):continue
            owner=before.get_text(' ',strip=True)
            if len(owner)>120 or not re.search(r'\bGICs?\b|certificates?\b',owner,re.I):continue
            # No annex from another table, ambiguous footnote or partial tail.
            from worker.native_rate_tables import _local_notes
            notes=_local_notes(soup,table)
            if notes is None:continue
            record='\n'.join([owner,table.get_text('\n',strip=True),*after,*notes])
            if after and len(record)<=6400:
                output.append(('named_deposit_schedule',owner,record))
    for paragraph in main.find_all('p')[:512]:
        literal=paragraph.get_text(' ',strip=True)
        first=re.split(r'(?<=[.!?])\s+',literal,maxsplit=1)[0]
        match=BLANKET_FEE.fullmatch(first)
        if match:
            # A first sentence must not hide a later condition or linked note.
            # Only a separately named registered-account sentence can belong
            # to another product when the declaration names non-registered.
            tail=literal[len(first):].strip()
            if re.match(r'non[- ]registered ',match['name'],re.I):
                tail=re.sub(r'For our registered savings accounts,[^.!?]*[.]', '',tail,flags=re.I)
            if (paragraph.select('a[href*="#"], [aria-describedby]') or re.search(
                    r'\b(?:fees?|charges?|if|when|unless|except|provided|conditions?|terms|first|only|free|minimum balance)\b',tail,re.I)):
                continue
            output.append(('named_deposit_fee',match['name'],first))
    return list(dict.fromkeys(output))


def deposit_variants(context, candidates, detail_url):
    from worker.native_rate_tables import rate_schedules
    from worker.pipeline.fpds_collection_accuracy import quote_supports_value, text
    from worker.pipeline.fpds_extraction.service import _canonical_official_source_url
    proposals={}
    for c in candidates:
        if (c.anchor_type!='named_deposit_schedule'
            or c.retrieval_metadata.get('captured_companion') is not True
            or _canonical_official_source_url(c.retrieval_metadata.get('parent_detail_url'))!=detail_url
            or c.bank_code!=context.bank_code or c.country_code!=context.country_code
            or c.source_language!=context.source_language):continue
        quote=c.evidence_excerpt
        schedules=rate_schedules(quote,annual_only=True)
        if len(schedules)!=1 or not quote_supports_value('non_redeemable_flag',True,quote):continue
        name=str(c.anchor_value)
        if not quote.startswith(name+'\n'):continue
        values={'product_name':name,'term_rate_table':[{**r,'notes':text(quote)} for r in schedules[0]],
            'non_redeemable_flag':True}
        minimum=re.search(r'minimum deposit of \$(\d[\d,]*(?:\.\d+)?)',quote,re.I)
        if minimum:values['minimum_deposit']=float(minimum[1].replace(',',''))
        calculation=re.search(r'Interest is calculated per annum[.]',quote,re.I)
        payment=re.search(r'Interest is paid at maturity[.]',quote,re.I)
        if calculation:values['interest_calculation_method']=calculation[0]
        if payment:values['interest_payment_frequency']=payment[0]
        records={}
        for field,value in values.items():
            evidence_quote=name if field=='product_name' else quote
            if not quote_supports_value(field,value,evidence_quote):continue
            records[field]={'candidate_value':value,'source_document_id':c.source_document_id,
                'source_snapshot_id':c.source_snapshot_id,'evidence_chunk_id':c.evidence_chunk_id,
                'evidence_text_excerpt':quote,'anchor_type':c.anchor_type,'anchor_value':name,
                'page_no':c.page_no,'chunk_index':c.chunk_index,'field_metadata':{
                    'official_grounding_contract_version':'collection-official-grounding-v2',
                    'official_verification_status':'match','official_grounding_method':'deterministic_named_deposit_table',
                    'official_web_sources':[{'url':c.retrieval_metadata['source_url']}],
                    'evidence_quote':evidence_quote}}
        if {'product_name','term_rate_table','non_redeemable_flag'}<=records.keys():
            proposals.setdefault(name,[]).append({'product_name':name,**{k:r['candidate_value'] for k,r in records.items()},'field_records':records,
                'evidence_chunk_id':c.evidence_chunk_id,'evidence_text_excerpt':quote,
                'field_metadata':records['product_name']['field_metadata']})
    # Identical captured URL aliases deduplicate; disagreeing records exclude.
    import json
    return [rows[0] for rows in proposals.values() if len({json.dumps({k:r[k] for k in ['product_name','term_rate_table']},sort_keys=True) for r in rows})==1]
