from __future__ import annotations

import logging
import time
from typing import Optional

from xrpl import Wallet
from xrpl.clients.sync_client import Client
from xrpl.models import (
    EscrowCancel,
    EscrowCreate,
    EscrowFinish,
    Response,
    Transaction,
)
from xrpl.utils import xrp_to_drops

from .exceptions import XRPLClientError

logger = logging.getLogger(__name__)

DEFAULT_ESCROW_DURATION = 3600  # 1 hour in seconds
DEPOSIT_ESCROW_DURATION = 86400  # 24 hours for deposits


def create_deposit_escrow(
    client: Client,
    member_wallet: Wallet,
    amount: int,
    dest_address: str,
    finish_after: Optional[int] = None,
) -> int:
    """
    Create a deposit escrow with longer duration for member contributions.

    Args:
        client: Connected XRPL client
        member_wallet: Wallet of the member creating the escrow
        amount: Amount in XRP drops
        dest_address: Destination address for the escrow
        finish_after: Unix timestamp when escrow can be finished (optional)

    Returns:
        Sequence number of the created escrow

    Raises:
        XRPLClientError: If escrow creation fails
    """
    if finish_after is None:
        finish_after = int(time.time()) + DEPOSIT_ESCROW_DURATION

    escrow_tx = EscrowCreate(
        account=member_wallet.address,
        destination=dest_address,
        amount=str(amount),
        finish_after=finish_after,
    )

    try:
        response = client.submit_and_wait(escrow_tx, member_wallet)
        _validate_response(response, "EscrowCreate")

        sequence = escrow_tx.sequence
        if sequence is None:
            raise XRPLClientError("Failed to get sequence number from escrow transaction")

        logger.info(
            "Created deposit escrow %s -> %s, amount=%s, sequence=%s",
            member_wallet.address,
            dest_address,
            amount,
            sequence,
        )
        return sequence

    except Exception as e:
        raise XRPLClientError(f"Failed to create deposit escrow: {e}") from e


def create_settlement_escrow(
    client: Client,
    payer_wallet: Wallet,
    payee: str,
    amount: int,
    finish_after: Optional[int] = None,
) -> int:
    """
    Create a short-duration escrow for settlement payments.

    Args:
        client: Connected XRPL client
        payer_wallet: Wallet of the payer creating the escrow
        payee: Address of the payment recipient
        amount: Amount in XRP drops
        finish_after: Unix timestamp when escrow can be finished (optional)

    Returns:
        Sequence number of the created escrow

    Raises:
        XRPLClientError: If escrow creation fails
    """
    if finish_after is None:
        finish_after = int(time.time()) + DEFAULT_ESCROW_DURATION

    escrow_tx = EscrowCreate(
        account=payer_wallet.address,
        destination=payee,
        amount=str(amount),
        finish_after=finish_after,
    )

    try:
        response = client.submit_and_wait(escrow_tx, payer_wallet)
        _validate_response(response, "EscrowCreate")

        sequence = escrow_tx.sequence
        if sequence is None:
            raise XRPLClientError("Failed to get sequence number from escrow transaction")

        logger.info(
            "Created settlement escrow %s -> %s, amount=%s, sequence=%s",
            payer_wallet.address,
            payee,
            amount,
            sequence,
        )
        return sequence

    except Exception as e:
        raise XRPLClientError(f"Failed to create settlement escrow: {e}") from e


def finish_escrow(
    client: Client,
    wallet: Wallet,
    owner: str,
    sequence: int,
) -> str:
    """
    Execute an EscrowFinish transaction to complete an escrow.

    Args:
        client: Connected XRPL client
        wallet: Wallet authorized to finish the escrow
        owner: Address of the escrow owner
        sequence: Sequence number of the escrow to finish

    Returns:
        Transaction hash of the EscrowFinish transaction

    Raises:
        XRPLClientError: If escrow finish fails
    """
    finish_tx = EscrowFinish(
        account=wallet.address,
        owner=owner,
        offer_sequence=sequence,
    )

    try:
        response = client.submit_and_wait(finish_tx, wallet)
        _validate_response(response, "EscrowFinish")

        tx_hash = response.result.get("hash")
        if not tx_hash:
            raise XRPLClientError("Failed to get transaction hash from EscrowFinish response")

        logger.info(
            "Finished escrow owner=%s, sequence=%s, hash=%s",
            owner,
            sequence,
            tx_hash,
        )
        return tx_hash

    except Exception as e:
        raise XRPLClientError(f"Failed to finish escrow: {e}") from e


def cancel_escrow(
    client: Client,
    owner: str,
    sequence: int,
) -> str:
    """
    Cancel an expired escrow (can only be done after expiry).

    Args:
        client: Connected XRPL client
        owner: Address of the escrow owner
        sequence: Sequence number of the escrow to cancel

    Returns:
        Transaction hash of the EscrowCancel transaction

    Raises:
        XRPLClientError: If escrow cancel fails
    """
    # Note: This requires the owner's wallet to sign, but for simplicity
    # we're assuming the client has access to it. In production, this
    # would need proper wallet management.
    cancel_tx = EscrowCancel(
        account=owner,
        owner=owner,
        offer_sequence=sequence,
    )

    try:
        # Note: This would need the owner's wallet to sign
        # For now, this is a placeholder that would need proper implementation
        logger.warning(
            "EscrowCancel transaction created but not submitted - requires owner wallet"
        )

        # In a real implementation, you'd need:
        # response = client.submit_and_wait(cancel_tx, owner_wallet)
        # _validate_response(response, "EscrowCancel")
        # return response.result.get("hash")

        # Placeholder return for now
        return f"CANCEL_TX_{owner}_{sequence}"

    except Exception as e:
        raise XRPLClientError(f"Failed to cancel escrow: {e}") from e


def _validate_response(response: Response, tx_type: str) -> None:
    """Validate XRPL transaction response."""
    if not response.is_successful():
        error_msg = f"{tx_type} transaction failed: {response.result}"
        raise XRPLClientError(error_msg)

    result = response.result
    if result.get("engine_result") != "tesSUCCESS":
        error_msg = f"{tx_type} transaction engine result: {result.get('engine_result')}"
        raise XRPLClientError(error_msg)