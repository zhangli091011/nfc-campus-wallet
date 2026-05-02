"""
Database connection and session management.

Provides SQLAlchemy engine and session factory for database operations.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.declarative import declarative_base
from typing import Generator
import logging

from core.config import get_settings

logger = logging.getLogger(__name__)

# SQLAlchemy base class for ORM models
Base = declarative_base()

# Global engine and session factory
engine = None
SessionLocal = None


def init_database():
    """
    Initialize database engine and session factory with connection pooling.
    
    Connection pooling configuration:
    - pool_size: Number of connections to maintain in the pool
    - max_overflow: Additional connections that can be created beyond pool_size
    - pool_pre_ping: Verify connections are alive before using them
    - pool_timeout: Seconds to wait for a connection from the pool
    - pool_recycle: Recycle connections after this many seconds to prevent stale connections
    
    Prepared statements:
    SQLAlchemy ORM automatically uses prepared statements for all queries,
    which provides:
    - Query plan caching for improved performance
    - Protection against SQL injection
    - Reduced parsing overhead on the database server
    
    Should be called once at application startup.
    """
    global engine, SessionLocal
    
    settings = get_settings()
    
    # Create engine with connection pooling
    # Connection pooling minimizes connection overhead by reusing connections
    # instead of creating new ones for each request (Requirement 19.3)
    engine = create_engine(
        settings.database_url,
        pool_pre_ping=True,  # Verify connections before using (detect stale connections)
        pool_size=settings.database_pool_size,  # Connection pool size
        max_overflow=settings.database_max_overflow,  # Max connections beyond pool_size
        pool_timeout=settings.database_pool_timeout,  # Timeout for getting connection
        pool_recycle=settings.database_pool_recycle,  # Recycle connections to prevent staleness
        echo=False  # Set to True for SQL query logging
    )
    
    # Create session factory
    # Sessions use prepared statements automatically for all ORM queries (Requirement 19.4)
    SessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine
    )
    
    logger.info(
        f"Database connection initialized with pool_size={settings.database_pool_size}, "
        f"max_overflow={settings.database_max_overflow}"
    )


def get_db() -> Generator[Session, None, None]:
    """
    Dependency function to get database session.
    
    Yields:
        Session: SQLAlchemy database session
        
    Usage:
        @app.get("/endpoint")
        def endpoint(db: Session = Depends(get_db)):
            # Use db session here
            pass
    """
    if SessionLocal is None:
        raise RuntimeError("Database not initialized. Call init_database() first.")
    
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables():
    """
    Create all database tables defined by ORM models.
    
    Note: In production, use Alembic migrations instead.
    """
    if engine is None:
        raise RuntimeError("Database not initialized. Call init_database() first.")
    
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created")
