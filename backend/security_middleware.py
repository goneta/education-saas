import os
import time
from collections import defaultdict, deque

from starlette.requests import Request
from starlette.responses import JSONResponse, Response


# Rate limiting is a production concern (the in-memory limiter is per-process and
# not meaningful in dev/test). Enabled in production, or when explicitly forced.
RATE_LIMIT_ENABLED = os.getenv("RATE_LIMIT_ENABLED", "").lower() == "true" or os.getenv("APP_ENV") == "production"
RATE_LIMIT_WINDOW_SECONDS = int(os.getenv("RATE_LIMIT_WINDOW_SECONDS", "60"))
RATE_LIMIT_MAX_REQUESTS = int(os.getenv("RATE_LIMIT_MAX_REQUESTS", "120"))
AUTH_RATE_LIMIT_MAX_REQUESTS = int(os.getenv("AUTH_RATE_LIMIT_MAX_REQUESTS", "60"))
MAX_REQUEST_BODY_BYTES = int(os.getenv("MAX_REQUEST_BODY_BYTES", str(2 * 1024 * 1024)))

_requests: dict[str, deque[float]] = defaultdict(deque)
_redis_client = None


def _redis():
    global _redis_client
    redis_url = os.getenv("REDIS_URL")
    if not redis_url:
        return None
    if _redis_client is not None:
        return _redis_client
    try:
        import redis  # type: ignore
        _redis_client = redis.from_url(redis_url, decode_responses=True)
        _redis_client.ping()
        return _redis_client
    except Exception:
        _redis_client = False
        return None


def _client_key(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    ip = forwarded.split(",", 1)[0].strip() if forwarded else (request.client.host if request.client else "unknown")
    return f"{ip}:{request.url.path}"


async def rate_limit_middleware(request: Request, call_next):
    content_length = request.headers.get("content-length")
    if content_length and int(content_length) > MAX_REQUEST_BODY_BYTES:
        # Return (not raise) inside HTTP middleware: raising HTTPException here
        # breaks the BaseHTTPMiddleware chain (anyio EndOfStream) under load.
        return JSONResponse({"detail": "Request body too large"}, status_code=413)

    if not RATE_LIMIT_ENABLED:
        return await call_next(request)

    key = _client_key(request)
    max_requests = AUTH_RATE_LIMIT_MAX_REQUESTS if request.url.path.startswith("/auth/") else RATE_LIMIT_MAX_REQUESTS
    redis_client = _redis()
    if redis_client:
        redis_key = f"rate:{key}"
        count = redis_client.incr(redis_key)
        if count == 1:
            redis_client.expire(redis_key, RATE_LIMIT_WINDOW_SECONDS)
        if count > max_requests:
            return JSONResponse({"detail": "Too many requests"}, status_code=429)
        return await call_next(request)

    now = time.monotonic()
    bucket = _requests[key]
    while bucket and now - bucket[0] > RATE_LIMIT_WINDOW_SECONDS:
        bucket.popleft()

    if len(bucket) >= max_requests:
        return JSONResponse({"detail": "Too many requests"}, status_code=429)
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
