"""
Database configuration for Supabase PostgreSQL.

This module provides database connection setup and session management
using SQLAlchemy with Supabase PostgreSQL backend.
"""

import os
from typing import Generator
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import NullPool, QueuePool
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class DatabaseConfig:
    """Database configuration settings"""

    # Supabase connection details
    SUPABASE_URL = os.getenv("SUPABASE_URL", "https://sspwpkhajtooztzisioo.supabase.co")
    SUPABASE_DB_PASSWORD = os.getenv("SUPABASE_DB_PASSWORD", "")

    # Construct PostgreSQL connection URL
    # Format: postgresql://postgres:[PASSWORD]@db.[PROJECT_REF].supabase.co:5432/postgres
    # Extract project ref from URL
    PROJECT_REF = SUPABASE_URL.replace("https://", "").replace(".supabase.co", "")

    # Database URL for SQLAlchemy
    DATABASE_URL = os.getenv(
        "DATABASE_URL",
        f"postgresql://postgres.{PROJECT_REF}:{SUPABASE_DB_PASSWORD}@aws-0-us-west-1.pooler.supabase.com:6543/postgres"
    )

    # Connection pool settings
    POOL_SIZE = int(os.getenv("DB_POOL_SIZE", "5"))
    MAX_OVERFLOW = int(os.getenv("DB_MAX_OVERFLOW", "10"))
    POOL_TIMEOUT = int(os.getenv("DB_POOL_TIMEOUT", "30"))
    POOL_RECYCLE = int(os.getenv("DB_POOL_RECYCLE", "3600"))  # 1 hour

    # Echo SQL queries (for debugging)
    ECHO_SQL = os.getenv("DB_ECHO_SQL", "false").lower() == "true"


# Create SQLAlchemy engine with connection pooling
def create_db_engine():
    """
    Create SQLAlchemy engine with appropriate connection pooling.

    Returns:
        Engine: SQLAlchemy engine instance

    Security considerations:
    - Uses SSL for connections (Supabase enforces this)
    - Connection pooling to limit database connections
    - Timeout settings to prevent hung connections
    """
    config = DatabaseConfig()

    # Validate that we have a database password
    if not config.SUPABASE_DB_PASSWORD:
        raise ValueError(
            "SUPABASE_DB_PASSWORD environment variable not set. "
            "Please set it in your .env file or environment."
        )

    engine = create_engine(
        config.DATABASE_URL,
        poolclass=QueuePool,
        pool_size=config.POOL_SIZE,
        max_overflow=config.MAX_OVERFLOW,
        pool_timeout=config.POOL_TIMEOUT,
        pool_recycle=config.POOL_RECYCLE,
        pool_pre_ping=True,  # Verify connections before using
        echo=config.ECHO_SQL,
        connect_args={
            "sslmode": "require",  # Enforce SSL connection
            "application_name": "lendx_backend",
        }
    )

    # Add connection event listeners for logging
    @event.listens_for(engine, "connect")
    def receive_connect(dbapi_conn, connection_record):
        """Log when new database connection is established"""
        # Set timezone to UTC for all connections
        cursor = dbapi_conn.cursor()
        cursor.execute("SET timezone='UTC'")
        cursor.close()

    return engine


# Global engine instance (created on first import)
engine = None

def init_db():
    """
    Initialize database engine.

    This should be called once at application startup.

    Returns:
        Engine: SQLAlchemy engine instance
    """
    global engine
    if engine is None:
        engine = create_db_engine()
    return engine


# Session factory
SessionLocal = None

def get_session_factory():
    """
    Get or create session factory.

    Returns:
        sessionmaker: SQLAlchemy session factory
    """
    global SessionLocal
    if SessionLocal is None:
        if engine is None:
            init_db()
        SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=engine
        )
    return SessionLocal


def get_db_session() -> Session:
    """
    Get a database session.

    This creates a new session from the session factory.
    Remember to close the session after use.

    Returns:
        Session: SQLAlchemy session

    Example:
        session = get_db_session()
        try:
            # Use session
            user = session.query(User).first()
        finally:
            session.close()
    """
    factory = get_session_factory()
    return factory()


def get_db() -> Generator[Session, None, None]:
    """
    Dependency function for FastAPI to get database session.

    This is designed to be used with FastAPI's Depends() for
    automatic session management and cleanup.

    Yields:
        Session: SQLAlchemy session

    Example:
        @app.get("/users")
        def get_users(db: Session = Depends(get_db)):
            return db.query(User).all()
    """
    session = get_db_session()
    try:
        yield session
    finally:
        session.close()


def close_db():
    """
    Close database engine and dispose of connection pool.

    This should be called during application shutdown.
    """
    global engine
    if engine is not None:
        engine.dispose()
        engine = None


# Health check function
def check_db_connection() -> bool:
    """
    Check if database connection is healthy.

    Returns:
        bool: True if connection is healthy, False otherwise

    Example:
        if not check_db_connection():
            logger.error("Database connection failed!")
    """
    try:
        session = get_db_session()
        # Execute simple query to verify connection
        session.execute("SELECT 1")
        session.close()
        return True
    except Exception as e:
        print(f"Database connection check failed: {e}")
        return False
