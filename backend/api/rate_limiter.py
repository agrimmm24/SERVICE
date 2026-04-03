from fastapi import HTTPException, Request, status
from collections import defaultdict
import time
from typing import Dict, Tuple, Callable

# Simple in-memory rate limiter supporting granular endpoints
# Structure: { "endpoint_path": { "ip_address": (request_count, last_request_time) } }
rate_limit_store: Dict[str, Dict[str, Tuple[int, float]]] = defaultdict(lambda: defaultdict(lambda: (0, 0.0)))

def get_rate_limiter(limit: int = 5, window_seconds: int = 60) -> Callable:
    """
    Factory function to create a dependency for rate limiting.
    Usage: @app.post("/route", dependencies=[Depends(get_rate_limiter(limit=5, window_seconds=60))])
    """
    async def _rate_limit_dependency(request: Request):
        client_ip = request.client.host if request.client else "unknown"
        endpoint = request.url.path
        current_time = time.time()
        
        count, last_time = rate_limit_store[endpoint][client_ip]
        
        # If time window passed, reset count
        if current_time - last_time > window_seconds:
            count = 1
            last_time = current_time
        else:
            count += 1
            
        rate_limit_store[endpoint][client_ip] = (count, last_time)
        
        if count > limit:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many requests. Please try again later."
            )
        return True
        
    return _rate_limit_dependency

# Default rate limiter (5 requests per 60 seconds) for backwards compatibility
rate_limit = get_rate_limiter(limit=5, window_seconds=60)
