from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import math
import os
import re

DEFAULT_VECTOR_DIMENSIONS = 64
DEFAULT_VECTOR_EMBEDDING_MODEL_ID = "fpds-hash-lexical-v1"
DEFAULT_VECTOR_EMBEDDING_SOURCE = "deterministic-lexical-bootstrap"

_TOKEN_RE = re.compile(r"[a-z0-9]+")


@dataclass(frozen=True)
class VectorEmbeddingConfig:
    namespace: str
    model_id: str
    dimensions: int = DEFAULT_VECTOR_DIMENSIONS
    source: str = DEFAULT_VECTOR_EMBEDDING_SOURCE

    @classmethod
    def from_env(cls) -> "VectorEmbeddingConfig":
        dimensions = int(os.getenv("FPDS_VECTOR_EMBEDDING_DIMENSIONS", str(DEFAULT_VECTOR_DIMENSIONS)))
        if dimensions != DEFAULT_VECTOR_DIMENSIONS:
            raise ValueError(
                "FPDS_VECTOR_EMBEDDING_DIMENSIONS must be 64 for the current pgvector bootstrap schema"
            )
        return cls(
            namespace=os.getenv("FPDS_VECTOR_NAMESPACE", "fpds-dev").strip() or "fpds-dev",
            model_id=os.getenv("FPDS_VECTOR_EMBEDDING_MODEL", DEFAULT_VECTOR_EMBEDDING_MODEL_ID).strip()
            or DEFAULT_VECTOR_EMBEDDING_MODEL_ID,
            dimensions=dimensions,
        )


def build_retrieval_embedding(value: str, *, dimensions: int = DEFAULT_VECTOR_DIMENSIONS) -> list[float]:
    if dimensions <= 0:
        raise ValueError("dimensions must be positive")

    vector = [0.0] * dimensions
    tokens = _TOKEN_RE.findall(value.lower())
    if not tokens:
        return vector

    for token in tokens:
        digest = sha256(token.encode("utf-8")).digest()
        index = int.from_bytes(digest[:4], "big") % dimensions
        sign = 1.0 if digest[4] % 2 == 0 else -1.0
        vector[index] += sign

    norm = math.sqrt(sum(item * item for item in vector))
    if norm == 0:
        return [0.0] * dimensions
    return [round(item / norm, 6) for item in vector]


def format_pgvector_literal(vector: list[float]) -> str:
    return "[" + ",".join(f"{item:.6f}" for item in vector) + "]"


def build_embedding_source_hash(value: str) -> str:
    normalized = " ".join(_TOKEN_RE.findall(value.lower()))
    return sha256(normalized.encode("utf-8")).hexdigest()


def build_evidence_chunk_embedding_id(
    *,
    evidence_chunk_id: str,
    namespace: str,
    model_id: str,
) -> str:
    digest = sha256(f"{evidence_chunk_id}|{namespace}|{model_id}".encode("utf-8")).hexdigest()[:16]
    return f"ece-{digest}"

