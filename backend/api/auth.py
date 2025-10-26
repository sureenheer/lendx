"""Authentication endpoints for LendX."""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from xrpl.wallet import Wallet
import logging

from ..config.database import get_db
from ..models.database import User
from ..services.did_service import create_did_for_user, get_did_document
from ..xrpl_client.client import connect

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/auth", tags=["authentication"])

# XRPL client for testnet
def get_xrpl_client():
    """Get XRPL client connection."""
    return connect('testnet')


class SignupRequest(BaseModel):
    """Signup request model."""
    username: str = None  # Optional for MVP


class SignupResponse(BaseModel):
    """Signup response model."""
    address: str
    did: str
    seed: str  # WARNING: Only for demo! Never return in production
    explorer_url: str
    message: str


class VerifyResponse(BaseModel):
    """Verify user response model."""
    address: str
    did: str = None
    did_document: dict = None
    exists: bool


@router.post("/signup", response_model=SignupResponse)
async def signup(request: SignupRequest = None, db: Session = Depends(get_db)):
    """
    Create new user with XRPL wallet and DID.
    
    For MVP demo:
    - Generates wallet automatically
    - Creates DID on XRPL testnet
    - Returns seed (DEMO ONLY - never do this in production!)
    """
    try:
        # Generate wallet
        wallet = Wallet.create()
        logger.info(f"Generated wallet for signup: {wallet.classic_address}")
        
        # Check if user already exists
        existing_user = db.query(User).filter(User.address == wallet.classic_address).first()
        if existing_user:
            raise HTTPException(400, "User already exists")
        
        # Create DID on XRPL
        did = create_did_for_user(
            user_wallet=wallet,
            network='testnet',
            update_database=False  # We'll handle DB manually
        )
        
        logger.info(f"Created DID: {did}")
        
        # Create user in database
        user = User(
            address=wallet.classic_address,
            did=did
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        
        logger.info(f"Created user in database: {wallet.classic_address}")
        
        return SignupResponse(
            address=wallet.classic_address,
            did=did,
            seed=wallet.seed,  # WARNING: Only for demo!
            explorer_url=f"https://testnet.xrpl.org/accounts/{wallet.classic_address}",
            message="User created successfully with DID on XRPL testnet"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Signup failed: {e}")
        raise HTTPException(status_code=500, detail=f"Signup failed: {str(e)}")


@router.get("/verify/{address}", response_model=VerifyResponse)
async def verify_user(address: str, db: Session = Depends(get_db)):
    """
    Verify user exists and retrieve DID information.
    
    Args:
        address: User's XRP wallet address
        
    Returns:
        User information including DID and DID document
    """
    try:
        # Check database
        user = db.query(User).filter(User.address == address).first()
        
        if not user:
            return VerifyResponse(
                address=address,
                did=None,
                did_document=None,
                exists=False
            )
        
        # Get DID document from XRPL
        did_document = None
        if user.did:
            try:
                did_document = get_did_document(address, network='testnet')
            except Exception as e:
                logger.warning(f"Failed to retrieve DID document for {address}: {e}")
        
        return VerifyResponse(
            address=address,
            did=user.did,
            did_document=did_document,
            exists=True
        )
        
    except Exception as e:
        logger.error(f"Verify user failed for {address}: {e}")
        raise HTTPException(status_code=500, detail=f"Verification failed: {str(e)}")


@router.get("/health")
async def auth_health():
    """Health check for auth endpoints."""
    return {
        "status": "healthy",
        "service": "authentication",
        "endpoints": ["/signup", "/verify/{address}"]
    }
