"""
Test Pool model operations.
"""

import pytest
from decimal import Decimal
from backend.config.database import get_db_session
from backend.models.database import User, Pool


class TestPoolModel:
    """Test Pool model CRUD operations"""

    @pytest.fixture
    def db_session(self):
        """Provide a database session for tests"""
        session = get_db_session()
        yield session
        session.rollback()
        session.close()

    @pytest.fixture
    def test_user(self, db_session):
        """Create a test user"""
        user = User(
            address="rN7n7otQDd6FczFgLdlqtyMVrn3WnFBBEx",
            did="did:xrpl:1:lender"
        )
        db_session.add(user)
        db_session.commit()
        return user

    def test_create_pool(self, db_session, test_user):
        """Test creating a lending pool"""
        pool = Pool(
            pool_address="00000000F1A7E3E8B7F0000000000000000000000000000000000001",
            issuer_address=test_user.address,
            total_balance=Decimal("10000.00"),
            current_balance=Decimal("10000.00"),
            minimum_loan=Decimal("100.00"),
            duration_days=30,
            interest_rate=Decimal("5.50"),
            tx_hash="ABC123DEF456"
        )
        db_session.add(pool)
        db_session.commit()

        retrieved = db_session.query(Pool).filter_by(
            pool_address="00000000F1A7E3E8B7F0000000000000000000000000000000000001"
        ).first()

        assert retrieved is not None
        assert retrieved.total_balance == Decimal("10000.00")
        assert retrieved.current_balance == Decimal("10000.00")
        assert retrieved.interest_rate == Decimal("5.50")

    def test_pool_foreign_key_constraint(self, db_session):
        """Test that pool requires valid issuer address"""
        pool = Pool(
            pool_address="00000000F1A7E3E8B7F0000000000000000000000000000000000001",
            issuer_address="rInvalidAddress123",  # Non-existent user
            total_balance=Decimal("10000.00"),
            current_balance=Decimal("10000.00"),
            minimum_loan=Decimal("100.00"),
            duration_days=30,
            interest_rate=Decimal("5.50"),
            tx_hash="ABC123"
        )
        db_session.add(pool)

        with pytest.raises(Exception):  # Should raise ForeignKeyViolation
            db_session.commit()

    def test_query_pools_by_issuer(self, db_session, test_user):
        """Test querying all pools by issuer"""
        pool1 = Pool(
            pool_address="00000000F1A7E3E8B7F0000000000000000000000000000000000001",
            issuer_address=test_user.address,
            total_balance=Decimal("10000.00"),
            current_balance=Decimal("10000.00"),
            minimum_loan=Decimal("100.00"),
            duration_days=30,
            interest_rate=Decimal("5.50"),
            tx_hash="ABC1"
        )
        pool2 = Pool(
            pool_address="00000000F1A7E3E8B7F0000000000000000000000000000000000002",
            issuer_address=test_user.address,
            total_balance=Decimal("5000.00"),
            current_balance=Decimal("5000.00"),
            minimum_loan=Decimal("50.00"),
            duration_days=60,
            interest_rate=Decimal("7.00"),
            tx_hash="ABC2"
        )
        db_session.add_all([pool1, pool2])
        db_session.commit()

        pools = db_session.query(Pool).filter_by(issuer_address=test_user.address).all()
        assert len(pools) == 2

    def test_update_pool_current_balance(self, db_session, test_user):
        """Test updating pool current balance when loan is issued"""
        pool = Pool(
            pool_address="00000000F1A7E3E8B7F0000000000000000000000000000000000001",
            issuer_address=test_user.address,
            total_balance=Decimal("10000.00"),
            current_balance=Decimal("10000.00"),
            minimum_loan=Decimal("100.00"),
            duration_days=30,
            interest_rate=Decimal("5.50"),
            tx_hash="ABC123"
        )
        db_session.add(pool)
        db_session.commit()

        # Simulate issuing a loan
        pool.current_balance -= Decimal("1000.00")
        db_session.commit()

        retrieved = db_session.query(Pool).filter_by(
            pool_address="00000000F1A7E3E8B7F0000000000000000000000000000000000001"
        ).first()
        assert retrieved.current_balance == Decimal("9000.00")

    def test_pool_decimal_precision(self, db_session, test_user):
        """Test that decimal values maintain precision"""
        pool = Pool(
            pool_address="00000000F1A7E3E8B7F0000000000000000000000000000000000001",
            issuer_address=test_user.address,
            total_balance=Decimal("10000.123456"),
            current_balance=Decimal("10000.123456"),
            minimum_loan=Decimal("100.50"),
            duration_days=30,
            interest_rate=Decimal("5.75"),
            tx_hash="ABC123"
        )
        db_session.add(pool)
        db_session.commit()

        retrieved = db_session.query(Pool).filter_by(
            pool_address="00000000F1A7E3E8B7F0000000000000000000000000000000000001"
        ).first()
        assert retrieved.total_balance == Decimal("10000.123456")


class TestPoolMPTIntegration:
    """Test PoolMPT creation on XRPL during pool creation"""

    @pytest.mark.integration
    def test_create_pool_with_mpt_on_xrpl(self):
        """
        Integration test: Creating a pool should create PoolMPT on XRPL testnet.

        This test verifies that:
        1. POST /pools creates an MPT on XRPL
        2. Returns MPT ID as pool_address
        3. Returns tx_hash for verification
        4. Database stores the MPT ID and tx_hash
        5. Explorer URL is provided for verification
        """
        from fastapi.testclient import TestClient
        from backend.api.main import app

        client = TestClient(app)

        # Create pool request
        pool_data = {
            "name": "Test Pool",
            "amount": 1000.0,
            "interest_rate": 5.5,
            "max_term_days": 30,
            "min_loan_amount": 100.0,
            "lender_address": "rN7n7otQDd6FczFgLdlqtyMVrn3HMzve5x"  # Test address
        }

        response = client.post("/pools", json=pool_data)

        # Verify response
        assert response.status_code == 200
        result = response.json()

        # Check required fields
        assert "pool_id" in result
        assert "pool_address" in result
        assert "tx_hash" in result
        assert "explorer_url" in result

        # Verify pool_id equals pool_address (both are MPT ID)
        assert result["pool_id"] == result["pool_address"]

        # Verify MPT ID format (64 hex characters)
        assert len(result["pool_id"]) >= 64

        # Verify tx_hash format (64 hex characters)
        assert len(result["tx_hash"]) == 64

        # Verify explorer URL contains tx_hash
        assert result["tx_hash"] in result["explorer_url"]
        assert "testnet.xrpl.org" in result["explorer_url"]

        # Verify database has the pool with correct MPT ID
        from backend.config.database import get_db_session
        from backend.models.database import Pool

        db = get_db_session()
        pool = db.query(Pool).filter_by(pool_address=result["pool_id"]).first()

        assert pool is not None
        assert pool.pool_address == result["pool_id"]
        assert pool.tx_hash == result["tx_hash"]
        assert float(pool.total_balance) == pool_data["amount"]

        db.close()
