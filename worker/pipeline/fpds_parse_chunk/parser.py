from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO
import re

from bs4 import BeautifulSoup
from pypdf import PdfReader

from .models import ParsedArtifact, ParsedSegment

PARSER_NAME = "fpds-parse-chunk"
PARSER_VERSION = "fpds-parse-chunk-v1"
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
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "noscript", "svg"]):
        tag.decompose()

    container = soup.find("main") or soup.body or soup
    sections = _extract_html_sections(container)
    if not sections:
        fallback_text = _normalize_text(container.get_text("\n", strip=True))
        if fallback_text:
            sections = [_RawSegment(anchor_type="section", anchor_value="document", page_no=None, text=fallback_text)]

    full_text, segments = _finalize_segments(sections)
    if not full_text.strip():
        raise ValueError("HTML parser produced no usable text.")

    parser_metadata = {
        "parser_name": PARSER_NAME,
        "content_type": "text/html",
        "section_count": len(segments),
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


def _extract_html_sections(container: BeautifulSoup) -> list[_RawSegment]:
    sections: list[_RawSegment] = []
    current_title: str | None = None
    current_lines: list[str] = []
    last_line: str | None = None

    def flush_section() -> None:
        nonlocal current_lines, current_title
        text_lines = [line for line in current_lines if line]
        if not text_lines:
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

    for tag in container.find_all(["h1", "h2", "h3", "h4", "h5", "h6", "p", "li", "td", "th"], recursive=True):
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
