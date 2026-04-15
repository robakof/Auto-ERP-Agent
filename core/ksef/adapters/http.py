"""Thin httpx wrapper for KSeF API.

Responsibilities:
- base_url, default headers, timeout
- retry 5xx / connection / timeout via tenacity (exp backoff)
- respect Retry-After on 429
- map error responses to KSefApiError / KSefTransportError
- structured JSON logging

Upper layers (KSeFApiClient, KSefAuth) call typed `request_json`/`request_bytes`
and never touch httpx directly.
"""
from __future__ import annotations

import json
import logging
import time
from typing import Any

import httpx
from tenacity import (
    RetryCallState,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from core.ksef.exceptions import KSefApiError, KSefTransportError

_LOG = logging.getLogger("ksef.http")

_DEFAULT_TIMEOUT = httpx.Timeout(connect=10.0, read=30.0, write=30.0, pool=10.0)
_RETRY_ATTEMPTS = 3


def _is_retryable_status(status: int) -> bool:
    return status >= 500 or status == 429


def _extract_error(body: Any, status: int) -> KSefApiError:
    """Parse KSeF error payload into a typed exception.

    Supports both `ExceptionResponse` (legacy) and `problem+json` shapes.
    """
    error_code: str | None = None
    message = ""
    details: list[str] = []

    if isinstance(body, dict):
        exceptions = body.get("exception", {}).get("exceptionDetailList") or []
        if exceptions:
            first = exceptions[0]
            error_code = str(first.get("exceptionCode") or "") or None
            message = str(first.get("exceptionDescription") or "")
            for raw in first.get("details") or []:
                details.append(str(raw))
        else:
            # problem+json shape
            error_code = str(body.get("type") or body.get("title") or "") or None
            message = str(body.get("detail") or body.get("title") or "")
    else:
        message = str(body)[:500]

    if not message:
        message = f"HTTP {status}"
    return KSefApiError(status, error_code, message, details)


def _log_retry(state: RetryCallState) -> None:
    outcome = state.outcome
    exc = outcome.exception() if outcome else None
    _LOG.warning(
        json.dumps({
            "event": "ksef_http_retry",
            "attempt": state.attempt_number,
            "error": repr(exc) if exc else None,
        })
    )


class KSefHttp:
    """httpx wrapper with retry, 429 handling, and typed errors.

    `client` is injected so tests can pass respx-mounted `httpx.Client` instances.
    """

    def __init__(
        self,
        base_url: str,
        client: httpx.Client | None = None,
        timeout: httpx.Timeout = _DEFAULT_TIMEOUT,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._client = client or httpx.Client(
            base_url=self._base_url,
            timeout=timeout,
            headers={"User-Agent": "mrowisko-ksef/0.1"},
        )

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> "KSefHttp":
        return self

    def __exit__(self, *exc: Any) -> None:
        self.close()

    def request_json(
        self,
        method: str,
        path: str,
        *,
        bearer: str | None = None,
        json_body: Any = None,
        params: dict[str, Any] | None = None,
        expected_statuses: tuple[int, ...] = (200,),
    ) -> Any:
        """Send request, return parsed JSON body (dict or list). Raises KSefApiError / KSefTransportError."""
        resp = self._send(method, path, bearer=bearer, json_body=json_body, params=params)
        if resp.status_code not in expected_statuses:
            raise _extract_error(_safe_json(resp), resp.status_code)
        parsed = _safe_json(resp)
        return parsed if parsed is not None else {}

    def request_bytes(
        self,
        method: str,
        path: str,
        *,
        bearer: str | None = None,
        params: dict[str, Any] | None = None,
        expected_statuses: tuple[int, ...] = (200,),
    ) -> tuple[bytes, str]:
        """Send request, return raw body + content-type (e.g. for UPO XML)."""
        resp = self._send(method, path, bearer=bearer, params=params)
        if resp.status_code not in expected_statuses:
            raise _extract_error(_safe_json(resp), resp.status_code)
        return resp.content, resp.headers.get("content-type", "")

    def request_empty(
        self,
        method: str,
        path: str,
        *,
        bearer: str | None = None,
        expected_statuses: tuple[int, ...] = (204,),
    ) -> None:
        """Send request, expect empty body (e.g. close session, logout)."""
        resp = self._send(method, path, bearer=bearer)
        if resp.status_code not in expected_statuses:
            raise _extract_error(_safe_json(resp), resp.status_code)

    # ---- internals ---------------------------------------------------

    @retry(
        reraise=True,
        stop=stop_after_attempt(_RETRY_ATTEMPTS),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type(KSefTransportError),
        before_sleep=_log_retry,
    )
    def _send(
        self,
        method: str,
        path: str,
        *,
        bearer: str | None = None,
        json_body: Any = None,
        params: dict[str, Any] | None = None,
    ) -> httpx.Response:
        headers: dict[str, str] = {}
        if bearer:
            headers["Authorization"] = f"Bearer {bearer}"
        if json_body is not None:
            headers["Content-Type"] = "application/json"

        try:
            resp = self._client.request(
                method,
                path,
                headers=headers or None,
                json=json_body,
                params=params,
            )
        except (httpx.TimeoutException, httpx.TransportError) as exc:
            raise KSefTransportError(f"transport error for {method} {path}: {exc}", cause=exc) from exc

        if resp.status_code == 429:
            # Double-sleep intentional: Retry-After honours API throttle window,
            # tenacity exp backoff (1→4→10s) adds jitter safety for retry attempts.
            retry_after = resp.headers.get("retry-after")
            if retry_after is not None:
                self._sleep_retry_after(retry_after)
            raise KSefTransportError(f"429 Too Many Requests for {method} {path}")

        if resp.status_code >= 500:
            raise KSefTransportError(f"{resp.status_code} server error for {method} {path}")

        return resp

    @staticmethod
    def _sleep_retry_after(value: str) -> None:
        try:
            seconds = float(value)
        except ValueError:
            return
        time.sleep(max(0.0, min(seconds, 60.0)))


def _safe_json(resp: httpx.Response) -> Any:
    try:
        return resp.json()
    except ValueError:
        return None
