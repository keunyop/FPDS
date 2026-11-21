"""Offline verification of the applied D-090 cutover manifest and product versions.

The original one-time transaction is preserved in Git at 2eb1eb45fe78:scripts/maintenance/collection_accuracy_cutover.py.
"""
from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "api/service")]
from worker.pipeline.fpds_collection_accuracy import ACCURACY_VERSION, RECEIPT_KEY, payload_digest

OPERATION = "collection_accuracy_cutover_20260930"
APPROVED_MANIFEST_SHA256 = "1f79a61b737b1e25d35c94253b8f98e19135dcdb480034e3c499e234d0204f1c"
AUTHORIZATION = "Product Owner explicitly authorized 355 history-preserving product deactivations, 470 automatic review closures and legacy manual product-review API retirement on 2026-09-30, accepting an empty Public catalogue."


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def digest(value):
    return sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def load_manifest(path):
    raw = Path(path).read_bytes()
    require(sha256(raw).hexdigest() == APPROVED_MANIFEST_SHA256, "The approved manifest changed")
    manifest = json.loads(raw)
    require(manifest["count"] == 355 and manifest["accepted_count"] == 0, "Unexpected product scope")
    require(len(manifest["items"]) == len({i["product_id"] for i in manifest["items"]}) == 355, "Duplicate or missing product")
    reviews = manifest["legacy_review_tasks"]
    require(len(reviews) == len({i["review_task_id"] for i in reviews}) == 470, "Unexpected review scope")
    require({i["country_code"] for i in manifest["items"]} == {"CA", "US"}, "Unexpected country")
    require(all(i["assessment"]["accepted"] is False for i in manifest["items"]), "Accepted product included")
    return manifest


def prepare_product(cp, previous, item):
    require(cp["status"] == "active", "Product is no longer active: " + cp["product_id"])
    require(cp["current_version_no"] == item["version_no"] and digest(cp["current_snapshot_payload"]) == item["before_sha256"], "Stale canonical manifest: " + cp["product_id"])
    require(previous["product_version_id"] == item["product_version_id"] and previous["version_status"] == "approved", "Current version changed")
    require(previous["normalized_payload"] == cp["current_snapshot_payload"], "Canonical and current version disagree")
    require(all(cp[k] == item[k] for k in ("country_code", "bank_code", "product_type", "product_name")), "Identity changed")
    after = {**item["after"], "status": "inactive"}
    receipt = {**after[RECEIPT_KEY], "accepted": False, "operation_id": OPERATION,
               "reasons": sorted(set(item["assessment"]["reasons"] + ["legacy_collection_retired"]))}
    receipt["digest"] = payload_digest(cp, after)
    after[RECEIPT_KEY] = receipt
    version = "pver_accuracy_" + sha256(cp["product_id"].encode()).hexdigest()[:24]
    return {"product_id": cp["product_id"], "version_no": cp["current_version_no"] + 1,
            "product_version_id": version, "previous_version_id": previous["product_version_id"], "after": after,
            "event_metadata": {"operation_id": OPERATION, "authorization": AUTHORIZATION,
                "actor_type": "service", "actor_id": "accuracy-policy-cutover", "country_code": cp["country_code"],
                "previous_version_id": previous["product_version_id"], "current_version_id": version,
                "before_sha256": item["before_sha256"], "after_sha256": digest(after),
                "changed_field_names": sorted(k for k in set(cp["current_snapshot_payload"]) | set(after) if cp["current_snapshot_payload"].get(k) != after.get(k)),
                "exclusion_reasons": receipt["reasons"], "status_before": "active", "status_after": "inactive",
                "verification_timestamp_preserved": True}}


if __name__ == "__main__":
    raise SystemExit("D-090 is complete. Use the manifest verification tests for historical checks.")
