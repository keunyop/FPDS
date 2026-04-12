from __future__ import annotations

import os
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol


@dataclass(frozen=True)
class ParseChunkStorageConfig:
    driver: str
    env_prefix: str
    snapshot_object_prefix: str
    parsed_object_prefix: str
    retention_class: str
    bucket: str | None = None
    endpoint: str | None = None
    region: str | None = None
    filesystem_root: str | None = None

    @classmethod
    def from_env(cls) -> "ParseChunkStorageConfig":
        return cls(
            driver=os.getenv("FPDS_OBJECT_STORAGE_DRIVER", "s3-compatible"),
            env_prefix=os.getenv("FPDS_OBJECT_STORAGE_PREFIX", os.getenv("FPDS_EVIDENCE_PREFIX_ROOT", "dev")),
            snapshot_object_prefix=os.getenv("FPDS_SNAPSHOT_OBJECT_PREFIX", "snapshots"),
            parsed_object_prefix=os.getenv("FPDS_PARSED_OBJECT_PREFIX", "parsed"),
            retention_class=os.getenv("FPDS_EVIDENCE_RETENTION_CLASS", "hot"),
            bucket=os.getenv("FPDS_OBJECT_STORAGE_BUCKET"),
            endpoint=os.getenv("FPDS_OBJECT_STORAGE_ENDPOINT"),
            region=os.getenv("FPDS_OBJECT_STORAGE_REGION"),
            filesystem_root=os.getenv("FPDS_PARSED_FILESYSTEM_ROOT", os.getenv("FPDS_SNAPSHOT_FILESYSTEM_ROOT")),
        )

    def build_parsed_text_object_key(
        self,
        *,
        country_code: str,
        bank_code: str,
        source_document_id: str,
        parsed_document_id: str,
    ) -> str:
        return self._join_key(
            self.env_prefix,
            self.parsed_object_prefix,
            country_code,
            bank_code,
            source_document_id,
            parsed_document_id,
            "parsed.txt",
        )

    def build_parsed_metadata_object_key(
        self,
        *,
        country_code: str,
        bank_code: str,
        source_document_id: str,
        parsed_document_id: str,
    ) -> str:
        return self._join_key(
            self.env_prefix,
            self.parsed_object_prefix,
            country_code,
            bank_code,
            source_document_id,
            parsed_document_id,
            "metadata.json",
        )

    @staticmethod
    def _join_key(*parts: str) -> str:
        return "/".join(part.strip("/").strip() for part in parts if part and part.strip("/").strip())


class ParseChunkObjectStore(Protocol):
    def get_object_bytes(self, *, object_key: str) -> bytes:
        ...

    def put_object_bytes(self, *, object_key: str, data: bytes, content_type: str) -> None:
        ...


@dataclass
class FilesystemObjectStore:
    root_dir: Path

    def get_object_bytes(self, *, object_key: str) -> bytes:
        target = self.root_dir / Path(object_key.replace("/", os.sep))
        return target.read_bytes()

    def put_object_bytes(self, *, object_key: str, data: bytes, content_type: str) -> None:
        target = self.root_dir / Path(object_key.replace("/", os.sep))
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)


@dataclass
class AwsCliS3ObjectStore:
    bucket: str
    region: str | None = None
    endpoint: str | None = None

    def get_object_bytes(self, *, object_key: str) -> bytes:
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp_path = Path(tmp.name)

        try:
            command = [
                "aws",
                "s3api",
                "get-object",
                "--bucket",
                self.bucket,
                "--key",
                object_key,
                str(tmp_path),
            ]
            if self.region:
                command.extend(["--region", self.region])
            if self.endpoint:
                command.extend(["--endpoint-url", self.endpoint])
            completed = subprocess.run(command, capture_output=True, text=True, check=False)
            if completed.returncode != 0:
                stderr = completed.stderr.strip() or completed.stdout.strip() or "unknown aws error"
                raise RuntimeError(f"AWS CLI get-object failed: {stderr}")
            return tmp_path.read_bytes()
        finally:
            tmp_path.unlink(missing_ok=True)

    def put_object_bytes(self, *, object_key: str, data: bytes, content_type: str) -> None:
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(data)
            tmp_path = Path(tmp.name)

        try:
            command = [
                "aws",
                "s3api",
                "put-object",
                "--bucket",
                self.bucket,
                "--key",
                object_key,
                "--body",
                str(tmp_path),
                "--content-type",
                content_type,
            ]
            if self.region:
                command.extend(["--region", self.region])
            if self.endpoint:
                command.extend(["--endpoint-url", self.endpoint])
            completed = subprocess.run(command, capture_output=True, text=True, check=False)
            if completed.returncode != 0:
                stderr = completed.stderr.strip() or completed.stdout.strip() or "unknown aws error"
                raise RuntimeError(f"AWS CLI put-object failed: {stderr}")
        finally:
            tmp_path.unlink(missing_ok=True)


def build_object_store(config: ParseChunkStorageConfig) -> ParseChunkObjectStore:
    driver = config.driver.lower()
    if driver == "filesystem":
        if not config.filesystem_root:
            raise ValueError("filesystem parse storage requires FPDS_PARSED_FILESYSTEM_ROOT or FPDS_SNAPSHOT_FILESYSTEM_ROOT")
        return FilesystemObjectStore(root_dir=Path(config.filesystem_root))
    if driver in {"s3-compatible", "s3"}:
        if not config.bucket:
            raise ValueError("s3-compatible parse storage requires FPDS_OBJECT_STORAGE_BUCKET")
        return AwsCliS3ObjectStore(bucket=config.bucket, region=config.region, endpoint=config.endpoint)
    raise ValueError(f"Unsupported parse storage driver: {config.driver}")
