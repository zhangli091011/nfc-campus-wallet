"""
Request logging middleware for NFC Campus E-Wallet System.

Logs all API requests with timestamp, endpoint, uid, result status, and duration.
Uses structured JSON format for machine parsing.
"""

import logging
import time
from typing import Optional
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from utils.structured_logger import get_structured_logger

logger = logging.getLogger(__name__)
structured_logger = get_structured_logger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware to log all API requests with structured data.
    
    Captures request details, response status, and execution time.
    """
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
    
    async def dispatch(self, request: Request, call_next):
        """
        Process request and log details.
        
        Args:
            request: Incoming HTTP request
            call_next: Next middleware/handler in chain
            
        Returns:
            Response from next handler
        """
        # Record start time
        start_time = time.time()
        
        # Extract UID from request if available
        uid = await self._extract_uid(request)
        
        # Process request
        response = await call_next(request)
        
        # Calculate duration
        duration_ms = (time.time() - start_time) * 1000
        
        # Determine result status
        result = "success" if response.status_code < 400 else "error"
        
        # Extract error code if available (from response body)
        error_code = None
        if result == "error":
            # For error responses, we can't easily read the body here
            # as it's already been consumed. We'll rely on the status code.
            if response.status_code == 401:
                error_code = "AUTH_ERROR"
            elif response.status_code == 400:
                error_code = "VALIDATION_ERROR"
            elif response.status_code >= 500:
                error_code = "INTERNAL_ERROR"
        
        # Log API request
        structured_logger.log_api_request(
            endpoint=request.url.path,
            method=request.method,
            uid=uid,
            status_code=response.status_code,
            result=result,
            error_code=error_code,
            duration_ms=duration_ms
        )
        
        return response
    
    async def _extract_uid(self, request: Request) -> Optional[str]:
        """
        Extract UID from request (query params or body).
        
        Args:
            request: HTTP request
            
        Returns:
            UID string if found, None otherwise
        """
        # Try query parameters first (for GET requests)
        uid = request.query_params.get("uid")
        if uid:
            return uid
        
        # Try to extract from body (for POST requests)
        # Note: We need to be careful not to consume the body
        # as it needs to be available for downstream handlers
        try:
            # Check if body has already been read
            if hasattr(request.state, "uid"):
                return request.state.uid
            
            # For POST requests, we can't easily read the body here
            # without consuming it. We'll rely on query params or
            # let downstream handlers set it.
            return None
        except Exception:
            return None
