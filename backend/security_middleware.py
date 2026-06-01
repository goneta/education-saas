import os
import time
from collections import defaultdict, deque

from fastapi import HTTPException
from starlette.requests import Request
from starlette.responses import Response


RATE_LIMIT_WINDOW_SECONDS = int(os.getenv("RATE_LIMIT_WINDOW_SECONDS", "60"))
RATE_LIMIT_MAX_REQUESTS = int(os.getenv("RATE_LIMIT_MAX_REQUESTS", "120"))
AUTH_RATE_LIMIT_MAX_REQUESTS = int(os.getenv("AUTH_RATE_LIMIT_MAX_REQUESTS", "60"))
MAX_REQUEST_BODY_BYTES = int(os.getenv("MAX_REQUEST_BODY_BYTES", str(2 * 1024 * 1024)))

_requests: dict[str, deque[float]] = defaultdict(deque)


def _client_key(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    ip = forwarded.split(",", 1)[0].strip() if forwarded else (request.client.host if request.client else "unknown")
    return f"{ip}:{request.url.path}"


async def rate_limit_middleware(request: Request, call_next):
    content_length = request.headers.get("content-length")
    if content_length and int(content_length) > MAX_REQUEST_BODY_BYTES:
        raise HTTPException(status_code=413, detail="Request body too large")

    key = _client_key(request)
    now = time.monotonic()
    bucket = _requests[key]
    while bucket and now - bucket[0] > RATE_LIMIT_WINDOW_SECONDS:
        bucket.popleft()

    max_requests = AUTH_RATE_LIMIT_MAX_REQUESTS if request.url.path.startswith("/auth/") else RATE_LIMIT_MAX_REQUESTS
    if len(bucket) >= max_requests:
        raise HTTPException(status_code=429, detail="Too many requests")
    bucket.append(now)
    return await call_next(request)


async def security_headers_middleware(request: Request, call_next):
    response: Response = await call_next(request)
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
    response.headers.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
    response.headers.setdefault("Content-Security-Policy", "default-src 'self'; frame-ancestors 'none'; object-src 'none'; base-uri 'self'")
    if request.url.scheme == "https":
        response.headers.setdefault("Strict-Transport-Security", "max-age=31536000; includeSubDomains")
    return response
