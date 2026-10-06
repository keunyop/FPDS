"""Conservative source availability; financial body text is never an error cue."""
import re
from bs4 import BeautifulSoup

def html_unavailable_reason(body):
    soup=BeautifulSoup(body.decode('utf-8',errors='replace'),'html.parser')
    main=soup.find('main') or soup
    candidates=[soup.title,main.find('h1')]
    error=re.compile(r'^(?:404(?:\s*[-:|]\s*)?|(?:error|erreur)\s+404\b|page (?:not found|introuvable|non trouv\u00e9e)|not found|the page (?:you requested )?(?:cannot|could not) be found|\u30da\u30fc\u30b8\u304c\u898b\u3064\u304b\u308a\u307e\u305b\u3093|\ud398\uc774\uc9c0\ub97c \ucc3e\uc744 \uc218 \uc5c6)',re.I)
    return 'soft_404' if any(n is not None and error.search(n.get_text(' ',strip=True)) for n in candidates) else None
