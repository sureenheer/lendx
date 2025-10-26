"""
DID (Decentralized Identifier) service for XRPL identity management.

This service implements W3C DID v1.0 compliant identity creation and management
on the XRP Ledger using the DIDSet and DIDDelete transactions (XLS-40 amendment).

The DID format follows: did:xrpl:{network}:{address}
- network: 1 for testnet, 0 for mainnet
- address: XRPL wallet address

DID documents contain verification methods for cryptographic identity verification.
"""

import json
import logging
from typing import Optional, Dict, Any, Literal
from xrpl.wallet import Wallet
from xrpl.models.transactions import DIDSet, DIDDelete
from xrpl.models.requests import LedgerEntry
from xrpl.clients import JsonRpcClient

from backend.xrpl_client.client import connect, submit_and_wait as xrpl_submit_and_wait
from backend.xrpl_client.exceptions import wrap_xrpl_exception, XRPLClientError
from backend.config.database import get_db_session
from backend.models.database import User

logger = logging.getLogger(__name__)


# Network identifiers for DID format
NETWORK_TESTNET = "1"
NETWORK_MAINNET = "0"


def _get_network_id(network: Literal['testnet', 'mainnet']) -> str:
    """Get network ID for DID format."""
    return NETWORK_TESTNET if network == 'testnet' else NETWORK_MAINNET


def _format_did(address: str, network: Literal['testnet', 'mainnet'] = 'testnet') -> str:
    """
    Format DID string according to W3C DID specification.

    Format: did:xrpl:{network}:{address}

    Args:
        address: XRPL wallet address
        network: Network type ('testnet' or 'mainnet')

    Returns:
        Formatted DID string
    """
    network_id = _get_network_id(network)
    return f"did:xrpl:{network_id}:{address}"


def _create_did_document(
    address: str,
    public_key: str,
    network: Literal['testnet', 'mainnet'] = 'testnet'
) -> Dict[str, Any]:
    """
    Create W3C compliant DID document.

    Args:
        address: XRPL wallet address
        public_key: Public key for verification (hex-encoded)
        network: Network type

    Returns:
        DID document as dictionary
    """
    did = _format_did(address, network)

    return {
        "@context": [
            "https://www.w3.org/ns/did/v1",
            "https://w3id.org/security/suites/ed25519-2020/v1"
        ],
        "id": did,
        "verificationMethod": [{
            "id": f"{did}#keys-1",
            "type": "Ed25519VerificationKey2020",
            "controller": did,
            "publicKeyMultibase": public_key
        }],
        "authentication": [
            f"{did}#keys-1"
        ],
        "assertionMethod": [
            f"{did}#keys-1"
        ]
    }


def _encode_hex(data: str) -> str:
    """Encode string data to uppercase hex format required by XRPL."""
    return data.encode('utf-8').hex().upper()


def _decode_hex(hex_data: str) -> str:
    """Decode hex string to UTF-8 string."""
    return bytes.fromhex(hex_data).decode('utf-8')


@wrap_xrpl_exception
def create_did_for_user(
    user_wallet: Wallet,
    network: Literal['testnet', 'mainnet'] = 'testnet',
    update_database: bool = True,
    uri: Optional[str] = None,
    data: Optional[str] = None
) -> str:
    """
    Create on-chain DID for user during signup.

    This function:
    1. Creates a W3C compliant DID document
    2. Submits a DIDSet transaction to XRPL
    3. Optionally updates the user record in the database

    Args:
        user_wallet: User's XRPL wallet
        network: Target network ('testnet' or 'mainnet')
        update_database: If True, update user record with DID
        uri: Optional URI pointing to off-chain DID document (hex-encoded if provided)
        data: Optional additional data (hex-encoded if provided)

    Returns:
        DID string in format: "did:xrpl:{network}:{address}"

    Raises:
        XRPLClientError: If DID creation fails
        ValueError: If user wallet is invalid

    Example:
        >>> from xrpl.wallet import Wallet
        >>> wallet = Wallet.create()
        >>> did = create_did_for_user(wallet, network='testnet')
        >>> print(did)
        'did:xrpl:1:rN7n7otQDd6FczFgLdlqtyMVrn3HMfXkPj'
    """
    if not user_wallet or not user_wallet.classic_address:
        raise ValueError("Invalid user wallet provided")

    address = user_wallet.classic_address
    public_key = user_wallet.public_key

    logger.info(f"Creating DID for user {address} on {network}")

    # Format DID
    did = _format_did(address, network)

    # Create DID document
    did_document = _create_did_document(address, public_key, network)
    did_document_json = json.dumps(did_document)

    # Connect to XRPL
    client = connect(network)

    try:
        # Prepare DIDSet transaction
        # IMPORTANT: The did_document field has a 256 CHARACTER limit (not bytes)
        # This means 128 bytes max since hex encoding doubles the length
        # For most DID documents, this is too small, so we use URI instead
        did_document_hex = _encode_hex(did_document_json)

        # Check if document fits in the 256 character limit
        if len(did_document_hex) <= 256:
            logger.info(f"DID document fits on-chain ({len(did_document_hex)} chars)")
            # Store full DID document on-chain
            tx = DIDSet(
                account=address,
                did_document=did_document_hex,
                uri=_encode_hex(uri) if uri else None,
                data=_encode_hex(data) if data else None
            )
        else:
            logger.info(f"DID document too large ({len(did_document_hex)} chars), using URI approach")
            # In production, upload full DID document to IPFS or other decentralized storage
            # and store the URI in the URI field. For now, store essential data on-chain.
            tx = DIDSet(
                account=address,
                uri=_encode_hex(uri or f"https://lendx.com/did/{address}.json"),
                data=_encode_hex(data or f"pubkey:{public_key}")
            )

        # Submit transaction
        response = xrpl_submit_and_wait(client, tx, user_wallet)

        if response.get('meta', {}).get('TransactionResult') != 'tesSUCCESS':
            raise XRPLClientError(
                f"DID creation failed: {response.get('meta', {}).get('TransactionResult')}"
            )

        logger.info(f"DID created successfully: {did}")
        logger.info(f"Transaction hash: {response.get('hash')}")

        # Update database if requested
        if update_database:
            try:
                session = get_db_session()
                try:
                    user = session.query(User).filter_by(address=address).first()
                    if user:
                        user.did = did
                        session.commit()
                        logger.info(f"Updated user {address} with DID {did}")
                    else:
                        # Create new user if doesn't exist
                        new_user = User(address=address, did=did)
                        session.add(new_user)
                        session.commit()
                        logger.info(f"Created new user {address} with DID {did}")
                finally:
                    session.close()
            except Exception as e:
                logger.error(f"Failed to update database with DID: {e}")
                # Don't fail the whole operation if database update fails

        return did

    except Exception as e:
        logger.error(f"Failed to create DID for {address}: {e}")
        raise


@wrap_xrpl_exception
def get_did_document(
    address: str,
    network: Literal['testnet', 'mainnet'] = 'testnet'
) -> Optional[Dict[str, Any]]:
    """
    Retrieve DID document from XRPL ledger.

    This function queries the ledger for the DID object associated with
    the given address and returns the parsed DID document.

    Args:
        address: XRPL wallet address
        network: Target network ('testnet' or 'mainnet')

    Returns:
        DID document as dict with verification methods, or None if not found

    Raises:
        XRPLClientError: If ledger query fails

    Example:
        >>> doc = get_did_document('rN7n7otQDd6FczFgLdlqtyMVrn3HMfXkPj')
        >>> print(doc['id'])
        'did:xrpl:1:rN7n7otQDd6FczFgLdlqtyMVrn3HMfXkPj'
    """
    logger.info(f"Retrieving DID document for {address} from {network}")

    client = connect(network)

    try:
        # Query ledger for DID entry
        request = LedgerEntry(
            did=address,
            ledger_index="validated"
        )

        response = client.request(request)

        if response.is_successful():
            node = response.result.get('node')

            if not node:
                logger.info(f"No DID found for address {address}")
                return None

            # Extract DID fields
            did_document_hex = node.get('DIDDocument')
            uri_hex = node.get('URI')
            data_hex = node.get('Data')

            # Parse DID document if available
            if did_document_hex:
                try:
                    did_document_json = _decode_hex(did_document_hex)
                    did_document = json.loads(did_document_json)

                    # Add additional fields from ledger
                    did_document['_ledger'] = {
                        'uri': _decode_hex(uri_hex) if uri_hex else None,
                        'data': _decode_hex(data_hex) if data_hex else None,
                        'owner': node.get('Account'),
                        'ledger_index': node.get('index')
                    }

                    return did_document
                except (json.JSONDecodeError, ValueError) as e:
                    logger.error(f"Failed to parse DID document: {e}")

            # If no document stored on-chain, construct minimal document
            did = _format_did(address, network)
            minimal_doc = {
                "id": did,
                "_ledger": {
                    'uri': _decode_hex(uri_hex) if uri_hex else None,
                    'data': _decode_hex(data_hex) if data_hex else None,
                    'owner': node.get('Account'),
                    'ledger_index': node.get('index')
                },
                "note": "Full DID document may be available at URI"
            }

            return minimal_doc
        else:
            logger.warning(f"Failed to retrieve DID for {address}: {response.result}")
            return None

    except Exception as e:
        logger.error(f"Error retrieving DID document for {address}: {e}")
        raise


@wrap_xrpl_exception
def update_did_document(
    user_wallet: Wallet,
    network: Literal['testnet', 'mainnet'] = 'testnet',
    uri: Optional[str] = None,
    data: Optional[str] = None,
    did_document: Optional[Dict[str, Any]] = None
) -> bool:
    """
    Update DID document on XRPL.

    This function submits a new DIDSet transaction to update the existing
    DID document. All fields are optional - only provided fields will be updated.

    Args:
        user_wallet: User's XRPL wallet
        network: Target network ('testnet' or 'mainnet')
        uri: New URI value (will be hex-encoded)
        data: New data value (will be hex-encoded)
        did_document: New DID document (will be JSON-encoded then hex-encoded)

    Returns:
        True if successful, False otherwise

    Raises:
        XRPLClientError: If update transaction fails
        ValueError: If no fields provided for update

    Example:
        >>> success = update_did_document(
        ...     wallet,
        ...     uri="https://example.com/did-doc.json"
        ... )
    """
    if not any([uri, data, did_document]):
        raise ValueError("At least one field (uri, data, or did_document) must be provided for update")

    address = user_wallet.classic_address
    logger.info(f"Updating DID for {address} on {network}")

    client = connect(network)

    try:
        # Prepare transaction with updated fields
        tx_params = {"account": address}

        if uri:
            tx_params["uri"] = _encode_hex(uri)

        if data:
            tx_params["data"] = _encode_hex(data)

        if did_document:
            did_doc_json = json.dumps(did_document)
            did_doc_hex = _encode_hex(did_doc_json)

            if len(did_doc_hex) > 256:  # 256 character limit
                logger.warning("DID document too large for on-chain storage")
                raise ValueError("DID document exceeds maximum size (256 characters = 128 bytes)")

            tx_params["did_document"] = did_doc_hex

        tx = DIDSet(**tx_params)

        # Submit transaction
        response = xrpl_submit_and_wait(client, tx, user_wallet)

        if response.get('meta', {}).get('TransactionResult') != 'tesSUCCESS':
            logger.error(f"DID update failed: {response.get('meta', {}).get('TransactionResult')}")
            return False

        logger.info(f"DID updated successfully for {address}")
        logger.info(f"Transaction hash: {response.get('hash')}")

        return True

    except Exception as e:
        logger.error(f"Failed to update DID for {address}: {e}")
        raise


@wrap_xrpl_exception
def delete_did(
    user_wallet: Wallet,
    network: Literal['testnet', 'mainnet'] = 'testnet',
    update_database: bool = True
) -> bool:
    """
    Delete DID from XRPL ledger.

    This removes the DID object from the ledger. This operation is irreversible.

    Args:
        user_wallet: User's XRPL wallet
        network: Target network ('testnet' or 'mainnet')
        update_database: If True, remove DID from user record

    Returns:
        True if successful

    Raises:
        XRPLClientError: If delete transaction fails
    """
    address = user_wallet.classic_address
    logger.info(f"Deleting DID for {address} on {network}")

    client = connect(network)

    try:
        tx = DIDDelete(account=address)

        response = xrpl_submit_and_wait(client, tx, user_wallet)

        if response.get('meta', {}).get('TransactionResult') != 'tesSUCCESS':
            logger.error(f"DID deletion failed: {response.get('meta', {}).get('TransactionResult')}")
            return False

        logger.info(f"DID deleted successfully for {address}")

        # Update database if requested
        if update_database:
            try:
                session = get_db_session()
                try:
                    user = session.query(User).filter_by(address=address).first()
                    if user:
                        user.did = None
                        session.commit()
                        logger.info(f"Removed DID from user {address} in database")
                finally:
                    session.close()
            except Exception as e:
                logger.error(f"Failed to update database after DID deletion: {e}")

        return True

    except Exception as e:
        logger.error(f"Failed to delete DID for {address}: {e}")
        raise


def get_did_from_address(
    address: str,
    network: Literal['testnet', 'mainnet'] = 'testnet'
) -> Optional[str]:
    """
    Get DID string for an address.

    This is a convenience function that checks if a DID exists on-chain
    and returns the formatted DID string.

    Args:
        address: XRPL wallet address
        network: Target network

    Returns:
        DID string if exists, None otherwise
    """
    doc = get_did_document(address, network)
    if doc:
        return doc.get('id') or _format_did(address, network)
    return None
