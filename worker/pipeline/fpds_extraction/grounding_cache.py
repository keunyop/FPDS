"""Bounded private grounding reuse; never substitutes for fresh capture or validation."""
from dataclasses import asdict
from datetime import UTC, datetime
from hashlib import sha256
import json
from pathlib import Path

from worker.pipeline.fpds_ai_runtime import configured_model_id
from .models import ExtractedFieldCandidate


def input_digest(context, candidates, requested_fields, collected_fields, *, day=None):
    root = Path(__file__).resolve().parents[1]
    files = [root / name for name in (
        "fpds_extraction/service.py", "fpds_extraction/grounding_cache.py",
        "fpds_field_contract.py", "fpds_collection_accuracy.py", "fpds_market_profile.py", "fpds_approval_policy.py",
        "fpds_comparison_instructions.py", "fpds_ai_runtime.py", "fpds_rate_safety.py",
        "../country_defaults.py")]
    value = {"version": 1, "day": day or datetime.now(UTC).date().isoformat(),
        "model": configured_model_id(), "code": [sha256(p.read_bytes()).hexdigest() for p in files],
        "context": asdict(context), "candidates": [asdict(c) for c in candidates],
        "requested_fields": requested_fields, "collected_fields": [f.to_dict() for f in collected_fields]}
    return sha256(json.dumps(value, sort_keys=True, ensure_ascii=True, allow_nan=False).encode()).hexdigest()


def grounded_with_reuse(*, object_store, storage_config, run_id, context, candidates,
                        requested_fields, collected_fields, extract):
    # Missing currency text does not block grounding of actual product facts.
    # The shared validator resolves and records the country default afterward.
    key = storage_config._join_key(storage_config.env_prefix, storage_config.extraction_object_prefix,
        context.country_code, context.bank_code, context.source_document_id, "grounding-cache.json")
    fingerprint = input_digest(context, candidates, requested_fields, collected_fields)
    try:
        raw = object_store.get_object_bytes(object_key=key)
        if len(raw) > 2_000_000:
            raise ValueError("Oversize grounding cache")
        cached = json.loads(raw)
        if cached.get("fingerprint") == fingerprint and cached.get("origin_run_id"):
            fields = [ExtractedFieldCandidate(**v) for v in cached["fields"]]
            chunks = {c.evidence_chunk_id: c for c in candidates}
            for field in fields:
                chunk = chunks.get(field.evidence_chunk_id)
                if (chunk is None or field.source_document_id != context.source_document_id
                    or field.source_snapshot_id != context.snapshot_id
                    or field.evidence_text_excerpt != chunk.evidence_excerpt):
                    raise ValueError("Cached field provenance mismatch")
            usage = {**cached["usage"], "prompt_tokens": 0, "completion_tokens": 0,
                "provider_request_id": None, "reused": True,
                "origin_run_id": cached["origin_run_id"], "cache_fingerprint": fingerprint}
            return fields, [*cached["notes"], "Reused unchanged same-day grounding; all current validation gates still apply."], usage
    except Exception:
        # Missing/expired/corrupt/private storage unavailable: normal grounded extraction.
        pass
    fields, notes, usage = extract(context=context, candidates=candidates,
        requested_fields=requested_fields, collected_fields=collected_fields)
    if usage is not None:
        cache = {"fingerprint": fingerprint, "origin_run_id": run_id,
                 "fields": [f.to_dict() for f in fields], "notes": notes, "usage": usage}
        try:
            object_store.put_object_bytes(object_key=key,
                data=json.dumps(cache, ensure_ascii=True, allow_nan=False).encode(), content_type="application/json")
        except Exception:
            notes = [*notes, "Grounding reuse cache unavailable; current extraction is preserved."]
    return fields, notes, usage
