from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO
import re

from bs4 import BeautifulSoup
from pypdf import PdfReader

from worker.discovery.fpds_discovery.discovery import extract_structured_text_sections

from .models import ParsedArtifact, ParsedSegment

PARSER_NAME = "fpds-parse-chunk"
PARSER_VERSION = "fpds-parse-chunk-v5"
_WHITESPACE_RE = re.compile(r"[ \t\r\f\v]+")


@dataclass(frozen=True)
class _RawSegment:
    anchor_type: str
    anchor_value: str | None
    page_no: int | None
    text: str


def parse_snapshot_bytes(*, body: bytes, content_type: str) -> ParsedArtifact:
    normalized_content_type = content_type.lower().strip()
    if normalized_content_type.startswith("text/html"):
        return _parse_html(body)
    if normalized_content_type.startswith("application/pdf") or body.startswith(b"%PDF"):
        return _parse_pdf(body)
    raise ValueError(f"Unsupported snapshot content type for parsing: {content_type}")


def _parse_html(body: bytes) -> ParsedArtifact:
    html = body.decode("utf-8", errors="replace")
    structured_sections = extract_structured_text_sections(html)
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "noscript", "svg"]):
        tag.decompose()
    for image in soup.find_all("img"):
        alt_text = _normalize_text(str(image.get("alt") or ""))
        if image.find_parent("table") is not None and alt_text.casefold() in {"check", "x"}:
            # Comparison tables often encode boolean product conditions only
            # as accessible Check/X images. Preserve those meanings in the
            # evidence stream instead of silently dropping the table values.
            image.replace_with(alt_text)

    sections: list[_RawSegment] = []
    fallback_text = ""
    for container in _html_parse_containers(soup):
        sections = _extract_html_sections(container)
        fallback_text = _normalize_text(container.get_text("\n", strip=True))
        if sections or fallback_text:
            break
    if not sections and fallback_text:
        sections = [_RawSegment(anchor_type="section", anchor_value="document", page_no=None, text=fallback_text)]
    if not sections:
        document_title = _normalize_text((soup.title.get_text(" ", strip=True) if soup.title else ""))
        if document_title:
            sections = [_RawSegment(anchor_type="section", anchor_value="document", page_no=None, text=document_title)]
    sections.extend(
        _RawSegment(
            anchor_type="structured_component",
            anchor_value=f"structured-component-{index}",
            page_no=None,
            text=text,
        )
        for index, text in enumerate(structured_sections, start=1)
    )

    sections.extend(_rate_table_evidence_sections(soup))
    full_text, segments = _finalize_segments(sections)
    if not full_text.strip():
        raise ValueError("HTML parser produced no usable text.")

    parser_metadata = {
        "parser_name": PARSER_NAME,
        "content_type": "text/html",
        "section_count": len(segments),
        "structured_component_section_count": len(structured_sections),
        "partial_parse_flag": False,
    }
    return ParsedArtifact(
        parser_name=PARSER_NAME,
        parser_version=PARSER_VERSION,
        full_text=full_text,
        parse_quality_note=None,
        parser_metadata=parser_metadata,
        segments=segments,
    )


def _rate_table_evidence_sections(soup: BeautifulSoup) -> list[_RawSegment]:
    """Preserve structural row/header/notes relationships as captured evidence.

    Never synthesize rate labels or annual units. Only one pricing table may
    use document-wide Legal notes; multiple tables need explicit footnote links.
    Full original sections remain available alongside these scoped sections.
    """
    container = soup.find("main") or soup.body or soup
    tables = [t for t in container.find_all("table") if re.search(r"\d(?:\.\d+)?\s*%", t.get_text(" ", strip=True))]
    output = []
    for index, table in enumerate(tables):
        head = table.find("thead")
        column_headers = head.find_all("th") if head is not None else [t for t in table.find_all("th") if t.get("scope") == "col"]
        if not column_headers:
            first_row = table.find("tr")
            if first_row is not None and not first_row.find("td"):
                column_headers = first_row.find_all("th")
        headers = [t.get_text(" ", strip=True) for t in column_headers]
        caption = table.find("caption")
        if caption:
            headers.insert(0, caption.get_text(" ", strip=True))
        if not headers or not re.search(r"\b(?:rates?|APY|APR|interest|yield)\b", " ".join(headers), re.I):
            continue
        notes = []
        for link in table.find_all("a", href=True):
            href = str(link["href"])
            if href.startswith("#") and (target := soup.find(id=href[1:])) is not None:
                if target.find_parent("table") is None:
                    notes.append(target.get_text(" ", strip=True))
        if len(tables) == 1:
            for label in container.find_all(["h2", "h3", "h4", "button", "summary"]):
                if label.get_text(" ", strip=True).lower() not in {"legal", "rate notes", "rate disclosures", "terms and conditions"}:
                    continue
                target_id = label.get("aria-controls")
                target = soup.find(id=target_id) if target_id else label.find_next_sibling()
                if target is not None and target.find("table") is None:
                    notes.append(target.get_text(" ", strip=True))
        notes = list(dict.fromkeys(n for n in notes if n))
        rows = []
        for row in table.find_all("tr"):
            cells = row.find_all(["td", "th"], recursive=False)
            if row.find("td") is not None:
                rows.append("\n".join(c.get_text(" ", strip=True) for c in cells))
        # A maturity schedule retains all its rows and qualifications together.
        # Account tables instead preserve each product's own row.
        term_schedule = rows and all(re.search(r"^\d+\s+(?:days?|months?|years?)\b", r, re.I) for r in rows)
        groups = ["\n".join(rows)] if term_schedule else rows
        for row_index, row in enumerate(groups):
            text = "\n".join([*headers, row, *notes])
            if len(text) > 6400:
                continue  # Do not truncate conditions or create partial proof.
            output.append(_RawSegment("rate_table_schedule" if term_schedule else "rate_table_row",
                f"rate-table-{index}-row-{row_index}", None, text))
    return output


def _html_parse_containers(soup: BeautifulSoup) -> list[BeautifulSoup]:
    containers: list[BeautifulSoup] = []
    main = soup.find("main")
    if main is not None:
        containers.append(main)
    if soup.body is not None and soup.body not in containers:
        containers.append(soup.body)
    if soup not in containers:
        containers.append(soup)
    return containers


def _extract_html_sections(container: BeautifulSoup) -> list[_RawSegment]:
    sections: list[_RawSegment] = []
    current_title: str | None = None
    current_lines: list[str] = []
    last_line: str | None = None

    def flush_section() -> None:
        nonlocal current_lines, current_title
        text_lines = [line for line in current_lines if line]
        if not text_lines and not current_title:
            return
        section_title = current_title or "Document"
        section_text = "\n".join([section_title, *text_lines])
        sections.append(
            _RawSegment(
                anchor_type="section",
                anchor_value=_slugify(section_title),
                page_no=None,
                text=section_text,
            )
        )
        current_lines = []
        current_title = None

    semantic_tags = {"h1", "h2", "h3", "h4", "h5", "h6", "p", "li", "td", "th"}
    supplemental_tags = {"div", "span", "dt", "dd", "strong"}
    all_tags = semantic_tags | supplemental_tags
    for tag in container.find_all(sorted(all_tags), recursive=True):
        # Preserve leaf values used by modern rate cards without repeating text
        # already represented by a semantic or nested leaf element.
        if tag.name in supplemental_tags and tag.find(all_tags, recursive=True) is not None:
            continue
        text = _normalize_text(tag.get_text(" ", strip=True))
        if not text:
            continue
        if tag.name in {"h1", "h2", "h3", "h4", "h5", "h6"}:
            flush_section()
            current_title = text
            last_line = text
            continue
        if text == last_line:
            continue
        current_lines.append(text)
        last_line = text

    flush_section()
    return sections


def _parse_pdf(body: bytes) -> ParsedArtifact:
    reader = PdfReader(BytesIO(body))
    raw_segments: list[_RawSegment] = []
    empty_pages: list[int] = []

    for page_index, page in enumerate(reader.pages, start=1):
        text = _normalize_multiline_text(page.extract_text() or "")
        if not text:
            empty_pages.append(page_index)
            continue
        raw_segments.append(
            _RawSegment(
                anchor_type="page",
                anchor_value=f"page-{page_index}",
                page_no=page_index,
                text=text,
            )
        )

    full_text, segments = _finalize_segments(raw_segments)
    if not full_text.strip():
        raise ValueError("PDF parser produced no usable text.")

    parse_quality_note = None
    if empty_pages:
        parse_quality_note = f"Partial PDF parse: no text extracted from pages {', '.join(str(page) for page in empty_pages)}."

    parser_metadata = {
        "parser_name": PARSER_NAME,
        "content_type": "application/pdf",
        "page_count": len(reader.pages),
        "extracted_page_count": len(segments),
        "empty_page_numbers": empty_pages,
        "partial_parse_flag": bool(empty_pages),
    }
    return ParsedArtifact(
        parser_name=PARSER_NAME,
        parser_version=PARSER_VERSION,
        full_text=full_text,
        parse_quality_note=parse_quality_note,
        parser_metadata=parser_metadata,
        segments=segments,
    )


def _finalize_segments(raw_segments: list[_RawSegment]) -> tuple[str, list[ParsedSegment]]:
    parts: list[str] = []
    segments: list[ParsedSegment] = []
    cursor = 0
    delimiter = "\n\n"

    for raw_segment in raw_segments:
        text = raw_segment.text.strip()
        if not text:
            continue
        if parts:
            parts.append(delimiter)
            cursor += len(delimiter)
        start = cursor
        parts.append(text)
        cursor += len(text)
        segments.append(
            ParsedSegment(
                anchor_type=raw_segment.anchor_type,
                anchor_value=raw_segment.anchor_value,
                page_no=raw_segment.page_no,
                text=text,
                char_start=start,
                char_end=cursor,
            )
        )

    return "".join(parts), segments


def _normalize_text(value: str) -> str:
    return _WHITESPACE_RE.sub(" ", value).strip()


def _normalize_multiline_text(value: str) -> str:
    lines = [_normalize_text(line) for line in value.splitlines()]
    compact_lines = [line for line in lines if line]
    return "\n".join(compact_lines).strip()


def _slugify(value: str) -> str:
    lowered = value.lower()
    lowered = re.sub(r"[^a-z0-9]+", "-", lowered)
    return lowered.strip("-") or "section"
