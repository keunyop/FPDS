"""Dependency-free exact symbolic disclosure reference handling."""
import re

def resolved_symbol_text(value):
    """Remove only independently defined footnote stars, never masked prices."""
    value=str(value)
    if not all(label in value for label in ['Interest Rates and Interest Charges','Variable Rate Information:','Credit Approval:']):
        return value
    definitions=list(re.finditer(r'(?<!\*)(\*{1,4})(?!\*)\s*(?:The rate|The minimum|We charge)',value))
    symbols=[m[1] for m in definitions]
    if not symbols or len(set(symbols))!=len(symbols):
        return value
    positions={m.start() for m in definitions}
    matches=list(re.finditer(r'(?<!\*)\*{1,4}(?!\*)',value))
    for match in matches:
        if match[0] not in symbols:
            return value
        if match.start() not in positions and not re.search(r'(?:\d|%|Transfers|Prime Rate[.])\s*$',value[:match.start()]):
            return value
    return re.sub(r'(?<!\*)\*{1,4}(?!\*)','',value)
