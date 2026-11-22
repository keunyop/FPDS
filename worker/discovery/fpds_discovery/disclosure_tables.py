"""Read paired product-name/document columns without borrowing a neighbouring offer."""
import re

from bs4 import BeautifulSoup


def disclosure_labels(html: str) -> dict[tuple[str, str], str]:
    if "商品名" not in html or "説明書" not in html:
        return {}
    soup = BeautifulSoup(html, "html.parser")
    labels = {}
    ambiguous = set()
    for table in soup.find_all("table"):
        rows = table.select(":scope > tr, :scope > tbody > tr, :scope > thead > tr")
        if not rows:
            continue
        heads = [cell.get_text(strip=True) for cell in rows[0].find_all(["td", "th"], recursive=False)]
        if not heads or heads != ["商品名", "説明書"] * (len(heads) // 2):
            continue
        for row in rows[1:]:
            cells = row.find_all(["td", "th"], recursive=False)
            if len(cells) != len(heads) or any(c.has_attr("rowspan") or c.has_attr("colspan") for c in cells):
                continue
            for name_cell, document_cell in zip(cells[::2], cells[1::2]):
                links = document_cell.select("a[href]")
                name = " ".join(name_cell.stripped_strings)
                if len(links) != 1 or not name or name_cell.find(["table", "a"]) or document_cell.find("table"):
                    continue
                size = links[0].get_text(" ", strip=True)
                if not re.fullmatch(r"[\d,.]+\s*(?:KB|MB)", size, re.I):
                    continue
                key = (links[0]["href"], size)
                if key in labels and labels[key] != name:
                    ambiguous.add(key)
                labels[key] = name
    return {key: name for key, name in labels.items() if key not in ambiguous}
