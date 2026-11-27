"""Owned numbered sections in Japanese bank product disclosures."""
import re
import unicodedata


def annual_limit_tiers(value):
    """Return the validated rate rows in JPY and annual percentage points."""
    text = unicodedata.normalize("NFKC", value)
    if "お借入利率(年利)" not in text or "金利改定ルール" not in text:
        return []
    match = re.search(r"ご利用限度額\s+金利\s*\n(.*?)\n8[.]\s*金利改定ルール", text, re.S)
    if not match:
        return []
    rows = match[1].splitlines()
    previous = None
    tiers = []
    for index, row in enumerate(rows):
        tier = re.fullmatch(r"\s*(?:(\d[\d,]*)\s*万円超)?\s*(?:(\d[\d,]*)\s*万円以下)?\s+(\d+(?:\.\d+)?)\s*%\s*", row)
        if not tier:
            return []
        low, high = (int(x.replace(",", "")) if x else None for x in tier.groups()[:2])
        if (low != previous or (high is None) != (index == len(rows) - 1)
                or (high is not None and high <= (low or 0))):
            return []
        previous = high
        tiers.append((low * 10000 if low is not None else None,
                      high * 10000 if high is not None else None, tier[3]))
    return tiers if len(rows) >= 2 and "変動金利" in text and "上限金利" in text else []


def annual_limit_schedule(value):
    return bool(annual_limit_tiers(value))


def numbered_sections(pages):
    """Emit records only from one complete, unambiguous disclosed credit line."""
    if not pages or "商品概要説明書" not in pages[0]:
        return []
    sections = {}
    for number, page in enumerate(pages, 1):
        hits = list(re.finditer(r"(?m)^([０-９0-9]{1,2})[．.][ \t]*(?=[^\d\s])", page))
        for index, hit in enumerate(hits):
            key = int(hit[1])
            if key in sections:
                return []
            end = hits[index + 1].start() if index + 1 < len(hits) else len(page)
            sections[key] = (number, page[hit.start():end].strip())
    if not {1, 2, 3, 4, 5, 6, 7, 8, 9, 13, 14} <= sections.keys():
        return []
    name = re.fullmatch(r"[０-９0-9]+[．.]\s*商品名[ \t　]+([^\n]+)", sections[1][1])
    if not name or "カードローン" not in name[1] or not re.search(r"(?m)^株式会社\s*鹿児島銀行$", pages[0]):
        return []
    name = name[1].strip()
    heading = pages[0][:pages[0].index(sections[1][1]) + len(sections[1][1])].strip()
    records = [("jp_disclosure_identity", name, 1, heading)]
    for key, label, anchor in ((2, "ご利用限度額", "jp_disclosure_limit"),
                               (5, "ご利用いただける方", "jp_disclosure_eligibility"),
                               (9, "お利息の計算方法", "jp_disclosure_calculation"),
                               (13, "担保・保証人", "jp_disclosure_security")):
        number, excerpt = sections[key]
        if re.match(r"[０-９0-9]+[．.]\s*" + label, excerpt):
            records.append((anchor, name, number, excerpt))
    schedule = sections[4][1] + "\n" + sections[8][1]
    if sections[4][0] == sections[8][0] and annual_limit_schedule(schedule):
        records.append(("jp_disclosure_annual_rates", name, sections[4][0], schedule))
    return records
