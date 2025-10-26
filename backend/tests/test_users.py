"""
Test User model operations.
"""

import pytest
from backend.config.database import get_db_session
from backend.models.database import User


class TestUserModel:
    """Test User model CRUD operations"""

    @pytest.fixture
    def db_session(self):
        """Provide a database session for tests"""
        session = get_db_session()
        yield session
        # Cleanup
        session.rollback()
        session.close()

    def test_create_user_minimal(self, db_session):
        """Test creating user with only required fields"""
        user = User(address="rN7n7otQDd6FczFgLdlqtyMVrn3WnFBBEx")
        db_session.add(user)
        db_session.commit()

        retrieved = db_session.query(User).filter_by(
            address="rN7n7otQDd6FczFgLdlqtyMVrn3WnFBBEx"
        ).first()

        assert retrieved is not None
        assert retrieved.did is None
        assert retrieved.created_at is not None

    def test_create_user_with_did(self, db_session):
        """Test creating user with DID"""
        user = User(
            address="rN7n7otQDd6FczFgLdlqtyMVrn3WnFBBEx",
            did="did:xrpl:1:rN7n7otQDd6FczFgLdlqtyMVrn3WnFBBEx"
        )
        db_session.add(user)
        db_session.commit()

        retrieved = db_session.query(User).filter_by(
            address="rN7n7otQDd6FczFgLdlqtyMVrn3WnFBBEx"
        ).first()

        assert retrieved.did == "did:xrpl:1:rN7n7otQDd6FczFgLdlqtyMVrn3WnFBBEx"

    def test_user_address_format_validation(self, db_session):
        """Test that invalid XRP addresses should fail (business logic validation)"""
        # This will test the model validation if implemented
        user = User(address="invalid_address")
        db_session.add(user)
        # This should work at DB level but should be caught by model validation
        # For now, we just test it can be stored
        db_session.commit()
        assert user.address == "invalid_address"

    def test_query_user_by_did(self, db_session):
        """Test querying user by DID"""
        user = User(
            address="rN7n7otQDd6FczFgLdlqtyMVrn3WnFBBEx",
            did="did:xrpl:1:test123"
        )
        db_session.add(user)
        db_session.commit()

        retrieved = db_session.query(User).filter_by(did="did:xrpl:1:test123").first()
        assert retrieved is not None
        assert retrieved.address == "rN7n7otQDd6FczFgLdlqtyMVrn3WnFBBEx"

    def test_update_user_did(self, db_session):
        """Test updating user DID"""
        user = User(address="rN7n7otQDd6FczFgLdlqtyMVrn3WnFBBEx")
        db_session.add(user)
        db_session.commit()

        # Update DID
        user.did = "did:xrpl:1:updated"
        db_session.commit()

        retrieved = db_session.query(User).filter_by(
            address="rN7n7otQDd6FczFgLdlqtyMVrn3WnFBBEx"
        ).first()
        assert retrieved.did == "did:xrpl:1:updated"

    def test_delete_user(self, db_session):
        """Test deleting a user"""
        user = User(address="rN7n7otQDd6FczFgLdlqtyMVrn3WnFBBEx")
        db_session.add(user)
        db_session.commit()

        db_session.delete(user)
        db_session.commit()

        retrieved = db_session.query(User).filter_by(
            address="rN7n7otQDd6FczFgLdlqtyMVrn3WnFBBEx"
        ).first()
        assert retrieved is None
