"""FastAPI backend for LendX application."""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, List, Optional
import uvicorn
import time

from ..xrpl_client import (
    connect,
    submit_and_wait,
    create_issuance,
    mint_to_holder,
    get_mpt_balance,
)

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

# In-memory storage for demo (replace with database in production)
lending_pools: Dict[str, dict] = {}
loan_applications: Dict[str, dict] = {}
active_loans: Dict[str, dict] = {}


@app.get("/")
async def root():
    """Health check endpoint."""
    return {"message": "LendX API is running", "status": "healthy"}

@app.post("/pools")
async def create_lending_pool(pool_data: LendingPoolCreate):
    """Create a new lending pool."""
    pool_id = f"pool_{len(lending_pools) + 1}"

    pool = {
        "id": pool_id,
        "name": pool_data.name,
        "amount": pool_data.amount,
        "available": pool_data.amount,
        "interest_rate": pool_data.interest_rate,
        "max_term_days": pool_data.max_term_days,
        "min_loan_amount": pool_data.min_loan_amount,
        "lender_address": pool_data.lender_address,
        "status": "active",
        "created_at": time.time(),
    }

    lending_pools[pool_id] = pool

    return {"pool_id": pool_id, "message": "Lending pool created successfully"}

@app.get("/pools")
async def get_lending_pools():
    """Get all active lending pools."""
    return {"pools": list(lending_pools.values())}

@app.get("/pools/{pool_id}")
async def get_lending_pool(pool_id: str):
    """Get a specific lending pool by ID."""
    if pool_id not in lending_pools:
        raise HTTPException(status_code=404, detail="Lending pool not found")

    return {"pool": lending_pools[pool_id]}

@app.post("/loans/apply")
async def apply_for_loan(application: LoanApplication):
    """Apply for a loan from a lending pool."""
    if application.pool_id not in lending_pools:
        raise HTTPException(status_code=404, detail="Lending pool not found")

    pool = lending_pools[application.pool_id]
    if application.amount > pool["available"]:
        raise HTTPException(status_code=400, detail="Insufficient funds in pool")

    loan_id = f"loan_{len(loan_applications) + 1}"

    loan_app = {
        "id": loan_id,
        "pool_id": application.pool_id,
        "amount": application.amount,
        "purpose": application.purpose,
        "term_days": application.term_days,
        "borrower_address": application.borrower_address,
        "offered_rate": application.offered_rate,
        "status": "pending",
        "applied_at": time.time(),
    }

    loan_applications[loan_id] = loan_app

    return {"loan_id": loan_id, "message": "Loan application submitted successfully"}

@app.get("/loans/applications")
async def get_loan_applications(pool_id: Optional[str] = None):
    """Get loan applications, optionally filtered by pool."""
    applications = list(loan_applications.values())

    if pool_id:
        applications = [app for app in applications if app["pool_id"] == pool_id]

    return {"applications": applications}

@app.post("/loans/{loan_id}/approve")
async def approve_loan(loan_id: str, approval: LoanApproval):
    """Approve or reject a loan application."""
    if loan_id not in loan_applications:
        raise HTTPException(status_code=404, detail="Loan application not found")

    loan_app = loan_applications[loan_id]
    pool = lending_pools[loan_app["pool_id"]]

    if approval.approved:
        # Update pool available funds
        pool["available"] -= loan_app["amount"]

        # Move to active loans
        active_loans[loan_id] = {
            **loan_app,
            "status": "active",
            "approved_at": time.time(),
            "lender_address": approval.lender_address,
        }

        # Remove from applications
        del loan_applications[loan_id]

        return {"message": "Loan approved successfully", "loan_id": loan_id}
    else:
        loan_app["status"] = "rejected"
        return {"message": "Loan application rejected", "loan_id": loan_id}

@app.get("/loans/active")
async def get_active_loans(lender_address: Optional[str] = None, borrower_address: Optional[str] = None):
    """Get active loans, optionally filtered by lender or borrower."""
    loans = list(active_loans.values())

    if lender_address:
        loans = [loan for loan in loans if loan.get("lender_address") == lender_address]

    if borrower_address:
        loans = [loan for loan in loans if loan["borrower_address"] == borrower_address]

    return {"loans": loans}

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
async def health_check():
    """Detailed health check endpoint."""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "pools_count": len(lending_pools),
        "applications_count": len(loan_applications),
        "active_loans_count": len(active_loans),
    }

if __name__ == "__main__":
    uvicorn.run(
        "backend.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )