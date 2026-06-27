# src/api/middleware.py
import logging
import uuid
import time
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from configs.settings import settings

logger = logging.getLogger(__name__)

import jwt

def get_limiter_key(request: Request) -> str:
    if hasattr(request.state, "user_sub") and request.state.user_sub:
        return request.state.user_sub
    return get_remote_address(request)

# Layer 4b: Rate Limiter
limiter = Limiter(key_func=get_limiter_key, default_limits=[f"{settings.RATE_LIMIT_PER_USER}/minute"])

class JWTExtractionMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        sub = None
        auth = request.headers.get("Authorization")
        if auth and auth.startswith("Bearer "):
            token = auth.split(" ")[1]
            try:
                unverified_claims = jwt.decode(token, options={"verify_signature": False})
                sub = unverified_claims.get("sub")
            except Exception:
                pass
        request.state.user_sub = sub
        return await call_next(request)

class RequestTracingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid.uuid4())
        # Attach to request state
        request.state.request_id = request_id
        
        start_time = time.time()
        
        try:
            response = await call_next(request)
            
            process_time = (time.time() - start_time) * 1000
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Process-Time-Ms"] = str(int(process_time))
            
            logger.info(f"Request {request.method} {request.url.path} completed in {process_time:.2f}ms. ID: {request_id}")
            return response
        except Exception as e:
            process_time = (time.time() - start_time) * 1000
            logger.error(f"Request {request.method} {request.url.path} failed in {process_time:.2f}ms. ID: {request_id}. Error: {e}")
            raise
