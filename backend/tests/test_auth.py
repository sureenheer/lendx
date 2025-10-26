"""
Tests for authentication endpoints including DID creation.

This module tests the user signup flow which includes:
- Wallet generation
- DID creation on XRPL
- User database storage
- Security considerations
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from fastapi.testclient import TestClient
from xrpl.wallet import Wallet

from backend.api.main import app
from backend.models.database import User


# Create test client
client = TestClient(app)


class TestSignupEndpoint:
    """Tests for POST /api/auth/signup endpoint"""

    @patch('backend.api.auth.Wallet.create')
    @patch('backend.api.auth.create_did_for_user')
    def test_signup_creates_user_with_did(
        self,
        mock_create_did,
        mock_wallet_create,
        db_session
    ):
        """Test successful user signup with DID creation"""
        # Mock wallet generation
        mock_wallet = Mock()
        mock_wallet.address = "rTestAddress123456789012345678"
        mock_wallet.seed = "sTestSeed123456789012345678901"
        mock_wallet_create.return_value = mock_wallet

        # Mock DID creation
        expected_did = "did:xrpl:1:rTestAddress123456789012345678"
        mock_create_did.return_value = expected_did

        # Make signup request
        response = client.post("/api/auth/signup", json={})

        # Assertions
        assert response.status_code == 200
        data = response.json()

        assert data["address"] == mock_wallet.address
        assert data["did"] == expected_did
        assert data["seed"] == mock_wallet.seed
        assert "explorer_url" in data
        assert "testnet.xrpl.org" in data["explorer_url"]
        assert data["message"] == "User created with DID on XRPL. Save your seed!"

        # Verify DID was created with correct parameters
        mock_create_did.assert_called_once()
        call_args = mock_create_did.call_args
        assert call_args[1]["network"] == "testnet"
        assert call_args[1]["update_database"] == False

    @patch('backend.api.auth.Wallet.create')
    @patch('backend.api.auth.create_did_for_user')
    def test_signup_stores_user_in_database(
        self,
        mock_create_did,
        mock_wallet_create,
        db_session
    ):
        """Test that signup stores user record in database"""
        # Mock wallet and DID
        mock_wallet = Mock()
        mock_wallet.address = "rNewUser123456789012345678901"
        mock_wallet.seed = "sNewUserSeed123456789012345678"
        mock_wallet_create.return_value = mock_wallet
        mock_create_did.return_value = "did:xrpl:1:rNewUser123456789012345678901"

        # Signup
        response = client.post("/api/auth/signup", json={})

        assert response.status_code == 200

        # Verify user exists in database
        user = db_session.query(User).filter_by(address=mock_wallet.address).first()
        assert user is not None
        assert user.address == mock_wallet.address
        assert user.did == "did:xrpl:1:rNewUser123456789012345678901"
        assert user.created_at is not None

    @patch('backend.api.auth.Wallet.create')
    def test_signup_with_existing_user_returns_error(
        self,
        mock_wallet_create,
        db_session,
        create_test_user
    ):
        """Test that signup fails if user already exists"""
        # Create existing user
        existing_address = "rExistingUser123456789012345678"
        create_test_user(existing_address, "did:xrpl:1:rExistingUser123456789012345678")

        # Mock wallet to return same address
        mock_wallet = Mock()
        mock_wallet.address = existing_address
        mock_wallet_create.return_value = mock_wallet

        # Attempt signup
        response = client.post("/api/auth/signup", json={})

        assert response.status_code == 400
        assert "already exists" in response.json()["detail"].lower()

    @patch('backend.api.auth.Wallet.create')
    @patch('backend.api.auth.create_did_for_user')
    def test_signup_rollback_on_did_creation_failure(
        self,
        mock_create_did,
        mock_wallet_create,
        db_session
    ):
        """Test database rollback when DID creation fails"""
        # Mock wallet
        mock_wallet = Mock()
        mock_wallet.address = "rFailedDID123456789012345678901"
        mock_wallet_create.return_value = mock_wallet

        # Mock DID creation to fail
        mock_create_did.side_effect = Exception("XRPL connection failed")

        # Attempt signup
        response = client.post("/api/auth/signup", json={})

        assert response.status_code == 500
        assert "Signup failed" in response.json()["detail"]

        # Verify user was NOT created in database
        user = db_session.query(User).filter_by(address=mock_wallet.address).first()
        assert user is None

    @patch('backend.api.auth.Wallet.create')
    @patch('backend.api.auth.create_did_for_user')
    def test_signup_optional_username_parameter(
        self,
        mock_create_did,
        mock_wallet_create,
        db_session
    ):
        """Test signup accepts optional username parameter"""
        # Mock wallet and DID
        mock_wallet = Mock()
        mock_wallet.address = "rUserWithName12345678901234567"
        mock_wallet.seed = "sTestSeed123456789012345678901"
        mock_wallet_create.return_value = mock_wallet
        mock_create_did.return_value = "did:xrpl:1:rUserWithName12345678901234567"

        # Signup with username (currently not used in MVP but accepted)
        response = client.post("/api/auth/signup", json={"username": "testuser"})

        assert response.status_code == 200
        data = response.json()
        assert data["address"] == mock_wallet.address

    @patch('backend.api.auth.Wallet.create')
    @patch('backend.api.auth.create_did_for_user')
    def test_signup_response_includes_explorer_url(
        self,
        mock_create_did,
        mock_wallet_create,
        db_session
    ):
        """Test that signup response includes XRPL explorer URL"""
        # Mock wallet
        mock_wallet = Mock()
        mock_wallet.address = "rExplorerTest123456789012345678"
        mock_wallet.seed = "sTestSeed123456789012345678901"
        mock_wallet_create.return_value = mock_wallet
        mock_create_did.return_value = "did:xrpl:1:rExplorerTest123456789012345678"

        # Signup
        response = client.post("/api/auth/signup", json={})

        assert response.status_code == 200
        data = response.json()

        # Verify explorer URL format
        expected_url = f"https://testnet.xrpl.org/accounts/{mock_wallet.address}"
        assert data["explorer_url"] == expected_url


class TestVerifyUserEndpoint:
    """Tests for GET /api/auth/verify/{address} endpoint"""

    def test_verify_existing_user(self, db_session, create_test_user):
        """Test verifying an existing user returns correct data"""
        # Create test user
        address = "rVerifyUser123456789012345678901"
        did = "did:xrpl:1:rVerifyUser123456789012345678901"
        user = create_test_user(address, did)

        # Verify user
        response = client.get(f"/api/auth/verify/{address}")

        assert response.status_code == 200
        data = response.json()

        assert data["address"] == address
        assert data["did"] == did
        assert "created_at" in data
        assert data["explorer_url"] == f"https://testnet.xrpl.org/accounts/{address}"

    def test_verify_nonexistent_user(self, db_session):
        """Test verifying non-existent user returns 404"""
        response = client.get("/api/auth/verify/rNonExistentUser123456789012345")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_verify_user_without_did(self, db_session, create_test_user):
        """Test verifying user without DID returns null DID"""
        # Create user without DID
        address = "rNoDIDUser1234567890123456789012"
        user = create_test_user(address, None)

        # Verify
        response = client.get(f"/api/auth/verify/{address}")

        assert response.status_code == 200
        data = response.json()

        assert data["address"] == address
        assert data["did"] is None


class TestAuthSecurityConsiderations:
    """Tests for security aspects of authentication"""

    @patch('backend.api.auth.Wallet.create')
    @patch('backend.api.auth.create_did_for_user')
    def test_seed_returned_for_demo_only(
        self,
        mock_create_did,
        mock_wallet_create,
        db_session
    ):
        """
        Test that seed is returned in response.

        WARNING: This is intentionally insecure for demo purposes.
        Production should NEVER return private keys/seeds.
        """
        mock_wallet = Mock()
        mock_wallet.address = "rSecurityTest123456789012345678"
        mock_wallet.seed = "sPrivateKey123456789012345678"
        mock_wallet_create.return_value = mock_wallet
        mock_create_did.return_value = "did:xrpl:1:rSecurityTest123456789012345678"

        response = client.post("/api/auth/signup", json={})

        assert response.status_code == 200
        data = response.json()

        # Seed is returned (DEMO ONLY - document this security consideration)
        assert data["seed"] == mock_wallet.seed
        assert "Save your seed" in data["message"]

    def test_verify_endpoint_does_not_expose_sensitive_data(
        self,
        db_session,
        create_test_user
    ):
        """Test that verify endpoint doesn't expose sensitive information"""
        address = "rSensitiveData123456789012345678"
        user = create_test_user(address, "did:xrpl:1:test")

        response = client.get(f"/api/auth/verify/{address}")

        assert response.status_code == 200
        data = response.json()

        # Verify only safe data is exposed
        assert "seed" not in data
        assert "private_key" not in data
        # Public information only
        assert "address" in data
        assert "did" in data


class TestDIDCreationIntegration:
    """Integration tests for DID creation on XRPL"""

    @patch('backend.api.auth.xrpl_client')
    @patch('backend.api.auth.Wallet.create')
    @patch('backend.api.auth.create_did_for_user')
    def test_did_creation_uses_testnet(
        self,
        mock_create_did,
        mock_wallet_create,
        mock_xrpl_client,
        db_session
    ):
        """Test that DID creation uses testnet for development"""
        mock_wallet = Mock()
        mock_wallet.address = "rTestNet123456789012345678901"
        mock_wallet.seed = "sTestSeed123456789012345678901"
        mock_wallet_create.return_value = mock_wallet
        mock_create_did.return_value = "did:xrpl:1:rTestNet123456789012345678901"

        response = client.post("/api/auth/signup", json={})

        assert response.status_code == 200

        # Verify DID creation used testnet
        call_args = mock_create_did.call_args
        assert call_args[1]["network"] == "testnet"

    @patch('backend.api.auth.Wallet.create')
    @patch('backend.api.auth.create_did_for_user')
    def test_did_format_follows_w3c_spec(
        self,
        mock_create_did,
        mock_wallet_create,
        db_session
    ):
        """Test that DID follows W3C DID specification format"""
        mock_wallet = Mock()
        mock_wallet.address = "rW3CFormat1234567890123456789012"
        mock_wallet_create.return_value = mock_wallet

        # DID should follow format: did:xrpl:{network}:{address}
        expected_did = "did:xrpl:1:rW3CFormat1234567890123456789012"
        mock_create_did.return_value = expected_did

        response = client.post("/api/auth/signup", json={})

        assert response.status_code == 200
        data = response.json()

        # Verify DID format
        assert data["did"].startswith("did:xrpl:")
        assert data["did"] == expected_did


class TestDatabaseConstraints:
    """Tests for database constraints and validation"""

    @patch('backend.api.auth.Wallet.create')
    @patch('backend.api.auth.create_did_for_user')
    def test_user_address_is_primary_key(
        self,
        mock_create_did,
        mock_wallet_create,
        db_session
    ):
        """Test that user address serves as primary key"""
        mock_wallet = Mock()
        mock_wallet.address = "rPrimaryKey123456789012345678901"
        mock_wallet.seed = "sTestSeed123456789012345678901"
        mock_wallet_create.return_value = mock_wallet
        mock_create_did.return_value = "did:xrpl:1:rPrimaryKey123456789012345678901"

        # Create first user
        response1 = client.post("/api/auth/signup", json={})
        assert response1.status_code == 200

        # Attempt to create duplicate (should fail)
        response2 = client.post("/api/auth/signup", json={})
        assert response2.status_code == 400

    @patch('backend.api.auth.Wallet.create')
    @patch('backend.api.auth.create_did_for_user')
    def test_did_uniqueness_constraint(
        self,
        mock_create_did,
        mock_wallet_create,
        db_session,
        create_test_user
    ):
        """Test that DID must be unique in database"""
        # Create user with specific DID
        duplicate_did = "did:xrpl:1:rDuplicateDID123456789012345"
        create_test_user("rExisting123456789012345678901", duplicate_did)

        # Attempt to create another user with same DID
        mock_wallet = Mock()
        mock_wallet.address = "rNewUser123456789012345678901234"
        mock_wallet.seed = "sTestSeed123456789012345678901"
        mock_wallet_create.return_value = mock_wallet
        mock_create_did.return_value = duplicate_did

        response = client.post("/api/auth/signup", json={})

        # Should fail due to unique constraint on DID
        # Note: This depends on database constraint enforcement
        assert response.status_code in [400, 500]
