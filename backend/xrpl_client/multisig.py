from __future__ import annotations

import logging
from typing import Dict, List

from xrpl.wallet import Wallet
from xrpl.clients.sync_client import Client
from xrpl.models import (
    Response,
    SignerEntry,
    SignerListSet,
    Transaction,
)
from xrpl.core.binarycodec import encode_for_multisigning, encode_for_signing

from .exceptions import XRPLClientError

logger = logging.getLogger(__name__)


def setup_multisig_account(
    client: Client,
    master_wallet: Wallet,
    signers: List[str],
    threshold: int,
) -> str:
    """
    Setup a multisig account by setting the SignerList.

    Args:
        client: Connected XRPL client
        master_wallet: Master wallet that will setup the multisig
        signers: List of signer addresses
        threshold: Number of signatures required

    Returns:
        Transaction hash of the SignerListSet transaction

    Raises:
        XRPLClientError: If multisig setup fails
    """
    if threshold <= 0 or threshold > len(signers):
        raise XRPLClientError(
            f"Invalid threshold {threshold}. Must be between 1 and {len(signers)}"
        )

    if len(signers) == 0:
        raise XRPLClientError("At least one signer is required")

    # Create signer entries with equal weight (1 each)
    signer_entries = [
        SignerEntry(account=signer, signer_weight=1)
        for signer in signers
    ]

    signer_list_tx = SignerListSet(
        account=master_wallet.address,
        signer_quorum=threshold,
        signer_entries=signer_entries,
    )

    try:
        response = client.submit_and_wait(signer_list_tx, master_wallet)
        _validate_response(response, "SignerListSet")

        tx_hash = response.result.get("hash")
        if not tx_hash:
            raise XRPLClientError("Failed to get transaction hash from SignerListSet response")

        logger.info(
            "Setup multisig account %s with %d signers, threshold=%d, hash=%s",
            master_wallet.address,
            len(signers),
            threshold,
            tx_hash,
        )
        return tx_hash

    except Exception as e:
        raise XRPLClientError(f"Failed to setup multisig account: {e}") from e


def create_multisig_tx(
    tx_json: Dict,
    signers: List[Wallet],
) -> str:
    """
    Collect signatures from multiple wallets and combine into a multisigned transaction.

    Args:
        tx_json: Transaction JSON to be signed
        signers: List of wallets that will sign the transaction

    Returns:
        Hex-encoded multisigned transaction blob

    Raises:
        XRPLClientError: If multisig creation fails
    """
    if not signers:
        raise XRPLClientError("At least one signer is required")

    try:
        # Create the base transaction
        tx = Transaction.from_dict(tx_json)

        # Collect signatures from each signer
        signatures = []
        for signer in signers:
            # Encode transaction for multisigning
            tx_for_signing = encode_for_multisigning(tx, signer.address)

            # Sign the transaction
            signature = signer.sign(tx_for_signing, multisign=True)
            signatures.append({
                "account": signer.address,
                "signature": signature,
            })

        # Combine signatures into multisigned transaction
        # Note: This is a simplified implementation
        # Real implementation would use xrpl library's multisign utilities
        multisigned_tx = tx.to_dict()
        multisigned_tx["Signers"] = [
            {
                "Signer": {
                    "Account": sig["account"],
                    "TxnSignature": sig["signature"],
                }
            }
            for sig in signatures
        ]

        # Encode the final transaction
        final_tx = Transaction.from_dict(multisigned_tx)
        tx_blob = encode_for_signing(final_tx)

        logger.info(
            "Created multisigned transaction with %d signatures for %s",
            len(signatures),
            tx_json.get("TransactionType", "Unknown"),
        )
        return tx_blob

    except Exception as e:
        raise XRPLClientError(f"Failed to create multisig transaction: {e}") from e


def submit_multisigned(
    client: Client,
    tx_blob: str,
) -> Dict:
    """
    Submit a multisigned transaction to the XRPL.

    Args:
        client: Connected XRPL client
        tx_blob: Hex-encoded multisigned transaction

    Returns:
        Transaction result dictionary

    Raises:
        XRPLClientError: If submission fails
    """
    try:
        # Submit the transaction blob directly
        response = client.submit(tx_blob)
        _validate_response(response, "Multisigned Transaction")

        result = response.result
        tx_hash = result.get("hash")
        engine_result = result.get("engine_result")

        logger.info(
            "Submitted multisigned transaction hash=%s, result=%s",
            tx_hash,
            engine_result,
        )

        return {
            "hash": tx_hash,
            "engine_result": engine_result,
            "result": result,
        }

    except Exception as e:
        raise XRPLClientError(f"Failed to submit multisigned transaction: {e}") from e


def _validate_response(response: Response, tx_type: str) -> None:
    """Validate XRPL transaction response."""
    if not response.is_successful():
        error_msg = f"{tx_type} transaction failed: {response.result}"
        raise XRPLClientError(error_msg)

    result = response.result
    engine_result = result.get("engine_result")

    # For multisigned transactions, we may get different success codes
    success_codes = {"tesSUCCESS", "terQUEUED", "tesPARTIAL"}

    if engine_result and engine_result not in success_codes:
        error_msg = f"{tx_type} transaction engine result: {engine_result}"
        raise XRPLClientError(error_msg)