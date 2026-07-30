from __future__ import annotations

import json
import re
from typing import Any

from psycopg import Connection

from api_service.country_catalog import COUNTRY_BY_CODE, COUNTRY_CATALOG
from api_service.errors import SourceRegistryError
from api_service.security import new_id, utc_now


def normalize_country_code(country_code: str) -> str:
    normalized = country_code.strip().upper()
    if not re.fullmatch(r"[A-Z]{2}", normalized) or normalized not in COUNTRY_BY_CODE:
        raise SourceRegistryError(
            status_code=422,
            code="unsupported_country_code",
            message="Select a country from the prepared country list.",
        )
    return normalized


def load_country_registry(connection: Connection) -> dict[str, Any]:
    rows = connection.execute(
        """
        SELECT country_code, country_name, status, display_order, created_at, updated_at
        FROM country_registry
        ORDER BY country_name, country_code
        """
    ).fetchall()
    configured = {str(row["country_code"]).upper(): row for row in rows}

    items = [
        _serialize_catalog_item(code=code, fallback_name=name, row=configured.get(code))
        for code, name in COUNTRY_CATALOG
    ]
    active_count = sum(1 for item in items if item["status"] == "active")
    return {
        "items": items,
        "summary": {
            "total_items": len(items),
            "active_items": active_count,
            "available_items": len(items) - active_count,
        },
    }


def activate_country(
    connection: Connection,
    *,
    country_code: str,
    actor: dict[str, Any],
    request_context: dict[str, Any],
) -> dict[str, Any]:
    normalized = normalize_country_code(country_code)
    country_name = COUNTRY_BY_CODE[normalized]
    existing = connection.execute(
        """
        SELECT country_code, country_name, status, display_order, created_at, updated_at
        FROM country_registry
        WHERE country_code = %(country_code)s
        FOR UPDATE
        """,
        {"country_code": normalized},
    ).fetchone()
    if existing and existing["status"] == "active":
        return _serialize_catalog_item(code=normalized, fallback_name=country_name, row=existing)

    now = utc_now()
    row = connection.execute(
        """
        INSERT INTO country_registry (
            country_code, country_name, status, display_order, created_at, updated_at
        )
        VALUES (
            %(country_code)s, %(country_name)s, 'active', 1000, %(now)s, %(now)s
        )
        ON CONFLICT (country_code) DO UPDATE
        SET
            country_name = EXCLUDED.country_name,
            status = 'active',
            updated_at = EXCLUDED.updated_at
        RETURNING country_code, country_name, status, display_order, created_at, updated_at
        """,
        {"country_code": normalized, "country_name": country_name, "now": now},
    ).fetchone()
    _record_country_audit_event(
        connection,
        actor=actor,
        request_context=request_context,
        event_type="country_activated",
        country_code=normalized,
        diff_summary=f"Activated country `{normalized}` ({country_name}).",
        previous_status=str(existing["status"]) if existing else None,
        next_status="active",
    )
    return _serialize_catalog_item(code=normalized, fallback_name=country_name, row=row)


def deactivate_country(
    connection: Connection,
    *,
    country_code: str,
    current_country_code: str,
    actor: dict[str, Any],
    request_context: dict[str, Any],
) -> dict[str, Any]:
    normalized = normalize_country_code(country_code)
    current = normalize_country_code(current_country_code)
    if normalized == current:
        raise SourceRegistryError(
            status_code=409,
            code="current_country_cannot_be_deactivated",
            message="Sign in through another active country before deactivating this country.",
        )

    row = connection.execute(
        """
        SELECT country_code, country_name, status, display_order, created_at, updated_at
        FROM country_registry
        WHERE country_code = %(country_code)s
        FOR UPDATE
        """,
        {"country_code": normalized},
    ).fetchone()
    if not row or row["status"] != "active":
        return _serialize_catalog_item(code=normalized, fallback_name=COUNTRY_BY_CODE[normalized], row=row)

    active_rows = connection.execute(
        """
        SELECT country_code
        FROM country_registry
        WHERE status = 'active'
        FOR UPDATE
        """
    ).fetchall()
    if len(active_rows) <= 1:
        raise SourceRegistryError(
            status_code=409,
            code="last_active_country",
            message="At least one country must remain active.",
        )

    now = utc_now()
    updated = connection.execute(
        """
        UPDATE country_registry
        SET status = 'inactive', updated_at = %(now)s
        WHERE country_code = %(country_code)s
        RETURNING country_code, country_name, status, display_order, created_at, updated_at
        """,
        {"country_code": normalized, "now": now},
    ).fetchone()
    connection.execute(
        """
        UPDATE admin_auth_session
        SET
            session_status = 'revoked',
            revoked_at = %(now)s,
            revoked_reason = 'country_deactivated'
        WHERE country_code = %(country_code)s
          AND session_status = 'active'
        """,
        {"country_code": normalized, "now": now},
    )
    _record_country_audit_event(
        connection,
        actor=actor,
        request_context=request_context,
        event_type="country_deactivated",
        country_code=normalized,
        diff_summary=f"Deactivated country `{normalized}` ({COUNTRY_BY_CODE[normalized]}).",
        previous_status="active",
        next_status="inactive",
    )
    return _serialize_catalog_item(code=normalized, fallback_name=COUNTRY_BY_CODE[normalized], row=updated)


def _serialize_catalog_item(
    *,
    code: str,
    fallback_name: str,
    row: dict[str, Any] | None,
) -> dict[str, Any]:
    status = str(row["status"]) if row else "inactive"
    return {
        "country_code": code,
        "country_name": str(row.get("country_name") or fallback_name) if row else fallback_name,
        "status": status,
        "created_at": _isoformat(row.get("created_at")) if row else None,
        "updated_at": _isoformat(row.get("updated_at")) if row else None,
    }


def _isoformat(value: Any) -> str | None:
    if value is None:
        return None
    return value.isoformat() if hasattr(value, "isoformat") else str(value)


def _record_country_audit_event(
    connection: Connection,
    *,
    actor: dict[str, Any],
    request_context: dict[str, Any],
    event_type: str,
    country_code: str,
    diff_summary: str,
    previous_status: str | None,
    next_status: str,
) -> None:
    connection.execute(
        """
        INSERT INTO audit_event (
            audit_event_id,
            event_category,
            event_type,
            actor_type,
            actor_id,
            actor_role_snapshot,
            target_type,
            target_id,
            request_id,
            diff_summary,
            source_ref,
            ip_address,
            user_agent,
            event_payload,
            occurred_at
        )
        VALUES (
            %(audit_event_id)s,
            'config',
            %(event_type)s,
            'user',
            %(actor_id)s,
            %(actor_role_snapshot)s,
            'country_registry',
            %(country_code)s,
            %(request_id)s,
            %(diff_summary)s,
            %(source_ref)s,
            %(ip_address)s,
            %(user_agent)s,
            %(event_payload)s::jsonb,
            %(occurred_at)s
        )
        """,
        {
            "audit_event_id": new_id("audit"),
            "event_type": event_type,
            "actor_id": actor.get("user_id"),
            "actor_role_snapshot": actor.get("role"),
            "country_code": country_code,
            "request_id": request_context.get("request_id"),
            "diff_summary": diff_summary,
            "source_ref": request_context.get("request_id"),
            "ip_address": request_context.get("ip_address"),
            "user_agent": request_context.get("user_agent"),
            "event_payload": json.dumps(
                {
                    "country_code": country_code,
                    "country_name": COUNTRY_BY_CODE[country_code],
                    "previous_status": previous_status,
                    "next_status": next_status,
                }
            ),
            "occurred_at": utc_now(),
        },
    )
