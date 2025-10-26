"""
Test Loan model operations.
"""

import pytest
from decimal import Decimal
from datetime import datetime, timedelta
from backend.config.database import get_db_session
from backend.models.database import User, Pool, Loan


class TestLoanModel:
    """Test Loan model CRUD operations"""

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

    def test_create_loan(self, db_session, test_borrower, test_lender, test_pool):
        """Test creating a loan"""
        now = datetime.now()
        loan = Loan(
            loan_address="00000000L0A1N2000000000000000000000000000000000000000001",
            pool_address=test_pool.pool_address,
            borrower_address=test_borrower.address,
            lender_address=test_lender.address,
            start_date=now,
            end_date=now + timedelta(days=30),
            principal=Decimal("1000.00"),
            interest=Decimal("55.00"),
            state="ONGOING",
            tx_hash="LOAN_TX_HASH"
        )
        db_session.add(loan)
        db_session.commit()

        retrieved = db_session.query(Loan).filter_by(
            loan_address="00000000L0A1N2000000000000000000000000000000000000000001"
        ).first()

        assert retrieved is not None
        assert retrieved.state == "ONGOING"
        assert retrieved.principal == Decimal("1000.00")
        assert retrieved.interest == Decimal("55.00")

    def test_loan_state_validation(self, db_session, test_borrower, test_lender, test_pool):
        """Test that only valid loan states are allowed"""
        now = datetime.now()
        loan = Loan(
            loan_address="00000000L0A1N2000000000000000000000000000000000000000001",
            pool_address=test_pool.pool_address,
            borrower_address=test_borrower.address,
            lender_address=test_lender.address,
            start_date=now,
            end_date=now + timedelta(days=30),
            principal=Decimal("1000.00"),
            interest=Decimal("55.00"),
            state="INVALID_STATE",
            tx_hash="LOAN_TX_HASH"
        )
        db_session.add(loan)

        with pytest.raises(Exception):  # Should raise CheckViolation
            db_session.commit()

    def test_query_loans_by_borrower(self, db_session, test_borrower, test_lender, test_pool):
        """Test querying loans by borrower"""
        now = datetime.now()
        loan1 = Loan(
            loan_address="00000000L0A1N2000000000000000000000000000000000000000001",
            pool_address=test_pool.pool_address,
            borrower_address=test_borrower.address,
            lender_address=test_lender.address,
            start_date=now,
            end_date=now + timedelta(days=30),
            principal=Decimal("1000.00"),
            interest=Decimal("55.00"),
            state="ONGOING",
            tx_hash="LOAN1"
        )
        loan2 = Loan(
            loan_address="00000000L0A1N2000000000000000000000000000000000000000002",
            pool_address=test_pool.pool_address,
            borrower_address=test_borrower.address,
            lender_address=test_lender.address,
            start_date=now - timedelta(days=60),
            end_date=now - timedelta(days=30),
            principal=Decimal("500.00"),
            interest=Decimal("27.50"),
            state="PAID",
            tx_hash="LOAN2"
        )
        db_session.add_all([loan1, loan2])
        db_session.commit()

        loans = db_session.query(Loan).filter_by(
            borrower_address=test_borrower.address
        ).all()
        assert len(loans) == 2

    def test_query_loans_by_lender(self, db_session, test_borrower, test_lender, test_pool):
        """Test querying loans by lender"""
        now = datetime.now()
        loan = Loan(
            loan_address="00000000L0A1N2000000000000000000000000000000000000000001",
            pool_address=test_pool.pool_address,
            borrower_address=test_borrower.address,
            lender_address=test_lender.address,
            start_date=now,
            end_date=now + timedelta(days=30),
            principal=Decimal("1000.00"),
            interest=Decimal("55.00"),
            state="ONGOING",
            tx_hash="LOAN_TX_HASH"
        )
        db_session.add(loan)
        db_session.commit()

        loans = db_session.query(Loan).filter_by(lender_address=test_lender.address).all()
        assert len(loans) == 1
        assert loans[0].borrower_address == test_borrower.address

    def test_update_loan_state_to_paid(self, db_session, test_borrower, test_lender, test_pool):
        """Test updating loan state to PAID"""
        now = datetime.now()
        loan = Loan(
            loan_address="00000000L0A1N2000000000000000000000000000000000000000001",
            pool_address=test_pool.pool_address,
            borrower_address=test_borrower.address,
            lender_address=test_lender.address,
            start_date=now,
            end_date=now + timedelta(days=30),
            principal=Decimal("1000.00"),
            interest=Decimal("55.00"),
            state="ONGOING",
            tx_hash="LOAN_TX_HASH"
        )
        db_session.add(loan)
        db_session.commit()

        # Mark as paid
        loan.state = "PAID"
        db_session.commit()

        retrieved = db_session.query(Loan).filter_by(
            loan_address="00000000L0A1N2000000000000000000000000000000000000000001"
        ).first()
        assert retrieved.state == "PAID"

    def test_update_loan_state_to_defaulted(self, db_session, test_borrower, test_lender, test_pool):
        """Test updating loan state to DEFAULTED"""
        now = datetime.now()
        loan = Loan(
            loan_address="00000000L0A1N2000000000000000000000000000000000000000001",
            pool_address=test_pool.pool_address,
            borrower_address=test_borrower.address,
            lender_address=test_lender.address,
            start_date=now - timedelta(days=60),
            end_date=now - timedelta(days=30),  # Expired
            principal=Decimal("1000.00"),
            interest=Decimal("55.00"),
            state="ONGOING",
            tx_hash="LOAN_TX_HASH"
        )
        db_session.add(loan)
        db_session.commit()

        # Mark as defaulted
        loan.state = "DEFAULTED"
        db_session.commit()

        retrieved = db_session.query(Loan).filter_by(
            loan_address="00000000L0A1N2000000000000000000000000000000000000000001"
        ).first()
        assert retrieved.state == "DEFAULTED"

    def test_query_active_loans(self, db_session, test_borrower, test_lender, test_pool):
        """Test querying only active (ONGOING) loans"""
        now = datetime.now()
        loan1 = Loan(
            loan_address="00000000L0A1N2000000000000000000000000000000000000000001",
            pool_address=test_pool.pool_address,
            borrower_address=test_borrower.address,
            lender_address=test_lender.address,
            start_date=now,
            end_date=now + timedelta(days=30),
            principal=Decimal("1000.00"),
            interest=Decimal("55.00"),
            state="ONGOING",
            tx_hash="LOAN1"
        )
        loan2 = Loan(
            loan_address="00000000L0A1N2000000000000000000000000000000000000000002",
            pool_address=test_pool.pool_address,
            borrower_address=test_borrower.address,
            lender_address=test_lender.address,
            start_date=now - timedelta(days=60),
            end_date=now - timedelta(days=30),
            principal=Decimal("500.00"),
            interest=Decimal("27.50"),
            state="PAID",
            tx_hash="LOAN2"
        )
        db_session.add_all([loan1, loan2])
        db_session.commit()

        active_loans = db_session.query(Loan).filter_by(state="ONGOING").all()
        assert len(active_loans) == 1
        assert active_loans[0].loan_address == "00000000L0A1N2000000000000000000000000000000000000000001"
