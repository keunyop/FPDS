"""Dated discovery leads. Only a fresh matching bank listing can select a document."""
import csv
import re
import unicodedata
from functools import lru_cache
from pathlib import Path
from urllib.parse import urlparse

from .discovery import extract_links
from worker.source_content_validity import html_unavailable_reason
from .url_utils import normalize_source_url


LISTINGS = Path(__file__).resolve().parents[1] / "data" / "jp_higo_kagoshima_listings.csv"
ISSUERS = {"HIGO": ("肥後銀行", "www.higobank.co.jp"), "KAGOSHIMA": ("鹿児島銀行", "www.kagin.co.jp")}
KIND_TERMS = {"chequing": ("普通預金", "当座預金"), "savings": ("貯蓄預金",),
              "gic": ("定期預金",), "mortgage": ("住宅ローン", "ホームローン"),
              "personal-loan": ("フリーローン", "マイカーローン"), "line-of-credit": ("カードローン",),
              "business-loan": ("事業者ローン",), "business-line-of-credit": ("事業者カードローン",)}


def _new_named_kind(name, kind):
    if kind in {"mortgage", "personal-loan", "line-of-credit"} and re.search(r"事業者|事業資金|法人", name):
        return False
    matches = {code for code, terms in KIND_TERMS.items() if any(term in name for term in terms)}
    if "business-line-of-credit" in matches:
        matches.discard("line-of-credit")
    return matches == {kind} and not re.search(r"媒介|取次|仕組|スワップ|先物予約|新規.*(?:終了|中止)|一覧", name)


@lru_cache(maxsize=1)
def listed_documents():
    with LISTINGS.open(encoding="utf-8", newline="") as source:
        return tuple(csv.DictReader(source))


def disclosure_indexes(bank_code, kind, coverage_url):
    urls = list(dict.fromkeys(row["index_url"] for row in listed_documents()
                              if row["bank_code"] == bank_code and row["discovery_type"] == kind
                              and row["disposition"] == "listed"))
    if not coverage_url or not any(normalize_source_url(u) == normalize_source_url(coverage_url) for u in urls):
        return []
    return [url for url in urls if urlparse(url).hostname == urlparse(coverage_url).hostname]


def current_disclosures(*, bank_code, product_type, index_url, html):
    rows = [row for row in listed_documents() if row["bank_code"] == bank_code
            and row["discovery_type"] == product_type and row["disposition"] == "listed"
            and normalize_source_url(row["index_url"]) == normalize_source_url(index_url)]
    if not rows:
        return []
    expected = {(row["document_url"], row["listing_label_ja"]) for row in rows}
    known_urls = {row["document_url"] for row in listed_documents() if row["bank_code"] == bank_code}
    links = extract_links(html, base_url=index_url)
    host = urlparse(index_url).hostname
    labels_by_url = {}
    for link in links:
        if link.source_type == "pdf":
            labels_by_url.setdefault(link.resolved_url, set()).add(link.anchor_text)
    return [link for link in links if link.source_type == "pdf"
            and ((link.resolved_url, link.anchor_text) in expected or (
                link.resolved_url not in known_urls and _new_named_kind(link.anchor_text, product_type)))
            and len(labels_by_url[link.resolved_url]) == 1
            and urlparse(link.resolved_url).hostname == host]


def name_key(name):
    value = re.sub(r"\s+", "", unicodedata.normalize("NFKC", name))
    # The directory puts the repayment-account variant in parentheses.
    return re.sub(r"\((返済用口座(?:不要型|引落型))\)$", r"\1", value)


def confirmed_product(bank_code, kind, name, detail_url, evidence):
    """Check the actual detail's name/issuer and its independently indexed scope."""
    issuer, host = ISSUERS[bank_code]
    if not detail_url.startswith("https://") or urlparse(detail_url).hostname not in {host, host.removeprefix("www.")}:
        return False
    path = normalize_source_url(detail_url)
    def same_document(url):
        try:
            return (str(url).startswith("https://") and
                    normalize_source_url(str(url)).replace("://www.", "://") == path.replace("://www.", "://"))
        except ValueError:
            return False
    known = [row for row in listed_documents() if row["bank_code"] == bank_code and same_document(row["document_url"])]
    indexed = {name_key(row["listing_label_ja"]) for row in known
               if row["discovery_type"] == kind and row["disposition"] == "listed"}
    proposed = name_key(name)
    if not proposed or (known and indexed != {proposed}):
        return False
    own = "\n".join(str(chunk.get("evidence_excerpt") or "") for chunk in evidence
                    if chunk.get("source_url") and same_document(chunk["source_url"]))
    if not any(name_key(line) in {issuer, "株式会社" + issuer} for line in own.splitlines()):
        return False
    for line in own.splitlines():
        if proposed in name_key(line) and re.search(r"新規(?:のお?取り?扱い|申込受付)(?:は)?(?:終了|中止)", line):
            return False
    names = {name_key(m[1]) for m in re.finditer(
        r"(?m)^\s*(?:[0-9０-９]+[．.]\s*)?商品名[ \t　:：]+([^\r\n]+)", own)}
    if names and names != {proposed}:
        return False
    # A new disclosure can establish its scope without a dated inventory row.
    # Require the actual named product, a bank-issued document and a specific kind.
    if not known:
        if (not names or "商品概要説明書" not in own or not _new_named_kind(proposed, kind)
                or re.search(r"媒介|取次|仕組預金|仕組み預金|スワップ|先物予約|新規.*(?:終了|中止)", own)):
            return False
    return bool(names) or any(name_key(line) == proposed for line in own.splitlines())


def check_capture_listings(sources, policy, fetcher):
    """Recheck listed PDF leads on subsequent ordinary Runs, once per index."""
    from .fetch import fetch_response
    documents = {}
    errors = {}
    fetched = {}
    for source in sources:
        meta = source.source_metadata.get("discovery_metadata") or {}
        if not isinstance(meta, dict) or meta.get("selection_path") != "named_official_disclosure":
            continue
        url = meta.get("listing_url")
        kind = source.source_metadata.get("product_type")
        key = (source.bank_code, kind, url)
        if not any(row["bank_code"] == source.bank_code and row["index_url"] == url
                   and row["discovery_type"] == kind for row in listed_documents()):
            errors[source.source_id] = "Unregistered product disclosure index"
            continue
        if url not in fetched:
            try:
                response = (fetcher or fetch_response)(url, policy)
                if (normalize_source_url(response.final_url) != normalize_source_url(url)
                        or not response.content_type.startswith("text/html") or not 200 <= response.status_code < 300):
                    raise ValueError("Unexpected index destination or media type")
                reason = html_unavailable_reason(response.body)
                if reason:
                    raise ValueError(reason)
                fetched[url] = response
            except Exception as exc:
                fetched[url] = str(exc)
        response = fetched[url]
        if isinstance(response, str):
            errors[source.source_id] = "Official product disclosure index unavailable: " + response[:300]
            continue
        if key not in documents:
            documents[key] = {(link.resolved_url, link.anchor_text) for link in current_disclosures(
                bank_code=source.bank_code, product_type=kind, index_url=url,
                html=response.body.decode("utf-8", errors="replace"))}
        if (source.resolved_url, meta.get("listing_name")) not in documents[key]:
            errors[source.source_id] = "Current official index does not confirm this product disclosure"
    return errors, {url: response for url, response in fetched.items() if not isinstance(response, str)}
