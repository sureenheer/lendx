"""
Test Application model operations.
"""

import pytest
from decimal import Decimal
from datetime import datetime, timedelta
from backend.config.database import get_db_session
from backend.models.database import User, Pool, Application


class TestApplicationModel:
    """Test Application model CRUD operations"""

    @pytest.fixture
    def db_session(self):
        """Provide a database session for tests"""
        session = get_db_session()
        yield session
        session.rollback()
        session.close()

    @pytest.fixture
    def test_lender(self, db_session):
        """Create a test lender"""
        lender = User(
            address="rN7n7otQDd6FczFgLdlqtyMVrn3WnFBBEx",
            did="did:xrpl:1:lender"
        )
        db_session.add(lender)
        db_session.commit()
        return lender

    @pytest.fixture
    def test_borrower(self, db_session):
        """Create a test borrower"""
        borrower = User(
            address="rPEPPER7kfTD9w2To4CQk6UCfuHM9c6GDY",
            did="did:xrpl:1:borrower"
        )
        db_session.add(borrower)
        db_session.commit()
        return borrower

    @pytest.fixture
    def test_pool(self, db_session, test_lender):
        """Create a test pool"""
        pool = Pool(
            pool_address="00000000F1A7E3E8B7F0000000000000000000000000000000000001",
            issuer_address=test_lender.address,
            total_balance=Decimal("10000.00"),
            current_balance=Decimal("10000.00"),
            minimum_loan=Decimal("100.00"),
            duration_days=30,
            interest_rate=Decimal("5.50"),
            tx_hash="POOL_TX_HASH"
        )
        db_session.add(pool)
        db_session.commit()
        return pool

    def test_create_application(self, db_session, test_borrower, test_pool):
        """Test creating a loan application"""
        now = datetime.now()
        application = Application(
            application_address="00000000A1B2C3D4E5F0000000000000000000000000000000000001",
            borrower_address=test_borrower.address,
            pool_address=test_pool.pool_address,
            application_date=now,
            dissolution_date=now + timedelta(days=30),
            state="PENDING",
            principal=Decimal("1000.00"),
            interest=Decimal("55.00"),
            tx_hash="APP_TX_HASH"
        )
        db_session.add(application)
        db_session.commit()

        retrieved = db_session.query(Application).filter_by(
            application_address="00000000A1B2C3D4E5F0000000000000000000000000000000000001"
        ).first()

        assert retrieved is not None
        assert retrieved.state == "PENDING"
        assert retrieved.principal == Decimal("1000.00")

    def test_application_state_validation(self, db_session, test_borrower, test_pool):
        """Test that only valid states are allowed"""
        now = datetime.now()
        application = Application(
            application_address="00000000A1B2C3D4E5F0000000000000000000000000000000000001",
            borrower_address=test_borrower.address,
            pool_address=test_pool.pool_address,
            application_date=now,
            dissolution_date=now + timedelta(days=30),
            state="INVALID_STATE",  # Invalid state
            principal=Decimal("1000.00"),
            interest=Decimal("55.00"),
            tx_hash="APP_TX_HASH"
        )
        db_session.add(application)

        with pytest.raises(Exception):  # Should raise CheckViolation
            db_session.commit()

    def test_query_applications_by_borrower(self, db_session, test_borrower, test_pool):
        """Test querying applications by borrower"""
        now = datetime.now()
        app1 = Application(
            application_address="00000000A1B2C3D4E5F0000000000000000000000000000000000001",
            borrower_address=test_borrower.address,
            pool_address=test_pool.pool_address,
            application_date=now,
            dissolution_date=now + timedelta(days=30),
            state="PENDING",
            principal=Decimal("1000.00"),
            interest=Decimal("55.00"),
            tx_hash="APP1"
        )
        app2 = Application(
            application_address="00000000A1B2C3D4E5F0000000000000000000000000000000000002",
            borrower_address=test_borrower.address,
            pool_address=test_pool.pool_address,
            application_date=now,
            dissolution_date=now + timedelta(days=30),
            state="APPROVED",
            principal=Decimal("500.00"),
            interest=Decimal("27.50"),
            tx_hash="APP2"
        )
        db_session.add_all([app1, app2])
        db_session.commit()

        apps = db_session.query(Application).filter_by(
            borrower_address=test_borrower.address
        ).all()
        assert len(apps) == 2

    def test_query_applications_by_pool(self, db_session, test_borrower, test_pool):
        """Test querying applications by pool"""
        now = datetime.now()
        application = Application(
            application_address="00000000A1B2C3D4E5F0000000000000000000000000000000000001",
            borrower_address=test_borrower.address,
            pool_address=test_pool.pool_address,
            application_date=now,
            dissolution_date=now + timedelta(days=30),
            state="PENDING",
            principal=Decimal("1000.00"),
            interest=Decimal("55.00"),
            tx_hash="APP_TX_HASH"
        )
        db_session.add(application)
        db_session.commit()

        apps = db_session.query(Application).filter_by(
            pool_address=test_pool.pool_address
        ).all()
        assert len(apps) == 1
        assert apps[0].borrower_address == test_borrower.address

    def test_update_application_state(self, db_session, test_borrower, test_pool):
        """Test updating application state (approve/reject)"""
        now = datetime.now()
        application = Application(
            application_address="00000000A1B2C3D4E5F0000000000000000000000000000000000001",
            borrower_address=test_borrower.address,
            pool_address=test_pool.pool_address,
            application_date=now,
            dissolution_date=now + timedelta(days=30),
            state="PENDING",
            principal=Decimal("1000.00"),
            interest=Decimal("55.00"),
            tx_hash="APP_TX_HASH"
        )
        db_session.add(application)
        db_session.commit()

        # Approve the application
        application.state = "APPROVED"
        db_session.commit()

        retrieved = db_session.query(Application).filter_by(
            application_address="00000000A1B2C3D4E5F0000000000000000000000000000000000001"
        ).first()
        assert retrieved.state == "APPROVED"
