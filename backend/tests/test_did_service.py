"""
Test suite for DID service.

Tests DID creation, retrieval, update, and deletion on XRPL testnet.
"""

import pytest
import json
from xrpl.wallet import Wallet
from xrpl.clients import JsonRpcClient

from backend.services.did_service import (
    create_did_for_user,
    get_did_document,
    update_did_document,
    delete_did,
    get_did_from_address,
    _format_did,
    _create_did_document,
    _encode_hex,
    _decode_hex
)
from backend.xrpl_client.client import connect
from backend.models.database import User


class TestDIDFormatting:
    """Test DID formatting and encoding utilities"""

    def test_format_did_testnet(self):
        """Test DID formatting for testnet"""
        address = "rN7n7otQDd6FczFgLdlqtyMVrn3HMfXkPj"
        did = _format_did(address, 'testnet')
        assert did == f"did:xrpl:1:{address}"

    def test_format_did_mainnet(self):
        """Test DID formatting for mainnet"""
        address = "rN7n7otQDd6FczFgLdlqtyMVrn3HMfXkPj"
        did = _format_did(address, 'mainnet')
        assert did == f"did:xrpl:0:{address}"

    def test_encode_decode_hex(self):
        """Test hex encoding and decoding"""
        original = "Hello, XRPL!"
        encoded = _encode_hex(original)
        decoded = _decode_hex(encoded)
        assert decoded == original
        assert encoded == encoded.upper()  # Should be uppercase

    def test_create_did_document_structure(self):
        """Test DID document structure"""
        address = "rN7n7otQDd6FczFgLdlqtyMVrn3HMfXkPj"
        public_key = "ED01234567890ABCDEF"

        doc = _create_did_document(address, public_key, 'testnet')

        # Check required fields
        assert "@context" in doc
        assert "id" in doc
        assert "verificationMethod" in doc
        assert doc["id"] == f"did:xrpl:1:{address}"

        # Check verification method
        assert len(doc["verificationMethod"]) == 1
        vm = doc["verificationMethod"][0]
        assert vm["type"] == "Ed25519VerificationKey2020"
        assert vm["publicKeyMultibase"] == public_key
        assert vm["controller"] == doc["id"]


class TestDIDServiceIntegration:
    """Integration tests with XRPL testnet (requires network connection)"""

    @pytest.fixture
    def test_wallet(self):
        """Create a test wallet for integration tests"""
        # Generate a new wallet for testing
        wallet = Wallet.create()
        return wallet

    @pytest.fixture
    def funded_wallet(self, test_wallet):
        """
        Fund the test wallet with XRP from testnet faucet.

        Note: This requires network connection and may be rate-limited.
        For CI/CD, consider using a pre-funded test wallet.
        """
        from xrpl.clients import JsonRpcClient
        from xrpl.wallet import generate_faucet_wallet

        # Use faucet to fund wallet
        try:
            client = JsonRpcClient("https://s.altnet.rippletest.net:51234/")
            funded = generate_faucet_wallet(client, test_wallet)
            return funded
        except Exception as e:
            pytest.skip(f"Failed to fund wallet from faucet: {e}")

    @pytest.mark.integration
    def test_create_did_basic(self, funded_wallet):
        """Test basic DID creation on testnet"""
        # Create DID (without database update for isolation)
        did = create_did_for_user(
            funded_wallet,
            network='testnet',
            update_database=False
        )

        # Verify format
        assert did.startswith("did:xrpl:1:")
        assert funded_wallet.classic_address in did

    @pytest.mark.integration
    def test_create_and_retrieve_did(self, funded_wallet):
        """Test DID creation and retrieval roundtrip"""
        # Create DID
        did = create_did_for_user(
            funded_wallet,
            network='testnet',
            update_database=False
        )

        # Wait a moment for ledger to validate
        import time
        time.sleep(5)

        # Retrieve DID document
        doc = get_did_document(funded_wallet.classic_address, network='testnet')

        assert doc is not None
        assert doc["id"] == did
        assert "verificationMethod" in doc or "_ledger" in doc

    @pytest.mark.integration
    def test_create_did_with_custom_data(self, funded_wallet):
        """Test DID creation with custom URI and data"""
        custom_uri = "https://example.com/did-doc.json"
        custom_data = "custom metadata"

        did = create_did_for_user(
            funded_wallet,
            network='testnet',
            update_database=False,
            uri=custom_uri,
            data=custom_data
        )

        # Wait for validation
        import time
        time.sleep(5)

        # Retrieve and verify
        doc = get_did_document(funded_wallet.classic_address, network='testnet')

        assert doc is not None
        if "_ledger" in doc:
            assert doc["_ledger"]["uri"] == custom_uri
            assert doc["_ledger"]["data"] == custom_data

    @pytest.mark.integration
    def test_update_did_document(self, funded_wallet):
        """Test updating DID document"""
        # Create initial DID
        did = create_did_for_user(
            funded_wallet,
            network='testnet',
            update_database=False
        )

        import time
        time.sleep(5)

        # Update with new URI
        new_uri = "https://updated.example.com/did.json"
        success = update_did_document(
            funded_wallet,
            network='testnet',
            uri=new_uri
        )

        assert success is True

        time.sleep(5)

        # Verify update
        doc = get_did_document(funded_wallet.classic_address, network='testnet')
        assert doc is not None
        if "_ledger" in doc:
            assert doc["_ledger"]["uri"] == new_uri

    @pytest.mark.integration
    def test_delete_did(self, funded_wallet):
        """Test DID deletion"""
        # Create DID
        did = create_did_for_user(
            funded_wallet,
            network='testnet',
            update_database=False
        )

        import time
        time.sleep(5)

        # Delete DID
        success = delete_did(
            funded_wallet,
            network='testnet',
            update_database=False
        )

        assert success is True

        time.sleep(5)

        # Verify deletion
        doc = get_did_document(funded_wallet.classic_address, network='testnet')
        assert doc is None

    @pytest.mark.integration
    def test_get_did_from_address(self, funded_wallet):
        """Test convenience function to get DID from address"""
        # Create DID
        expected_did = create_did_for_user(
            funded_wallet,
            network='testnet',
            update_database=False
        )

        import time
        time.sleep(5)

        # Get DID from address
        actual_did = get_did_from_address(
            funded_wallet.classic_address,
            network='testnet'
        )

        assert actual_did == expected_did

    @pytest.mark.integration
    def test_get_did_from_nonexistent_address(self):
        """Test getting DID for address without DID"""
        # Random address that likely doesn't have a DID
        random_wallet = Wallet.create()

        did = get_did_from_address(
            random_wallet.classic_address,
            network='testnet'
        )

        assert did is None


class TestDIDServiceErrors:
    """Test error handling in DID service"""

    def test_create_did_invalid_wallet(self):
        """Test error when creating DID with invalid wallet"""
        with pytest.raises(ValueError, match="Invalid user wallet"):
            create_did_for_user(None, network='testnet')

    def test_update_did_no_fields(self):
        """Test error when updating DID with no fields"""
        wallet = Wallet.create()

        with pytest.raises(ValueError, match="At least one field"):
            update_did_document(wallet, network='testnet')

    def test_update_did_document_too_large(self):
        """Test error when DID document exceeds size limit"""
        wallet = Wallet.create()

        # Create oversized document (>256 bytes)
        large_doc = {
            "id": "did:example:123",
            "data": "x" * 1000  # Too large
        }

        with pytest.raises(ValueError, match="exceeds maximum size"):
            update_did_document(
                wallet,
                network='testnet',
                did_document=large_doc
            )


class TestDIDDatabaseIntegration:
    """Test DID service integration with database"""

    @pytest.mark.integration
    @pytest.mark.database
    def test_create_did_updates_database(self, funded_wallet, db_session):
        """Test that DID creation updates user record"""
        address = funded_wallet.classic_address

        # Ensure user exists
        user = db_session.query(User).filter_by(address=address).first()
        if not user:
            user = User(address=address)
            db_session.add(user)
            db_session.commit()

        # Create DID with database update
        did = create_did_for_user(
            funded_wallet,
            network='testnet',
            update_database=True
        )

        # Verify database was updated
        db_session.refresh(user)
        assert user.did == did

    @pytest.mark.integration
    @pytest.mark.database
    def test_delete_did_updates_database(self, funded_wallet, db_session):
        """Test that DID deletion updates user record"""
        address = funded_wallet.classic_address

        # Create user with DID
        did = create_did_for_user(
            funded_wallet,
            network='testnet',
            update_database=True
        )

        import time
        time.sleep(5)

        # Delete DID with database update
        success = delete_did(
            funded_wallet,
            network='testnet',
            update_database=True
        )

        assert success

        # Verify database was updated
        user = db_session.query(User).filter_by(address=address).first()
        assert user.did is None
