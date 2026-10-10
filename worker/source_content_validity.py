"""Conservative source availability; financial body text is never an error cue."""
import re
from bs4 import BeautifulSoup

def html_unavailable_reason(body):
    soup=BeautifulSoup(body.decode('utf-8',errors='replace'),'html.parser')
    main=soup.find('main') or soup
    candidates=[soup.title,main.find('h1')]
    error=re.compile(r'^(?:404(?:\s*[-:|]\s*)?|(?:error|erreur)\s+404\b|page (?:not found|introuvable|non trouv\u00e9e)|not found|the page (?:you requested )?(?:cannot|could not) be found|\u30da\u30fc\u30b8\u304c\u898b\u3064\u304b\u308a\u307e\u305b\u3093|\ud398\uc774\uc9c0\ub97c \ucc3e\uc744 \uc218 \uc5c6)',re.I)
    if any(n is not None and error.search(n.get_text(' ',strip=True)) for n in candidates):
        return 'soft_404'
    heading = main.find('h1')
    if heading is not None and re.fullmatch(r"(?:Oops[!.]?|Oops, Something went wrong[!.]?|Something went wrong[!.]?|It[\u2019']s not you, it[\u2019']s us[!.]?)", heading.get_text(' ',strip=True), re.I):
        # Require an actual adjacent unavailable-page statement. Financial
        # help copy or a sample error elsewhere cannot make a page unavailable.
        for block in heading.find_all_next(['h1','h2','p'], limit=4):
            if block.name == 'h1':
                break
            literal = block.get_text(' ',strip=True)
            if len(literal) <= 700 and re.search(r"\b(?:we (?:can[\u2019']t|cannot|couldn[\u2019']t) find (?:that|this|the) page|the page (?:cannot|could not) be found|the page you[\u2019']re trying to access doesn[\u2019']t appear to exist)\b",literal,re.I):
                return 'soft_404'
    return None
