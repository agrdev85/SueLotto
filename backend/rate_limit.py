import os
import time
import logging
from collections import defaultdict
from fastapi import HTTPException, Request
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Dict, List, Tuple

logger = logging.getLogger("suenalotto.ratelimit")

RATE_LIMIT_ENABLED = os.getenv("RATE_LIMIT_ENABLED", "true").lower() == "true"
RATE_LIMIT_REQUESTS = int(os.getenv("RATE_LIMIT_REQUESTS", "60"))
RATE_LIMIT_WINDOW = int(os.getenv("RATE_LIMIT_WINDOW", "60"))
RATE_LIMIT_LOGIN_REQUESTS = int(os.getenv("RATE_LIMIT_LOGIN_REQUESTS", "5"))
RATE_LIMIT_LOGIN_WINDOW = int(os.getenv("RATE_LIMIT_LOGIN_WINDOW", "300"))


class RateLimiter:
    def __init__(self):
        self._windows: Dict[str, List[float]] = defaultdict(list)

    def _clean(self, key: str, window: int):
        now = time.time()
        self._windows[key] = [t for t in self._windows[key] if now - t < window]

    def check(self, key: str, max_requests: int, window: int) -> bool:
        if not RATE_LIMIT_ENABLED:
            return True
        self._clean(key, window)
        if len(self._windows[key]) >= max_requests:
            return False
        self._windows[key].append(time.time())
        return True


_rate_limiter = RateLimiter()


class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host if request.client else "unknown"
        path = request.url.path

        if RATE_LIMIT_ENABLED:
            if path.endswith("/auth/login"):
                ok = _rate_limiter.check(
                    f"login:{client_ip}", RATE_LIMIT_LOGIN_REQUESTS, RATE_LIMIT_LOGIN_WINDOW
                )
                if not ok:
                    logger.warning("Rate limit exceeded for login: %s", client_ip)
                    from fastapi.responses import JSONResponse
                    return JSONResponse(
                        status_code=429,
                        content={"detail": "Demasiados intentos. Espera 5 minutos."},
                    )
            else:
                ok = _rate_limiter.check(
                    f"general:{client_ip}", RATE_LIMIT_REQUESTS, RATE_LIMIT_WINDOW
                )
                if not ok:
                    from fastapi.responses import JSONResponse
                    return JSONResponse(
                        status_code=429,
                        content={"detail": "Demasiadas solicitudes. Intenta de nuevo en un minuto."},
                    )

        response = await call_next(request)
        return response
