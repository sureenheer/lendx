"""
Test database connection and basic operations.
These tests verify that the database configuration and connection work correctly.
"""

import pytest
from decimal import Decimal
from datetime import datetime, timedelta
from backend.config.database import get_db_session, init_db
from backend.models.database import User, Pool, Application, Loan, UserMPTBalance


class TestDatabaseConnection:
    """Test database connection and initialization"""

    def test_database_connection(self):
        """Test that we can connect to the database"""
        session = get_db_session()
        assert session is not None
        session.close()

    def test_database_initialization(self):
        """Test database initialization"""
        engine = init_db()
        assert engine is not None


class TestDatabaseOperations:
    """Test basic CRUD operations"""

    @pytest.fixture
    def db_session(self):
        """Provide a database session for tests"""
        session = get_db_session()
        yield session
        # Cleanup after test
        session.rollback()
        session.close()

    def test_create_user(self, db_session):
        """Test creating a user"""
        user = User(
            address="rN7n7otQDd6FczFgLdlqtyMVrn3WnFBBEx",
            did="did:xrpl:1:rN7n7otQDd6FczFgLdlqtyMVrn3WnFBBEx"
        )
        db_session.add(user)
        db_session.commit()

        # Query the user back
        retrieved_user = db_session.query(User).filter_by(
            address="rN7n7otQDd6FczFgLdlqtyMVrn3WnFBBEx"
        ).first()

        assert retrieved_user is not None
        assert retrieved_user.address == "rN7n7otQDd6FczFgLdlqtyMVrn3WnFBBEx"
        assert retrieved_user.did == "did:xrpl:1:rN7n7otQDd6FczFgLdlqtyMVrn3WnFBBEx"
        assert retrieved_user.created_at is not None

    def test_user_unique_did(self, db_session):
        """Test that DID must be unique"""
        user1 = User(
            address="rN7n7otQDd6FczFgLdlqtyMVrn3WnFBBEx",
            did="did:xrpl:1:test"
        )
        db_session.add(user1)
        db_session.commit()

        # Try to create another user with same DID
        user2 = User(
            address="rPEPPER7kfTD9w2To4CQk6UCfuHM9c6GDY",
            did="did:xrpl:1:test"
        )
        db_session.add(user2)

        with pytest.raises(Exception):  # Should raise IntegrityError
            db_session.commit()
