import json
import logging
import os
import time

from starlette.requests import Request

from . import database, models


logger = logging.getLogger("education_saas")
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(message)s"))
    logger.addHandler(handler)
logger.setLevel(os.getenv("LOG_LEVEL", "INFO"))

SLOW_REQUEST_MS = int(os.getenv("SLOW_REQUEST_MS", "1500"))


async def observability_middleware(request: Request, call_next):
    started = time.perf_counter()
    response = await call_next(request)
    elapsed_ms = round((time.perf_counter() - started) * 1000, 2)
    payload = {
        "event": "http_request",
        "method": request.method,
        "path": request.url.path,
        "status_code": response.status_code,
        "latency_ms": elapsed_ms,
        "client_ip": request.client.host if request.client else None,
        "user_agent": request.headers.get("user-agent"),
    }
    logger.info(json.dumps(payload, default=str))
    if response.status_code >= 500 or elapsed_ms >= SLOW_REQUEST_MS:
        db = database.SessionLocal()
        try:
            db.add(models.SecurityEvent(
                event_type="api_5xx" if response.status_code >= 500 else "slow_request",
                severity="high" if response.status_code >= 500 else "medium",
                details=payload,
                ip_address=payload["client_ip"],
                user_agent=payload["user_agent"],
            ))
            db.commit()
        except Exception:
            db.rollback()
        finally:
            db.close()
    return response
