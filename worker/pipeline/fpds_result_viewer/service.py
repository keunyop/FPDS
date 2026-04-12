from __future__ import annotations

from datetime import UTC, datetime

_HIGHLIGHT_FIELD_ORDER = (
    "status",
    "monthly_fee",
    "fee_waiver_condition",
    "standard_rate",
    "promotional_rate",
    "public_display_rate",
    "public_display_fee",
    "minimum_balance",
    "minimum_deposit",
    "term_length_days",
    "interest_payment_frequency",
    "eligibility_text",
    "notes",
    "last_verified_at",
)
_FIELD_LABELS = {
    "status": "Status",
    "monthly_fee": "Monthly Fee",
    "fee_waiver_condition": "Fee Waiver",
    "standard_rate": "Standard Rate",
    "promotional_rate": "Promo Rate",
    "public_display_rate": "Public Rate",
    "public_display_fee": "Public Fee",
    "minimum_balance": "Minimum Balance",
    "minimum_deposit": "Minimum Deposit",
    "term_length_days": "Term Length",
    "interest_payment_frequency": "Interest Payout",
    "eligibility_text": "Eligibility",
    "notes": "Notes",
    "last_verified_at": "Last Verified",
}


class ResultViewerPayloadService:
    def build_payload(
        self,
        *,
        run_overview: dict[str, object],
        candidate_rows: list[dict[str, object]],
        source_id_by_document_id: dict[str, str],
        generated_at: str | None = None,
    ) -> dict[str, object]:
        generated_at = generated_at or datetime.now(UTC).isoformat()
        candidates = [
            self._build_candidate_payload(
                candidate_row=item,
                source_id=source_id_by_document_id.get(str(item.get("source_document_id")), None),
            )
            for item in candidate_rows
        ]
        metrics = {
            "candidate_count": len(candidates),
            "pass_count": sum(1 for item in candidates if item["validation_status"] == "pass"),
            "warning_count": sum(1 for item in candidates if item["validation_status"] == "warning"),
            "error_count": sum(1 for item in candidates if item["validation_status"] == "error"),
            "review_queued_count": sum(1 for item in candidates if item["review_task_id"]),
            "evidence_link_count": sum(len(item["evidence_links"]) for item in candidates),
            "average_confidence": round(
                sum(float(item["source_confidence"]) for item in candidates) / len(candidates),
                4,
            )
            if candidates
            else 0.0,
        }
        return {
            "viewer_version": "fpds-prototype-viewer-v1",
            "generated_at": generated_at,
            "run": {
                **run_overview,
                "source_ids": list(run_overview.get("run_metadata", {}).get("source_ids", [])),
                "routing_mode": run_overview.get("run_metadata", {}).get("routing_mode"),
            },
            "metrics": metrics,
            "candidates": candidates,
        }

    def build_payload_js(self, *, payload: dict[str, object]) -> str:
        return "window.FPDS_VIEWER_PAYLOAD = " + _json_dumps(payload) + ";\n"

    def _build_candidate_payload(
        self,
        *,
        candidate_row: dict[str, object],
        source_id: str | None,
    ) -> dict[str, object]:
        candidate_payload = dict(candidate_row.get("candidate_payload", {}))
        evidence_links = [self._build_evidence_payload(item) for item in candidate_row.get("evidence_links", [])]
        highlight_fields = []
        for field_name in _HIGHLIGHT_FIELD_ORDER:
            value = candidate_payload.get(field_name)
            if value in {None, ""}:
                continue
            highlight_fields.append(
                {
                    "field_name": field_name,
                    "label": _FIELD_LABELS.get(field_name, _titleize(field_name)),
                    "value": value,
                }
            )
        if not highlight_fields:
            for field_name, value in candidate_payload.items():
                if value in {None, ""}:
                    continue
                highlight_fields.append(
                    {
                        "field_name": field_name,
                        "label": _FIELD_LABELS.get(field_name, _titleize(field_name)),
                        "value": value,
                    }
                )

        return {
            "source_id": source_id,
            "review_task_id": candidate_row.get("review_task_id"),
            "review_state": candidate_row.get("review_state"),
            "queue_reason_code": candidate_row.get("queue_reason_code"),
            "issue_summary": list(candidate_row.get("issue_summary", [])),
            "candidate_id": candidate_row.get("candidate_id"),
            "run_id": candidate_row.get("run_id"),
            "source_document_id": candidate_row.get("source_document_id"),
            "bank_code": candidate_row.get("bank_code"),
            "bank_name": candidate_row.get("bank_name") or candidate_row.get("bank_code"),
            "country_code": candidate_row.get("country_code"),
            "product_family": candidate_row.get("product_family"),
            "product_type": candidate_row.get("product_type"),
            "subtype_code": candidate_row.get("subtype_code"),
            "product_name": candidate_row.get("product_name"),
            "source_language": candidate_row.get("source_language"),
            "currency": candidate_row.get("currency"),
            "candidate_state": candidate_row.get("candidate_state"),
            "validation_status": candidate_row.get("validation_status"),
            "source_confidence": float(candidate_row.get("source_confidence", 0.0)),
            "review_reason_code": candidate_row.get("review_reason_code"),
            "validation_issue_codes": list(candidate_row.get("validation_issue_codes", [])),
            "candidate_payload": candidate_payload,
            "field_mapping_metadata": dict(candidate_row.get("field_mapping_metadata", {})),
            "highlight_fields": highlight_fields,
            "source_context": {
                "source_url": candidate_row.get("source_url"),
                "source_type": candidate_row.get("source_type"),
                "source_metadata": dict(candidate_row.get("source_metadata", {})),
                "snapshot_id": candidate_row.get("snapshot_id"),
                "fetched_at": candidate_row.get("fetched_at"),
                "parsed_document_id": candidate_row.get("parsed_document_id"),
                "parse_quality_note": candidate_row.get("parse_quality_note"),
                "stage_status": candidate_row.get("stage_status"),
                "warning_count": candidate_row.get("warning_count"),
                "error_count": candidate_row.get("error_count"),
                "error_summary": candidate_row.get("error_summary"),
                "runtime_notes": list(candidate_row.get("runtime_notes", [])),
            },
            "evidence_links": evidence_links,
            "evidence_field_count": len({item["field_name"] for item in evidence_links}),
        }

    @staticmethod
    def _build_evidence_payload(evidence_row: dict[str, object]) -> dict[str, object]:
        return {
            "field_name": evidence_row.get("field_name"),
            "label": _FIELD_LABELS.get(str(evidence_row.get("field_name")), _titleize(str(evidence_row.get("field_name")))),
            "candidate_value": evidence_row.get("candidate_value"),
            "citation_confidence": float(evidence_row.get("citation_confidence", 0.0)),
            "evidence_chunk_id": evidence_row.get("evidence_chunk_id"),
            "evidence_excerpt": evidence_row.get("evidence_excerpt"),
            "anchor_type": evidence_row.get("anchor_type"),
            "anchor_value": evidence_row.get("anchor_value"),
            "page_no": evidence_row.get("page_no"),
            "chunk_index": evidence_row.get("chunk_index"),
            "anchor_label": evidence_row.get("anchor_label"),
        }


def _titleize(field_name: str) -> str:
    return field_name.replace("_", " ").strip().title()


def _json_dumps(payload: dict[str, object]) -> str:
    import json

    return json.dumps(payload, indent=2, ensure_ascii=True)

