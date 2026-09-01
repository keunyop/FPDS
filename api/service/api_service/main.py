from __future__ import annotations

from datetime import UTC, datetime
from secrets import compare_digest
from typing import Annotated
from typing import Any
from typing import Literal
from uuid import uuid4

from fastapi import FastAPI, Query, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from api_service.auth import (
    LoginError,
    authenticate_user,
    create_signup_request,
    get_session_by_token,
    load_admin_login_countries,
    load_signup_requests,
    review_signup_request,
    revoke_session,
    switch_session_country,
)
from api_service.aggregate_refresh import (
    AggregateRefreshError,
    launch_aggregate_refresh_runner,
    load_dashboard_health,
    queue_review_aggregate_refresh_request,
    request_manual_aggregate_refresh,
)
from api_service.bank_ai_onboarding import run_bank_ai_onboarding
from api_service.ai_verification import (
    AiVerificationError,
    load_latest_ai_verification,
    run_review_ai_verification,
)
from api_service.change_history import load_change_history_list, normalize_change_history_filters
from api_service.config import Settings
from api_service.countries import activate_country, deactivate_country, load_country_registry
from api_service.db import open_connection
from api_service.errors import SourceRegistryError
from api_service.models import BankAiOnboardingRequest
from api_service.models import BankWriteRequest
from api_service.models import CountrySwitchRequest
from api_service.models import LoginRequest
from api_service.models import ProductTypeWriteRequest
from api_service.models import PublicEngagementRequest
from api_service.models import PublicFeedbackRequest
from api_service.models import ReviewDecisionRequest
from api_service.models import SignupRequestCreateRequest
from api_service.models import SignupRequestReviewRequest
from api_service.models import SourceCatalogCollectionRequest
from api_service.models import SourceCatalogWriteRequest
from api_service.models import SourceCollectionRequest
from api_service.models import SourceRegistryWriteRequest
from api_service.public_dashboard import (
    SUPPORTED_AXIS_PRESETS,
    load_public_dashboard_rankings,
    load_public_dashboard_scatter,
    load_public_dashboard_summary,
    normalize_public_dashboard_query,
)
from api_service.public_engagement import (
    PublicEngagementRateLimiter,
    load_public_product_engagement_summary,
    record_public_product_engagement,
)
from api_service.public_feedback import (
    PublicFeedbackRateLimiter,
    create_public_feedback_submission,
    is_feedback_category_allowed,
    load_public_feedback_submissions,
    normalize_public_feedback_filters,
)
from api_service.public_products import (
    PRODUCT_SORT_OPTIONS,
    load_available_public_countries,
    load_public_filters,
    load_public_product_detail,
    load_public_products,
    normalize_public_products_query,
)
from api_service.product_types import (
    create_product_type_definition,
    delete_product_type_definition,
    load_product_type_definition,
    load_product_type_list,
    normalize_product_type_filters,
    update_product_type_definition,
)
from api_service.review_detail import (
    ReviewRequestContext,
    ReviewTaskError,
    apply_review_decision,
    load_review_task_detail,
)
from api_service.review_queue import load_review_queue, normalize_review_queue_filters
from api_service.run_retry import RunRetryError, retry_failed_run
from api_service.run_status import load_run_status_detail, load_run_status_list, normalize_run_status_filters
from api_service.source_registry import (
    delete_source_registry_item,
    load_source_registry_detail,
    load_source_registry_list,
    normalize_source_registry_filters,
)
from api_service.source_catalog import (
    create_bank_profile,
    delete_bank_profile,
    create_source_catalog_item,
    load_bank_detail,
    load_bank_list,
    load_source_catalog_detail,
    load_source_catalog_list,
    normalize_bank_filters,
    normalize_source_catalog_filters,
    start_source_catalog_collection,
    update_bank_profile,
    update_source_catalog_item,
)


def _request_ip(request: Request) -> str | None:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client:
        return request.client.host
    return None


def _meta(request: Request, extra: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = {
        "request_id": request.state.request_id,
        "generated_at": request.state.generated_at,
    }
    if extra:
        payload.update(extra)
    return payload


def _success(
    data: dict[str, Any],
    request: Request,
    status_code: int = 200,
    *,
    meta_extra: dict[str, Any] | None = None,
) -> JSONResponse:
    return JSONResponse(status_code=status_code, content={"data": data, "meta": _meta(request, extra=meta_extra)})


def _error(*, status_code: int, code: str, message: str, request: Request) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={
            "error": {"code": code, "message": message, "details": {}},
            "meta": _meta(request),
        },
    )


def _attach_auth_cookies(response: Response, *, settings: Settings, session_token: str, csrf_token: str | None) -> None:
    response.set_cookie(
        key=settings.session_cookie_name,
        value=session_token,
        httponly=True,
        secure=settings.cookie_secure,
        samesite=settings.cookie_same_site,
        path="/",
    )
    if csrf_token:
        response.set_cookie(
            key=settings.csrf_cookie_name,
            value=csrf_token,
            httponly=False,
            secure=settings.cookie_secure,
            samesite=settings.cookie_same_site,
            path="/",
        )


def _clear_auth_cookies(response: Response, settings: Settings) -> None:
    response.delete_cookie(settings.session_cookie_name, path="/")
    response.delete_cookie(settings.csrf_cookie_name, path="/")


settings = Settings.from_env()
app = FastAPI(
    title="FPDS Admin API",
    docs_url="/docs",
    redoc_url=None,
)
app.state.settings = settings
app.state.public_engagement_rate_limiter = PublicEngagementRateLimiter()
app.state.public_feedback_rate_limiter = PublicFeedbackRateLimiter()


def _public_app_auth_error(request: Request) -> JSONResponse | None:
    configured_secret = request.app.state.settings.public_app_api_secret
    if not configured_secret:
        return _error(
            status_code=503,
            code="public_app_credential_not_configured",
            message="The Public app credential is not configured.",
            request=request,
        )
    provided_secret = request.headers.get("x-fpds-public-app-secret", "")
    if not provided_secret or not compare_digest(provided_secret, configured_secret):
        return _error(
            status_code=401,
            code="invalid_public_app_credential",
            message="A valid Public app credential is required.",
            request=request,
        )
    return None


@app.middleware("http")
async def request_context_middleware(request: Request, call_next):
    request.state.request_id = request.headers.get("x-request-id", f"req_{uuid4().hex}")
    request.state.generated_at = datetime.now(UTC).isoformat()
    response = await call_next(request)
    response.headers["x-request-id"] = request.state.request_id

    settings: Settings = request.app.state.settings
    if settings.security_headers_enabled:
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Content-Security-Policy"] = "default-src 'self'; base-uri 'self'; frame-ancestors 'none'; object-src 'none'; img-src 'self' data:; style-src 'self' 'unsafe-inline'; script-src 'self'; connect-src 'self'"
        if settings.cookie_secure:
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response


@app.exception_handler(LoginError)
async def login_error_handler(request: Request, exc: LoginError):
    return _error(status_code=exc.status_code, code=exc.code, message=exc.message, request=request)


@app.exception_handler(ReviewTaskError)
async def review_task_error_handler(request: Request, exc: ReviewTaskError):
    return _error(status_code=exc.status_code, code=exc.code, message=exc.message, request=request)


@app.exception_handler(AiVerificationError)
async def ai_verification_error_handler(request: Request, exc: AiVerificationError):
    return _error(status_code=exc.status_code, code=exc.code, message=exc.message, request=request)


@app.exception_handler(SourceRegistryError)
async def source_registry_error_handler(request: Request, exc: SourceRegistryError):
    return _error(status_code=exc.status_code, code=exc.code, message=exc.message, request=request)


@app.exception_handler(AggregateRefreshError)
async def aggregate_refresh_error_handler(request: Request, exc: AggregateRefreshError):
    return _error(status_code=exc.status_code, code=exc.code, message=exc.message, request=request)


@app.exception_handler(RunRetryError)
async def run_retry_error_handler(request: Request, exc: RunRetryError):
    return _error(status_code=exc.status_code, code=exc.code, message=exc.message, request=request)


@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError):
    return _error(status_code=422, code="validation_error", message="Invalid request payload.", request=request)


@app.exception_handler(Exception)
async def unhandled_error_handler(request: Request, exc: Exception):
    return _error(status_code=500, code="internal_error", message="Internal server error.", request=request)


app.add_middleware(
    CORSMiddleware,
    allow_origins=sorted({*settings.allowed_public_origins, *settings.allowed_admin_origins}),
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "X-CSRF-Token", "X-Request-ID"],
)


def _resolve_session(request: Request) -> tuple[dict[str, Any], dict[str, Any]]:
    settings: Settings = request.app.state.settings
    session_token = request.cookies.get(settings.session_cookie_name)
    if not session_token:
        raise LoginError(status_code=401, code="authentication_required", message="Admin session is required.")

    with open_connection(settings) as connection:
        resolved = get_session_by_token(connection, session_token=session_token, settings=settings)
        if not resolved:
            raise LoginError(status_code=401, code="authentication_required", message="Admin session is required.")
    return resolved


def _require_csrf(request: Request, *, session_info: dict[str, Any]) -> None:
    settings: Settings = request.app.state.settings
    if not settings.csrf_enabled:
        return

    expected = session_info.get("csrf_token")
    provided = request.headers.get("x-csrf-token")
    if not expected or provided != expected:
        raise ReviewTaskError(status_code=403, code="invalid_csrf_token", message="A valid CSRF token is required.")


def _require_admin_role(actor: dict[str, Any]) -> None:
    if str(actor.get("role") or "").lower() != "admin":
        raise SourceRegistryError(status_code=403, code="admin_role_required", message="Admin role is required.")


def _session_country(session_info: dict[str, Any]) -> str:
    country_code = str(session_info.get("country_code") or "").strip().upper()
    if len(country_code) != 2:
        raise LoginError(
            status_code=401,
            code="country_context_required",
            message="Sign in again and select a country.",
        )
    return country_code


def _require_payload_country(payload: dict[str, Any], *, country_code: str) -> dict[str, Any]:
    requested = str(payload.get("country_code") or country_code).strip().upper()
    if requested != country_code:
        raise SourceRegistryError(
            status_code=403,
            code="country_scope_mismatch",
            message="The requested record is outside the signed-in country.",
        )
    return {**payload, "country_code": country_code}


def _require_country_records(
    connection: Any,
    *,
    table_name: str,
    id_column: str,
    record_ids: list[str],
    country_code: str,
) -> None:
    trusted_scopes = {
        ("bank", "bank_code"),
        ("source_registry_item", "source_id"),
        ("source_registry_catalog_item", "catalog_item_id"),
        ("normalized_candidate", "candidate_id"),
        ("ingestion_run", "run_id"),
    }
    if (table_name, id_column) not in trusted_scopes:
        raise RuntimeError("Unsupported country scope lookup.")
    unique_ids = list(dict.fromkeys(record_ids))
    rows = connection.execute(
        f"""
        SELECT {id_column}
        FROM {table_name}
        WHERE {id_column} = ANY(%(record_ids)s)
          AND country_code = %(country_code)s
        """,
        {"record_ids": unique_ids, "country_code": country_code},
    ).fetchall()
    if len(rows) != len(unique_ids):
        raise SourceRegistryError(
            status_code=404,
            code="country_scoped_record_not_found",
            message="The requested record was not found in the signed-in country.",
        )


def _require_review_task_country(connection: Any, *, review_task_id: str, country_code: str) -> None:
    row = connection.execute(
        """
        SELECT rt.review_task_id
        FROM review_task AS rt
        JOIN normalized_candidate AS nc
          ON nc.candidate_id = rt.candidate_id
        WHERE rt.review_task_id = %(review_task_id)s
          AND nc.country_code = %(country_code)s
        """,
        {"review_task_id": review_task_id, "country_code": country_code},
    ).fetchone()
    if not row:
        raise SourceRegistryError(
            status_code=404,
            code="country_scoped_record_not_found",
            message="The requested record was not found in the signed-in country.",
        )


@app.get("/healthz")
async def healthz() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/admin/auth/countries")
async def admin_login_countries(request: Request) -> JSONResponse:
    settings: Settings = request.app.state.settings
    with open_connection(settings) as connection:
        countries = load_admin_login_countries(connection)
    return _success({"countries": countries}, request)


@app.get("/api/admin/countries")
async def country_registry(request: Request) -> JSONResponse:
    actor, _ = _resolve_session(request)
    _require_admin_role(actor)
    settings: Settings = request.app.state.settings
    with open_connection(settings) as connection:
        payload = load_country_registry(connection)
    return _success(payload, request)


@app.post("/api/admin/countries/{country_code}/activate")
async def activate_country_registry_item(request: Request, country_code: str) -> JSONResponse:
    actor, session_info = _resolve_session(request)
    _require_admin_role(actor)
    _require_csrf(request, session_info=session_info)
    settings: Settings = request.app.state.settings
    with open_connection(settings) as connection:
        country = activate_country(
            connection,
            country_code=country_code,
            actor=actor,
            request_context={
                "request_id": request.state.request_id,
                "ip_address": _request_ip(request),
                "user_agent": request.headers.get("user-agent"),
            },
        )
    return _success({"country": country}, request)


@app.delete("/api/admin/countries/{country_code}")
async def deactivate_country_registry_item(request: Request, country_code: str) -> JSONResponse:
    actor, session_info = _resolve_session(request)
    _require_admin_role(actor)
    _require_csrf(request, session_info=session_info)
    settings: Settings = request.app.state.settings
    with open_connection(settings) as connection:
        country = deactivate_country(
            connection,
            country_code=country_code,
            current_country_code=_session_country(session_info),
            actor=actor,
            request_context={
                "request_id": request.state.request_id,
                "ip_address": _request_ip(request),
                "user_agent": request.headers.get("user-agent"),
            },
        )
    return _success({"country": country}, request)


@app.post("/api/admin/auth/login")
async def login(request: Request, payload: LoginRequest) -> JSONResponse:
    settings: Settings = request.app.state.settings
    with open_connection(settings) as connection:
        user, session, session_token = authenticate_user(
            connection,
            login_id=payload.login_id,
            password=payload.password,
            country_code=payload.country_code,
            ip_address=_request_ip(request),
            user_agent=request.headers.get("user-agent"),
            request_id=request.state.request_id,
            settings=settings,
        )

    response = _success(
        {
            "user": {
                "user_id": user["user_id"],
                "login_id": user["login_id"],
                "email": user["email"],
                "role": user["role"],
                "display_name": user["display_name"],
                "issued_at": session["issued_at"].isoformat(),
                "expires_at": session["absolute_expires_at"].isoformat(),
            },
            "country_code": session["country_code"],
            "csrf_token": session["csrf_token"],
            "redirect_to": "/admin",
        },
        request,
    )
    _attach_auth_cookies(
        response,
        settings=settings,
        session_token=session_token,
        csrf_token=session["csrf_token"],
    )
    return response


@app.post("/api/admin/auth/signup-requests")
async def signup_request_create(request: Request, payload: SignupRequestCreateRequest) -> JSONResponse:
    settings: Settings = request.app.state.settings
    with open_connection(settings) as connection:
        signup_request = create_signup_request(
            connection,
            login_id=payload.login_id,
            display_name=payload.display_name,
            password=payload.password,
            request_id=request.state.request_id,
            ip_address=_request_ip(request),
            user_agent=request.headers.get("user-agent"),
        )
    return _success({"signup_request": signup_request}, request, status_code=201)


@app.get("/api/admin/auth/signup-requests")
async def signup_request_list(request: Request) -> JSONResponse:
    actor, _session_info = _resolve_session(request)
    _require_admin_role(actor)
    settings: Settings = request.app.state.settings
    with open_connection(settings) as connection:
        payload = load_signup_requests(connection)
    return _success(payload, request)


@app.post("/api/admin/auth/signup-requests/{signup_request_id}/approve")
async def signup_request_approve(
    request: Request,
    signup_request_id: str,
    payload: SignupRequestReviewRequest,
) -> JSONResponse:
    actor, session_info = _resolve_session(request)
    _require_admin_role(actor)
    _require_csrf(request, session_info=session_info)
    settings: Settings = request.app.state.settings
    with open_connection(settings) as connection:
        reviewed_request = review_signup_request(
            connection,
            signup_request_id=signup_request_id,
            action="approve",
            actor=actor,
            role=payload.role,
            reason_text=payload.reason_text,
            request_id=request.state.request_id,
            ip_address=_request_ip(request),
            user_agent=request.headers.get("user-agent"),
        )
    return _success({"signup_request": reviewed_request}, request)


@app.post("/api/admin/auth/signup-requests/{signup_request_id}/reject")
async def signup_request_reject(
    request: Request,
    signup_request_id: str,
    payload: SignupRequestReviewRequest,
) -> JSONResponse:
    actor, session_info = _resolve_session(request)
    _require_admin_role(actor)
    _require_csrf(request, session_info=session_info)
    settings: Settings = request.app.state.settings
    with open_connection(settings) as connection:
        reviewed_request = review_signup_request(
            connection,
            signup_request_id=signup_request_id,
            action="reject",
            actor=actor,
            role=None,
            reason_text=payload.reason_text,
            request_id=request.state.request_id,
            ip_address=_request_ip(request),
            user_agent=request.headers.get("user-agent"),
        )
    return _success({"signup_request": reviewed_request}, request)


@app.post("/api/admin/auth/logout")
async def logout(request: Request) -> JSONResponse:
    settings: Settings = request.app.state.settings
    session_token = request.cookies.get(settings.session_cookie_name)
    if session_token:
        with open_connection(settings) as connection:
            resolved = get_session_by_token(connection, session_token=session_token, settings=settings)
            if resolved:
                actor, session = resolved
                revoke_session(
                    connection,
                    auth_session_id=session["auth_session_id"],
                    request_id=request.state.request_id,
                    actor=actor,
                    ip_address=_request_ip(request),
                    user_agent=request.headers.get("user-agent"),
                )

    response = _success({"logged_out": True}, request)
    _clear_auth_cookies(response, settings)
    return response


@app.get("/api/admin/auth/session")
async def session(request: Request) -> JSONResponse:
    actor, session_info = _resolve_session(request)
    return _success(
        {
            "user": actor,
            "country_code": _session_country(session_info),
            "csrf_token": session_info["csrf_token"],
        },
        request,
    )


@app.post("/api/admin/auth/country")
async def switch_country(request: Request, payload: CountrySwitchRequest) -> JSONResponse:
    actor, session_info = _resolve_session(request)
    _require_csrf(request, session_info=session_info)
    settings: Settings = request.app.state.settings
    with open_connection(settings) as connection:
        country_code = switch_session_country(
            connection,
            auth_session_id=session_info["auth_session_id"],
            country_code=payload.country_code,
            actor=actor,
            request_id=request.state.request_id,
            ip_address=_request_ip(request),
            user_agent=request.headers.get("user-agent"),
        )
    return _success({"country_code": country_code, "redirect_to": "/admin"}, request)


@app.get("/api/admin/sources")
async def source_registry_list(
    request: Request,
    bank_code: str | None = None,
    country_code: str | None = None,
    product_type: str | None = None,
    status: str | None = None,
    discovery_role: str | None = None,
    q: str | None = None,
) -> JSONResponse:
    _actor, session_info = _resolve_session(request)
    session_country = _session_country(session_info)
    if country_code:
        _require_payload_country({"country_code": country_code}, country_code=session_country)
    filters = normalize_source_registry_filters(
        bank_code=bank_code,
        country_code=session_country,
        product_type=product_type,
        status=status,
        discovery_role=discovery_role,
        search=q,
    )
    settings: Settings = request.app.state.settings
    with open_connection(settings) as connection:
        payload = load_source_registry_list(connection, filters=filters)
    return _success(payload, request)


@app.post("/api/admin/sources")
async def create_source_registry(
    request: Request,
    payload: SourceRegistryWriteRequest,
) -> JSONResponse:
    _resolve_session(request)
    return _error(
        status_code=405,
        code="source_registry_read_only",
        message="Source registry rows are read-only. Update Banks or Source Catalog instead.",
        request=request,
    )


@app.get("/api/admin/sources/{source_id}")
async def source_registry_detail(request: Request, source_id: str) -> JSONResponse:
    _actor, session_info = _resolve_session(request)
    country_code = _session_country(session_info)
    settings: Settings = request.app.state.settings
    with open_connection(settings) as connection:
        _require_country_records(
            connection,
            table_name="source_registry_item",
            id_column="source_id",
            record_ids=[source_id],
            country_code=country_code,
        )
        payload = load_source_registry_detail(connection, source_id=source_id)
    if not payload:
        return _error(status_code=404, code="source_registry_item_not_found", message="Source registry item was not found.", request=request)
    return _success(payload, request)


@app.patch("/api/admin/sources/{source_id}")
async def patch_source_registry(
    request: Request,
    source_id: str,
    payload: SourceRegistryWriteRequest,
) -> JSONResponse:
    _resolve_session(request)
    return _error(
        status_code=405,
        code="source_registry_read_only",
        message="Source registry rows are read-only. Update Banks or Source Catalog instead.",
        request=request,
    )


@app.delete("/api/admin/sources/{source_id}")
async def delete_source_registry(request: Request, source_id: str) -> JSONResponse:
    actor, session_info = _resolve_session(request)
    _require_admin_role(actor)
    _require_csrf(request, session_info=session_info)
    settings: Settings = request.app.state.settings
    with open_connection(settings) as connection:
        _require_country_records(
            connection,
            table_name="source_registry_item",
            id_column="source_id",
            record_ids=[source_id],
            country_code=_session_country(session_info),
        )
        source = delete_source_registry_item(
            connection,
            source_id=source_id,
            actor=actor,
            request_context={
                "request_id": request.state.request_id,
                "ip_address": _request_ip(request),
                "user_agent": request.headers.get("user-agent"),
            },
        )
    return _success({"source": source}, request)


@app.post("/api/admin/source-collections")
async def launch_source_collection(request: Request, payload: SourceCollectionRequest) -> JSONResponse:
    actor, session_info = _resolve_session(request)
    _require_admin_role(actor)
    _require_csrf(request, session_info=session_info)
    settings: Settings = request.app.state.settings
    with open_connection(settings) as connection:
        _require_country_records(
            connection,
            table_name="source_registry_item",
            id_column="source_id",
            record_ids=payload.source_ids,
            country_code=_session_country(session_info),
        )
        result = start_source_collection(
            connection,
            source_ids=payload.source_ids,
            actor=actor,
            request_context={
                "request_id": request.state.request_id,
                "ip_address": _request_ip(request),
                "user_agent": request.headers.get("user-agent"),
            },
        )
    return _success(result, request, status_code=202)


@app.get("/api/admin/banks")
async def bank_list(
    request: Request,
    status: str | None = None,
    q: str | None = None,
) -> JSONResponse:
    _actor, session_info = _resolve_session(request)
    filters = normalize_bank_filters(country_code=_session_country(session_info), search=q, status=status)
    settings: Settings = request.app.state.settings
    with open_connection(settings) as connection:
        payload = load_bank_list(connection, filters=filters)
    return _success(payload, request)


@app.post("/api/admin/banks")
async def create_bank(
    request: Request,
    payload: BankWriteRequest,
) -> JSONResponse:
    actor, session_info = _resolve_session(request)
    _require_admin_role(actor)
    _require_csrf(request, session_info=session_info)
    country_code = _session_country(session_info)
    settings: Settings = request.app.state.settings
    with open_connection(settings) as connection:
        bank = create_bank_profile(
            connection,
            payload=_require_payload_country(payload.model_dump(exclude_unset=True), country_code=country_code),
            actor=actor,
            request_context={
                "request_id": request.state.request_id,
                "ip_address": _request_ip(request),
                "user_agent": request.headers.get("user-agent"),
            },
        )
    return _success({"bank": bank}, request, status_code=201)


@app.post("/api/admin/banks/ai-onboard")
def ai_onboard_banks(
    request: Request,
    payload: BankAiOnboardingRequest,
) -> JSONResponse:
    actor, session_info = _resolve_session(request)
    _require_admin_role(actor)
    _require_csrf(request, session_info=session_info)
    country_code = _session_country(session_info)
    settings: Settings = request.app.state.settings
    with open_connection(settings) as connection:
        result = run_bank_ai_onboarding(
            connection,
            country_code=country_code,
            requested_count=payload.count,
            actor=actor,
            request_context={
                "request_id": request.state.request_id,
                "ip_address": _request_ip(request),
                "user_agent": request.headers.get("user-agent"),
            },
        )
    if not result["ok"]:
        return JSONResponse(
            status_code=int(result["status_code"]),
            content={
                "error": {
                    "code": result["error"]["code"],
                    "message": result["error"]["message"],
                    "details": {},
                },
                "data": {"operation_id": result["operation_id"]},
                "meta": _meta(request),
            },
        )
    response_payload = {
        key: value
        for key, value in result.items()
        if key not in {"ok", "status_code"}
    }
    return _success(response_payload, request, status_code=201)


@app.get("/api/admin/banks/{bank_code}")
async def bank_detail(request: Request, bank_code: str) -> JSONResponse:
    _actor, session_info = _resolve_session(request)
    country_code = _session_country(session_info)
    settings: Settings = request.app.state.settings
    with open_connection(settings) as connection:
        _require_country_records(
            connection,
            table_name="bank",
            id_column="bank_code",
            record_ids=[bank_code.upper()],
            country_code=country_code,
        )
        payload = load_bank_detail(connection, bank_code=bank_code.upper())
    if not payload:
        return _error(status_code=404, code="bank_profile_not_found", message="Bank profile was not found.", request=request)
    return _success(payload, request)


@app.patch("/api/admin/banks/{bank_code}")
async def patch_bank(
    request: Request,
    bank_code: str,
    payload: BankWriteRequest,
) -> JSONResponse:
    actor, session_info = _resolve_session(request)
    _require_admin_role(actor)
    _require_csrf(request, session_info=session_info)
    country_code = _session_country(session_info)
    settings: Settings = request.app.state.settings
    with open_connection(settings) as connection:
        _require_country_records(
            connection,
            table_name="bank",
            id_column="bank_code",
            record_ids=[bank_code.upper()],
            country_code=country_code,
        )
        bank = update_bank_profile(
            connection,
            bank_code=bank_code.upper(),
            payload=_require_payload_country(payload.model_dump(exclude_unset=True), country_code=country_code),
            actor=actor,
            request_context={
                "request_id": request.state.request_id,
                "ip_address": _request_ip(request),
                "user_agent": request.headers.get("user-agent"),
            },
        )
    return _success({"bank": bank}, request)


@app.delete("/api/admin/banks/{bank_code}")
async def delete_bank(request: Request, bank_code: str) -> JSONResponse:
    actor, session_info = _resolve_session(request)
    _require_admin_role(actor)
    _require_csrf(request, session_info=session_info)
    settings: Settings = request.app.state.settings
    with open_connection(settings) as connection:
        _require_country_records(
            connection,
            table_name="bank",
            id_column="bank_code",
            record_ids=[bank_code.upper()],
            country_code=_session_country(session_info),
        )
        bank = delete_bank_profile(
            connection,
            bank_code=bank_code.upper(),
            actor=actor,
            request_context={
                "request_id": request.state.request_id,
                "ip_address": _request_ip(request),
                "user_agent": request.headers.get("user-agent"),
            },
        )
    return _success({"bank": bank}, request)


@app.get("/api/admin/source-catalog")
async def source_catalog_list(
    request: Request,
    bank_code: str | None = None,
    product_type: str | None = None,
    status: str | None = None,
    q: str | None = None,
) -> JSONResponse:
    _actor, session_info = _resolve_session(request)
    filters = normalize_source_catalog_filters(
        country_code=_session_country(session_info),
        search=q,
        bank_code=bank_code,
        product_type=product_type,
        status=status,
    )
    settings: Settings = request.app.state.settings
    with open_connection(settings) as connection:
        payload = load_source_catalog_list(connection, filters=filters)
    return _success(payload, request)


@app.post("/api/admin/source-catalog")
async def create_source_catalog(
    request: Request,
    payload: SourceCatalogWriteRequest,
) -> JSONResponse:
    actor, session_info = _resolve_session(request)
    _require_admin_role(actor)
    _require_csrf(request, session_info=session_info)
    settings: Settings = request.app.state.settings
    with open_connection(settings) as connection:
        bank_code = str(payload.bank_code or "").strip().upper()
        _require_country_records(
            connection,
            table_name="bank",
            id_column="bank_code",
            record_ids=[bank_code],
            country_code=_session_country(session_info),
        )
        catalog_item = create_source_catalog_item(
            connection,
            payload=payload.model_dump(exclude_unset=True),
            actor=actor,
            request_context={
                "request_id": request.state.request_id,
                "ip_address": _request_ip(request),
                "user_agent": request.headers.get("user-agent"),
            },
        )
    return _success({"catalog_item": catalog_item}, request, status_code=201)


@app.get("/api/admin/source-catalog/{catalog_item_id}")
async def source_catalog_detail(request: Request, catalog_item_id: str) -> JSONResponse:
    _actor, session_info = _resolve_session(request)
    settings: Settings = request.app.state.settings
    with open_connection(settings) as connection:
        _require_country_records(
            connection,
            table_name="source_registry_catalog_item",
            id_column="catalog_item_id",
            record_ids=[catalog_item_id],
            country_code=_session_country(session_info),
        )
        payload = load_source_catalog_detail(connection, catalog_item_id=catalog_item_id)
    if not payload:
        return _error(status_code=404, code="source_catalog_not_found", message="Source catalog item was not found.", request=request)
    return _success(payload, request)


@app.patch("/api/admin/source-catalog/{catalog_item_id}")
async def patch_source_catalog(
    request: Request,
    catalog_item_id: str,
    payload: SourceCatalogWriteRequest,
) -> JSONResponse:
    actor, session_info = _resolve_session(request)
    _require_admin_role(actor)
    _require_csrf(request, session_info=session_info)
    settings: Settings = request.app.state.settings
    with open_connection(settings) as connection:
        _require_country_records(
            connection,
            table_name="source_registry_catalog_item",
            id_column="catalog_item_id",
            record_ids=[catalog_item_id],
            country_code=_session_country(session_info),
        )
        if payload.bank_code:
            _require_country_records(
                connection,
                table_name="bank",
                id_column="bank_code",
                record_ids=[payload.bank_code.upper()],
                country_code=_session_country(session_info),
            )
        catalog_item = update_source_catalog_item(
            connection,
            catalog_item_id=catalog_item_id,
            payload=payload.model_dump(exclude_unset=True),
            actor=actor,
            request_context={
                "request_id": request.state.request_id,
                "ip_address": _request_ip(request),
                "user_agent": request.headers.get("user-agent"),
            },
        )
    return _success({"catalog_item": catalog_item}, request)


@app.post("/api/admin/source-catalog/collect")
async def launch_source_catalog_collection(request: Request, payload: SourceCatalogCollectionRequest) -> JSONResponse:
    actor, session_info = _resolve_session(request)
    _require_admin_role(actor)
    _require_csrf(request, session_info=session_info)
    settings: Settings = request.app.state.settings
    with open_connection(settings) as connection:
        _require_country_records(
            connection,
            table_name="source_registry_catalog_item",
            id_column="catalog_item_id",
            record_ids=payload.catalog_item_ids,
            country_code=_session_country(session_info),
        )
        result = start_source_catalog_collection(
            connection,
            catalog_item_ids=payload.catalog_item_ids,
            precision_rediscovery=payload.precision_rediscovery,
            actor=actor,
            request_context={
                "request_id": request.state.request_id,
                "ip_address": _request_ip(request),
                "user_agent": request.headers.get("user-agent"),
            },
        )
    return _success(result, request, status_code=202)


@app.get("/api/admin/product-types")
async def product_type_list(
    request: Request,
    status: str | None = None,
    q: str | None = None,
) -> JSONResponse:
    _resolve_session(request)
    filters = normalize_product_type_filters(search=q, status=status)
    settings: Settings = request.app.state.settings
    with open_connection(settings) as connection:
        payload = load_product_type_list(connection, filters=filters)
    return _success(payload, request)


@app.post("/api/admin/product-types")
async def create_product_type(
    request: Request,
    payload: ProductTypeWriteRequest,
) -> JSONResponse:
    actor, session_info = _resolve_session(request)
    _require_admin_role(actor)
    _require_csrf(request, session_info=session_info)
    settings: Settings = request.app.state.settings
    with open_connection(settings) as connection:
        product_type = create_product_type_definition(
            connection,
            payload=payload.model_dump(exclude_unset=True),
            actor=actor,
            country_code=_session_country(session_info),
            request_context={
                "request_id": request.state.request_id,
                "ip_address": _request_ip(request),
                "user_agent": request.headers.get("user-agent"),
            },
        )
    return _success({"product_type": product_type}, request, status_code=201)


@app.get("/api/admin/product-types/{product_type_code}")
async def product_type_detail(request: Request, product_type_code: str) -> JSONResponse:
    _resolve_session(request)
    settings: Settings = request.app.state.settings
    with open_connection(settings) as connection:
        payload = load_product_type_definition(connection, product_type_code=product_type_code.lower())
    if not payload:
        return _error(status_code=404, code="product_type_not_found", message="Product type was not found.", request=request)
    return _success({"product_type": payload}, request)


@app.patch("/api/admin/product-types/{product_type_code}")
async def patch_product_type(
    request: Request,
    product_type_code: str,
    payload: ProductTypeWriteRequest,
) -> JSONResponse:
    actor, session_info = _resolve_session(request)
    _require_admin_role(actor)
    _require_csrf(request, session_info=session_info)
    settings: Settings = request.app.state.settings
    with open_connection(settings) as connection:
        product_type = update_product_type_definition(
            connection,
            product_type_code=product_type_code.lower(),
            payload=payload.model_dump(exclude_unset=True),
            actor=actor,
            country_code=_session_country(session_info),
            request_context={
                "request_id": request.state.request_id,
                "ip_address": _request_ip(request),
                "user_agent": request.headers.get("user-agent"),
            },
    )
    return _success({"product_type": product_type}, request)


@app.delete("/api/admin/product-types/{product_type_code}")
async def delete_product_type(request: Request, product_type_code: str) -> JSONResponse:
    actor, session_info = _resolve_session(request)
    _require_admin_role(actor)
    _require_csrf(request, session_info=session_info)
    settings: Settings = request.app.state.settings
    with open_connection(settings) as connection:
        product_type = delete_product_type_definition(
            connection,
            product_type_code=product_type_code.lower(),
            actor=actor,
            request_context={
                "request_id": request.state.request_id,
                "ip_address": _request_ip(request),
                "user_agent": request.headers.get("user-agent"),
            },
        )
    return _success({"product_type": product_type}, request)


@app.get("/api/public/products")
async def public_products(
    request: Request,
    locale: str | None = None,
    country_code: str | None = "CA",
    bank_code: Annotated[list[str] | None, Query()] = None,
    product_type: Annotated[list[str] | None, Query()] = None,
    subtype_code: Annotated[list[str] | None, Query()] = None,
    target_customer_tag: Annotated[list[str] | None, Query()] = None,
    fee_bucket: str | None = None,
    minimum_balance_bucket: str | None = None,
    minimum_deposit_bucket: str | None = None,
    term_bucket: str | None = None,
    q: Annotated[str | None, Query(max_length=120)] = None,
    product_name: Annotated[str | None, Query(max_length=120)] = None,
    sort_by: str = "default",
    sort_order: Literal["asc", "desc"] = "desc",
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> JSONResponse:
    query = normalize_public_products_query(
        locale=locale,
        country_code=country_code,
        bank_codes=bank_code,
        product_types=product_type,
        subtype_codes=subtype_code,
        target_customer_tags=target_customer_tag,
        fee_bucket=fee_bucket,
        minimum_balance_bucket=minimum_balance_bucket,
        minimum_deposit_bucket=minimum_deposit_bucket,
        term_bucket=term_bucket,
        search_query=q,
        product_name_query=product_name,
        sort_by=sort_by,
        sort_order=sort_order,
        page=page,
        page_size=page_size,
    )
    settings: Settings = request.app.state.settings
    with open_connection(settings) as connection:
        payload = load_public_products(connection, query=query)
    return _success(
        payload,
        request,
        meta_extra={
            "locale": query.filters.locale,
            "page": payload["page"],
            "page_size": payload["page_size"],
            "total_items": payload["total_items"],
        },
    )


@app.post("/api/public/engagement")
async def public_engagement(request: Request, payload: PublicEngagementRequest) -> JSONResponse:
    auth_error = _public_app_auth_error(request)
    if auth_error:
        return auth_error
    limiter: PublicEngagementRateLimiter = request.app.state.public_engagement_rate_limiter
    if not limiter.allow():
        return _error(
            status_code=429,
            code="public_engagement_rate_limited",
            message="Public engagement recording is temporarily rate limited.",
            request=request,
        )
    settings: Settings = request.app.state.settings
    with open_connection(settings) as connection:
        recorded = record_public_product_engagement(
            connection,
            country_code=payload.country_code,
            product_id=payload.product_id,
            event_type=payload.event_type,
        )
    if not recorded:
        return _error(
            status_code=404,
            code="public_product_not_found",
            message="The product is not active in the latest Public snapshot.",
            request=request,
        )
    return _success({"recorded": True}, request, status_code=202)


@app.post("/api/public/feedback")
async def public_feedback(request: Request, payload: PublicFeedbackRequest) -> JSONResponse:
    auth_error = _public_app_auth_error(request)
    if auth_error:
        return auth_error
    if (
        not is_feedback_category_allowed(
            submission_type=payload.submission_type,
            category=payload.category,
        )
        or (payload.submission_type == "product_error" and not payload.product_id)
        or (payload.submission_type == "site_feedback" and payload.product_id is not None)
    ):
        return _error(
            status_code=400,
            code="invalid_feedback_payload",
            message="The feedback category or product context is invalid.",
            request=request,
        )
    limiter: PublicFeedbackRateLimiter = request.app.state.public_feedback_rate_limiter
    if not limiter.allow():
        return _error(
            status_code=429,
            code="public_feedback_rate_limited",
            message="Public feedback submission is temporarily rate limited.",
            request=request,
        )
    settings: Settings = request.app.state.settings
    with open_connection(settings) as connection:
        submission = create_public_feedback_submission(
            connection,
            country_code=payload.country_code,
            submission_type=payload.submission_type,
            category=payload.category,
            details=payload.details,
            locale=payload.locale,
            product_id=payload.product_id,
        )
    if not submission:
        return _error(
            status_code=404,
            code=(
                "public_product_not_found"
                if payload.submission_type == "product_error"
                else "public_country_not_found"
            ),
            message="The selected Public product or country is not available.",
            request=request,
        )
    return _success({"submission": submission}, request, status_code=201)


@app.get("/api/public/admin/feedback")
async def public_admin_feedback(
    request: Request,
    country_code: Annotated[
        str | None,
        Query(min_length=2, max_length=2, pattern=r"^[A-Za-z]{2}$"),
    ] = None,
    submission_type: Literal["product_error", "site_feedback"] | None = None,
    category: Literal[
        "accessibility_issue",
        "broken_link",
        "content_issue",
        "feature_suggestion",
        "incorrect_product_details",
        "incorrect_rate_or_fee",
        "missing_information",
        "other",
        "outdated_information",
        "usability_issue",
    ] | None = None,
    q: Annotated[str | None, Query(max_length=200)] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 50,
) -> JSONResponse:
    auth_error = _public_app_auth_error(request)
    if auth_error:
        return auth_error
    filters = normalize_public_feedback_filters(
        country_code=country_code,
        submission_type=submission_type,
        category=category,
        search=q,
        page=page,
        page_size=page_size,
    )
    settings: Settings = request.app.state.settings
    with open_connection(settings) as connection:
        payload = load_public_feedback_submissions(connection, filters=filters)
    return _success(payload, request)


@app.get("/api/public/admin/engagement-summary")
async def public_engagement_summary(
    request: Request,
    country_code: Annotated[str | None, Query(min_length=2, max_length=2, pattern=r"^[A-Za-z]{2}$")] = None,
) -> JSONResponse:
    auth_error = _public_app_auth_error(request)
    if auth_error:
        return auth_error
    settings: Settings = request.app.state.settings
    with open_connection(settings) as connection:
        summary = load_public_product_engagement_summary(
            connection,
            country_code=country_code,
        )
    return _success(summary, request)


@app.get("/api/public/products/{product_id}")
async def public_product_detail(
    request: Request,
    product_id: str,
    locale: str | None = None,
    country_code: str | None = "CA",
) -> JSONResponse:
    filters = normalize_public_products_query(
        locale=locale,
        country_code=country_code,
        bank_codes=None,
        product_types=None,
        subtype_codes=None,
        target_customer_tags=None,
        fee_bucket=None,
        minimum_balance_bucket=None,
        minimum_deposit_bucket=None,
        term_bucket=None,
        sort_by="default",
        sort_order="desc",
        page=1,
        page_size=1,
    ).filters
    settings: Settings = request.app.state.settings
    with open_connection(settings) as connection:
        payload = load_public_product_detail(connection, product_id=product_id, filters=filters)
    if payload is None:
        return _error(
            status_code=404,
            code="not_found",
            message="Public product was not found in the latest active snapshot.",
            request=request,
        )
    return _success(payload, request, meta_extra={"locale": filters.locale, "product_id": product_id})


@app.get("/api/public/filters")
async def public_filters(
    request: Request,
    locale: str | None = None,
    country_code: str | None = "CA",
    bank_code: Annotated[list[str] | None, Query()] = None,
    product_type: Annotated[list[str] | None, Query()] = None,
    subtype_code: Annotated[list[str] | None, Query()] = None,
    target_customer_tag: Annotated[list[str] | None, Query()] = None,
    fee_bucket: str | None = None,
    minimum_balance_bucket: str | None = None,
    minimum_deposit_bucket: str | None = None,
    term_bucket: str | None = None,
    q: Annotated[str | None, Query(max_length=120)] = None,
) -> JSONResponse:
    query = normalize_public_products_query(
        locale=locale,
        country_code=country_code,
        bank_codes=bank_code,
        product_types=product_type,
        subtype_codes=subtype_code,
        target_customer_tags=target_customer_tag,
        fee_bucket=fee_bucket,
        minimum_balance_bucket=minimum_balance_bucket,
        minimum_deposit_bucket=minimum_deposit_bucket,
        term_bucket=term_bucket,
        search_query=q,
        sort_by="default",
        sort_order="desc",
        page=1,
        page_size=20,
    )
    settings: Settings = request.app.state.settings
    with open_connection(settings) as connection:
        payload = load_public_filters(
            connection,
            filters=query.filters,
            search_query=query.search_query,
        )
    return _success(payload, request, meta_extra={"locale": query.filters.locale})


@app.get("/api/public/countries")
async def public_countries(request: Request) -> JSONResponse:
    settings: Settings = request.app.state.settings
    with open_connection(settings) as connection:
        countries = load_available_public_countries(connection)
    return _success({"countries": countries}, request)


@app.get("/api/public/dashboard-summary")
async def public_dashboard_summary(
    request: Request,
    locale: str | None = None,
    country_code: str | None = "CA",
    bank_code: Annotated[list[str] | None, Query()] = None,
    product_type: Annotated[list[str] | None, Query()] = None,
    subtype_code: Annotated[list[str] | None, Query()] = None,
    target_customer_tag: Annotated[list[str] | None, Query()] = None,
    fee_bucket: str | None = None,
    minimum_balance_bucket: str | None = None,
    minimum_deposit_bucket: str | None = None,
    term_bucket: str | None = None,
) -> JSONResponse:
    query = normalize_public_dashboard_query(
        locale=locale,
        country_code=country_code,
        bank_codes=bank_code,
        product_types=product_type,
        subtype_codes=subtype_code,
        target_customer_tags=target_customer_tag,
        fee_bucket=fee_bucket,
        minimum_balance_bucket=minimum_balance_bucket,
        minimum_deposit_bucket=minimum_deposit_bucket,
        term_bucket=term_bucket,
        axis_preset=None,
    )
    settings: Settings = request.app.state.settings
    with open_connection(settings) as connection:
        payload = load_public_dashboard_summary(connection, query=query)
    return _success(payload, request, meta_extra={"locale": query.filters.locale})


@app.get("/api/public/dashboard-rankings")
async def public_dashboard_rankings(
    request: Request,
    locale: str | None = None,
    country_code: str | None = "CA",
    bank_code: Annotated[list[str] | None, Query()] = None,
    product_type: Annotated[list[str] | None, Query()] = None,
    subtype_code: Annotated[list[str] | None, Query()] = None,
    target_customer_tag: Annotated[list[str] | None, Query()] = None,
    fee_bucket: str | None = None,
    minimum_balance_bucket: str | None = None,
    minimum_deposit_bucket: str | None = None,
    term_bucket: str | None = None,
) -> JSONResponse:
    query = normalize_public_dashboard_query(
        locale=locale,
        country_code=country_code,
        bank_codes=bank_code,
        product_types=product_type,
        subtype_codes=subtype_code,
        target_customer_tags=target_customer_tag,
        fee_bucket=fee_bucket,
        minimum_balance_bucket=minimum_balance_bucket,
        minimum_deposit_bucket=minimum_deposit_bucket,
        term_bucket=term_bucket,
        axis_preset=None,
    )
    settings: Settings = request.app.state.settings
    with open_connection(settings) as connection:
        payload = load_public_dashboard_rankings(connection, query=query)
    return _success(payload, request, meta_extra={"locale": query.filters.locale})


@app.get("/api/public/dashboard-scatter")
async def public_dashboard_scatter(
    request: Request,
    locale: str | None = None,
    country_code: str | None = "CA",
    bank_code: Annotated[list[str] | None, Query()] = None,
    product_type: Annotated[list[str] | None, Query()] = None,
    subtype_code: Annotated[list[str] | None, Query()] = None,
    target_customer_tag: Annotated[list[str] | None, Query()] = None,
    fee_bucket: str | None = None,
    minimum_balance_bucket: str | None = None,
    minimum_deposit_bucket: str | None = None,
    term_bucket: str | None = None,
    axis_preset: str | None = None,
) -> JSONResponse:
    query = normalize_public_dashboard_query(
        locale=locale,
        country_code=country_code,
        bank_codes=bank_code,
        product_types=product_type,
        subtype_codes=subtype_code,
        target_customer_tags=target_customer_tag,
        fee_bucket=fee_bucket,
        minimum_balance_bucket=minimum_balance_bucket,
        minimum_deposit_bucket=minimum_deposit_bucket,
        term_bucket=term_bucket,
        axis_preset=axis_preset,
    )
    settings: Settings = request.app.state.settings
    with open_connection(settings) as connection:
        payload = load_public_dashboard_scatter(connection, query=query)
    return _success(payload, request, meta_extra={"locale": query.filters.locale})


@app.get("/api/admin/review-tasks")
async def review_tasks(
    request: Request,
    state: Annotated[list[Literal["queued", "approved", "rejected", "edited", "deferred"]] | None, Query()] = None,
    bank_code: str | None = None,
    product_type: str | None = None,
    validation_status: Literal["pass", "warning", "error"] | None = None,
    created_from: datetime | None = None,
    created_to: datetime | None = None,
    q: str | None = None,
    sort_by: Literal["priority", "created_at", "updated_at", "source_confidence", "product_name"] = "priority",
    sort_order: Literal["asc", "desc"] = "desc",
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> JSONResponse:
    _actor, session_info = _resolve_session(request)
    filters = normalize_review_queue_filters(
        country_code=_session_country(session_info),
        states=state,
        bank_code=bank_code,
        product_type=product_type,
        validation_status=validation_status,
        created_from=created_from,
        created_to=created_to,
        search=q,
        sort_by=sort_by,
        sort_order=sort_order,
        page=page,
        page_size=page_size,
    )
    settings: Settings = request.app.state.settings
    with open_connection(settings) as connection:
        payload = load_review_queue(connection, filters=filters)
    return _success(payload, request)


@app.get("/api/admin/review-tasks/{review_task_id}")
async def review_task_detail(request: Request, review_task_id: str) -> JSONResponse:
    actor, session_info = _resolve_session(request)
    settings: Settings = request.app.state.settings
    with open_connection(settings) as connection:
        _require_review_task_country(
            connection,
            review_task_id=review_task_id,
            country_code=_session_country(session_info),
        )
        payload = load_review_task_detail(connection, review_task_id=review_task_id, actor_role=str(actor["role"]))
        if payload:
            payload["ai_verification"] = load_latest_ai_verification(
                connection,
                review_task_id=review_task_id,
                actor_role=str(actor["role"]),
                review_state=str(payload["review_task"].get("review_state") or ""),
            )
    if not payload:
        return _error(status_code=404, code="review_task_not_found", message="Review task was not found.", request=request)
    return _success(payload, request)


@app.post("/api/admin/review-tasks/{review_task_id}/ai-verify")
def ai_verify_review_task(request: Request, review_task_id: str) -> JSONResponse:
    actor, session_info = _resolve_session(request)
    _require_csrf(request, session_info=session_info)
    settings: Settings = request.app.state.settings
    with open_connection(settings) as connection:
        _require_review_task_country(
            connection,
            review_task_id=review_task_id,
            country_code=_session_country(session_info),
        )
        detail = load_review_task_detail(
            connection,
            review_task_id=review_task_id,
            actor_role=str(actor["role"]),
        )
        if not detail:
            return _error(
                status_code=404,
                code="review_task_not_found",
                message="Review task was not found.",
                request=request,
            )
        result = run_review_ai_verification(
            connection,
            detail=detail,
            actor=actor,
            request_context={
                "request_id": request.state.request_id,
                "ip_address": _request_ip(request),
                "user_agent": request.headers.get("user-agent"),
            },
        )
    if not result["ok"]:
        return JSONResponse(
            status_code=int(result["status_code"]),
            content={
                "error": {
                    "code": result["error"]["code"],
                    "message": result["error"]["message"],
                    "details": {},
                },
                "data": {"ai_verification": result["ai_verification"]},
                "meta": _meta(request),
            },
        )
    return _success({"ai_verification": result["ai_verification"]}, request)


@app.get("/api/admin/runs")
async def run_status_list(
    request: Request,
    state: Annotated[list[Literal["started", "completed", "failed", "retried"]] | None, Query()] = None,
    run_type: str | None = None,
    partial_only: bool = False,
    started_from: datetime | None = None,
    started_to: datetime | None = None,
    q: str | None = None,
    sort_by: Literal["started_at", "completed_at", "candidate_count", "review_queued_count", "run_type"] = "started_at",
    sort_order: Literal["asc", "desc"] = "desc",
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> JSONResponse:
    _actor, session_info = _resolve_session(request)
    filters = normalize_run_status_filters(
        country_code=_session_country(session_info),
        states=state,
        run_type=run_type,
        partial_only=partial_only,
        started_from=started_from,
        started_to=started_to,
        search=q,
        sort_by=sort_by,
        sort_order=sort_order,
        page=page,
        page_size=page_size,
    )
    settings: Settings = request.app.state.settings
    with open_connection(settings) as connection:
        payload = load_run_status_list(connection, filters=filters)
    return _success(payload, request)


@app.get("/api/admin/runs/{run_id}")
async def run_status_detail(request: Request, run_id: str) -> JSONResponse:
    _actor, session_info = _resolve_session(request)
    settings: Settings = request.app.state.settings
    with open_connection(settings) as connection:
        _require_country_records(
            connection,
            table_name="ingestion_run",
            id_column="run_id",
            record_ids=[run_id],
            country_code=_session_country(session_info),
        )
        payload = load_run_status_detail(connection, run_id=run_id)
    if not payload:
        return _error(status_code=404, code="run_not_found", message="Run was not found.", request=request)
    return _success(payload, request)


@app.post("/api/admin/runs/{run_id}/retry")
async def retry_run(request: Request, run_id: str) -> JSONResponse:
    actor, session_info = _resolve_session(request)
    _require_admin_role(actor)
    _require_csrf(request, session_info=session_info)
    settings: Settings = request.app.state.settings
    with open_connection(settings) as connection:
        _require_country_records(
            connection,
            table_name="ingestion_run",
            id_column="run_id",
            record_ids=[run_id],
            country_code=_session_country(session_info),
        )
        payload = retry_failed_run(
            connection,
            run_id=run_id,
            actor=actor,
            request_context={
                "request_id": request.state.request_id,
                "ip_address": _request_ip(request),
                "user_agent": request.headers.get("user-agent"),
            },
        )
    return _success(payload, request, status_code=202)


@app.get("/api/admin/dashboard-health")
async def dashboard_health(request: Request) -> JSONResponse:
    _actor, session_info = _resolve_session(request)
    settings: Settings = request.app.state.settings
    with open_connection(settings) as connection:
        payload = load_dashboard_health(connection, country_code=_session_country(session_info))
    return _success(payload, request)


@app.post("/api/admin/dashboard-health/retry")
async def retry_dashboard_health(request: Request) -> JSONResponse:
    actor, session_info = _resolve_session(request)
    _require_admin_role(actor)
    _require_csrf(request, session_info=session_info)
    settings: Settings = request.app.state.settings
    with open_connection(settings) as connection:
        payload = request_manual_aggregate_refresh(
            connection,
            actor=actor,
            country_code=_session_country(session_info),
            request_context={
                "request_id": request.state.request_id,
                "ip_address": _request_ip(request),
                "user_agent": request.headers.get("user-agent"),
            },
        )
    payload["launch"] = launch_aggregate_refresh_runner()
    return _success(payload, request, status_code=202)


@app.get("/api/admin/change-history")
async def change_history_list(
    request: Request,
    product_id: str | None = None,
    bank_code: str | None = None,
    product_type: str | None = None,
    change_type: Literal["New", "Updated", "Discontinued", "Reclassified", "ManualOverride"] | None = None,
    changed_from: datetime | None = None,
    changed_to: datetime | None = None,
    q: str | None = None,
    sort_by: Literal["detected_at", "change_type", "product_name", "bank_code"] = "detected_at",
    sort_order: Literal["asc", "desc"] = "desc",
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> JSONResponse:
    _actor, session_info = _resolve_session(request)
    filters = normalize_change_history_filters(
        country_code=_session_country(session_info),
        product_id=product_id,
        bank_code=bank_code,
        product_type=product_type,
        change_type=change_type,
        changed_from=changed_from,
        changed_to=changed_to,
        search=q,
        sort_by=sort_by,
        sort_order=sort_order,
        page=page,
        page_size=page_size,
    )
    settings: Settings = request.app.state.settings
    with open_connection(settings) as connection:
        payload = load_change_history_list(connection, filters=filters)
    return _success(payload, request)


async def _handle_review_decision(
    request: Request,
    *,
    review_task_id: str,
    action_type: Literal["approve", "reject", "edit_approve", "defer"],
    payload: ReviewDecisionRequest,
) -> JSONResponse:
    actor, session_info = _resolve_session(request)
    _require_csrf(request, session_info=session_info)
    settings: Settings = request.app.state.settings
    aggregate_refresh_request: dict[str, Any] | None = None
    with open_connection(settings) as connection:
        _require_review_task_country(
            connection,
            review_task_id=review_task_id,
            country_code=_session_country(session_info),
        )
        result = apply_review_decision(
            connection,
            review_task_id=review_task_id,
            action_type=action_type,
            actor=actor,
            reason_code=payload.reason_code,
            reason_text=payload.reason_text,
            override_payload=payload.override_payload,
            context=ReviewRequestContext(
                request_id=request.state.request_id,
                ip_address=_request_ip(request),
                user_agent=request.headers.get("user-agent"),
            ),
        )
        if action_type in {"approve", "edit_approve"} and result.get("product_id"):
            aggregate_refresh_request = queue_review_aggregate_refresh_request(
                connection,
                actor=actor,
                request_context={
                    "request_id": request.state.request_id,
                    "ip_address": _request_ip(request),
                    "user_agent": request.headers.get("user-agent"),
                },
                review_task_id=review_task_id,
                product_id=str(result["product_id"]),
                action_type=action_type,
                change_event_types=[str(item) for item in result.get("change_event_types", [])],
                country_code=str(result["country_code"]),
            )
    if aggregate_refresh_request:
        aggregate_refresh_request["launch"] = launch_aggregate_refresh_runner()
    return _success(
        {
            "result": result,
            "aggregate_refresh": aggregate_refresh_request,
        },
        request,
    )


@app.post("/api/admin/review-tasks/{review_task_id}/approve")
async def approve_review_task(request: Request, review_task_id: str, payload: ReviewDecisionRequest) -> JSONResponse:
    return await _handle_review_decision(request, review_task_id=review_task_id, action_type="approve", payload=payload)


@app.post("/api/admin/review-tasks/{review_task_id}/reject")
async def reject_review_task(request: Request, review_task_id: str, payload: ReviewDecisionRequest) -> JSONResponse:
    return await _handle_review_decision(request, review_task_id=review_task_id, action_type="reject", payload=payload)


@app.post("/api/admin/review-tasks/{review_task_id}/edit-approve")
async def edit_approve_review_task(request: Request, review_task_id: str, payload: ReviewDecisionRequest) -> JSONResponse:
    return await _handle_review_decision(request, review_task_id=review_task_id, action_type="edit_approve", payload=payload)


@app.post("/api/admin/review-tasks/{review_task_id}/defer")
async def defer_review_task(request: Request, review_task_id: str, payload: ReviewDecisionRequest) -> JSONResponse:
    return await _handle_review_decision(request, review_task_id=review_task_id, action_type="defer", payload=payload)
