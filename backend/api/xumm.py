"""
Xumm Wallet API Endpoints
Server-side proxy for Xumm SDK operations
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional
import logging

from ..services.xumm_service import get_xumm_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/xumm", tags=["xumm"])


class TransactionPayloadRequest(BaseModel):
    """Request model for creating transaction payload"""
    tx_json: Dict[str, Any]


class PayloadStatusResponse(BaseModel):
    """Response model for payload status"""
    signed: bool
    cancelled: bool
    expired: bool
    account: Optional[str] = None
    txid: Optional[str] = None


@router.post("/signin")
async def create_signin_payload():
    """
    Create a Xumm sign-in payload
    Returns QR code and deeplink for user to sign in with Xumm app
    """
    try:
        xumm = get_xumm_service()
        payload = await xumm.create_signin_payload()
        
        logger.info(f"Created sign-in payload: {payload['uuid']}")
        
        return {
            "success": True,
            "payload": payload
        }
    except Exception as e:
        logger.error(f"Failed to create sign-in payload: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/transaction")
async def create_transaction_payload(request: TransactionPayloadRequest):
    """
    Create a Xumm transaction payload for signing
    Returns QR code and deeplink for user to sign transaction
    """
    try:
        xumm = get_xumm_service()
        payload = await xumm.create_transaction_payload(request.tx_json)
        
        logger.info(f"Created transaction payload: {payload['uuid']}")
        
        return {
            "success": True,
            "payload": payload
        }
    except Exception as e:
        logger.error(f"Failed to create transaction payload: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/payload/{payload_uuid}")
async def get_payload_status(payload_uuid: str):
    """
    Get the status of a Xumm payload
    Check if user has signed, cancelled, or if it expired
    """
    try:
        xumm = get_xumm_service()
        status = await xumm.get_payload_status(payload_uuid)
        
        return {
            "success": True,
            "status": status
        }
    except Exception as e:
        logger.error(f"Failed to get payload status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/payload/{payload_uuid}")
async def cancel_payload(payload_uuid: str):
    """Cancel a pending Xumm payload"""
    try:
        xumm = get_xumm_service()
        success = await xumm.cancel_payload(payload_uuid)
        
        if success:
            logger.info(f"Cancelled payload: {payload_uuid}")
            return {"success": True, "message": "Payload cancelled"}
        else:
            raise HTTPException(status_code=400, detail="Failed to cancel payload")
    except Exception as e:
        logger.error(f"Failed to cancel payload: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def xumm_health():
    """Check if Xumm service is configured and accessible"""
    try:
        xumm = get_xumm_service()
        return {
            "success": True,
            "configured": True,
            "message": "Xumm service is ready"
        }
    except Exception as e:
        return {
            "success": False,
            "configured": False,
            "message": str(e)
        }
