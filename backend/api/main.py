"""FastAPI backend for LendX application."""

from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from decimal import Decimal
from datetime import datetime, timedelta
import uvicorn
import logging

from ..xrpl_client import (
    connect,
    submit_and_wait,
    create_issuance,
    mint_to_holder,
    get_mpt_balance,
    setup_rlusd_trustline,
    get_rlusd_balance,
    transfer_rlusd,
    check_trustline_exists,
    RLUSD_ISSUER,
    RLUSD_CURRENCY
)
from ..config.database import get_db, init_db, check_db_connection
from ..models.database import User, Pool, Application, Loan, UserMPTBalance
from ..services.mpt_service import create_pool_mpt, create_application_mpt, create_loan_mpt
from ..models.mpt_schemas import PoolMPTMetadata, ApplicationMPTMetadata, LoanMPTMetadata

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize XRPL client for testnet
xrpl_client = None

def get_xrpl_client():
    """Get or create XRPL client connection."""
    global xrpl_client
    if xrpl_client is None:
        xrpl_client = connect('testnet')
    return xrpl_client

app = FastAPI(
    title="LendX API",
    description="Backend API for LendX decentralized lending platform",
    version="1.0.0",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],  # Frontend URLs
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import and register routers
from .auth import router as auth_router

app.include_router(auth_router)

# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    """Initialize database connection on startup"""
    try:
        init_db()
        if check_db_connection():
            logger.info("Database connection established successfully")
        else:
            logger.error("Database connection check failed")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")

# Pydantic models for API requests/responses
class LendingPoolCreate(BaseModel):
    name: str
    amount: float
    interest_rate: float
    max_term_days: int
    min_loan_amount: float
    lender_address: str

class LoanApplication(BaseModel):
    pool_id: str
    amount: float
    purpose: str
    term_days: int
    borrower_address: str
    offered_rate: float

class LoanApproval(BaseModel):
    loan_id: str
    approved: bool
    lender_address: str

class BalanceRequest(BaseModel):
    address: str
    token_id: Optional[str] = None

class ApplicationUpdate(BaseModel):
    application_address: str
    state: str = Field(..., pattern="^(PENDING|APPROVED|REJECTED|EXPIRED)$")

class RLUSDTrustlineRequest(BaseModel):
    address: str
    limit: Optional[str] = "1000000"

class RLUSDTransferRequest(BaseModel):
    from_address: str
    to_address: str
    amount: float


@app.get("/")
async def root():
    """Health check endpoint."""
    return {"message": "LendX API is running", "status": "healthy"}

@app.post("/pools")
async def create_lending_pool(pool_data: LendingPoolCreate, db: Session = Depends(get_db)):
    """Create a new lending pool with MPT on XRPL."""
    try:
        # Verify lender exists
        lender = db.query(User).filter_by(address=pool_data.lender_address).first()
        if not lender:
            # Auto-create user if doesn't exist
            lender = User(address=pool_data.lender_address)
            db.add(lender)
            db.flush()

        # Create pool on XRPL (MPT issuance)
        # For MVP demo: generate a wallet (in production, use user's wallet from frontend)
        from xrpl.wallet import Wallet
        lender_wallet = Wallet.create()
        logger.info(f"Generated demo wallet for pool creation: {lender_wallet.classic_address}")
        
        # Create MPT metadata
        pool_metadata = PoolMPTMetadata(
            issuer_addr=lender_wallet.classic_address,
            total_balance=Decimal(str(pool_data.amount)),
            current_balance=Decimal(str(pool_data.amount)),
            minimum_loan=Decimal(str(pool_data.min_loan_amount)),
            duration=pool_data.max_term_days,
            interest_rate=Decimal(str(pool_data.interest_rate))
        )
        
        # Create MPT on XRPL
        client = get_xrpl_client()
        mpt_result = create_pool_mpt(
            client=client,
            issuer_wallet=lender_wallet,
            metadata=pool_metadata
        )
        
        pool_address = mpt_result['mpt_id']
        tx_hash = mpt_result.get('tx_hash', f"TX_POOL_{int(datetime.now().timestamp())}")
        
        logger.info(f"Created PoolMPT on XRPL: {pool_address}")

        # Create pool in database
        pool = Pool(
            pool_address=pool_address,
            issuer_address=lender_wallet.classic_address,
            total_balance=Decimal(str(pool_data.amount)),
            current_balance=Decimal(str(pool_data.amount)),
            minimum_loan=Decimal(str(pool_data.min_loan_amount)),
            duration_days=pool_data.max_term_days,
            interest_rate=Decimal(str(pool_data.interest_rate)),
            tx_hash=tx_hash
        )

        db.add(pool)
        db.commit()
        db.refresh(pool)

        logger.info(f"Created pool {pool_address} for lender {lender_wallet.classic_address}")
        return {
            "pool_id": pool_address,
            "pool_address": pool_address,
            "tx_hash": tx_hash,
            "explorer_url": f"https://testnet.xrpl.org/transactions/{tx_hash}",
            "wallet_address": lender_wallet.classic_address,
            "wallet_seed": lender_wallet.seed,  # WARNING: Only for demo!
            "message": "Pool created on XRPL testnet. Verify at explorer_url"
        }

    except IntegrityError as e:
        db.rollback()
        logger.error(f"Database integrity error creating pool: {e}")
        raise HTTPException(status_code=400, detail="Pool creation failed: integrity error")
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating pool: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create pool: {str(e)}")

@app.get("/pools")
async def get_lending_pools(db: Session = Depends(get_db)):
    """Get all active lending pools."""
    try:
        pools = db.query(Pool).all()
        return {"pools": [pool.to_dict() for pool in pools]}
    except Exception as e:
        logger.error(f"Error fetching pools: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch pools: {str(e)}")

@app.get("/pools/{pool_id}")
async def get_lending_pool(pool_id: str, db: Session = Depends(get_db)):
    """Get a specific lending pool by ID."""
    try:
        pool = db.query(Pool).filter_by(pool_address=pool_id).first()
        if not pool:
            raise HTTPException(status_code=404, detail="Lending pool not found")

        return {"pool": pool.to_dict()}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching pool {pool_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch pool: {str(e)}")

@app.post("/loans/apply")
async def apply_for_loan(application: LoanApplication, db: Session = Depends(get_db)):
    """Apply for a loan from a lending pool with ApplicationMPT on XRPL."""
    try:
        # Verify pool exists
        pool = db.query(Pool).filter_by(pool_address=application.pool_id).first()
        if not pool:
            raise HTTPException(status_code=404, detail="Lending pool not found")

        # Check pool has sufficient funds
        if Decimal(str(application.amount)) > pool.current_balance:
            raise HTTPException(status_code=400, detail="Insufficient funds in pool")

        # Verify borrower exists or create
        borrower = db.query(User).filter_by(address=application.borrower_address).first()
        if not borrower:
            borrower = User(address=application.borrower_address)
            db.add(borrower)
            db.flush()

        # Create ApplicationMPT on XRPL
        # For MVP demo: generate a wallet (in production, use user's wallet from frontend)
        from xrpl.wallet import Wallet
        borrower_wallet = Wallet.create()
        logger.info(f"Generated demo wallet for application: {borrower_wallet.classic_address}")
        
        # Calculate interest
        interest = Decimal(str(application.amount)) * pool.interest_rate / Decimal("100")
        
        # Create ApplicationMPT metadata
        app_metadata = ApplicationMPTMetadata(
            borrower_addr=borrower_wallet.classic_address,
            pool_addr=pool.pool_address,
            application_date=datetime.now(),
            dissolution_date=datetime.now() + timedelta(days=application.term_days),
            state="PENDING",
            principal=Decimal(str(application.amount)),
            interest=interest
        )
        
        # Create MPT on XRPL
        client = get_xrpl_client()
        mpt_result = create_application_mpt(
            client=client,
            borrower_wallet=borrower_wallet,
            metadata=app_metadata
        )
        
        application_address = mpt_result['mpt_id']
        tx_hash = mpt_result.get('tx_hash', f"TX_APP_{int(datetime.now().timestamp())}")
        
        logger.info(f"Created ApplicationMPT on XRPL: {application_address}")

        app = Application(
            application_address=application_address,
            borrower_address=borrower_wallet.classic_address,
            pool_address=application.pool_id,
            application_date=datetime.now(),
            dissolution_date=datetime.now() + timedelta(days=application.term_days),
            state="PENDING",
            principal=Decimal(str(application.amount)),
            interest=interest,
            tx_hash=tx_hash
        )

        db.add(app)
        db.commit()
        db.refresh(app)

        logger.info(f"Created loan application {application_address}")
        return {
            "loan_id": application_address,
            "application_address": application_address,
            "tx_hash": tx_hash,
            "explorer_url": f"https://testnet.xrpl.org/transactions/{tx_hash}",
            "wallet_address": borrower_wallet.classic_address,
            "wallet_seed": borrower_wallet.seed,  # WARNING: Only for demo!
            "message": "Application submitted on XRPL testnet"
        }

    except HTTPException:
        raise
    except IntegrityError as e:
        db.rollback()
        logger.error(f"Database integrity error creating application: {e}")
        raise HTTPException(status_code=400, detail="Application creation failed")
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating loan application: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create application: {str(e)}")

@app.get("/loans/applications")
async def get_loan_applications(pool_id: Optional[str] = None, db: Session = Depends(get_db)):
    """Get loan applications, optionally filtered by pool."""
    try:
        query = db.query(Application)

        if pool_id:
            query = query.filter_by(pool_address=pool_id)

        applications = query.all()
        return {"applications": [app.to_dict() for app in applications]}

    except Exception as e:
        logger.error(f"Error fetching loan applications: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch applications: {str(e)}")

@app.post("/loans/{loan_id}/approve")
async def approve_loan(loan_id: str, approval: LoanApproval, db: Session = Depends(get_db)):
    """Approve or reject a loan application with LoanMPT creation on XRPL."""
    try:
        # Get application
        app = db.query(Application).filter_by(application_address=loan_id).first()
        if not app:
            raise HTTPException(status_code=404, detail="Loan application not found")

        # Get pool
        pool = db.query(Pool).filter_by(pool_address=app.pool_address).first()
        if not pool:
            raise HTTPException(status_code=404, detail="Pool not found")

        if approval.approved:
            # Verify application is in PENDING state
            if app.state != "PENDING":
                raise HTTPException(status_code=400, detail=f"Application not in PENDING state (current: {app.state})")
            
            # Update application state
            app.state = "APPROVED"

            # Update pool balance
            pool.current_balance -= app.principal

            # Create LoanMPT on XRPL
            # For MVP demo: generate a wallet (in production, use lender's wallet from frontend)
            from xrpl.wallet import Wallet
            lender_wallet = Wallet.create()
            logger.info(f"Generated demo wallet for loan: {lender_wallet.classic_address}")
            
            # Create LoanMPT metadata
            loan_metadata = LoanMPTMetadata(
                pool_addr=app.pool_address,
                borrower_addr=app.borrower_address,
                lender_addr=lender_wallet.classic_address,
                start_date=datetime.now(),
                end_date=datetime.now() + timedelta(days=pool.duration_days),
                principal=app.principal,
                interest=app.interest,
                state="ONGOING"
            )
            
            # Create MPT on XRPL
            client = get_xrpl_client()
            mpt_result = create_loan_mpt(
                client=client,
                lender_wallet=lender_wallet,
                metadata=loan_metadata
            )
            
            loan_address = mpt_result['mpt_id']
            tx_hash = mpt_result.get('tx_hash', f"TX_LOAN_{int(datetime.now().timestamp())}")
            
            logger.info(f"Created LoanMPT on XRPL: {loan_address}")

            loan = Loan(
                loan_address=loan_address,
                pool_address=app.pool_address,
                borrower_address=app.borrower_address,
                lender_address=lender_wallet.classic_address,
                start_date=datetime.now(),
                end_date=datetime.now() + timedelta(days=pool.duration_days),
                principal=app.principal,
                interest=app.interest,
                state="ONGOING",
                tx_hash=tx_hash
            )

            db.add(loan)
            db.commit()

            logger.info(f"Approved loan application {loan_id}, created loan {loan_address}")
            return {
                "message": "Loan approved successfully, LoanMPT created",
                "loan_id": loan_address,
                "loan_address": loan_address,
                "application_tx_hash": app.tx_hash,
                "loan_tx_hash": tx_hash,
                "loan_explorer_url": f"https://testnet.xrpl.org/transactions/{tx_hash}",
                "application_explorer_url": f"https://testnet.xrpl.org/transactions/{app.tx_hash}",
                "wallet_address": lender_wallet.classic_address,
                "wallet_seed": lender_wallet.seed  # WARNING: Only for demo!
            }
        else:
            # Reject application
            app.state = "REJECTED"
            db.commit()

            logger.info(f"Rejected loan application {loan_id}")
            return {"message": "Loan application rejected", "loan_id": loan_id}

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error approving/rejecting loan {loan_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to process approval: {str(e)}")

@app.get("/loans/active")
async def get_active_loans(
    lender_address: Optional[str] = None,
    borrower_address: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get active loans, optionally filtered by lender or borrower."""
    try:
        query = db.query(Loan)

        if lender_address:
            query = query.filter_by(lender_address=lender_address)

        if borrower_address:
            query = query.filter_by(borrower_address=borrower_address)

        loans = query.all()
        return {"loans": [loan.to_dict() for loan in loans]}

    except Exception as e:
        logger.error(f"Error fetching active loans: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch loans: {str(e)}")

@app.post("/balance")
async def get_balance(request: BalanceRequest):
    """Get XRP or token balance for an address."""
    try:
        # Connect to XRPL
        client = connect('testnet')

        if request.token_id:
            # Get MPT balance
            balance = get_mpt_balance(client, request.address, request.token_id)
        else:
            # Get XRP balance (this would need to be implemented in xrpl_client)
            balance = 0  # Placeholder

        return {"address": request.address, "balance": balance, "token_id": request.token_id}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get balance: {str(e)}")

@app.get("/health")
async def health_check(db: Session = Depends(get_db)):
    """Detailed health check endpoint."""
    try:
        pools_count = db.query(Pool).count()
        applications_count = db.query(Application).count()
        active_loans_count = db.query(Loan).count()

        return {
            "status": "healthy",
            "version": "1.0.0",
            "database": "connected",
            "pools_count": pools_count,
            "applications_count": applications_count,
            "active_loans_count": active_loans_count,
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "version": "1.0.0",
            "database": "disconnected",
            "error": str(e)
        }


# ============================================================================
# NEW ENDPOINTS FROM SPEC_ALIGNMENT.md
# ============================================================================

@app.get("/api/loans")
async def get_loans_by_mode(
    mode: str = Query(..., regex="^(borrower|lender)$"),
    address: str = Query(...),
    db: Session = Depends(get_db)
):
    """
    Get loans filtered by user role (borrower or lender).

    Args:
        mode: Either 'borrower' or 'lender'
        address: User's XRP wallet address

    Returns:
        List of loans for the specified user role
    """
    try:
        if mode == "borrower":
            loans = db.query(Loan).filter_by(borrower_address=address).all()
        else:  # mode == "lender"
            loans = db.query(Loan).filter_by(lender_address=address).all()

        return {"loans": [loan.to_dict() for loan in loans]}

    except Exception as e:
        logger.error(f"Error fetching loans for {mode} {address}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch loans: {str(e)}")


@app.get("/api/verify")
async def verify_user(address: str = Query(...), db: Session = Depends(get_db)):
    """
    Get user DID and default MPT balance.

    Args:
        address: User's XRP wallet address

    Returns:
        User information including DID and MPT balance
    """
    try:
        user = db.query(User).filter_by(address=address).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Get default MPT balance (could be extended to query specific MPT)
        mpt_balance = db.query(UserMPTBalance).filter_by(
            user_address=address
        ).first()

        return {
            "address": user.address,
            "did": user.did,
            "mpt_balance": float(mpt_balance.balance) if mpt_balance else 0.0,
            "created_at": user.created_at.isoformat() if user.created_at else None
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error verifying user {address}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to verify user: {str(e)}")


@app.put("/api/application")
async def update_application_status(
    update_data: ApplicationUpdate,
    db: Session = Depends(get_db)
):
    """
    Update application status.

    Args:
        update_data: Contains application_address and new state

    Returns:
        Success message
    """
    try:
        app = db.query(Application).filter_by(
            application_address=update_data.application_address
        ).first()

        if not app:
            raise HTTPException(status_code=404, detail="Application not found")

        # Update state
        app.state = update_data.state
        db.commit()

        logger.info(f"Updated application {update_data.application_address} to state {update_data.state}")
        return {
            "message": "Application status updated successfully",
            "application_address": update_data.application_address,
            "state": update_data.state
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating application {update_data.application_address}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update application: {str(e)}")


# ============================================================================
# RLUSD ENDPOINTS
# ============================================================================

@app.post("/api/rlusd/setup")
async def setup_rlusd_trust(request: RLUSDTrustlineRequest):
    """
    Create RLUSD trust line for a user.

    Note: In production, this would require wallet signing from frontend.
    This endpoint is for demonstration/testing purposes.

    Args:
        request: Contains user address and trust line limit

    Returns:
        Transaction hash of trust line creation
    """
    try:
        # Connect to XRPL
        client = connect('testnet')

        # Note: In production, wallet would be from user's signature
        # For now, this is a placeholder that would fail without proper wallet
        logger.warning("RLUSD trust line setup requires wallet from frontend - endpoint for reference only")

        return {
            "message": "Trust line setup requires wallet signature from frontend",
            "rlusd_issuer": RLUSD_ISSUER,
            "rlusd_currency": RLUSD_CURRENCY,
            "limit": request.limit
        }

    except Exception as e:
        logger.error(f"Error setting up RLUSD trust line: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to setup trust line: {str(e)}")


@app.get("/api/rlusd/balance/{address}")
async def get_rlusd_balance_endpoint(address: str, db: Session = Depends(get_db)):
    """
    Get RLUSD balance for an address.

    This queries the XRPL in real-time and optionally caches the result
    in the database for performance.

    Args:
        address: XRP wallet address

    Returns:
        RLUSD balance and trust line status
    """
    try:
        # Connect to XRPL
        client = connect('testnet')

        # Check if trust line exists
        has_trustline = check_trustline_exists(client, address)

        # Get balance
        balance = get_rlusd_balance(client, address)

        # Cache balance in database
        user = db.query(User).filter_by(address=address).first()
        if not user:
            user = User(address=address)
            db.add(user)
            db.flush()

        # Update or create balance cache
        # Note: Using a generic MPT ID for RLUSD
        rlusd_mpt_id = f"RLUSD_{RLUSD_ISSUER}"
        balance_cache = db.query(UserMPTBalance).filter_by(
            user_address=address,
            mpt_id=rlusd_mpt_id
        ).first()

        if balance_cache:
            balance_cache.balance = balance
            balance_cache.last_synced = datetime.now()
        else:
            balance_cache = UserMPTBalance(
                user_address=address,
                mpt_id=rlusd_mpt_id,
                balance=balance
            )
            db.add(balance_cache)

        db.commit()

        logger.info(f"Fetched RLUSD balance for {address}: {balance}")

        return {
            "address": address,
            "balance": float(balance),
            "has_trustline": has_trustline,
            "rlusd_issuer": RLUSD_ISSUER,
            "rlusd_currency": RLUSD_CURRENCY,
            "last_synced": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Error fetching RLUSD balance for {address}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch RLUSD balance: {str(e)}")


@app.get("/api/rlusd/check-trustline/{address}")
async def check_rlusd_trustline(address: str):
    """
    Check if an address has RLUSD trust line set up.

    This is useful for pre-flight checks before attempting transfers
    or loan disbursements.

    Args:
        address: XRP wallet address

    Returns:
        Trust line status
    """
    try:
        client = connect('testnet')
        has_trustline = check_trustline_exists(client, address)

        logger.info(f"Trust line check for {address}: {has_trustline}")

        return {
            "address": address,
            "has_trustline": has_trustline,
            "rlusd_issuer": RLUSD_ISSUER,
            "message": "Trust line exists" if has_trustline else "No RLUSD trust line found"
        }

    except Exception as e:
        logger.error(f"Error checking trust line for {address}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to check trust line: {str(e)}")


@app.post("/api/rlusd/transfer")
async def transfer_rlusd_endpoint(request: RLUSDTransferRequest):
    """
    Transfer RLUSD between addresses.

    Note: In production, this would require wallet signing from frontend.
    This endpoint is for demonstration/testing purposes.

    Args:
        request: Contains sender, recipient, and amount

    Returns:
        Transaction hash of the transfer
    """
    try:
        # Connect to XRPL
        client = connect('testnet')

        # Note: In production, wallet would be from user's signature
        logger.warning("RLUSD transfer requires wallet signature from frontend - endpoint for reference only")

        # Validate both parties have trust lines
        sender_has_trustline = check_trustline_exists(client, request.from_address)
        recipient_has_trustline = check_trustline_exists(client, request.to_address)

        if not sender_has_trustline:
            raise HTTPException(
                status_code=400,
                detail=f"Sender {request.from_address} does not have RLUSD trust line"
            )

        if not recipient_has_trustline:
            raise HTTPException(
                status_code=400,
                detail=f"Recipient {request.to_address} does not have RLUSD trust line"
            )

        return {
            "message": "RLUSD transfer requires wallet signature from frontend",
            "from": request.from_address,
            "to": request.to_address,
            "amount": request.amount,
            "rlusd_currency": RLUSD_CURRENCY,
            "rlusd_issuer": RLUSD_ISSUER
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error transferring RLUSD: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to transfer RLUSD: {str(e)}")


@app.get("/api/rlusd/info")
async def get_rlusd_info():
    """
    Get RLUSD configuration information.

    Returns:
        RLUSD issuer address and currency code
    """
    return {
        "rlusd_issuer": RLUSD_ISSUER,
        "rlusd_currency": RLUSD_CURRENCY,
        "network": "testnet",
        "description": "Ripple USD stablecoin on XRP Ledger",
        "requires_trustline": True
    }

if __name__ == "__main__":
    uvicorn.run(
        "backend.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )