from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List
import uuid
import time

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from ..graph.types import Edge, Graph
from ..services.iou import IOUService
from ..services.settlement import SettlementService
from ..xrpl_client.mpt import MPTService
from ..xrpl_client.multisig import MultisigService
from ..xrpl_client.escrow import EscrowService


@dataclass
class Group:
    group_id: str
    name: str
    deposit_xrp: float
    threshold: int
    signers: list[str]
    issuance_id: str | None = None
    multisig_address: str | None = None
    created_at: float = 0.0


@dataclass
class SettlementProposal:
    proposal_id: str
    group_id: str
    transactions: list[dict]
    signatures: dict[str, str]
    status: str
    created_at: float


app = FastAPI(title="Group Settlement API", version="1.0.0")

# In-memory storage (replace with database in production)
groups: dict[str, Group] = {}
settlement_proposals: dict[str, SettlementProposal] = {}

# Services
iou_service = IOUService()
settlement_service = SettlementService()
mpt_service = MPTService()
multisig_service = MultisigService()
escrow_service = EscrowService()


@app.post("/groups")
async def create_group(
    name: str, 
    deposit_xrp: float, 
    threshold: int, 
    signers: list[str]
) -> dict:
    """Create MPT, multisig account. Return {group_id, issuance_id}"""
    group_id = str(uuid.uuid4())
    
    try:
        # Create multisig account
        multisig_address = await multisig_service.create_multisig_account(
            signers=signers,
            threshold=threshold
        )
        
        # Create MPT (Multi-Purpose Token) for the group
        issuance_id = await mpt_service.create_mpt(
            issuer=multisig_address,
            group_id=group_id
        )
        
        # Store group information
        group = Group(
            group_id=group_id,
            name=name,
            deposit_xrp=deposit_xrp,
            threshold=threshold,
            signers=signers,
            issuance_id=issuance_id,
            multisig_address=multisig_address,
            created_at=time.time()
        )
        groups[group_id] = group
        
        return {
            "group_id": group_id,
            "issuance_id": issuance_id,
            "multisig_address": multisig_address
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create group: {str(e)}")


@app.post("/groups/{group_id}/join")
async def join_group(
    group_id: str,
    member_address: str,
    escrow_tx_hash: str
) -> dict:
    """Verify escrow, authorize MPT holder. Return {status, member_address}"""
    if group_id not in groups:
        raise HTTPException(status_code=404, detail="Group not found")
    
    group = groups[group_id]
    
    try:
        # Verify escrow transaction
        escrow_valid = await escrow_service.verify_escrow(
            tx_hash=escrow_tx_hash,
            expected_amount=group.deposit_xrp,
            destination=group.multisig_address
        )
        
        if not escrow_valid:
            raise HTTPException(status_code=400, detail="Invalid escrow transaction")
        
        # Authorize MPT holder
        await mpt_service.authorize_holder(
            issuance_id=group.issuance_id,
            holder_address=member_address
        )
        
        return {
            "status": "success",
            "member_address": member_address,
            "group_id": group_id
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to join group: {str(e)}")


@app.get("/groups/{group_id}")
async def get_group(group_id: str) -> Group:
    """Return group details"""
    if group_id not in groups:
        raise HTTPException(status_code=404, detail="Group not found")
    
    return groups[group_id]


@app.get("/groups/{group_id}/balances")
async def get_balances(group_id: str) -> dict[str, float]:
    """Return address -> net balance"""
    if group_id not in groups:
        raise HTTPException(status_code=404, detail="Group not found")
    
    try:
        # Get current graph state for the group
        graph = await iou_service.get_graph(group_id)
        
        # Calculate net balances
        balances = iou_service.calculate_net_balances(graph)
        
        return balances
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get balances: {str(e)}")


@app.post("/groups/{group_id}/iou")
async def add_iou_endpoint(
    group_id: str,
    debtor: str,
    creditor: str,
    amount: float
) -> dict[str, float]:
    """Add IOU, return updated nets"""
    if group_id not in groups:
        raise HTTPException(status_code=404, detail="Group not found")
    
    if amount <= 0:
        raise HTTPException(status_code=400, detail="Amount must be positive")
    
    try:
        # Add IOU to the system
        updated_balances = await iou_service.add_iou(
            group_id=group_id,
            debtor=debtor,
            creditor=creditor,
            amount=amount
        )
        
        return updated_balances
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to add IOU: {str(e)}")


@app.post("/groups/{group_id}/settlements")
async def propose_settlement_endpoint(
    group_id: str
) -> SettlementProposal:
    """Create proposal with unsigned txs"""
    if group_id not in groups:
        raise HTTPException(status_code=404, detail="Group not found")
    
    group = groups[group_id]
    proposal_id = str(uuid.uuid4())
    
    try:
        # Generate settlement transactions
        settlement_txs = await settlement_service.generate_settlement_transactions(
            group_id=group_id,
            multisig_address=group.multisig_address
        )
        
        # Create settlement proposal
        proposal = SettlementProposal(
            proposal_id=proposal_id,
            group_id=group_id,
            transactions=settlement_txs,
            signatures={},
            status="pending",
            created_at=time.time()
        )
        
        settlement_proposals[proposal_id] = proposal
        
        return proposal
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create settlement proposal: {str(e)}")


@app.post("/settlements/{proposal_id}/sign")
async def sign_settlement(
    proposal_id: str,
    signer: str,
    signature: str
) -> SettlementProposal:
    """Add signature, return status"""
    if proposal_id not in settlement_proposals:
        raise HTTPException(status_code=404, detail="Settlement proposal not found")
    
    proposal = settlement_proposals[proposal_id]
    group = groups[proposal.group_id]
    
    # Verify signer is authorized
    if signer not in group.signers:
        raise HTTPException(status_code=403, detail="Unauthorized signer")
    
    try:
        # Add signature to proposal
        proposal.signatures[signer] = signature
        
        # Check if we have enough signatures
        if len(proposal.signatures) >= group.threshold:
            proposal.status = "ready"
        
        settlement_proposals[proposal_id] = proposal
        
        return proposal
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to sign settlement: {str(e)}")


@app.post("/settlements/{proposal_id}/broadcast")
async def broadcast_settlement_endpoint(
    proposal_id: str
) -> dict:
    """Submit escrows, return tracking"""
    if proposal_id not in settlement_proposals:
        raise HTTPException(status_code=404, detail="Settlement proposal not found")
    
    proposal = settlement_proposals[proposal_id]
    
    if proposal.status != "ready":
        raise HTTPException(status_code=400, detail="Settlement not ready for broadcast")
    
    try:
        # Submit settlement transactions to XRPL
        tx_results = await settlement_service.broadcast_settlement(
            proposal_id=proposal_id,
            transactions=proposal.transactions,
            signatures=proposal.signatures
        )
        
        # Update proposal status
        proposal.status = "broadcast"
        settlement_proposals[proposal_id] = proposal
        
        return {
            "proposal_id": proposal_id,
            "status": "broadcast",
            "transaction_results": tx_results
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to broadcast settlement: {str(e)}")


@app.get("/")
async def root():
    """Health check endpoint"""
    return {"message": "Group Settlement API is running"}


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "groups_count": len(groups),
        "proposals_count": len(settlement_proposals)
    }