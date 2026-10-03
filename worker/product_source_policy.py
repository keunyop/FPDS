"""Conservative product identity and availability checks on official evidence."""
from datetime import UTC, date, datetime
import re
from html.parser import HTMLParser

_TYPE_PATTERNS = {
    'chequing': r'chequing|checking', 'checking': r'chequing|checking',
    'savings': r'savings?', 'gic': r'GICs?|guaranteed investment certificates?|term deposits?|certificates? of deposit|CDs?',
    'mortgage': r'mortgages?', 'personal-loan': r'personal loans?|RSP loans?|RRSP loans?',
    'line-of-credit': r'lines? of credit|HELOC', 'credit-card': r'credit cards?',
}


class _AvailabilityTextParser(HTMLParser):
    """Keep notice blocks separate without importing Worker-only libraries."""

    _HEADINGS = {'title', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6'}
    _HIDDEN = {'script', 'style', 'noscript', 'nav'}
    _BLOCKS = {'p', 'div', 'section', 'article', 'aside', 'header', 'footer',
               'main', 'blockquote', 'li', 'ul', 'ol', 'table', 'tr', 'td', 'th',
               'dl', 'dt', 'dd', 'br', 'hr'}
    _VOID = {'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input',
             'link', 'meta', 'param', 'source', 'track', 'wbr'}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self._stack: list[str] = []
        self._first_heading = False
        self._capture_heading = False
        self.heading: list[str] = []
        self.body: list[str] = []

    def handle_starttag(self, tag, attrs):
        if tag in self._BLOCKS or tag in self._HEADINGS or tag in self._HIDDEN:
            self.body.append('\n')
        if tag == 'h1' and not self._first_heading and not any(t in self._HIDDEN for t in self._stack):
            self._first_heading = True
            self._capture_heading = True
        if tag not in self._VOID:
            self._stack.append(tag)

    def handle_endtag(self, tag):
        if tag in self._stack:
            index = len(self._stack) - 1 - self._stack[::-1].index(tag)
            if 'h1' in self._stack[index:]:
                self._capture_heading = False
            del self._stack[index:]
        if tag in self._BLOCKS or tag in self._HEADINGS or tag in self._HIDDEN:
            self.body.append('\n')

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        self.handle_endtag(tag)

    def handle_data(self, data):
        if any(tag in self._HIDDEN for tag in self._stack):
            return
        if self._capture_heading:
            self.heading.append(data.strip())
        if not any(tag in self._HEADINGS for tag in self._stack):
            self.body.append(data.strip() + ' ')


def unavailable_for_new_customers(content: str, *, product_type: str, product_name: str | None = None, today: date | None = None) -> bool:
    pattern = _TYPE_PATTERNS.get(product_type)
    if not pattern:
        return False
    today = today or datetime.now(UTC).date()
    parser = _AvailabilityTextParser()
    parser.feed(content)
    parser.close()
    identity = product_name or ' '.join(parser.heading)
    generic = {'bank', 'banks', 'account', 'accounts', 'checking', 'chequing', 'savings', 'saving',
               'credit', 'card', 'cards', 'personal', 'loan', 'loans', 'line', 'lines', 'of', 'the',
               'mortgage', 'mortgages', 'gic', 'gics', 'term', 'deposit', 'deposits', 'certificate', 'certificates'}
    identity_tokens = set(re.findall(r'[a-z0-9]+', identity.lower())) - generic
    text = ''.join(parser.body)
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


def non_product_identity_reason(*, product_type: str, primary_heading: str = "", page_title: str = "") -> str | None:
    """Classify only the prominent identity, never benefits or navigation text.

    Insurance and account tools remain usable as bounded supporting evidence;
    they cannot themselves identify one of the supported financial products.
    An unknown title is left for the normal evidence and boundary gates.
    """
    if product_type not in _TYPE_PATTERNS:
        return None
    identity = re.sub(r"\s+", " ", primary_heading or page_title.split("|", 1)[0]).strip()
    if not identity:
        return None
    if re.search(r"\b(?:search tool|rate calculator|loan calculator|mortgage calculator|payment calculator)\b", identity, re.I):
        return "non_product_service_flow"
    if re.search(r"\b(?:mortgage|loan|credit card|line of credit|mastercard|visa)\b.{0,35}\b(?:insurance|access details|security protection|security features)\b", identity, re.I):
        return "non_product_service_flow"
    if product_type == "credit-card" and re.search(r"\bprepaid\b", identity, re.I):
        return "non_product_service_flow"
    return None
