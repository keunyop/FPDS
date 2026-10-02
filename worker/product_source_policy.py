"""Conservative product-scoped availability checks on captured official text."""
from datetime import UTC, date, datetime
import re
from bs4 import BeautifulSoup

_TYPE_PATTERNS = {
    'chequing': r'chequing|checking', 'checking': r'chequing|checking',
    'savings': r'savings?', 'gic': r'GICs?|guaranteed investment certificates?|term deposits?|certificates? of deposit|CDs?',
    'mortgage': r'mortgages?', 'personal-loan': r'personal loans?|RSP loans?|RRSP loans?',
    'line-of-credit': r'lines? of credit|HELOC', 'credit-card': r'credit cards?',
}


def unavailable_for_new_customers(content: str, *, product_type: str, product_name: str | None = None, today: date | None = None) -> bool:
    pattern = _TYPE_PATTERNS.get(product_type)
    if not pattern:
        return False
    today = today or datetime.now(UTC).date()
    soup = BeautifulSoup(content, 'html.parser')
    for tag in soup(['script', 'style', 'noscript', 'nav']):
        tag.decompose()
    heading = soup.find('h1')
    identity = product_name or (heading.get_text(' ', strip=True) if heading else '')
    generic = {'bank', 'banks', 'account', 'accounts', 'checking', 'chequing', 'savings', 'saving',
               'credit', 'card', 'cards', 'personal', 'loan', 'loans', 'line', 'lines', 'of', 'the',
               'mortgage', 'mortgages', 'gic', 'gics', 'term', 'deposit', 'deposits', 'certificate', 'certificates'}
    identity_tokens = set(re.findall(r'[a-z0-9]+', identity.lower())) - generic
    for tag in soup(['title', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
        tag.decompose()
    text = soup.get_text(' ', strip=True)
    # Inspect full notices, not just page titles; unrelated product notices
    # remain ineligible because the same sentence must name this product type.
    for sentence in re.split(r'(?<=[.!?])\s+|\n', text):
        if not re.search(r'\b(?:'+pattern+r')\b', sentence, re.I):
            continue
        # May as an effective-date month is not the modal uncertainty word.
        uncertainty_context = re.sub(r'\bMay \d{1,2},? \d{4}\b', 'dated notice', sentence, flags=re.I)
        if re.search(r'\b(?:not discontinued|has not discontinued|will|plans? to|may|might|could|temporarily)\b', uncertainty_context, re.I):
            continue
        closed = re.search(
            r'\b(?:has discontinued|discontinued) (?:the )?opening of new\b|'
            r'\bno longer (?:available|offered|accepting|open)|'
            r'\b(?:not|unavailable) (?:available )?(?:to|for) new (?:customers|applications)|'
            r'\bstopped accepting new applications\b', sentence, re.I)
        if not closed:
            continue
        # A legacy variant of this same product type is not the current one.
        # Broad category closure is explicit only for category-level opening
        # or a sentence starting with the bare category name.
        generic_closure = re.search(r'opening of new\s+(?:'+pattern+r')\b', sentence, re.I) or re.match(
            r'\s*(?:The )?(?:'+pattern+r')\s+(?:accounts?|products?|cards?|applications?)?\s*(?:are|is|no longer|has)\b', sentence, re.I)
        if identity_tokens and not generic_closure and not identity_tokens <= set(re.findall(r'[a-z0-9]+', sentence.lower())):
            continue
        # A future-dated or unparsable effective notice does not prove closure.
        effective = re.search(r'\b(?:as of|effective|from|starting)\s+([A-Za-z]+ \d{1,2},? \d{4}|\d{4}-\d{2}-\d{2})', sentence, re.I)
        if effective:
            parsed = None
            for fmt in ('%B %d, %Y', '%B %d %Y', '%b %d, %Y', '%Y-%m-%d'):
                try:
                    parsed = datetime.strptime(effective[1], fmt).date()
                    break
                except ValueError:
                    pass
            if parsed is None or parsed > today:
                continue
        elif re.search(r'\b(?:as of|effective|starting|from)\b', sentence, re.I):
            continue
        return True
    return False
