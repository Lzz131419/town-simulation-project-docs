"""Consistent errors and bounded, content-free request diagnostics."""

import time
import uuid
import traceback
from pathlib import Path
from starlette.exceptions import HTTPException
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import OperationalError
from ..telemetry import log


def error(request: Request, status: int, code: str, detail: str, **extra):
    request_id = getattr(request.state, "request_id", "")
    return JSONResponse(
        {"detail": detail, "code": code, "request_id": request_id, **extra},
        status_code=status,
        headers={"X-Request-ID": request_id},
    )


def configure_http(app: FastAPI):
    @app.exception_handler(HTTPException)
    async def http_error(request, exc):
        response = error(
            request,
            exc.status_code,
            {401: "unauthenticated", 403: "forbidden", 404: "not_found", 409: "conflict"}.get(
                exc.status_code, "request_rejected"
            ),
            exc.detail,
        )
        if exc.headers:
            response.headers.update(exc.headers)
        return response

    @app.exception_handler(ValueError)
    async def invalid(request, exc):
        return error(request, 400, "invalid_command", str(exc))

    @app.exception_handler(RequestValidationError)
    async def validation(request, exc):
        # Never echo input values (passwords, API keys, messages) in error responses.
        fields = [{"field": ".".join(map(str, e["loc"])), "type": e["type"]} for e in exc.errors()]
        return error(request, 422, "invalid_input", "提交的参数不符合要求", fields=fields)

    @app.exception_handler(OperationalError)
    async def unavailable(request, exc):
        log("database_unavailable", request_id=getattr(request.state, "request_id", ""))
        return error(request, 503, "storage_unavailable", "存储暂时不可用，请稍后重试")

    @app.exception_handler(Exception)
    async def unexpected(request, exc):
        log(
            "request_failed",
            request_id=getattr(request.state, "request_id", ""),
            error_type=type(exc).__name__,
            frames=[
                f"{Path(f.filename).name}:{f.lineno}:{f.name}"
                for f in traceback.extract_tb(exc.__traceback__)[-6:]
            ],
        )
        return error(request, 500, "internal_error", "服务暂时无法完成请求，请凭请求编号排查")

    @app.middleware("http")
    async def request_trace(request, call_next):
        request.state.request_id = uuid.uuid4().hex
        start = time.perf_counter()
        status = 500
        try:
            origin = request.headers.get("origin")
            if (
                request.method not in {"GET", "HEAD", "OPTIONS"}
                and origin
                and origin.rstrip("/") != str(request.base_url).rstrip("/")
            ):
                response = error(request, 403, "origin_mismatch", "请求来源不匹配")
            else:
                response = await call_next(request)
            status = response.status_code
            response.headers["X-Request-ID"] = request.state.request_id
            return response
        finally:
            if request.url.path.startswith("/api/"):
                log(
                    "http_request",
                    request_id=request.state.request_id,
                    method=request.method,
                    path=request.url.path,
                    status=status,
                    duration_ms=round((time.perf_counter() - start) * 1000, 2),
                )
