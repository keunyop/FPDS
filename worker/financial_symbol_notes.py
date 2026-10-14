"""Dependency-free exact symbolic disclosure reference handling."""
import re

def resolved_symbol_text(value):
    """Remove only independently defined footnote stars, never masked prices."""
    value=str(value)
    card = all(label in value for label in ['Interest Rates and Interest Charges','Variable Rate Information:','Credit Approval:'])
    lending = all(label in value for label in ['Minimum APR is ', 'maximum APR is ',
        'Minimum repayment period is ', 'maximum repayment period is ',
        'APR (Annual Percentage Rate', 'Rates and fees are subject to change.'])
    if not (card or lending):
        return value
    pattern = (r'(?<!\*)(\*{1,4})(?!\*)\s*(?:The rate|The minimum|We charge)' if card else
               r'(?<!\*)(\*{1,3})(?!\*)\s*(?:Minimum APR is|Minimum repayment period is|Rates and fees are subject to change[.])')
    definitions=list(re.finditer(pattern,value))
    if lending and not card and {m[1] for m in definitions} != {'*', '**', '***'}:
        return value
    symbols=[m[1] for m in definitions]
    if not symbols or len(set(symbols))!=len(symbols):
        return value
    positions={m.start() for m in definitions}
    matches=list(re.finditer(r'(?<!\*)\*{1,4}(?!\*)',value))
    for match in matches:
        if match[0] not in symbols:
            return value
        if match.start() not in positions and not re.search(r'(?:\d|%[.]?|Transfers|Prime Rate[.])\s*$',value[:match.start()]):
            return value
    return re.sub(r'(?<!\*)\*{1,4}(?!\*)','',value)
