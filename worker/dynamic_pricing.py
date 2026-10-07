"""Detect empty source-native pricing slots; rendering never supplies a fact."""
import re


def has_empty_dynamic_rate_slot(html: str) -> bool:
    # Literal rate-loader markup plus an empty slot is stronger than a stray
    # percentage in legal notes. No scripts are evaluated here.
    loaders = re.findall(r'<script\b[^>]*\bsrc\s*=\s*["\']([^"\']+)', html, re.I)
    if not any(re.search(r'rates?|pricing|interest|apr|apy', src, re.I) for src in loaders):
        return False
    if not re.search(r'interest\s+rate|annual\s+percentage|\b(?:APR|APY)\b', html, re.I):
        return False
    marker = r'\b(?:id|class|data-[\w-]+)\s*=\s*["\'][^"\']*(?:rates?[_-]|pricing[_-])[^"\']*["\']'
    for match in re.finditer(r'<(?:div|tbody)\b([^>]{0,1500})>\s*</(?:div|tbody)>', html, re.I):
        if re.search(marker, match[1], re.I):
            return True
    for match in re.finditer(r'<tr\b([^>]{0,1500})>(.{0,3000}?)</tr>', html, re.I | re.S):
        if (re.search(marker, match[1], re.I)
                and re.fullmatch(r'\s*<th\b[^>]*>.+?</th>\s*', match[2], re.I | re.S)
                and not re.search(r'<td\b', match[2], re.I)):
            return True
    return False
