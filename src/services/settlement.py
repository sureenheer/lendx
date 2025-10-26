from __future__ import annotations

import logging
import time
import uuid
from dataclasses import dataclass, field
from typing import Dict, List

from src.services.iou import get_group_balances

logger = logging.getLogger(__name__)

ESCROW_HOLD_SECONDS = 60 * 60  # 1 hour buffer before escrows can be canceled
REQUIRED_SIGNATURES = 2
DROPS_PER_UNIT = 1_000_000  # XRPL drops per XRP
EPSILON = 1e-9


@dataclass(slots=True)
class Payment:
    payer: str
    payee: str
    amount: float


@dataclass(slots=True)
class EscrowInstruction:
    payment: Payment
    transaction: dict
    tx_hash: str | None = None
    confirmed: bool = False
    executed: bool = False


@dataclass
class SettlementProposal:
    proposal_id: str
    group_id: str
    payments: List[Payment]
    escrows: List[EscrowInstruction]
    signatures: Dict[str, str] = field(default_factory=dict)
    status: str = "pending_signatures"
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)


_proposal_store: Dict[str, SettlementProposal] = {}


def propose_settlement(group_id: str) -> SettlementProposal:
    """
    Compute a settlement proposal by matching debtors to creditors greedily.
    """
    nets = get_group_balances(group_id)
    if not nets:
        raise ValueError(f"No balances available for group '{group_id}'")

    payments = _build_payments(nets)
    if not payments:
        raise ValueError("All balances are already settled")

    escrows = [_build_escrow_instruction(group_id, payment) for payment in payments]

    proposal = SettlementProposal(
        proposal_id=str(uuid.uuid4()),
        group_id=group_id,
        payments=payments,
        escrows=escrows,
        status="pending_signatures",
    )

    _proposal_store[proposal.proposal_id] = proposal
    logger.info("Created settlement proposal %s for group %s", proposal.proposal_id, group_id)
    return proposal


def add_signature(proposal_id: str, signer: str, signature: str) -> SettlementProposal:
    """
    Attach a participant signature to the proposal and check if the threshold is met.
    """
    proposal = _get_proposal(proposal_id)
    proposal.signatures[signer] = signature
    proposal.updated_at = time.time()

    if len(proposal.signatures) >= REQUIRED_SIGNATURES:
        proposal.status = "ready_to_broadcast"
    logger.debug("Proposal %s signatures: %d", proposal_id, len(proposal.signatures))
    return proposal


def broadcast_settlement(proposal_id: str) -> dict:
    """
    Submit unsigned escrow transactions to XRPL (stubbed) and mark the proposal as broadcast.
    """
    proposal = _get_proposal(proposal_id)
    if proposal.status not in {"ready_to_broadcast", "broadcast"}:
        raise ValueError(f"Proposal {proposal_id} is not ready to broadcast (status={proposal.status})")

    results = []
    for escrow in proposal.escrows:
        if escrow.confirmed:
            continue
        response = _submit_escrow_transaction(escrow.transaction)
        escrow.tx_hash = response.get("hash", escrow.tx_hash)
        escrow.confirmed = response.get("confirmed", False)
        results.append(response)

    proposal.status = "broadcast"
    proposal.updated_at = time.time()
    logger.info("Broadcast %d escrows for proposal %s", len(results), proposal_id)
    return {"proposal_id": proposal.proposal_id, "results": results}


def execute_escrows(proposal_id: str) -> list[str]:
    """
    Execute EscrowFinish for every escrow after timeout.
    """
    proposal = _get_proposal(proposal_id)
    if proposal.status != "broadcast":
        raise ValueError(f"Proposal {proposal_id} must be broadcast before execution")

    executed_hashes: list[str] = []
    for escrow in proposal.escrows:
        if escrow.executed or not escrow.tx_hash:
            continue
        finish_hash = _finish_escrow(escrow.tx_hash)
        escrow.executed = True
        executed_hashes.append(finish_hash)

    if executed_hashes and all(e.executed for e in proposal.escrows):
        proposal.status = "completed"
    proposal.updated_at = time.time()
    logger.info("Executed %d escrows for proposal %s", len(executed_hashes), proposal_id)
    return executed_hashes


def _build_payments(nets: dict[str, float]) -> list[Payment]:
    """
    Build a list of payments by greedily matching positive balances (owed) to negatives (is owed).
    """
    debtors = [{"user": acct, "amount": amt} for acct, amt in nets.items() if amt > EPSILON]
    creditors = [{"user": acct, "amount": -amt} for acct, amt in nets.items() if amt < -EPSILON]

    if not debtors or not creditors:
        return []

    # Sort for determinism and to roughly match largest obligations first.
    debtors.sort(key=lambda item: item["amount"], reverse=True)
    creditors.sort(key=lambda item: item["amount"], reverse=True)

    payments: list[Payment] = []
    debtor_idx = creditor_idx = 0

    while debtor_idx < len(debtors) and creditor_idx < len(creditors):
        debtor = debtors[debtor_idx]
        creditor = creditors[creditor_idx]
        amount = min(debtor["amount"], creditor["amount"])

        payments.append(Payment(payer=debtor["user"], payee=creditor["user"], amount=amount))

        debtor["amount"] -= amount
        creditor["amount"] -= amount

        if debtor["amount"] <= EPSILON:
            debtor_idx += 1
        if creditor["amount"] <= EPSILON:
            creditor_idx += 1

    return payments


def _build_escrow_instruction(group_id: str, payment: Payment) -> EscrowInstruction:
    cancel_after = int(time.time()) + ESCROW_HOLD_SECONDS
    tx = {
        "TransactionType": "EscrowCreate",
        "Account": payment.payer,
        "Destination": payment.payee,
        "Amount": _to_drops(payment.amount),
        "CancelAfter": cancel_after,
        "Memos": [
            {"MemoData": f"group:{group_id}".encode().hex()},
        ],
    }
    return EscrowInstruction(payment=payment, transaction=tx)


def _to_drops(amount: float) -> str:
    drops = max(1, int(round(amount * DROPS_PER_UNIT)))
    return str(drops)


def _submit_escrow_transaction(transaction: dict) -> dict:
    """
    Placeholder for XRPL submission. Returns a pseudo hash for now.
    """
    fake_hash = f"FAKE{uuid.uuid4().hex[:24].upper()}"
    logger.debug("Submitting escrow transaction stub: %s", fake_hash)
    return {"hash": fake_hash, "confirmed": False, "transaction": transaction}


def _finish_escrow(tx_hash: str) -> str:
    """
    Placeholder for EscrowFinish call.
    """
    finish_hash = f"FIN{uuid.uuid4().hex[:24].upper()}"
    logger.debug("Finishing escrow %s with stub hash %s", tx_hash, finish_hash)
    return finish_hash


def _get_proposal(proposal_id: str) -> SettlementProposal:
    proposal = _proposal_store.get(proposal_id)
    if not proposal:
        raise KeyError(f"Unknown proposal_id '{proposal_id}'")
    return proposal
