"""Multi-Purpose Token (MPT) operations for XRPL."""

import logging
from typing import Dict, Any
from xrpl.clients import JsonRpcClient
from xrpl.models import (
    MPTokenIssuanceCreate,
    MPTokenAuthorize,
    Payment,
    AccountObjects,
    MPTokenIssuanceDestroy
)
from xrpl.wallet import Wallet
from xrpl.utils import hex_to_str
from decimal import Decimal

from .client import submit_and_wait
from .exceptions import wrap_xrpl_exception, XRPLClientError

logger = logging.getLogger(__name__)


@wrap_xrpl_exception
def create_issuance(client: JsonRpcClient, issuer_wallet: Wallet, ticker: str, name: str) -> str:
    """
    Create an MPT issuance with non-transferable flags.

    Args:
        client: Connected XRPL client
        issuer_wallet: Wallet of the token issuer
        ticker: Token ticker symbol
        name: Token display name

    Returns:
        Issuance ID from transaction metadata

    Raises:
        XRPLClientError: If issuance creation fails
    """
    try:
        # Create MPT issuance transaction with non-transferable flag
        tx = MPTokenIssuanceCreate(
            account=issuer_wallet.classic_address,
            mpt_id="00000000000000000000000000000000",  # Will be assigned by ledger
            # Non-transferable flag (0x00000002) - tokens can only be transferred by issuer
            flags=0x00000002,
            # Optional metadata
            ticker=ticker.encode('utf-8').hex() if len(ticker) <= 3 else None,
            metadata={
                "name": name,
                "ticker": ticker
            }
        )

        response = submit_and_wait(client, tx.to_dict(), issuer_wallet)

        # Extract issuance_id from metadata
        if 'meta' in response and 'CreatedNode' in response['meta']:
            for created_node in response['meta']['CreatedNode']:
                if created_node.get('LedgerEntryType') == 'MPToken':
                    issuance_id = created_node.get('NewFields', {}).get('MPTokenID')
                    if issuance_id:
                        logger.info(f"Created MPT issuance: {issuance_id}")
                        return issuance_id

        # Fallback: try to find in AffectedNodes
        for node in response.get('meta', {}).get('AffectedNodes', []):
            if 'CreatedNode' in node:
                created = node['CreatedNode']
                if created.get('LedgerEntryType') == 'MPToken':
                    issuance_id = created.get('NewFields', {}).get('MPTokenID')
                    if issuance_id:
                        logger.info(f"Created MPT issuance: {issuance_id}")
                        return issuance_id

        raise XRPLClientError("Failed to extract issuance_id from transaction metadata")

    except Exception as e:
        logger.error(f"MPT issuance creation failed: {e}")
        raise


@wrap_xrpl_exception
def authorize_holder(client: JsonRpcClient, holder_wallet: Wallet, issuance_id: str) -> str:
    """
    Submit MPTokenAuthorize transaction for a holder.

    Args:
        client: Connected XRPL client
        holder_wallet: Wallet of the token holder
        issuance_id: MPT issuance ID to authorize

    Returns:
        Transaction hash

    Raises:
        XRPLClientError: If authorization fails
    """
    try:
        tx = MPTokenAuthorize(
            account=holder_wallet.classic_address,
            mpt_id=issuance_id
        )

        response = submit_and_wait(client, tx.to_dict(), holder_wallet)
        tx_hash = response.get('hash')

        if not tx_hash:
            raise XRPLClientError("Failed to get transaction hash from response")

        logger.info(f"Authorized holder {holder_wallet.classic_address} for MPT {issuance_id}")
        return tx_hash

    except Exception as e:
        logger.error(f"MPT authorization failed: {e}")
        raise


@wrap_xrpl_exception
def get_mpt_balance(client: JsonRpcClient, holder_address: str, issuance_id: str) -> float:
    """
    Query MPT balance for a holder address.

    Args:
        client: Connected XRPL client
        holder_address: Address to check balance for
        issuance_id: MPT issuance ID

    Returns:
        MPT balance as float

    Raises:
        XRPLClientError: If balance query fails
    """
    try:
        # Query account objects for MPToken entries
        request = AccountObjects(
            account=holder_address,
            type="mptoken"
        )

        response = client.request(request)

        if not response.is_successful():
            raise XRPLClientError(f"Failed to query account objects: {response.result}")

        # Look for the specific MPT issuance
        account_objects = response.result.get('account_objects', [])

        for obj in account_objects:
            if obj.get('MPTokenID') == issuance_id:
                # Parse balance - MPT balances are stored as hex strings
                balance_hex = obj.get('MPTAmount', '0')
                if isinstance(balance_hex, str):
                    # Convert hex to decimal
                    balance = int(balance_hex, 16) if balance_hex.startswith('0x') else int(balance_hex)
                else:
                    balance = int(balance_hex)

                # Convert to float (assuming standard decimal places)
                balance_float = float(balance) / 1000000  # 6 decimal places standard

                logger.debug(f"MPT balance for {holder_address}: {balance_float}")
                return balance_float

        # No balance found - return 0
        logger.debug(f"No MPT balance found for {holder_address}, returning 0")
        return 0.0

    except Exception as e:
        logger.error(f"Failed to get MPT balance: {e}")
        raise


@wrap_xrpl_exception
def mint_to_holder(client: JsonRpcClient, issuer_wallet: Wallet, holder: str, amount: float, issuance_id: str) -> str:
    """
    Mint MPT tokens to a holder address.

    Args:
        client: Connected XRPL client
        issuer_wallet: Wallet of the token issuer
        holder: Address to mint tokens to
        amount: Amount to mint
        issuance_id: MPT issuance ID

    Returns:
        Transaction hash

    Raises:
        XRPLClientError: If minting fails
    """
    try:
        # Convert amount to MPT format (typically with 6 decimal places)
        mpt_amount = int(amount * 1000000)

        tx = Payment(
            account=issuer_wallet.classic_address,
            destination=holder,
            amount={
                "currency": issuance_id,
                "value": str(mpt_amount),
                "issuer": issuer_wallet.classic_address
            }
        )

        response = submit_and_wait(client, tx.to_dict(), issuer_wallet)
        tx_hash = response.get('hash')

        if not tx_hash:
            raise XRPLClientError("Failed to get transaction hash from response")

        logger.info(f"Minted {amount} MPT to {holder}, tx: {tx_hash}")
        return tx_hash

    except Exception as e:
        logger.error(f"MPT minting failed: {e}")
        raise


@wrap_xrpl_exception
def burn_from_holder(client: JsonRpcClient, issuer_wallet: Wallet, holder: str, amount: float, issuance_id: str) -> str:
    """
    Burn (clawback) MPT tokens from a holder address.

    Args:
        client: Connected XRPL client
        issuer_wallet: Wallet of the token issuer
        holder: Address to burn tokens from
        amount: Amount to burn
        issuance_id: MPT issuance ID

    Returns:
        Transaction hash

    Raises:
        XRPLClientError: If burning fails
    """
    try:
        # Convert amount to MPT format (typically with 6 decimal places)
        mpt_amount = int(amount * 1000000)

        # Clawback operation - negative amount payment from issuer perspective
        tx = Payment(
            account=issuer_wallet.classic_address,
            destination=holder,
            amount={
                "currency": issuance_id,
                "value": f"-{mpt_amount}",  # Negative value for clawback
                "issuer": issuer_wallet.classic_address
            },
            # Clawback flag
            flags=0x00000020
        )

        response = submit_and_wait(client, tx.to_dict(), issuer_wallet)
        tx_hash = response.get('hash')

        if not tx_hash:
            raise XRPLClientError("Failed to get transaction hash from response")

        logger.info(f"Burned {amount} MPT from {holder}, tx: {tx_hash}")
        return tx_hash

    except Exception as e:
        logger.error(f"MPT burning failed: {e}")
        raise


@wrap_xrpl_exception
def destroy_issuance(client: JsonRpcClient, issuer_wallet: Wallet, issuance_id: str) -> str:
    """
    Destroy an MPT issuance (optional utility function).

    Args:
        client: Connected XRPL client
        issuer_wallet: Wallet of the token issuer
        issuance_id: MPT issuance ID to destroy

    Returns:
        Transaction hash

    Raises:
        XRPLClientError: If destruction fails
    """
    try:
        tx = MPTokenIssuanceDestroy(
            account=issuer_wallet.classic_address,
            mpt_id=issuance_id
        )

        response = submit_and_wait(client, tx.to_dict(), issuer_wallet)
        tx_hash = response.get('hash')

        if not tx_hash:
            raise XRPLClientError("Failed to get transaction hash from response")

        logger.info(f"Destroyed MPT issuance {issuance_id}, tx: {tx_hash}")
        return tx_hash

    except Exception as e:
        logger.error(f"MPT issuance destruction failed: {e}")
        raise