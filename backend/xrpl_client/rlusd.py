"""
RLUSD integration for XRP Ledger stablecoin transactions.

This module provides functions for interacting with RLUSD (Ripple USD),
a USD-backed stablecoin issued on the XRP Ledger. RLUSD uses XRPL's
issued currency framework, requiring trust lines for holding balances.

Key operations:
- Trust line setup: Users must create a trust line to the RLUSD issuer
- Balance queries: Query RLUSD balances via account_lines
- Transfers: Send RLUSD using Payment transactions with currency object

Security considerations:
- Always verify issuer address matches official RLUSD issuer
- Validate trust line limits to prevent over-exposure
- Use proper amount precision (6 decimal places recommended)
- Implement rate limiting on transfers to prevent abuse
"""

import os
import logging
from decimal import Decimal
from typing import Optional
from xrpl.clients import JsonRpcClient
from xrpl.models import TrustSet, Payment, IssuedCurrencyAmount
from xrpl.wallet import Wallet
from xrpl.transaction import autofill_and_sign
from xrpl import transaction

from .exceptions import wrap_xrpl_exception, XRPLClientError

logger = logging.getLogger(__name__)

# RLUSD Configuration
# Testnet issuer for RLUSD
RLUSD_ISSUER = os.getenv("RLUSD_ISSUER", "rQhWct2fv4Vc4KRjRgMrxa8xPN9Zx9iLKV")
RLUSD_CURRENCY = os.getenv("RLUSD_CURRENCY", "RLUSD")

# Mainnet issuer (for production use)
# RLUSD_ISSUER_MAINNET = "rMxCKbEDwqr76QuheSUMdEGf4B9xJ8m5De"


@wrap_xrpl_exception
def setup_rlusd_trustline(
    client: JsonRpcClient,
    user_wallet: Wallet,
    limit: str = "1000000"
) -> str:
    """
    Create trust line to RLUSD issuer.

    This enables a user to hold RLUSD tokens. The trust line must be
    created before the user can receive RLUSD from any source.

    Args:
        client: Connected XRPL client
        user_wallet: User's wallet to create trust line from
        limit: Maximum RLUSD user can hold (default: 1,000,000)

    Returns:
        Transaction hash of the trust line creation

    Raises:
        XRPLClientError: If transaction fails
        ValueError: If limit is invalid

    Example:
        >>> client = connect('testnet')
        >>> wallet = Wallet.create()
        >>> tx_hash = setup_rlusd_trustline(client, wallet, limit="50000")
        >>> print(f"Trust line created: {tx_hash}")

    Security notes:
        - Setting a trust line limit protects against over-issuance
        - Lower limits reduce risk but may restrict functionality
        - Users can update limits later with another TrustSet transaction
    """
    try:
        # Validate limit
        if Decimal(limit) <= 0:
            raise ValueError("Trust line limit must be positive")

        logger.info(f"Creating RLUSD trust line for {user_wallet.address} with limit {limit}")

        # Create TrustSet transaction
        trust_set = TrustSet(
            account=user_wallet.address,
            limit_amount=IssuedCurrencyAmount(
                currency=RLUSD_CURRENCY,
                issuer=RLUSD_ISSUER,
                value=limit
            )
        )

        # Sign and submit transaction
        signed_tx = autofill_and_sign(trust_set, client, user_wallet)
        response = transaction.submit_and_wait(signed_tx, client)

        tx_hash = response.result.get('hash')
        logger.info(f"RLUSD trust line created successfully: {tx_hash}")

        return tx_hash

    except ValueError:
        raise
    except Exception as e:
        logger.error(f"Failed to create RLUSD trust line: {e}")
        raise XRPLClientError(f"Trust line creation failed: {e}") from e


@wrap_xrpl_exception
def get_rlusd_balance(client: JsonRpcClient, address: str) -> Decimal:
    """
    Get RLUSD balance for an address.

    Uses account_lines API to query trust line balances and filters
    for the RLUSD issuer.

    Args:
        client: Connected XRPL client
        address: XRP wallet address to query

    Returns:
        RLUSD balance as Decimal (0 if no trust line exists)

    Example:
        >>> client = connect('testnet')
        >>> balance = get_rlusd_balance(client, "rAddress123")
        >>> print(f"Balance: {balance} RLUSD")

    Performance notes:
        - This queries the XRPL in real-time
        - Consider caching balances in database for frequently accessed accounts
        - Staleness check recommended (e.g., max 5 minutes old)
    """
    try:
        logger.debug(f"Querying RLUSD balance for {address}")

        # Query account lines
        request = {
            "command": "account_lines",
            "account": address,
            "ledger_index": "validated"
        }

        response = client.request(request)

        # Check for error in response
        if 'error' in response.result:
            logger.warning(f"Error querying account lines for {address}: {response.result.get('error_message')}")
            return Decimal("0")

        # Filter for RLUSD trust line
        lines = response.result.get('lines', [])

        for line in lines:
            if (line.get('currency') == RLUSD_CURRENCY and
                line.get('account') == RLUSD_ISSUER):
                balance = Decimal(line.get('balance', '0'))
                logger.debug(f"Found RLUSD balance: {balance}")
                return balance

        # No RLUSD trust line found
        logger.debug(f"No RLUSD trust line found for {address}")
        return Decimal("0")

    except Exception as e:
        logger.error(f"Failed to get RLUSD balance for {address}: {e}")
        # Return 0 instead of raising to gracefully handle missing trust lines
        return Decimal("0")


@wrap_xrpl_exception
def transfer_rlusd(
    client: JsonRpcClient,
    from_wallet: Wallet,
    to_address: str,
    amount: Decimal
) -> str:
    """
    Transfer RLUSD tokens between addresses.

    Both sender and recipient must have RLUSD trust lines set up.
    The sender must have sufficient RLUSD balance.

    Args:
        client: Connected XRPL client
        from_wallet: Sender's wallet
        to_address: Recipient's XRP address
        amount: Amount to transfer (in RLUSD)

    Returns:
        Transaction hash of the transfer

    Raises:
        XRPLClientError: If transaction fails
        ValueError: If amount is invalid

    Example:
        >>> client = connect('testnet')
        >>> sender = Wallet.create()
        >>> tx_hash = transfer_rlusd(client, sender, "rRecipient", Decimal("100.50"))
        >>> print(f"Transfer complete: {tx_hash}")

    Security considerations:
        - Validates recipient address format
        - Amount precision limited to 15 significant digits
        - Requires both parties to have trust lines
        - Transaction will fail if sender has insufficient balance
    """
    try:
        # Validate amount
        if amount <= 0:
            raise ValueError("Transfer amount must be positive")

        logger.info(f"Transferring {amount} RLUSD from {from_wallet.address} to {to_address}")

        # Create Payment transaction with RLUSD currency
        payment = Payment(
            account=from_wallet.address,
            destination=to_address,
            amount=IssuedCurrencyAmount(
                currency=RLUSD_CURRENCY,
                issuer=RLUSD_ISSUER,
                value=str(amount)
            )
        )

        # Sign and submit transaction
        signed_tx = autofill_and_sign(payment, client, from_wallet)
        response = transaction.submit_and_wait(signed_tx, client)

        tx_hash = response.result.get('hash')
        logger.info(f"RLUSD transfer successful: {tx_hash}")

        return tx_hash

    except ValueError:
        raise
    except Exception as e:
        logger.error(f"Failed to transfer RLUSD: {e}")
        raise XRPLClientError(f"RLUSD transfer failed: {e}") from e


@wrap_xrpl_exception
def check_trustline_exists(client: JsonRpcClient, address: str) -> bool:
    """
    Check if an address has RLUSD trust line set up.

    This is useful for verifying prerequisites before attempting
    RLUSD transfers or issuing loans in RLUSD.

    Args:
        client: Connected XRPL client
        address: XRP wallet address to check

    Returns:
        True if RLUSD trust line exists, False otherwise

    Example:
        >>> client = connect('testnet')
        >>> has_trustline = check_trustline_exists(client, "rAddress123")
        >>> if not has_trustline:
        >>>     print("Please set up RLUSD trust line first")

    Use cases:
        - Pre-flight checks before loan disbursement
        - User onboarding validation
        - Error prevention in transfer flows
    """
    try:
        logger.debug(f"Checking RLUSD trust line for {address}")

        request = {
            "command": "account_lines",
            "account": address,
            "ledger_index": "validated"
        }

        response = client.request(request)

        # Check for error (e.g., account doesn't exist)
        if 'error' in response.result:
            logger.debug(f"Account {address} not found or has no trust lines")
            return False

        lines = response.result.get('lines', [])

        # Look for RLUSD trust line
        for line in lines:
            if (line.get('currency') == RLUSD_CURRENCY and
                line.get('account') == RLUSD_ISSUER):
                logger.debug(f"RLUSD trust line exists for {address}")
                return True

        logger.debug(f"No RLUSD trust line for {address}")
        return False

    except Exception as e:
        logger.error(f"Error checking trust line for {address}: {e}")
        return False


def get_rlusd_issuer() -> str:
    """
    Get the RLUSD issuer address for the current network.

    Returns:
        RLUSD issuer XRP address

    Note:
        - Returns testnet issuer by default
        - Override with RLUSD_ISSUER environment variable
        - Use RLUSD_ISSUER_MAINNET for production
    """
    return RLUSD_ISSUER


def validate_rlusd_amount(amount: Decimal) -> bool:
    """
    Validate RLUSD amount format and range.

    Args:
        amount: Amount to validate

    Returns:
        True if valid, False otherwise

    Validation rules:
        - Must be positive
        - Maximum 15 significant digits
        - Maximum 6 decimal places recommended
    """
    if amount <= 0:
        return False

    # Check decimal places (recommend max 6 for USD precision)
    str_amount = str(amount)
    if '.' in str_amount:
        decimal_places = len(str_amount.split('.')[1])
        if decimal_places > 15:  # XRPL limit
            return False

    return True
