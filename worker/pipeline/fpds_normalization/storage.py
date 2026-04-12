from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from worker.pipeline.fpds_parse_chunk.storage import (
    AwsCliS3ObjectStore,
    FilesystemObjectStore,
    ParseChunkObjectStore,
)


@dataclass(frozen=True)
class NormalizationStorageConfig:
    driver: str
    env_prefix: str
    normalization_object_prefix: str
    retention_class: str
    bucket: str | None = None
    endpoint: str | None = None
    region: str | None = None
    filesystem_root: str | None = None

    @classmethod
    def from_env(cls) -> "NormalizationStorageConfig":
        return cls(
            driver=os.getenv("FPDS_OBJECT_STORAGE_DRIVER", "s3-compatible"),
            env_prefix=os.getenv("FPDS_OBJECT_STORAGE_PREFIX", os.getenv("FPDS_EVIDENCE_PREFIX_ROOT", "dev")),
            normalization_object_prefix=os.getenv("FPDS_NORMALIZED_OBJECT_PREFIX", "normalized"),
            retention_class=os.getenv("FPDS_EVIDENCE_RETENTION_CLASS", "hot"),
            bucket=os.getenv("FPDS_OBJECT_STORAGE_BUCKET"),
            endpoint=os.getenv("FPDS_OBJECT_STORAGE_ENDPOINT"),
            region=os.getenv("FPDS_OBJECT_STORAGE_REGION"),
            filesystem_root=os.getenv(
                "FPDS_NORMALIZED_FILESYSTEM_ROOT",
                os.getenv("FPDS_EXTRACTION_FILESYSTEM_ROOT", os.getenv("FPDS_PARSED_FILESYSTEM_ROOT", os.getenv("FPDS_SNAPSHOT_FILESYSTEM_ROOT"))),
            ),
        )

    def build_normalized_object_key(
        self,
        *,
        country_code: str,
        bank_code: str,
        source_document_id: str,
        candidate_id: str,
    ) -> str:
        return self._join_key(
            self.env_prefix,
            self.normalization_object_prefix,
            country_code,
            bank_code,
            source_document_id,
            candidate_id,
            "normalized.json",
        )

    def build_metadata_object_key(
        self,
        *,
        country_code: str,
        bank_code: str,
        source_document_id: str,
        candidate_id: str,
    ) -> str:
        return self._join_key(
            self.env_prefix,
            self.normalization_object_prefix,
            country_code,
            bank_code,
            source_document_id,
            candidate_id,
            "metadata.json",
        )

    @staticmethod
    def _join_key(*parts: str) -> str:
        return "/".join(part.strip("/").strip() for part in parts if part and part.strip("/").strip())


def build_object_store(config: NormalizationStorageConfig) -> ParseChunkObjectStore:
    driver = config.driver.lower()
    if driver == "filesystem":
        if not config.filesystem_root:
            raise ValueError("filesystem normalization storage requires a configured filesystem root")
        return FilesystemObjectStore(root_dir=Path(config.filesystem_root))
    if driver in {"s3-compatible", "s3"}:
        if not config.bucket:
            raise ValueError("s3-compatible normalization storage requires FPDS_OBJECT_STORAGE_BUCKET")
        return AwsCliS3ObjectStore(bucket=config.bucket, region=config.region, endpoint=config.endpoint)
    raise ValueError(f"Unsupported normalization storage driver: {config.driver}")
