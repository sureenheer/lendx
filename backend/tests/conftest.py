"""
Pytest configuration and shared fixtures for LendX tests.

This file provides test fixtures and configuration that are shared
across all test modules.
"""

import os
import pytest
from decimal import Decimal
from datetime import datetime, timedelta
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from backend.models.database import Base, User, Pool, Application, Loan

# Set test environment variables before importing config
os.environ["SUPABASE_DB_PASSWORD"] = os.getenv("SUPABASE_DB_PASSWORD", "")
os.environ["DATABASE_URL"] = os.getenv(
    "DATABASE_URL",
    f"postgresql://postgres.sspwpkhajtooztzisioo:{os.environ['SUPABASE_DB_PASSWORD']}@aws-0-us-west-1.pooler.supabase.com:6543/postgres"
)


@pytest.fixture(scope="session")
def db_engine():
    """
    Create a database engine for the test session.
    This is created once per test session.
    """
    from backend.config.database import DatabaseConfig

    config = DatabaseConfig()

    # Skip if no password set (for local testing without DB)
    if not config.SUPABASE_DB_PASSWORD:
        pytest.skip("SUPABASE_DB_PASSWORD not set")

    engine = create_engine(
        config.DATABASE_URL,
        echo=False,
        connect_args={
            "sslmode": "require",
            "application_name": "lendx_tests",
        }
    )

    # Verify connection
    try:
        with engine.connect() as conn:
            conn.execute("SELECT 1")
    except Exception as e:
        pytest.skip(f"Cannot connect to database: {e}")

    yield engine
    engine.dispose()


@pytest.fixture(scope="function")
def db_session(db_engine):
    """
    Create a new database session for each test.
    Automatically rolls back after each test to keep tests isolated.
    """
    connection = db_engine.connect()
    transaction = connection.begin()
    session = sessionmaker(bind=connection)()

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def sample_user_address():
    """Sample XRP wallet address for testing"""
    return "rN7n7otQDd6FczFgLdlqtyMVrn3WnFBBEx"


@pytest.fixture
def sample_user_did():
    """Sample DID for testing"""
    return "did:xrpl:1:rN7n7otQDd6FczFgLdlqtyMVrn3WnFBBEx"


@pytest.fixture
def create_test_user(db_session):
    """
    Factory fixture to create test users.

    Usage:
        user = create_test_user("rAddress123", "did:xrpl:1:test")
    """
    def _create_user(address: str, did: str = None):
        user = User(address=address, did=did)
        db_session.add(user)
        db_session.commit()
        return user

    return _create_user


@pytest.fixture
def create_test_pool(db_session):
    """
    Factory fixture to create test pools.

    Usage:
        pool = create_test_pool(
            pool_address="MPT123",
            issuer_address="rAddress123",
            total_balance=10000.0
        )
    """
    def _create_pool(
        pool_address: str,
        issuer_address: str,
        total_balance: float = 10000.0,
        current_balance: float = None,
        minimum_loan: float = 100.0,
        duration_days: int = 30,
        interest_rate: float = 5.5,
        tx_hash: str = "TEST_TX_HASH"
    ):
        if current_balance is None:
            current_balance = total_balance

        pool = Pool(
            pool_address=pool_address,
            issuer_address=issuer_address,
            total_balance=Decimal(str(total_balance)),
            current_balance=Decimal(str(current_balance)),
            minimum_loan=Decimal(str(minimum_loan)),
            duration_days=duration_days,
            interest_rate=Decimal(str(interest_rate)),
            tx_hash=tx_hash
        )
        db_session.add(pool)
        db_session.commit()
        return pool

    return _create_pool


@pytest.fixture
def create_test_application(db_session):
    """
    Factory fixture to create test applications.

    Usage:
        app = create_test_application(
            application_address="APP123",
            borrower_address="rBorrower",
            pool_address="POOL123"
        )
    """
    def _create_application(
        application_address: str,
        borrower_address: str,
        pool_address: str,
        principal: float = 1000.0,
        interest: float = 55.0,
        state: str = "PENDING",
        application_date: datetime = None,
        dissolution_date: datetime = None,
        tx_hash: str = "TEST_APP_TX"
    ):
        if application_date is None:
            application_date = datetime.now()
        if dissolution_date is None:
            dissolution_date = application_date + timedelta(days=30)

        app = Application(
            application_address=application_address,
            borrower_address=borrower_address,
            pool_address=pool_address,
            application_date=application_date,
            dissolution_date=dissolution_date,
            state=state,
            principal=Decimal(str(principal)),
            interest=Decimal(str(interest)),
            tx_hash=tx_hash
        )
        db_session.add(app)
        db_session.commit()
        return app

    return _create_application


@pytest.fixture
def create_test_loan(db_session):
    """
    Factory fixture to create test loans.

    Usage:
        loan = create_test_loan(
            loan_address="LOAN123",
            pool_address="POOL123",
            borrower_address="rBorrower",
            lender_address="rLender"
        )
    """
    def _create_loan(
        loan_address: str,
        pool_address: str,
        borrower_address: str,
        lender_address: str,
        principal: float = 1000.0,
        interest: float = 55.0,
        state: str = "ONGOING",
        start_date: datetime = None,
        end_date: datetime = None,
        tx_hash: str = "TEST_LOAN_TX"
    ):
        if start_date is None:
            start_date = datetime.now()
        if end_date is None:
            end_date = start_date + timedelta(days=30)

        loan = Loan(
            loan_address=loan_address,
            pool_address=pool_address,
            borrower_address=borrower_address,
            lender_address=lender_address,
            start_date=start_date,
            end_date=end_date,
            principal=Decimal(str(principal)),
            interest=Decimal(str(interest)),
            state=state,
            tx_hash=tx_hash
        )
        db_session.add(loan)
        db_session.commit()
        return loan

    return _create_loan


@pytest.fixture
def cleanup_test_data(db_session):
    """
    Fixture to clean up test data after tests.
    Use this when you need to ensure clean state.
    """
    yield
    # Cleanup happens after test
    db_session.query(Loan).delete()
    db_session.query(Application).delete()
    db_session.query(Pool).delete()
    db_session.query(User).delete()
    db_session.commit()
