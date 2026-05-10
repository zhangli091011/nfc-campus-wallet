"""
FastAPI middleware for signature verification.

This middleware extracts timestamp and signature from requests,
validates them using the signature utilities, and returns 401 errors
for authentication failures. All authentication failures are logged.
"""

import logging
from typing import Optional
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from core.security import verify_request
from core.exceptions import (
    SignatureError,
    TimestampExpiredError,
    TimestampInvalidError,
    SignatureVerificationError
)
from core.config import get_settings
from utils.structured_logger import get_structured_logger

logger = logging.getLogger(__name__)
structured_logger = get_structured_logger(__name__)


# CORS headers to include in all error responses
CORS_HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Credentials": "true",
    "Access-Control-Allow-Methods": "*",
    "Access-Control-Allow-Headers": "*",
    "Access-Control-Expose-Headers": "*",
}


def _cors_json_response(status_code: int, content: dict) -> JSONResponse:
    """Create a JSONResponse with CORS headers included."""
    return JSONResponse(
        status_code=status_code,
        content=content,
        headers=CORS_HEADERS
    )


class SignatureVerificationMiddleware(BaseHTTPMiddleware):
    """
    Middleware to verify request signatures and timestamps.
    
    Extracts authentication parameters from query strings (GET) or
    request body (POST), validates them, and rejects unauthorized requests.
    """
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.settings = get_settings()
        self.secret_key = self.settings.secret_key
        self.time_window = self.settings.timestamp_window
        
        # Endpoints that bypass authentication
        self.bypass_paths = {"/health", "/docs", "/redoc", "/openapi.json", "/transactions", "/leaderboard"}
        # Path prefixes that bypass authentication (for JWT-authenticated endpoints)
        self.bypass_prefixes = [
            "/booths", "/products", "/auth", "/events", "/participants",
            "/api/stock", "/users", "/reports", "/leaderboard",
            "/refund", "/correction", "/stocks", "/exports",
            "/cash-reconciliation", "/api/trade", "/api/bank",
            "/merchant",
        ]
        # Paths that support event mode (no signature required when event_id + card_uid provided)
        self.event_mode_paths = {"/recharge", "/pay", "/balance"}
    
    async def dispatch(self, request: Request, call_next):
        """
        Process request through signature verification.
        
        Args:
            request: Incoming HTTP request
            call_next: Next middleware/handler in chain
            
        Returns:
            Response from next handler or 401 error response
        """
        # Bypass authentication for OPTIONS requests (CORS preflight)
        if request.method == "OPTIONS":
            return await call_next(request)
        
        # Bypass authentication for health check and docs
        if request.url.path in self.bypass_paths:
            return await call_next(request)
        
        # Bypass authentication for JWT-authenticated endpoints
        for prefix in self.bypass_prefixes:
            if request.url.path.startswith(prefix):
                return await call_next(request)
        
        try:
            # Extract authentication parameters based on method
            if request.method == "GET":
                auth_params = await self._extract_from_query(request)
            else:  # POST, PUT, etc.
                auth_params = await self._extract_from_body(request)
            
            # Check if event mode for paths that support it
            if auth_params == {} and request.url.path in self.event_mode_paths:
                # Event mode - bypass signature verification
                logger.info(f"Event mode request - bypassing signature verification: {request.url.path}")
                return await call_next(request)
            
            # Check if event mode (empty dict means bypass signature verification)
            # Note: event_mode_paths are already handled above, this is for any other paths
            if auth_params == {}:
                # Event mode on unsupported path - still require authentication
                logger.warning(
                    f"Event mode not supported for path: {request.url.path}"
                )
                structured_logger.log_authentication_failure(
                    endpoint=request.url.path,
                    reason="Event mode not supported for this endpoint",
                    error_code="AUTH_ERROR"
                )
                return _cors_json_response(
                    status_code=401,
                    content={
                        "error_code": "AUTH_ERROR",
                        "message": "Event mode not supported for this endpoint. Please use JWT authentication."
                    }
                )
            
            # Verify request authentication
            if auth_params:
                verify_request(
                    uid=auth_params["uid"],
                    timestamp=auth_params["timestamp"],
                    signature=auth_params["signature"],
                    secret_key=self.secret_key,
                    time_window=self.time_window,
                    amount=auth_params.get("amount")
                )
            else:
                # Missing authentication parameters
                logger.warning(
                    f"Authentication failed: Missing parameters - "
                    f"method={request.method}, path={request.url.path}"
                )
                structured_logger.log_authentication_failure(
                    endpoint=request.url.path,
                    reason="Missing authentication parameters",
                    error_code="AUTH_ERROR"
                )
                return _cors_json_response(
                    status_code=401,
                    content={
                        "error_code": "AUTH_ERROR",
                        "message": "Missing authentication parameters"
                    }
                )
            
            # Authentication successful, proceed to next handler
            response = await call_next(request)
            return response
            
        except TimestampExpiredError as e:
            logger.warning(
                f"Authentication failed: Timestamp expired - "
                f"path={request.url.path}, reason={str(e)}"
            )
            structured_logger.log_authentication_failure(
                endpoint=request.url.path,
                reason=f"Timestamp expired: {str(e)}",
                uid=auth_params.get("uid") if auth_params else None,
                timestamp=auth_params.get("timestamp") if auth_params else None,
                error_code="TIMESTAMP_EXPIRED"
            )
            return _cors_json_response(
                status_code=401,
                content={
                    "error_code": "TIMESTAMP_EXPIRED",
                    "message": "Request timestamp expired"
                }
            )
        
        except TimestampInvalidError as e:
            logger.warning(
                f"Authentication failed: Invalid timestamp - "
                f"path={request.url.path}, reason={str(e)}"
            )
            structured_logger.log_authentication_failure(
                endpoint=request.url.path,
                reason=f"Invalid timestamp: {str(e)}",
                uid=auth_params.get("uid") if auth_params else None,
                timestamp=auth_params.get("timestamp") if auth_params else None,
                error_code="TIMESTAMP_INVALID"
            )
            return _cors_json_response(
                status_code=401,
                content={
                    "error_code": "TIMESTAMP_INVALID",
                    "message": "Request timestamp is invalid"
                }
            )
        
        except SignatureVerificationError as e:
            logger.warning(
                f"Authentication failed: Signature verification failed - "
                f"path={request.url.path}, reason={str(e)}"
            )
            structured_logger.log_authentication_failure(
                endpoint=request.url.path,
                reason=f"Signature verification failed: {str(e)}",
                uid=auth_params.get("uid") if auth_params else None,
                timestamp=auth_params.get("timestamp") if auth_params else None,
                error_code="SIGNATURE_INVALID"
            )
            return _cors_json_response(
                status_code=401,
                content={
                    "error_code": "SIGNATURE_INVALID",
                    "message": "Request signature verification failed"
                }
            )
        
        except Exception as e:
            logger.error(
                f"Authentication error: Unexpected exception - "
                f"path={request.url.path}, error={str(e)}",
                exc_info=True
            )
            structured_logger.log_authentication_failure(
                endpoint=request.url.path,
                reason=f"Unexpected error: {str(e)}",
                uid=auth_params.get("uid") if auth_params else None,
                error_code="AUTH_ERROR"
            )
            return _cors_json_response(
                status_code=401,
                content={
                    "error_code": "AUTH_ERROR",
                    "message": "Request authentication failed"
                }
            )
    
    async def _extract_from_query(self, request: Request) -> Optional[dict]:
        """
        Extract authentication parameters from query string.
        
        Supports two modes:
        1. Legacy mode: uid, timestamp, signature
        2. Event mode: event_id, card_uid (bypasses signature verification)
        
        Args:
            request: HTTP request with query parameters
            
        Returns:
            Dictionary with uid, timestamp, signature, or None if missing
            Returns empty dict {} for event mode (to bypass signature check)
        """
        query_params = request.query_params
        
        # Check for event mode parameters (event_id + card_uid)
        event_id = query_params.get("event_id")
        card_uid = query_params.get("card_uid")
        
        if event_id and card_uid:
            # Event mode - bypass signature verification
            # Return empty dict to indicate authentication should be bypassed
            return {}
        
        # Legacy mode - check for signature parameters
        uid = query_params.get("uid")
        timestamp_str = query_params.get("timestamp")
        signature = query_params.get("signature")
        
        if not all([uid, timestamp_str, signature]):
            return None
        
        try:
            timestamp = int(timestamp_str)
        except (ValueError, TypeError):
            return None
        
        return {
            "uid": uid,
            "timestamp": timestamp,
            "signature": signature
        }
    
    async def _extract_from_body(self, request: Request) -> Optional[dict]:
        """
        Extract authentication parameters from request body.
        
        Supports two modes:
        1. Legacy mode: uid, timestamp, signature, amount
        2. Event mode: event_id, card_uid (bypasses signature verification)
        
        Args:
            request: HTTP request with JSON body
            
        Returns:
            Dictionary with uid, timestamp, signature, amount (optional), or None if missing
            Returns empty dict {} for event mode (to bypass signature check)
        """
        try:
            # Read body and cache it for downstream handlers
            body = await request.body()
            
            # Parse JSON body
            import json
            body_data = json.loads(body.decode("utf-8"))
            
            # Check for event mode parameters (event_id + card_uid)
            event_id = body_data.get("event_id")
            card_uid = body_data.get("card_uid")
            
            logger.debug(f"Body data: event_id={event_id}, card_uid={card_uid}, keys={list(body_data.keys())}")
            
            if event_id and card_uid:
                # Event mode - bypass signature verification
                # Return empty dict to indicate authentication should be bypassed
                logger.info(f"Event mode detected in body: event_id={event_id}, card_uid={card_uid}")
                return {}
            
            # Legacy mode - check for signature parameters
            uid = body_data.get("uid")
            timestamp = body_data.get("timestamp")
            signature = body_data.get("signature")
            amount = body_data.get("amount")
            
            if not all([uid, timestamp, signature]):
                logger.debug(f"Legacy mode parameters incomplete: uid={uid}, timestamp={timestamp}, signature={signature}")
                return None
            
            # Ensure timestamp is integer
            if not isinstance(timestamp, int):
                try:
                    timestamp = int(timestamp)
                except (ValueError, TypeError):
                    return None
            
            result = {
                "uid": uid,
                "timestamp": timestamp,
                "signature": signature
            }
            
            # Include amount if present (for payment/recharge requests)
            if amount is not None:
                result["amount"] = float(amount)
            
            return result
            
        except (json.JSONDecodeError, UnicodeDecodeError, AttributeError):
            return None
