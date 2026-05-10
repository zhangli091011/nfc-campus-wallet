"""
Main application entry point for NFC Campus E-Wallet System.

This module initializes the FastAPI application, loads configuration,
and sets up routes and middleware.
"""

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException
import logging
import os

# 更新导入路径 - 使用 core 模块
from core.config import load_settings, get_settings
from core.database import init_database
from middleware import SignatureVerificationMiddleware
from middleware.request_logging import RequestLoggingMiddleware

# 路由导入
from routes.balance import router as balance_router
from routes.payment import router as payment_router
from routes.recharge import router as recharge_router
from routes.transactions import router as transactions_router
from routes.leaderboard import router as leaderboard_router
from routes.reports import router as reports_router
from routes.events import router as events_router
from routes.participants import router as participants_router
from routes.booths import router as booths_router
from routes.products import router as products_router
from routes.auth import router as auth_router
from routes.users import router as users_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Database initialization is handled by start_server.py
# Do NOT initialize here to avoid duplicate initialization


def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application.
    
    Returns:
        FastAPI: Configured application instance
    """
    # Load configuration
    try:
        load_settings()
        settings = get_settings()
        logger.info("Configuration loaded successfully")
    except ValueError as e:
        logger.error(f"Failed to load configuration: {e}")
        raise
    
    # Initialize database (safe to call multiple times)
    try:
        init_database()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise
    
    # Create FastAPI app
    app = FastAPI(
        title="NFC Campus E-Wallet System",
        description="Backend API for cashless campus transactions using NFC cards",
        version="1.0.0"
    )
    
    # Middleware order: Middleware added LAST runs FIRST (outermost)
    # So we add in reverse order: inner -> outer
    
    # 1. Request logging (innermost - runs last on request, first on response)
    app.add_middleware(RequestLoggingMiddleware)
    
    # 2. Signature verification (middle layer)
    app.add_middleware(SignatureVerificationMiddleware)
    
    # 3. CORS middleware (outermost - runs first on request, last on response)
    # This ensures CORS headers are added to ALL responses, including 401/403 errors
    # from the SignatureVerificationMiddleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure appropriately for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["*"],
    )
    
    # Add exception handlers to ensure CORS headers are included in error responses
    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        """Handle HTTP exceptions and ensure CORS headers are included"""
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail},
            headers={
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Credentials": "true",
                "Access-Control-Allow-Methods": "*",
                "Access-Control-Allow-Headers": "*",
            }
        )
    
    @app.exception_handler(HTTPException)
    async def fastapi_exception_handler(request: Request, exc: HTTPException):
        """Handle FastAPI HTTP exceptions and ensure CORS headers are included"""
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail},
            headers={
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Credentials": "true",
                "Access-Control-Allow-Methods": "*",
                "Access-Control-Allow-Headers": "*",
            }
        )
    
    # Register routes
    # Authentication routes (first, for login and user management)
    app.include_router(auth_router, tags=["authentication"])
    app.include_router(users_router, tags=["users"])
    
    # Booth management system
    app.include_router(booths_router, tags=["booths"])
    app.include_router(products_router, tags=["products"])
    
    # Event and participant management
    app.include_router(events_router, tags=["events"])
    app.include_router(participants_router, tags=["participants"])
    
    # Transaction endpoints
    app.include_router(balance_router, tags=["balance"])
    app.include_router(payment_router, tags=["payment"])
    app.include_router(recharge_router, tags=["recharge"])
    app.include_router(transactions_router, tags=["transactions"])
    app.include_router(leaderboard_router, tags=["leaderboard"])
    app.include_router(reports_router, tags=["reports"])
    
    # Event close and cash reconciliation
    from routes.event_close import router as event_close_router
    from routes.cash_reconciliation import router as cash_reconciliation_router
    from routes.exports import router as exports_router
    
    app.include_router(event_close_router, tags=["events"])
    app.include_router(cash_reconciliation_router, tags=["cash-reconciliation"])
    app.include_router(exports_router, tags=["exports"])
    
    # Stock market system
    from routes.stocks import router as stocks_router
    from routes.stock_api import router as stock_api_router
    
    app.include_router(stocks_router, tags=["stock-market"])
    app.include_router(stock_api_router, tags=["stock-api"])
    
    # Bank credit system (官方银行信用垫资)
    from routes.bank_credit import router as bank_credit_router, legacy_router as bank_credit_legacy_router
    app.include_router(bank_credit_router, tags=["bank-credit"])
    app.include_router(bank_credit_legacy_router, tags=["bank-credit-legacy"])
    
    # Merchant system (商户自主注册与管理)
    from routes.merchant import router as merchant_router
    from routes.cost_evidence import router as cost_evidence_router
    app.include_router(merchant_router, tags=["merchant"])
    app.include_router(cost_evidence_router, tags=["merchant-cost-evidence"])
    
    # Refund monitoring system (退款监控与审计)
    from routes.refund_monitor import router as refund_monitor_router
    app.include_router(refund_monitor_router, tags=["refund-monitor"])
    
    # Trade operations (退款等交易操作)
    from routes.refund import router as refund_router
    app.include_router(refund_router, tags=["trade"])
    
    # Health check endpoint
    @app.get("/health")
    async def health_check():
        """Health check endpoint."""
        return {"status": "healthy", "service": "nfc-campus-wallet"}
    
    # Mount uploads directory for static file serving
    uploads_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "uploads")
    os.makedirs(uploads_dir, exist_ok=True)
    app.mount("/uploads", StaticFiles(directory=uploads_dir), name="uploads")
    
    logger.info(f"Application initialized on {settings.server_host}:{settings.server_port}")
    
    return app


# Create app instance (lazy initialization for testing)
app = None


def get_app() -> FastAPI:
    """Get or create the application instance."""
    global app
    if app is None:
        app = create_app()
    return app


# Initialize app for production use
try:
    app = create_app()
except ValueError:
    # Allow import without configuration for testing
    pass


if __name__ == "__main__":
    import uvicorn
    
    if app is None:
        app = create_app()
    
    settings = get_settings()
    uvicorn.run(
        "app.main:app",
        host=settings.server_host,
        port=settings.server_port,
        reload=True
    )
