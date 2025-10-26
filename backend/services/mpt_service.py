"""
MPT (Multi-Purpose Token) service layer for LendX.

This service provides CRUD operations for the 4 MPT types:
- PoolMPT: Lending pool configurations
- ApplicationMPT: Loan application records
- LoanMPT: Active and completed loan records
- DefaultMPT: Borrower default tracking (global, system-owned)

MPT metadata is immutable after creation on XRPL. Mutable state (like application
status or loan status) is tracked in the database with transaction memos for updates.
"""

import logging
import json
from typing import Optional, Dict, Any
from decimal import Decimal
from datetime import datetime

from xrpl.clients import JsonRpcClient
from xrpl.wallet import Wallet
from xrpl.models import AccountObjects

from backend.xrpl_client import connect
from backend.xrpl_client.mpt import create_issuance, mint_to_holder, get_mpt_balance
from backend.xrpl_client.exceptions import XRPLClientError, wrap_xrpl_exception
from backend.models.mpt_schemas import (
    PoolMPTMetadata,
    ApplicationMPTMetadata,
    LoanMPTMetadata,
    DefaultMPTMetadata,
    ApplicationState,
    LoanState
)

logger = logging.getLogger(__name__)


@wrap_xrpl_exception
def create_pool_mpt(
    client: JsonRpcClient,
    issuer_wallet: Wallet,
    metadata: PoolMPTMetadata
) -> Dict[str, str]:
    """
    Create a PoolMPT token representing a lending pool.

    Args:
        client: Connected XRPL client
        issuer_wallet: Lender's wallet (pool owner)
        metadata: Pool configuration metadata

    Returns:
        Dictionary with 'mpt_id' and 'tx_hash'

    Raises:
        XRPLClientError: If MPT creation fails
        ValueError: If metadata validation fails
    """
    try:
        # Validate metadata
        if metadata.issuer_addr != issuer_wallet.classic_address:
            raise ValueError(
                f"issuer_addr in metadata ({metadata.issuer_addr}) must match wallet address ({issuer_wallet.classic_address})"
            )

        # Create ticker symbol (max 3 chars for XRPL)
        ticker = "POOL"

        # Create name with pool details
        name = f"LendX Pool {metadata.total_balance}XRP @{metadata.interest_rate}%"

        # Create MPT issuance with metadata
        result = create_issuance(
            client=client,
            issuer_wallet=issuer_wallet,
            ticker=ticker,
            name=name
        )

        logger.info(f"Created PoolMPT {result['mpt_id']} for issuer {issuer_wallet.classic_address}")

        return {
            "mpt_id": result['mpt_id'],
            "tx_hash": result['tx_hash'],
            "metadata": metadata.to_json_dict()
        }

    except Exception as e:
        logger.error(f"Failed to create PoolMPT: {e}")
        raise


@wrap_xrpl_exception
def create_application_mpt(
    client: JsonRpcClient,
    borrower_wallet: Wallet,
    metadata: ApplicationMPTMetadata
) -> Dict[str, str]:
    """
    Create an ApplicationMPT token representing a loan application.

    Args:
        client: Connected XRPL client
        borrower_wallet: Borrower's wallet
        metadata: Application metadata

    Returns:
        Dictionary with 'mpt_id' and 'tx_hash'

    Raises:
        XRPLClientError: If MPT creation fails
        ValueError: If metadata validation fails
    """
    try:
        # Validate metadata
        if metadata.borrower_addr != borrower_wallet.classic_address:
            raise ValueError(
                f"borrower_addr in metadata ({metadata.borrower_addr}) must match wallet address ({borrower_wallet.classic_address})"
            )

        # Create ticker symbol
        ticker = "APP"

        # Create name with application details
        name = f"LendX Application {metadata.principal}XRP"

        # Create MPT issuance
        result = create_issuance(
            client=client,
            issuer_wallet=borrower_wallet,
            ticker=ticker,
            name=name
        )

        logger.info(f"Created ApplicationMPT {result['mpt_id']} for borrower {borrower_wallet.classic_address}")

        return {
            "mpt_id": result['mpt_id'],
            "tx_hash": result['tx_hash'],
            "metadata": metadata.to_json_dict()
        }

    except Exception as e:
        logger.error(f"Failed to create ApplicationMPT: {e}")
        raise


@wrap_xrpl_exception
def create_loan_mpt(
    client: JsonRpcClient,
    lender_wallet: Wallet,
    metadata: LoanMPTMetadata
) -> Dict[str, str]:
    """
    Create a LoanMPT token representing an active or completed loan.

    Args:
        client: Connected XRPL client
        lender_wallet: Lender's wallet (loan issuer)
        metadata: Loan metadata

    Returns:
        Dictionary with 'mpt_id' and 'tx_hash'

    Raises:
        XRPLClientError: If MPT creation fails
        ValueError: If metadata validation fails
    """
    try:
        # Validate metadata
        if metadata.lender_addr != lender_wallet.classic_address:
            raise ValueError(
                f"lender_addr in metadata ({metadata.lender_addr}) must match wallet address ({lender_wallet.classic_address})"
            )

        # Create ticker symbol
        ticker = "LOAN"

        # Create name with loan details
        name = f"LendX Loan {metadata.principal}XRP"

        # Create MPT issuance
        result = create_issuance(
            client=client,
            issuer_wallet=lender_wallet,
            ticker=ticker,
            name=name
        )

        logger.info(f"Created LoanMPT {result['mpt_id']} for lender {lender_wallet.classic_address}")

        return {
            "mpt_id": result['mpt_id'],
            "tx_hash": result['tx_hash'],
            "metadata": metadata.to_json_dict()
        }

    except Exception as e:
        logger.error(f"Failed to create LoanMPT: {e}")
        raise


# Global DefaultMPT ID (set once after system initialization)
_DEFAULT_MPT_ID: Optional[str] = None


def set_default_mpt_id(mpt_id: str) -> None:
    """
    Set the global DefaultMPT ID.

    This should be called once during system initialization after creating
    the DefaultMPT issuance.

    Args:
        mpt_id: The DefaultMPT issuance ID
    """
    global _DEFAULT_MPT_ID
    _DEFAULT_MPT_ID = mpt_id
    logger.info(f"Set global DefaultMPT ID: {mpt_id}")


def get_default_mpt_id() -> Optional[str]:
    """
    Get the global DefaultMPT ID.

    Returns:
        The DefaultMPT issuance ID, or None if not initialized
    """
    return _DEFAULT_MPT_ID


@wrap_xrpl_exception
def create_default_mpt(
    client: JsonRpcClient,
    system_wallet: Wallet
) -> Dict[str, str]:
    """
    Create the global DefaultMPT token for tracking borrower defaults.

    This should only be called once during system initialization.
    The DefaultMPT is a system-owned token where each borrower's default
    amount is tracked as their token balance.

    Args:
        client: Connected XRPL client
        system_wallet: System wallet (DefaultMPT issuer)

    Returns:
        Dictionary with 'mpt_id'

    Raises:
        XRPLClientError: If MPT creation fails
        RuntimeError: If DefaultMPT already exists
    """
    global _DEFAULT_MPT_ID

    try:
        # Check if DefaultMPT already exists
        if _DEFAULT_MPT_ID is not None:
            raise RuntimeError(
                f"DefaultMPT already exists with ID: {_DEFAULT_MPT_ID}. "
                "This token should only be created once."
            )

        # Create ticker symbol
        ticker = "DEF"

        # Create name
        name = "LendX Default Tracker"

        # Create MPT issuance
        mpt_id = create_issuance(
            client=client,
            issuer_wallet=system_wallet,
            ticker=ticker,
            name=name
        )

        # Set global ID
        _DEFAULT_MPT_ID = mpt_id

        logger.info(f"Created DefaultMPT {mpt_id} for system wallet {system_wallet.classic_address}")

        return {
            "mpt_id": mpt_id,
            "issuer": system_wallet.classic_address
        }

    except Exception as e:
        logger.error(f"Failed to create DefaultMPT: {e}")
        raise


@wrap_xrpl_exception
def get_mpt_metadata(
    client: JsonRpcClient,
    issuer_address: str,
    mpt_id: str
) -> Optional[Dict[str, Any]]:
    """
    Retrieve MPT metadata from XRPL.

    Note: This is a placeholder implementation. XRPL MPT metadata retrieval
    depends on how metadata is stored (transaction memos, separate data structures, etc.).
    For now, we rely on database storage of metadata.

    Args:
        client: Connected XRPL client
        issuer_address: MPT issuer address
        mpt_id: MPT issuance ID

    Returns:
        Metadata dictionary, or None if not found

    Raises:
        XRPLClientError: If query fails
    """
    try:
        # Query account objects for MPToken issuance
        request = AccountObjects(
            account=issuer_address,
            type="mpt_issuance"
        )

        response = client.request(request)

        if not response.is_successful():
            raise XRPLClientError(f"Failed to query account objects: {response.result}")

        # Look for the specific MPT issuance
        account_objects = response.result.get('account_objects', [])

        for obj in account_objects:
            if obj.get('MPTokenID') == mpt_id:
                # Extract metadata from object
                # Note: This is a simplified implementation
                # Actual metadata structure depends on XRPL implementation
                metadata = obj.get('Metadata', {})
                logger.debug(f"Found MPT metadata for {mpt_id}: {metadata}")
                return metadata

        # MPT not found
        logger.warning(f"MPT {mpt_id} not found for issuer {issuer_address}")
        return None

    except Exception as e:
        logger.error(f"Failed to get MPT metadata: {e}")
        raise


@wrap_xrpl_exception
def track_borrower_default(
    client: JsonRpcClient,
    system_wallet: Wallet,
    borrower_address: str,
    default_amount: Decimal
) -> str:
    """
    Track a borrower default by minting DefaultMPT tokens.

    The amount of DefaultMPT tokens held by a borrower represents their
    total default amount across all loans.

    Args:
        client: Connected XRPL client
        system_wallet: System wallet (DefaultMPT issuer)
        borrower_address: Borrower's address
        default_amount: Amount to add to default balance

    Returns:
        Transaction hash

    Raises:
        XRPLClientError: If minting fails
        RuntimeError: If DefaultMPT not initialized
    """
    try:
        # Ensure DefaultMPT exists
        if _DEFAULT_MPT_ID is None:
            raise RuntimeError(
                "DefaultMPT not initialized. Call create_default_mpt() first."
            )

        # Mint default tokens to borrower
        # This increases their default balance
        tx_hash = mint_to_holder(
            client=client,
            issuer_wallet=system_wallet,
            holder=borrower_address,
            amount=float(default_amount),
            issuance_id=_DEFAULT_MPT_ID
        )

        logger.info(f"Tracked default of {default_amount} XRP for borrower {borrower_address}")

        return tx_hash

    except Exception as e:
        logger.error(f"Failed to track borrower default: {e}")
        raise


@wrap_xrpl_exception
def get_borrower_default_balance(
    client: JsonRpcClient,
    borrower_address: str
) -> Decimal:
    """
    Get a borrower's total default balance.

    Args:
        client: Connected XRPL client
        borrower_address: Borrower's address

    Returns:
        Total default amount as Decimal

    Raises:
        XRPLClientError: If query fails
        RuntimeError: If DefaultMPT not initialized
    """
    try:
        # Ensure DefaultMPT exists
        if _DEFAULT_MPT_ID is None:
            raise RuntimeError(
                "DefaultMPT not initialized. Call create_default_mpt() first."
            )

        # Get DefaultMPT balance for borrower
        balance = get_mpt_balance(
            client=client,
            holder_address=borrower_address,
            issuance_id=_DEFAULT_MPT_ID
        )

        logger.debug(f"Default balance for {borrower_address}: {balance} XRP")

        return Decimal(str(balance))

    except Exception as e:
        logger.error(f"Failed to get borrower default balance: {e}")
        raise


# Helper functions for parsing metadata from database

def parse_pool_metadata(metadata_dict: Dict[str, Any]) -> PoolMPTMetadata:
    """
    Parse PoolMPT metadata from dictionary (e.g., from database).

    Args:
        metadata_dict: Metadata dictionary

    Returns:
        Validated PoolMPTMetadata object

    Raises:
        ValueError: If validation fails
    """
    return PoolMPTMetadata(**metadata_dict)


def parse_application_metadata(metadata_dict: Dict[str, Any]) -> ApplicationMPTMetadata:
    """
    Parse ApplicationMPT metadata from dictionary (e.g., from database).

    Args:
        metadata_dict: Metadata dictionary

    Returns:
        Validated ApplicationMPTMetadata object

    Raises:
        ValueError: If validation fails
    """
    # Handle datetime parsing if strings
    if isinstance(metadata_dict.get('application_date'), str):
        metadata_dict['application_date'] = datetime.fromisoformat(
            metadata_dict['application_date'].replace('Z', '+00:00')
        )
    if isinstance(metadata_dict.get('dissolution_date'), str):
        metadata_dict['dissolution_date'] = datetime.fromisoformat(
            metadata_dict['dissolution_date'].replace('Z', '+00:00')
        )

    return ApplicationMPTMetadata(**metadata_dict)


def parse_loan_metadata(metadata_dict: Dict[str, Any]) -> LoanMPTMetadata:
    """
    Parse LoanMPT metadata from dictionary (e.g., from database).

    Args:
        metadata_dict: Metadata dictionary

    Returns:
        Validated LoanMPTMetadata object

    Raises:
        ValueError: If validation fails
    """
    # Handle datetime parsing if strings
    if isinstance(metadata_dict.get('start_date'), str):
        metadata_dict['start_date'] = datetime.fromisoformat(
            metadata_dict['start_date'].replace('Z', '+00:00')
        )
    if isinstance(metadata_dict.get('end_date'), str):
        metadata_dict['end_date'] = datetime.fromisoformat(
            metadata_dict['end_date'].replace('Z', '+00:00')
        )

    return LoanMPTMetadata(**metadata_dict)


def parse_default_metadata(metadata_dict: Dict[str, Any]) -> DefaultMPTMetadata:
    """
    Parse DefaultMPT metadata from dictionary (e.g., from database).

    Args:
        metadata_dict: Metadata dictionary

    Returns:
        Validated DefaultMPTMetadata object

    Raises:
        ValueError: If validation fails
    """
    return DefaultMPTMetadata(**metadata_dict)
