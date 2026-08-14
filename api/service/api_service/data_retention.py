from __future__ import annotations

from typing import Any


def apply_data_retention(connection: Any) -> dict[str, Any]:
    """Apply the database-owned bounded-retention policy when it is installed."""

    row = connection.execute(
        """
        SELECT to_regprocedure('fpds_apply_data_retention()') IS NOT NULL AS available
        """
    ).fetchone()
    if not row or not bool(row.get("available")):
        return {"status": "not_installed"}

    result = connection.execute(
        """
        SELECT fpds_apply_data_retention() AS retention_summary
        """
    ).fetchone()
    summary = result.get("retention_summary") if result else None
    return {
        "status": "completed",
        "removed": dict(summary) if isinstance(summary, dict) else {},
    }
